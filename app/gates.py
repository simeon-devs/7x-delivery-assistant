"""
The rules. One place.

Every permission in the system is decided here, computed from the facts in the shipment row at
the moment it is asked. Nothing is read from a stored boolean, because a stored boolean goes
stale the moment an action changes the record.

The model never sees these rules. It is handed the answer and a sentence to say, so it has no
way to reason around a rule it was never shown.

Sources for each rule are in DECISIONS.md:
  D-02  the six states
  D-03  duplicate rows that disagree about a terminal state
  D-06  attempts that contradict the status
  D-07  COD blocks an address change (a POLICY call, labelled as such)
  D-08  no phone on file means the customer cannot be verified
"""

from __future__ import annotations

# D-02: the six real states, and what each one means for action.
TERMINAL = {"delivered", "returned"}
RESCHEDULABLE = {"failed", "redelivery_scheduled", "out_for_delivery", "in_transit"}

# D-03 / operational rule: three attempts is the limit in the source data.
MAX_ATTEMPTS = 3

# How far ahead a delivery may be moved.
MAX_DAYS_AHEAD = 14


# ---------------------------------------------------------------------------
# The sentences a customer actually reads.
#
# A-22: these are written as plain English, not as error codes, because the staff console shows
# the same string. The customer and the staff member must never be told two different stories.
# ---------------------------------------------------------------------------

def _closed_text(state: str) -> str:
    if state == "delivered":
        return "Our record shows this parcel has already been delivered."
    return "This parcel has been returned to the sender."


REASON_TEXT = {
    "no_phone_on_file": (
        "There's no phone number on this shipment, so I have no way to confirm it's yours."
    ),
    "attempt_limit_reached": (
        "This parcel has already had 3 delivery attempts, which is the limit, "
        "so it needs a person to look at it."
    ),
    "duplicate_conflict": (
        "I have two records for this parcel and they don't agree with each other."
    ),
    "not_reschedulable": (
        "This parcel isn't at a stage where I can change the delivery."
    ),
}


def cod_text(amount: float) -> str:
    return (
        f"This parcel has {amount:,.2f} AED to collect on delivery, "
        "and I don't change the address on parcels with a payment attached."
    )


# ---------------------------------------------------------------------------


def evaluate(row) -> dict:
    """
    Take a shipment row (sqlite3.Row or dict) and return what may be done to it, right now.

    Returns a dict rather than an object so it drops straight into a tool response.
    """
    state = (row["state"] or "").strip()
    attempts = int(row["delivery_attempts"] or 0)
    cod = float(row["cod_amount_aed"] or 0)
    phone = row["phone"]
    conflict = bool(row["flag_duplicate_conflict"])
    attempts_unreliable = bool(row["flag_attempts_unreliable"])

    is_open = state not in TERMINAL

    # ---- reasons this shipment needs a person, whatever the customer asks for
    block_codes: list[str] = []
    if not phone:
        block_codes.append("no_phone_on_file")          # D-08
    if attempts >= MAX_ATTEMPTS:
        block_codes.append("attempt_limit_reached")
    if conflict:
        block_codes.append("duplicate_conflict")        # D-03

    requires_human = bool(block_codes)

    # ---- reschedule
    if not is_open:
        resch_ok, resch_why = False, _closed_text(state)
    elif requires_human:
        resch_ok, resch_why = False, REASON_TEXT[block_codes[0]]
    elif state not in RESCHEDULABLE:
        resch_ok, resch_why = False, REASON_TEXT["not_reschedulable"]
    else:
        resch_ok, resch_why = True, None

    # ---- change address
    # D-07: COD blocks an address change. This is a policy decision, not a data rule.
    # It is applied on top of the reschedule gate, so a COD parcel can still be moved
    # to another day; it just cannot be moved to another place.
    if not resch_ok:
        addr_ok, addr_why = False, resch_why
    elif cod > 0:
        addr_ok, addr_why = False, cod_text(cod)
    else:
        addr_ok, addr_why = True, None

    return {
        "is_open": is_open,
        "requires_human": requires_human,
        "block_codes": block_codes,
        "can_reschedule": resch_ok,
        "reschedule_blocked_because": resch_why,
        "can_change_address": addr_ok,
        "change_address_blocked_because": addr_why,
        # D-06: when the attempt count and the status disagree, neither is trustworthy.
        # The assistant is forbidden from stating that an attempt was made.
        "attempts_reliable": not attempts_unreliable,
        "data_confidence": row["data_confidence"] or "clean",
    }


def gate_for(row, action: str) -> tuple[bool, str | None, str | None]:
    """
    The single question the door asks: may this action happen to this row, right now?

    Returns (allowed, reason_text, reason_code).
    """
    g = evaluate(row)

    if action == "reschedule":
        if g["can_reschedule"]:
            return True, None, None
        code = g["block_codes"][0] if g["block_codes"] else "not_actionable"
        return False, g["reschedule_blocked_because"], code

    if action == "change_address":
        if g["can_change_address"]:
            return True, None, None
        if g["can_reschedule"]:          # blocked only by COD
            return False, g["change_address_blocked_because"], "cod_on_delivery"
        code = g["block_codes"][0] if g["block_codes"] else "not_actionable"
        return False, g["change_address_blocked_because"], code

    raise ValueError(f"unknown action: {action}")

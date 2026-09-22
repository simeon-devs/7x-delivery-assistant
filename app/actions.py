"""
The one door, and the five tools.

Everything the assistant can do passes through `_do_action`. There is no other path from the
model to the database. That is deliberate:

  * the gate cannot be skipped, because skipping it would mean not calling the function that
    does the writing;
  * the action log cannot have holes, because the logging lives in the same function;
  * when someone asks where the safety is, the answer is one function, not five places.

The door re-reads the record at the moment of the write. What the model was told earlier is a
photograph; the door looks at the thing itself. This closes the window where a parcel is looked
up at 14:00, blocked by a staff member at 14:01, and written at 14:02.

Every tool returns the same four fields:  { ok, data, reason, escalate }
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from . import gates
from .db import TODAY, log_action, next_case_id

MAX_DAYS_AHEAD = gates.MAX_DAYS_AHEAD


# ---------------------------------------------------------------- shapes


def ok(data: dict, reason: str | None = None) -> dict:
    return {"ok": True, "data": data, "reason": reason, "escalate": False}


def refuse(reason: str, data: dict | None = None, escalate: bool = True) -> dict:
    return {"ok": False, "data": data or {}, "reason": reason, "escalate": escalate}


# ---------------------------------------------------------------- reading


def _row(conn, tracking_number: str):
    return conn.execute(
        "SELECT * FROM shipments WHERE tracking_number = ?",
        (str(tracking_number).strip().upper(),),
    ).fetchone()


def _session(conn, session_id: str):
    return conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()


def _view(row, g: dict) -> dict:
    """
    What the model is allowed to see about a shipment.

    FACTS, never PERMISSIONS.

    The model is given no way to know in advance what it is allowed to do. There is no
    `can_reschedule` here, and no `blocked_because`. It finds out by attempting, and the answer
    comes back from the gate as a refusal with a sentence attached.

    This was not the first design. The first version handed the model the permission flags, and
    it behaved exactly as you would expect a sensible assistant to behave: it saw `false`,
    skipped the tool, and escalated on its own judgement. That is wrong twice. The customer
    never hears the real reason, and the audit trail records "handed to a person" rather than
    "refused, because 389.18 AED is due on delivery". Prompting against it did not hold. Taking
    the information away did.

    Where the records contradict each other, the status itself is withheld too. If the model
    has no status to recite, it has to say the thing that is actually true: that the records
    disagree.
    """
    conflicted = bool(row["flag_duplicate_conflict"])
    unreliable = not g["attempts_reliable"]

    view = {
        "tracking_number": row["tracking_number"],
        "customer_name": row["customer_name"],
        "emirate": row["emirate"],
        "delivery_address": row["delivery_address"],
        "scheduled_date": row["scheduled_date"],
        "shipment_date": row["shipment_date"],
        "cod_amount_aed": float(row["cod_amount_aed"] or 0),
    }

    if conflicted:
        # D-03. Two rows, disagreeing about a terminal state. There is no status to give.
        view["status"] = "UNCLEAR"
        view["must_tell_customer"] = (
            "There are two records for this parcel and they do not agree with each other. "
            "One says it was delivered and the other does not."
        )
        view["then"] = "Say that to the customer in your own plain words, then escalate."
        view["delivery_attempts"] = "unknown"

    elif unreliable:
        # D-06. The attempt count and the status contradict each other, so neither is safe
        # to read out. 6.6% of real complaints are customers saying an attempt never happened.
        view["status"] = "UNCLEAR"
        view["must_tell_customer"] = (
            "The record for this parcel is contradictory. It reports a delivery attempt but "
            "no attempt is actually logged against it."
        )
        view["then"] = "Say that to the customer in your own plain words, then escalate."
        view["delivery_attempts"] = "unknown"

    else:
        view["status"] = row["state"]
        view["delivery_attempts"] = f"{row['delivery_attempts']} of {gates.MAX_ATTEMPTS}"

    return view


# ---------------------------------------------------------------- cases


def _open_case(
    conn,
    *,
    session_id: str | None,
    tracking_number: str | None,
    reason_code: str,
    reason_text: str,
    customer_request: str | None,
) -> str:
    """
    Create a case, or reuse the open one that already covers this exact situation so a retry
    does not fill the queue with duplicates.
    """
    existing = conn.execute(
        """SELECT id FROM cases
           WHERE status = 'open' AND session_id IS ? AND tracking_number IS ?
             AND reason_code = ?""",
        (session_id, tracking_number, reason_code),
    ).fetchone()
    if existing:
        return existing["id"]

    case_id = next_case_id(conn)
    conn.execute(
        """INSERT INTO cases
           (id, session_id, tracking_number, reason_code, reason_text,
            customer_request, status, created_at)
           VALUES (?,?,?,?,?,?,'open',?)""",
        (
            case_id,
            session_id,
            tracking_number,
            reason_code,
            reason_text,
            customer_request,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    return case_id


# ---------------------------------------------------------------- THE DOOR


def _do_action(conn, session_id: str | None, tracking_number: str, action: str, params: dict) -> dict:
    """
    The only way to change a shipment.

      1. read the record fresh, right now
      2. check the gate
      3. write, or refuse and raise a case
      4. log it either way
      5. return the standard shape
    """
    # 1 ------------------------------------------------------------- read fresh
    row = _row(conn, tracking_number)
    if row is None:
        detail = f"No shipment found for {tracking_number}."
        log_action(
            conn, session_id=session_id, tracking_number=str(tracking_number),
            action=action, outcome="refused", detail=detail, params=params,
        )
        return refuse("I can't find a parcel with that tracking number.", escalate=False)

    tn = row["tracking_number"]

    # 2 ------------------------------------------------------------- the gate
    allowed, reason_text, reason_code = gates.gate_for(row, action)

    if not allowed:
        # 3a ---------------------------------------------------- refuse and raise a case
        #
        # The case is created HERE rather than depending on the model remembering to call
        # escalate_to_human. A refusal can never silently fall through the cracks.
        case_id = _open_case(
            conn,
            session_id=session_id,
            tracking_number=tn,
            reason_code=reason_code or "blocked",
            reason_text=reason_text or "Blocked.",
            customer_request=json.dumps(params),
        )
        detail = f"Refused to {_verb(action)} on {tn}. {reason_text} Sent to the human queue."
        log_action(
            conn, session_id=session_id, tracking_number=tn, action=action,
            outcome="refused", detail=detail, params=params,
        )
        return refuse(reason_text, data={"case_id": case_id, "tracking_number": tn})

    # 3b ------------------------------------------------------------- write
    now = datetime.now().isoformat(timespec="seconds")

    if action == "reschedule":
        new_date = params["new_date"]
        conn.execute(
            """UPDATE shipments
               SET scheduled_date = ?, state = 'redelivery_scheduled', updated_at = ?
               WHERE tracking_number = ?""",
            (new_date, now, tn),
        )
        detail = f"Rescheduled {tn} to {new_date}."

    elif action == "change_address":
        new_address = params["new_address"]
        conn.execute(
            "UPDATE shipments SET delivery_address = ?, updated_at = ? WHERE tracking_number = ?",
            (new_address, now, tn),
        )
        detail = f"Changed the address on {tn} to {new_address}."

    else:  # pragma: no cover
        raise ValueError(f"unknown action: {action}")

    # 4 ------------------------------------------------------------- log
    log_action(
        conn, session_id=session_id, tracking_number=tn, action=action,
        outcome="done", detail=detail, params=params,
    )

    # 5 ------------------------------------------------------------- return the new truth
    fresh = _row(conn, tn)
    return ok(_view(fresh, gates.evaluate(fresh)))


def _verb(action: str) -> str:
    return {"reschedule": "reschedule", "change_address": "change the address"}.get(action, action)


# ---------------------------------------------------------------- THE FIVE TOOLS


def find_shipments_for_customer(conn, session_id: str) -> dict:
    """Every parcel belonging to the verified customer on this session."""
    s = _session(conn, session_id)
    if s is None or not s["verified"] or not s["phone"]:
        return refuse(
            "I can't look up your parcels until the number on this conversation is verified.",
            escalate=False,
        )

    rows = conn.execute(
        "SELECT * FROM shipments WHERE phone = ? ORDER BY state, tracking_number",
        (s["phone"],),
    ).fetchall()

    if not rows:
        return ok({"shipments": [], "count": 0},
                  reason="No parcels are registered to this number.")

    open_first = [r for r in rows if r["state"] not in gates.TERMINAL]
    closed = [r for r in rows if r["state"] in gates.TERMINAL]
    listed = (open_first + closed)[:10]

    # The list deliberately does NOT carry permissions.
    #
    # When the model can see `can_change_address: false` up front it tends to skip the tool and
    # escalate on its own judgement. That is the wrong shape twice over: the customer never
    # hears the real reason the gate would have given, and the audit trail records "handed to a
    # person" instead of "refused, because X". Permissions belong to the moment of the write.
    # Warnings still travel, because those change what the assistant should SAY, not what it
    # is allowed to do.
    def _brief(r) -> dict:
        g = gates.evaluate(r)
        v = {
            "tracking_number": r["tracking_number"],
            "delivery_address": r["delivery_address"],
            "scheduled_date": r["scheduled_date"],
            "cod_amount_aed": float(r["cod_amount_aed"] or 0),
        }
        full = _view(r, g)
        v["status"] = full["status"]
        for k in ("must_tell_customer", "then"):
            if k in full:
                v[k] = full[k]
        return v

    return ok({"count": len(rows), "shipments": [_brief(r) for r in listed]})


def get_shipment(conn, session_id: str | None, tracking_number: str) -> dict:
    """
    One parcel.

    A-07: status is readable by anyone holding the tracking number, because it is already
    public on every carrier's tracking page. Acting on it is what requires verification.
    """
    row = _row(conn, tracking_number)
    if row is None:
        return refuse("I can't find a parcel with that tracking number.", escalate=False)

    g = gates.evaluate(row)
    view = _view(row, g)

    s = _session(conn, session_id) if session_id else None
    verified_owner = bool(s and s["verified"] and s["phone"] and s["phone"] == row["phone"])

    if not verified_owner:
        # Tracking level (A-07). Status is already public on every carrier's site, so showing
        # it adds no exposure. Acting on it is the part that needs a verified number.
        #
        # This goes in its own field rather than into must_tell_customer, which may already
        # hold something more important. A parcel whose two records disagree about delivery
        # needs the customer to hear THAT, not a note about verification.
        if not row["phone"]:
            view["note"] = gates.REASON_TEXT["no_phone_on_file"]
        else:
            view["note"] = (
                "This conversation is not verified against the number on this shipment, so "
                "you can tell them where it is but nothing can be changed on it."
            )
        view.setdefault("then", "Say that, then offer to pass it to a person.")

    return ok(view)


def reschedule_delivery(conn, session_id: str, tracking_number: str, new_date: str) -> dict:
    """Move a delivery to a new date. Changes the record."""
    parsed = _parse_date(new_date)
    if parsed is None:
        return refuse("I couldn't read that date. Give it to me as YYYY-MM-DD.", escalate=False)
    if parsed <= TODAY:
        return refuse("That date has already passed. Pick a day from tomorrow onwards.",
                      escalate=False)
    if parsed > TODAY + timedelta(days=MAX_DAYS_AHEAD):
        return refuse(
            f"I can only move a delivery up to {MAX_DAYS_AHEAD} days ahead. "
            "For anything further out, a person needs to arrange it.",
        )

    if not _owns(conn, session_id, tracking_number):
        return _not_verified(conn, session_id, tracking_number,
                             {"new_date": parsed.isoformat()}, "reschedule")

    return _do_action(conn, session_id, tracking_number, "reschedule",
                      {"new_date": parsed.isoformat()})


def change_address(conn, session_id: str, tracking_number: str, new_address: str) -> dict:
    """Change where a parcel goes. Changes the record."""
    addr = (new_address or "").strip()
    if len(addr) < 8:
        return refuse("That address looks incomplete. Give me the full delivery address.",
                      escalate=False)

    if not _owns(conn, session_id, tracking_number):
        return _not_verified(conn, session_id, tracking_number,
                             {"new_address": addr}, "change_address")

    return _do_action(conn, session_id, tracking_number, "change_address",
                      {"new_address": addr})


def escalate_to_human(
    conn,
    session_id: str,
    reason: str,
    details: str | None = None,
    tracking_number: str | None = None,
) -> dict:
    """
    Hand the conversation to a person.

    A-04: the assistant goes silent in this session by default. Only a staff member turns it
    back on.
    """
    tn = None
    row = None
    if tracking_number:
        row = _row(conn, tracking_number)
        tn = row["tracking_number"] if row else None

    case_id = _open_case(
        conn,
        session_id=session_id,
        tracking_number=tn,
        reason_code="customer_request",
        reason_text=reason,
        customer_request=details,
    )
    conn.execute("UPDATE sessions SET assistant_enabled = 0 WHERE id = ?", (session_id,))

    log_action(
        conn, session_id=session_id, tracking_number=tn, action="escalate",
        outcome="done", detail=f"Handed to a person. {reason} ({case_id})",
        params={"details": details},
    )

    result = {"case_id": case_id}

    # If this parcel's records contradict each other, the customer has to be told that, in this
    # reply, not in a case note they will never see.
    #
    # The sentence is repeated here, in the LAST tool result before the model writes its
    # answer, because putting it only in the shipment lookup did not work: by the time the
    # model composed its reply the instruction was two rounds back and it summarised it away.
    # Position in the context is doing real work here, not emphasis.
    if row is not None:
        g = gates.evaluate(row)
        v = _view(row, g)
        if "must_tell_customer" in v:
            result["say_this_before_anything_else"] = (
                "Tell the customer this first, in your own words, before you mention the "
                "case number: " + v["must_tell_customer"]
            )

    return ok(result, reason="Handed to a person.")


# ---------------------------------------------------------------- internals


def _owns(conn, session_id: str | None, tracking_number: str) -> bool:
    s = _session(conn, session_id) if session_id else None
    if not s or not s["verified"] or not s["phone"]:
        return False
    row = _row(conn, tracking_number)
    return bool(row and row["phone"] and row["phone"] == s["phone"])


def _not_verified(conn, session_id, tracking_number, params, action) -> dict:
    row = _row(conn, tracking_number)
    if row is None:
        return refuse("I can't find a parcel with that tracking number.", escalate=False)

    tn = row["tracking_number"]
    if not row["phone"]:
        why = gates.REASON_TEXT["no_phone_on_file"]          # D-08, the 71
        code = "no_phone_on_file"
    else:
        why = ("This conversation isn't verified against the number on this shipment, "
               "so I can't make changes to it.")
        code = "not_verified"

    case_id = _open_case(
        conn, session_id=session_id, tracking_number=tn, reason_code=code,
        reason_text=why, customer_request=json.dumps(params),
    )
    log_action(
        conn, session_id=session_id, tracking_number=tn, action=action,
        outcome="refused", detail=f"Refused to {_verb(action)} on {tn}. {why} "
                                 "Sent to the human queue.",
        params=params,
    )
    return refuse(why, data={"case_id": case_id, "tracking_number": tn})


def _parse_date(value: str) -> date | None:
    v = (value or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    return None

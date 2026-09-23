"""
The cast: every row the demo touches, pinned by tracking number.

Two lists, and they never overlap:

  SEED    the eight conversations that already exist when the demo opens. Recorded once against
          the real model (python -m app.demo record --all) and replayed at every reset (A-26).
  PICKER  the rows a reviewer can start a fresh conversation as. Nothing has happened to these,
          so "a normal parcel" is still normal when they pick it.

Each SEED scenario also carries `needs`, the profile the record must have before the steps run
("allowed" | "refused" | "unclear", the same three words as `Persona.outcome`).

Tracking numbers and the customer's lines only. Names, phones and addresses come from the
database at run time, so nothing from the client's file lives in this repository.

Step kinds, as tuples:
  ("say", text)              the customer types; the assistant answers (recorded)
  ("verify", tracking)       web only: the customer types a tracking number
  ("code",)                  web only: the customer types the code that was sent
  ("staff", author, text)    a person replies from the console; the assistant stands down
  ("handback",)              the person hands the conversation back to the assistant
  ("resolve",)               the person resolves every open case on this conversation

Expectations (python -m app.demo check):
  state, scheduled_date         exact values on the shipment row afterwards
  address_unchanged             True: the address must equal what it was before
  address_contains              a substring the new address must contain
  cases                         exactly these [reason_code, status] pairs on the session
  cases_include                 at least these pairs
  assistant_enabled, verified   exact booleans on the session

validate(conn) checks this module against the code and the database -- every tracking number
exists, SEED/PICKER/WEB_TRY do not overlap, and each row's actual profile matches what it claims
-- and returns the problems found, if any. demo.py refuses to record while it is non-empty.
"""

from __future__ import annotations

from dataclasses import dataclass

from .db import next_weekday


@dataclass(frozen=True)
class Scenario:
    key: str
    what: str
    tracking: str
    channel: str            # "whatsapp" | "web"
    needs: str               # "allowed" | "refused" | "unclear" -- the profile the record must have
    age_minutes: int        # how long before "now" it started, when replayed
    steps: tuple
    expect: dict


@dataclass(frozen=True)
class Persona:
    tracking: str
    label: str
    outcome: str            # "allowed" | "refused" | "unclear"


THURSDAY = next_weekday(3).isoformat()  # the Thursday after TODAY; the scripts say "Thursday" and the checks need the date

SEED: tuple[Scenario, ...] = (
    Scenario(
        key="reschedule", what="a normal parcel, moved to Thursday",
        tracking="EX400003AE", channel="whatsapp", needs="allowed", age_minutes=180,
        steps=(
            ("say", "hi, where is my parcel?"),
            ("say", "I won't be home this week until Thursday. can you move it?"),
            ("say", "yes please"),
        ),
        expect={"state": "redelivery_scheduled", "scheduled_date": THURSDAY,
                "address_unchanged": True, "cases": [], "assistant_enabled": True},
    ),
    Scenario(
        key="cod", what="cash on delivery: the date is moved, then the address is refused",
        tracking="EX400001AE", channel="whatsapp", needs="refused", age_minutes=120,
        steps=(
            ("say", "hi, can you deliver my parcel on Thursday instead? I'll be home then"),
            ("say", "yes"),
            ("say", "actually, could you send it to my office instead of home?"),
            ("say", "Prism Tower, office 1204, Business Bay, Dubai"),
            ("say", "yes that's right, please change it"),
        ),
        expect={"state": "redelivery_scheduled", "scheduled_date": THURSDAY,
                "address_unchanged": True, "cases_include": [["cod_on_delivery", "open"]]},
    ),
    Scenario(
        key="conflict", what="two records that disagree about delivery",
        tracking="EX400215AE", channel="whatsapp", needs="unclear", age_minutes=90,
        steps=(
            ("say", "the app says my parcel was delivered but I never received anything"),
        ),
        expect={"state": "out_for_delivery", "address_unchanged": True,
                "cases_include": [["duplicate_conflict", "open"]], "assistant_enabled": False},
    ),
    Scenario(
        key="attempts", what="already at the attempt limit",
        tracking="EX400077AE", channel="whatsapp", needs="refused", age_minutes=70,
        steps=(
            ("say", "can you try delivering my parcel again tomorrow?"),
            ("say", "yes, tomorrow please"),
        ),
        expect={"state": "failed", "address_unchanged": True,
                "cases_include": [["attempt_limit_reached", "open"]]},
    ),
    Scenario(
        key="nophone", what="no phone on file, on the website",
        tracking="EX400016AE", channel="web", needs="refused", age_minutes=45,
        steps=(
            ("verify", "EX400016AE"),
            ("say", "where is EX400016AE? and please change its delivery address to "
                    "Office 12, Tower 5, Al Majaz, Sharjah"),
            ("say", "yes, please change it"),
        ),
        expect={"state": "in_transit", "address_unchanged": True,
                "cases_include": [["no_phone_on_file", "open"]], "verified": False},
    ),
    Scenario(
        key="person", what="asks for a person; Ali takes it, answers, hands back",
        tracking="EX400044AE", channel="whatsapp", needs="allowed", age_minutes=30,
        steps=(
            ("say", "your app crashes every time I try to pay for the delivery. I want to talk "
                    "to a person"),
            ("staff", "Ali", "Hi, Ali here from 7X. Sorry about the app. Which phone are you on, "
                             "and does it crash before or after you enter the card number? I'll "
                             "pass it straight to the app team."),
            ("say", "iPhone. it crashes right after I tap pay"),
            ("staff", "Ali", "Thanks. Logged with the app team under your number; they'll message "
                             "you today. Your parcel itself is fine and still on its way."),
            ("resolve",),
            ("handback",),
        ),
        expect={"state": "failed", "address_unchanged": True,
                "cases": [["customer_request", "resolved"]], "assistant_enabled": True},
    ),
    Scenario(
        key="arabic", what="the reschedule, in Arabic",
        tracking="EX400027AE", channel="whatsapp", needs="allowed", age_minutes=15,
        steps=(
            ("say", "أين شحنتي؟"),
            ("say", "لا أستطيع الاستلام هذا الأسبوع، هل يمكن تأجيلها إلى يوم الخميس؟"),
            ("say", "نعم من فضلك"),
        ),
        expect={"state": "redelivery_scheduled", "scheduled_date": THURSDAY,
                "address_unchanged": True, "cases": [], "assistant_enabled": True},
    ),
    Scenario(
        key="webaddress", what="verified on the website, then the address is changed",
        tracking="EX400008AE", channel="web", needs="allowed", age_minutes=5,
        steps=(
            ("verify", "EX400008AE"),
            ("code",),
            ("say", "Hi, I've moved. Please deliver EX400008AE to Office 1104, Tower 2, "
                    "Business Bay, Dubai instead"),
            ("say", "yes, that's correct"),
        ),
        expect={"state": "in_transit", "address_contains": "Business Bay", "cases": [],
                "verified": True, "scheduled_date": None},
    ),
)

PICKER: tuple[Persona, ...] = (
    Persona("EX400006AE", "A normal parcel that can be moved", "allowed"),
    Persona("EX400019AE", "Cash on delivery, address change is blocked", "refused"),
    Persona("EX401001AE", "Two records that disagree about delivery", "unclear"),
    Persona("EX400101AE", "Already at the 3 attempt limit", "refused"),
    Persona("EX400033AE", "No phone on file, cannot be verified", "refused"),
    Persona("EX400009AE", "Already delivered", "refused"),
)

# What the Website pane hands a reviewer, who otherwise has no number to type.
WEB_TRY: tuple[tuple[str, str, bool], ...] = (
    ("EX400025AE", "a phone is on file, so a code is sent", True),
    ("EX400143AE", "no phone on file, so only the status shows", False),
)

STEP_KINDS = {"say", "verify", "code", "staff", "handback", "resolve"}
STEP_ARITY = {"say": 2, "verify": 2, "code": 1, "staff": 3, "handback": 1, "resolve": 1}
EXPECT_KEYS = {"state", "scheduled_date", "address_unchanged", "address_contains",
               "cases", "cases_include", "assistant_enabled", "verified"}


def profile(row) -> str:
    """What the record says can happen to it, in the cast's three words."""
    from . import gates   # imported here: cast is data, gates is the rules; keep the direction one way
    if row["flag_duplicate_conflict"]:
        return "unclear"
    return "allowed" if gates.evaluate(row)["can_change_address"] else "refused"


def validate(conn) -> list[str]:
    """
    Everything the docstring promises, checked against the code and the data. Returns the
    problems; empty means the cast is sound. demo.py refuses to record while this is non-empty,
    and reports it in check, so a re-cleaned file cannot leave a label telling a lie.
    """
    problems: list[str] = []
    seed = {sc.tracking for sc in SEED}
    picker = {p.tracking for p in PICKER}
    web = {t for t, _, _ in WEB_TRY}
    for a, b, name in ((seed, picker, "SEED and PICKER"), (seed, web, "SEED and WEB_TRY"),
                       (picker, web, "PICKER and WEB_TRY")):
        if a & b:
            problems.append(f"{name} share {sorted(a & b)}")
    if len({sc.key for sc in SEED}) != len(SEED):
        problems.append("SEED keys are not unique")
    for sc in SEED:
        if sc.channel not in ("whatsapp", "web"):
            problems.append(f"{sc.key}: channel {sc.channel!r}")
        for step in sc.steps:
            if not step:
                problems.append(f"{sc.key}: empty step")
                continue
            if step[0] not in STEP_KINDS:
                problems.append(f"{sc.key}: unknown step {step[0]!r}")
            elif len(step) != STEP_ARITY[step[0]]:
                problems.append(f"{sc.key}: step {step[0]!r} has {len(step)} elements, "
                                f"expected {STEP_ARITY[step[0]]}")
        for k in sc.expect:
            if k not in EXPECT_KEYS:
                problems.append(f"{sc.key}: unknown expectation {k!r}")

    def row(tn):
        return conn.execute("SELECT * FROM shipments WHERE tracking_number=?", (tn,)).fetchone()

    for tn in sorted(seed | picker | web):
        if row(tn) is None:
            problems.append(f"{tn} is not in the database")
    for sc in SEED:
        r = row(sc.tracking)
        if r is not None and profile(r) != sc.needs:
            problems.append(f"{sc.key}: needs {sc.needs}, the record says {profile(r)}")
    for p in PICKER:
        r = row(p.tracking)
        if r is not None and profile(r) != p.outcome:
            problems.append(f"{p.tracking}: labelled {p.outcome}, the record says {profile(r)}")
    for tn, _, has_phone in WEB_TRY:
        r = row(tn)
        if r is not None and bool(r["phone"]) != has_phone:
            problems.append(f"{tn}: labelled has_phone={has_phone}, the record says "
                            f"{bool(r['phone'])}")
    return problems


def scenario(key: str) -> Scenario:
    for sc in SEED:
        if sc.key == key:
            return sc
    raise KeyError(key)

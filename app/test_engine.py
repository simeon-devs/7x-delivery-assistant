"""
Step 1 verification. No UI, no model, no API key.

Proves four things:

  1. The gates computed live from the database agree with the numbers the cleaning layer
     produced. If these drift, one of the two is wrong and the whole safety story is shaky.
  2. An allowed action really changes a row.
  3. A blocked action really refuses, raises a case, and leaves the row untouched.
  4. Every one of those left a line in the log.

Run:  python -m app.test_engine
"""

from __future__ import annotations

from datetime import timedelta

from . import actions, db, gates
from .db import TODAY

PASS, FAIL = "  ok  ", " FAIL "
failures = 0


def check(label: str, got, want) -> None:
    global failures
    good = got == want
    if not good:
        failures += 1
    print(f"[{PASS if good else FAIL}] {label:<52} got={got!r:<28} want={want!r}")


def note(label: str, value) -> None:
    print(f"[ info ] {label:<52} {value}")


# ---------------------------------------------------------------------------

print("\n=== rebuilding the database from the cleaned file ===\n")
n = db.reset()
conn = db.connect()
note("shipments loaded", n)

# --- phone must be text, not a float (D-08)
sample = conn.execute(
    "SELECT phone FROM shipments WHERE phone IS NOT NULL LIMIT 1"
).fetchone()["phone"]
check("phone stored as E.164 text", sample.startswith("+") and "." not in sample, True)
note("phone sample", sample)


print("\n=== 1. do the live gates agree with the cleaning layer? ===\n")

rows = conn.execute("SELECT * FROM shipments").fetchall()
g = [gates.evaluate(r) for r in rows]

check("total shipments", len(rows), 840)
check("open", sum(x["is_open"] for x in g), 349)
check("can_reschedule", sum(x["can_reschedule"] for x in g), 262)
check("can_change_address", sum(x["can_change_address"] for x in g), 201)
check("requires_human among open",
      sum(x["requires_human"] for x in g if x["is_open"]), 87)

note("no phone on file",
     sum(1 for x in g if "no_phone_on_file" in x["block_codes"]))
note("attempt limit reached",
     sum(1 for x in g if "attempt_limit_reached" in x["block_codes"]))
note("duplicate conflict",
     sum(1 for x in g if "duplicate_conflict" in x["block_codes"]))


print("\n=== 2. an allowed action changes the row ===\n")

target = conn.execute("""
    SELECT * FROM shipments
    WHERE phone IS NOT NULL AND cod_amount_aed = 0 AND delivery_attempts < 3
      AND flag_duplicate_conflict = 0
      AND state IN ('failed','out_for_delivery','in_transit')
    LIMIT 1
""").fetchone()

with conn:
    conn.execute(
        """INSERT INTO sessions (id, channel, phone, customer_name, verified,
                                 assistant_enabled, created_at)
           VALUES ('s-test','whatsapp',?,?,1,1,?)""",
        (target["phone"], target["customer_name"], TODAY.isoformat()),
    )

tn = target["tracking_number"]
new_date = (TODAY + timedelta(days=2)).isoformat()
note("target parcel", f"{tn}  state={target['state']}  attempts={target['delivery_attempts']}")

with conn:
    res = actions.reschedule_delivery(conn, "s-test", tn, new_date)

check("reschedule returned ok", res["ok"], True)
after = conn.execute("SELECT * FROM shipments WHERE tracking_number=?", (tn,)).fetchone()
check("scheduled_date written to the row", after["scheduled_date"], new_date)
check("state moved to redelivery_scheduled", after["state"], "redelivery_scheduled")


print("\n=== 3. a blocked action refuses, and changes nothing ===\n")

# --- COD blocks an address change (D-07)
cod = conn.execute("""
    SELECT * FROM shipments
    WHERE phone IS NOT NULL AND cod_amount_aed > 0 AND delivery_attempts < 3
      AND flag_duplicate_conflict = 0
      AND state IN ('failed','out_for_delivery','in_transit')
    LIMIT 1
""").fetchone()

with conn:
    conn.execute("UPDATE sessions SET phone=?, customer_name=? WHERE id='s-test'",
                 (cod["phone"], cod["customer_name"]))
    res = actions.change_address(conn, "s-test", cod["tracking_number"],
                                 "Prism Tower, office 1204, Business Bay, Dubai")

check("COD address change refused", res["ok"], False)
check("a case was raised", bool(res["data"].get("case_id")), True)
note("reason given to the customer", res["reason"])
unchanged = conn.execute("SELECT delivery_address FROM shipments WHERE tracking_number=?",
                         (cod["tracking_number"],)).fetchone()
check("address untouched", unchanged["delivery_address"], cod["delivery_address"])

# --- but the same parcel CAN still be moved to another day
with conn:
    res2 = actions.reschedule_delivery(conn, "s-test", cod["tracking_number"], new_date)
check("same COD parcel can still be rescheduled", res2["ok"], True)

# --- attempt limit
limit = conn.execute("""
    SELECT * FROM shipments
    WHERE delivery_attempts >= 3 AND phone IS NOT NULL AND state NOT IN ('delivered','returned')
    LIMIT 1
""").fetchone()
with conn:
    conn.execute("UPDATE sessions SET phone=? WHERE id='s-test'", (limit["phone"],))
    res3 = actions.reschedule_delivery(conn, "s-test", limit["tracking_number"], new_date)
check("attempt limit refuses a reschedule", res3["ok"], False)
note("reason given to the customer", res3["reason"])

# --- no phone on file (the 71)
nophone = conn.execute(
    "SELECT * FROM shipments WHERE phone IS NULL AND state NOT IN ('delivered','returned') LIMIT 1"
).fetchone()
with conn:
    res4 = actions.reschedule_delivery(conn, "s-test", nophone["tracking_number"], new_date)
check("no phone on file refuses a reschedule", res4["ok"], False)
note("reason given to the customer", res4["reason"])

# --- a closed parcel
closed = conn.execute("SELECT * FROM shipments WHERE state='delivered' LIMIT 1").fetchone()
with conn:
    conn.execute("UPDATE sessions SET phone=? WHERE id='s-test'", (closed["phone"],))
    res5 = actions.reschedule_delivery(conn, "s-test", closed["tracking_number"], new_date)
check("a delivered parcel refuses a reschedule", res5["ok"], False)


print("\n=== 4. contradictory records carry a warning, not a status ===\n")

conflict = conn.execute(
    "SELECT * FROM shipments WHERE flag_duplicate_conflict = 1 LIMIT 1"
).fetchone()
view = actions.get_shipment(conn, None, conflict["tracking_number"])
check("conflicted parcel has NO status to recite", view["data"]["status"], "UNCLEAR")
check("and carries the sentence the customer must hear",
      "must_tell_customer" in view["data"], True)
note("sentence", view["data"].get("must_tell_customer"))

unreliable = conn.execute(
    "SELECT * FROM shipments WHERE flag_attempts_unreliable = 1 AND flag_duplicate_conflict = 0 LIMIT 1"
).fetchone()
if unreliable:
    v2 = actions.get_shipment(conn, None, unreliable["tracking_number"])
    check("unreliable attempts hidden from the model", v2["data"]["delivery_attempts"], "unknown")


print("\n=== 5. tracking is open, acting is not (A-07) ===\n")

anon = actions.get_shipment(conn, None, tn)
check("anyone can see the status", anon["ok"], True)
check("the status is there", bool(anon["data"]["status"]), True)
check("a note explains why nothing can be changed", "note" in anon["data"], True)
note("note shown", anon["data"]["note"])

# The model is never told what it may do. It finds out by attempting (A-12 / _view).
check("no permission flags reach the model",
      any(k.startswith("can_") for k in anon["data"]), False)

# And a conflicted parcel seen by an unverified viewer must still lead with the contradiction,
# not with a note about verification.
anon_conflict = actions.get_shipment(conn, None, conflict["tracking_number"])
check("contradiction still wins over the verification note",
      anon_conflict["data"]["must_tell_customer"].startswith("There are two records"), True)


print("\n=== 6. the date rules ===\n")

with conn:
    conn.execute("UPDATE sessions SET phone=? WHERE id='s-test'", (target["phone"],))
past = actions.reschedule_delivery(conn, "s-test", tn, (TODAY - timedelta(days=1)).isoformat())
check("a past date is refused", past["ok"], False)
far = actions.reschedule_delivery(conn, "s-test", tn, (TODAY + timedelta(days=40)).isoformat())
check("a date 40 days out is refused", far["ok"], False)
junk = actions.reschedule_delivery(conn, "s-test", tn, "next thursday")
check("unparseable date is refused", junk["ok"], False)


print("\n=== 7. everything left a trace ===\n")

log = conn.execute("SELECT * FROM action_log ORDER BY id").fetchall()
cases = conn.execute("SELECT * FROM cases ORDER BY id").fetchall()
check("log has entries", len(log) > 0, True)
check("every log line has a human sentence",
      all(r["detail"] and not r["detail"].isupper() for r in log), True)
note("log lines", len(log))
note("cases raised", len(cases))

print("\n  what the operations console will show:\n")
for r in log:
    mark = "done   " if r["outcome"] == "done" else "refused"
    print(f"    {mark}  {r['detail']}")

print("\n  the queue:\n")
for c in cases:
    print(f"    {c['id']}  {c['tracking_number']}  {c['reason_code']}")


print("\n" + "=" * 78)
if failures:
    print(f"  {failures} CHECK(S) FAILED")
else:
    print("  all checks passed")
print("=" * 78 + "\n")

conn.close()
raise SystemExit(1 if failures else 0)

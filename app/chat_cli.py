"""
Step 2 verification. A conversation in the terminal, no UI.

The test the whole prototype rests on: after the conversation, is the row different?
That is how tau-bench scores agents -- on the final state of the database, not on the
transcript -- and it is the line between an agent and a chatbot with a table in its context.

Prints the shipment row before and after, every tool call the model made, and the real token
usage so the cost is measured rather than guessed.

    python -m app.chat_cli                      pick a customer, talk to it
    python -m app.chat_cli --scenario cod       run a scripted scenario
    python -m app.chat_cli --list               show the scenarios
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys

from . import agent, db, gates

DIM, BOLD, RESET = "\033[2m", "\033[1m", "\033[0m"
GREEN, AMBER, BLUE = "\033[32m", "\033[33m", "\033[36m"

# Sonnet 5 list price per million tokens. Verify against anthropic.com/pricing before quoting
# these figures anywhere: this number ends up on a slide.
PRICE_IN, PRICE_CACHE_WRITE, PRICE_CACHE_READ, PRICE_OUT = 2.00, 2.50, 0.20, 10.00


# Each scenario names the kind of shipment to find, then the lines to send.
SCENARIOS = {
    "happy": {
        "what": "a normal open parcel that can be rescheduled",
        "sql": """SELECT * FROM shipments
                  WHERE phone IS NOT NULL AND cod_amount_aed = 0 AND delivery_attempts < 3
                    AND flag_duplicate_conflict = 0 AND flag_attempts_unreliable = 0
                    AND state IN ('failed','out_for_delivery','in_transit') LIMIT 1""",
        "lines": [
            "hi, where is my parcel?",
            "I won't be home this week until Thursday. can you move it?",
            "yes please",
        ],
    },
    "cod": {
        "what": "a cash-on-delivery parcel, address change should be refused",
        "sql": """SELECT * FROM shipments
                  WHERE phone IS NOT NULL AND cod_amount_aed > 0 AND delivery_attempts < 3
                    AND flag_duplicate_conflict = 0
                    AND state IN ('failed','out_for_delivery','in_transit') LIMIT 1""",
        "lines": [
            "I need this delivered to my office instead, not my home",
            "Prism Tower, office 1204, Business Bay, Dubai",
            "yes that's right, please change it",
        ],
    },
    "conflict": {
        "what": "a parcel whose two records disagree about delivery",
        "sql": "SELECT * FROM shipments WHERE flag_duplicate_conflict = 1 LIMIT 1",
        "lines": [
            "the app says my parcel was delivered but I never received anything",
        ],
    },
    "human": {
        "what": "customer asks for a person straight away",
        "sql": """SELECT * FROM shipments WHERE phone IS NOT NULL
                  AND state NOT IN ('delivered','returned') LIMIT 1""",
        "lines": ["I want to speak to a human being"],
    },
    "arabic": {
        "what": "the same reschedule, in Arabic",
        "sql": """SELECT * FROM shipments
                  WHERE phone IS NOT NULL AND cod_amount_aed = 0 AND delivery_attempts < 3
                    AND flag_duplicate_conflict = 0 AND flag_attempts_unreliable = 0
                    AND state IN ('failed','out_for_delivery','in_transit') LIMIT 1""",
        "lines": ["أين شحنتي؟", "لا أستطيع الاستلام اليوم، هل يمكن تأجيلها إلى يوم الخميس؟"],
    },
    "nophone": {
        "what": "no phone on file, cannot be verified (46 of the 349 open)",
        "sql": """SELECT * FROM shipments WHERE phone IS NULL
                  AND state NOT IN ('delivered','returned') LIMIT 1""",
        "lines": ["where is my parcel and can you change the address to Sharjah?"],
    },
}


def snapshot(conn, tn: str) -> dict:
    r = conn.execute("SELECT * FROM shipments WHERE tracking_number=?", (tn,)).fetchone()
    return {
        "state": r["state"],
        "scheduled_date": r["scheduled_date"],
        "delivery_address": r["delivery_address"],
        "attempts": r["delivery_attempts"],
    }


def show_tool_calls(calls: list[dict]) -> None:
    for c in calls:
        res = c["result"]
        mark = f"{GREEN}ok{RESET}" if res["ok"] else f"{AMBER}refused{RESET}"
        args = ", ".join(f"{k}={v!r}" for k, v in (c["input"] or {}).items())
        print(f"    {DIM}tool{RESET} {BLUE}{c['name']}{RESET}({args}) -> {mark}")
        if not res["ok"] and res.get("reason"):
            print(f"         {DIM}{res['reason']}{RESET}")
        if res.get("data", {}).get("case_id"):
            print(f"         {DIM}case {res['data']['case_id']}{RESET}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", choices=sorted(SCENARIOS))
    ap.add_argument("--channel", default="whatsapp", choices=["whatsapp", "web"])
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--fresh", action="store_true", help="rebuild the database first")
    args = ap.parse_args()

    if args.list:
        for k, v in SCENARIOS.items():
            print(f"  {k:<10} {v['what']}")
        return 0

    if args.fresh:
        db.reset()
    db.ensure()
    conn = db.connect()

    scenario = SCENARIOS[args.scenario] if args.scenario else SCENARIOS["happy"]
    row = conn.execute(scenario["sql"]).fetchone()
    if row is None:
        print("no shipment matched that scenario")
        return 1

    tn = row["tracking_number"]
    g = gates.evaluate(row)
    before = snapshot(conn, tn)

    session_id = "s-cli-" + secrets.token_hex(4)
    with conn:
        conn.execute(
            """INSERT INTO sessions (id, channel, phone, customer_name, verified,
                                     assistant_enabled, created_at)
               VALUES (?,?,?,?,?,1,?)""",
            (
                session_id,
                args.channel,
                row["phone"],
                row["customer_name"],
                # WhatsApp: the number is verified by the channel. Web would need a code first.
                1 if row["phone"] else 0,
                db.now(),
            ),
        )

    print(f"\n{BOLD}parcel {tn}{RESET}   {row['customer_name']}   {args.channel}")
    print(f"{DIM}  state={row['state']}  attempts={row['delivery_attempts']}  "
          f"cod={row['cod_amount_aed']}  reschedule={g['can_reschedule']}  "
          f"address={g['can_change_address']}{RESET}")
    print(f"{DIM}  before: {json.dumps(before)}{RESET}\n")

    lines = scenario["lines"] if args.scenario else None
    turn = 0
    total_in = total_out = 0
    total_cr = total_cw = 0

    while True:
        if lines is not None:
            if turn >= len(lines):
                break
            text = lines[turn]
            print(f"{BOLD}customer{RESET}  {text}")
        else:
            try:
                text = input(f"{BOLD}customer{RESET}  ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not text or text in {"quit", "exit"}:
                break
        turn += 1

        out = agent.respond(conn, session_id, text)
        u = out.get("usage") or {}
        total_in += u.get("input", 0)
        total_out += u.get("output", 0)
        total_cr += u.get("cache_read", 0)
        total_cw += u.get("cache_write", 0)

        if out["tool_calls"]:
            show_tool_calls(out["tool_calls"])
        if out["reply"]:
            print(f"{BOLD}7X{RESET}        {out['reply']}\n")
        else:
            print(f"{DIM}        [assistant is off -- a person has this conversation]{RESET}\n")

    after = snapshot(conn, tn)
    changed = {k: (before[k], after[k]) for k in before if before[k] != after[k]}

    print(f"{BOLD}{'-' * 70}{RESET}")
    print(f"  before : {json.dumps(before)}")
    print(f"  after  : {json.dumps(after)}")
    if changed:
        print(f"\n  {GREEN}THE RECORD CHANGED{RESET}")
        for k, (b, a) in changed.items():
            print(f"    {k}: {b!r}  ->  {a!r}")
    else:
        print(f"\n  {AMBER}record unchanged{RESET} (correct if the action was refused)")

    cases = conn.execute(
        "SELECT * FROM cases WHERE session_id=? ORDER BY id", (session_id,)
    ).fetchall()
    if cases:
        print("\n  queue:")
        for c in cases:
            print(f"    {c['id']}  {c['reason_code']}  {DIM}{c['reason_text'][:60]}{RESET}")

    log = conn.execute(
        "SELECT * FROM action_log WHERE session_id=? ORDER BY id", (session_id,)
    ).fetchall()
    if log:
        print("\n  trace:")
        for r in log:
            print(f"    {r['outcome']:<8} {r['detail']}")

    # Measured token counts, priced at the constants above.
    cost = (total_in * PRICE_IN + total_cw * PRICE_CACHE_WRITE
            + total_cr * PRICE_CACHE_READ + total_out * PRICE_OUT) / 1e6
    print(f"\n  {DIM}tokens: {total_in:,} in / {total_cr:,} cached / {total_out:,} out"
          f"   approx ${cost:.4f}{RESET}")
    print()
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

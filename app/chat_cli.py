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

The scenarios are the ones in cast.py -- the same eight the console opens with, and the same
six people the chat's picker offers. There is no second list here to drift from them: change a
line in the cast and the terminal, the seeded demo and the customer picker all change together.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import agent, cast, convo, db, gates

DIM, BOLD, RESET = "\033[2m", "\033[1m", "\033[0m"
GREEN, AMBER, BLUE = "\033[32m", "\033[33m", "\033[36m"

# Sonnet 5 list price per million tokens. Verify against anthropic.com/pricing before quoting
# these figures anywhere: this number ends up on a slide.
PRICE_IN, PRICE_CACHE_WRITE, PRICE_CACHE_READ, PRICE_OUT = 2.00, 2.50, 0.20, 10.00


def choose(conn) -> cast.Persona | None:
    """
    Interactive mode. The picker rows from the cast, named by the database -- the same six the
    customer chat offers, so the terminal and the browser start from the same people.
    """
    rows = []
    for person in cast.PICKER:
        r = conn.execute("SELECT customer_name FROM shipments WHERE tracking_number = ?",
                         (person.tracking,)).fetchone()
        if r is not None:
            rows.append((person, r["customer_name"]))
    if not rows:
        print("none of the picker rows are in this database")
        return None

    print(f"\n{BOLD}who are you?{RESET}")
    for i, (person, name) in enumerate(rows, 1):
        print(f"  {i}  {name or '—':<22} {DIM}{person.label}{RESET}")
    try:
        raw = input(f"\n{BOLD}pick{RESET}      ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
    if not raw.isdigit() or not 1 <= int(raw) <= len(rows):
        print("not one of those")
        return None
    return rows[int(raw) - 1][0]


def open_session(conn, channel: str, row) -> str:
    """
    The same door both surfaces use, so the terminal proves the real path and not a shortcut.

    On WhatsApp the number arrives already verified by the channel. On the web it has to be
    earned: a code goes to the number on the record and comes back the way the customer reads
    it off their phone. A row with no phone cannot be verified at all, which is the whole point
    of that scenario -- it stays unverified and the assistant has to cope.
    """
    tn = row["tracking_number"]
    with conn:
        sid = convo.new_session(conn, channel, row["phone"] if channel == "whatsapp" else None)

    if channel == "whatsapp":
        # One number can sit on several parcels. This conversation is about this one.
        with conn:
            conn.execute("UPDATE sessions SET focus_tracking = ? WHERE id = ?", (tn, sid))
        return sid

    with conn:
        started = convo.verify_start(conn, sid, tn)
    if not started["can_verify"]:
        print(f"{DIM}  web: not verified — {started['reason']}{RESET}")
        return sid
    with conn:
        done = convo.verify_confirm(conn, sid, started["demo_code"])
    print(f"{DIM}  web: code {started['demo_code']} sent to {started['masked_phone']}"
          f" — verified={done['verified']}{RESET}")
    return sid


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
    ap.add_argument("--scenario", choices=[sc.key for sc in cast.SEED])
    ap.add_argument("--channel", choices=["whatsapp", "web"],
                    help="override the channel the scenario was written for")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--fresh", action="store_true", help="rebuild the database first")
    args = ap.parse_args()

    if args.list:
        for sc in cast.SEED:
            print(f"  {sc.key:<11} {sc.channel:<9} {sc.what}")
        return 0

    if args.fresh:
        db.reset()
    db.ensure()
    conn = db.connect()

    # A scenario is a pinned row and the customer's lines. Without one, the picker rows are
    # offered and the conversation is typed by hand.
    if args.scenario:
        sc = next(s for s in cast.SEED if s.key == args.scenario)
        tn, channel = sc.tracking, args.channel or sc.channel
        # The staff replies and hand-backs in a seeded scenario belong to the console. Here the
        # assistant answers every line, which is what this tool is for.
        lines = [step[1] for step in sc.steps if step[0] == "say"]
    else:
        person = choose(conn)
        if person is None:
            return 1
        tn, channel, lines = person.tracking, args.channel or "whatsapp", None

    row = conn.execute("SELECT * FROM shipments WHERE tracking_number = ?", (tn,)).fetchone()
    if row is None:
        print(f"{tn} is not in this database. Run with --fresh, or re-clean the file.")
        return 1

    g = gates.evaluate(row)
    before = snapshot(conn, tn)
    session_id = open_session(conn, channel, row)

    print(f"\n{BOLD}parcel {tn}{RESET}   {row['customer_name']}   {channel}")
    print(f"{DIM}  state={row['state']}  attempts={row['delivery_attempts']}  "
          f"cod={row['cod_amount_aed']}  reschedule={g['can_reschedule']}  "
          f"address={g['can_change_address']}{RESET}")
    print(f"{DIM}  before: {json.dumps(before)}{RESET}\n")

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

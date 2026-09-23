"""
The demo state: eight conversations that already happened (A-26).

    python -m app.demo list                what is scripted, and what has been recorded
    python -m app.demo record --all        run every scenario against the real model, once
    python -m app.demo record cod arabic   re-record some; the rest replay first, so the case
                                           numbers a recorded reply mentions stay true
    python -m app.demo seed                reset, then replay every recording
    python -m app.demo check               compare the replayed state with what cast.SEED promises

A recording holds the customer's lines, the assistant's exact replies and tool calls, and the
staff steps. It does NOT hold tool results: on replay every tool call runs again through the
real door (actions.py), so the writes, the cases and the log are genuine, and identical on every
reset because the data is identical.

All eight live in one data/seed.json rather than eight files, because on a host they arrive as a
secret file and pasting one is a great deal less error-prone than pasting eight. They carry
names and addresses from the client's file, so like the shipment data they are never committed.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from . import agent, cast, convo, db

# Recording always writes here. Reading searches the same places the shipment file is searched,
# so a server can receive the bundle as a secret file.
SEED_WRITE = db.ROOT / "data" / "seed.json"

# Seconds between one event and the next, by the kind of the next event. A customer takes a
# while to type; the assistant answers in seconds; a person takes minutes. This is what gives
# the queue a spread of waiting times instead of eight rows all reading the same second.
CADENCE = {"customer": 75, "assistant": 8, "verify": 60, "code": 30,
           "staff": 120, "handback": 60, "resolve": 5}


def bundle_path() -> Path:
    """Resolved on every call, because recording creates the file this looks for."""
    found = db.data_candidates("seed.json", "SEED_BUNDLE")
    return next((p for p in found if p.exists()), SEED_WRITE)


def _load_all() -> dict:
    p = bundle_path()
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _load(key: str) -> dict | None:
    return _load_all().get(key)


def _store(key: str, rec: dict) -> None:
    bundle = _load_all()
    bundle[key] = rec
    SEED_WRITE.parent.mkdir(parents=True, exist_ok=True)
    SEED_WRITE.write_text(json.dumps(bundle, ensure_ascii=False, indent=1), encoding="utf-8")


def _sid(key: str) -> str:
    return f"s-seed-{key}"


def _snapshot(conn, tn: str) -> dict:
    r = conn.execute(
        "SELECT state, scheduled_date, delivery_address FROM shipments WHERE tracking_number=?",
        (tn,),
    ).fetchone()
    return {"state": r["state"], "scheduled_date": r["scheduled_date"],
            "address": r["delivery_address"]}


def _phone_for(conn, sc: cast.Scenario) -> str | None:
    row = conn.execute("SELECT phone FROM shipments WHERE tracking_number=?",
                       (sc.tracking,)).fetchone()
    if row is None:
        raise SystemExit(f"{sc.key}: {sc.tracking} is not in the database")
    return row["phone"] if sc.channel == "whatsapp" else None


# ---------------------------------------------------------------- recording (real model)


def _run_live(conn, sc: cast.Scenario) -> dict:
    """One scenario against the real model. Returns the recording; does not store it."""
    sid = _sid(sc.key)
    with conn:
        convo.new_session(conn, sc.channel, _phone_for(conn, sc), sid=sid)
    before = _snapshot(conn, sc.tracking)
    events: list[dict] = []

    for step in sc.steps:
        kind = step[0]
        if kind == "say":
            last = conn.execute("SELECT COALESCE(MAX(id), 0) m FROM messages").fetchone()["m"]
            # respond() runs its own transactions, so it must not be wrapped in one.
            out = agent.respond(conn, sid, step[1])
            if out.get("error"):
                raise SystemExit(f"{sc.key}: the model call failed: {out['error']}")
            events.append({"kind": "customer", "text": step[1]})
            print(f"    customer  {step[1]}")
            for r in conn.execute(
                """SELECT blocks FROM messages WHERE id > ? AND session_id = ?
                   AND role = 'assistant' ORDER BY id""", (last, sid)):
                blocks = json.loads(r["blocks"])
                events.append({"kind": "assistant", "blocks": blocks})
                for b in blocks:
                    if b["type"] == "tool_use":
                        print(f"        tool  {b['name']}({b.get('input') or {}})")
            print(f"    7X        {out['reply'] or '[silent: a person has this conversation]'}")
        elif kind == "verify":
            with conn:
                convo.verify_start(conn, sid, step[1])
            events.append({"kind": "verify", "tracking": step[1]})
        elif kind == "code":
            s = conn.execute("SELECT pending_code FROM sessions WHERE id=?", (sid,)).fetchone()
            with conn:
                convo.verify_confirm(conn, sid, s["pending_code"])
            events.append({"kind": "code"})
        elif kind == "staff":
            with conn:
                convo.staff_reply(conn, sid, step[1], step[2])
            events.append({"kind": "staff", "author": step[1], "text": step[2]})
            print(f"    {step[1]:<9} {step[2]}")
        elif kind == "handback":
            with conn:
                convo.set_assistant(conn, sid, True)
            events.append({"kind": "handback"})
        elif kind == "resolve":
            with conn:
                convo.resolve_open_cases(conn, sid)
            events.append({"kind": "resolve"})
        else:  # pragma: no cover
            raise ValueError(f"unknown step {step!r}")

    return {"key": sc.key, "tracking": sc.tracking, "channel": sc.channel,
            "recorded_at": db.now(), "before": before, "events": events}


def record(keys) -> None:
    """
    Record `keys` live, against the real model. Every other scenario in cast.SEED is replayed
    first from its own existing recording, in order, so a case number a freshly recorded reply
    mentions is the same number a full `--all` recording would have given it -- the case
    counter only advances in the order scenarios actually run.
    """
    keys = set(keys)
    db.reset()
    conn = db.connect()
    try:
        problems = cast.validate(conn)
        if problems:
            raise SystemExit("cast.py does not match the database:\n  " + "\n  ".join(problems))

        now = datetime.now()
        for sc in cast.SEED:
            if sc.key in keys:
                print(f"-- recording {sc.key}: {sc.what} --")
                rec = _run_live(conn, sc)
                _store(sc.key, rec)
            else:
                rec = _load(sc.key)
                if rec is None:
                    print(f"-- {sc.key}: no recording yet, skipped. Case numbers a live reply "
                          "mentions after this point may not match a full --all recording. --")
                    continue
                print(f"-- {sc.key}: replaying from its existing recording --")
                start = now - timedelta(minutes=sc.age_minutes)
                with conn:
                    _replay(conn, sc, rec, start)
    finally:
        db.set_clock(None)
        conn.close()


# ---------------------------------------------------------------- replay (no model, ever)


def _replay(conn, sc: cast.Scenario, rec: dict, start: datetime) -> None:
    """
    One recording, replayed for real. Nothing here calls the model: it inserts what the
    customer and the assistant said, then re-runs every recorded tool call through the real
    door (actions.py via agent.run_tool), so the shipment writes, the cases and the action log
    are genuine, and identical on every reset because the inputs are identical.

    The caller owns the transaction (seed() wraps every scenario in one; record() wraps one
    scenario at a time) -- this function only ever executes against the connection it is given.
    """
    sid = _sid(sc.key)
    with db.frozen(start):
        convo.new_session(conn, sc.channel, _phone_for(conn, sc), sid=sid)
        t = start
        for ev in rec["events"]:
            kind = ev["kind"]
            t = t + timedelta(seconds=CADENCE.get(kind, 30))
            db.set_clock(t)

            if kind == "customer":
                agent.save(conn, sid, role="customer", content=ev["text"], api_role="user",
                          blocks=[{"type": "text", "text": ev["text"]}])
            elif kind == "assistant":
                blocks = ev["blocks"]
                text = "".join(b.get("text", "") for b in blocks
                              if b.get("type") == "text").strip()
                agent.save(conn, sid, role="assistant", content=text, api_role="assistant",
                          blocks=blocks)
                results = []
                for b in blocks:
                    if b.get("type") != "tool_use":
                        continue
                    result = agent.run_tool(conn, sid, b["name"], b.get("input") or {})
                    results.append({"type": "tool_result", "tool_use_id": b["id"],
                                    "content": json.dumps(result), "is_error": not result["ok"]})
                    # Same rule the message endpoint uses: keep the pinned card pointed at
                    # whatever the assistant last touched.
                    tn = (b.get("input") or {}).get("tracking_number")
                    if not tn:
                        tn = (result.get("data") or {}).get("tracking_number")
                    if tn:
                        conn.execute("UPDATE sessions SET focus_tracking=? WHERE id=?", (tn, sid))
                if results:
                    agent.save(conn, sid, role="system", content="", api_role="user",
                              blocks=results)
            elif kind == "verify":
                convo.verify_start(conn, sid, ev["tracking"])
            elif kind == "code":
                s = conn.execute("SELECT pending_code FROM sessions WHERE id=?",
                                 (sid,)).fetchone()
                convo.verify_confirm(conn, sid, s["pending_code"])
            elif kind == "staff":
                convo.staff_reply(conn, sid, ev["author"], ev["text"])
            elif kind == "handback":
                convo.set_assistant(conn, sid, True)
            elif kind == "resolve":
                convo.resolve_open_cases(conn, sid)
            else:  # pragma: no cover
                raise ValueError(f"unknown event {ev!r}")


def seed() -> dict:
    """
    A-18 / A-26. Reset the shipment data, then replay every scenario that has a recording. The
    console opens mid-shift: eight real conversations, each stamped as having happened
    `age_minutes` ago, each backed by writes that just went through the real door again.
    """
    n = db.reset()
    conn = db.connect()
    now = datetime.now()
    seeded: list[str] = []
    missing: list[str] = []
    try:
        with conn:
            for sc in cast.SEED:
                rec = _load(sc.key)
                if rec is None:
                    missing.append(sc.key)
                    continue
                start = now - timedelta(minutes=sc.age_minutes)
                _replay(conn, sc, rec, start)
                seeded.append(sc.key)
    finally:
        db.set_clock(None)
        conn.close()
    return {"shipments": n, "seeded": seeded, "missing": missing}


def ensure() -> None:
    """
    Seed a first boot, or a boot whose database is empty because the data file had not arrived
    yet. Never a restart that already has data: whatever people did survives.
    """
    if db.DB_PATH.exists():
        conn = db.connect()
        try:
            has_table = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='shipments'"
            ).fetchone()[0]
            if has_table and conn.execute("SELECT COUNT(*) FROM shipments").fetchone()[0]:
                return
        finally:
            conn.close()
    try:
        seed()
    except RuntimeError:
        db.ensure()     # no data file: builds the empty schema and logs why


# ---------------------------------------------------------------- check


def check() -> int:
    """
    Compare the replayed state against what cast.SEED promises. Prints one line per problem
    cast.validate() found, then one line per scenario. Returns the number of failures; 0 means
    the demo is healthy.
    """
    conn = db.connect()
    failures = 0
    try:
        for problem in cast.validate(conn):
            print(f"FAIL cast {problem}")
            failures += 1

        for sc in cast.SEED:
            rec = _load(sc.key)
            if rec is None:
                print(f"{sc.key:<12} no recording")
                continue

            sid = _sid(sc.key)
            s = conn.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
            if s is None:
                print(f"{sc.key:<12} no session (run seed first)")
                failures += 1
                continue

            row = conn.execute("SELECT * FROM shipments WHERE tracking_number=?",
                               (sc.tracking,)).fetchone()
            exp = sc.expect
            problems: list[str] = []

            if "state" in exp and row["state"] != exp["state"]:
                problems.append(f"state={row['state']!r} want {exp['state']!r}")
            if "scheduled_date" in exp and row["scheduled_date"] != exp["scheduled_date"]:
                problems.append(f"scheduled_date={row['scheduled_date']!r} "
                                f"want {exp['scheduled_date']!r}")
            if exp.get("address_unchanged") and row["delivery_address"] != rec["before"]["address"]:
                problems.append(f"address changed: {rec['before']['address']!r} -> "
                                f"{row['delivery_address']!r}")
            if "address_contains" in exp and exp["address_contains"] not in (row["delivery_address"] or ""):
                problems.append(f"address={row['delivery_address']!r} does not contain "
                                f"{exp['address_contains']!r}")

            if "cases" in exp or "cases_include" in exp:
                have = sorted((c["reason_code"], c["status"]) for c in conn.execute(
                    "SELECT reason_code, status FROM cases WHERE session_id=?", (sid,)))
                if "cases" in exp:
                    want = sorted(tuple(x) for x in exp["cases"])
                    if have != want:
                        problems.append(f"cases={have} want {want}")
                if "cases_include" in exp:
                    want_inc = [tuple(x) for x in exp["cases_include"]]
                    missing_cases = [w for w in want_inc if w not in have]
                    if missing_cases:
                        problems.append(f"cases missing {missing_cases} (have {have})")

            if "assistant_enabled" in exp and bool(s["assistant_enabled"]) != exp["assistant_enabled"]:
                problems.append(f"assistant_enabled={bool(s['assistant_enabled'])} "
                                f"want {exp['assistant_enabled']}")
            if "verified" in exp and bool(s["verified"]) != exp["verified"]:
                problems.append(f"verified={bool(s['verified'])} want {exp['verified']}")

            if problems:
                failures += 1
                print(f"{sc.key:<12} FAIL  " + "; ".join(problems))
            else:
                print(f"{sc.key:<12} ok")
    finally:
        conn.close()
    return failures


# ---------------------------------------------------------------- cli


def main() -> int:
    parser = argparse.ArgumentParser(
        description="The demo state: eight scripted conversations, recorded once, replayed at "
                    "every reset (A-26)."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="what is scripted, and what has been recorded")

    p_record = sub.add_parser("record", help="run scenarios against the real model, once")
    p_record.add_argument("keys", nargs="*", help="scenario keys to record live")
    p_record.add_argument("--all", action="store_true", help="record every scenario live")

    sub.add_parser("seed", help="reset, then replay every recording")
    sub.add_parser("check", help="compare the replayed state with what cast.SEED promises")

    args = parser.parse_args()
    valid = {sc.key for sc in cast.SEED}

    if args.cmd == "list":
        bundle = _load_all()
        for sc in cast.SEED:
            recorded = "recorded" if sc.key in bundle else "not recorded"
            print(f"{sc.key:<12} {sc.tracking:<12} {sc.channel:<8} {sc.age_minutes:>4}m  "
                 f"{recorded}")
        return 0

    if args.cmd == "record":
        if args.all:
            keys = set(valid)
        elif args.keys:
            keys = set(args.keys)
        else:
            parser.error("record needs scenario keys, or --all")
            return 2   # pragma: no cover -- parser.error() already exits
        unknown = keys - valid
        if unknown:
            parser.error(f"unknown scenario keys: {sorted(unknown)}")
            return 2   # pragma: no cover
        record(keys)
        return 0

    if args.cmd == "seed":
        out = seed()
        print(f"shipments: {out['shipments']}  seeded: {out['seeded']}  "
             f"missing: {out['missing']}")
        return 0

    if args.cmd == "check":
        return 1 if check() else 0

    return 1  # pragma: no cover -- argparse enforces a valid subcommand


if __name__ == "__main__":
    sys.exit(main())

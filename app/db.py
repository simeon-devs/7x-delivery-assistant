"""
Database for the 7X delivery assistant prototype.

Loads the cleaned shipment file into SQLite so that actions are real writes against a real
store, not edits to an in-memory object. This matters: the prototype is judged on whether a
record is genuinely different after a conversation, not on what the assistant said.

Design notes
------------
A-17  One clock. TODAY is defined once, here, and imported everywhere.
A-18  reset() is a first-class function, built now rather than bolted on the night before.

The shipments table stores FACTS (state, attempts, COD, phone, flags), never the derived
permission columns from the CSV. Permissions are recomputed from the facts on every read by
gates.py. A frozen `can_reschedule` boolean would go stale the moment an action changed the
record, which is the exact bug the whole design is trying to avoid.
"""

from __future__ import annotations

import csv
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path


# ---------------------------------------------------------------- one clock (A-17)

TODAY = date(2026, 9, 22)

# ---------------------------------------------------------------- the other clock
#
# TODAY is the date the shipment dates are read against (A-17). now() is the moment an action,
# a message or a case actually happens: the trace is a log, so it carries real timestamps.
# set_clock() freezes now() -- used by the demo replay (A-26) so a conversation recorded once
# can be stamped as having happened two hours ago. Nothing else may call it.

_CLOCK: datetime | None = None


def now() -> str:
    """ISO timestamp to the second, real unless the clock is frozen."""
    return (_CLOCK or datetime.now()).isoformat(timespec="seconds")


def set_clock(at: datetime | None) -> None:
    global _CLOCK
    _CLOCK = at


@contextmanager
def frozen(at: datetime):
    """Freeze now() for the duration, and restore it whatever happens. The replay ticks the
    clock forward inside this with set_clock(); the guard is so an exception cannot leave a
    live server stamping the past."""
    global _CLOCK
    prior, _CLOCK = _CLOCK, at
    try:
        yield
    finally:
        _CLOCK = prior


def next_weekday(weekday: int) -> date:
    """The next such day strictly after TODAY. Monday is 0, so Thursday is 3."""
    return TODAY + timedelta(days=(weekday - TODAY.weekday()) % 7 or 7)


ROOT = Path(__file__).resolve().parent.parent

# SEVENX_DB lets a host put the database on a writable disk of its own choosing.
DB_PATH = Path(os.environ.get("SEVENX_DB") or ROOT / "data" / "7x.db")


def data_candidates(filename: str, env_var: str) -> list[Path]:
    """
    Every place a data file might be, best first.

    These files are derived from the client's confidential spreadsheet, so they are not in git
    and a server has to receive them another way. Different hosts drop them in different
    places -- Render mounts a secret file at /etc/secrets and also puts one in the project
    root -- and guessing wrong looks exactly like the file never arriving. So look in all of
    them, and when none has it, say every path that was tried.
    """
    out = [Path(os.environ[env_var])] if os.environ.get(env_var) else []
    out += [Path("/etc/secrets") / filename, ROOT / "data" / filename, ROOT / filename]
    seen, unique = set(), []
    for p in out:
        if str(p) not in seen:
            seen.add(str(p))
            unique.append(p)
    return unique


def _resolve(filename: str, env_var: str) -> Path:
    found = data_candidates(filename, env_var)
    return next((p for p in found if p.exists()), found[0])


SHIPMENTS_TRIED = data_candidates("shipments_clean.csv", "SHIPMENTS_CSV")
SOURCE_CSV = _resolve("shipments_clean.csv", "SHIPMENTS_CSV")
# The rows the cleaning kept out. Not needed to run, but without it the data readiness page
# cannot show that 866 went in and 840 came out, which is the whole point of that page.
QUARANTINE_CSV = _resolve("shipments_quarantine.csv", "QUARANTINE_CSV")


SCHEMA = """
CREATE TABLE shipments (
    tracking_number         TEXT PRIMARY KEY,
    customer_name           TEXT,
    emirate                 TEXT,
    service_type            TEXT,
    weight_kg               REAL,
    notes                   TEXT,

    state                   TEXT NOT NULL,
    raw_status              TEXT,
    delivery_attempts       INTEGER NOT NULL DEFAULT 0,

    phone                   TEXT,
    delivery_address        TEXT,
    cod_amount_aed          REAL NOT NULL DEFAULT 0,

    shipment_date           TEXT,
    shipment_date_format    TEXT,          -- which format it was parsed with (D-04)
    shipment_date_raw       TEXT,          -- the original string, kept beside the parsed value
    last_attempt_date       TEXT,
    last_attempt_date_format TEXT,
    last_attempt_date_raw   TEXT,
    scheduled_date          TEXT,          -- set by a reschedule; NULL until then

    flag_impossible_dates   INTEGER NOT NULL DEFAULT 0,
    flag_future_date        INTEGER NOT NULL DEFAULT 0,
    flag_attempts_unreliable INTEGER NOT NULL DEFAULT 0,
    flag_missing_phone      INTEGER NOT NULL DEFAULT 0,
    flag_missing_address    INTEGER NOT NULL DEFAULT 0,
    flag_duplicate_conflict INTEGER NOT NULL DEFAULT 0,
    data_confidence         TEXT NOT NULL DEFAULT 'clean',

    updated_at              TEXT
);

CREATE INDEX idx_shipments_phone ON shipments(phone);

CREATE TABLE sessions (
    id                 TEXT PRIMARY KEY,
    channel            TEXT NOT NULL,        -- 'web' | 'whatsapp'
    phone              TEXT,                 -- NULL until verified
    customer_name      TEXT,
    verified           INTEGER NOT NULL DEFAULT 0,
    assistant_enabled  INTEGER NOT NULL DEFAULT 1,   -- A-04 toggle
    pending_code       TEXT,                 -- web channel only
    pending_tracking   TEXT,
    focus_tracking     TEXT,                 -- the parcel pinned on screen
    created_at         TEXT NOT NULL
);

CREATE TABLE messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL,
    role        TEXT NOT NULL,        -- 'customer' | 'assistant' | 'staff' | 'system'
    author      TEXT,                 -- staff name, when role='staff'
    content     TEXT NOT NULL,        -- plain text, for display
    blocks      TEXT,                 -- the raw API content blocks, for rebuilding history
    api_role    TEXT,                 -- 'user' | 'assistant', NULL for notices
    created_at  TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX idx_messages_session ON messages(session_id, id);

CREATE TABLE cases (
    id               TEXT PRIMARY KEY,     -- C-1047
    session_id       TEXT,
    tracking_number  TEXT,
    reason_code      TEXT NOT NULL,
    reason_text      TEXT NOT NULL,
    customer_request TEXT,                 -- what they asked for, so staff need not re-ask
    status           TEXT NOT NULL DEFAULT 'open',   -- open | resolved
    created_at       TEXT NOT NULL,
    resolved_at      TEXT
);

CREATE TABLE action_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT,
    tracking_number TEXT,
    action          TEXT NOT NULL,
    outcome         TEXT NOT NULL,        -- done | refused
    detail          TEXT NOT NULL,        -- a human sentence (A-22)
    params          TEXT,                 -- json
    created_at      TEXT NOT NULL
);

CREATE TABLE counters (
    name  TEXT PRIMARY KEY,
    value INTEGER NOT NULL
);
"""


# ---------------------------------------------------------------- connection


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # The console polls while the chat writes. WAL lets a reader and a writer coexist; timeout=5
    # is the busy timeout, so a second writer waits up to five seconds instead of failing.
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


# ---------------------------------------------------------------- loading


def _clean_text(value) -> str | None:
    """A CSV field, or None when it is blank. Every value off the reader is a string."""
    s = (value or "").strip()
    return s or None


def _phone_to_text(value) -> str | None:
    """
    D-08: the source column is float64, which is wrong for a phone number. A float loses
    leading zeros and risks precision artefacts on long numbers. Cast to E.164 text.

    The CSV round-trip re-floated the column that clean_shipments.py had already fixed, so
    this runs again here rather than trusting the file: a value may arrive as 971551161559.0.
    """
    s = (value or "").strip()
    if s.endswith(".0"):
        s = s[:-2]
    s = "".join(ch for ch in s if ch.isdigit())
    return "+" + s if s else None


def _as_int_flag(value) -> int:
    """A boolean column written by pandas reads back as True/False; a hand-written one as 1/0."""
    return 1 if (value or "").strip().lower() in {"true", "1", "yes"} else 0


def _as_float(value) -> float | None:
    s = (value or "").strip()
    return float(s) if s else None


def _as_int(value) -> int:
    """Counts survive the round trip as 2 or as 2.0, depending on who wrote the file."""
    s = (value or "").strip()
    return int(float(s)) if s else 0


def load_shipments(conn: sqlite3.Connection) -> int:
    """
    The cleaned file into SQLite.

    Read with the standard library rather than pandas. The running app needs no dataframe --
    this is 840 rows read once at boot -- and pandas plus numpy is 109 MB of wheels to install
    on a host for one read_csv. The analysis scripts, which genuinely do need it, still use it.
    """
    if not SOURCE_CSV.exists():
        # Fail with the fix rather than a bare traceback: this is the one file a fresh server
        # will not have, and the message is the first thing anyone deploying will read.
        tried = "\n  ".join(str(p) for p in SHIPMENTS_TRIED)
        raise RuntimeError(
            "No shipment data. The cleaned file is not in git on purpose. Looked in:\n  "
            + tried
            + "\nOn Render, add a secret file named shipments_clean.csv. Locally, run "
              "`python -m analysis.clean_shipments` to rebuild it from the source spreadsheet."
        )
    with SOURCE_CSV.open(newline="", encoding="utf-8") as fh:
        source = list(csv.DictReader(fh))

    rows = []
    for r in source:
        rows.append(
            (
                (r["tracking_number"] or "").strip(),
                _clean_text(r["customer_name"]),
                _clean_text(r["emirate"]),
                _clean_text(r["service_type"]),
                _as_float(r["weight_kg"]),
                _clean_text(r["notes"]),
                (r["state"] or "").strip(),
                _clean_text(r["raw_status"]),
                _as_int(r["delivery_attempts"]),
                _phone_to_text(r["phone"]),
                _clean_text(r["delivery_address"]),
                _as_float(r["cod_amount_aed"]) or 0.0,
                _clean_text(r["shipment_date"]),
                _clean_text(r["shipment_date_format"]),
                _clean_text(r["shipment_date_raw"]),
                _clean_text(r["last_attempt_date"]),
                _clean_text(r["last_attempt_date_format"]),
                _clean_text(r["last_attempt_date_raw"]),
                None,  # scheduled_date
                _as_int_flag(r["flag_impossible_dates"]),
                _as_int_flag(r["flag_future_date"]),
                _as_int_flag(r["flag_attempts_unreliable"]),
                _as_int_flag(r["flag_missing_phone"]),
                _as_int_flag(r["flag_missing_address"]),
                _as_int_flag(r["flag_duplicate_conflict"]),
                _clean_text(r["data_confidence"]) or "clean",
                None,  # updated_at: loaded, not written
            )
        )

    conn.executemany(
        """INSERT INTO shipments (
               tracking_number,
               customer_name,
               emirate,
               service_type,
               weight_kg,
               notes,
               state,
               raw_status,
               delivery_attempts,
               phone,
               delivery_address,
               cod_amount_aed,
               shipment_date,
               shipment_date_format,
               shipment_date_raw,
               last_attempt_date,
               last_attempt_date_format,
               last_attempt_date_raw,
               scheduled_date,
               flag_impossible_dates,
               flag_future_date,
               flag_attempts_unreliable,
               flag_missing_phone,
               flag_missing_address,
               flag_duplicate_conflict,
               data_confidence,
               updated_at
           ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )
    return len(rows)


def reset() -> int:
    """
    A-18. Drop everything and reload from the cleaned file. One call, used by the demo reset
    button and by every test. Returns the number of shipments loaded.

    Rebuilt through SQLite rather than by deleting the file, so a connection that is already
    open sees the new content on its next transaction instead of writing into an orphan.
    """
    return _rebuild(load=True)


def _rebuild(load: bool) -> int:
    """
    Empty tables, then the data if it is wanted and present.

    `executescript` commits as it goes, so the schema is already on disk by the time the load
    runs. That is why this is one function: a load that fails must leave a database the empty
    path can finish, not a half-built one it would trip over.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = connect()
    conn.execute("PRAGMA foreign_keys = OFF")   # must be outside a transaction; messages -> sessions
    try:
        with conn:
            for (name,) in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall():
                conn.execute(f'DROP TABLE IF EXISTS "{name}"')
            conn.executescript(SCHEMA)
            n = load_shipments(conn) if load else 0
            conn.execute("INSERT INTO counters (name, value) VALUES ('case', 1000)")
        conn.execute("PRAGMA foreign_keys = ON")
    finally:
        conn.close()
    return n


def ensure() -> None:
    """
    Create and load the database if it does not exist yet.

    If the cleaned file has not reached this machine, build the empty schema and carry on. A
    server that starts, serves, and reports nought shipments can be fixed by whoever is looking
    at it; one that dies while importing only restarts for ever, and on a host that is the
    difference between a message you can read and a deploy that just says "failed".
    """
    if DB_PATH.exists() and not _is_empty():
        return
    # An empty database means either a first boot, or a boot that happened before the data
    # file arrived. Either way, try the load again: a server that gets its file on the second
    # deploy should come up with data, not stay empty because a file already existed.
    try:
        reset()
    except RuntimeError as e:
        print(f"STARTUP: {e}", flush=True)
        if not DB_PATH.exists():
            _rebuild(load=False)


def _is_empty() -> bool:
    conn = connect()
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='shipments'"
        ).fetchone()
        if row is None:
            return True
        return conn.execute("SELECT COUNT(*) FROM shipments").fetchone()[0] == 0
    finally:
        conn.close()


def secrets_seen() -> dict:
    """
    What is actually on disk where a host might have put the data, names and sizes only.

    A deploy that cannot find its file needs to know whether the file is absent, misnamed or
    empty, and those look identical from the outside. Filenames are not secret; contents are
    never read here.
    """
    out = {}
    for d in (Path("/etc/secrets"), ROOT, ROOT / "data"):
        try:
            out[str(d)] = sorted(
                f"{p.name} ({p.stat().st_size} bytes)"
                for p in d.iterdir() if p.is_file() and not p.name.startswith(".")
            )[:25]
        except OSError as e:
            out[str(d)] = [f"unreadable: {e.strerror}"]
    return out


# ---------------------------------------------------------------- helpers


def next_case_id(conn: sqlite3.Connection) -> str:
    """Readable case numbers a customer could quote on a phone call (A-21)."""
    cur = conn.execute(
        "UPDATE counters SET value = value + 1 WHERE name='case' RETURNING value"
    )
    value = cur.fetchone()[0]
    return f"C-{value}"


def log_action(
    conn: sqlite3.Connection,
    *,
    session_id: str | None,
    tracking_number: str | None,
    action: str,
    outcome: str,
    detail: str,
    params: dict | None = None,
    when: str | None = None,
) -> None:
    conn.execute(
        """INSERT INTO action_log
           (session_id, tracking_number, action, outcome, detail, params, created_at)
           VALUES (?,?,?,?,?,?,?)""",
        (
            session_id,
            tracking_number,
            action,
            outcome,
            detail,
            json.dumps(params or {}),
            # A timestamp, not a date: the log is real-clock (see now()).
            when or now(),
        ),
    )


if __name__ == "__main__":
    n = reset()
    print(f"loaded {n} shipments into {DB_PATH}")

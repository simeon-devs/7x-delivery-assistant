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

import json
import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------- one clock (A-17)

TODAY = date(2026, 9, 22)

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "7x.db"
SOURCE_CSV = ROOT / "data" / "shipments_clean.csv"


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
    last_attempt_date       TEXT,
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
    created_at         TEXT NOT NULL
);

CREATE TABLE messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL,
    role        TEXT NOT NULL,        -- 'customer' | 'assistant' | 'staff' | 'system'
    author      TEXT,                 -- staff name, when role='staff'
    content     TEXT NOT NULL,
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
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------------- loading


def _phone_to_text(value) -> str | None:
    """
    D-08: the source column is float64, which is wrong for a phone number. A float loses
    leading zeros and risks precision artefacts on long numbers. Cast to E.164 text.

    The CSV round-trip re-floated the column that clean_shipments.py had already fixed, so
    this runs again here rather than trusting the file.
    """
    if value is None or pd.isna(value):
        return None
    s = str(value).strip()
    if s.endswith(".0"):
        s = s[:-2]
    s = "".join(ch for ch in s if ch.isdigit())
    if not s:
        return None
    return "+" + s


def _clean_text(value) -> str | None:
    if value is None or pd.isna(value):
        return None
    s = str(value).strip()
    return s or None


def _as_int_flag(value) -> int:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0
    if isinstance(value, str):
        return 1 if value.strip().lower() in {"true", "1", "yes"} else 0
    return 1 if bool(value) else 0


def load_shipments(conn: sqlite3.Connection) -> int:
    df = pd.read_csv(SOURCE_CSV)
    now = TODAY.isoformat()
    rows = []

    for r in df.itertuples(index=False):
        rows.append(
            (
                str(r.tracking_number).strip(),
                _clean_text(r.customer_name),
                _clean_text(r.emirate),
                _clean_text(r.service_type),
                None if pd.isna(r.weight_kg) else float(r.weight_kg),
                _clean_text(r.notes),
                str(r.state).strip(),
                _clean_text(r.raw_status),
                0 if pd.isna(r.delivery_attempts) else int(r.delivery_attempts),
                _phone_to_text(r.phone),
                _clean_text(r.delivery_address),
                0.0 if pd.isna(r.cod_amount_aed) else float(r.cod_amount_aed),
                _clean_text(r.shipment_date),
                _clean_text(r.last_attempt_date),
                None,  # scheduled_date
                _as_int_flag(r.flag_impossible_dates),
                _as_int_flag(r.flag_future_date),
                _as_int_flag(r.flag_attempts_unreliable),
                _as_int_flag(r.flag_missing_phone),
                _as_int_flag(r.flag_missing_address),
                _as_int_flag(r.flag_duplicate_conflict),
                _clean_text(r.data_confidence) or "clean",
                now,
            )
        )

    conn.executemany(
        """INSERT INTO shipments (
               tracking_number, customer_name, emirate, service_type, weight_kg, notes,
               state, raw_status, delivery_attempts,
               phone, delivery_address, cod_amount_aed,
               shipment_date, last_attempt_date, scheduled_date,
               flag_impossible_dates, flag_future_date, flag_attempts_unreliable,
               flag_missing_phone, flag_missing_address, flag_duplicate_conflict,
               data_confidence, updated_at
           ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )
    return len(rows)


def reset() -> int:
    """
    A-18. Drop everything and reload from the cleaned file. One call, used by the demo reset
    button and by every test. Returns the number of shipments loaded.
    """
    if DB_PATH.exists():
        DB_PATH.unlink()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = connect()
    with conn:
        conn.executescript(SCHEMA)
        n = load_shipments(conn)
        conn.execute("INSERT INTO counters (name, value) VALUES ('case', 1000)")
    conn.close()
    return n


def ensure() -> None:
    """Create and load the database if it does not exist yet."""
    if not DB_PATH.exists():
        reset()


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
            when or TODAY.isoformat(),
        ),
    )


if __name__ == "__main__":
    n = reset()
    print(f"loaded {n} shipments into {DB_PATH}")

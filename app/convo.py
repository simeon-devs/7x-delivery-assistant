"""
What happens to a conversation outside the model: opening one, verifying it, a person replying,
handing back, resolving.

main.py's endpoints call these, and so does the demo replay (demo.py), so a seeded conversation
is made by exactly the code a live one is. Every function takes an open connection and runs
inside the caller's transaction; none commits.
"""

from __future__ import annotations

import secrets

from . import db, gates


def mask(phone: str | None) -> str | None:
    if not phone:
        return None
    return phone[:7] + " ••• " + phone[-4:]


def notice(conn, sid: str, text: str) -> None:
    conn.execute(
        "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, 'notice', ?, ?)",
        (sid, text, db.now()),
    )


def new_session(conn, channel: str, phone: str | None = None, sid: str | None = None) -> str:
    """
    A-23. On WhatsApp the number arrives already verified by the channel, so the session is
    born verified and pointed at the customer's open parcel. On the web it knows nothing.
    """
    sid = sid or "s-" + secrets.token_hex(4)
    name, verified, focus = None, 0, None
    if channel == "whatsapp" and phone:
        row = conn.execute(
            """SELECT customer_name, tracking_number FROM shipments WHERE phone = ?
               ORDER BY CASE WHEN state IN ('delivered','returned') THEN 1 ELSE 0 END LIMIT 1""",
            (phone,),
        ).fetchone()
        name = row["customer_name"] if row else None
        focus = row["tracking_number"] if row else None
        verified = 1
    conn.execute(
        """INSERT INTO sessions (id, channel, phone, customer_name, verified,
                                 assistant_enabled, focus_tracking, created_at)
           VALUES (?,?,?,?,?,1,?,?)""",
        (sid, channel, phone, name, verified, focus, db.now()),
    )
    if verified:
        notice(conn, sid, f"Verified by WhatsApp · {mask(phone)}")
    return sid


def verify_start(conn, sid: str, tracking: str) -> dict:
    """
    A-06. The customer types ONE thing, the tracking number. The phone is read off the record
    and the code goes TO THAT NUMBER, never to one they type. Someone holding the parcel can read
    the masked number off the screen; they cannot receive the message.

    Raises LookupError when there is no such parcel.
    """
    row = conn.execute(
        "SELECT * FROM shipments WHERE tracking_number = ?", (tracking.strip().upper(),)
    ).fetchone()
    if row is None:
        raise LookupError("I can't find a parcel with that tracking number.")
    tn = row["tracking_number"]
    if not row["phone"]:
        # One of the 46 open shipments with no phone on file. Tracking only, and say why.
        conn.execute("UPDATE sessions SET focus_tracking=? WHERE id=?", (tn, sid))
        return {"can_verify": False, "tracking_number": tn,
                "reason": gates.REASON_TEXT["no_phone_on_file"]}
    code = f"{secrets.randbelow(9000) + 1000}"
    conn.execute(
        "UPDATE sessions SET pending_code=?, pending_tracking=?, focus_tracking=? WHERE id=?",
        (code, tn, tn, sid),
    )
    # The demo cannot send a real SMS. Label it rather than hide it (A-06).
    return {"can_verify": True, "tracking_number": tn, "masked_phone": mask(row["phone"]),
            "demo_code": code}


def verify_confirm(conn, sid: str, code: str) -> dict:
    s = conn.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
    if s is None:
        raise LookupError("no such session")
    if not s["pending_code"] or (code or "").strip() != s["pending_code"]:
        return {"verified": False, "reason": "That code doesn't match. Try again."}
    row = conn.execute(
        "SELECT * FROM shipments WHERE tracking_number=?", (s["pending_tracking"],)
    ).fetchone()
    if row is None:
        raise LookupError("I can't find a parcel with that tracking number.")
    conn.execute(
        """UPDATE sessions SET verified=1, phone=?, customer_name=?, pending_code=NULL
           WHERE id=?""",
        (row["phone"], row["customer_name"], sid),
    )
    notice(conn, sid, f"Verified · {mask(row['phone'])}")
    n = conn.execute("SELECT COUNT(*) n FROM shipments WHERE phone=?",
                     (row["phone"],)).fetchone()["n"]
    return {"verified": True, "customer_name": row["customer_name"], "parcel_count": n}


def staff_reply(conn, sid: str, author: str, text: str) -> None:
    """A-04. A person replies into the customer's own conversation and the assistant stands
    down in that thread. The first reply announces the person, so the customer knows."""
    first = conn.execute(
        "SELECT COUNT(*) n FROM messages WHERE session_id = ? AND role = 'staff'", (sid,)
    ).fetchone()["n"] == 0
    if first:
        notice(conn, sid, f"{author} from 7X joined this conversation")
    conn.execute(
        """INSERT INTO messages (session_id, role, author, content, created_at)
           VALUES (?, 'staff', ?, ?, ?)""",
        (sid, author, text, db.now()),
    )
    conn.execute("UPDATE sessions SET assistant_enabled = 0 WHERE id = ?", (sid,))


def set_assistant(conn, sid: str, enabled: bool) -> None:
    """The toggle. Manual only: no timeout ever turns the assistant back on, because a person
    switched it off for a reason."""
    conn.execute("UPDATE sessions SET assistant_enabled = ? WHERE id = ?",
                 (1 if enabled else 0, sid))
    if enabled:
        notice(conn, sid, "Handed back to the assistant")


def resolve_case(conn, case_id: str) -> int:
    cur = conn.execute(
        "UPDATE cases SET status='resolved', resolved_at=? WHERE id=? AND status='open'",
        (db.now(), case_id),
    )
    return cur.rowcount


def resolve_open_cases(conn, sid: str) -> int:
    cur = conn.execute(
        "UPDATE cases SET status='resolved', resolved_at=? WHERE session_id=? AND status='open'",
        (db.now(), sid),
    )
    return cur.rowcount

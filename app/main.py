"""
The web server.

One FastAPI process serves the API, the customer chat and the staff console. One deploy, one
URL (A-10). A hosted link beats a recorded video, and splitting the frontend onto a different
host would buy nothing but CORS and a second deployment to break on the day.

No login (A-05). Two routes instead:

    /chat   the customer surface
    /ops    the staff surface

Staff authentication is a solved problem and not what the assignment asks to see. CUSTOMER
identity is a different thing and is not cut: see /api/sessions/{id}/verify/*.
"""

from __future__ import annotations

import random
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import actions, agent, db, gates

STATIC = Path(__file__).parent / "static"

app = FastAPI(title="7X delivery assistant", docs_url="/api/docs")
db.ensure()


def conn():
    return db.connect()


# ---------------------------------------------------------------- payloads


class NewSession(BaseModel):
    channel: str = "whatsapp"
    phone: str | None = None          # whatsapp: the channel supplies a verified number


class Said(BaseModel):
    text: str


class StartVerify(BaseModel):
    tracking_number: str


class ConfirmVerify(BaseModel):
    code: str


# ---------------------------------------------------------------- helpers


def _shipment_card(c, tracking: str | None) -> dict | None:
    """
    The parcel pinned at the top of the chat.

    A-13: this is read from the database, never from anything the model said. If the assistant
    claims it moved a delivery to Thursday and the row still says Tuesday, the card says
    Tuesday. That is what makes the demo proof rather than theatre.
    """
    if not tracking:
        return None
    row = c.execute(
        "SELECT * FROM shipments WHERE tracking_number = ?", (tracking,)
    ).fetchone()
    if row is None:
        return None

    g = gates.evaluate(row)
    conflicted = bool(row["flag_duplicate_conflict"]) or not g["attempts_reliable"]

    return {
        "tracking_number": row["tracking_number"],
        "status": "unclear" if conflicted else row["state"],
        "unclear": conflicted,
        "address": row["delivery_address"],
        "scheduled_date": row["scheduled_date"],
        "cod": float(row["cod_amount_aed"] or 0),
        "attempts": None if conflicted else row["delivery_attempts"],
        "max_attempts": gates.MAX_ATTEMPTS,
        "emirate": row["emirate"],
        "updated_at": row["updated_at"],
    }


def _messages(c, session_id: str) -> list[dict]:
    rows = c.execute(
        """SELECT role, author, content, created_at FROM messages
           WHERE session_id = ? AND role IN ('customer','assistant','staff','notice')
           ORDER BY id""",
        (session_id,),
    ).fetchall()
    return [
        {"role": r["role"], "author": r["author"], "text": r["content"],
         "at": r["created_at"]}
        for r in rows
        if r["content"]
    ]


def _session_dict(c, s) -> dict:
    return {
        "id": s["id"],
        "channel": s["channel"],
        "phone": s["phone"],
        "masked_phone": _mask(s["phone"]),
        "customer_name": s["customer_name"],
        "verified": bool(s["verified"]),
        "assistant_enabled": bool(s["assistant_enabled"]),
        "focus_tracking": s["focus_tracking"],
        "created_at": s["created_at"],
    }


def _mask(phone: str | None) -> str | None:
    if not phone:
        return None
    return phone[:7] + " ••• " + phone[-4:]


# ---------------------------------------------------------------- demo personas


@app.get("/api/demo/customers")
def demo_customers():
    """
    The people you can start a WhatsApp conversation as.

    Each one is a real row from the cleaned file, chosen because it exercises a different
    part of the system. This is the scenario picker, and it is also what turns a live demo
    from a tightrope into a walkthrough (A-16).
    """
    picks = [
        ("A normal parcel that can be moved", """
            SELECT * FROM shipments WHERE phone IS NOT NULL AND cod_amount_aed = 0
              AND delivery_attempts < 3 AND flag_duplicate_conflict = 0
              AND flag_attempts_unreliable = 0
              AND state IN ('out_for_delivery','failed','in_transit') LIMIT 1"""),
        ("Cash on delivery, address change is blocked", """
            SELECT * FROM shipments WHERE phone IS NOT NULL AND cod_amount_aed > 0
              AND delivery_attempts < 3 AND flag_duplicate_conflict = 0
              AND state IN ('out_for_delivery','failed','in_transit') LIMIT 1"""),
        ("Two records that disagree about delivery", """
            SELECT * FROM shipments WHERE flag_duplicate_conflict = 1
              AND phone IS NOT NULL LIMIT 1"""),
        ("Already at the 3 attempt limit", """
            SELECT * FROM shipments WHERE delivery_attempts >= 3 AND phone IS NOT NULL
              AND state NOT IN ('delivered','returned') LIMIT 1"""),
        ("No phone on file, cannot be verified", """
            SELECT * FROM shipments WHERE phone IS NULL
              AND state NOT IN ('delivered','returned') LIMIT 1"""),
    ]
    c = conn()
    out = []
    for label, sql in picks:
        row = c.execute(sql).fetchone()
        if row is None:
            continue
        out.append({
            "label": label,
            "customer_name": row["customer_name"],
            "phone": row["phone"],
            "masked_phone": _mask(row["phone"]),
            "tracking_number": row["tracking_number"],
        })
    c.close()
    return out


# ---------------------------------------------------------------- sessions


@app.post("/api/sessions")
def create_session(body: NewSession):
    c = conn()
    sid = "s-" + datetime.now().strftime("%H%M%S") + str(random.randint(10, 99))

    name = None
    verified = 0
    focus = None

    if body.channel == "whatsapp" and body.phone:
        # A-23. On WhatsApp the number arrives already verified by the channel, so the
        # customer skips verification entirely. Zero steps to a useful answer.
        row = c.execute(
            """SELECT customer_name, tracking_number FROM shipments
               WHERE phone = ? ORDER BY
                 CASE WHEN state IN ('delivered','returned') THEN 1 ELSE 0 END LIMIT 1""",
            (body.phone,),
        ).fetchone()
        name = row["customer_name"] if row else None
        focus = row["tracking_number"] if row else None
        verified = 1

    with c:
        c.execute(
            """INSERT INTO sessions (id, channel, phone, customer_name, verified,
                                     assistant_enabled, focus_tracking, created_at)
               VALUES (?,?,?,?,?,1,?,?)""",
            (sid, body.channel, body.phone, name, verified, focus,
             datetime.now().isoformat(timespec="seconds")),
        )

        if body.channel == "whatsapp" and verified:
            c.execute(
                """INSERT INTO messages (session_id, role, content, created_at)
                   VALUES (?, 'notice', ?, ?)""",
                (sid, f"Verified by WhatsApp · {_mask(body.phone)}",
                 datetime.now().isoformat(timespec="seconds")),
            )

    s = c.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
    out = _session_dict(c, s)
    c.close()
    return out


@app.get("/api/sessions")
def list_sessions():
    c = conn()
    rows = c.execute("SELECT * FROM sessions ORDER BY created_at DESC, id DESC").fetchall()
    out = []
    for s in rows:
        d = _session_dict(c, s)
        last = c.execute(
            """SELECT content FROM messages WHERE session_id=? AND content != ''
               ORDER BY id DESC LIMIT 1""", (s["id"],)
        ).fetchone()
        d["preview"] = (last["content"][:60] if last else "")
        d["open_cases"] = c.execute(
            "SELECT COUNT(*) n FROM cases WHERE session_id=? AND status='open'", (s["id"],)
        ).fetchone()["n"]
        out.append(d)
    c.close()
    return out


@app.get("/api/sessions/{sid}")
def get_session(sid: str):
    c = conn()
    s = c.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
    if s is None:
        c.close()
        raise HTTPException(404, "no such session")
    out = {
        "session": _session_dict(c, s),
        "messages": _messages(c, sid),
        "shipment": _shipment_card(c, s["focus_tracking"]),
    }
    c.close()
    return out


# ---------------------------------------------------------------- verification (web only)


@app.post("/api/sessions/{sid}/verify/start")
def verify_start(sid: str, body: StartVerify):
    """
    A-06. The customer types ONE thing, the tracking number. We read the phone off the record
    and send a code TO THAT NUMBER -- never to a number they type, which would prove nothing.

    Someone holding the parcel can read the masked number off the screen. They cannot receive
    the message.
    """
    c = conn()
    row = c.execute(
        "SELECT * FROM shipments WHERE tracking_number = ?",
        (body.tracking_number.strip().upper(),),
    ).fetchone()
    if row is None:
        c.close()
        raise HTTPException(404, "I can't find a parcel with that tracking number.")

    if not row["phone"]:
        # One of the 46 open shipments with no phone on file. Tracking only, and say why.
        with c:
            c.execute("UPDATE sessions SET focus_tracking=? WHERE id=?",
                      (row["tracking_number"], sid))
        c.close()
        return {
            "can_verify": False,
            "tracking_number": row["tracking_number"],
            "reason": gates.REASON_TEXT["no_phone_on_file"],
        }

    code = f"{random.randint(1000, 9999)}"
    with c:
        c.execute(
            """UPDATE sessions SET pending_code=?, pending_tracking=?, focus_tracking=?
               WHERE id=?""",
            (code, row["tracking_number"], row["tracking_number"], sid),
        )
    c.close()
    return {
        "can_verify": True,
        "tracking_number": row["tracking_number"],
        "masked_phone": _mask(row["phone"]),
        # The demo cannot send a real SMS. Label it rather than hide it (A-06).
        "demo_code": code,
    }


@app.post("/api/sessions/{sid}/verify/confirm")
def verify_confirm(sid: str, body: ConfirmVerify):
    c = conn()
    s = c.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
    if s is None:
        c.close()
        raise HTTPException(404, "no such session")

    if not s["pending_code"] or body.code.strip() != s["pending_code"]:
        c.close()
        return {"verified": False, "reason": "That code doesn't match. Try again."}

    row = c.execute(
        "SELECT * FROM shipments WHERE tracking_number=?", (s["pending_tracking"],)
    ).fetchone()

    with c:
        c.execute(
            """UPDATE sessions SET verified=1, phone=?, customer_name=?,
                                   pending_code=NULL WHERE id=?""",
            (row["phone"], row["customer_name"], sid),
        )
        c.execute(
            """INSERT INTO messages (session_id, role, content, created_at)
               VALUES (?, 'notice', ?, ?)""",
            (sid, f"Verified · {_mask(row['phone'])}",
             datetime.now().isoformat(timespec="seconds")),
        )

    n = c.execute("SELECT COUNT(*) n FROM shipments WHERE phone=?",
                  (row["phone"],)).fetchone()["n"]
    c.close()
    return {"verified": True, "customer_name": row["customer_name"], "parcel_count": n}


# ---------------------------------------------------------------- talking


@app.post("/api/sessions/{sid}/message")
def send_message(sid: str, body: Said):
    c = conn()
    s = c.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
    if s is None:
        c.close()
        raise HTTPException(404, "no such session")

    with c:
        out = agent.respond(c, sid, body.text)

        # Keep the pinned card pointed at whatever the assistant last touched.
        for call in out["tool_calls"]:
            tn = (call.get("input") or {}).get("tracking_number")
            if not tn:
                tn = (call.get("result", {}).get("data") or {}).get("tracking_number")
            if tn:
                c.execute("UPDATE sessions SET focus_tracking=? WHERE id=?", (tn, sid))

    s = c.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
    result = {
        "reply": out["reply"],
        "assistant_enabled": out["assistant_enabled"],
        "shipment": _shipment_card(c, s["focus_tracking"]),
        "messages": _messages(c, sid),
        "usage": out.get("usage"),
    }
    c.close()
    return result


# ---------------------------------------------------------------- reset


@app.post("/api/reset")
def reset():
    """A-18. One button restores the data, clears every conversation and empties the queue."""
    n = db.reset()
    return {"ok": True, "shipments": n}


# ---------------------------------------------------------------- pages


@app.get("/")
def landing():
    return FileResponse(STATIC / "index.html")


@app.get("/chat")
def chat_page():
    return FileResponse(STATIC / "chat.html")


@app.get("/ops")
def ops_page():
    path = STATIC / "ops.html"
    if path.exists():
        return FileResponse(path)
    return HTMLResponse(
        "<body style='font:15px system-ui;padding:40px'>"
        "<p>The operations console is step 4.</p>"
        "<p><a href='/chat'>Back to the customer view</a></p></body>"
    )


app.mount("/static", StaticFiles(directory=STATIC), name="static")

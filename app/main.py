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

import json
import secrets
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import actions, agent, cast, db, gates
from .db import TODAY

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


class StaffReply(BaseModel):
    text: str
    author: str = "Ali"


class AssistantToggle(BaseModel):
    enabled: bool


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
        # The addressee on the record, not the person in the conversation. In a
        # verified session they are the same person; on the card the record wins.
        "customer_name": row["customer_name"],
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
    The people a reviewer can start a WhatsApp conversation as, and the numbers to try on the
    website. Pinned in cast.py (A-16, A-26): rows nothing has happened to, so "a normal parcel"
    is still normal when they pick it. Names and numbers come from the database, not the code.
    """
    c = conn()
    people = []
    for p in cast.PICKER:
        row = c.execute("SELECT * FROM shipments WHERE tracking_number=?",
                        (p.tracking,)).fetchone()
        if row is None:
            continue
        people.append({
            "label": p.label,
            "outcome": p.outcome,
            "customer_name": row["customer_name"],
            "phone": row["phone"],
            "masked_phone": _mask(row["phone"]),
            "tracking_number": row["tracking_number"],
        })
    c.close()
    return {"people": people, "web": [{"tracking": t, "why": w} for t, w in cast.WEB_TRY]}


@app.get("/api/meta")
def meta():
    """The two facts a page shows about the demo itself: which day the assistant thinks it is
    (A-17), and how many real shipments it can see."""
    c = conn()
    n = c.execute("SELECT COUNT(*) n FROM shipments").fetchone()["n"]
    c.close()
    return {"today": TODAY.isoformat(), "today_label": TODAY.strftime("%a %d %b %Y"),
            "model": agent.MODEL, "shipments": n}


# ---------------------------------------------------------------- sessions


@app.post("/api/sessions")
def create_session(body: NewSession):
    c = conn()
    sid = "s-" + secrets.token_hex(4)

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
             db.now()),
        )

        if body.channel == "whatsapp" and verified:
            c.execute(
                """INSERT INTO messages (session_id, role, content, created_at)
                   VALUES (?, 'notice', ?, ?)""",
                (sid, f"Verified by WhatsApp · {_mask(body.phone)}",
                 db.now()),
            )

    s = c.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
    out = _session_dict(c, s)
    c.close()
    return out


@app.get("/api/sessions")
def list_sessions():
    c = conn()
    rows = c.execute("SELECT * FROM sessions ORDER BY created_at DESC, rowid DESC").fetchall()
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

    code = f"{secrets.randbelow(9000) + 1000}"
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
             db.now()),
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


# ================================================================= operations


def _age(iso: str | None) -> str:
    """Waiting time is MEASURED, so it is shown. A target would be invented, so
    there isn't one."""
    if not iso:
        return ""
    try:
        secs = max(0.0, (datetime.now() - datetime.fromisoformat(iso)).total_seconds())
    except ValueError:
        return ""
    if secs < 60:
        return f"{int(secs)}s"
    if secs < 3600:
        return f"{int(secs // 60)}m"
    if secs < 86400:
        return f"{int(secs // 3600)}h"
    return f"{int(secs // 86400)}d"


REASON_LABEL = {
    "cod_on_delivery":       "Cash on delivery",
    "attempt_limit_reached": "Attempt limit",
    "no_phone_on_file":      "No phone on file",
    "duplicate_conflict":    "Records disagree",
    "not_verified":          "Not verified",
    "not_actionable":        "Not actionable",
    "customer_request":      "Asked for a person",
}


def _timeline(c, session_id: str) -> list[dict]:
    """
    The conversation as a human needs it: what was said, AND what was attempted.

    A staff member picking up a case needs to see `change_address -> refused ->
    745.72 AED due`, not just the polite sentence the customer got. The tool
    calls live in the stored API blocks, so they are pulled back out and
    interleaved in order.
    """
    rows = c.execute(
        "SELECT * FROM messages WHERE session_id = ? ORDER BY id", (session_id,)
    ).fetchall()

    out: list[dict] = []
    pending: dict[str, dict] = {}

    for r in rows:
        blocks = json.loads(r["blocks"]) if r["blocks"] else []

        if r["role"] in ("customer", "staff", "notice") and r["content"]:
            out.append({"kind": "message", "role": r["role"], "author": r["author"],
                        "text": r["content"], "at": r["created_at"]})
            continue

        if r["role"] == "assistant":
            if r["content"]:
                out.append({"kind": "message", "role": "assistant", "author": None,
                            "text": r["content"], "at": r["created_at"]})
            for b in blocks:
                if b.get("type") == "tool_use":
                    entry = {"kind": "tool", "name": b["name"], "input": b.get("input") or {},
                             "outcome": None, "reason": None, "at": r["created_at"]}
                    pending[b["id"]] = entry
                    out.append(entry)

        elif r["role"] == "system":
            for b in blocks:
                if b.get("type") != "tool_result":
                    continue
                entry = pending.pop(b.get("tool_use_id"), None)
                if entry is None:
                    continue
                try:
                    res = json.loads(b.get("content") or "{}")
                except (TypeError, ValueError):
                    res = {}
                entry["outcome"] = "done" if res.get("ok") else "refused"
                entry["reason"] = res.get("reason")
    return out


@app.get("/api/cases")
def list_cases(status: str | None = None, reason: str | None = None, q: str | None = None):
    c = conn()
    rows = c.execute(
        """SELECT k.*, s.channel, s.customer_name, s.assistant_enabled
           FROM cases k LEFT JOIN sessions s ON s.id = k.session_id
           ORDER BY CASE k.status WHEN 'open' THEN 0 ELSE 1 END, k.created_at DESC"""
    ).fetchall()

    cases = []
    for r in rows:
        if status and r["status"] != status:
            continue
        if reason and r["reason_code"] != reason:
            continue
        if q:
            hay = " ".join(str(x or "") for x in
                           (r["id"], r["tracking_number"], r["customer_name"])).lower()
            if q.lower() not in hay:
                continue
        taken = c.execute(
            """SELECT author FROM messages WHERE session_id = ? AND role = 'staff'
               ORDER BY id DESC LIMIT 1""", (r["session_id"],)
        ).fetchone()
        cases.append({
            "id": r["id"], "status": r["status"],
            "tracking_number": r["tracking_number"],
            "customer_name": r["customer_name"],
            "channel": r["channel"],
            "reason_code": r["reason_code"],
            "reason_label": REASON_LABEL.get(r["reason_code"], r["reason_code"]),
            "reason_text": r["reason_text"],
            "created_at": r["created_at"], "age": _age(r["created_at"]),
            "taken_by": taken["author"] if taken else None,
            "assistant_enabled": bool(r["assistant_enabled"]),
        })

    # Composition of REAL cases. Not a projection, and not a time series.
    breakdown: dict[str, int] = {}
    longest = None
    for k in cases:
        if k["status"] != "open":
            continue
        breakdown[k["reason_label"]] = breakdown.get(k["reason_label"], 0) + 1
        if longest is None or k["created_at"] < longest:
            longest = k["created_at"]

    today = db.now()[:10]  # the log is real-clock, so "today" is too
    summary = {
        "open": sum(1 for k in cases if k["status"] == "open"),
        "resolved_today": c.execute(
            "SELECT COUNT(*) n FROM cases WHERE status='resolved' AND resolved_at LIKE ?",
            (today + "%",)).fetchone()["n"],
        "longest_waiting": _age(longest),
        "breakdown": breakdown,
    }
    c.close()
    return {"summary": summary, "cases": cases}


@app.get("/api/cases/{case_id}")
def get_case(case_id: str):
    c = conn()
    k = c.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    if k is None:
        c.close()
        raise HTTPException(404, "no such case")
    s = c.execute("SELECT * FROM sessions WHERE id = ?", (k["session_id"],)).fetchone()

    out = {
        "case": {
            "id": k["id"], "status": k["status"],
            "tracking_number": k["tracking_number"],
            "reason_code": k["reason_code"],
            "reason_label": REASON_LABEL.get(k["reason_code"], k["reason_code"]),
            "reason_text": k["reason_text"],
            "customer_request": k["customer_request"],
            "created_at": k["created_at"], "age": _age(k["created_at"]),
            "resolved_at": k["resolved_at"],
        },
        "session": _session_dict(c, s) if s else None,
        "timeline": _timeline(c, k["session_id"]) if k["session_id"] else [],
        "shipment": _shipment_card(c, k["tracking_number"]),
        "trace": [dict(r) for r in c.execute(
            "SELECT * FROM action_log WHERE session_id = ? ORDER BY id", (k["session_id"],))],
    }
    c.close()
    return out


@app.post("/api/cases/{case_id}/reply")
def staff_reply(case_id: str, body: StaffReply):
    """A-04. A person replies into the customer's own conversation, and the
    assistant stands down in that thread by default."""
    c = conn()
    k = c.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    if k is None or not k["session_id"]:
        c.close()
        raise HTTPException(404, "no such case")

    now = db.now()
    with c:
        first = c.execute(
            """SELECT COUNT(*) n FROM messages WHERE session_id = ? AND role = 'staff'""",
            (k["session_id"],)).fetchone()["n"] == 0
        if first:
            c.execute("""INSERT INTO messages (session_id, role, content, created_at)
                         VALUES (?, 'notice', ?, ?)""",
                      (k["session_id"], f"{body.author} from 7X joined this conversation", now))
        c.execute("""INSERT INTO messages (session_id, role, author, content, created_at)
                     VALUES (?, 'staff', ?, ?, ?)""",
                  (k["session_id"], body.author, body.text, now))
        c.execute("UPDATE sessions SET assistant_enabled = 0 WHERE id = ?", (k["session_id"],))
    c.close()
    return {"ok": True}


@app.post("/api/cases/{case_id}/resolve")
def resolve_case(case_id: str):
    c = conn()
    with c:
        c.execute("UPDATE cases SET status='resolved', resolved_at=? WHERE id=?",
                  (db.now(), case_id))
    c.close()
    return {"ok": True}


@app.post("/api/sessions/{sid}/assistant")
def set_assistant(sid: str, body: AssistantToggle):
    """The toggle. Manual only -- no timeout ever turns the assistant back on,
    because a person switched it off for a reason."""
    c = conn()
    now = db.now()
    with c:
        c.execute("UPDATE sessions SET assistant_enabled = ? WHERE id = ?",
                  (1 if body.enabled else 0, sid))
        if body.enabled:
            c.execute("""INSERT INTO messages (session_id, role, content, created_at)
                         VALUES (?, 'notice', ?, ?)""",
                      (sid, "Handed back to the assistant", now))
    c.close()
    return {"ok": True, "enabled": body.enabled}


@app.get("/api/trace")
def trace(outcome: str | None = None, limit: int = 300):
    c = conn()
    rows = c.execute("SELECT * FROM action_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    out = []
    for r in rows:
        if outcome and r["outcome"] != outcome:
            continue
        case = c.execute(
            """SELECT id FROM cases WHERE session_id IS ? AND tracking_number IS ?
               ORDER BY id DESC LIMIT 1""", (r["session_id"], r["tracking_number"])).fetchone()
        out.append({
            "id": r["id"], "at": r["created_at"], "session_id": r["session_id"],
            "tracking_number": r["tracking_number"], "action": r["action"],
            "outcome": r["outcome"], "detail": r["detail"],
            "case_id": case["id"] if case else None,
        })
    totals = c.execute(
        "SELECT outcome, COUNT(*) n FROM action_log GROUP BY outcome").fetchall()
    c.close()
    return {"rows": out, "totals": {r["outcome"]: r["n"] for r in totals}}


@app.get("/api/readiness")
def readiness():
    """
    The cleaning story, computed from the same database everything else reads.

    This is the screen nobody else will have: not what the assistant did, but
    which rows it was allowed anywhere near, and why the rest were refused.
    """
    c = conn()

    states = {r["state"]: r["n"] for r in c.execute(
        "SELECT state, COUNT(*) n FROM shipments GROUP BY 1 ORDER BY 2 DESC")}

    rows = c.execute("SELECT * FROM shipments").fetchall()
    g = [gates.evaluate(r) for r in rows]
    block_counts: dict[str, int] = {}
    for x in g:
        for code in x["block_codes"]:
            block_counts[REASON_LABEL.get(code, code)] = \
                block_counts.get(REASON_LABEL.get(code, code), 0) + 1

    # D-02: 22 written spellings of 6 real things. Shown rather than described.
    spellings: dict[str, list[str]] = {}
    for r in c.execute(
            "SELECT DISTINCT state, raw_status FROM shipments WHERE raw_status IS NOT NULL"):
        spellings.setdefault(r["state"], []).append(r["raw_status"])
    for v in spellings.values():
        v.sort()

    # D-04: the trap. Day-first and month-first in the SAME column.
    fmts = {r["f"]: r["n"] for r in c.execute(
        """SELECT shipment_date_format f, COUNT(*) n FROM shipments
           WHERE shipment_date_format IS NOT NULL GROUP BY 1 ORDER BY 2 DESC""")}
    samples = []
    for f in fmts:
        if f == "iso":
            continue
        r = c.execute(
            """SELECT shipment_date_raw raw, shipment_date parsed FROM shipments
               WHERE shipment_date_format = ? LIMIT 1""", (f,)).fetchone()
        if r:
            samples.append({"format": f, "raw": r["raw"], "parsed": r["parsed"],
                            "count": fmts[f],
                            "order": "month first" if f.startswith("mm") else
                                     ("serial" if "serial" in f else "day first")})

    flags = {
        "records disagree":    c.execute("SELECT COUNT(*) n FROM shipments WHERE flag_duplicate_conflict=1").fetchone()["n"],
        "attempts unreliable": c.execute("SELECT COUNT(*) n FROM shipments WHERE flag_attempts_unreliable=1").fetchone()["n"],
        "impossible dates":    c.execute("SELECT COUNT(*) n FROM shipments WHERE flag_impossible_dates=1").fetchone()["n"],
        "no phone on file":    c.execute("SELECT COUNT(*) n FROM shipments WHERE phone IS NULL").fetchone()["n"],
        "no address on file":  c.execute("SELECT COUNT(*) n FROM shipments WHERE flag_missing_address=1").fetchone()["n"],
    }

    quarantine, q_counts = [], {}
    qpath = db.ROOT / "data" / "shipments_quarantine.csv"
    if qpath.exists():
        import pandas as pd
        q = pd.read_csv(qpath)
        col = "quarantine_reason" if "quarantine_reason" in q.columns else q.columns[-1]
        q_counts = {str(k): int(v) for k, v in q[col].value_counts().items()}
        for r in q.head(40).itertuples(index=False):
            d = dict(r._asdict())
            quarantine.append({
                "tracking_number": str(d.get("tracking_number", "")),
                "raw_status": str(d.get("raw_status", "") or ""),
                "reason": str(d.get(col, "")),
            })

    c.close()
    return {
        "reconciliation": {
            "input": 840 + sum(q_counts.values()),
            "quarantined": sum(v for k, v in q_counts.items() if "duplicate" not in k),
            "superseded": sum(v for k, v in q_counts.items() if "duplicate" in k),
            "clean": len(rows),
        },
        "states": states,
        "gates": {
            "open": sum(x["is_open"] for x in g),
            "reschedulable": sum(x["can_reschedule"] for x in g),
            "address_changeable": sum(x["can_change_address"] for x in g),
            "needs_human_open": sum(x["requires_human"] for x in g if x["is_open"]),
            "suspect": sum(1 for r in rows if r["data_confidence"] != "clean"),
        },
        "block_counts": block_counts,
        "spellings": spellings,
        "date_formats": samples,
        "flags": flags,
        "quarantine": quarantine,
        "quarantine_counts": q_counts,
    }


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

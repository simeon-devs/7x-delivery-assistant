"""
The agent loop.

A plain tool-use loop on the Anthropic SDK. No framework.

The flow is: identify the shipment, check the gate, act or refuse. That is a function, not a
graph, and a graph library for a straight line is a dependency that cannot be justified when
someone asks why it is there. Under challenge the whole control path has to be one file you can
open and point at.

What the model can and cannot do:

  * it has five tools and nothing else. No database handle, no shell, no network.
  * it starts every conversation knowing nothing about any parcel (A-12). Not one row of
    shipment data reaches the system prompt, so it cannot answer from context. It has to call
    a tool to know anything at all, which is what makes this agentic rather than a chatbot
    with a table pasted in.
  * it is handed ANSWERS and SENTENCES, never rules. It cannot reason its way around a rule it
    was never shown.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from . import actions, db
from .db import TODAY

load_dotenv()

# The SDK looks for ANTHROPIC_API_KEY; accept ANTHROPIC_KEY too so a working .env is not a
# naming argument.
_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_KEY")

MODEL = "claude-sonnet-5"
MAX_TOKENS = 1024
MAX_TOOL_ROUNDS = 6

PROMPT_PATH = Path(__file__).parent / "prompts" / "customer_assistant.md"

# Effort "low". The model is not the thing deciding whether an action is permitted -- code
# is -- so deep reasoning has nowhere to apply, and latency is a feature in a chat window.
# This used to say "no extended thinking" while the call left thinking unset, which on Sonnet 5
# means it runs adaptive thinking anyway: 13 of 37 recorded calls thought, billed as output.
# Low effort rather than thinking disabled: with thinking off, the model can write a tool call
# into its reply text instead of making it. Measured on all eight seeded conversations, together
# with caching the whole conversation (below): model cost per conversation $0.0161 -> $0.0131,
# and every conversation ended in the same actions and the same cases.
EFFORT = "low"


# ---------------------------------------------------------------- tool schemas

TOOLS = [
    {
        "name": "find_shipments_for_customer",
        "description": (
            "List the parcels belonging to the verified customer in this conversation. "
            "Use this at the start of a conversation, or whenever you need to know which "
            "parcels the customer has. Takes no arguments."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_shipment",
        "description": (
            "Look up one parcel by its tracking number. Returns its status, address, dates, "
            "and whether it can be rescheduled or re-addressed. If something cannot be done, "
            "the response contains the exact sentence to tell the customer. "
            "Looking up is free and needs no confirmation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tracking_number": {
                    "type": "string",
                    "description": "The tracking number, e.g. EX400312AE",
                }
            },
            "required": ["tracking_number"],
        },
    },
    {
        "name": "reschedule_delivery",
        "description": (
            "Move a delivery to a new date. THIS CHANGES THE RECORD. "
            "Confirm the exact date with the customer in words before calling this. "
            "If it returns ok=false the delivery was NOT moved and you must say so."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tracking_number": {"type": "string"},
                "new_date": {
                    "type": "string",
                    "description": (
                        f"The new delivery date as YYYY-MM-DD. Today is {TODAY.isoformat()}. "
                        "Work out the actual date from what the customer said."
                    ),
                },
            },
            "required": ["tracking_number", "new_date"],
        },
    },
    {
        "name": "change_address",
        "description": (
            "Change where a parcel is delivered. THIS CHANGES THE RECORD. "
            "Read the full new address back to the customer before calling this. "
            "If it returns ok=false the address was NOT changed and you must say so."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tracking_number": {"type": "string"},
                "new_address": {
                    "type": "string",
                    "description": "The complete new delivery address.",
                },
            },
            "required": ["tracking_number", "new_address"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": (
            "Hand this conversation to a member of staff. Call this immediately whenever the "
            "customer asks for a person, whenever a parcel's records contradict each other, "
            "and whenever they ask for something outside parcels (app problems, accounts, "
            "billing, lost or damaged items, compensation). "
            "Put everything the customer has told you into 'details' so the staff member does "
            "not have to ask them again."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "One short line on why this needs a person.",
                },
                "details": {
                    "type": "string",
                    "description": "Everything the customer said that staff will need.",
                },
                "tracking_number": {
                    "type": "string",
                    "description": "The parcel involved, if there is one.",
                },
            },
            "required": ["reason"],
        },
    },
]


# ---------------------------------------------------------------- dispatch

def run_tool(conn, session_id: str, name: str, args: dict) -> dict:
    if name == "find_shipments_for_customer":
        return actions.find_shipments_for_customer(conn, session_id)
    if name == "get_shipment":
        return actions.get_shipment(conn, session_id, args.get("tracking_number", ""))
    if name == "reschedule_delivery":
        return actions.reschedule_delivery(
            conn, session_id, args.get("tracking_number", ""), args.get("new_date", "")
        )
    if name == "change_address":
        return actions.change_address(
            conn, session_id, args.get("tracking_number", ""), args.get("new_address", "")
        )
    if name == "escalate_to_human":
        return actions.escalate_to_human(
            conn,
            session_id,
            args.get("reason", "Customer asked for a person."),
            args.get("details"),
            args.get("tracking_number"),
        )
    return {"ok": False, "data": {}, "reason": f"Unknown tool {name}.", "escalate": False}


# ---------------------------------------------------------------- prompt

def build_system_prompt(channel: str, customer_name: str | None) -> str:
    text = PROMPT_PATH.read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S).lstrip()
    ex = db.next_weekday(3)
    return (
        text.replace("{{TODAY}}", TODAY.strftime("%A %d %B %Y"))
        .replace("{{CHANNEL}}", "WhatsApp" if channel == "whatsapp" else "the 7X website")
        .replace("{{CUSTOMER_NAME}}", customer_name or "unknown")
        .replace("{{EXAMPLE_DATE}}", f"{ex:%A} {ex.day} {ex:%B}")
    )


# ---------------------------------------------------------------- history

def _history(conn, session_id: str) -> list[dict]:
    rows = conn.execute(
        """SELECT api_role, blocks FROM messages
           WHERE session_id = ? AND api_role IS NOT NULL ORDER BY id""",
        (session_id,),
    ).fetchall()
    turns = [{"role": r["api_role"], "content": json.loads(r["blocks"])} for r in rows]

    # A tool_use with no tool_result after it is a conversation the API rejects. That should
    # not happen any more, but a session recorded before the fix would be unusable for ever,
    # so drop the unanswered turn rather than carry a shape that cannot be sent.
    answered = {b.get("tool_use_id") for t in turns for b in t["content"]
                if isinstance(b, dict) and b.get("type") == "tool_result"}
    clean = []
    for t in turns:
        wants = {b.get("id") for b in t["content"]
                 if isinstance(b, dict) and b.get("type") == "tool_use"}
        if wants and not wants <= answered:
            continue
        clean.append(t)
    return clean


def save(conn, session_id: str, *, role: str, content: str,
         api_role: str | None = None, blocks: list | None = None,
         author: str | None = None) -> None:
    conn.execute(
        """INSERT INTO messages (session_id, role, author, content, blocks, api_role, created_at)
           VALUES (?,?,?,?,?,?,?)""",
        (
            session_id,
            role,
            author,
            content,
            json.dumps(blocks) if blocks is not None else None,
            api_role,
            db.now(),
        ),
    )


# ---------------------------------------------------------------- the loop

def respond(conn, session_id: str, customer_message: str) -> dict:
    """
    One customer turn in, one assistant turn out.

    Returns { reply, tool_calls, assistant_enabled, usage }, and an "error" key too when the
    model call itself failed. If a staff member has taken the conversation over, the assistant
    stays silent (A-04) and reply is None.
    """
    session = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if session is None:
        raise ValueError(f"no session {session_id}")

    with conn:
        save(conn, session_id, role="customer", content=customer_message,
             api_role="user", blocks=[{"type": "text", "text": customer_message}])

    # A-04: a human has taken over. The assistant does not speak until a person turns it
    # back on. No timeout does it automatically.
    if not session["assistant_enabled"]:
        return {"reply": None, "tool_calls": [], "assistant_enabled": False,
                "usage": {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "calls": 0}}

    client = Anthropic(api_key=_KEY)
    system = build_system_prompt(session["channel"], session["customer_name"])
    # Prompt caching. The cache prefix runs tools -> system -> messages, so one marker on the
    # system block caches the tool schemas with it. Everything before the conversation is the
    # same on every call, and it is most of the tokens.
    system_blocks = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
    messages = _history(conn, session_id)
    tool_calls: list[dict] = []
    usage = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "calls": 0}

    for _ in range(MAX_TOOL_ROUNDS):
        # No write transaction spans this call. A turn can take tens of seconds; holding
        # SQLite's single write lock for that long makes a second conversation, or a reset,
        # wait five seconds and then fail.
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system_blocks,
                tools=TOOLS,
                messages=messages,
                output_config={"effort": EFFORT},
                # Every tool round resends the whole conversation; this caches it, not just the
                # system prompt, so the resent part is read at a tenth of the price.
                cache_control={"type": "ephemeral"},
            )
        except Exception as e:  # noqa: BLE001 -- whatever failed, the customer hears something
            return _failed(conn, session_id, tool_calls, usage, e)
        u = response.usage
        usage["input"] += u.input_tokens
        usage["output"] += u.output_tokens
        usage["cache_read"] += getattr(u, "cache_read_input_tokens", 0) or 0
        usage["cache_write"] += getattr(u, "cache_creation_input_tokens", 0) or 0
        usage["calls"] += 1

        blocks = [b.model_dump() for b in response.content]
        text = "".join(b["text"] for b in blocks if b["type"] == "text").strip()
        messages.append({"role": "assistant", "content": blocks})
        with conn:
            save(conn, session_id, role="assistant", content=text,
                 api_role="assistant", blocks=blocks)

        if response.stop_reason != "tool_use":
            # A tool call earlier in this same turn (escalate_to_human, most likely) may have
            # switched the assistant off. Report what the database says now, not what was true
            # when the loop started.
            enabled = conn.execute(
                "SELECT assistant_enabled FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()["assistant_enabled"]
            return {"reply": text, "tool_calls": tool_calls,
                    "assistant_enabled": bool(enabled), "usage": usage}

        results = []
        for b in blocks:
            if b["type"] != "tool_use":
                continue
            # Each tool commits on its own, and a failure becomes a refusal rather than an
            # exception. The saved blocks must always pair a tool_use with a tool_result:
            # an orphan pair is a conversation the API will not accept again, and these
            # blocks are what the demo replays.
            try:
                with conn:
                    result = run_tool(conn, session_id, b["name"], b["input"] or {})
            except Exception as e:  # noqa: BLE001
                result = {"ok": False, "data": {},
                          "reason": f"That tool failed: {type(e).__name__}.", "escalate": True}
            tool_calls.append({"name": b["name"], "input": b["input"], "result": result})
            results.append({"type": "tool_result", "tool_use_id": b["id"],
                            "content": json.dumps(result), "is_error": not result["ok"]})
        with conn:
            save(conn, session_id, role="system", content="", api_role="user", blocks=results)
        messages.append({"role": "user", "content": results})

    # MAX_TOOL_ROUNDS rounds and no answer. Say so, and make it true (A-03): a person really is
    # asked, under its own reason code -- not the parcel's block code, which on a conflicted
    # parcel would collide with the case _do_action already opened and get deduped away, so the
    # "the assistant looped" signal would never reach the queue at all.
    reply = "Let me get a person to help with this."
    with conn:
        actions.escalate_to_human(conn, session_id,
                                  f"The assistant could not finish within {MAX_TOOL_ROUNDS} "
                                  "tool calls.",
                                  details=customer_message, reason_code="assistant_error")
        save(conn, session_id, role="assistant", content=reply, api_role="assistant",
             blocks=[{"type": "text", "text": reply}])
    return {"reply": reply, "tool_calls": tool_calls, "assistant_enabled": False, "usage": usage}


def _failed(conn, session_id: str, tool_calls: list, usage: dict, error: Exception) -> dict:
    """The API call failed. The customer gets a sentence, a person gets a case, nothing is
    lost: the customer's message is already saved, so the person can read it. The reply below
    is the one thing that must not depend on the database, so nothing here is allowed to raise."""
    reply = "Something went wrong on my side. I've asked a person to pick this up."
    # Never the raw exception: a base URL carrying credentials, for instance, must not land
    # somewhere a staff member reads it.
    detail = f"{type(error).__name__}: {getattr(error, 'message', str(error))}"[:300]
    try:
        with conn:
            actions.escalate_to_human(
                conn, session_id,
                f"The assistant failed mid-conversation: {type(error).__name__}.",
                details=detail, reason_code="assistant_error",
            )
            save(conn, session_id, role="assistant", content=reply, api_role="assistant",
                 blocks=[{"type": "text", "text": reply}])
    except Exception:  # noqa: BLE001 -- the reply must reach the customer even if this fails
        pass
    return {"reply": reply, "tool_calls": tool_calls, "assistant_enabled": False,
            "usage": usage, "error": str(error)}

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

# No extended thinking. The model is not the thing deciding whether an action is permitted —
# code is — so the reasoning it would buy has nowhere to apply, and latency is a feature in a
# chat window. Revisit only if date handling proves weak.


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

def _run_tool(conn, session_id: str, name: str, args: dict) -> dict:
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
    return (
        text.replace("{{TODAY}}", TODAY.strftime("%A %d %B %Y"))
        .replace("{{CHANNEL}}", "WhatsApp" if channel == "whatsapp" else "the 7X website")
        .replace("{{CUSTOMER_NAME}}", customer_name or "unknown")
    )


# ---------------------------------------------------------------- history

def _history(conn, session_id: str) -> list[dict]:
    rows = conn.execute(
        """SELECT api_role, blocks FROM messages
           WHERE session_id = ? AND api_role IS NOT NULL ORDER BY id""",
        (session_id,),
    ).fetchall()
    return [{"role": r["api_role"], "content": json.loads(r["blocks"])} for r in rows]


def _save(conn, session_id: str, *, role: str, content: str,
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

    Returns { reply, tool_calls, assistant_enabled }. If a staff member has taken the
    conversation over, the assistant stays silent (A-04) and reply is None.
    """
    session = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if session is None:
        raise ValueError(f"no session {session_id}")

    _save(conn, session_id, role="customer", content=customer_message,
          api_role="user", blocks=[{"type": "text", "text": customer_message}])

    # A-04: a human has taken over. The assistant does not speak until a person turns it
    # back on. No timeout does it automatically.
    if not session["assistant_enabled"]:
        return {"reply": None, "tool_calls": [], "assistant_enabled": False,
                "usage": {"input": 0, "output": 0, "calls": 0}}

    client = Anthropic(api_key=_KEY)
    system = build_system_prompt(session["channel"], session["customer_name"])
    messages = _history(conn, session_id)
    tool_calls: list[dict] = []
    usage = {"input": 0, "output": 0, "calls": 0}

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            tools=TOOLS,
            messages=messages,
        )
        usage["input"] += response.usage.input_tokens
        usage["output"] += response.usage.output_tokens
        usage["calls"] += 1

        blocks = [b.model_dump() for b in response.content]
        text = "".join(b["text"] for b in blocks if b["type"] == "text").strip()
        messages.append({"role": "assistant", "content": blocks})
        _save(conn, session_id, role="assistant", content=text,
              api_role="assistant", blocks=blocks)

        if response.stop_reason != "tool_use":
            return {"reply": text, "tool_calls": tool_calls,
                    "assistant_enabled": True, "usage": usage}

        results = []
        for b in blocks:
            if b["type"] != "tool_use":
                continue
            result = _run_tool(conn, session_id, b["name"], b["input"] or {})
            tool_calls.append({"name": b["name"], "input": b["input"], "result": result})
            results.append({
                "type": "tool_result",
                "tool_use_id": b["id"],
                "content": json.dumps(result),
            })

        messages.append({"role": "user", "content": results})
        _save(conn, session_id, role="system", content="", api_role="user", blocks=results)

        # escalate_to_human switches the assistant off mid-turn. Let it finish this reply,
        # then stop; the next customer message will get silence until a person re-enables it.
        session = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()

    return {
        "reply": "Let me get a person to help with this.",
        "tool_calls": tool_calls,
        "assistant_enabled": bool(session["assistant_enabled"]),
        "usage": usage,
    }

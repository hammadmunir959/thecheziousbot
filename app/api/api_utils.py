"""
api_utils.py — Shared utilities for CheziousBot API endpoints.
"""

import json
import logging

from fastapi import HTTPException
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command
from sqlmodel import Session

from ..models.users_model import User
from ..agent.graphs.graph import workflow
from ..services.session_service import (
    get_session_id,
    resolve_session_id,
    SessionError,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# User utilities
# ---------------------------------------------------------

def get_user(user_id: str, db: Session) -> User:
    """Fetch user or raise 401."""

    user = db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized.")

    return user


# ---------------------------------------------------------
# Session utilities
# ---------------------------------------------------------

def resolve_thread(user_id: str, thread_id: str | None) -> str:
    """Resolve or create a conversation thread."""

    try:
        if thread_id:
            return resolve_session_id(thread_id, user_id)
        return get_session_id(user_id)
    except SessionError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Graph helpers
# ---------------------------------------------------------

def _is_interrupted(state) -> bool:
    """Return True if the graph is paused at an interrupt."""

    return bool(
        state.next
        and state.tasks
        and state.tasks[0].interrupts
    )


def build_graph_input(config: dict, message: str) -> Command | dict:
    """
    Build graph input.
    Resumes from interrupt if paused, otherwise sends a new human message.
    """

    state = workflow.get_state(config)

    if _is_interrupted(state):
        return Command(resume=message)

    return {"messages": [HumanMessage(content=message)]}


def get_reply(config: dict) -> tuple[str, bool]:
    """
    Retrieve the final AI reply from graph state.

    Returns:
        (reply: str, interrupted: bool)
    """

    state = workflow.get_state(config)

    if _is_interrupted(state):
        payload = state.tasks[0].interrupts[0].value
        content = payload.get("content", str(payload)) if isinstance(payload, dict) else str(payload)
        return content, True

    for msg in reversed(state.values.get("messages", [])):
        if isinstance(msg, AIMessage) and msg.content.strip():
            return msg.content.strip(), False

    raise ValueError("Graph produced no AI response.")


# ---------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------

def sse(event: str, data: dict) -> str:
    """Format a single Server-Sent Event."""

    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def stream_text(close_event: str, text: str, chunk_size: int = 3):
    """
    Stream a plain text string token by token as SSE events.

    Yields "token" events for each chunk, then a final close_event
    ("done" or "interrupt") with an empty content to signal end of stream.

    Args:
        close_event:  "done" | "interrupt" — the final event type.
        text:         The full string to stream.
        chunk_size:   Characters per token chunk (default: 3).
    """

    for i in range(0, len(text), chunk_size):
        yield sse("token", {"content": text[i : i + chunk_size]})

    yield sse(close_event, {"content": ""})
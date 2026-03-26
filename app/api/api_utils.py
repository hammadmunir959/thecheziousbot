"""
api_utils.py — Utility functions for API endpoints.
"""

import json
import logging
import time

from fastapi import APIRouter,  HTTPException
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langgraph.types import Command
from sqlmodel import Session

from ..agent.graphs.graph import workflow
from ..models.users_model import User
from ..services.session_service import get_session_id, resolve_session_id, SessionError

logger = logging.getLogger(__name__)
router = APIRouter()

CHUNK_SIZE = 5
CHUNK_DELAY = 0.03

def get_user(user_id: str, db: Session) -> User:
    """Fetch user from DB or raise 404."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


def resolve_thread(user_id: str, thread_id: str | None) -> str:
    """Resolve or create a thread ID for the user."""
    try:
        return resolve_session_id(thread_id, user_id) if thread_id else get_session_id(user_id)
    except SessionError as e:
        raise HTTPException(status_code=400, detail=str(e))


def make_config(user_id: str, thread_id: str) -> dict:
    """Create a configuration dictionary for the graph."""
    
    return {"configurable": {"user_id": user_id, "thread_id": thread_id}}


def get_interrupt(config: dict) -> str | None:
    
    """Get current interrupt text from graph state, or None."""
    state = workflow.get_state(config)
    if state.next and state.tasks and state.tasks[0].interrupts:
        val = state.tasks[0].interrupts[0].value
        return val.get("content", str(val)) if isinstance(val, dict) else str(val)
    return None


def get_last_ai(config: dict) -> str | None:
    """Get the last AI message from graph state."""
    state = workflow.get_state(config)
    for msg in reversed(state.values.get("messages", [])):
        if isinstance(msg, AIMessage) and msg.content.strip():
            return msg.content.strip()
    return None


def build_input(config: dict, message: str):
    """Return (graph_input, had_interrupt)."""
    had_interrupt = get_interrupt(config) is not None
    if had_interrupt:
        return Command(resume=message), True
    return {"messages": [HumanMessage(content=message)]}, False


def sse(event: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def simulate_typing(text: str, final_event: str):
    """Fake token-by-token for non-LLM text (interrupts, receipts)."""
    for i in range(0, len(text), CHUNK_SIZE):
        yield sse("token", {"content": text[i : i + CHUNK_SIZE]})
        time.sleep(CHUNK_DELAY)
    yield sse(final_event, {"content": ""})


# ── Streaming ────────────────────────────────────────────────────────────────

def stream_response(config: dict, message: str):
    """Generator that yields SSE strings for streaming chat responses.
        Handles both real LLM tokens and simulates tokens for interrupts or non-LLM messages.
        
        
    Yields:        str: Formatted SSE string to send to the client.
    
    """
    try:
        graph_input, _ = build_input(config, message)
        existing_interrupt = get_interrupt(config)
        non_chat_message = None

        for event_type, event_data in workflow.stream(graph_input, config=config, stream_mode=["messages", "updates"]):

            # Stream real LLM tokens (chat node only)
            if event_type == "messages":
                chunk, meta = event_data
                
                is_chat_node = meta.get("langgraph_node") == "chat"
                is_llm_token = isinstance(chunk, AIMessageChunk) and chunk.content
                if is_llm_token and is_chat_node:
                    yield sse("token", {"content": chunk.content})

            # Capture messages from other nodes (receipts, cancellations, etc.)
            elif event_type == "updates" and isinstance(event_data, dict):
                for node_name, node_output in event_data.items():
                    if node_name != "chat" and isinstance(node_output, dict):
                        for msg in node_output.get("messages", []):
                            if isinstance(msg, AIMessage) and msg.content:
                                non_chat_message = msg.content

        # End the stream
        new_interrupt = get_interrupt(config)
        # check if there's a new interrupt that wasn't present at the start of streaming
        is_new_interrupt = new_interrupt and new_interrupt != existing_interrupt
        
        if is_new_interrupt:
            yield from simulate_typing(new_interrupt, "interrupt")  # graph paused, waiting for user
        elif non_chat_message:
            yield from simulate_typing(non_chat_message, "done")    # non-LLM node responded
        else:
            yield sse("done", {"content": ""})                       # normal LLM response ended

    except Exception:
        logger.exception("Streaming failed")
        yield sse("error", {"detail": "Something went wrong. Please try again."})
        
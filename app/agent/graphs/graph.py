"""
graph.py — Main LangGraph agent graph for CheziousBot.

"""

# ── 1. Imports ────────────────────────────────────────────────────────────────
import sqlite3
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from ..state import State
from ..nodes.chat_node import chat_node
from ..nodes.classify_intent_node import classify_intent_node
from ..nodes.info_node import info_node
from ..nodes.summarize_node import summarize_node

from ..nodes.extract_node import extract_node
from ..nodes.validate_node import validate_node
from ..nodes.confirm_node import confirm_node
from ..nodes.execute_order_node import execute_order_node

from ...config.settings import settings


# ── 2. Router Functions ───────────────────────────────────────────────────────
def route_early_summarize(state: State) -> str:
    """Trigger summarization BEFORE classification if history is too long (4 chars = 1 token)."""
    messages = state.get("messages", [])
    
    if not messages:
        return "classify"
    
    # Calculate estimated tokens (4 characters = 1 token)
    total_chars = sum(len(m.content) for m in messages if hasattr(m, "content") and m.content)
    estimated_tokens = total_chars // 4

    if estimated_tokens > settings.SUMMARIZE_TOKEN_THRESHOLD:
        return "summarize"

    return "classify"


def route_after_classify(state: State) -> str:
    """Route based on classified intent, with active cart awareness."""
    
    intent       = (state.get("intent") or "").upper()

    if intent == "ORDER":
        return "extract"
    if intent == "INFO":
        return "info"
    if intent == "SPAM":
        return "chat"
        
    return "chat"


def route_by_status(state: State) -> str:
    """Generic router that reads the order_status emitted by nodes."""

    order_status= state["order_status"].upper()

    return order_status


# ── 3. Graph Nodes ────────────────────────────────────────────────────────────
graph = StateGraph(State)

# Auxillary nodes
graph.add_node("classify",       classify_intent_node)
graph.add_node("info",           info_node)
graph.add_node("chat",           chat_node)
graph.add_node("summarize",      summarize_node)

# Order lifecycle nodes
graph.add_node("extract",        extract_node)
graph.add_node("validate",       validate_node)
graph.add_node("confirm",        confirm_node)
graph.add_node("execute",        execute_order_node)


# ── 4. Graph Edges ────────────────────────────────────────────────────────────

# Initial evaluation
graph.add_conditional_edges(
    START,
    route_early_summarize,
    {
        "summarize": "summarize",
        "classify":  "classify",
    },
)

graph.add_edge("summarize", "classify")

# Intent routing
graph.add_conditional_edges(
    "classify",
    route_after_classify,
    {
        "extract": "extract",
        "info":    "info",
        "chat":    "chat",
    },
)

graph.add_edge("info", "chat")

# Order processing
graph.add_edge("extract", "validate")

graph.add_conditional_edges(
    "validate",
    route_by_status,
    {
        "VALIDATED":  "confirm",
        "EXTRACTING": "extract",
        "CANCELLED":  END,
    },
)

graph.add_conditional_edges(
    "confirm",
    route_by_status,
    {
        "CONFIRMED":  "execute",
        "EXTRACTING": "extract",  
        "CANCELLED":  END,
    },
)

# Terminal edges
graph.add_edge("execute", END)
graph.add_edge("chat",    END)


# ── 5. Compilation ────────────────────────────────────────────────────────────
conn = sqlite3.connect(settings.CHECKPOINT_DB_PATH, check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

workflow = graph.compile(checkpointer=checkpointer)

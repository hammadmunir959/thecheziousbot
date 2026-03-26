"""
summarize_node.py — Rolling conversation memory compressor.

Triggered when the message history grows beyond the token threshold.
Compresses older messages into a factual summary, preserving all
order-critical information (items, address, payment, corrections).

Tracks `last_summarized_index` so each run only processes *new* messages,
avoiding redundant re-summarization.
"""

import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.agent.state import State
from app.agent.llm_client import llm, advanced_llm
from app.agent.prompts.prompts import SUMMARIZE_PROMPT
from app.config.settings import settings

logger = logging.getLogger(__name__)

# ── 1. LLMs ───────────────────────────────────────────────────────────────
_primary = llm.bind(temperature=0).with_retry(stop_after_attempt=settings.MAX_LLM_RETRIES)
_fallback = advanced_llm.bind(temperature=0).with_retry(stop_after_attempt=settings.MAX_LLM_RETRIES)
_summarize_llm = _primary.with_fallbacks([_fallback])

# ── 2. Chains ─────────────────────────────────────────────────────────────
_prompt = ChatPromptTemplate.from_messages([
    ("system", SUMMARIZE_PROMPT),
    ("system", "### CURRENT CONTEXT"),
    ("system", "[CURRENT_SUMMARY]:\n{existing_summary}"),
    MessagesPlaceholder("new_messages"),
    ("system", "### FINAL INSTRUCTION: Update the summary based on [NEW_MESSAGES].")
])
_chain = _prompt | _summarize_llm

# ── 3. Utilities ──────────────────────────────────────────────────────────
def prepare_input(state: State) -> dict:
    """Extracts new messages and existing summary for compression."""
    messages = state.get("messages", [])
    last_idx = state.get("last_summarized_index", 0)
    existing_summary = state.get("summary", "")
    
    new_messages = messages[last_idx:]
    
    return {
        "new_messages": new_messages,
        "existing_summary": existing_summary or "None",
        "total_messages_count": len(messages)
    }

# ── 4. Node ───────────────────────────────────────────────────────────────
def summarize_node(state: State) -> dict:
    """Compresses conversation history into a rolling factual summary."""
    
    inputs = prepare_input(state)
    if not inputs["new_messages"]:
        return {}

    try:
        response = _chain.invoke(inputs)
        
        if not response or not response.content:
            logger.error("summarize_node failed: LLM returned no response.")
            return {}

        return {
            "summary": response.content.strip(),
            "last_summarized_index": inputs["total_messages_count"],
        }

    except Exception as e:
        logger.error(f"summarize_node failed: {e}")
        return {}


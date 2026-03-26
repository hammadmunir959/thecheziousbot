"""
info_node.py — Multi-intent info retrieval node with structured output.
"""

import json
from langchain_core.prompts import ChatPromptTemplate

from app.agent.state import State
from app.agent.llm_client import llm, advanced_llm
from app.utils.knowledge_base import search, ESSENTIAL_INFO
from app.agent.prompts.prompts import INFO_CLASSIFICATION_PROMPT
from app.schemas.schemas import InfoClassification, InfoClassificationData
from app.config.settings import settings

# ── 1. LLMs ───────────────────────────────────────────────────────────────
_primary = advanced_llm.bind(temperature=0).with_structured_output(InfoClassificationData).with_retry(stop_after_attempt=settings.MAX_LLM_RETRIES)
_fallback = llm.bind(temperature=0).with_structured_output(InfoClassificationData).with_retry(stop_after_attempt=settings.MAX_LLM_RETRIES)

# ── 2. Chain ──────────────────────────────────────────────────────────────
_prompt = ChatPromptTemplate.from_messages([
    ("system", INFO_CLASSIFICATION_PROMPT),
    ("system", "### CONTEXT\nEarlier Summary: {summary}"),
    ("human", "{user_msg}"),
])
_chain = _prompt | _primary.with_fallbacks([_fallback])

# ── 3. Utilities ──────────────────────────────────────────────────────────
def prepare_input(state: State) -> dict:
    """Extracts the latest user message and summary for classification."""
    messages = state.get("messages", [])
    user_message = messages[-1].content
    summary = state.get("summary", "None")
    return {
        "user_msg": user_message,
        "summary": summary,
    }


def get_kb_data(result: InfoClassificationData) -> str:
    """
    Iterates over ALL extracted intents, runs a KB search for each,
    and merges results into a single JSON payload.
    """
    if not result.intents:
        return json.dumps({"results": None, "essential_info": ESSENTIAL_INFO}, indent=2, ensure_ascii=False)

    merged_results: dict = {}

    for intent in result.intents:
        category = (intent.category or "").lower().strip()
        query    = (intent.query    or "").lower().strip()

        # Skip null/empty intents (greetings etc.)
        if not category and not query:
            continue

        if category not in ("menu", "locations", "policies"):
            category = None

        data = search(category=category, query=query)
        intent_results = data.get("results")

        if intent_results is None:
            continue

        # ── Merge strategy ────────────────────────────────────────────────
        # search() returns results shaped as:
        #   {"menu": {...}}  /  {"locations": [...]}  /  {"policies": {...}}  / raw list/dict
        # We accumulate everything under a shared dict keyed by category.
        if isinstance(intent_results, dict):
            for key, value in intent_results.items():
                if key in merged_results and isinstance(merged_results[key], dict) and isinstance(value, dict):
                    merged_results[key].update(value)
                else:
                    merged_results[key] = value
        else:
            # Raw list (e.g. a list of branch strings for one city)
            label = category or query or "results"
            existing = merged_results.get(label)
            if isinstance(existing, list):
                existing.extend(intent_results)
            else:
                merged_results[label] = intent_results

    # Always attach essential_info so the chat node has fallback context
    final_payload = {
        "results": merged_results if merged_results else None,
        "essential_info": ESSENTIAL_INFO,
    }

    return json.dumps(final_payload, indent=2, ensure_ascii=False)


# ── 4. Node ───────────────────────────────────────────────────────────────
def info_node(state: State) -> dict:
    """Classifies ALL user intents and retrieves information from the KB."""

    inputs = prepare_input(state)

    try:
        result: InfoClassificationData = _chain.invoke(inputs)
        info_json = get_kb_data(result)

    except Exception:
        # Fallback: return essential info overview
        fallback = InfoClassificationData(intents=[InfoClassification(category=None, query=None)])
        info_json = get_kb_data(fallback)

    return {"info_data": info_json}
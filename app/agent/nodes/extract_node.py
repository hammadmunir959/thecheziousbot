"""
extract_node.py — Structured order extraction via LLM chain with fallback.
"""
from typing import Any, Dict
import groq

from app.agent.state import State
from app.agent.llm_client import llm, advanced_llm
from app.schemas.schemas import OrderDetailsSchema
from app.config.settings import settings
from app.agent.prompts.prompts import EXTRACT_PROMPT
from app.agent.nodes.nodes_utils import prepare_extraction_input, build_extraction_result

# ── 1. LLM / Chains ───────────────────────────────────────────────────────

_primary_llm  = llm.with_structured_output(OrderDetailsSchema).with_retry(stop_after_attempt=settings.MAX_LLM_RETRIES)
_fallback_llm = advanced_llm.with_structured_output(OrderDetailsSchema).with_retry(stop_after_attempt=settings.MAX_LLM_RETRIES)

_chain = EXTRACT_PROMPT | _primary_llm.with_fallbacks([_fallback_llm])


# ── 2. Node ───────────────────────────────────────────────────────────────

def extract_node(state: State) -> Dict[str, Any]:
    """Analyze conversation context to extract structured order details."""
    inputs = prepare_extraction_input(state)

    try:
        extraction = _chain.invoke(inputs)
        if not extraction:
            return {
                "order_errors": ["I had trouble reading your order. Could you rephrase it?"],
                "order_status": "extracting",
            }
        return build_extraction_result(extraction)

    except Exception as e:
        if isinstance(e, groq.RateLimitError):
            return {
                "order_errors": ["We're a little busy right now — please try again in a few seconds! 🕐"],
                "order_status": "extracting",
            }
        return {
            "order_errors": [f"Something went wrong: {e}. Please try again."],
            "order_status": "extracting",
        }

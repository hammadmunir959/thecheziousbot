"""
nodes_utils.py — Specialized helpers for LangGraph nodes.
"""

import logging
from typing import List
from app.config.settings import settings

from app.utils.utils import normalize_address
from app.agent.prompts.prompts import VALIDATION_EXPLAIN_PROMPT
logger = logging.getLogger(__name__)
    
VALID_PAYMENT_METHODS = {"cash", "card", "online"}


def validate_fields(
    items: list, 
    address: str, 
    payment: str, 
    warnings: list = None
) -> List[str]:
    """
    validation for the entire order.
    Returns: list of errors
    """
    from app.utils.knowledge_base import LOCATIONS
    errors = []

    # 1. Cart Validation
    if not items:
        return ["Your cart is empty. Please tell me what you'd like to order."]
    
    # Check for unresolved items (marked with price 0 in resolver)
    for i in items:
        if i.price == 0:
            errors.append(f"The ITEM '{i.item}' is NOT FOUND in Menu or invalid. ")

    # 2. Address Validation (10-character rule + City coverage)
    addr = normalize_address((address or "").strip())
    if len(addr) < 10:
        errors.append("Address is too short. Please provide a complete delivery address (min 10 characters).")
    else:
        addr_lower = addr.lower()
        all_areas = [a.lower() for areas in LOCATIONS.values() for a in areas]
        if not any(city in addr_lower for city in LOCATIONS) and \
           not any(area in addr_lower for area in all_areas):
            errors.append(
                f"We only deliver to: {', '.join(LOCATIONS.keys())}. "
                "Please provide an address in a supported city."
            )

    # 3. Payment Method Validation
    if (payment or "").strip().lower() not in VALID_PAYMENT_METHODS:
        errors.append("Please specify a valid payment method: Cash, Card, or Online.")

    # 4. Integrate Extraction Warnings
    if warnings:
        errors.extend(warnings)

    return errors


def explain_errors_with_llm(errors: List[str], state: dict) -> str:
    """Uses LLM to turn a list of technical validation errors into a friendly user message."""
    from app.agent.llm_client import advanced_llm
    from app.utils.utils import build_menu_summary
    
    # 1. Prepare history and inputs
    messages = state.get("messages", [])
    history = messages[-settings.RECENT_CONTEXT_MESSAGES:] if messages else []
    
    error_txt = "\n".join(f"- {e}" for e in errors)
    menu_summary = build_menu_summary()
    
    # 2. Invoke LLM
    chain = VALIDATION_EXPLAIN_PROMPT | advanced_llm.bind(temperature=0).with_retry(stop_after_attempt=settings.MAX_LLM_RETRIES)
    try:
        response = chain.invoke({
            "errors": error_txt,
            "history": history,
            "menu": menu_summary
        })
        return response.content.strip()
    except Exception as e:
        logger.exception("LLM failed to generate error explanation")
        return f"I need a little more info to proceed:\n{error_txt} "


# ---------------------------------------------------------------------------
# Extraction Node Helpers
# ---------------------------------------------------------------------------




def build_extraction_context(state: dict) -> str:
    """Build an XML context block from the current order state."""
    items = state.get("items", [])
    cart_txt = ", ".join(
        f"{i.quantity}x {i.item}{f' ({i.size})' if i.size and i.size.lower() != 'no size' else ''}"
        for i in items
    ) or "Empty"

    ctx = (
        f"<conversation_summary>{state.get('summary', '')}</conversation_summary>\n\n"
        f"<current_order_state>\n"
        f"<current_items>{cart_txt}</current_items>\n"
        f"<current_address>{state.get('delivery_address') or 'None'}</current_address>\n"
        f"<current_payment>{state.get('payment_method') or 'None'}</current_payment>\n"
        f"</current_order_state>"
    )

    errors = state.get("order_errors")
    if errors:
        ctx += f"\n\n[SIGNAL]: User is currently correcting errors in the order.\n<validation_errors>{errors}</validation_errors>"

    if state.get("order_status") == "validated":
        ctx += "\n\n[SIGNAL]: User is currently reviewing or modifying a completed order summary."

    return ctx


def prepare_extraction_input(state: dict) -> dict:
    """Gather all inputs needed by the extraction prompt."""

    from app.utils.utils import build_menu_summary
    
    messages = state.get("messages", [])
    
    return {
        "menu":         build_menu_summary(),
        "context":      build_extraction_context(state),
        "history":      messages[-settings.RECENT_CONTEXT_MESSAGES:] if messages else [],
        "user_message": messages[-1].content if messages else ""
    }


def build_extraction_result(extraction) -> dict:
    """Build a diff-only state update from a successful extraction."""
    from app.utils.utils import normalize_address, merge_items
    result = {
        "items":              merge_items(extraction.items or []),
        "order_errors":       [],
        "order_status":       "extracted",
    }

    raw_addr = (extraction.delivery_address or "").strip()
    if raw_addr:
        result["delivery_address"] = normalize_address(raw_addr)

    raw_pay = (extraction.payment_method or "").strip().lower()
    if raw_pay:
        result["payment_method"] = raw_pay

    return result

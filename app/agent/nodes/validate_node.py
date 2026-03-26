from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import interrupt
from app.agent.state import State
from app.utils.utils import is_cancel_command, _resolve_items, build_price_map
from .nodes_utils import validate_fields, explain_errors_with_llm
from app.agent.prompts.prompts import SYSTEM_ORDER_CANCELLED


def validate_node(state: State) -> dict:
    """
    Validate the current order state.
    Consolidates cart, address, and payment checks into a single pass.
    Uses LLM for dynamic feedback and interrupt for user correction.
    """
            
    # 1. Gather inputs
    items    = state.get("items", [])
    address  = state.get("delivery_address")
    payment  = state.get("payment_method")
    
    # 2. Resolve RAW Items against live menu
        # a. using build_price_map() to get the price map and size based items
    price_map, size_based = build_price_map()
        # b. using _resolve_items() to resolve the items against the price map and size based items
        # get the warnings from the resolution or resolved items only

    resolved_items, warnings = _resolve_items(items, price_map, size_based)
    
    # Combine resolution warnings with any extraction errors to avoid dropping them
    extraction_errors = state.get("order_errors", [])
    all_warnings = (warnings or []) + extraction_errors
    
    # 3. Execute Validation
    errors = validate_fields(
        items=resolved_items,
        address=address,
        payment=payment,
        warnings=all_warnings
    )

    # 3. Handle Validation Outcome
    if errors:
        # Generate friendly explanation using LLM
        explanation = explain_errors_with_llm(errors, state)
        
        # Pause execution and wait for user correction
        # The return value of interrupt() is the user input obtained upon resumption
        user_input = interrupt(explanation)

        # Process user response upon resumption
        if is_cancel_command(user_input):
            
            return {
                "order_status":        "cancelled",
                "order_errors":        [],
                "items":               [],
                "delivery_address":    None,
                "payment_method":      None,
                "messages":            [
                    AIMessage(content=explanation), 
                    HumanMessage(content=user_input),
                    AIMessage(content=SYSTEM_ORDER_CANCELLED)
                ],
            }

        # For any other input, trigger re-extraction
        return {
            "order_status":        "extracting",
            "order_errors":        errors,
            "messages": [
                AIMessage(content=explanation), 
                HumanMessage(content=user_input)
            ]
        }

    # Validation Passed
    return {
        "order_status":        "validated",
        "order_errors":        [],
        "items":               resolved_items,
    }

# app/agent/order_subgraph/nodes/confirm_node.py
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import interrupt
from app.agent.state import State
from app.utils.utils import (
    compute_total, 
    format_order_summary, 
    is_cancel_command, 
    is_confirmed
)

def confirm_node(state: State) -> dict:
    """Show order summary and handle human-in-the-loop confirmation."""
    
    address     = state.get("delivery_address")
    payment     = state.get("payment_method")
    items       = state.get("items", [])
    
    # Calculate total right before confirmation
    total = compute_total(items) if items else 0

    # 1. Format Hardcoded Summary
    summary = format_order_summary(items, total, address, payment)
    
    # 2. Trigger Interrupt
    # Execution pauses here. Upon resumption, user_input is the block return.
    user_input = interrupt(summary)
    
    # 3. Process Resumption Decision
    text = user_input.strip().lower()
    
    # CANCEL: Exit to END
    if is_cancel_command(text):
        from app.agent.prompts.prompts import SYSTEM_ORDER_CANCELLED
        return {
            "order_status":        "cancelled",
            "order_errors":        [],
            "items":               [],
            "delivery_address":    None,
            "payment_method":      None,
            "messages":            [
                AIMessage(content=summary), 
                HumanMessage(content=user_input),
                AIMessage(content=SYSTEM_ORDER_CANCELLED)
            ],
        }
    
    # CONFIRM: Proceed to Execution
    if is_confirmed(text):
        return {
            "order_status":      "confirmed",
            "messages": [
                AIMessage(content=summary),
                HumanMessage(content=user_input)
            ]
        }
    
    # EDIT: Return to Extraction for anything else
    return {
        "order_status":        "extracting",  # Reset status, routing will lead to 'extract'
        "messages": [
            AIMessage(content=summary),
            HumanMessage(content=user_input)
        ]
    }
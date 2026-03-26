"""
execute_order_node.py — Final order execution via service layer.
"""
from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from app.agent.state import State
from app.services.services import create_order, UserNotFoundError, ServiceError
from app.agent.prompts.prompts import (
    EXECUTE_UNREGISTERED_MSG,
    EXECUTE_SERVICE_ERROR_MSG,
    EXECUTE_GENERIC_ERROR_MSG,
)


from app.utils.utils import format_order_summary, compute_total

def execute_order_node(state: State, config: RunnableConfig) -> dict:
    """Submit the validated order to the service layer and return a final AIMessage."""
    
    user_id = config.get("configurable", {}).get("user_id", "guest")
    items   = state.get("items", [])
    address = state.get("delivery_address", "").strip()
    payment = state.get("payment_method", "").lower()
    total   = compute_total(items)

    try:
        order = create_order(
            user_id=user_id,
            items=items,
            delivery_address=address,
            payment_method=payment,
        )
        
        # Build the final detailed summary for the user
        item_lines_list = []
        for i in items:
            line = f"  • {i.quantity}x {i.item} ({i.size or 'Standard'})"
            if getattr(i, "quantity", 1) > 1:
                line += f" — ₨{i.price} each = ₨{i.quantity * i.price}"
            else:
                line += f" — ₨{i.price}"
            item_lines_list.append(line)
        
        item_lines = "\n".join(item_lines_list)
        
        success_content = (
            f"### Order Successfully Placed! \n\n"

            f"**Order ID:** #{order.id}\n\n"
            f"**Items:**\n{item_lines}\n\n"
            f"**Total Bill:** ₨{total}\n"
            f"**Delivery Address:** {address}\n"
            f"**Payment Method:** {payment.upper()}\n\n"
            "Our rider will be at your door in about 30-45 minutes. Thank you for choosing Cheezious! 🍕"
        )

        return {
            "order_status":      "created",
            "order_errors":      [],
            "order_id":          order.id,
            "items":             [],
            "delivery_address":  None,
            "payment_method":    None,
            "messages": [AIMessage(content=success_content)],
        }
    except UserNotFoundError:
        return {
            "order_status": "cancelled",
            "order_errors": ["user_not_registered"],
            "messages": [AIMessage(content=EXECUTE_UNREGISTERED_MSG)],
            "order_id": None
        }
    except ServiceError as e:
        return {
            "order_status": "cancelled",
            "order_errors": [f"service_error: {e}"],
            "messages": [AIMessage(content=EXECUTE_SERVICE_ERROR_MSG.format(error=e))],
            "order_id": None
        }
    except Exception as e:
        return {
            "order_status": "cancelled",
            "order_errors": [f"unexpected_error: {e}"],
            "messages": [AIMessage(content=EXECUTE_GENERIC_ERROR_MSG.format(error=e))],
            "order_id": None
        }
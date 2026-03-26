from typing import Any, List, Literal, Optional
from langgraph.graph import MessagesState
from ..schemas.schemas import MenuItem


# Canonical order lifecycle statuses
ORDER_STATUSES = Literal[
    "extracting",              # Intermediate: Waiting for user input to parse/correct
    "extracted",               # Raw data parsed but not validated
    "validated",               # Verified, summary shown, waiting for final confirm
    "confirmed",               # User confirmed, about to execute
    "created",                 # Terminal: Order successfully placed
    "cancelled",               # Terminal: Order aborted
]


class State(MessagesState):
    """
    Conversation state for CheziousBot.
    Inherits `messages` from MessagesState.
    """

    # Intent classification (classify_intent_node)
    intent: Optional[str] = None  # "ORDER" | "INFO" | "SPAM"

    # Info retrieval (info_node)
    info_data: Optional[str] = None

    # Conversation memory (summarize_node)
    summary: str = ""
    last_summarized_index: int = 0

    # Order lifecycle
    order_status: Optional[ORDER_STATUSES] = None
    order_errors: List[str] = []

    # Order fields (shared with order subgraph via checkpoint)
    order_id: Optional[str] = None
    items: List[MenuItem] = []
    delivery_address: Optional[str] = None
    payment_method: Optional[Literal["cash", "card", "online"]] = None


#schemas.schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Annotated, List, Optional
from datetime import datetime
import re





class ConfirmationAnalysis(BaseModel):
    """Analysis of user's response to an order summary."""
    decision: Literal["confirm", "cancel", "edit"] = Field(
        description="The user's intent: confirm the order, cancel/stop, or edit/change items."
    )
    modifications: Optional[str] = Field(
        default=None,
        description="If decision is 'edit', describe what the user wants to change (e.g., 'add 1 more pizza')."
    )


class IntentClassification(BaseModel):
    """Classify whether the user wants to place an order or get info."""
    
    reasoning : str = Field(
        description="Briefly explain why this intent was chosen"
    )
    
    intent: Literal["ORDER", "INFO", "SPAM"] = Field(
    description=(
        "'ORDER' if the user explicitly wants to place, modify, or cancel an order. "
        "'INFO' for relevant business inquiries (menu, hours, location, policies, or polite greetings). "
        "'SPAM' for nonsensical text, gibberish, offensive content, or topics completely unrelated to the business."
    )
)


class InfoClassification(BaseModel):
    category: Optional[str] = Field(
        default=None,
        description=(
            "Knowledge base category to search: 'menu', 'locations', or 'policies'. "
            "Null for greetings or other irrelevant content."
        )
    )
    query: Optional[str] = Field(
        default=None,
        description=(
            "Short, specific search term to look up within the category (e.g. 'tikka pizza', 'DHA', 'hours'). "
            "Null if the user wants the full category returned (e.g. 'show me the menu')."
        )
    )



class InfoClassificationData(BaseModel):
    intents: List[InfoClassification] = Field(
        default_factory=list,
        description="List of classified intents extracted from the conversation. Can be empty if no info-related intent is detected."
    )



# ── Internal Agent/Tool Schemas ──────────────────────────────────────────────

class MenuItem(BaseModel):
    """Represents a single item in a cart for validation purposes."""
    item: str = Field(description="Name of the base item (e.g. 'Fajita Pizza'). Do NOT include size.")
    size: Optional[str] = Field(default=None, description="Item size if applicable (e.g., 'Small', 'Large')")
    quantity: int = Field(default=1, description="Number of units for this item", ge=1)
    price: int = Field(default=0, description="Price per unit (populated during validation)", ge=0)


class OrderDetailsSchema(BaseModel):
    """Structured extraction of order details (used by order subgraph)."""
    items: List[MenuItem] = Field(
        default_factory=list,
        description="List of menu items. Each item MUST have 'item' (base name, e.g., 'fajita pizza') and 'quantity'."
    )
    delivery_address: Optional[str] = Field(
        default=None,
        description="The customer's full delivery street address if provided."
    )
    payment_method: Optional[Literal["cash", "card", "online"]] = Field(
        default=None,
        description="The chosen payment method, if provided."
    )


# ── User Registration Schemas ────────────────────────────────────────────────

class UserCreate(BaseModel):
    """Schema for creating a new user."""
    name: str = Field(
        ..., 
        min_length=2, 
        max_length=120,
        description="Full name of the user."
    )
    phone: str = Field(
        ...,
        description="Phone number in format +92XXXXXXXXXX or 03XXXXXXXXX."
    )

    @field_validator("name")
    def validate_name(cls, v):
        if not re.match(r"^[A-Za-z'-]+(?:\s[A-Za-z'-]+)*$", v):
            raise ValueError("Name contains invalid characters.")
        return v

    @field_validator("phone")
    def validate_and_normalize_phone(cls, v):
        if not re.match(r"^(?:\+92\d{10}|03\d{9})$", v):
            raise ValueError("Invalid phone number format.")
        
        # Normalization: Convert 03XXXXXXXXX to +923XXXXXXXXX
        if v.startswith("03"):
            v = "+92" + v[1:]
            
        return v


class UserResponse(BaseModel):
    """Schema for user response data."""
    id: str
    name: str
    phone: str
    created_at: datetime



# ── Chat Endpoint Schemas ───────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Schema for a chat message request."""
    message: str = Field(..., min_length=1, description="The user's message text.")
    user_id: str = Field("guest", description="Unique identifier for the user.")
    thread_id: Optional[str] = Field(None, description="Thread ID for conversation continuity.")


class ChatResponse(BaseModel):
    """Schema for the agent's chat response."""
    reply: str
    thread_id: str


# ── Order Response Schemas ───────────────────────────────────────────────────

class OrderItemResponse(BaseModel):
    """Schema for a single item in a completed order."""
    item_name: str
    qty: int
    price: int
    total: int


class OrderResponse(BaseModel):
    """Schema for full order details."""
    id: str
    user_id: str
    status: str
    payment_method: str
    created_at: datetime
    delivery_address: Optional[str]
    total_bill: int
    items: List[OrderItemResponse]


class OrderListResponse(BaseModel):
    """Schema for a list of orders."""
    orders: List[OrderResponse]

from sqlmodel import SQLModel, Relationship, Field
from sqlalchemy import Computed
# from pydantic import Field
import uuid
from typing import Optional,  Literal, List, TYPE_CHECKING
import re
from datetime import datetime, timezone

if TYPE_CHECKING:
    from .users_model import User

from enum import Enum

class OrderStatus(str, Enum):
    in_cart = "in_cart"
    created ="created"
    on_the_way = "on_the_way"
    delivered = "delivered"
    cancelled = "cancelled"

class PaymentMethod(str, Enum):
    cash = "cash"
    card = "card"
    online = "online"

# --- ORDER MODEL ---
class Order(SQLModel, table=True):
    __tablename__ = "orders"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    status: OrderStatus = Field(default=OrderStatus.in_cart)
    payment_method: PaymentMethod = Field(default=PaymentMethod.cash)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    delivery_address: Optional[str] = Field(default=None, min_length=10, max_length=500)
    total_bill: int = Field(default=0, description="Total bill in PKR")

    user: "User" = Relationship(back_populates="orders")
    items: List["OrderItem"] = Relationship(
        back_populates="order",
        cascade_delete=True
    )

    def compute_total(self) -> int:
        """Calculate total from items and store it."""
        self.total_bill = sum(item.total for item in self.items)
        return self.total_bill

# --- ORDER ITEM MODEL ---
class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    order_id: str = Field(foreign_key="orders.id", index=True)
    item_name: str = Field(description="Name of the Menu Item")
    qty: int = Field(ge=1)
    price: int = Field(ge=0)
    
    total: int | None = Field(default=None, sa_column_args=(Computed("qty * price"),))
    
    order: "Order" = Relationship(
        back_populates="items",
        
        )
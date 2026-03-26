# import uuid
# import re
# from typing import Optional, List, Literal
# from datetime import datetime, timezone
# from sqlmodel import SQLModel, Relationship, Field

# # --- USER MODEL ---
# class User(SQLModel, table=True):
#     __tablename__ = "users"
    
#     id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
#     name: str = Field(
#         default="Guest", 
#         min_length=2, 
#         max_length=120,
#         pattern=r"^[A-Za-z'-]+(?:\s[A-Za-z'-]+)*$" 
#     )
    
#     phone: str = Field(
#         ...,
#         pattern=r"^(?:\+92|03)\d{9}$",
#         max_length=13
#     )
    
#     created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
#     orders: List["Order"] = Relationship(back_populates="user")
#     sessions: List["Session"] = Relationship(
#         back_populates="user",
#         cascade_delete=True

#          )
    

# # --- ORDER MODEL ---
# class Order(SQLModel, table=True):
#     __tablename__ = "orders"
    
#     id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
#     user_id: str = Field(foreign_key="users.id", index=True)
#     status: Literal["pending", "completed", "cancelled"] = Field(default="pending")
#     payment_method: Literal["cash", "card", "online"] = Field(default="cash")
#     created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
   
#     delivery_address: Optional[str] = Field(default=None, min_length=10, max_length=500)

#     user: "User" = Relationship(back_populates="orders")
#     items: List["OrderItem"] = Relationship(
#         back_populates="order",
#         cascade_delete=True
#         )
    
#     @property
#     def total_bill(self) -> int:
#         return sum(item.total for item in self.items)


# # --- ORDER ITEM MODEL ---
# class OrderItem(SQLModel, table=True):
#     __tablename__ = "order_items"
    
#     id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
#     order_id: str = Field(foreign_key="orders.id", index=True)
#     item_name: str = Field(description="Name of the Menu Item")
#     qty: int = Field(ge=1)
#     price: int = Field(ge=0)
    
#     order: "Order" = Relationship(
#         back_populates="items",
    
        
        
#         )

#     @property
#     def total(self) -> int:
#         return self.qty * self.price
    
    
    
# # Sessions


# class Session(SQLModel, table=True):
#     __tablename__ = "sessions"

#     id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
#     user_id: str = Field(foreign_key="users.id", index=True)
    
#     # Timing
#     created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

#     # Relationships
#     user: "User" = Relationship(
#         back_populates="sessions",
#         cascade_delete=True
        
#         )
    
#     messages: List["ChatMessage"] = Relationship(
#         back_populates="session",
#         cascade_delete=True,
#         sa_relationship_kwargs={"order_by": "ChatMessage.created_at"}
#     )

# class ChatMessage(SQLModel, table=True):
#     __tablename__ = "chat_messages"

#     id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
#     session_id: str = Field(..., foreign_key="sessions.id", index=True)
    
#     role: Literal["HumanMessage", "AIMessage"] = Field(...)
#     content: str = Field(min_length=1)
#     created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

#     # Relationships
#     session: "Session" = Relationship(
#         back_populates="messages",
   
#         )
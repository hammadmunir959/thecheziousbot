import uuid
import re
from typing import Optional, List, Literal , TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Relationship, Field

if TYPE_CHECKING:

    from .order_model import Order
    from .session_model import Session
    

# --- USER MODEL ---
class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    name: str = Field(
        default="Guest", 
        min_length=2, 
        max_length=120,
        regex=r"^[A-Za-z'-]+(?:\s[A-Za-z'-]+)*$" 
    )
    
    phone: str = Field(
        ...,
        regex=r"^(?:\+92|03)\d{9}$",
        max_length=13
    )
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    orders: List["Order"] = Relationship(
        back_populates="user",
        cascade_delete=True
        
        )
    sessions: List["Session"] = Relationship(
        back_populates="user",
        cascade_delete=True

         )
    
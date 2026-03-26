import uuid
from typing import Optional, List, Literal, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Relationship, Field

if TYPE_CHECKING:
    from .users_model import User


from enum import Enum

class RoleEnum(str, Enum):
    HumanMessage = "HumanMessage"
    AIMessage = "AIMessage"

class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    # cart : List[Cart] 
    
    # Timing
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    user: "User" = Relationship(
        back_populates="sessions",

        
        )
    
    
    
    # messages: List["ChatMessage"] = Relationship(
    #     back_populates="session",
    #     cascade_delete=True,
    #     sa_relationship_kwargs={"order_by": "ChatMessage.created_at"}
    # )

# class ChatMessage(SQLModel, table=True):
#     __tablename__ = "chat_messages"

#     id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
#     session_id: str = Field(..., foreign_key="sessions.id", index=True)
    
#     role: RoleEnum = Field(...)
#     content: str = Field(min_length=1)
#     created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

#     # Relationships
#     session: "Session" = Relationship(back_populates="messages")
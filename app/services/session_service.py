"""
session_service.py — Service layer for session management.
"""

import logging
from sqlmodel import Session, select
from ..database.db import engine
from ..models.session_model import Session as SessionModel
from ..models.users_model import User as UserModel

logger = logging.getLogger(__name__)

class SessionError(Exception):
    """Base class for session service errors."""
    pass

class SessionOwnershipError(SessionError):
    """Raised when a session does not belong to the provided user."""
    pass

class UserNotFoundError(SessionError):
    """Raised when a user is not found during session operations."""
    pass

def resolve_session_id(session_id: str, user_id: str) -> str:
    """
    Validates if the provided session_id belongs to the user_id.
    
    Args:
        session_id: The ID of the session to check.
        user_id: The ID of the user who should own the session.
        
    Returns:
        The same session_id if valid.
        
    Raises:
        SessionOwnershipError: If the session belongs to a different user or doesn't exist.
    """
    try:
        with Session(engine) as session:
            db_session = session.get(SessionModel, session_id)
            
            if not db_session:
                raise SessionOwnershipError(f"Session '{session_id}' not found.")
            
            if db_session.user_id != user_id:
                logger.warning(f"Session ownership mismatch: Session {session_id} belongs to {db_session.user_id}, but {user_id} tried to access it.")
                raise SessionOwnershipError(f"Session '{session_id}' does not belong to user '{user_id}'.")
            
            return session_id
            
    except SessionOwnershipError:
        raise
    except Exception as e:
        logger.exception(f"Error resolving session {session_id} for user {user_id}")
        raise SessionError(f"Internal error during session resolution: {str(e)}")

def get_session_id(user_id: str) -> str:
    """
    Generates and persists a new session for the given user.
    
    Args:
        user_id: The ID of the user for whom to create a session.
        
    Returns:
        The newly generated session_id.
        
    Raises:
        UserNotFoundError: If the user does not exist in the database.
    """
    try:
        with Session(engine) as session:
            # Enforce user existence before creating session
            user = session.get(UserModel, user_id)
            if not user:
                raise UserNotFoundError(f"Cannot create session: User '{user_id}' not found.")
            
            new_session = SessionModel(user_id=user_id)
            session.add(new_session)
            session.commit()
            session.refresh(new_session)
            
            logger.info(f"Generated new session {new_session.id} for user {user_id}")
            return new_session.id
            
    except UserNotFoundError:
        raise
    except Exception as e:
        logger.exception(f"Error creating session for user {user_id}")
        raise SessionError(f"Failed to generate session: {str(e)}")

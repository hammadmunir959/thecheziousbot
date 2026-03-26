from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from sqlalchemy.exc import IntegrityError

from ....database.db import get_db
from ....models.users_model import User
from ....schemas.schemas import UserCreate, UserResponse
from sqlmodel import select

router = APIRouter()

@router.post("", response_model=UserResponse, status_code=201)
def create_user(user_data: UserCreate, session: Session = Depends(get_db)):
    """
    Register a new user in the system.
    """
    
    try:
        # Check if user with this normalized phone already exists
        statement = select(User).where(User.phone == user_data.phone)
        existing_user = session.exec(statement).first()
        
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="A user with this phone number is already registered."
            )
        
        db_user = User(
            name=user_data.name,
            phone=user_data.phone
        )
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user
        
    except HTTPException:
        raise
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=400, 
            detail="A user with this information already exists."
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to create user: {str(e)}"
        )

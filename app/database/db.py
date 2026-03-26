import os
from sqlmodel import Session, create_engine, SQLModel
from ..config.settings import settings

# Ensure folder exists
os.makedirs("./data/", exist_ok=True)

# Create the engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create tables
def init_db():
    from ..models import __all__
    SQLModel.metadata.create_all(engine)

# Session Generator
def get_db():
    with Session(engine) as session:
        yield session

# Initialize DB on import
init_db()
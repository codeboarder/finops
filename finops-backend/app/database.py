"""
Database initialization and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os

from app.models.cost_history import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./finops.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_history_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db() -> Session:
    """Get database session with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """Get a new database session (caller must close)."""
    return SessionLocal()

"""Dependency injection for FastAPI routes."""

from typing import Generator

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.datastore.local import LocalDataStore
from app.services.datastore.base import DataStore


def get_db() -> Generator[Session, None, None]:
    """Provide a database session for request handling."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_datastore() -> DataStore:
    """Provide a DataStore instance."""
    return LocalDataStore()

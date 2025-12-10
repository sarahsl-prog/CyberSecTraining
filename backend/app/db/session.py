"""Database session configuration."""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

# Create engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=settings.debug,  # Log SQL in debug mode
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI routes.

    Yields a database session and ensures it's properly closed after use.

    Usage:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

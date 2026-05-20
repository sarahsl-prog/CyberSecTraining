"""Database session configuration."""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool  # For SQLite

from app.config import settings

# Create engine with connection pooling (Fix Issue #7)
if settings.database_url.startswith("sqlite"):
    # SQLite-specific configuration with pooling
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        echo=settings.debug,
        poolclass=StaticPool,  # Use a single connection for SQLite
        pool_pre_ping=True,  # Verify connections before use
    )
else:
    # For PostgreSQL/MySQL with proper pooling
    from sqlalchemy.pool import QueuePool
    engine = create_engine(
        settings.database_url,
        echo=settings.debug,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=3600,   # Recycle connections after 1 hour
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

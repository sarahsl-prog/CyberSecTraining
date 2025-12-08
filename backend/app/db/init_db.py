"""Database initialization."""

from pathlib import Path

from app.config import settings
from app.db.session import engine
from app.models import Base


def init_db() -> None:
    """Initialize the database by creating all tables."""
    # Ensure data directory exists
    data_dir = settings.data_dir
    if isinstance(data_dir, str):
        data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    # Create all tables
    Base.metadata.create_all(bind=engine)

"""SQLAlchemy base model and common mixins."""

import uuid
from datetime import datetime, UTC
from typing import Any

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower()


def _utc_now() -> datetime:
    """Get current UTC time as a timezone-aware datetime."""
    return datetime.now(UTC)


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns."""

    created_at = Column(DateTime, default=_utc_now, nullable=False)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now, nullable=False)


class IdMixin:
    """Mixin that adds a UUID primary key."""

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

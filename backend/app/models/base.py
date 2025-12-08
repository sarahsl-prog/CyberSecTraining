"""SQLAlchemy base model and common mixins."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower()


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns."""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class IdMixin:
    """Mixin that adds a UUID primary key."""

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

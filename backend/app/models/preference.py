"""Preference model for storing user preferences as key-value pairs."""

from sqlalchemy import Column, String, Text

from app.models.base import Base, TimestampMixin


class Preference(Base, TimestampMixin):
    """Stores user preferences as key-value pairs."""

    __tablename__ = "preferences"

    user_id = Column(String(36), primary_key=True)  # "local" for single-user
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Preference(user={self.user_id}, key={self.key})>"

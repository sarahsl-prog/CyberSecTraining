"""Progress model for tracking user progress through scenarios."""

from sqlalchemy import Column, String, Boolean, Integer, DateTime

from app.models.base import Base, IdMixin, TimestampMixin


class Progress(Base, IdMixin, TimestampMixin):
    """Tracks user progress through scenarios."""

    __tablename__ = "progress"

    user_id = Column(String(36), nullable=False, index=True)  # "local" for single-user
    scenario_id = Column(String(100), nullable=False, index=True)
    completed = Column(Boolean, default=False)
    score = Column(Integer, nullable=True)
    hints_used = Column(Integer, default=0)
    time_spent = Column(Integer, default=0)  # seconds
    completed_at = Column(DateTime, nullable=True)
    last_accessed_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Progress(scenario={self.scenario_id}, completed={self.completed})>"

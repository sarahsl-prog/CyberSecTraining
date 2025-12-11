"""Scan model for network scan operations."""

from sqlalchemy import Column, String, DateTime, Text, Integer, Float

from app.models.base import Base, IdMixin, TimestampMixin


class Scan(Base, IdMixin, TimestampMixin):
    """Represents a network scan operation."""

    __tablename__ = "scans"

    network_id = Column(String(36), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=True)
    scan_type = Column(String(20), nullable=False)  # quick, deep
    status = Column(String(20), nullable=False)  # pending, in_progress, completed, stopped, failed

    # Scan configuration
    target_range = Column(String(50), nullable=True)  # e.g., "192.168.1.0/24"
    port_range = Column(String(100), nullable=True)  # e.g., "1-1024" or "1-65535"

    # Scan timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Scan progress
    progress = Column(Float, default=0.0, nullable=True)
    scanned_hosts = Column(Integer, default=0, nullable=True)
    total_hosts = Column(Integer, default=0, nullable=True)

    # Results summary (JSON stored as text)
    results_summary = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Scan(id={self.id}, type={self.scan_type}, status={self.status})>"

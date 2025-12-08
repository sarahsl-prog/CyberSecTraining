"""Topology model for network device connections."""

from sqlalchemy import Column, String, ForeignKey

from app.models.base import Base


class Topology(Base):
    """Represents connections between network devices."""

    __tablename__ = "topology"

    device_id = Column(String(36), ForeignKey("devices.id"), primary_key=True)
    connected_to_device_id = Column(String(36), ForeignKey("devices.id"), primary_key=True)
    connection_type = Column(String(50), nullable=True)  # e.g., "wired", "wireless", "unknown"

    def __repr__(self) -> str:
        return f"<Topology(from={self.device_id}, to={self.connected_to_device_id})>"

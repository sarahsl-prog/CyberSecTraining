"""Device model for discovered network devices."""

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base, IdMixin, TimestampMixin


class Device(Base, IdMixin, TimestampMixin):
    """Represents a discovered network device."""

    __tablename__ = "devices"

    network_id = Column(String(36), nullable=False, index=True)
    ip = Column(String(45), nullable=False)  # Supports IPv6
    mac = Column(String(17), nullable=True)  # MAC address
    hostname = Column(String(255), nullable=True)
    device_type = Column(String(50), nullable=True)  # router, pc, mobile, iot, etc.
    os = Column(String(100), nullable=True)  # Operating system if detected
    last_seen = Column(DateTime, nullable=True)

    # Relationships
    vulnerabilities = relationship("Vulnerability", back_populates="device", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Device(id={self.id}, ip={self.ip}, hostname={self.hostname})>"

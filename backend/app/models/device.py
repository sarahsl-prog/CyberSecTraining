"""
Device model for discovered network devices.

This model stores information about devices discovered during network scans,
including their network configuration, vendor information, and detected services.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, IdMixin, TimestampMixin


class Device(Base, IdMixin, TimestampMixin):
    """
    Represents a discovered network device.

    Attributes:
        scan_id: ID of the scan that discovered this device
        ip: IP address of the device
        mac: MAC address (if detected)
        hostname: Resolved hostname
        vendor: Device manufacturer (from MAC lookup)
        device_type: Category (router, server, workstation, etc.)
        os: Detected operating system
        os_accuracy: Confidence level of OS detection (0-100)
        is_up: Whether the device is currently responding
        last_seen: When the device was last detected
        open_ports_json: JSON string of open ports data
    """

    __tablename__ = "devices"

    # Scan reference
    scan_id = Column(String(36), nullable=False, index=True)

    # Network information
    ip = Column(String(45), nullable=False)  # Supports IPv6
    mac = Column(String(17), nullable=True)  # MAC address
    hostname = Column(String(255), nullable=True)

    # Device identification
    vendor = Column(String(100), nullable=True)  # Manufacturer name
    device_type = Column(String(50), nullable=True)  # router, server, workstation, etc.
    os = Column(String(100), nullable=True)  # Operating system if detected
    os_accuracy = Column(Integer, default=0)  # OS detection confidence (0-100)

    # Status
    is_up = Column(Boolean, default=True)
    last_seen = Column(DateTime, nullable=True)

    # Open ports stored as JSON
    open_ports_json = Column(Text, nullable=True)

    # Relationships
    vulnerabilities = relationship(
        "Vulnerability",
        back_populates="device",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Device(id={self.id}, ip={self.ip}, hostname={self.hostname})>"

    def to_dict(self) -> dict:
        """Convert device to dictionary."""
        import json

        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "ip": self.ip,
            "mac": self.mac,
            "hostname": self.hostname,
            "vendor": self.vendor,
            "device_type": self.device_type,
            "os": self.os,
            "os_accuracy": self.os_accuracy,
            "is_up": self.is_up,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "open_ports": json.loads(self.open_ports_json) if self.open_ports_json else [],
            "vulnerability_count": len(self.vulnerabilities) if self.vulnerabilities else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

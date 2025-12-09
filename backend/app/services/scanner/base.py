"""
Base scanner interface and data models.

This module defines the abstract interface for network scanners and the
data models used throughout the scanning system. All scanner implementations
should inherit from BaseScannerInterface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class ScanType(str, Enum):
    """
    Types of network scans supported by the system.

    QUICK: Fast scan of common ports (1-1024), suitable for initial discovery
    DEEP: Comprehensive scan of all ports (1-65535), takes longer but thorough
    DISCOVERY: Host discovery only, no port scanning
    CUSTOM: User-defined port range scan
    """
    QUICK = "quick"
    DEEP = "deep"
    DISCOVERY = "discovery"
    CUSTOM = "custom"


class ScanStatus(str, Enum):
    """
    Status of a network scan operation.

    PENDING: Scan has been created but not started
    RUNNING: Scan is currently in progress
    COMPLETED: Scan finished successfully
    FAILED: Scan encountered an error
    CANCELLED: Scan was cancelled by user
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PortInfo:
    """
    Information about an open port on a device.

    Attributes:
        port: Port number (1-65535)
        protocol: Transport protocol (tcp/udp)
        state: Port state (open, closed, filtered)
        service: Detected service name (e.g., "ssh", "http")
        version: Service version if detected
        banner: Service banner/response if available
    """
    port: int
    protocol: str = "tcp"
    state: str = "open"
    service: Optional[str] = None
    version: Optional[str] = None
    banner: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert port info to dictionary."""
        return {
            "port": self.port,
            "protocol": self.protocol,
            "state": self.state,
            "service": self.service,
            "version": self.version,
            "banner": self.banner,
        }


@dataclass
class DeviceInfo:
    """
    Information about a discovered network device.

    Attributes:
        ip: IP address of the device
        mac: MAC address (if available, only for local network)
        hostname: Resolved hostname
        vendor: Device vendor from MAC address lookup
        os: Detected operating system
        os_accuracy: Confidence level of OS detection (0-100)
        device_type: Type of device (router, computer, IoT, etc.)
        open_ports: List of open ports with service info
        last_seen: Timestamp when device was last detected
        is_up: Whether the device responded to probes
    """
    ip: str
    mac: Optional[str] = None
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    os: Optional[str] = None
    os_accuracy: int = 0
    device_type: Optional[str] = None
    open_ports: list[PortInfo] = field(default_factory=list)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    is_up: bool = True

    def to_dict(self) -> dict:
        """Convert device info to dictionary."""
        return {
            "ip": self.ip,
            "mac": self.mac,
            "hostname": self.hostname,
            "vendor": self.vendor,
            "os": self.os,
            "os_accuracy": self.os_accuracy,
            "device_type": self.device_type,
            "open_ports": [p.to_dict() for p in self.open_ports],
            "last_seen": self.last_seen.isoformat(),
            "is_up": self.is_up,
        }


@dataclass
class ScanResult:
    """
    Complete result of a network scan operation.

    Attributes:
        scan_id: Unique identifier for this scan
        target_range: Network range that was scanned
        scan_type: Type of scan performed
        status: Current status of the scan
        devices: List of discovered devices
        started_at: Timestamp when scan started
        completed_at: Timestamp when scan finished
        error_message: Error message if scan failed
        progress: Scan progress percentage (0-100)
        scanned_hosts: Number of hosts scanned so far
        total_hosts: Total number of hosts to scan
    """
    scan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_range: str = ""
    scan_type: ScanType = ScanType.QUICK
    status: ScanStatus = ScanStatus.PENDING
    devices: list[DeviceInfo] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: float = 0.0
    scanned_hosts: int = 0
    total_hosts: int = 0

    def to_dict(self) -> dict:
        """Convert scan result to dictionary."""
        return {
            "scan_id": self.scan_id,
            "target_range": self.target_range,
            "scan_type": self.scan_type.value,
            "status": self.status.value,
            "devices": [d.to_dict() for d in self.devices],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "progress": self.progress,
            "scanned_hosts": self.scanned_hosts,
            "total_hosts": self.total_hosts,
            "device_count": len(self.devices),
        }


class BaseScannerInterface(ABC):
    """
    Abstract base class for network scanner implementations.

    All scanner implementations must inherit from this class and implement
    the required methods. This allows for different scanner backends
    (nmap, scapy, etc.) to be used interchangeably.
    """

    @abstractmethod
    async def scan_network(
        self,
        target: str,
        scan_type: ScanType = ScanType.QUICK,
        port_range: Optional[str] = None,
    ) -> ScanResult:
        """
        Perform a network scan on the specified target.

        Args:
            target: IP address, range (192.168.1.0/24), or hostname
            scan_type: Type of scan to perform
            port_range: Custom port range (e.g., "22,80,443" or "1-1000")

        Returns:
            ScanResult containing discovered devices and scan metadata
        """
        pass

    @abstractmethod
    async def get_scan_progress(self, scan_id: str) -> float:
        """
        Get the current progress of a running scan.

        Args:
            scan_id: Unique identifier of the scan

        Returns:
            Progress percentage (0.0 to 100.0)
        """
        pass

    @abstractmethod
    async def cancel_scan(self, scan_id: str) -> bool:
        """
        Cancel a running scan.

        Args:
            scan_id: Unique identifier of the scan to cancel

        Returns:
            True if scan was cancelled, False if scan not found or already complete
        """
        pass

    @abstractmethod
    async def discover_hosts(self, target: str) -> list[str]:
        """
        Perform host discovery without port scanning.

        This is a faster operation that only checks which hosts are up.

        Args:
            target: Network range to scan (e.g., "192.168.1.0/24")

        Returns:
            List of IP addresses that responded to probes
        """
        pass

"""
Pydantic schemas for network scanning API.

These schemas define the request and response models for the network
scanning endpoints. They provide automatic validation and documentation.
"""

from datetime import datetime, UTC
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.scanner.base import ScanType, ScanStatus


class PortResponse(BaseModel):
    """Response model for port information."""

    port: int = Field(..., description="Port number (1-65535)")
    protocol: str = Field(default="tcp", description="Transport protocol (tcp/udp)")
    state: str = Field(default="open", description="Port state")
    service: Optional[str] = Field(None, description="Detected service name")
    version: Optional[str] = Field(None, description="Service version")
    banner: Optional[str] = Field(None, description="Service banner")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "port": 22,
                "protocol": "tcp",
                "state": "open",
                "service": "ssh",
                "version": "OpenSSH 8.9",
                "banner": None,
            }
        }
    )


class DeviceResponse(BaseModel):
    """Response model for discovered device information."""

    ip: str = Field(..., description="IP address")
    mac: Optional[str] = Field(None, description="MAC address")
    hostname: Optional[str] = Field(None, description="Resolved hostname")
    vendor: Optional[str] = Field(None, description="Device manufacturer")
    os: Optional[str] = Field(None, description="Detected operating system")
    os_accuracy: int = Field(default=0, description="OS detection confidence (0-100)")
    device_type: Optional[str] = Field(None, description="Device category")
    open_ports: list[PortResponse] = Field(default_factory=list, description="Open ports")
    last_seen: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Last detection time")
    is_up: bool = Field(default=True, description="Whether device is responding")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ip": "192.168.1.1",
                "mac": "00:1A:2B:3C:4D:5E",
                "hostname": "router.local",
                "vendor": "Linksys",
                "os": "Linux",
                "os_accuracy": 95,
                "device_type": "router",
                "open_ports": [
                    {"port": 80, "protocol": "tcp", "state": "open", "service": "http"},
                    {"port": 443, "protocol": "tcp", "state": "open", "service": "https"},
                ],
                "last_seen": "2024-12-08T12:00:00Z",
                "is_up": True,
            }
        }
    )


class ScanRequest(BaseModel):
    """Request model for starting a network scan."""

    target: str = Field(
        ...,
        description="IP address or CIDR range to scan (e.g., '192.168.1.0/24')",
        examples=["192.168.1.0/24", "192.168.1.1"],
    )
    scan_type: ScanType = Field(
        default=ScanType.QUICK,
        description="Type of scan to perform",
    )
    port_range: Optional[str] = Field(
        None,
        description="Custom port range (e.g., '22,80,443' or '1-1000')",
        examples=["22,80,443", "1-1000", "80-8080"],
    )
    user_consent: bool = Field(
        ...,
        description="User confirms they own or have permission to scan this network",
    )

    @field_validator("target")
    @classmethod
    def validate_target_format(cls, v: str) -> str:
        """Basic validation of target format."""
        v = v.strip()
        if not v:
            raise ValueError("Target cannot be empty")
        return v

    @field_validator("port_range")
    @classmethod
    def validate_port_range(cls, v: Optional[str]) -> Optional[str]:
        """Validate port range format."""
        if v is None:
            return v

        v = v.strip()
        if not v:
            return None

        # Basic validation - detailed validation happens in scanner
        valid_chars = set("0123456789,-")
        if not all(c in valid_chars for c in v):
            raise ValueError(
                "Port range must contain only numbers, commas, and dashes"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "target": "192.168.1.0/24",
                "scan_type": "quick",
                "port_range": None,
                "user_consent": True,
            }
        }
    )


class ScanResponse(BaseModel):
    """Response model for scan results."""

    scan_id: str = Field(..., description="Unique identifier for this scan")
    target_range: str = Field(..., description="Network range that was scanned")
    scan_type: str = Field(..., description="Type of scan performed")
    status: str = Field(..., description="Current scan status")
    devices: list[DeviceResponse] = Field(
        default_factory=list,
        description="Discovered devices",
    )
    started_at: Optional[datetime] = Field(None, description="Scan start time")
    completed_at: Optional[datetime] = Field(None, description="Scan completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    progress: float = Field(default=0.0, description="Scan progress (0-100)")
    scanned_hosts: int = Field(default=0, description="Number of hosts scanned")
    total_hosts: int = Field(default=0, description="Total hosts to scan")
    device_count: int = Field(default=0, description="Number of devices found")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scan_id": "550e8400-e29b-41d4-a716-446655440000",
                "target_range": "192.168.1.0/24",
                "scan_type": "quick",
                "status": "completed",
                "devices": [],
                "started_at": "2024-12-08T12:00:00Z",
                "completed_at": "2024-12-08T12:02:30Z",
                "error_message": None,
                "progress": 100.0,
                "scanned_hosts": 254,
                "total_hosts": 254,
                "device_count": 5,
            }
        }
    )


class ScanStatusResponse(BaseModel):
    """Response model for scan status check."""

    scan_id: str = Field(..., description="Scan identifier")
    status: str = Field(..., description="Current status")
    progress: float = Field(..., description="Progress percentage (0-100)")
    device_count: int = Field(default=0, description="Devices found so far")
    error_message: Optional[str] = Field(None, description="Error if failed")


class PaginatedScanResponse(BaseModel):
    """Paginated response for scan history."""

    items: list[ScanResponse] = Field(default_factory=list, description="Scan items")
    total: int = Field(..., description="Total number of scans")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 10,
                "pages": 0,
            }
        }
    )


class NetworkInterfaceResponse(BaseModel):
    """Response model for network interface information."""

    name: str = Field(..., description="Interface name")
    ip: str = Field(..., description="IP address")
    netmask: str = Field(..., description="Network mask")
    network: str = Field(..., description="Network range in CIDR notation")
    is_private: bool = Field(..., description="Whether this is a private network")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "eth0",
                "ip": "192.168.1.100",
                "netmask": "255.255.255.0",
                "network": "192.168.1.0/24",
                "is_private": True,
            }
        }
    )


class NetworkValidationRequest(BaseModel):
    """Request model for network validation."""

    target: str = Field(
        ...,
        description="IP or network range to validate",
    )


class NetworkValidationResponse(BaseModel):
    """Response model for network validation."""

    valid: bool = Field(..., description="Whether the target is valid")
    target: str = Field(..., description="The validated target")
    is_private: bool = Field(default=False, description="Whether it's a private network")
    num_hosts: int = Field(default=0, description="Number of hosts in range")
    type: str = Field(default="unknown", description="Type: 'single_ip' or 'network'")
    error: Optional[str] = Field(None, description="Validation error message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "valid": True,
                "target": "192.168.1.0/24",
                "is_private": True,
                "num_hosts": 254,
                "type": "network",
                "error": None,
            }
        }
    )

"""
Pydantic schemas for device API.

These schemas define the request and response models for the device
management endpoints.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PortSchema(BaseModel):
    """Schema for port information."""

    port: int = Field(..., ge=1, le=65535, description="Port number")
    protocol: str = Field(default="tcp", description="Transport protocol")
    state: str = Field(default="open", description="Port state")
    service: Optional[str] = Field(None, description="Service name")
    version: Optional[str] = Field(None, description="Service version")
    banner: Optional[str] = Field(None, description="Service banner")


class DeviceBase(BaseModel):
    """Base schema for device data."""

    ip: str = Field(..., description="IP address")
    mac: Optional[str] = Field(None, description="MAC address")
    hostname: Optional[str] = Field(None, description="Hostname")
    vendor: Optional[str] = Field(None, description="Device vendor")
    device_type: Optional[str] = Field(None, description="Device type")
    os: Optional[str] = Field(None, description="Operating system")
    os_accuracy: int = Field(default=0, ge=0, le=100, description="OS detection confidence")


class DeviceCreate(DeviceBase):
    """Schema for creating a device."""

    scan_id: str = Field(..., description="ID of the scan that discovered this device")
    open_ports: list[PortSchema] = Field(default_factory=list, description="Open ports")


class DeviceUpdate(BaseModel):
    """Schema for updating a device."""

    hostname: Optional[str] = Field(None, description="Hostname")
    device_type: Optional[str] = Field(None, description="Device type")
    os: Optional[str] = Field(None, description="Operating system")

    class Config:
        extra = "forbid"


class DeviceResponse(DeviceBase):
    """Schema for device response."""

    id: str = Field(..., description="Device ID")
    scan_id: str = Field(..., description="Scan ID")
    is_up: bool = Field(default=True, description="Device status")
    last_seen: Optional[datetime] = Field(None, description="Last seen timestamp")
    open_ports: list[PortSchema] = Field(default_factory=list, description="Open ports")
    vulnerability_count: int = Field(default=0, description="Number of vulnerabilities")
    created_at: Optional[datetime] = Field(None, description="Created timestamp")
    updated_at: Optional[datetime] = Field(None, description="Updated timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "scan_id": "550e8400-e29b-41d4-a716-446655440001",
                "ip": "192.168.1.1",
                "mac": "00:1A:2B:3C:4D:5E",
                "hostname": "router.local",
                "vendor": "Linksys",
                "device_type": "router",
                "os": "Linux",
                "os_accuracy": 95,
                "is_up": True,
                "last_seen": "2024-12-08T12:00:00Z",
                "open_ports": [
                    {"port": 80, "protocol": "tcp", "state": "open", "service": "http"}
                ],
                "vulnerability_count": 2,
                "created_at": "2024-12-08T12:00:00Z",
                "updated_at": "2024-12-08T12:00:00Z",
            }
        }


class DeviceListResponse(BaseModel):
    """Schema for paginated device list."""

    items: list[DeviceResponse] = Field(..., description="List of devices")
    total: int = Field(..., description="Total number of devices")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total pages")

"""
Pydantic schemas for API request/response validation.

This package contains all the Pydantic models used for:
- Request body validation
- Response serialization
- API documentation generation
"""

from app.schemas.network import (
    ScanRequest,
    ScanResponse,
    ScanStatusResponse,
    DeviceResponse,
    PortResponse,
    NetworkInterfaceResponse,
    NetworkValidationRequest,
    NetworkValidationResponse,
)

__all__ = [
    "ScanRequest",
    "ScanResponse",
    "ScanStatusResponse",
    "DeviceResponse",
    "PortResponse",
    "NetworkInterfaceResponse",
    "NetworkValidationRequest",
    "NetworkValidationResponse",
]

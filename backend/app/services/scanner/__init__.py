"""
Network scanning service module.

This module provides network scanning capabilities for discovering devices,
detecting open ports, and identifying potential vulnerabilities on local networks.

Key Components:
- NetworkValidator: Validates network ranges and ensures only private networks are scanned
- NmapScanner: Wrapper around nmap for port scanning and service detection
- DeviceFingerprinter: Identifies device types, OS, and manufacturers
- ScanOrchestrator: Coordinates scanning operations and manages scan lifecycle

Security Notes:
- Only private network ranges are allowed (10.x, 192.168.x, 172.16-31.x)
- All scans are audit logged
- User consent is required before scanning
"""

from app.services.scanner.network_validator import NetworkValidator, NetworkValidationError
from app.services.scanner.base import (
    BaseScannerInterface,
    ScanType,
    ScanStatus,
    ScanResult,
    DeviceInfo,
    PortInfo,
)
from app.services.scanner.nmap_scanner import NmapScanner
from app.services.scanner.device_fingerprint import DeviceFingerprinter, DeviceType
from app.services.scanner.orchestrator import ScanOrchestrator

__all__ = [
    # Validator
    "NetworkValidator",
    "NetworkValidationError",
    # Base types
    "BaseScannerInterface",
    "ScanType",
    "ScanStatus",
    "ScanResult",
    "DeviceInfo",
    "PortInfo",
    # Scanner implementations
    "NmapScanner",
    # Fingerprinting
    "DeviceFingerprinter",
    "DeviceType",
    # Orchestration
    "ScanOrchestrator",
]

"""
Pytest configuration and shared fixtures.

This module provides common fixtures used across all tests, including:
- Test client for API testing
- Database fixtures
- Mock objects for external services
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

# Set test configuration before importing app
import os
os.environ["DEBUG"] = "false"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["ENABLE_REAL_SCANNING"] = "false"

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.

    Yields:
        TestClient instance
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_nmap():
    """
    Create a mock nmap PortScanner.

    Returns:
        MagicMock configured to simulate nmap
    """
    mock = MagicMock()
    mock.nmap_version.return_value = ("7", "94")
    mock.all_hosts.return_value = ["192.168.1.1", "192.168.1.100"]

    # Mock scan results
    mock.__getitem__ = MagicMock(side_effect=lambda host: {
        "192.168.1.1": {
            "state": MagicMock(return_value="up"),
            "hostnames": MagicMock(return_value=[{"name": "router.local"}]),
            "addresses": {"mac": "00:1A:2B:3C:4D:5E"},
            "vendor": {"00:1A:2B:3C:4D:5E": "Linksys"},
            "tcp": {
                80: {"state": "open", "name": "http", "version": "", "product": ""},
                443: {"state": "open", "name": "https", "version": "", "product": ""},
            },
        },
        "192.168.1.100": {
            "state": MagicMock(return_value="up"),
            "hostnames": MagicMock(return_value=[{"name": "desktop.local"}]),
            "addresses": {},
            "tcp": {
                22: {"state": "open", "name": "ssh", "version": "OpenSSH 8.9", "product": "OpenSSH"},
            },
        },
    }.get(host, {}))

    return mock


@pytest.fixture
def sample_device_info():
    """
    Create sample DeviceInfo for testing.

    Returns:
        Dictionary with device info
    """
    from app.services.scanner.base import DeviceInfo, PortInfo

    return DeviceInfo(
        ip="192.168.1.1",
        mac="00:1A:2B:3C:4D:5E",
        hostname="router.local",
        vendor="Linksys",
        os="Linux",
        os_accuracy=90,
        device_type="router",
        open_ports=[
            PortInfo(port=80, service="http"),
            PortInfo(port=443, service="https"),
        ],
        is_up=True,
    )


@pytest.fixture
def sample_scan_result():
    """
    Create sample ScanResult for testing.

    Returns:
        ScanResult instance
    """
    from datetime import datetime
    from app.services.scanner.base import (
        ScanResult,
        ScanType,
        ScanStatus,
        DeviceInfo,
        PortInfo,
    )

    return ScanResult(
        scan_id="test-scan-123",
        target_range="192.168.1.0/24",
        scan_type=ScanType.QUICK,
        status=ScanStatus.COMPLETED,
        devices=[
            DeviceInfo(
                ip="192.168.1.1",
                mac="00:1A:2B:3C:4D:5E",
                hostname="router.local",
                device_type="router",
                open_ports=[
                    PortInfo(port=80, service="http"),
                    PortInfo(port=443, service="https"),
                ],
                is_up=True,
            ),
        ],
        started_at=datetime(2024, 12, 8, 12, 0, 0),
        completed_at=datetime(2024, 12, 8, 12, 2, 30),
        progress=100.0,
        scanned_hosts=254,
        total_hosts=254,
    )

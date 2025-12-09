"""
Tests for network scanning API routes.

These tests verify that:
- API endpoints return correct responses
- Input validation works properly
- Error handling is correct
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.scanner.base import ScanResult, ScanStatus, ScanType, DeviceInfo, PortInfo
from app.services.scanner.network_validator import NetworkValidationError


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_orchestrator():
    """Create mock orchestrator."""
    mock = MagicMock()
    mock.start_scan = AsyncMock()
    mock.get_scan_status = AsyncMock()
    mock.cancel_scan = AsyncMock()
    mock.get_scan_history = AsyncMock()
    mock.get_network_interfaces = MagicMock()
    mock.detect_local_network = MagicMock()
    mock.validate_target = MagicMock()
    return mock


class TestScanEndpoint:
    """Tests for POST /api/v1/network/scan endpoint."""

    def test_scan_requires_user_consent(self, client):
        """Test that scan requires user consent."""
        response = client.post(
            "/api/v1/network/scan",
            json={
                "target": "192.168.1.0/24",
                "scan_type": "quick",
                "user_consent": False,
            },
        )

        assert response.status_code == 403
        assert "consent" in response.json()["detail"].lower()

    def test_scan_rejects_public_network(self, client):
        """Test that public networks are rejected."""
        response = client.post(
            "/api/v1/network/scan",
            json={
                "target": "8.8.8.8",
                "scan_type": "quick",
                "user_consent": True,
            },
        )

        assert response.status_code == 400
        assert "private" in response.json()["detail"].lower()

    def test_scan_validates_target_format(self, client):
        """Test that invalid target format is rejected."""
        response = client.post(
            "/api/v1/network/scan",
            json={
                "target": "",
                "scan_type": "quick",
                "user_consent": True,
            },
        )

        assert response.status_code == 422  # Validation error

    def test_scan_validates_port_range(self, client):
        """Test that invalid port range is rejected."""
        response = client.post(
            "/api/v1/network/scan",
            json={
                "target": "192.168.1.0/24",
                "scan_type": "custom",
                "port_range": "invalid!@#",
                "user_consent": True,
            },
        )

        assert response.status_code == 422  # Validation error

    @patch("app.api.routes.network.get_scan_orchestrator")
    def test_scan_success(self, mock_get_orchestrator, client):
        """Test successful scan initiation."""
        mock_orch = MagicMock()
        mock_result = ScanResult(
            scan_id="test-123",
            target_range="192.168.1.0/24",
            scan_type=ScanType.QUICK,
            status=ScanStatus.RUNNING,
            progress=0.0,
        )
        mock_orch.start_scan = AsyncMock(return_value=mock_result)
        mock_get_orchestrator.return_value = mock_orch

        response = client.post(
            "/api/v1/network/scan",
            json={
                "target": "192.168.1.0/24",
                "scan_type": "quick",
                "user_consent": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["scan_id"] == "test-123"
        assert data["status"] == "running"


class TestGetScanEndpoint:
    """Tests for GET /api/v1/network/scan/{scan_id} endpoint."""

    @patch("app.api.routes.network.get_scan_orchestrator")
    def test_get_scan_found(self, mock_get_orchestrator, client):
        """Test getting existing scan."""
        mock_orch = MagicMock()
        mock_result = ScanResult(
            scan_id="test-123",
            target_range="192.168.1.0/24",
            scan_type=ScanType.QUICK,
            status=ScanStatus.COMPLETED,
            devices=[
                DeviceInfo(
                    ip="192.168.1.1",
                    hostname="router",
                    open_ports=[PortInfo(port=80, service="http")],
                )
            ],
            progress=100.0,
        )
        mock_orch.get_scan_status = AsyncMock(return_value=mock_result)
        mock_get_orchestrator.return_value = mock_orch

        response = client.get("/api/v1/network/scan/test-123")

        assert response.status_code == 200
        data = response.json()
        assert data["scan_id"] == "test-123"
        assert data["status"] == "completed"
        assert len(data["devices"]) == 1

    @patch("app.api.routes.network.get_scan_orchestrator")
    def test_get_scan_not_found(self, mock_get_orchestrator, client):
        """Test getting non-existent scan."""
        mock_orch = MagicMock()
        mock_orch.get_scan_status = AsyncMock(return_value=None)
        mock_get_orchestrator.return_value = mock_orch

        response = client.get("/api/v1/network/scan/nonexistent")

        assert response.status_code == 404


class TestScanStatusEndpoint:
    """Tests for GET /api/v1/network/scan/{scan_id}/status endpoint."""

    @patch("app.api.routes.network.get_scan_orchestrator")
    def test_get_status(self, mock_get_orchestrator, client):
        """Test getting scan status."""
        mock_orch = MagicMock()
        mock_result = ScanResult(
            scan_id="test-123",
            status=ScanStatus.RUNNING,
            progress=50.0,
        )
        mock_orch.get_scan_status = AsyncMock(return_value=mock_result)
        mock_get_orchestrator.return_value = mock_orch

        response = client.get("/api/v1/network/scan/test-123/status")

        assert response.status_code == 200
        data = response.json()
        assert data["scan_id"] == "test-123"
        assert data["status"] == "running"
        assert data["progress"] == 50.0


class TestCancelScanEndpoint:
    """Tests for POST /api/v1/network/scan/{scan_id}/cancel endpoint."""

    @patch("app.api.routes.network.get_scan_orchestrator")
    def test_cancel_scan_success(self, mock_get_orchestrator, client):
        """Test cancelling a scan."""
        mock_orch = MagicMock()
        mock_orch.cancel_scan = AsyncMock(return_value=True)
        mock_get_orchestrator.return_value = mock_orch

        response = client.post("/api/v1/network/scan/test-123/cancel")

        assert response.status_code == 200
        assert "cancelled" in response.json()["message"].lower()

    @patch("app.api.routes.network.get_scan_orchestrator")
    def test_cancel_scan_not_found(self, mock_get_orchestrator, client):
        """Test cancelling non-existent scan."""
        mock_orch = MagicMock()
        mock_orch.cancel_scan = AsyncMock(return_value=False)
        mock_get_orchestrator.return_value = mock_orch

        response = client.post("/api/v1/network/scan/nonexistent/cancel")

        assert response.status_code == 404


class TestListScansEndpoint:
    """Tests for GET /api/v1/network/scans endpoint."""

    @patch("app.api.routes.network.get_scan_orchestrator")
    def test_list_scans(self, mock_get_orchestrator, client):
        """Test listing scans."""
        mock_orch = MagicMock()
        mock_orch.get_scan_history = AsyncMock(return_value=[
            ScanResult(scan_id="scan-1", status=ScanStatus.COMPLETED),
            ScanResult(scan_id="scan-2", status=ScanStatus.COMPLETED),
        ])
        mock_get_orchestrator.return_value = mock_orch

        response = client.get("/api/v1/network/scans")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @patch("app.api.routes.network.get_scan_orchestrator")
    def test_list_scans_pagination(self, mock_get_orchestrator, client):
        """Test scan listing with pagination."""
        mock_orch = MagicMock()
        mock_orch.get_scan_history = AsyncMock(return_value=[])
        mock_get_orchestrator.return_value = mock_orch

        response = client.get("/api/v1/network/scans?limit=5&offset=10")

        assert response.status_code == 200
        mock_orch.get_scan_history.assert_called_with(limit=5, offset=10)


class TestInterfacesEndpoint:
    """Tests for GET /api/v1/network/interfaces endpoint."""

    @patch("app.api.routes.network.get_scan_orchestrator")
    def test_list_interfaces(self, mock_get_orchestrator, client):
        """Test listing network interfaces."""
        mock_orch = MagicMock()
        mock_orch.get_network_interfaces = MagicMock(return_value=[
            {
                "name": "eth0",
                "ip": "192.168.1.100",
                "netmask": "255.255.255.0",
                "network": "192.168.1.0/24",
                "is_private": True,
            }
        ])
        mock_get_orchestrator.return_value = mock_orch

        response = client.get("/api/v1/network/interfaces")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "eth0"


class TestDetectEndpoint:
    """Tests for GET /api/v1/network/detect endpoint."""

    @patch("app.api.routes.network.get_scan_orchestrator")
    def test_detect_network_found(self, mock_get_orchestrator, client):
        """Test network detection when found."""
        mock_orch = MagicMock()
        mock_orch.detect_local_network = MagicMock(return_value="192.168.1.0/24")
        mock_get_orchestrator.return_value = mock_orch

        response = client.get("/api/v1/network/detect")

        assert response.status_code == 200
        data = response.json()
        assert data["detected"] is True
        assert data["network"] == "192.168.1.0/24"

    @patch("app.api.routes.network.get_scan_orchestrator")
    def test_detect_network_not_found(self, mock_get_orchestrator, client):
        """Test network detection when not found."""
        mock_orch = MagicMock()
        mock_orch.detect_local_network = MagicMock(return_value=None)
        mock_get_orchestrator.return_value = mock_orch

        response = client.get("/api/v1/network/detect")

        assert response.status_code == 200
        data = response.json()
        assert data["detected"] is False


class TestValidateEndpoint:
    """Tests for POST /api/v1/network/validate endpoint."""

    @patch("app.api.routes.network.get_scan_orchestrator")
    def test_validate_valid_target(self, mock_get_orchestrator, client):
        """Test validating valid target."""
        mock_orch = MagicMock()
        mock_orch.validate_target = MagicMock(return_value={
            "is_private": True,
            "num_hosts": 254,
            "type": "network",
        })
        mock_get_orchestrator.return_value = mock_orch

        response = client.post(
            "/api/v1/network/validate",
            json={"target": "192.168.1.0/24"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["is_private"] is True

    @patch("app.api.routes.network.get_scan_orchestrator")
    def test_validate_invalid_target(self, mock_get_orchestrator, client):
        """Test validating invalid target."""
        mock_orch = MagicMock()
        mock_orch.validate_target = MagicMock(
            side_effect=NetworkValidationError("Not private")
        )
        mock_get_orchestrator.return_value = mock_orch

        response = client.post(
            "/api/v1/network/validate",
            json={"target": "8.8.8.8"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["error"] is not None

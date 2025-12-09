"""
Tests for device API routes.

These tests verify device CRUD operations work correctly.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.device import Device


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return MagicMock()


@pytest.fixture
def sample_device():
    """Create sample device model."""
    device = MagicMock(spec=Device)
    device.id = "device-123"
    device.scan_id = "scan-456"
    device.ip = "192.168.1.1"
    device.mac = "00:1A:2B:3C:4D:5E"
    device.hostname = "router.local"
    device.vendor = "Linksys"
    device.device_type = "router"
    device.os = "Linux"
    device.os_accuracy = 95
    device.is_up = True
    device.last_seen = datetime(2024, 12, 8, 12, 0, 0)
    device.open_ports_json = json.dumps([
        {"port": 80, "protocol": "tcp", "state": "open", "service": "http"},
        {"port": 443, "protocol": "tcp", "state": "open", "service": "https"},
    ])
    device.vulnerabilities = []
    device.created_at = datetime(2024, 12, 8, 12, 0, 0)
    device.updated_at = datetime(2024, 12, 8, 12, 0, 0)
    return device


class TestListDevices:
    """Tests for GET /api/v1/devices endpoint."""

    @patch("app.api.routes.devices.get_db")
    def test_list_devices_empty(self, mock_get_db, client):
        """Test listing devices when none exist."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        mock_get_db.return_value = mock_db

        response = client.get("/api/v1/devices")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    @patch("app.api.routes.devices.get_db")
    def test_list_devices_with_results(self, mock_get_db, client, sample_device):
        """Test listing devices with results."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.count.return_value = 1
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_device]
        mock_db.query.return_value = mock_query
        mock_get_db.return_value = mock_db

        response = client.get("/api/v1/devices")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["ip"] == "192.168.1.1"

    @patch("app.api.routes.devices.get_db")
    def test_list_devices_filter_by_scan(self, mock_get_db, client, sample_device):
        """Test filtering devices by scan ID."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.count.return_value = 1
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_device]
        mock_db.query.return_value = mock_query
        mock_get_db.return_value = mock_db

        response = client.get("/api/v1/devices?scan_id=scan-456")

        assert response.status_code == 200
        # Verify filter was called
        mock_query.filter.assert_called()

    @patch("app.api.routes.devices.get_db")
    def test_list_devices_pagination(self, mock_get_db, client):
        """Test device pagination."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.count.return_value = 100
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        mock_get_db.return_value = mock_db

        response = client.get("/api/v1/devices?page=2&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10
        assert data["pages"] == 10  # 100 / 10


class TestGetDevice:
    """Tests for GET /api/v1/devices/{device_id} endpoint."""

    @patch("app.api.routes.devices.get_db")
    def test_get_device_found(self, mock_get_db, client, sample_device):
        """Test getting existing device."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = sample_device
        mock_get_db.return_value = mock_db

        response = client.get("/api/v1/devices/device-123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "device-123"
        assert data["ip"] == "192.168.1.1"

    @patch("app.api.routes.devices.get_db")
    def test_get_device_not_found(self, mock_get_db, client):
        """Test getting non-existent device."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        response = client.get("/api/v1/devices/nonexistent")

        assert response.status_code == 404


class TestUpdateDevice:
    """Tests for PUT /api/v1/devices/{device_id} endpoint."""

    @patch("app.api.routes.devices.get_db")
    def test_update_device(self, mock_get_db, client, sample_device):
        """Test updating device."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = sample_device
        mock_get_db.return_value = mock_db

        response = client.put(
            "/api/v1/devices/device-123",
            json={"hostname": "new-router.local"},
        )

        assert response.status_code == 200
        mock_db.commit.assert_called_once()

    @patch("app.api.routes.devices.get_db")
    def test_update_device_not_found(self, mock_get_db, client):
        """Test updating non-existent device."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        response = client.put(
            "/api/v1/devices/nonexistent",
            json={"hostname": "new-name"},
        )

        assert response.status_code == 404


class TestDeleteDevice:
    """Tests for DELETE /api/v1/devices/{device_id} endpoint."""

    @patch("app.api.routes.devices.get_db")
    def test_delete_device(self, mock_get_db, client, sample_device):
        """Test deleting device."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = sample_device
        mock_get_db.return_value = mock_db

        response = client.delete("/api/v1/devices/device-123")

        assert response.status_code == 200
        mock_db.delete.assert_called_once_with(sample_device)
        mock_db.commit.assert_called_once()

    @patch("app.api.routes.devices.get_db")
    def test_delete_device_not_found(self, mock_get_db, client):
        """Test deleting non-existent device."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        response = client.delete("/api/v1/devices/nonexistent")

        assert response.status_code == 404


class TestGetDeviceVulnerabilities:
    """Tests for GET /api/v1/devices/{device_id}/vulnerabilities endpoint."""

    @patch("app.api.routes.devices.get_db")
    def test_get_device_vulnerabilities(self, mock_get_db, client, sample_device):
        """Test getting device vulnerabilities."""
        mock_vuln = MagicMock()
        mock_vuln.to_dict.return_value = {
            "id": "vuln-1",
            "vuln_type": "default_credentials",
            "severity": "high",
        }
        sample_device.vulnerabilities = [mock_vuln]

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = sample_device
        mock_get_db.return_value = mock_db

        response = client.get("/api/v1/devices/device-123/vulnerabilities")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["vuln_type"] == "default_credentials"

    @patch("app.api.routes.devices.get_db")
    def test_get_device_vulnerabilities_not_found(self, mock_get_db, client):
        """Test getting vulnerabilities for non-existent device."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        response = client.get("/api/v1/devices/nonexistent/vulnerabilities")

        assert response.status_code == 404

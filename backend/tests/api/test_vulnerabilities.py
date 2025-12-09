"""
Tests for vulnerability API routes.

These tests verify vulnerability CRUD operations and statistics work correctly.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.vulnerability import Vulnerability


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_vulnerability():
    """Create sample vulnerability model."""
    vuln = MagicMock(spec=Vulnerability)
    vuln.id = "vuln-123"
    vuln.device_id = "device-456"
    vuln.vuln_type = "default_credentials"
    vuln.severity = "high"
    vuln.title = "Default Credentials Detected"
    vuln.description = "The device is using default login credentials."
    vuln.cve_id = None
    vuln.affected_service = "http"
    vuln.affected_port = "80"
    vuln.remediation = "Change the default username and password."
    vuln.is_fixed = False
    vuln.verified_fixed = False
    vuln.discovered_at = datetime(2024, 12, 8, 12, 0, 0)
    vuln.fixed_at = None
    vuln.created_at = datetime(2024, 12, 8, 12, 0, 0)
    vuln.updated_at = datetime(2024, 12, 8, 12, 0, 0)
    return vuln


class TestListVulnerabilities:
    """Tests for GET /api/v1/vulnerabilities endpoint."""

    @patch("app.api.routes.vulnerabilities.get_db")
    def test_list_vulnerabilities_empty(self, mock_get_db, client):
        """Test listing vulnerabilities when none exist."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        mock_get_db.return_value = mock_db

        response = client.get("/api/v1/vulnerabilities")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    @patch("app.api.routes.vulnerabilities.get_db")
    def test_list_vulnerabilities_with_results(self, mock_get_db, client, sample_vulnerability):
        """Test listing vulnerabilities with results."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.count.return_value = 1
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_vulnerability]
        mock_db.query.return_value = mock_query
        mock_get_db.return_value = mock_db

        response = client.get("/api/v1/vulnerabilities")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["vuln_type"] == "default_credentials"

    @patch("app.api.routes.vulnerabilities.get_db")
    def test_list_vulnerabilities_filter_by_severity(self, mock_get_db, client, sample_vulnerability):
        """Test filtering vulnerabilities by severity."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.count.return_value = 1
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_vulnerability]
        mock_db.query.return_value = mock_query
        mock_get_db.return_value = mock_db

        response = client.get("/api/v1/vulnerabilities?severity=high")

        assert response.status_code == 200
        mock_query.filter.assert_called()

    @patch("app.api.routes.vulnerabilities.get_db")
    def test_list_vulnerabilities_filter_by_fixed(self, mock_get_db, client, sample_vulnerability):
        """Test filtering vulnerabilities by fix status."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.count.return_value = 1
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_vulnerability]
        mock_db.query.return_value = mock_query
        mock_get_db.return_value = mock_db

        response = client.get("/api/v1/vulnerabilities?is_fixed=false")

        assert response.status_code == 200
        mock_query.filter.assert_called()


class TestGetVulnerabilitySummary:
    """Tests for GET /api/v1/vulnerabilities/summary endpoint."""

    @patch("app.api.routes.vulnerabilities.get_db")
    def test_get_summary(self, mock_get_db, client):
        """Test getting vulnerability summary."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.count.return_value = 10
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_db.query.return_value = mock_query
        mock_get_db.return_value = mock_db

        response = client.get("/api/v1/vulnerabilities/summary")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "critical" in data
        assert "high" in data
        assert "medium" in data
        assert "low" in data
        assert "fixed" in data
        assert "unfixed" in data


class TestGetVulnerability:
    """Tests for GET /api/v1/vulnerabilities/{vulnerability_id} endpoint."""

    @patch("app.api.routes.vulnerabilities.get_db")
    def test_get_vulnerability_found(self, mock_get_db, client, sample_vulnerability):
        """Test getting existing vulnerability."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = sample_vulnerability
        mock_get_db.return_value = mock_db

        response = client.get("/api/v1/vulnerabilities/vuln-123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "vuln-123"
        assert data["vuln_type"] == "default_credentials"

    @patch("app.api.routes.vulnerabilities.get_db")
    def test_get_vulnerability_not_found(self, mock_get_db, client):
        """Test getting non-existent vulnerability."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        response = client.get("/api/v1/vulnerabilities/nonexistent")

        assert response.status_code == 404


class TestUpdateVulnerability:
    """Tests for PUT /api/v1/vulnerabilities/{vulnerability_id} endpoint."""

    @patch("app.api.routes.vulnerabilities.get_db")
    def test_update_vulnerability(self, mock_get_db, client, sample_vulnerability):
        """Test updating vulnerability."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = sample_vulnerability
        mock_get_db.return_value = mock_db

        response = client.put(
            "/api/v1/vulnerabilities/vuln-123",
            json={"title": "Updated Title"},
        )

        assert response.status_code == 200
        mock_db.commit.assert_called_once()

    @patch("app.api.routes.vulnerabilities.get_db")
    def test_update_vulnerability_not_found(self, mock_get_db, client):
        """Test updating non-existent vulnerability."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        response = client.put(
            "/api/v1/vulnerabilities/nonexistent",
            json={"title": "New Title"},
        )

        assert response.status_code == 404

    @patch("app.api.routes.vulnerabilities.get_db")
    def test_update_vulnerability_mark_fixed(self, mock_get_db, client, sample_vulnerability):
        """Test updating vulnerability to mark as fixed."""
        sample_vulnerability.is_fixed = False
        sample_vulnerability.fixed_at = None

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = sample_vulnerability
        mock_get_db.return_value = mock_db

        response = client.put(
            "/api/v1/vulnerabilities/vuln-123",
            json={"is_fixed": True},
        )

        assert response.status_code == 200
        # Verify fixed_at was set
        assert sample_vulnerability.fixed_at is not None


class TestMarkVulnerabilityFixed:
    """Tests for POST /api/v1/vulnerabilities/{vulnerability_id}/mark-fixed endpoint."""

    @patch("app.api.routes.vulnerabilities.get_db")
    def test_mark_fixed(self, mock_get_db, client, sample_vulnerability):
        """Test marking vulnerability as fixed."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = sample_vulnerability
        mock_get_db.return_value = mock_db

        response = client.post(
            "/api/v1/vulnerabilities/vuln-123/mark-fixed",
            json={"is_fixed": True, "verified": False},
        )

        assert response.status_code == 200
        assert sample_vulnerability.is_fixed is True

    @patch("app.api.routes.vulnerabilities.get_db")
    def test_mark_fixed_verified(self, mock_get_db, client, sample_vulnerability):
        """Test marking vulnerability as fixed with verification."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = sample_vulnerability
        mock_get_db.return_value = mock_db

        response = client.post(
            "/api/v1/vulnerabilities/vuln-123/mark-fixed",
            json={"is_fixed": True, "verified": True},
        )

        assert response.status_code == 200
        assert sample_vulnerability.is_fixed is True
        assert sample_vulnerability.verified_fixed is True

    @patch("app.api.routes.vulnerabilities.get_db")
    def test_mark_unfixed(self, mock_get_db, client, sample_vulnerability):
        """Test marking vulnerability as unfixed."""
        sample_vulnerability.is_fixed = True
        sample_vulnerability.fixed_at = datetime.utcnow()
        sample_vulnerability.verified_fixed = True

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = sample_vulnerability
        mock_get_db.return_value = mock_db

        response = client.post(
            "/api/v1/vulnerabilities/vuln-123/mark-fixed",
            json={"is_fixed": False, "verified": False},
        )

        assert response.status_code == 200
        assert sample_vulnerability.is_fixed is False
        assert sample_vulnerability.fixed_at is None
        assert sample_vulnerability.verified_fixed is False

    @patch("app.api.routes.vulnerabilities.get_db")
    def test_mark_fixed_not_found(self, mock_get_db, client):
        """Test marking non-existent vulnerability."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        response = client.post(
            "/api/v1/vulnerabilities/nonexistent/mark-fixed",
            json={"is_fixed": True, "verified": False},
        )

        assert response.status_code == 404


class TestListVulnerabilityTypes:
    """Tests for GET /api/v1/vulnerabilities/types/list endpoint."""

    @patch("app.api.routes.vulnerabilities.get_db")
    def test_list_types(self, mock_get_db, client):
        """Test listing vulnerability types."""
        mock_db = MagicMock()
        mock_db.query.return_value.group_by.return_value.all.return_value = [
            ("default_credentials", 5),
            ("open_telnet", 3),
            ("open_ftp", 2),
        ]
        mock_get_db.return_value = mock_db

        response = client.get("/api/v1/vulnerabilities/types/list")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["vuln_type"] == "default_credentials"
        assert data[0]["count"] == 5

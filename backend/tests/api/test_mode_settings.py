"""Unit tests for mode settings API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.datastore.local import LocalDataStore


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def datastore(tmp_path):
    """Create a test datastore with temporary database."""
    db_path = tmp_path / "test.db"
    datastore = LocalDataStore(str(db_path))
    datastore.initialize()
    yield datastore


class TestGetModeSettings:
    """Tests for GET /api/v1/settings/mode endpoint."""

    def test_get_default_mode_settings(self, client):
        """Test getting mode settings returns training mode by default."""
        # First, reset to default by posting training mode
        client.post(
            "/api/v1/settings/mode",
            json={"mode": "training", "require_confirmation_for_live": True}
        )

        response = client.get("/api/v1/settings/mode")

        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "training"
        assert data["require_confirmation_for_live"] is True

    def test_mode_settings_included_in_all_settings(self, client):
        """Test mode settings are included in the all settings response."""
        # First, reset to default by posting training mode
        client.post(
            "/api/v1/settings/mode",
            json={"mode": "training", "require_confirmation_for_live": True}
        )

        response = client.get("/api/v1/settings")

        assert response.status_code == 200
        data = response.json()
        assert "mode" in data
        assert data["mode"]["mode"] == "training"


class TestUpdateModeSettings:
    """Tests for POST /api/v1/settings/mode endpoint."""

    def test_update_to_live_mode(self, client):
        """Test updating mode settings to live mode."""
        response = client.post(
            "/api/v1/settings/mode",
            json={"mode": "live", "require_confirmation_for_live": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "live"
        assert data["require_confirmation_for_live"] is True

    def test_update_to_training_mode(self, client):
        """Test updating mode settings to training mode."""
        # First set to live
        client.post(
            "/api/v1/settings/mode",
            json={"mode": "live", "require_confirmation_for_live": True}
        )

        # Then back to training
        response = client.post(
            "/api/v1/settings/mode",
            json={"mode": "training", "require_confirmation_for_live": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "training"
        assert data["require_confirmation_for_live"] is False

    def test_invalid_mode_rejected(self, client):
        """Test that invalid mode values are rejected."""
        response = client.post(
            "/api/v1/settings/mode",
            json={"mode": "invalid", "require_confirmation_for_live": True}
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_mode_persists_across_requests(self, client):
        """Test that mode settings persist across requests."""
        # Set to live mode
        client.post(
            "/api/v1/settings/mode",
            json={"mode": "live", "require_confirmation_for_live": True}
        )

        # Get mode settings
        response = client.get("/api/v1/settings/mode")

        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "live"

    def test_mode_change_defaults(self, client):
        """Test changing only the mode keeps other defaults."""
        response = client.post(
            "/api/v1/settings/mode",
            json={"mode": "live"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "live"
        # Should keep default for require_confirmation_for_live
        assert "require_confirmation_for_live" in data


class TestModeValidation:
    """Tests for mode settings validation."""

    def test_only_training_and_live_modes_allowed(self, client):
        """Test that only 'training' and 'live' are valid modes."""
        invalid_modes = ["test", "development", "production", "demo", ""]

        for invalid_mode in invalid_modes:
            response = client.post(
                "/api/v1/settings/mode",
                json={"mode": invalid_mode, "require_confirmation_for_live": True}
            )
            # Should fail Pydantic validation
            assert response.status_code in [400, 422], f"Mode '{invalid_mode}' should be rejected"

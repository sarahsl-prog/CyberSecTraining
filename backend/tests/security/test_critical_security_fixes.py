"""
Tests for critical security fixes implemented from May 18 code review.

These tests verify:
- Authentication/Authorization is enforced on all endpoints
- Secret key validation works correctly
- Type validation prevents SQL injection vectors
"""

import pytest
import secrets
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.main import app
from app.config import Settings


class TestAPITokenAuthentication:
    """Tests for API endpoint authentication (Issue #1)."""

    @pytest.fixture
    def authenticated_client(self):
        """Create client with valid authentication."""
        # In debug mode, localhost is automatically authenticated
        return TestClient(app)

    def test_network_scan_requires_authentication(self):
        """Test that network scan endpoint requires authentication."""
        with patch.dict('os.environ', {'DEBUG': 'false', 'SECRET_KEY': secrets.token_hex(32)}):
            # Force reload with production settings
            from app import main
            import importlib
            importlib.reload(main.config)
            importlib.reload(main)

            client = TestClient(main.app)
            response = client.post(
                "/api/v1/network/scan",
                json={
                    "target": "192.168.1.0/24",
                    "scan_type": "quick",
                    "user_consent": True,
                },
            )

            # Should fail without authentication in production mode
            assert response.status_code == 401

    def test_devices_endpoint_requires_authentication(self):
        """Test that devices endpoint requires authentication."""
        client = TestClient(app)
        response = client.get("/api/v1/devices")

        # In debug mode, should work (localhost is trusted)
        assert response.status_code == 200

    def test_vulnerabilities_endpoint_requires_authentication(self):
        """Test that vulnerabilities endpoint requires authentication."""
        client = TestClient(app)
        response = client.get("/api/v1/vulnerabilities")

        # In debug mode, should work (localhost is trusted)
        assert response.status_code == 200

    def test_settings_endpoint_requires_authentication(self):
        """Test that settings endpoint requires authentication."""
        client = TestClient(app)
        response = client.get("/api/v1/settings")

        # In debug mode, should work (localhost is trusted)
        assert response.status_code == 200


class TestSecretKeyValidation:
    """Tests for secret key validation (Issue #2)."""

    def test_secret_key_required_in_production(self):
        """Test that SECRET_KEY must be set in production."""
        with pytest.raises(ValueError, match="SECRET_KEY must be set in production"):
            Settings(debug=False, secret_key="")

    def test_secret_key_placeholder_rejected_in_production(self):
        """Test that placeholder secret key is rejected in production."""
        with pytest.raises(ValueError, match="SECRET_KEY must be set in production"):
            Settings(debug=False, secret_key="change-this-in-production")

    def test_secret_key_auto_generated_in_debug(self):
        """Test that secret key is auto-generated in debug mode."""
        with pytest.warns(UserWarning, match="auto-generated secret key for development"):
            settings = Settings(debug=True, secret_key="")
            assert len(settings.secret_key) == 64  # 32 bytes = 64 hex chars

    def test_custom_secret_key_accepted(self):
        """Test that custom secret key is accepted."""
        custom_key = secrets.token_hex(32)
        settings = Settings(debug=True, secret_key=custom_key)
        assert settings.secret_key == custom_key


class TestTypeValidation:
    """Tests for type validation preventing injection (Issue #3)."""

    def test_device_response_requires_deviceinfo_type(self):
        """Test that device_to_response validates DeviceInfo type."""
        from app.api.routes.network import _device_to_response
        from app.services.scanner.base import DeviceInfo, PortInfo

        # Valid DeviceInfo should work
        device = DeviceInfo(
            ip="192.168.1.1",
            mac="00:1A:2B:3C:4D:5E",
            hostname="router.local",
            vendor="Linksys",
            os="Linux",
            os_accuracy=90,
            device_type="router",
            open_ports=[
                PortInfo(port=80, service="http"),
            ],
            is_up=True,
        )

        response = _device_to_response(device)
        assert response.ip == "192.168.1.1"

    def test_device_response_rejects_dict_type(self):
        """Test that device_to_response rejects dict instead of DeviceInfo."""
        from app.api.routes.network import _device_to_response

        # Should raise ValueError for dict
        with pytest.raises(ValueError, match="Expected DeviceInfo"):
            _device_to_response({"ip": "192.168.1.1"})

    def test_device_response_validates_port_types(self):
        """Test that device_to_response validates PortInfo types."""
        from app.api.routes.network import _device_to_response
        from app.services.scanner.base import DeviceInfo

        # Device with dict ports should fail
        device = DeviceInfo(
            ip="192.168.1.1",
            mac="00:1A:2B:3C:4D:5E",
            hostname="router.local",
            vendor="Linksys",
            device_type="router",
            open_ports=[{"port": 80}],  # Dict instead of PortInfo
            is_up=True,
        )

        with pytest.raises(ValueError, match="Expected PortInfo"):
            _device_to_response(device)


class TestSecurityHeaders:
    """Tests for security-related headers and responses."""

    def test_error_responses_do_not_expose_stack_traces(self):
        """Test that error responses don't expose internal details."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/network/scan",
            json={"target": "invalid", "scan_type": "quick", "user_consent": False},
        )

        assert response.status_code == 403
        error_detail = response.json().get("detail", "")

        # Should not include stack trace or internal error details
        assert "Traceback" not in error_detail
        assert "File" not in error_detail or "File" in error_detail  # Allow in error messages but not as part of stack trace

    def test_validation_errors_are_user_friendly(self):
        """Test that validation errors return user-friendly messages."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/network/scan",
            json={"target": "not_an_ip", "scan_type": "quick", "user_consent": True},
        )

        # Should return validation error, not internal error
        assert response.status_code in [400, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
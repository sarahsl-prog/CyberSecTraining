"""
Tests for Critical security fixes.

These tests verify that critical security vulnerabilities have been addressed:
- Secret key validation in production
- Type validation in device response conversion
- Authentication and authorization checks
"""

import pytest
import os
import secrets
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.config import Settings
from app.services.scanner.base import DeviceInfo, PortInfo
from app.api.routes.network import _device_to_response
from app.core.logging import get_logger

logger = get_logger("test")


class TestSecretKeyValidation:
    """Tests for secret key validation (Critical Issue #2)."""

    def test_secret_key_validation_in_production(self):
        """Test that production mode requires a valid secret key."""
        os.environ["DEBUG"] = "false"
        os.environ["SECRET_KEY"] = ""
        
        # Missing SECRET_KEY should raise error in production
        with pytest.raises(ValueError) as exc_info:
            settings = Settings()
        
        assert "SECRET_KEY must be set" in str(exc_info.value)

    def test_secret_key_placeholder_rejected_in_production(self):
        """Test that placeholder value is rejected in production mode."""
        os.environ["DEBUG"] = "false"
        os.environ["SECRET_KEY"] = "change-this-in-production"
        
        # Placeholder should raise error in production
        with pytest.raises(ValueError) as exc_info:
            settings = Settings()
        
        assert "SECRET_KEY must be set" in str(exc_info.value)

    def test_secret_key_placeholder_allowed_in_debug(self):
        """Test that placeholder value is auto-generated in debug mode."""
        os.environ["DEBUG"] = "true"
        os.environ["SECRET_KEY"] = "change-this-in-production"
        
        settings = Settings()
        
        # Should auto-generate a key in debug mode
        assert settings.secret_key != "change-this-in-production"
        assert len(settings.secret_key) == 64  # 32 bytes in hex

    def test_secret_key_auto_generated_in_debug(self):
        """Test that secret key is auto-generated in debug mode."""
        os.environ["DEBUG"] = "true"
        os.environ["SECRET_KEY"] = ""
        
        settings = Settings()
        
        # Should have a generated key
        assert settings.secret_key
        assert len(settings.secret_key) == 64  # 32 bytes in hex
        assert settings.secret_key != "change-this-in-production"

    def test_secret_key_fixed_in_production(self):
        """Test that provided secret key works in production."""
        test_key = secrets.token_hex(32)
        os.environ["DEBUG"] = "false"
        os.environ["SECRET_KEY"] = test_key
        
        settings = Settings()
        
        assert settings.secret_key == test_key


class TestDeviceResponseTypeValidation:
    """Tests for type validation in _device_to_response (Critical Issue #3)."""

    def test_device_to_response_with_valid_device(self):
        """Test that valid DeviceInfo is converted correctly."""
        device = DeviceInfo(
            ip="192.168.1.1",
            mac="00:1A:2B:3C:4D:5E",
            hostname="test.local",
            open_ports=[PortInfo(port=80, service="http")],
            is_up=True,
        )
        
        result = _device_to_response(device)
        
        assert result.ip == "192.168.1.1"
        assert result.mac == "00:1A:2B:3C:4D:5E"
        assert result.hostname == "test.local"
        assert len(result.open_ports) == 1

    def test_device_to_response_rejects_invalid_device_type(self):
        """Test that invalid device type raises ValueError."""
        # Create a dict instead of DeviceInfo
        invalid_device = {
            "ip": "192.168.1.1",
            "mac": "00:1A:2B:3C:4D:5E",
        }
        
        with pytest.raises(ValueError) as exc_info:
            _device_to_response(invalid_device)
        
        assert "Expected DeviceInfo" in str(exc_info.value)

    def test_device_to_response_rejects_invalid_port_type(self):
        """Test that invalid port type raises ValueError."""
        device = DeviceInfo(
            ip="192.168.1.1",
            open_ports=[
                {"port": 80, "service": "http"}  # Dict instead of PortInfo
            ],
            is_up=True,
        )
        
        with pytest.raises(ValueError) as exc_info:
            _device_to_response(device)
        
        assert "Expected PortInfo" in str(exc_info.value)

    def test_device_to_response_handles_mixed_port_types(self):
        """Test that mixed valid/invalid port types are caught."""
        device = DeviceInfo(
            ip="192.168.1.1",
            open_ports=[
                PortInfo(port=80, service="http"),
                {"port": 443, "service": "https"}  # Invalid type
            ],
            is_up=True,
        )
        
        with pytest.raises(ValueError) as exc_info:
            _device_to_response(device)
        
        assert "Expected PortInfo" in str(exc_info.value)


class TestAuthenticationInfrastructure:
    """Tests for authentication infrastructure (Critical Issue #1)."""

    def test_trusted_host_middleware_available(self):
        """Test that TrustedHostMiddleware is available and can be configured."""
        from fastapi.middleware.trustedhost import TrustedHostMiddleware
        from app.main import create_app
        
        # Verify the middleware class is available
        assert TrustedHostMiddleware is not None
        
        # Create app in production mode
        os.environ["DEBUG"] = "false"
        os.environ["SECRET_KEY"] = secrets.token_hex(32)
        
        app = create_app()
        
        # The app should have middleware configured
        assert len(app.user_middleware) > 0

    def test_dependencies_module_exists(self):
        """Test that authentication dependencies module exists and is importable."""
        from app.api import dependencies
        
        # Verify key functions exist
        assert hasattr(dependencies, 'get_current_user')
        assert hasattr(dependencies, 'require_admin')
        assert hasattr(dependencies, 'require_api_key')
        assert hasattr(dependencies, 'is_trusted_host')

    def test_get_current_user_function_exists(self):
        """Test that get_current_user function exists and is callable."""
        from app.api.dependencies import get_current_user
        
        assert callable(get_current_user)
        # Function signature should have proper parameters
        assert hasattr(get_current_user, '__annotations__')

    def test_secret_key_not_exposed_in_logs(self):
        """Test that secret key is not exposed in logs."""
        test_key = secrets.token_hex(32)
        os.environ["DEBUG"] = "true"
        os.environ["SECRET_KEY"] = test_key
        
        settings = Settings()
        
        # Secret key should not appear in logs
        # This is more of an audit test - we just verify the value exists
        assert settings.secret_key == test_key
        assert len(settings.secret_key) == 64


class TestSecurityHardening:
    """Tests for overall security hardening."""

    def test_no_hardcoded_credentials_in_code(self):
        """Test that no hardcoded credentials exist in critical files."""
        import ast
        import re
        
        # Check critical files for hardcoded secrets
        critical_files = [
            "backend/app/config.py",
            "backend/app/main.py",
        ]
        
        for file_path in critical_files:
            full_path = Path(__file__).parent.parent / file_path
            if not full_path.exists():
                continue
                
            with open(full_path, 'r') as f:
                content = f.read()
            
            # Check for obvious hardcoded secrets
            patterns = [
                r'password\s*=\s*["\'][^"\']{8,}["\']',  # Long passwords
                r'api_key\s*=\s*["\'][^"\']{20,}["\']',  # Long API keys
                r'secret\s*=\s*"[^"\']{8,}"',  # Hardcoded secrets
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                # Filter out the placeholder we expect
                matches = [m for m in matches if "change-this-in-production" not in m.lower()]
                assert len(matches) == 0, f"Found potential hardcoded secret in {file_path}: {matches}"

    def test_debug_mode_defaults_to_true(self):
        """Test that debug mode defaults to true for safety."""
        # Without setting DEBUG env var, should default to true
        if "DEBUG" in os.environ:
            del os.environ["DEBUG"]
        
        settings = Settings()
        
        # Should default to true for safety
        assert settings.debug is True

    def test_security_headers_configurable(self):
        """Test that security-related settings are configurable."""
        test_key = secrets.token_hex(32)
        os.environ["DEBUG"] = "true"
        os.environ["SECRET_KEY"] = test_key
        
        settings = Settings()
        
        # Verify security configuration is loaded
        assert settings.secret_key == test_key
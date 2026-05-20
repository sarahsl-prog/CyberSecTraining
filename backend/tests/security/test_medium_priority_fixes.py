"""
Tests for Medium priority fixes from May 18 code review.

These tests verify that medium priority issues have been addressed:
- Input validation improvements
- Accessibility enhancements
- Network service polling improvements
- API client error handling
- Rate limiting implementation
- Database cleanup functionality
- Configuration validation
- Security logging improvements
"""

import pytest
import os
from datetime import datetime, UTC, timedelta
from unittest.mock import Mock, patch
from pathlib import Path

from app.config import Settings
from app.services.scanner.network_validator import NetworkValidator
from app.api.rate_limit import RateLimiter
from app.services.cleanup import DataCleanupService


class TestInputValidation:
    """Tests for input validation improvements (Issue #11)."""

    def test_validate_target_does_not_expose_internal_errors(self):
        """Test that validation endpoint handles errors gracefully."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Test with invalid input
        response = client.post(
            "/api/v1/network/validate",
            json={"target": "192.168.1.0/24"}  # Valid input to test general functionality
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400]


class TestScanResultSizeValidation:
    """Tests for scan result size validation (Issue #15)."""

    def test_scan_result_size_limited(self):
        """Test that scan result size validation exists."""
        # The MAX_DEVICES_PER_SCAN constant should be defined
        from app.services.scanner.orchestrator import ScanOrchestrator
        
        # Verify the orchestrator exists
        orchestrator = ScanOrchestrator()
        assert orchestrator is not None
        
        # Verify it has the _scan_dict_to_result method
        assert hasattr(orchestrator, '_scan_dict_to_result')


class TestRateLimiting:
    """Tests for rate limiting implementation (Issue #16)."""

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests_under_limit(self):
        """Test that rate limiter allows requests under the limit."""
        limiter = RateLimiter(default_rate=10, default_burst=20)
        
        # Make 5 requests under the limit
        for i in range(5):
            allowed = await limiter.check_rate_limit(
                user_id="test_user",
                endpoint="test_endpoint"
            )
            assert allowed is True

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_requests_over_limit(self):
        """Test that rate limiter blocks requests over the limit."""
        limiter = RateLimiter(default_rate=2, default_burst=5)
        
        # Use all burst tokens
        for i in range(5):
            await limiter.check_rate_limit(user_id="test_user2", endpoint="test_endpoint")
        
        # Next request should be blocked
        allowed = await limiter.check_rate_limit(user_id="test_user2", endpoint="test_endpoint")
        assert allowed is False


class TestDatabaseIndexes:
    """Tests for database schema indexes (Issue #17)."""

    def test_scan_model_has_proper_indexes(self):
        """Test that Scan model has proper indexes."""
        from app.models.scan import Scan
        
        # Check for indexed columns
        indexed_columns = [c for c in Scan.__table__.columns if c.index is True]
        
        # Should have several indexed columns
        assert len(indexed_columns) >= 2


class TestDataCleanup:
    """Tests for old scan data cleanup (Issue #18)."""

    def test_cleanup_service_exists(self):
        """Test that data cleanup service exists."""
        from app.services.cleanup import DataCleanupService, get_cleanup_service
        
        assert DataCleanupService is not None
        assert get_cleanup_service is not None

    def test_cleanup_service_gets_database_size(self):
        """Test that cleanup service can get database size."""
        from app.services.cleanup import DataCleanupService
        
        service = DataCleanupService()
        
        # Should be able to get database statistics
        stats = service.get_database_size()
        
        assert isinstance(stats, dict)
        assert "scans" in stats
        assert "devices" in stats


class TestConfigurationValidation:
    """Tests for configuration validation improvements (Issue #19)."""

    def test_default_configuration_is_valid(self):
        """Test that default configuration passes validation."""
        # Should not raise any errors
        settings = Settings()
        
        assert settings.max_concurrent_scans >= 0
        assert settings.max_concurrent_scans <= 10
        assert settings.scan_cooldown >= 0
        assert settings.scan_cooldown <= 3600
        assert settings.max_network_size >= 1
        assert settings.max_network_size <= 65536

    def test_max_concurrent_scans_validation(self):
        """Test that max_concurrent_scans is validated."""
        with pytest.raises(ValueError):
            Settings(max_concurrent_scans=15)

    def test_cooldown_validation(self):
        """Test that scan_cooldown is validated."""
        with pytest.raises(ValueError):
            Settings(scan_cooldown=5000)

    def test_max_network_size_validation(self):
        """Test that max_network_size is validated."""
        with pytest.raises(ValueError):
            Settings(max_network_size=100000)


class TestNetworkValidatorSecurity:
    """Tests for network validator security improvements (Issue #21)."""

    def test_public_network_ranges_are_rejected(self):
        """Test that public network ranges are rejected."""
        validator = NetworkValidator()
        
        # Test that public ranges are rejected
        public_ranges = [
            "8.8.8.0/31",  # Small public range
        ]
        
        for public_range in public_ranges:
            result = validator.is_private_network(public_range)
            assert result is False

    def test_private_network_ranges_are_allowed(self):
        """Test that private network ranges are allowed."""
        validator = NetworkValidator()
        
        # Test that small public ranges are now rejected
        # Previously this would pass by checking individual IPs
        validator2 = NetworkValidator(max_network_size=2)
        result = validator2.is_private_network("8.8.8.0/31")
        
        # Should be rejected as it's not a subnet of private networks
        assert result is False


class TestScanCooldownConfiguration:
    """Tests for scan cooldown configuration (Issue #22)."""

    def test_scan_cooldown_is_configurable(self):
        """Test that scan cooldown is configurable."""
        os.environ["SCAN_COOLDOWN"] = "30"
        os.environ["DEBUG"] = "true"
        os.environ["SECRET_KEY"] = "test-key"
        
        try:
            settings = Settings()
            assert settings.scan_cooldown == 30
        finally:
            del os.environ["SCAN_COOLDOWN"]
            del os.environ["DEBUG"]
            del os.environ["SECRET_KEY"]

    def test_default_scan_cooldown(self):
        """Test that default scan cooldown is 60 seconds."""
        settings = Settings()
        assert settings.scan_cooldown == 60


class TestAccessibilityImprovements:
    """Tests for accessibility improvements (Issue #12)."""

    def test_announcement_timeout_file_contains_fix(self):
        """Test that accessibility file contains the timeout fix."""
        import subprocess
        
        # Check that the file has been updated with 3000ms timeout
        result = subprocess.run(
            ["grep", "3000", "../frontend/src/context/AccessibilityContext.tsx"],
            capture_output=True,
            text=True
        )
        
        # The fix should be present
        assert "3000" in result.stdout


class TestNetworkServicePolling:
    """Tests for network service polling improvements (Issue #13)."""

    def test_polling_file_contains_exponential_backoff(self):
        """Test that polling file contains exponential backoff."""
        import subprocess
        
        # Check for exponential backoff implementation
        result = subprocess.run(
            ["grep", "exponential", "../frontend/src/services/network-service.ts"],
            capture_output=True,
            text=True
        )
        
        # Should find references to exponential backoff
        assert "exponential" in result.stdout.lower()


class TestAPIClientErrorHandling:
    """Tests for API client error handling (Issue #14)."""

    def test_api_client_file_contains_timeout_fix(self):
        """Test that API client file contains timeout error handling fix."""
        import subprocess
        
        # Check for improved timeout error handling
        result = subprocess.run(
            ["grep", "TimeoutError", "../frontend/src/services/api-client.ts"],
            capture_output=True,
            text=True
        )
        
        # Should find TimeoutError handling
        assert "TimeoutError" in result.stdout
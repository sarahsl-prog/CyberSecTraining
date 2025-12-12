"""
Tests for the scan orchestrator module.

These tests verify that:
- Scans require user consent
- Rate limiting is enforced
- Scan history is maintained
- Network validation is performed
- Mode routing (training vs live) works correctly
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.services.scanner.orchestrator import ScanOrchestrator, get_scan_orchestrator
from app.services.scanner.base import ScanType, ScanStatus, ScanResult
from app.services.scanner.network_validator import NetworkValidationError
from app.services.scanner.fake_network_generator import FakeNetworkGenerator
from app.services.scanner.nmap_scanner import NmapScanner


class TestScanOrchestrator:
    """Tests for the ScanOrchestrator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = ScanOrchestrator()

    # =========================================================================
    # User Consent Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_scan_requires_user_consent(self):
        """Test that scans fail without user consent."""
        with pytest.raises(PermissionError) as exc_info:
            await self.orchestrator.start_scan(
                target="192.168.1.0/24",
                scan_type=ScanType.QUICK,
                user_consent=False,
            )

        assert "consent" in str(exc_info.value).lower()

    # =========================================================================
    # Network Validation Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_scan_validates_target(self):
        """Test that scan validates target network."""
        # Patch scanner to avoid actual scanning
        with patch.object(
            self.orchestrator, "_get_scanner"
        ) as mock_get_scanner:
            mock_scanner = MagicMock()
            mock_scanner.scan_network = AsyncMock(
                return_value=ScanResult(status=ScanStatus.COMPLETED)
            )
            mock_get_scanner.return_value = mock_scanner

            # Public IP should fail
            with pytest.raises(NetworkValidationError):
                await self.orchestrator.start_scan(
                    target="8.8.8.8",
                    user_consent=True,
                )

    # =========================================================================
    # Rate Limiting Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_rate_limiting_cooldown(self):
        """Test that scans respect cooldown period."""
        # Simulate a recent scan
        self.orchestrator._last_scan_time = datetime.utcnow()

        with pytest.raises(RuntimeError) as exc_info:
            await self.orchestrator.start_scan(
                target="192.168.1.0/24",
                user_consent=True,
            )

        assert "wait" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_rate_limiting_concurrent_scan(self):
        """Test that concurrent scans are blocked."""
        # Simulate an active scan
        self.orchestrator._current_scan = "existing-scan-123"
        self.orchestrator._scan_history["existing-scan-123"] = ScanResult(
            scan_id="existing-scan-123",
            status=ScanStatus.RUNNING,
        )
        # Set last scan time to past to avoid cooldown error
        self.orchestrator._last_scan_time = datetime.utcnow() - timedelta(hours=1)

        with pytest.raises(RuntimeError) as exc_info:
            await self.orchestrator.start_scan(
                target="192.168.1.0/24",
                user_consent=True,
            )

        assert "already in progress" in str(exc_info.value).lower()

    # =========================================================================
    # Scan History Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_scan_history(self):
        """Test that completed scans are stored in history."""
        # Patch scanner and settings
        with patch.object(
            self.orchestrator, "_get_scanner"
        ) as mock_get_scanner, patch("app.services.scanner.orchestrator.settings") as mock_settings:
            mock_settings.enable_real_scanning = True
            mock_result = ScanResult(
                scan_id="test-123",
                status=ScanStatus.COMPLETED,
                target_range="192.168.1.0/24",
            )
            mock_scanner = MagicMock()
            mock_scanner.scan_network = AsyncMock(return_value=mock_result)
            mock_get_scanner.return_value = mock_scanner

            # Perform scan
            result = await self.orchestrator.start_scan(
                target="192.168.1.0/24",
                user_consent=True,
            )

            # Check history
            assert result.scan_id in self.orchestrator._scan_history

    @pytest.mark.asyncio
    async def test_get_scan_history(self):
        """Test getting scan history."""
        # Add some scans to datastore (scans are now loaded from database)
        for i in range(5):
            scan_time = datetime.utcnow() - timedelta(minutes=i)
            self.orchestrator._datastore.save_scan(
                user_id="local",
                scan_id=f"scan-{i}",
                scan_type="quick",
                status="completed",
                target_range="192.168.1.0/24",
                started_at=scan_time,
                completed_at=scan_time,
                progress=100.0,
            )

        # Get history with limit
        history = await self.orchestrator.get_scan_history(limit=3)
        assert len(history) == 3

        # Get history with offset
        history = await self.orchestrator.get_scan_history(limit=3, offset=2)
        assert len(history) == 3

    # =========================================================================
    # Scan Status Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_scan_status(self):
        """Test getting status of a specific scan."""
        # Add scan to history
        scan = ScanResult(
            scan_id="test-scan",
            status=ScanStatus.COMPLETED,
            progress=100.0,
        )
        self.orchestrator._scan_history["test-scan"] = scan

        result = await self.orchestrator.get_scan_status("test-scan")
        assert result is not None
        assert result.scan_id == "test-scan"
        assert result.status == ScanStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_get_scan_status_not_found(self):
        """Test getting status of non-existent scan."""
        result = await self.orchestrator.get_scan_status("nonexistent")
        assert result is None

    # =========================================================================
    # Network Detection Tests
    # =========================================================================

    def test_detect_local_network(self):
        """Test local network detection."""
        result = self.orchestrator.detect_local_network()

        # Could be None if netifaces not available
        if result is not None:
            assert "/" in result  # CIDR notation
            assert result.startswith(("10.", "172.", "192.168."))

    def test_get_network_interfaces(self):
        """Test getting network interfaces."""
        result = self.orchestrator.get_network_interfaces()

        assert isinstance(result, list)
        # Each interface should have expected keys
        for iface in result:
            assert "name" in iface
            assert "ip" in iface
            assert "network" in iface

    # =========================================================================
    # Target Validation Tests
    # =========================================================================

    def test_validate_target_valid(self):
        """Test validating a valid target."""
        result = self.orchestrator.validate_target("192.168.1.0/24")

        assert result["is_private"] is True
        assert "num_hosts" in result

    def test_validate_target_invalid(self):
        """Test validating an invalid target."""
        with pytest.raises(NetworkValidationError):
            self.orchestrator.validate_target("8.8.8.8")

    # =========================================================================
    # Mode Routing Tests
    # =========================================================================

    def test_get_application_mode_defaults_to_training(self):
        """Test that application mode defaults to training if not set."""
        # Mock datastore to return no preference
        with patch("app.services.scanner.orchestrator.get_datastore") as mock_get_datastore:
            mock_datastore = MagicMock()
            mock_datastore.get_preference.return_value = None
            mock_get_datastore.return_value = mock_datastore

            mode = self.orchestrator._get_application_mode()
            assert mode == "training"

    def test_get_application_mode_returns_stored_mode(self):
        """Test that application mode is read from datastore."""
        # Mock datastore to return live mode
        with patch("app.services.scanner.orchestrator.get_datastore") as mock_get_datastore:
            mock_datastore = MagicMock()
            mock_datastore.get_preference.return_value = '{"mode": "live", "require_confirmation_for_live": true}'
            mock_get_datastore.return_value = mock_datastore

            mode = self.orchestrator._get_application_mode()
            assert mode == "live"

    def test_get_scanner_returns_fake_in_training_mode(self):
        """Test that _get_scanner returns FakeNetworkGenerator in training mode."""
        # Mock mode to return training
        with patch.object(self.orchestrator, "_get_application_mode", return_value="training"):
            scanner = self.orchestrator._get_scanner()
            assert isinstance(scanner, FakeNetworkGenerator)

    def test_get_scanner_returns_nmap_in_live_mode(self):
        """Test that _get_scanner returns NmapScanner in live mode."""
        # Mock mode to return live
        with patch.object(self.orchestrator, "_get_application_mode", return_value="live"):
            scanner = self.orchestrator._get_scanner()
            assert isinstance(scanner, NmapScanner)

    def test_get_scanner_caches_fake_scanner(self):
        """Test that FakeNetworkGenerator is cached across calls."""
        with patch.object(self.orchestrator, "_get_application_mode", return_value="training"):
            scanner1 = self.orchestrator._get_scanner()
            scanner2 = self.orchestrator._get_scanner()
            assert scanner1 is scanner2

    def test_get_scanner_caches_nmap_scanner(self):
        """Test that NmapScanner is cached across calls."""
        with patch.object(self.orchestrator, "_get_application_mode", return_value="live"):
            scanner1 = self.orchestrator._get_scanner()
            scanner2 = self.orchestrator._get_scanner()
            assert scanner1 is scanner2

    @pytest.mark.asyncio
    async def test_training_mode_scan_completes(self):
        """Test that scans complete successfully in training mode."""
        # Mock mode to return training
        with patch.object(self.orchestrator, "_get_application_mode", return_value="training"):
            # Set last scan time to past to avoid cooldown
            self.orchestrator._last_scan_time = datetime.utcnow() - timedelta(hours=1)

            # Start scan
            result = await self.orchestrator.start_scan(
                target="192.168.1.0/24",
                scan_type=ScanType.QUICK,
                user_consent=True,
            )

            # Should return a pending result immediately
            assert result.status == ScanStatus.PENDING
            assert result.target_range == "192.168.1.0/24"

    @pytest.mark.asyncio
    async def test_live_mode_requires_enable_real_scanning(self):
        """Test that live mode requires enable_real_scanning to be True."""
        # Mock mode to return live and disable real scanning
        with patch.object(
            self.orchestrator, "_get_application_mode", return_value="live"
        ), patch("app.services.scanner.orchestrator.settings") as mock_settings:
            mock_settings.enable_real_scanning = False
            mock_settings.scan_cooldown = 5  # Add scan_cooldown to mock
            self.orchestrator._last_scan_time = datetime.utcnow() - timedelta(hours=1)

            # Should raise error
            with pytest.raises(RuntimeError) as exc_info:
                await self.orchestrator.start_scan(
                    target="192.168.1.0/24",
                    user_consent=True,
                )

            assert "switch to training mode" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_training_mode_bypasses_enable_real_scanning_check(self):
        """Test that training mode doesn't require enable_real_scanning."""
        # Mock mode to return training and disable real scanning
        with patch.object(
            self.orchestrator, "_get_application_mode", return_value="training"
        ), patch("app.services.scanner.orchestrator.settings") as mock_settings:
            mock_settings.enable_real_scanning = False
            mock_settings.scan_cooldown = 5  # Add scan_cooldown to mock
            self.orchestrator._last_scan_time = datetime.utcnow() - timedelta(hours=1)

            # Should succeed in training mode
            result = await self.orchestrator.start_scan(
                target="192.168.1.0/24",
                user_consent=True,
            )

            assert result.status == ScanStatus.PENDING


class TestGetScanOrchestrator:
    """Tests for the get_scan_orchestrator factory function."""

    def test_returns_singleton(self):
        """Test that factory returns singleton instance."""
        # Clear any existing instance
        import app.services.scanner.orchestrator as module
        module._orchestrator = None

        orch1 = get_scan_orchestrator()
        orch2 = get_scan_orchestrator()

        assert orch1 is orch2

    def test_creates_orchestrator(self):
        """Test that factory creates an orchestrator."""
        # Clear any existing instance
        import app.services.scanner.orchestrator as module
        module._orchestrator = None

        result = get_scan_orchestrator()

        assert isinstance(result, ScanOrchestrator)

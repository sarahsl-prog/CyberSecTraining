"""
Scan orchestrator module.

This module coordinates network scanning operations, manages scan lifecycle,
handles rate limiting, and provides a unified interface for all scanning operations.
It serves as the main entry point for the API layer to interact with scanning.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
import uuid

from app.core.logging import get_logger, get_audit_logger
from app.config import settings
from app.services.scanner.base import ScanType, ScanStatus, ScanResult, DeviceInfo
from app.services.scanner.nmap_scanner import NmapScanner
from app.services.scanner.network_validator import (
    NetworkValidator,
    NetworkValidationError,
    get_local_network,
    get_network_interfaces,
)

logger = get_logger("scanner")
audit_logger = get_audit_logger()


class ScanOrchestrator:
    """
    Orchestrates network scanning operations.

    This class provides:
    - Unified interface for all scan types
    - Rate limiting (one scan at a time)
    - Scan history management
    - User consent verification
    - Progress tracking

    Example:
        >>> orchestrator = ScanOrchestrator()
        >>> result = await orchestrator.start_scan(
        ...     target="192.168.1.0/24",
        ...     scan_type=ScanType.QUICK,
        ...     user_consent=True
        ... )
        >>> print(f"Found {len(result.devices)} devices")
    """

    def __init__(self):
        """Initialize the scan orchestrator."""
        self._scanner: Optional[NmapScanner] = None
        self._validator = NetworkValidator(max_network_size=settings.max_network_size)
        self._scan_history: dict[str, ScanResult] = {}
        self._current_scan: Optional[str] = None
        self._last_scan_time: Optional[datetime] = None
        self._scan_lock = asyncio.Lock()

        logger.info("ScanOrchestrator initialized")

    def _get_scanner(self) -> NmapScanner:
        """
        Lazy-load the nmap scanner.

        Returns:
            NmapScanner instance

        Raises:
            RuntimeError: If nmap is not available
        """
        if self._scanner is None:
            self._scanner = NmapScanner()
        return self._scanner

    async def start_scan(
        self,
        target: str,
        scan_type: ScanType = ScanType.QUICK,
        port_range: Optional[str] = None,
        user_consent: bool = False,
    ) -> ScanResult:
        """
        Start a new network scan.

        This method validates the request, checks rate limits, verifies consent,
        and initiates the scan.

        Args:
            target: Network range to scan (e.g., "192.168.1.0/24")
            scan_type: Type of scan (QUICK, DEEP, DISCOVERY, CUSTOM)
            port_range: Custom port range for CUSTOM scan type
            user_consent: Whether user has confirmed network ownership

        Returns:
            ScanResult with scan status and (eventually) results

        Raises:
            NetworkValidationError: If target is not valid
            PermissionError: If user consent is not provided
            RuntimeError: If another scan is already running
        """
        # Verify user consent
        if not user_consent:
            logger.warning("Scan attempted without user consent")
            audit_logger.warning(f"Scan blocked - no consent | target={target}")
            raise PermissionError(
                "User consent is required. You must confirm ownership of the network before scanning. "
                "This tool should only be used on networks you own or have "
                "explicit permission to scan."
            )

        # Validate target
        self._validator.validate(target)

        # Check rate limits
        await self._check_rate_limits()

        # Check if scanning is enabled (after validation checks for testability)
        if not settings.enable_real_scanning:
            logger.warning("Real scanning is disabled")
            raise RuntimeError(
                "Real network scanning is disabled. "
                "Enable it in settings or use scenario mode."
            )

        # Start scan
        async with self._scan_lock:
            scanner = self._get_scanner()

            # Log audit event
            audit_logger.info(
                f"Scan started with consent | "
                f"target={target} | "
                f"type={scan_type.value} | "
                f"user_consent={user_consent}"
            )

            # Execute scan asynchronously in background
            logger.info(f"Starting {scan_type.value} scan of {target}")

            # Create initial scan result with PENDING status
            scan_id = str(uuid.uuid4())
            result = ScanResult(
                scan_id=scan_id,
                target_range=target,
                scan_type=scan_type,
                status=ScanStatus.PENDING,
            )

            # Store in history immediately
            self._scan_history[scan_id] = result
            self._current_scan = scan_id

            # Start scan in background task
            asyncio.create_task(self._run_scan_background(scan_id, target, scan_type, port_range))

            return result

    async def _run_scan_background(
        self,
        scan_id: str,
        target: str,
        scan_type: ScanType,
        port_range: Optional[str] = None,
    ) -> None:
        """
        Run a scan in the background and update the result.

        Args:
            scan_id: Unique identifier for the scan
            target: Network target to scan
            scan_type: Type of scan to perform
            port_range: Optional custom port range
        """
        try:
            scanner = self._get_scanner()

            # Execute the scan with the provided scan_id
            result = await scanner.scan_network(target, scan_type, port_range, scan_id=scan_id)

            # Update the stored result with actual scan data
            if scan_id in self._scan_history:
                self._scan_history[scan_id] = result

            # Mark as complete
            self._current_scan = None
            self._last_scan_time = datetime.utcnow()

            logger.info(f"Background scan {scan_id} completed: {len(result.devices)} devices found")

        except Exception as e:
            logger.exception(f"Background scan {scan_id} failed: {e}")

            # Update scan status to failed
            if scan_id in self._scan_history:
                self._scan_history[scan_id].status = ScanStatus.FAILED
                self._scan_history[scan_id].error_message = f"Scan error: {str(e)}"
                self._scan_history[scan_id].completed_at = datetime.utcnow()

            self._current_scan = None

    async def _check_rate_limits(self) -> None:
        """
        Check rate limits before starting a scan.

        Raises:
            RuntimeError: If rate limits are exceeded
        """
        # Check if another scan is running
        if self._current_scan:
            scan = self._scan_history.get(self._current_scan)
            if scan and scan.status == ScanStatus.RUNNING:
                raise RuntimeError(
                    "Another scan is already in progress. "
                    "Please wait for it to complete or cancel it."
                )

        # Check cooldown period
        if self._last_scan_time:
            elapsed = datetime.utcnow() - self._last_scan_time
            cooldown = timedelta(seconds=settings.scan_cooldown)

            if elapsed < cooldown:
                remaining = (cooldown - elapsed).total_seconds()
                logger.warning(f"Scan cooldown: {remaining:.0f}s remaining")
                raise RuntimeError(
                    f"Please wait {remaining:.0f} seconds before starting another scan. "
                    f"This prevents excessive network traffic."
                )

    async def get_scan_status(self, scan_id: str) -> Optional[ScanResult]:
        """
        Get the status and results of a scan.

        Args:
            scan_id: Unique identifier of the scan

        Returns:
            ScanResult or None if not found
        """
        # Check current scanner first
        if self._scanner:
            result = self._scanner.get_scan_result(scan_id)
            if result:
                return result

        # Check history
        return self._scan_history.get(scan_id)

    async def cancel_scan(self, scan_id: str) -> bool:
        """
        Cancel a running scan.

        Args:
            scan_id: Unique identifier of the scan

        Returns:
            True if cancelled, False if not found or already complete
        """
        if self._scanner:
            cancelled = await self._scanner.cancel_scan(scan_id)
            if cancelled:
                self._current_scan = None
                return True
        return False

    async def get_scan_history(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> list[ScanResult]:
        """
        Get scan history.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of ScanResult objects, most recent first
        """
        # Combine with scanner's active scans
        all_scans = dict(self._scan_history)
        if self._scanner:
            for scan in self._scanner.get_all_scans():
                all_scans[scan.scan_id] = scan

        # Sort by start time (most recent first)
        sorted_scans = sorted(
            all_scans.values(),
            key=lambda s: s.started_at or datetime.min,
            reverse=True,
        )

        return sorted_scans[offset : offset + limit]

    def get_network_interfaces(self) -> list[dict]:
        """
        Get available network interfaces.

        Returns:
            List of interface information dictionaries
        """
        return get_network_interfaces()

    def detect_local_network(self) -> Optional[str]:
        """
        Auto-detect the local network range.

        Returns:
            Network range in CIDR notation or None
        """
        return get_local_network()

    def validate_target(self, target: str) -> dict:
        """
        Validate a scan target and return information about it.

        Args:
            target: IP address or network range

        Returns:
            Dictionary with validation result and network info

        Raises:
            NetworkValidationError: If target is invalid
        """
        return self._validator.get_network_info(target)


# Singleton instance for the application
_orchestrator: Optional[ScanOrchestrator] = None


def get_scan_orchestrator() -> ScanOrchestrator:
    """
    Get the global ScanOrchestrator instance.

    This provides a singleton orchestrator for the application,
    ensuring scan rate limits and history are shared.

    Returns:
        ScanOrchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ScanOrchestrator()
    return _orchestrator

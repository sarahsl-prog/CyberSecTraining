"""
Scan orchestrator module.

This module coordinates network scanning operations, manages scan lifecycle,
handles rate limiting, and provides a unified interface for all scanning operations.
It serves as the main entry point for the API layer to interact with scanning.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, Union
import uuid

from app.core.logging import get_logger, get_audit_logger
from app.config import settings
from app.services.scanner.base import ScanType, ScanStatus, ScanResult, DeviceInfo
from app.services.scanner.nmap_scanner import NmapScanner
from app.services.scanner.fake_network_generator import FakeNetworkGenerator
from app.services.scanner.network_validator import (
    NetworkValidator,
    NetworkValidationError,
    get_local_network,
    get_network_interfaces,
)
from app.dependencies import get_datastore

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
        self._nmap_scanner: Optional[NmapScanner] = None
        self._fake_scanner: Optional[FakeNetworkGenerator] = None
        self._validator = NetworkValidator(max_network_size=settings.max_network_size)
        self._scan_history: dict[str, ScanResult] = {}
        self._current_scan: Optional[str] = None
        self._last_scan_time: Optional[datetime] = None
        self._scan_lock = asyncio.Lock()
        self._datastore = get_datastore()

        logger.info("ScanOrchestrator initialized")

    def _get_application_mode(self) -> str:
        """
        Get the current application mode from settings.

        Returns:
            'training' or 'live' mode string

        Note:
            Defaults to 'training' if mode is not set in preferences.
        """
        try:
            datastore = get_datastore()
            mode_settings_json = datastore.get_preference("local", "mode_settings")

            if mode_settings_json:
                import json
                mode_data = json.loads(mode_settings_json)
                return mode_data.get("mode", "training")

            # Default to training mode if not set
            return "training"
        except Exception as e:
            logger.warning(f"Failed to get application mode, defaulting to training: {e}")
            return "training"

    def _get_scanner(self) -> Union[NmapScanner, FakeNetworkGenerator]:
        """
        Get the appropriate scanner based on application mode.

        Returns:
            NmapScanner for live mode, FakeNetworkGenerator for training mode

        Raises:
            RuntimeError: If nmap is not available in live mode
        """
        mode = self._get_application_mode()

        if mode == "live":
            # Live mode - use real nmap scanner
            if self._nmap_scanner is None:
                self._nmap_scanner = NmapScanner()
            return self._nmap_scanner
        else:
            # Training mode - use fake network generator
            if self._fake_scanner is None:
                self._fake_scanner = FakeNetworkGenerator(settings)
            return self._fake_scanner

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
        # Get current application mode
        mode = self._get_application_mode()

        # Verify user consent
        if not user_consent:
            logger.warning(f"Scan attempted without user consent | mode={mode}")
            audit_logger.warning(f"Scan blocked - no consent | target={target} | mode={mode}")
            raise PermissionError(
                "User consent is required. You must confirm ownership of the network before scanning. "
                "This tool should only be used on networks you own or have "
                "explicit permission to scan."
            )

        # Validate target
        self._validator.validate(target)

        # Check rate limits
        await self._check_rate_limits()

        # Check if real scanning is enabled (only in live mode)
        if mode == "live" and not settings.enable_real_scanning:
            logger.warning("Real scanning is disabled but live mode is active")
            raise RuntimeError(
                "Real network scanning is disabled. "
                "Enable it in settings or switch to training mode."
            )

        # Start scan
        async with self._scan_lock:
            scanner = self._get_scanner()

            # Log audit event with mode information
            audit_logger.info(
                f"Scan started with consent | "
                f"target={target} | "
                f"type={scan_type.value} | "
                f"mode={mode} | "
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

            # Save initial scan to database
            self._datastore.save_scan(
                user_id="local",
                scan_id=scan_id,
                scan_type=scan_type.value,
                status=ScanStatus.PENDING.value,
                target_range=target,
                port_range=port_range,
                started_at=None,
                completed_at=None,
                progress=0.0,
                scanned_hosts=0,
                total_hosts=0,
                results_summary=None,
            )

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

            # Save completed scan to database
            self._datastore.save_scan(
                user_id="local",
                scan_id=scan_id,
                scan_type=result.scan_type.value,
                status=result.status.value,
                target_range=result.target_range,
                port_range=port_range,
                started_at=result.started_at,
                completed_at=result.completed_at,
                progress=result.progress,
                scanned_hosts=result.scanned_hosts,
                total_hosts=result.total_hosts,
                results_summary=json.dumps(result.to_dict()),
            )

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

                # Save failed scan to database
                self._datastore.save_scan(
                    user_id="local",
                    scan_id=scan_id,
                    scan_type=self._scan_history[scan_id].scan_type.value,
                    status=ScanStatus.FAILED.value,
                    target_range=self._scan_history[scan_id].target_range,
                    port_range=port_range,
                    started_at=self._scan_history[scan_id].started_at,
                    completed_at=self._scan_history[scan_id].completed_at,
                    progress=self._scan_history[scan_id].progress,
                    scanned_hosts=self._scan_history[scan_id].scanned_hosts,
                    total_hosts=self._scan_history[scan_id].total_hosts,
                    results_summary=json.dumps({
                        "error": str(e),
                        "scan_id": scan_id,
                        "status": "failed",
                    }),
                )

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

    def _scan_dict_to_result(self, scan_dict: dict) -> ScanResult:
        """
        Convert a scan dictionary from the database to a ScanResult object.

        Args:
            scan_dict: Scan data from database

        Returns:
            ScanResult object
        """
        # Parse results_summary if available
        devices = []
        if scan_dict.get("results_summary"):
            try:
                summary = json.loads(scan_dict["results_summary"])
                devices_data = summary.get("devices", [])
                for dev_data in devices_data:
                    devices.append(DeviceInfo(**dev_data))
            except (json.JSONDecodeError, TypeError):
                pass

        # Parse datetime strings
        started_at = None
        completed_at = None
        if scan_dict.get("started_at"):
            if isinstance(scan_dict["started_at"], str):
                started_at = datetime.fromisoformat(scan_dict["started_at"])
            else:
                started_at = scan_dict["started_at"]

        if scan_dict.get("completed_at"):
            if isinstance(scan_dict["completed_at"], str):
                completed_at = datetime.fromisoformat(scan_dict["completed_at"])
            else:
                completed_at = scan_dict["completed_at"]

        return ScanResult(
            scan_id=scan_dict["scan_id"],
            target_range=scan_dict.get("target_range", ""),
            scan_type=ScanType(scan_dict["scan_type"]),
            status=ScanStatus(scan_dict["status"]),
            devices=devices,
            started_at=started_at,
            completed_at=completed_at,
            progress=scan_dict.get("progress", 0.0),
            scanned_hosts=scan_dict.get("scanned_hosts", 0),
            total_hosts=scan_dict.get("total_hosts", 0),
        )

    async def get_scan_status(self, scan_id: str) -> Optional[ScanResult]:
        """
        Get the status and results of a scan.

        Args:
            scan_id: Unique identifier of the scan

        Returns:
            ScanResult or None if not found
        """
        # Check current nmap scanner first (only NmapScanner has get_scan_result)
        if self._nmap_scanner:
            result = self._nmap_scanner.get_scan_result(scan_id)
            if result:
                return result

        # Check in-memory history
        if scan_id in self._scan_history:
            return self._scan_history[scan_id]

        # Check database
        scan_dict = self._datastore.get_scan("local", scan_id)
        if scan_dict:
            return self._scan_dict_to_result(scan_dict)

        return None

    async def cancel_scan(self, scan_id: str) -> bool:
        """
        Cancel a running scan.

        Args:
            scan_id: Unique identifier of the scan

        Returns:
            True if cancelled, False if not found or already complete

        Note:
            In training mode, scans complete immediately so cancellation is not supported.
        """
        # Only NmapScanner supports cancellation (FakeNetworkGenerator completes immediately)
        if self._nmap_scanner:
            cancelled = await self._nmap_scanner.cancel_scan(scan_id)
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
        Get scan history from database.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of ScanResult objects, most recent first
        """
        # Load scans from database
        scan_dicts = self._datastore.list_scans("local", limit=limit, offset=offset)

        # Convert to ScanResult objects
        results = []
        for scan_dict in scan_dicts:
            try:
                results.append(self._scan_dict_to_result(scan_dict))
            except Exception as e:
                logger.warning(f"Failed to convert scan {scan_dict.get('scan_id')}: {e}")

        return results

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

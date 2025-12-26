"""
Nmap scanner implementation.

This module provides the primary network scanning functionality using nmap.
It wraps the python-nmap library to provide async scanning capabilities
with progress tracking and proper error handling.

Requirements:
- nmap must be installed on the system
- python-nmap package

Note: Some features (like OS detection) may require elevated privileges.
"""

import asyncio
from datetime import datetime, UTC
from typing import Optional
import xml.etree.ElementTree as ET

from app.core.logging import get_logger, get_audit_logger
from app.config import settings
from app.services.scanner.base import (
    BaseScannerInterface,
    ScanType,
    ScanStatus,
    ScanResult,
    DeviceInfo,
    PortInfo,
)
from app.services.scanner.network_validator import NetworkValidator, NetworkValidationError
from app.services.scanner.device_fingerprint import DeviceFingerprinter

logger = get_logger("scanner")
audit_logger = get_audit_logger()


class NmapScanner(BaseScannerInterface):
    """
    Network scanner implementation using nmap.

    This class provides async network scanning using the nmap tool.
    It supports quick scans (common ports), deep scans (all ports),
    and host discovery.

    Example:
        >>> scanner = NmapScanner()
        >>> result = await scanner.scan_network("192.168.1.0/24", ScanType.QUICK)
        >>> for device in result.devices:
        ...     print(f"{device.ip}: {len(device.open_ports)} ports open")
    """

    def __init__(self):
        """
        Initialize the nmap scanner.

        Raises:
            RuntimeError: If nmap is not installed
        """
        self._nmap = None
        self._validator = NetworkValidator(max_network_size=settings.max_network_size)
        self._fingerprinter = DeviceFingerprinter()
        self._active_scans: dict[str, ScanResult] = {}
        self._scan_processes: dict[str, asyncio.subprocess.Process] = {}

        # Verify nmap is available
        self._verify_nmap_installed()

        logger.info("NmapScanner initialized")

    def _verify_nmap_installed(self) -> None:
        """
        Verify that nmap is installed and accessible.

        Raises:
            RuntimeError: If nmap is not installed
        """
        try:
            import nmap
            self._nmap = nmap.PortScanner()
            # Test that nmap binary exists
            version = self._nmap.nmap_version()
            logger.info(f"Using nmap version: {version}")
        except nmap.PortScannerError as e:
            logger.error(f"Nmap not found: {e}")
            raise RuntimeError(
                "Nmap is not installed or not in PATH. "
                "Please install nmap: https://nmap.org/download.html"
            )
        except Exception as e:
            logger.error(f"Error initializing nmap: {e}")
            raise RuntimeError(f"Failed to initialize nmap scanner: {e}")

    def _get_scan_arguments(self, scan_type: ScanType, port_range: Optional[str] = None) -> str:
        """
        Get nmap command arguments for a scan type.

        Args:
            scan_type: Type of scan to perform
            port_range: Custom port range (overrides default)

        Returns:
            Nmap argument string
        """
        base_args = "-sV"  # Version detection

        if scan_type == ScanType.QUICK:
            ports = port_range or settings.default_port_range
            return f"{base_args} -T4 -p {ports}"

        elif scan_type == ScanType.DEEP:
            ports = port_range or settings.deep_scan_port_range
            return f"{base_args} -T3 -p {ports}"

        elif scan_type == ScanType.DISCOVERY:
            return "-sn -T4"  # Ping scan only

        elif scan_type == ScanType.CUSTOM:
            ports = port_range or settings.default_port_range
            return f"{base_args} -T4 -p {ports}"

        return base_args

    async def scan_network(
        self,
        target: str,
        scan_type: ScanType = ScanType.QUICK,
        port_range: Optional[str] = None,
        scan_id: Optional[str] = None,
    ) -> ScanResult:
        """
        Perform a network scan on the specified target.

        This method validates the target, performs the scan, and returns
        detailed results including discovered devices and their open ports.

        Args:
            target: IP address or network range (e.g., "192.168.1.0/24")
            scan_type: Type of scan to perform (QUICK, DEEP, DISCOVERY, CUSTOM)
            port_range: Optional custom port range
            scan_id: Optional scan ID (will be generated if not provided)

        Returns:
            ScanResult with discovered devices and scan metadata

        Raises:
            NetworkValidationError: If target is not a valid private network
        """
        # Create scan result object
        result = ScanResult(
            scan_id=scan_id or str(__import__('uuid').uuid4()),
            target_range=target,
            scan_type=scan_type,
            status=ScanStatus.PENDING,
        )
        self._active_scans[result.scan_id] = result

        try:
            # Validate target network
            logger.info(f"Starting {scan_type.value} scan of {target}")
            self._validator.validate(target)

            # Audit log the scan
            audit_logger.info(
                f"Network scan initiated | "
                f"scan_id={result.scan_id} | "
                f"target={target} | "
                f"type={scan_type.value}"
            )

            # Update status
            result.status = ScanStatus.RUNNING
            result.started_at = datetime.now(UTC)

            # Get scan arguments
            arguments = self._get_scan_arguments(scan_type, port_range)
            logger.debug(f"Scan arguments: {arguments}")

            # Run the scan in a thread pool (nmap is blocking)
            result = await self._run_scan(result, target, arguments)

            # Fingerprint all discovered devices
            for device in result.devices:
                self._fingerprinter.identify_device(device)
                self._fingerprinter.enrich_ports(device)

            # Mark complete
            result.status = ScanStatus.COMPLETED
            result.completed_at = datetime.now(UTC)
            result.progress = 100.0

            # Audit log completion
            audit_logger.info(
                f"Network scan completed | "
                f"scan_id={result.scan_id} | "
                f"devices_found={len(result.devices)} | "
                f"duration={(result.completed_at - result.started_at).total_seconds():.1f}s"
            )

            logger.info(
                f"Scan {result.scan_id} completed: "
                f"{len(result.devices)} devices found"
            )

        except NetworkValidationError as e:
            logger.error(f"Network validation failed: {e}")
            result.status = ScanStatus.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.now(UTC)
            audit_logger.warning(
                f"Scan blocked - invalid target | "
                f"scan_id={result.scan_id} | "
                f"target={target} | "
                f"reason={e}"
            )

        except Exception as e:
            logger.exception(f"Scan failed: {e}")
            result.status = ScanStatus.FAILED
            result.error_message = f"Scan error: {str(e)}"
            result.completed_at = datetime.now(UTC)
            audit_logger.error(
                f"Scan failed | "
                f"scan_id={result.scan_id} | "
                f"error={e}"
            )

        finally:
            # Clean up
            if result.scan_id in self._scan_processes:
                del self._scan_processes[result.scan_id]

        return result

    async def _run_scan(
        self,
        result: ScanResult,
        target: str,
        arguments: str,
    ) -> ScanResult:
        """
        Execute the nmap scan in a background thread.

        Args:
            result: ScanResult to update
            target: Scan target
            arguments: Nmap arguments

        Returns:
            Updated ScanResult
        """
        loop = asyncio.get_event_loop()

        # Run nmap in executor to avoid blocking
        def do_scan():
            logger.debug(f"Executing nmap scan: {target} with args: {arguments}")
            self._nmap.scan(hosts=target, arguments=arguments)
            return self._nmap

        try:
            # Execute scan with timeout
            scanner = await asyncio.wait_for(
                loop.run_in_executor(None, do_scan),
                timeout=settings.scan_timeout,
            )

            # Parse results
            result = self._parse_scan_results(scanner, result)

        except asyncio.TimeoutError:
            logger.warning(f"Scan timed out after {settings.scan_timeout}s")
            result.error_message = f"Scan timed out after {settings.scan_timeout} seconds"
            result.status = ScanStatus.FAILED

        return result

    def _parse_scan_results(self, scanner, result: ScanResult) -> ScanResult:
        """
        Parse nmap scan results into DeviceInfo objects.

        Args:
            scanner: Completed nmap PortScanner
            result: ScanResult to populate

        Returns:
            Updated ScanResult
        """
        all_hosts = scanner.all_hosts()
        result.total_hosts = len(all_hosts)

        for host in all_hosts:
            result.scanned_hosts += 1

            try:
                host_data = scanner[host]
                device = self._parse_host(host, host_data)
                if device.is_up:
                    result.devices.append(device)
                    logger.debug(
                        f"Found device: {device.ip} "
                        f"({len(device.open_ports)} ports)"
                    )
            except Exception as e:
                logger.warning(f"Error parsing host {host}: {e}")

            # Update progress
            if result.total_hosts > 0:
                result.progress = (result.scanned_hosts / result.total_hosts) * 100

        return result

    def _parse_host(self, ip: str, host_data: dict) -> DeviceInfo:
        """
        Parse a single host from nmap results.

        Args:
            ip: IP address
            host_data: Nmap host data dictionary

        Returns:
            DeviceInfo object
        """
        device = DeviceInfo(ip=ip)

        # Check if host is up
        state = host_data.state()
        device.is_up = state == "up"

        if not device.is_up:
            return device

        # Get hostname
        hostnames = host_data.hostnames()
        if hostnames and hostnames[0].get("name"):
            device.hostname = hostnames[0]["name"]

        # Get MAC address (only available for local network scans)
        if "addresses" in host_data and "mac" in host_data["addresses"]:
            device.mac = host_data["addresses"]["mac"]

        # Get vendor from nmap (if available)
        if "vendor" in host_data and device.mac:
            vendors = host_data["vendor"]
            if device.mac in vendors:
                device.vendor = vendors[device.mac]

        # Get OS information
        if "osmatch" in host_data:
            os_matches = host_data["osmatch"]
            if os_matches:
                best_match = os_matches[0]
                device.os = best_match.get("name")
                try:
                    device.os_accuracy = int(best_match.get("accuracy", 0))
                except ValueError:
                    device.os_accuracy = 0

        # Get open ports
        for protocol in ["tcp", "udp"]:
            if protocol in host_data:
                for port_num, port_data in host_data[protocol].items():
                    if port_data.get("state") == "open":
                        port = PortInfo(
                            port=port_num,
                            protocol=protocol,
                            state=port_data.get("state", "open"),
                            service=port_data.get("name"),
                            version=port_data.get("version"),
                            banner=port_data.get("product"),
                        )
                        device.open_ports.append(port)

        # Sort ports by number
        device.open_ports.sort(key=lambda p: p.port)

        return device

    async def get_scan_progress(self, scan_id: str) -> float:
        """
        Get the current progress of a running scan.

        Args:
            scan_id: Unique identifier of the scan

        Returns:
            Progress percentage (0.0 to 100.0)
        """
        if scan_id in self._active_scans:
            return self._active_scans[scan_id].progress
        return 100.0  # Assume completed if not found

    async def cancel_scan(self, scan_id: str) -> bool:
        """
        Cancel a running scan.

        Args:
            scan_id: Unique identifier of the scan to cancel

        Returns:
            True if scan was cancelled, False if not found or already complete
        """
        if scan_id not in self._active_scans:
            logger.warning(f"Cannot cancel scan {scan_id}: not found")
            return False

        result = self._active_scans[scan_id]

        if result.status != ScanStatus.RUNNING:
            logger.warning(f"Cannot cancel scan {scan_id}: not running")
            return False

        # Try to terminate the process
        if scan_id in self._scan_processes:
            process = self._scan_processes[scan_id]
            process.terminate()
            await process.wait()

        result.status = ScanStatus.CANCELLED
        result.completed_at = datetime.now(UTC)

        audit_logger.info(f"Scan cancelled | scan_id={scan_id}")
        logger.info(f"Scan {scan_id} cancelled")

        return True

    async def discover_hosts(self, target: str) -> list[str]:
        """
        Perform host discovery without port scanning.

        This is a fast operation that only checks which hosts respond to
        ping or other discovery probes.

        Args:
            target: Network range to scan (e.g., "192.168.1.0/24")

        Returns:
            List of IP addresses that responded to probes
        """
        result = await self.scan_network(target, ScanType.DISCOVERY)

        if result.status == ScanStatus.COMPLETED:
            return [device.ip for device in result.devices if device.is_up]
        return []

    def get_scan_result(self, scan_id: str) -> Optional[ScanResult]:
        """
        Get a scan result by ID.

        Args:
            scan_id: Unique identifier of the scan

        Returns:
            ScanResult or None if not found
        """
        return self._active_scans.get(scan_id)

    def get_all_scans(self) -> list[ScanResult]:
        """
        Get all scan results (active and completed).

        Returns:
            List of all ScanResult objects
        """
        return list(self._active_scans.values())

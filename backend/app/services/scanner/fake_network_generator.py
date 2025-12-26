"""
Fake network data generator for training mode.

This module generates realistic but fake network scan data for educational purposes,
allowing users to practice network scanning and security analysis in a safe environment
without performing actual network scans.
"""

import asyncio
import hashlib
import ipaddress
import random
from datetime import datetime, timedelta
from typing import Optional

from app.config import Settings
from app.services.scanner.base import (
    PortInfo,
    DeviceInfo,
    ScanResult,
    ScanStatus,
    ScanType,
)
from app.services.scanner.device_fingerprint import DeviceType


class FakeNetworkGenerator:
    """
    Generates realistic fake network scan data for training mode.

    This class implements the same interface as NmapScanner but generates
    deterministic fake data instead of performing real network scans. The
    generated data is based on the target IP range and uses seeding to ensure
    consistent results for the same inputs.

    Features:
    - Deterministic generation (same input → same output)
    - Realistic device types, ports, and services
    - Simulated scan progress for realistic UX
    - MAC addresses with vendor prefixes
    - Hostname generation based on device type
    """

    # Device type templates with associated ports
    # These define realistic port combinations for each device type
    DEVICE_TEMPLATES = {
        DeviceType.ROUTER: {
            "ports": [80, 443, 22, 23, 53],
            "services": {80: "http", 443: "https", 22: "ssh", 23: "telnet", 53: "dns"},
            "hostname_prefix": "router",
            "os": "Linux 3.x - 4.x",
        },
        DeviceType.PRINTER: {
            "ports": [631, 9100, 80, 443],
            "services": {631: "ipp", 9100: "jetdirect", 80: "http", 443: "https"},
            "hostname_prefix": "printer",
            "os": None,
        },
        DeviceType.NAS: {
            "ports": [22, 80, 139, 445, 548, 2049, 5000, 5001],
            "services": {
                22: "ssh",
                80: "http",
                139: "netbios-ssn",
                445: "microsoft-ds",
                548: "afp",
                2049: "nfs",
                5000: "upnp",
                5001: "commplex-link",
            },
            "hostname_prefix": "nas",
            "os": "Linux 4.x",
        },
        DeviceType.WORKSTATION: {
            "ports": [135, 139, 445, 3389],
            "services": {
                135: "msrpc",
                139: "netbios-ssn",
                445: "microsoft-ds",
                3389: "ms-wbt-server",
            },
            "hostname_prefix": "workstation",
            "os": "Windows 10",
        },
        DeviceType.SERVER: {
            "ports": [22, 80, 443, 3306, 5432],
            "services": {
                22: "ssh",
                80: "http",
                443: "https",
                3306: "mysql",
                5432: "postgresql",
            },
            "hostname_prefix": "server",
            "os": "Ubuntu Linux",
        },
        DeviceType.LAPTOP: {
            "ports": [22],
            "services": {22: "ssh"},
            "hostname_prefix": "laptop",
            "os": "macOS",
        },
        DeviceType.IOT: {
            "ports": [80, 443, 1883, 8883],
            "services": {80: "http", 443: "https", 1883: "mqtt", 8883: "secure-mqtt"},
            "hostname_prefix": "iot-device",
            "os": None,
        },
        DeviceType.CAMERA: {
            "ports": [80, 554, 8080],
            "services": {80: "http", 554: "rtsp", 8080: "http-proxy"},
            "hostname_prefix": "camera",
            "os": None,
        },
    }

    # MAC vendor prefixes for realism
    MAC_VENDORS = {
        "00:1A:70": "Netgear",
        "00:11:22": "Cisco",
        "00:50:56": "VMware",
        "08:00:27": "VirtualBox",
        "00:0C:29": "VMware",
        "00:16:3E": "Xen",
        "52:54:00": "QEMU",
        "AC:DE:48": "TP-Link",
        "B8:27:EB": "Raspberry Pi",
        "DC:A6:32": "Raspberry Pi",
    }

    def __init__(self, settings: Settings):
        """
        Initialize the fake network generator.

        Args:
            settings: Application settings (used for consistency with real scanner)
        """
        self.settings = settings

    def _generate_seed(self, target: str) -> int:
        """
        Generate a deterministic seed from the target IP range.

        This ensures that the same target always produces the same fake data,
        making training scenarios predictable and repeatable.

        Args:
            target: Target IP range (e.g., "192.168.1.0/24")

        Returns:
            Integer seed for random number generator
        """
        # Use SHA-256 hash of target to generate seed
        hash_digest = hashlib.sha256(target.encode()).digest()
        # Convert first 4 bytes to integer
        return int.from_bytes(hash_digest[:4], byteorder='big')

    def _parse_network(self, target: str) -> tuple[ipaddress.IPv4Network, list[ipaddress.IPv4Address]]:
        """
        Parse target IP range and generate list of potential host IPs.

        Args:
            target: Target IP range in CIDR notation

        Returns:
            Tuple of (network object, list of host IPs)
        """
        network = ipaddress.IPv4Network(target, strict=False)
        # Get all host addresses (excluding network and broadcast)
        hosts = list(network.hosts())
        return network, hosts

    def _select_device_types(
        self, rng: random.Random, network: ipaddress.IPv4Network, count: int
    ) -> list[DeviceType]:
        """
        Select device types appropriate for the network class.

        Different network ranges suggest different device distributions:
        - 192.168.x.x: Home networks (router, printer, laptops, IoT)
        - 10.x.x.x: Enterprise networks (servers, workstations, printers)
        - 172.16-31.x.x: Small office (mix of both)

        Args:
            rng: Random number generator (seeded)
            network: Target network object
            count: Number of devices to generate

        Returns:
            List of device types to create
        """
        network_addr = str(network.network_address)
        device_types = []

        # Determine network type and device distribution
        if network_addr.startswith('192.168.'):
            # Home network - common consumer devices
            weights = {
                DeviceType.ROUTER: 1.0,  # Always have a router
                DeviceType.LAPTOP: 0.4,
                DeviceType.WORKSTATION: 0.2,
                DeviceType.PRINTER: 0.3,
                DeviceType.IOT: 0.4,
                DeviceType.CAMERA: 0.2,
                DeviceType.NAS: 0.1,
            }
        elif network_addr.startswith('10.'):
            # Enterprise network - business devices
            weights = {
                DeviceType.ROUTER: 1.0,
                DeviceType.SERVER: 0.5,
                DeviceType.WORKSTATION: 0.6,
                DeviceType.PRINTER: 0.4,
                DeviceType.NAS: 0.3,
                DeviceType.LAPTOP: 0.3,
                DeviceType.IOT: 0.1,
            }
        else:
            # Small office - balanced mix
            weights = {
                DeviceType.ROUTER: 1.0,
                DeviceType.WORKSTATION: 0.5,
                DeviceType.LAPTOP: 0.4,
                DeviceType.SERVER: 0.3,
                DeviceType.PRINTER: 0.4,
                DeviceType.NAS: 0.2,
                DeviceType.IOT: 0.2,
            }

        # Always add router first
        device_types.append(DeviceType.ROUTER)

        # Add remaining devices based on weights
        available_types = [t for t in weights.keys() if t != DeviceType.ROUTER]
        for _ in range(count - 1):
            # Weighted random selection
            device_type = rng.choices(
                available_types,
                weights=[weights[t] for t in available_types],
                k=1
            )[0]
            device_types.append(device_type)

        return device_types

    def _generate_mac(self, rng: random.Random) -> str:
        """
        Generate a realistic MAC address with vendor prefix.

        Args:
            rng: Random number generator

        Returns:
            MAC address string (e.g., "00:1A:70:XX:XX:XX")
        """
        # Select random vendor prefix
        prefix = rng.choice(list(self.MAC_VENDORS.keys()))
        # Generate random last 3 bytes
        suffix = ':'.join(f'{rng.randint(0, 255):02X}' for _ in range(3))
        return f"{prefix}:{suffix}"

    def _get_vendor_from_mac(self, mac: str) -> str:
        """
        Get vendor name from MAC address prefix.

        Args:
            mac: MAC address

        Returns:
            Vendor name or "Unknown"
        """
        prefix = mac[:8]
        return self.MAC_VENDORS.get(prefix, "Unknown")

    def _generate_device(
        self,
        rng: random.Random,
        ip: ipaddress.IPv4Address,
        device_type: DeviceType,
        index: int,
    ) -> DeviceInfo:
        """
        Generate a single fake device with realistic attributes.

        Args:
            rng: Random number generator
            ip: IP address for this device
            device_type: Type of device to generate
            index: Device index for hostname generation

        Returns:
            Generated DeviceInfo object
        """
        template = self.DEVICE_TEMPLATES[device_type]

        # Generate MAC and vendor
        mac = self._generate_mac(rng)
        vendor = self._get_vendor_from_mac(mac)

        # Generate hostname
        hostname = f"{template['hostname_prefix']}-{index:03d}"

        # Select ports (not all ports every time)
        all_ports = template['ports']
        # Randomly select 50-100% of available ports
        num_ports = rng.randint(max(1, len(all_ports) // 2), len(all_ports))
        selected_ports = rng.sample(all_ports, num_ports)

        # Create port info objects
        open_ports = [
            PortInfo(
                port=port,
                protocol="tcp",
                state="open",
                service=template['services'].get(port, "unknown"),
            )
            for port in sorted(selected_ports)
        ]

        # Simulate some devices being down (10% chance)
        is_up = rng.random() > 0.1

        return DeviceInfo(
            ip=str(ip),
            mac=mac if is_up else None,
            hostname=hostname if is_up else None,
            vendor=vendor if is_up else None,
            device_type=device_type if is_up else DeviceType.UNKNOWN,
            os=template['os'] if (is_up and template['os']) else None,
            os_accuracy=rng.randint(80, 95) if (is_up and template['os']) else None,
            open_ports=open_ports if is_up else [],
            is_up=is_up,
            last_seen=datetime.now(),
        )

    async def scan_network(
        self,
        target: str,
        scan_type: ScanType = ScanType.QUICK,
        port_range: Optional[str] = None,
        scan_id: Optional[str] = None,
    ) -> ScanResult:
        """
        Generate fake network scan results.

        This method simulates a network scan by generating realistic fake devices
        based on the target IP range. Results are deterministic - the same target
        will always produce the same devices.

        Args:
            target: Target IP range in CIDR notation (e.g., "192.168.1.0/24")
            scan_type: Type of scan (affects device count)
            port_range: Port range to scan (ignored for fake data)
            scan_id: Optional scan ID to use (if not provided, generates one)

        Returns:
            ScanResult with generated fake devices
        """
        # Parse network and generate seed
        network, hosts = self._parse_network(target)
        seed = self._generate_seed(target)
        rng = random.Random(seed)

        # Determine number of devices (3-15 for home, 5-20 for enterprise)
        network_addr = str(network.network_address)
        if network_addr.startswith('10.'):
            min_devices, max_devices = 5, 20
        elif network_addr.startswith('192.168.'):
            min_devices, max_devices = 3, 15
        else:
            min_devices, max_devices = 4, 18

        device_count = rng.randint(min_devices, max_devices)

        # Select random host IPs
        selected_ips = rng.sample(hosts, min(device_count, len(hosts)))

        # Determine device types
        device_types = self._select_device_types(rng, network, device_count)

        # Generate devices
        devices = []
        for i, (ip, device_type) in enumerate(zip(selected_ips, device_types), 1):
            device = self._generate_device(rng, ip, device_type, i)
            devices.append(device)

        # Simulate scan progress with realistic timing
        await self._simulate_scan_progress(device_count)

        # Use provided scan_id or generate one based on seed
        result_scan_id = scan_id if scan_id else f"fake-scan-{seed}"

        # Create scan result
        return ScanResult(
            scan_id=result_scan_id,
            target_range=target,
            scan_type=scan_type,
            status=ScanStatus.COMPLETED,
            started_at=datetime.now() - timedelta(seconds=2),
            completed_at=datetime.now(),
            progress=100.0,
            scanned_hosts=len(selected_ips),
            total_hosts=len(hosts),
            devices=devices,
        )

    async def _simulate_scan_progress(self, device_count: int) -> None:
        """
        Simulate scan progress with realistic timing.

        Creates a brief delay to make the fake scan feel more realistic,
        with timing proportional to the number of devices being "scanned".

        Args:
            device_count: Number of devices being scanned
        """
        # Base delay + per-device delay
        delay = 0.5 + (device_count * 0.05)
        await asyncio.sleep(min(delay, 3.0))  # Cap at 3 seconds

    async def discover_hosts(self, target: str) -> list[str]:
        """
        Perform host discovery without port scanning.

        This is a fast operation that only checks which hosts respond to
        ping or other discovery probes. For fake data, this generates a
        list of IPs without full device information.

        Args:
            target: Network range to scan (e.g., "192.168.1.0/24")

        Returns:
            List of IP addresses that responded to probes
        """
        # Parse network and generate seed
        network, hosts = self._parse_network(target)
        seed = self._generate_seed(target)
        rng = random.Random(seed)

        # Determine number of devices (same logic as scan_network)
        network_addr = str(network.network_address)
        if network_addr.startswith('10.'):
            min_devices, max_devices = 5, 20
        elif network_addr.startswith('192.168.'):
            min_devices, max_devices = 3, 15
        else:
            min_devices, max_devices = 4, 18

        device_count = rng.randint(min_devices, max_devices)

        # Select random host IPs
        selected_ips = rng.sample(hosts, min(device_count, len(hosts)))

        # Simulate some devices being down (10% chance)
        up_ips = [str(ip) for ip in selected_ips if rng.random() > 0.1]

        # Brief delay to simulate discovery
        await asyncio.sleep(0.3)

        return up_ips

    async def get_scan_progress(self, scan_id: str) -> float:
        """
        Get the current progress of a running scan.

        For fake scans, since they complete nearly instantly, this will
        always return 100.0. This is acceptable for training mode.

        Args:
            scan_id: Unique identifier of the scan

        Returns:
            Progress percentage (0.0 to 100.0)
        """
        # Fake scans complete immediately, so always return 100%
        return 100.0

    async def cancel_scan(self, scan_id: str) -> bool:
        """
        Cancel a running scan.

        For fake scans, cancellation is not supported since scans complete
        immediately. This always returns False indicating the scan cannot
        be cancelled (likely already complete).

        Args:
            scan_id: Unique identifier of the scan to cancel

        Returns:
            False (fake scans cannot be cancelled as they complete immediately)
        """
        # Fake scans complete immediately, cancellation not supported
        return False

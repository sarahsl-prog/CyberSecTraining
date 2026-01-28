"""
Device fingerprinting module.

This module provides functionality to identify device types, manufacturers,
and operating systems based on scan results. It uses MAC address lookup,
open port analysis, and service banners to make educated guesses about devices.
"""

from enum import Enum
from typing import Optional

from app.core.logging import get_logger
from app.services.scanner.base import DeviceInfo, PortInfo

logger = get_logger("scanner")


class DeviceType(str, Enum):
    """
    Categories of network devices.

    These categories help users understand what kind of device
    they're looking at and what vulnerabilities might be relevant.
    """
    ROUTER = "router"
    SWITCH = "switch"
    ACCESS_POINT = "access_point"
    FIREWALL = "firewall"
    SERVER = "server"
    WORKSTATION = "workstation"
    LAPTOP = "laptop"
    PRINTER = "printer"
    CAMERA = "camera"
    IOT = "iot"
    SMART_TV = "smart_tv"
    GAME_CONSOLE = "game_console"
    MOBILE = "mobile"
    NAS = "nas"
    UNKNOWN = "unknown"


# Port-to-service mappings for common identification
PORT_SERVICE_MAP = {
    21: "ftp",
    22: "ssh",
    23: "telnet",
    25: "smtp",
    53: "dns",
    67: "dhcp",
    68: "dhcp",
    80: "http",
    110: "pop3",
    123: "ntp",
    137: "netbios",
    138: "netbios",
    139: "netbios",
    143: "imap",
    161: "snmp",
    443: "https",
    445: "smb",
    515: "lpd",  # Printer
    548: "afp",  # Apple File Protocol
    554: "rtsp",  # Streaming
    631: "ipp",  # Internet Printing Protocol
    1883: "mqtt",  # IoT
    3306: "mysql",
    3389: "rdp",
    5000: "upnp",
    5353: "mdns",
    5432: "postgresql",
    5900: "vnc",
    6379: "redis",
    8080: "http-proxy",
    8443: "https-alt",
    8883: "mqtt-ssl",
    9100: "jetdirect",  # Printer
    27017: "mongodb",
}

# Device type signatures based on open ports
DEVICE_SIGNATURES = {
    # Routers typically have these ports
    "router": {
        "required_any": [80, 443, 8080],
        "common": [23, 53, 67, 161, 5000],
        "mac_prefixes": ["00:1A:2B", "00:90:4C"],  # Common router manufacturers
    },
    # Printers
    "printer": {
        "required_any": [515, 631, 9100],
        "common": [80, 443],
        "services": ["lpd", "ipp", "jetdirect"],
    },
    # Cameras
    "camera": {
        "required_any": [554, 8554],
        "common": [80, 443, 8080],
        "services": ["rtsp"],
    },
    # NAS devices
    "nas": {
        "required_any": [139, 445, 548],
        "common": [21, 22, 80, 443, 5000, 5001],
        "services": ["smb", "afp", "ftp"],
    },
    # IoT devices (generic)
    "iot": {
        "required_any": [1883, 8883, 5683],
        "common": [80, 443],
        "services": ["mqtt", "coap"],
    },
}

# MAC address prefixes for manufacturer identification
# First 3 bytes (6 hex chars) of MAC address identify manufacturer
MAC_VENDOR_PREFIXES = {
    # Apple
    "00:03:93": "Apple",
    "00:05:02": "Apple",
    "00:0A:27": "Apple",
    "00:0A:95": "Apple",
    "00:0D:93": "Apple",
    "00:11:24": "Apple",
    "00:14:51": "Apple",
    "00:16:CB": "Apple",
    "00:17:F2": "Apple",
    "00:19:E3": "Apple",
    "00:1B:63": "Apple",
    "00:1C:B3": "Apple",
    "00:1D:4F": "Apple",
    "00:1E:52": "Apple",
    "00:1E:C2": "Apple",
    "00:1F:5B": "Apple",
    "00:1F:F3": "Apple",
    "00:21:E9": "Apple",
    "00:22:41": "Apple",
    "00:23:12": "Apple",
    "00:23:32": "Apple",
    "00:23:6C": "Apple",
    "00:23:DF": "Apple",
    "00:24:36": "Apple",
    "00:25:00": "Apple",
    "00:25:4B": "Apple",
    "00:25:BC": "Apple",
    "00:26:08": "Apple",
    "00:26:4A": "Apple",
    "00:26:B0": "Apple",
    "00:26:BB": "Apple",
    # Samsung
    "00:00:F0": "Samsung",
    "00:02:78": "Samsung",
    "00:07:AB": "Samsung",
    "00:09:18": "Samsung",
    "00:0D:AE": "Samsung",
    "00:12:47": "Samsung",
    "00:12:FB": "Samsung",
    "00:13:77": "Samsung",
    "00:15:99": "Samsung",
    "00:15:B9": "Samsung",
    "00:16:32": "Samsung",
    "00:16:6B": "Samsung",
    "00:16:6C": "Samsung",
    "00:16:DB": "Samsung",
    "00:17:C9": "Samsung",
    "00:17:D5": "Samsung",
    "00:18:AF": "Samsung",
    # Google/Nest
    "54:60:09": "Google",
    "F4:F5:D8": "Google",
    "18:D6:C7": "Google Nest",
    "64:16:66": "Google Nest",
    # Amazon
    "00:FC:8B": "Amazon",
    "0C:47:C9": "Amazon",
    "34:D2:70": "Amazon",
    "40:B4:CD": "Amazon",
    "44:65:0D": "Amazon",
    "50:DC:E7": "Amazon",
    "68:37:E9": "Amazon",
    "68:54:FD": "Amazon",
    "74:C2:46": "Amazon",
    "84:D6:D0": "Amazon",
    "A0:02:DC": "Amazon",
    # Cisco/Linksys
    "00:00:0C": "Cisco",
    "00:01:42": "Cisco",
    "00:01:43": "Cisco",
    "00:01:63": "Cisco",
    "00:01:64": "Cisco",
    "00:01:96": "Cisco",
    "00:01:97": "Cisco",
    "00:01:C7": "Cisco",
    "00:01:C9": "Cisco",
    "00:02:16": "Cisco",
    "00:0C:41": "Linksys",
    "00:12:17": "Linksys",
    "00:14:BF": "Linksys",
    "00:16:B6": "Linksys",
    "00:18:39": "Linksys",
    "00:18:F8": "Linksys",
    "00:1A:70": "Linksys",
    "00:1C:10": "Linksys",
    "00:1D:7E": "Linksys",
    "00:1E:E5": "Linksys",
    # Netgear
    "00:09:5B": "Netgear",
    "00:0F:B5": "Netgear",
    "00:14:6C": "Netgear",
    "00:18:4D": "Netgear",
    "00:1B:2F": "Netgear",
    "00:1E:2A": "Netgear",
    "00:1F:33": "Netgear",
    "00:22:3F": "Netgear",
    "00:24:B2": "Netgear",
    "00:26:F2": "Netgear",
    # TP-Link
    "00:1D:0F": "TP-Link",
    "00:23:CD": "TP-Link",
    "00:27:19": "TP-Link",
    "14:CC:20": "TP-Link",
    "14:CF:92": "TP-Link",
    "18:A6:F7": "TP-Link",
    "1C:3B:F3": "TP-Link",
    "30:B5:C2": "TP-Link",
    "50:C7:BF": "TP-Link",
    "54:C8:0F": "TP-Link",
    # ASUS
    "00:0C:6E": "ASUS",
    "00:0E:A6": "ASUS",
    "00:11:2F": "ASUS",
    "00:13:D4": "ASUS",
    "00:15:F2": "ASUS",
    "00:17:31": "ASUS",
    "00:18:F3": "ASUS",
    "00:1A:92": "ASUS",
    "00:1B:FC": "ASUS",
    "00:1D:60": "ASUS",
    # Dell
    "00:06:5B": "Dell",
    "00:08:74": "Dell",
    "00:0B:DB": "Dell",
    "00:0D:56": "Dell",
    "00:0F:1F": "Dell",
    "00:11:43": "Dell",
    "00:12:3F": "Dell",
    "00:13:72": "Dell",
    "00:14:22": "Dell",
    "00:15:C5": "Dell",
    # HP
    "00:01:E6": "HP",
    "00:01:E7": "HP",
    "00:02:A5": "HP",
    "00:04:EA": "HP",
    "00:08:02": "HP",
    "00:08:83": "HP",
    "00:0A:57": "HP",
    "00:0B:CD": "HP",
    "00:0D:9D": "HP",
    "00:0E:7F": "HP",
    "00:0E:B3": "HP",
    "00:0F:20": "HP",
    "00:0F:61": "HP",
    "00:10:83": "HP",
    "00:10:E3": "HP",
    "00:11:0A": "HP",
    "00:11:85": "HP",
    "00:12:79": "HP",
    "00:13:21": "HP",
    "00:14:38": "HP",
    "00:14:C2": "HP",
    "00:15:60": "HP",
    # Intel
    "00:02:B3": "Intel",
    "00:03:47": "Intel",
    "00:04:23": "Intel",
    "00:07:E9": "Intel",
    "00:0C:F1": "Intel",
    "00:0E:0C": "Intel",
    "00:0E:35": "Intel",
    "00:11:11": "Intel",
    "00:12:F0": "Intel",
    "00:13:02": "Intel",
    "00:13:20": "Intel",
    "00:13:CE": "Intel",
    "00:13:E8": "Intel",
    "00:15:00": "Intel",
    "00:15:17": "Intel",
    "00:16:6F": "Intel",
    "00:16:76": "Intel",
    "00:16:EA": "Intel",
    "00:16:EB": "Intel",
    "00:17:35": "Intel",
    # Raspberry Pi Foundation
    "B8:27:EB": "Raspberry Pi",
    "DC:A6:32": "Raspberry Pi",
    "E4:5F:01": "Raspberry Pi",
    # Microsoft
    "00:03:FF": "Microsoft",
    "00:0D:3A": "Microsoft",
    "00:12:5A": "Microsoft",
    "00:15:5D": "Microsoft",
    "00:17:FA": "Microsoft",
    "00:1D:D8": "Microsoft",
    "00:22:48": "Microsoft",
    "00:25:AE": "Microsoft",
    "28:18:78": "Microsoft",
    "30:59:B7": "Microsoft",
}


class DeviceFingerprinter:
    """
    Identifies device types based on scan results.

    This class analyzes open ports, MAC addresses, and service banners
    to determine the type of device and its manufacturer.

    Example:
        >>> fingerprinter = DeviceFingerprinter()
        >>> device = DeviceInfo(ip="192.168.1.1", mac="00:1A:70:XX:XX:XX")
        >>> device.open_ports = [PortInfo(80), PortInfo(443), PortInfo(53)]
        >>> fingerprinter.identify_device(device)
        >>> print(device.device_type)  # "router"
        >>> print(device.vendor)  # "Linksys"
    """

    def __init__(self):
        """Initialize the device fingerprinter."""
        self._mac_lookup = None
        logger.debug("DeviceFingerprinter initialized")

    def _get_mac_lookup(self):
        """
        Lazy-load the MAC vendor lookup library.

        Returns:
            MacLookup instance or None if not available
        """
        if self._mac_lookup is None:
            try:
                from mac_vendor_lookup import MacLookup
                self._mac_lookup = MacLookup()
                # Try to update the database (might fail if offline)
                try:
                    self._mac_lookup.update_vendors()
                except Exception:
                    logger.debug("Could not update MAC vendor database")
            except ImportError:
                logger.warning("mac_vendor_lookup not installed")
                self._mac_lookup = False

        return self._mac_lookup if self._mac_lookup else None

    def identify_device(self, device: DeviceInfo) -> DeviceInfo:
        """
        Identify the type and manufacturer of a device.

        This method modifies the device in place, setting:
        - device_type: Category of device
        - vendor: Manufacturer name

        Args:
            device: DeviceInfo object to identify

        Returns:
            The same DeviceInfo object with updated fields
        """
        logger.debug(f"Identifying device: {device.ip}")

        # Identify vendor from MAC address
        if device.mac:
            device.vendor = self._identify_vendor(device.mac)

        # Identify device type from ports and services
        device.device_type = self._identify_type(device)

        logger.info(
            f"Device {device.ip} identified as {device.device_type} "
            f"(vendor: {device.vendor or 'unknown'})"
        )

        return device

    def _identify_vendor(self, mac: str) -> Optional[str]:
        """
        Identify device vendor from MAC address.

        Args:
            mac: MAC address (e.g., "00:1A:70:XX:XX:XX")

        Returns:
            Vendor name or None if not found
        """
        if not mac:
            return None

        # Normalize MAC address format
        mac_normalized = mac.upper().replace("-", ":").replace(".", ":")

        # Check our built-in prefix list first (faster)
        mac_prefix = mac_normalized[:8]
        if mac_prefix in MAC_VENDOR_PREFIXES:
            return MAC_VENDOR_PREFIXES[mac_prefix]

        # Try the mac-vendor-lookup library
        mac_lookup = self._get_mac_lookup()
        if mac_lookup:
            try:
                vendor = mac_lookup.lookup(mac_normalized)
                return vendor
            except Exception as e:
                logger.debug(f"MAC lookup failed for {mac}: {e}")

        return None

    def _identify_type(self, device: DeviceInfo) -> str:
        """
        Identify device type from open ports and services.

        Args:
            device: DeviceInfo with open ports

        Returns:
            DeviceType string
        """
        if not device.open_ports:
            return DeviceType.UNKNOWN

        open_port_numbers = {p.port for p in device.open_ports}
        services = {p.service for p in device.open_ports if p.service}

        # Check for printer
        if self._matches_signature("printer", open_port_numbers, services):
            return DeviceType.PRINTER

        # Check for camera
        if self._matches_signature("camera", open_port_numbers, services):
            return DeviceType.CAMERA

        # Check for workstation/desktop (before NAS, as workstations may have SMB)
        # RDP or VNC are strong indicators of a workstation, not NAS
        if 3389 in open_port_numbers or 5900 in open_port_numbers:
            return DeviceType.WORKSTATION

        # Check for NAS (file servers without remote desktop)
        if self._matches_signature("nas", open_port_numbers, services):
            return DeviceType.NAS

        # Additional workstation check for Windows file sharing without NAS indicators
        workstation_ports = {135, 139, 445}
        if open_port_numbers & workstation_ports:
            # If it has Windows-specific NetBIOS ports without other server services, it's likely a workstation
            if 135 in open_port_numbers:
                return DeviceType.WORKSTATION

        # Check for IoT
        if self._matches_signature("iot", open_port_numbers, services):
            return DeviceType.IOT

        # Check for router (common gateway device)
        if device.ip.endswith(".1") or device.ip.endswith(".254"):
            if 80 in open_port_numbers or 443 in open_port_numbers:
                return DeviceType.ROUTER

        # Check for server-like devices
        server_ports = {21, 22, 25, 53, 80, 110, 143, 443, 993, 995}
        if len(open_port_numbers & server_ports) >= 3:
            return DeviceType.SERVER

        # Fallback workstation check (any SMB without other indicators)
        if open_port_numbers & workstation_ports:
            return DeviceType.WORKSTATION

        # Default based on port count
        if len(open_port_numbers) > 5:
            return DeviceType.SERVER
        elif len(open_port_numbers) > 0:
            return DeviceType.WORKSTATION

        return DeviceType.UNKNOWN

    def _matches_signature(
        self,
        device_type: str,
        open_ports: set[int],
        services: set[str],
    ) -> bool:
        """
        Check if open ports match a device signature.

        Args:
            device_type: Type to check against
            open_ports: Set of open port numbers
            services: Set of detected service names

        Returns:
            True if the signature matches
        """
        signature = DEVICE_SIGNATURES.get(device_type, {})

        # Check required ports (must have at least one)
        required_any = signature.get("required_any", [])
        if required_any and not (open_ports & set(required_any)):
            return False

        # Check for service names
        sig_services = signature.get("services", [])
        if sig_services and (services & set(sig_services)):
            return True

        # If we have required ports, that's enough
        if required_any and (open_ports & set(required_any)):
            return True

        return False

    def get_service_name(self, port: int) -> Optional[str]:
        """
        Get the common service name for a port.

        Args:
            port: Port number

        Returns:
            Service name or None if unknown
        """
        return PORT_SERVICE_MAP.get(port)

    def enrich_ports(self, device: DeviceInfo) -> DeviceInfo:
        """
        Add service names to ports that don't have them.

        Args:
            device: DeviceInfo with open ports

        Returns:
            The same device with enriched port information
        """
        for port in device.open_ports:
            if not port.service:
                port.service = self.get_service_name(port.port)

        return device

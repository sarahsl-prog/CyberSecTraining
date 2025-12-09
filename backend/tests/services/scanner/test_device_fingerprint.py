"""
Tests for the device fingerprinting module.

These tests verify that:
- Device types are correctly identified from open ports
- MAC addresses are correctly mapped to vendors
- Service names are properly enriched
"""

import pytest
from app.services.scanner.device_fingerprint import (
    DeviceFingerprinter,
    DeviceType,
    PORT_SERVICE_MAP,
    MAC_VENDOR_PREFIXES,
)
from app.services.scanner.base import DeviceInfo, PortInfo


class TestDeviceFingerprinter:
    """Tests for the DeviceFingerprinter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.fingerprinter = DeviceFingerprinter()

    # =========================================================================
    # Service Name Tests
    # =========================================================================

    @pytest.mark.parametrize("port,expected_service", [
        (21, "ftp"),
        (22, "ssh"),
        (23, "telnet"),
        (80, "http"),
        (443, "https"),
        (445, "smb"),
        (3306, "mysql"),
        (3389, "rdp"),
        (5432, "postgresql"),
        (27017, "mongodb"),
    ])
    def test_get_service_name(self, port: int, expected_service: str):
        """Test service name lookup for common ports."""
        service = self.fingerprinter.get_service_name(port)
        assert service == expected_service

    def test_get_service_name_unknown_port(self):
        """Test that unknown ports return None."""
        # Port 12345 is unlikely to be in our map
        assert self.fingerprinter.get_service_name(12345) is None

    # =========================================================================
    # Vendor Identification Tests
    # =========================================================================

    @pytest.mark.parametrize("mac,expected_vendor", [
        ("00:1A:70:XX:XX:XX", "Linksys"),
        ("00:23:CD:XX:XX:XX", "TP-Link"),
        ("00:14:6C:XX:XX:XX", "Netgear"),
        ("00:18:F3:XX:XX:XX", "ASUS"),
        ("00:15:C5:XX:XX:XX", "Dell"),
        ("00:14:C2:XX:XX:XX", "HP"),
        ("B8:27:EB:XX:XX:XX", "Raspberry Pi"),
    ])
    def test_identify_vendor_from_prefix(self, mac: str, expected_vendor: str):
        """Test vendor identification from MAC prefix."""
        # Replace XX with valid hex chars
        mac = mac.replace("XX", "00")
        vendor = self.fingerprinter._identify_vendor(mac)
        assert vendor == expected_vendor

    def test_identify_vendor_none_mac(self):
        """Test that None MAC returns None vendor."""
        assert self.fingerprinter._identify_vendor(None) is None

    def test_identify_vendor_unknown_mac(self):
        """Test that unknown MAC prefix returns None (or library result)."""
        # This MAC prefix is not in our list
        result = self.fingerprinter._identify_vendor("AA:BB:CC:DD:EE:FF")
        # Could be None or from the mac-vendor-lookup library
        assert result is None or isinstance(result, str)

    # =========================================================================
    # Device Type Identification Tests
    # =========================================================================

    def test_identify_router(self):
        """Test router identification by ports and IP pattern."""
        device = DeviceInfo(
            ip="192.168.1.1",  # Common router IP
            open_ports=[
                PortInfo(port=80, service="http"),
                PortInfo(port=443, service="https"),
                PortInfo(port=53, service="dns"),
            ],
        )

        self.fingerprinter.identify_device(device)
        assert device.device_type == DeviceType.ROUTER

    def test_identify_printer(self):
        """Test printer identification by ports."""
        device = DeviceInfo(
            ip="192.168.1.50",
            open_ports=[
                PortInfo(port=9100, service="jetdirect"),
                PortInfo(port=631, service="ipp"),
                PortInfo(port=80, service="http"),
            ],
        )

        self.fingerprinter.identify_device(device)
        assert device.device_type == DeviceType.PRINTER

    def test_identify_nas(self):
        """Test NAS identification by ports."""
        device = DeviceInfo(
            ip="192.168.1.10",
            open_ports=[
                PortInfo(port=445, service="smb"),
                PortInfo(port=139, service="netbios"),
                PortInfo(port=22, service="ssh"),
                PortInfo(port=80, service="http"),
            ],
        )

        self.fingerprinter.identify_device(device)
        assert device.device_type == DeviceType.NAS

    def test_identify_camera(self):
        """Test camera identification by RTSP port."""
        device = DeviceInfo(
            ip="192.168.1.20",
            open_ports=[
                PortInfo(port=554, service="rtsp"),
                PortInfo(port=80, service="http"),
            ],
        )

        self.fingerprinter.identify_device(device)
        assert device.device_type == DeviceType.CAMERA

    def test_identify_iot(self):
        """Test IoT device identification by MQTT port."""
        device = DeviceInfo(
            ip="192.168.1.30",
            open_ports=[
                PortInfo(port=1883, service="mqtt"),
                PortInfo(port=80, service="http"),
            ],
        )

        self.fingerprinter.identify_device(device)
        assert device.device_type == DeviceType.IOT

    def test_identify_server(self):
        """Test server identification by multiple service ports."""
        device = DeviceInfo(
            ip="192.168.1.100",
            open_ports=[
                PortInfo(port=22, service="ssh"),
                PortInfo(port=80, service="http"),
                PortInfo(port=443, service="https"),
                PortInfo(port=3306, service="mysql"),
                PortInfo(port=25, service="smtp"),
            ],
        )

        self.fingerprinter.identify_device(device)
        assert device.device_type == DeviceType.SERVER

    def test_identify_workstation(self):
        """Test workstation identification by Windows ports."""
        device = DeviceInfo(
            ip="192.168.1.200",
            open_ports=[
                PortInfo(port=445, service="smb"),
                PortInfo(port=3389, service="rdp"),
            ],
        )

        self.fingerprinter.identify_device(device)
        assert device.device_type == DeviceType.WORKSTATION

    def test_identify_unknown_no_ports(self):
        """Test that device with no ports is unknown."""
        device = DeviceInfo(ip="192.168.1.50", open_ports=[])

        self.fingerprinter.identify_device(device)
        assert device.device_type == DeviceType.UNKNOWN

    # =========================================================================
    # Port Enrichment Tests
    # =========================================================================

    def test_enrich_ports_adds_service_names(self):
        """Test that port enrichment adds missing service names."""
        device = DeviceInfo(
            ip="192.168.1.1",
            open_ports=[
                PortInfo(port=22, service=None),  # No service name
                PortInfo(port=80, service=None),
                PortInfo(port=443, service="https"),  # Already has name
            ],
        )

        self.fingerprinter.enrich_ports(device)

        assert device.open_ports[0].service == "ssh"
        assert device.open_ports[1].service == "http"
        assert device.open_ports[2].service == "https"

    # =========================================================================
    # Full Identification Tests
    # =========================================================================

    def test_identify_device_sets_vendor_and_type(self):
        """Test that identify_device sets both vendor and type."""
        device = DeviceInfo(
            ip="192.168.1.1",
            mac="00:1A:70:00:00:00",  # Linksys prefix
            open_ports=[
                PortInfo(port=80, service="http"),
                PortInfo(port=443, service="https"),
            ],
        )

        result = self.fingerprinter.identify_device(device)

        assert result is device  # Same object returned
        assert device.vendor == "Linksys"
        assert device.device_type == DeviceType.ROUTER


class TestPortServiceMap:
    """Tests for the PORT_SERVICE_MAP constant."""

    def test_common_ports_present(self):
        """Test that common ports are in the map."""
        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389]

        for port in common_ports:
            assert port in PORT_SERVICE_MAP, f"Port {port} should be in map"

    def test_all_services_are_strings(self):
        """Test that all service values are strings."""
        for port, service in PORT_SERVICE_MAP.items():
            assert isinstance(port, int)
            assert isinstance(service, str)
            assert len(service) > 0


class TestMacVendorPrefixes:
    """Tests for the MAC_VENDOR_PREFIXES constant."""

    def test_major_vendors_present(self):
        """Test that major vendors are represented."""
        vendors = set(MAC_VENDOR_PREFIXES.values())

        expected_vendors = [
            "Apple", "Samsung", "Cisco", "Linksys", "Netgear",
            "TP-Link", "ASUS", "Dell", "HP", "Intel", "Raspberry Pi",
        ]

        for vendor in expected_vendors:
            assert vendor in vendors, f"Vendor {vendor} should be in prefixes"

    def test_prefix_format(self):
        """Test that all prefixes are in correct format."""
        for prefix, vendor in MAC_VENDOR_PREFIXES.items():
            # Should be in format XX:XX:XX
            assert len(prefix) == 8, f"Prefix {prefix} should be 8 chars"
            assert prefix[2] == ":" and prefix[5] == ":"
            assert isinstance(vendor, str)

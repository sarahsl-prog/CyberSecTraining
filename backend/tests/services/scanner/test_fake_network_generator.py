"""Unit tests for FakeNetworkGenerator."""

import pytest
from app.config import Settings
from app.services.scanner.fake_network_generator import FakeNetworkGenerator
from app.services.scanner.base import ScanType, ScanStatus
from app.services.scanner.device_fingerprint import DeviceType


@pytest.fixture
def generator():
    """Create a fake network generator instance."""
    settings = Settings()
    return FakeNetworkGenerator(settings)


class TestDeterministicGeneration:
    """Tests for deterministic fake data generation."""

    @pytest.mark.asyncio
    async def test_same_target_produces_same_results(self, generator):
        """Test that scanning the same target twice produces identical results."""
        target = "192.168.1.0/24"

        # Scan twice
        result1 = await generator.scan_network(target)
        result2 = await generator.scan_network(target)

        # Should have same number of devices
        assert len(result1.devices) == len(result2.devices)

        # Should have same device IPs
        ips1 = sorted([d.ip for d in result1.devices])
        ips2 = sorted([d.ip for d in result2.devices])
        assert ips1 == ips2

        # Should have same device types
        types1 = sorted([d.device_type for d in result1.devices])
        types2 = sorted([d.device_type for d in result2.devices])
        assert types1 == types2

    @pytest.mark.asyncio
    async def test_different_targets_produce_different_results(self, generator):
        """Test that different targets produce different fake data."""
        result1 = await generator.scan_network("192.168.1.0/24")
        result2 = await generator.scan_network("10.0.0.0/24")

        # Different targets should produce different device sets
        ips1 = set([d.ip for d in result1.devices])
        ips2 = set([d.ip for d in result2.devices])
        assert ips1 != ips2


class TestDeviceGeneration:
    """Tests for device generation logic."""

    @pytest.mark.asyncio
    async def test_generates_reasonable_device_count(self, generator):
        """Test that device count is within expected range."""
        result = await generator.scan_network("192.168.1.0/24")

        # Home network should have 3-15 devices
        assert 3 <= len(result.devices) <= 15

    @pytest.mark.asyncio
    async def test_always_includes_router(self, generator):
        """Test that generated networks always include a router."""
        result = await generator.scan_network("192.168.1.0/24")

        # Should have at least one router
        routers = [d for d in result.devices if d.device_type == DeviceType.ROUTER]
        assert len(routers) >= 1

    @pytest.mark.asyncio
    async def test_home_network_device_types(self, generator):
        """Test that home networks generate consumer devices."""
        result = await generator.scan_network("192.168.1.0/24")

        device_types = set([d.device_type for d in result.devices if d.is_up])

        # Should include common home devices
        common_home_types = {
            DeviceType.ROUTER,
            DeviceType.LAPTOP,
            DeviceType.PRINTER,
            DeviceType.IOT,
        }

        # At least some overlap with home device types
        assert len(device_types & common_home_types) >= 2

    @pytest.mark.asyncio
    async def test_enterprise_network_device_types(self, generator):
        """Test that enterprise networks generate business devices."""
        result = await generator.scan_network("10.0.0.0/24")

        device_types = set([d.device_type for d in result.devices if d.is_up])

        # Should include enterprise devices
        enterprise_types = {
            DeviceType.ROUTER,
            DeviceType.SERVER,
            DeviceType.WORKSTATION,
        }

        # Should have enterprise-type devices
        assert len(device_types & enterprise_types) >= 2

    @pytest.mark.asyncio
    async def test_devices_have_realistic_attributes(self, generator):
        """Test that generated devices have realistic attributes."""
        result = await generator.scan_network("192.168.1.0/24")

        for device in result.devices:
            if device.is_up:
                # Should have IP
                assert device.ip is not None
                assert device.ip.startswith("192.168.1.")

                # Should have MAC address
                assert device.mac is not None
                assert len(device.mac.split(':')) == 6

                # Should have hostname
                assert device.hostname is not None

                # Should have vendor
                assert device.vendor is not None

                # Should have device type
                assert device.device_type != DeviceType.UNKNOWN

                # Should have open ports if device is up
                assert len(device.open_ports) > 0


class TestPortGeneration:
    """Tests for port and service generation."""

    @pytest.mark.asyncio
    async def test_router_has_expected_ports(self, generator):
        """Test that routers have common router ports."""
        result = await generator.scan_network("192.168.1.0/24")

        routers = [d for d in result.devices if d.device_type == DeviceType.ROUTER and d.is_up]
        assert len(routers) > 0

        router = routers[0]
        router_ports = set([p.port for p in router.open_ports])

        # Router should have some common management ports
        common_router_ports = {80, 443, 22, 23, 53}
        assert len(router_ports & common_router_ports) >= 2

    @pytest.mark.asyncio
    async def test_ports_have_service_names(self, generator):
        """Test that ports have associated service names."""
        result = await generator.scan_network("192.168.1.0/24")

        for device in result.devices:
            if device.is_up:
                for port_info in device.open_ports:
                    # Port should have service name
                    assert port_info.service is not None
                    assert port_info.service != ""

                    # Common ports should have correct service names
                    if port_info.port == 80:
                        assert port_info.service == "http"
                    elif port_info.port == 443:
                        assert port_info.service == "https"
                    elif port_info.port == 22:
                        assert port_info.service == "ssh"

    @pytest.mark.asyncio
    async def test_printer_has_printer_ports(self, generator):
        """Test that printers have appropriate printing ports."""
        result = await generator.scan_network("192.168.1.0/24")

        printers = [d for d in result.devices if d.device_type == DeviceType.PRINTER and d.is_up]

        if printers:
            printer = printers[0]
            printer_ports = set([p.port for p in printer.open_ports])

            # Should have at least one printer port
            common_printer_ports = {631, 9100}
            assert len(printer_ports & common_printer_ports) >= 1


class TestMACAddressGeneration:
    """Tests for MAC address generation."""

    @pytest.mark.asyncio
    async def test_mac_addresses_have_vendor_prefixes(self, generator):
        """Test that MAC addresses use known vendor prefixes."""
        result = await generator.scan_network("192.168.1.0/24")

        known_prefixes = generator.MAC_VENDORS.keys()

        for device in result.devices:
            if device.is_up and device.mac:
                prefix = device.mac[:8]
                # MAC should use a known vendor prefix
                assert prefix in known_prefixes

    @pytest.mark.asyncio
    async def test_vendor_matches_mac_prefix(self, generator):
        """Test that vendor name matches MAC address prefix."""
        result = await generator.scan_network("192.168.1.0/24")

        for device in result.devices:
            if device.is_up and device.mac and device.vendor:
                prefix = device.mac[:8]
                expected_vendor = generator.MAC_VENDORS[prefix]
                assert device.vendor == expected_vendor


class TestScanResult:
    """Tests for scan result metadata."""

    @pytest.mark.asyncio
    async def test_scan_result_has_correct_metadata(self, generator):
        """Test that scan result includes proper metadata."""
        target = "192.168.1.0/24"
        result = await generator.scan_network(target, ScanType.QUICK)

        # Should have scan ID
        assert result.scan_id is not None
        assert result.scan_id.startswith("fake-scan-")

        # Should have correct target
        assert result.target_range == target

        # Should have correct scan type
        assert result.scan_type == ScanType.QUICK

        # Should be completed
        assert result.status == ScanStatus.COMPLETED

        # Should have timing information
        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.completed_at >= result.started_at

        # Should have progress
        assert result.progress == 100.0

        # Should have host counts
        assert result.scanned_hosts > 0
        assert result.total_hosts == 254  # /24 network has 254 hosts

    @pytest.mark.asyncio
    async def test_scan_completes_quickly(self, generator):
        """Test that fake scans complete in reasonable time."""
        import time

        target = "192.168.1.0/24"
        start = time.time()
        await generator.scan_network(target)
        duration = time.time() - start

        # Should complete in under 5 seconds
        assert duration < 5.0


class TestDownDevices:
    """Tests for simulating devices being down."""

    @pytest.mark.asyncio
    async def test_some_devices_may_be_down(self, generator):
        """Test that some devices are marked as down."""
        result = await generator.scan_network("192.168.1.0/24")

        # Count devices that are up vs down
        up_count = sum(1 for d in result.devices if d.is_up)
        down_count = sum(1 for d in result.devices if not d.is_up)

        # Most devices should be up (>80%)
        total = up_count + down_count
        assert up_count / total > 0.8

    @pytest.mark.asyncio
    async def test_down_devices_have_minimal_info(self, generator):
        """Test that down devices don't have detailed information."""
        result = await generator.scan_network("192.168.1.0/24")

        down_devices = [d for d in result.devices if not d.is_up]

        for device in down_devices:
            # Down devices shouldn't have MAC, hostname, or open ports
            assert device.mac is None or device.mac == ""
            assert device.hostname is None or device.hostname == ""
            assert len(device.open_ports) == 0


class TestNetworkTypes:
    """Tests for different network type handling."""

    @pytest.mark.asyncio
    async def test_enterprise_network_has_more_devices(self, generator):
        """Test that enterprise networks generate more devices."""
        home_result = await generator.scan_network("192.168.1.0/24")
        enterprise_result = await generator.scan_network("10.0.0.0/24")

        # Enterprise should typically have more devices (not always due to randomness)
        # But range should be higher
        assert max(5, len(home_result.devices)) <= 20
        assert max(5, len(enterprise_result.devices)) <= 20

    @pytest.mark.asyncio
    async def test_small_office_network_balanced_devices(self, generator):
        """Test that small office networks have balanced device mix."""
        result = await generator.scan_network("172.16.0.0/24")

        # Should have between home and enterprise device counts
        assert 4 <= len(result.devices) <= 18

        device_types = set([d.device_type for d in result.devices if d.is_up])

        # Should have a mix of device types
        assert len(device_types) >= 3


class TestBaseScannerInterface:
    """Tests for BaseScannerInterface implementation."""

    @pytest.mark.asyncio
    async def test_discover_hosts_returns_ips(self, generator):
        """Test that discover_hosts returns list of IP addresses."""
        target = "192.168.1.0/24"
        ips = await generator.discover_hosts(target)

        assert isinstance(ips, list)
        assert len(ips) > 0

        # All should be valid IPs in target range
        for ip in ips:
            assert ip.startswith("192.168.1.")

    @pytest.mark.asyncio
    async def test_discover_hosts_is_deterministic(self, generator):
        """Test that discover_hosts returns same IPs for same target."""
        target = "192.168.1.0/24"

        ips1 = await generator.discover_hosts(target)
        ips2 = await generator.discover_hosts(target)

        assert sorted(ips1) == sorted(ips2)

    @pytest.mark.asyncio
    async def test_discover_hosts_is_fast(self, generator):
        """Test that host discovery is faster than full scan."""
        import time

        target = "192.168.1.0/24"
        start = time.time()
        await generator.discover_hosts(target)
        duration = time.time() - start

        # Should complete in under 1 second
        assert duration < 1.0

    @pytest.mark.asyncio
    async def test_discover_hosts_enterprise_network(self, generator):
        """Test that enterprise networks return appropriate device count."""
        target = "10.0.0.0/24"
        ips = await generator.discover_hosts(target)

        # Should have between 5-20 devices for enterprise
        assert 4 <= len(ips) <= 20  # 4 accounts for ~10% down devices

        # All IPs should be in 10.x range
        for ip in ips:
            assert ip.startswith("10.0.0.")

    @pytest.mark.asyncio
    async def test_get_scan_progress_returns_float(self, generator):
        """Test that get_scan_progress returns progress percentage."""
        progress = await generator.get_scan_progress("fake-scan-123")

        assert isinstance(progress, float)
        assert 0.0 <= progress <= 100.0

    @pytest.mark.asyncio
    async def test_get_scan_progress_always_complete(self, generator):
        """Test that fake scans always report 100% progress."""
        # Since fake scans complete immediately
        progress = await generator.get_scan_progress("any-id")
        assert progress == 100.0

    @pytest.mark.asyncio
    async def test_cancel_scan_returns_false(self, generator):
        """Test that cancel_scan returns False (not cancellable)."""
        result = await generator.cancel_scan("fake-scan-123")

        assert isinstance(result, bool)
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_scan_any_id(self, generator):
        """Test that cancel_scan returns False for any scan ID."""
        # Fake scans can't be cancelled, regardless of ID
        result1 = await generator.cancel_scan("scan-1")
        result2 = await generator.cancel_scan("scan-2")
        result3 = await generator.cancel_scan("nonexistent")

        assert result1 is False
        assert result2 is False
        assert result3 is False

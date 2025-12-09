"""
Tests for the network validator module.

These tests verify that:
- Private networks are correctly identified
- Public networks are rejected
- Network size limits are enforced
- Invalid formats are handled properly
"""

import pytest
from app.services.scanner.network_validator import (
    NetworkValidator,
    NetworkValidationError,
    get_local_network,
    get_network_interfaces,
)


class TestNetworkValidator:
    """Tests for the NetworkValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = NetworkValidator()

    # =========================================================================
    # Private IP Detection Tests
    # =========================================================================

    @pytest.mark.parametrize("ip,expected", [
        # 10.0.0.0/8 range
        ("10.0.0.1", True),
        ("10.255.255.255", True),
        ("10.100.50.25", True),
        # 172.16.0.0/12 range
        ("172.16.0.1", True),
        ("172.31.255.255", True),
        ("172.20.100.50", True),
        # 192.168.0.0/16 range
        ("192.168.0.1", True),
        ("192.168.255.255", True),
        ("192.168.1.100", True),
        # Loopback
        ("127.0.0.1", True),
        ("127.255.255.255", True),
        # Link-local
        ("169.254.0.1", True),
        ("169.254.255.255", True),
        # Public IPs (should be False)
        ("8.8.8.8", False),
        ("1.1.1.1", False),
        ("142.250.185.46", False),  # Google
        ("172.15.0.1", False),  # Just outside private range
        ("172.32.0.1", False),  # Just outside private range
        ("192.167.1.1", False),  # Just outside private range
        ("193.168.1.1", False),  # Just outside private range
    ])
    def test_is_private_ip(self, ip: str, expected: bool):
        """Test private IP detection for various addresses."""
        result = self.validator.is_private_ip(ip)
        assert result == expected, f"Expected {ip} to be {'private' if expected else 'public'}"

    def test_is_private_ip_invalid(self):
        """Test that invalid IP addresses return False."""
        assert self.validator.is_private_ip("invalid") is False
        assert self.validator.is_private_ip("") is False
        assert self.validator.is_private_ip("256.256.256.256") is False

    # =========================================================================
    # Private Network Detection Tests
    # =========================================================================

    @pytest.mark.parametrize("network,expected", [
        # Valid private networks
        ("192.168.1.0/24", True),
        ("192.168.0.0/16", True),
        ("10.0.0.0/24", True),
        ("10.0.0.0/8", True),
        ("172.16.0.0/24", True),
        ("172.16.0.0/12", True),
        # Public networks (should be False)
        ("8.8.8.0/24", False),
        ("1.0.0.0/8", False),
        # Mixed (network includes public IPs - should be False)
        ("0.0.0.0/0", False),
    ])
    def test_is_private_network(self, network: str, expected: bool):
        """Test private network detection."""
        # Note: Some large networks will fail size check first
        # This tests the is_private_network method directly
        result = self.validator.is_private_network(network)
        assert result == expected, f"Expected {network} to be {'private' if expected else 'public'}"

    # =========================================================================
    # Validation Tests
    # =========================================================================

    def test_validate_single_private_ip(self):
        """Test validation of single private IP addresses."""
        # Should not raise
        self.validator.validate("192.168.1.1")
        self.validator.validate("10.0.0.1")
        self.validator.validate("172.16.0.1")

    def test_validate_private_network(self):
        """Test validation of private network ranges."""
        # Should not raise
        self.validator.validate("192.168.1.0/24")
        self.validator.validate("10.0.0.0/24")
        self.validator.validate("172.16.0.0/24")

    def test_validate_rejects_public_ip(self):
        """Test that public IP addresses are rejected."""
        with pytest.raises(NetworkValidationError) as exc_info:
            self.validator.validate("8.8.8.8")

        assert "private" in str(exc_info.value).lower()

    def test_validate_rejects_public_network(self):
        """Test that public network ranges are rejected."""
        with pytest.raises(NetworkValidationError) as exc_info:
            self.validator.validate("8.8.8.0/24")

        assert "private" in str(exc_info.value).lower()

    def test_validate_rejects_oversized_network(self):
        """Test that networks larger than max size are rejected."""
        validator = NetworkValidator(max_network_size=256)

        with pytest.raises(NetworkValidationError) as exc_info:
            # /16 has 65536 addresses, way over limit
            validator.validate("192.168.0.0/16")

        assert "too large" in str(exc_info.value).lower()

    def test_validate_rejects_invalid_format(self):
        """Test that invalid formats are rejected."""
        invalid_targets = [
            "not-an-ip",
            "192.168.1",  # Incomplete
            "192.168.1.256",  # Invalid octet
            "192.168.1.1/33",  # Invalid CIDR
            "",  # Empty
        ]

        for target in invalid_targets:
            with pytest.raises(NetworkValidationError):
                self.validator.validate(target)

    # =========================================================================
    # Network Info Tests
    # =========================================================================

    def test_get_network_info_single_ip(self):
        """Test getting info for a single IP."""
        info = self.validator.get_network_info("192.168.1.1")

        assert info["type"] == "single_ip"
        assert info["ip_address"] == "192.168.1.1"
        assert info["is_private"] is True
        assert info["num_hosts"] == 1

    def test_get_network_info_network(self):
        """Test getting info for a network range."""
        info = self.validator.get_network_info("192.168.1.0/24")

        assert info["type"] == "network"
        assert info["network_address"] == "192.168.1.0"
        assert info["broadcast_address"] == "192.168.1.255"
        assert info["num_addresses"] == 256
        assert info["is_private"] is True

    # =========================================================================
    # Max Size Configuration Tests
    # =========================================================================

    def test_custom_max_network_size(self):
        """Test that custom max network size is respected."""
        small_validator = NetworkValidator(max_network_size=16)

        # /28 has 16 addresses - should pass
        small_validator.validate("192.168.1.0/28")

        # /27 has 32 addresses - should fail
        with pytest.raises(NetworkValidationError):
            small_validator.validate("192.168.1.0/27")


class TestNetworkHelpers:
    """Tests for network helper functions."""

    def test_get_local_network_returns_valid_or_none(self):
        """Test that get_local_network returns valid network or None."""
        result = get_local_network()

        if result is not None:
            # Should be in CIDR notation
            assert "/" in result
            # Should be a private network
            validator = NetworkValidator(max_network_size=65536)
            assert validator.is_private_network(result)

    def test_get_network_interfaces_returns_list(self):
        """Test that get_network_interfaces returns a list."""
        result = get_network_interfaces()

        assert isinstance(result, list)

        # If we have interfaces, check structure
        for iface in result:
            assert "name" in iface
            assert "ip" in iface
            assert "netmask" in iface
            assert "network" in iface
            assert "is_private" in iface


class TestNetworkValidationError:
    """Tests for the NetworkValidationError exception."""

    def test_error_message(self):
        """Test error message is preserved."""
        error = NetworkValidationError("Test error message", network="192.168.1.0/24")

        assert str(error) == "Test error message"
        assert error.network == "192.168.1.0/24"
        assert error.message == "Test error message"

    def test_error_without_network(self):
        """Test error can be created without network parameter."""
        error = NetworkValidationError("Test error")

        assert str(error) == "Test error"
        assert error.network is None

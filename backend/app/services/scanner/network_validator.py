"""
Network validation utilities.

This module provides functions to validate network ranges and ensure that
only private networks can be scanned. This is a critical security feature
to prevent the tool from being used to scan public networks.

Private Network Ranges (RFC 1918):
- 10.0.0.0/8 (10.0.0.0 - 10.255.255.255)
- 172.16.0.0/12 (172.16.0.0 - 172.31.255.255)
- 192.168.0.0/16 (192.168.0.0 - 192.168.255.255)

Additional Private/Local Ranges:
- 127.0.0.0/8 (Loopback)
- 169.254.0.0/16 (Link-local)
"""

import ipaddress
from typing import Optional

from app.core.logging import get_logger

logger = get_logger("scanner")


class NetworkValidationError(Exception):
    """
    Exception raised when network validation fails.

    This is raised when attempting to scan a non-private network
    or when the network range is invalid.
    """

    def __init__(self, message: str, network: Optional[str] = None):
        """
        Initialize the validation error.

        Args:
            message: Human-readable error message
            network: The network string that failed validation
        """
        self.message = message
        self.network = network
        super().__init__(self.message)


class NetworkValidator:
    """
    Validates network ranges for scanning.

    This class ensures that only private networks can be scanned,
    protecting against accidental or intentional scanning of public networks.

    Example:
        >>> validator = NetworkValidator()
        >>> validator.validate("192.168.1.0/24")  # OK
        >>> validator.validate("8.8.8.8")  # Raises NetworkValidationError
    """

    # Private network ranges (RFC 1918)
    PRIVATE_NETWORKS = [
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
    ]

    # Additional allowed ranges (loopback, link-local)
    ADDITIONAL_ALLOWED = [
        ipaddress.ip_network("127.0.0.0/8"),      # Loopback
        ipaddress.ip_network("169.254.0.0/16"),   # Link-local
    ]

    # Maximum network size (prevent scanning huge ranges)
    MAX_NETWORK_SIZE = 256  # /24 equivalent

    def __init__(self, max_network_size: Optional[int] = None):
        """
        Initialize the network validator.

        Args:
            max_network_size: Maximum number of hosts allowed in a scan.
                             Defaults to 256 (/24 network).
        """
        self.max_network_size = max_network_size or self.MAX_NETWORK_SIZE
        logger.debug(f"NetworkValidator initialized with max_network_size={self.max_network_size}")

    def is_private_ip(self, ip: str) -> bool:
        """
        Check if an IP address is in a private range.

        Args:
            ip: IP address string (e.g., "192.168.1.1")

        Returns:
            True if the IP is private, False otherwise
        """
        try:
            ip_obj = ipaddress.ip_address(ip)

            # Check against private ranges
            for network in self.PRIVATE_NETWORKS + self.ADDITIONAL_ALLOWED:
                if ip_obj in network:
                    return True

            return False
        except ValueError:
            logger.warning(f"Invalid IP address: {ip}")
            return False

    def is_private_network(self, network: str) -> bool:
        """
        Check if a network range is entirely within private ranges.

        Args:
            network: Network in CIDR notation (e.g., "192.168.1.0/24")

        Returns:
            True if the entire network is private, False otherwise
        """
        try:
            net = ipaddress.ip_network(network, strict=False)

            # Check if the network is a subnet of any private range
            for private_net in self.PRIVATE_NETWORKS + self.ADDITIONAL_ALLOWED:
                if self._is_subnet_of(net, private_net):
                    return True

            # Also check individual IPs if it's a small range
            if net.num_addresses <= self.max_network_size:
                return all(self.is_private_ip(str(ip)) for ip in net.hosts())

            return False
        except ValueError:
            logger.warning(f"Invalid network: {network}")
            return False

    def _is_subnet_of(
        self,
        subnet: ipaddress.IPv4Network | ipaddress.IPv6Network,
        supernet: ipaddress.IPv4Network | ipaddress.IPv6Network,
    ) -> bool:
        """
        Check if one network is a subnet of another.

        Args:
            subnet: The potential subnet
            supernet: The potential supernet

        Returns:
            True if subnet is contained within supernet
        """
        try:
            # Check if subnet's network address is in supernet
            # and subnet's broadcast address is in supernet
            return (
                subnet.network_address >= supernet.network_address
                and subnet.broadcast_address <= supernet.broadcast_address
            )
        except TypeError:
            # Different IP versions
            return False

    def validate(self, target: str) -> ipaddress.IPv4Network | ipaddress.IPv4Address:
        """
        Validate a network target for scanning.

        This method performs comprehensive validation:
        1. Parses the target as an IP or network
        2. Checks if it's in a private range
        3. Verifies the network size is within limits

        Args:
            target: IP address or network range (e.g., "192.168.1.1" or "192.168.1.0/24")

        Returns:
            Parsed IP address or network object

        Raises:
            NetworkValidationError: If validation fails
        """
        logger.info(f"Validating network target: {target}")

        # Try to parse as a network first
        try:
            # Check if it's a CIDR notation
            if "/" in target:
                network = ipaddress.ip_network(target, strict=False)
                return self._validate_network(network, target)
            else:
                # Single IP address
                ip = ipaddress.ip_address(target)
                return self._validate_ip(ip, target)

        except ValueError as e:
            logger.error(f"Invalid target format: {target} - {e}")
            raise NetworkValidationError(
                f"Invalid network format: {target}. "
                "Use IP address (192.168.1.1) or CIDR notation (192.168.1.0/24)",
                network=target,
            )

    def _validate_network(
        self,
        network: ipaddress.IPv4Network | ipaddress.IPv6Network,
        original: str,
    ) -> ipaddress.IPv4Network | ipaddress.IPv6Network:
        """
        Validate a network range.

        Args:
            network: Parsed network object
            original: Original string for error messages

        Returns:
            The validated network object

        Raises:
            NetworkValidationError: If validation fails
        """
        # Check network size
        num_hosts = network.num_addresses
        if num_hosts > self.max_network_size:
            logger.warning(
                f"Network too large: {original} has {num_hosts} addresses "
                f"(max: {self.max_network_size})"
            )
            raise NetworkValidationError(
                f"Network range too large: {num_hosts} addresses. "
                f"Maximum allowed is {self.max_network_size} addresses. "
                f"Use a smaller range like /24 or specify individual IPs.",
                network=original,
            )

        # Check if private
        if not self.is_private_network(original):
            logger.error(f"Attempted to scan non-private network: {original}")
            raise NetworkValidationError(
                f"Only private networks can be scanned. "
                f"{original} is not in a private range "
                f"(10.x.x.x, 172.16-31.x.x, 192.168.x.x).",
                network=original,
            )

        logger.info(f"Network validated: {original} ({num_hosts} addresses)")
        return network

    def _validate_ip(
        self,
        ip: ipaddress.IPv4Address | ipaddress.IPv6Address,
        original: str,
    ) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
        """
        Validate a single IP address.

        Args:
            ip: Parsed IP address object
            original: Original string for error messages

        Returns:
            The validated IP address object

        Raises:
            NetworkValidationError: If validation fails
        """
        if not self.is_private_ip(str(ip)):
            logger.error(f"Attempted to scan non-private IP: {original}")
            raise NetworkValidationError(
                f"Only private IP addresses can be scanned. "
                f"{original} is not in a private range "
                f"(10.x.x.x, 172.16-31.x.x, 192.168.x.x).",
                network=original,
            )

        logger.info(f"IP validated: {original}")
        return ip

    def get_network_info(self, target: str) -> dict:
        """
        Get detailed information about a network target.

        Args:
            target: IP address or network range

        Returns:
            Dictionary with network details

        Raises:
            NetworkValidationError: If target is invalid
        """
        validated = self.validate(target)

        if isinstance(validated, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
            return {
                "target": target,
                "network_address": str(validated.network_address),
                "broadcast_address": str(validated.broadcast_address),
                "netmask": str(validated.netmask),
                "num_addresses": validated.num_addresses,
                "num_hosts": validated.num_addresses - 2 if validated.num_addresses > 2 else 1,
                "is_private": True,
                "type": "network",
            }
        else:
            return {
                "target": target,
                "ip_address": str(validated),
                "is_private": True,
                "type": "single_ip",
                "num_hosts": 1,
            }


def get_local_network() -> Optional[str]:
    """
    Detect the local network range of this machine.

    Returns:
        Network range in CIDR notation (e.g., "192.168.1.0/24")
        or None if detection fails
    """
    try:
        import netifaces
    except ImportError:
        logger.warning("netifaces not installed, cannot detect local network")
        return None

    try:
        # Get default gateway interface
        gateways = netifaces.gateways()
        default_interface = gateways.get("default", {}).get(netifaces.AF_INET, [None, None])[1]

        if not default_interface:
            logger.warning("Could not determine default network interface")
            return None

        # Get interface addresses
        addrs = netifaces.ifaddresses(default_interface)
        ipv4_info = addrs.get(netifaces.AF_INET, [{}])[0]

        ip = ipv4_info.get("addr")
        netmask = ipv4_info.get("netmask")

        if not ip or not netmask:
            logger.warning(f"Could not get IP/netmask for interface {default_interface}")
            return None

        # Create network from IP and netmask
        network = ipaddress.ip_network(f"{ip}/{netmask}", strict=False)
        logger.info(f"Detected local network: {network}")

        return str(network)

    except Exception as e:
        logger.error(f"Error detecting local network: {e}")
        return None


def get_network_interfaces() -> list[dict]:
    """
    Get list of available network interfaces with their addresses.

    Returns:
        List of dictionaries with interface information
    """
    try:
        import netifaces
    except ImportError:
        logger.warning("netifaces not installed")
        return []

    interfaces = []

    try:
        for iface_name in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface_name)
            ipv4_info = addrs.get(netifaces.AF_INET, [{}])[0]

            ip = ipv4_info.get("addr")
            netmask = ipv4_info.get("netmask")

            if ip and netmask:
                try:
                    network = ipaddress.ip_network(f"{ip}/{netmask}", strict=False)
                    interfaces.append({
                        "name": iface_name,
                        "ip": ip,
                        "netmask": netmask,
                        "network": str(network),
                        "is_private": NetworkValidator().is_private_ip(ip),
                    })
                except ValueError:
                    continue

        logger.debug(f"Found {len(interfaces)} network interfaces")
        return interfaces

    except Exception as e:
        logger.error(f"Error getting network interfaces: {e}")
        return []

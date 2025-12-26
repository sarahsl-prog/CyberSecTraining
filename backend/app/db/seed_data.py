"""
Database seeding for development and testing.

This module provides functions to populate the database with sample data
for development and testing purposes. It creates realistic network scan
data including devices, vulnerabilities, and scenarios.
"""

from datetime import datetime, timedelta, UTC
from typing import List

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models.device import Device
from app.models.scan import Scan
from app.models.vulnerability import Vulnerability
from app.models.progress import Progress
from app.models.preference import Preference
from app.models.topology import Topology

logger = get_logger("seed_data")


def create_sample_scan(db: Session) -> Scan:
    """
    Create a sample network scan.

    Args:
        db: Database session

    Returns:
        Created Scan instance
    """
    scan = Scan(
        id="sample-scan-001",
        target_range="192.168.1.0/24",
        scan_type="quick",
        status="completed",
        started_at=datetime.now(UTC) - timedelta(hours=2),
        completed_at=datetime.now(UTC) - timedelta(hours=1, minutes=58),
        scanned_hosts=254,
        total_hosts=254,
        progress=100.0,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    logger.info(f"Created sample scan: {scan.id}")
    return scan


def create_sample_devices(db: Session, scan_id: str) -> List[Device]:
    """
    Create sample network devices.

    Args:
        db: Database session
        scan_id: Parent scan ID

    Returns:
        List of created Device instances
    """
    devices_data = [
        {
            "ip": "192.168.1.1",
            "mac": "00:1A:2B:3C:4D:5E",
            "hostname": "router.local",
            "vendor": "Linksys",
            "device_type": "router",
            "os": "Linux",
            "os_accuracy": 95,
            "open_ports": [
                {"port": 80, "protocol": "tcp", "state": "open", "service": "http"},
                {"port": 443, "protocol": "tcp", "state": "open", "service": "https"},
                {"port": 53, "protocol": "udp", "state": "open", "service": "dns"},
            ],
            "vulnerability_count": 2,
        },
        {
            "ip": "192.168.1.10",
            "mac": "AA:BB:CC:DD:EE:FF",
            "hostname": "desktop.local",
            "vendor": "Dell Inc.",
            "device_type": "computer",
            "os": "Windows 10",
            "os_accuracy": 98,
            "open_ports": [
                {"port": 445, "protocol": "tcp", "state": "open", "service": "microsoft-ds"},
                {"port": 3389, "protocol": "tcp", "state": "open", "service": "ms-wbt-server"},
            ],
            "vulnerability_count": 1,
        },
        {
            "ip": "192.168.1.15",
            "mac": "11:22:33:44:55:66",
            "hostname": "laptop.local",
            "vendor": "Apple",
            "device_type": "computer",
            "os": "macOS",
            "os_accuracy": 92,
            "open_ports": [
                {"port": 22, "protocol": "tcp", "state": "open", "service": "ssh"},
                {"port": 5000, "protocol": "tcp", "state": "open", "service": "upnp"},
            ],
            "vulnerability_count": 0,
        },
        {
            "ip": "192.168.1.20",
            "mac": "AA:11:BB:22:CC:33",
            "hostname": "smart-tv.local",
            "vendor": "Samsung",
            "device_type": "media",
            "os": "Tizen",
            "os_accuracy": 85,
            "open_ports": [
                {"port": 8080, "protocol": "tcp", "state": "open", "service": "http-proxy"},
            ],
            "vulnerability_count": 3,
        },
        {
            "ip": "192.168.1.25",
            "mac": "BB:22:CC:33:DD:44",
            "hostname": "printer.local",
            "vendor": "HP",
            "device_type": "printer",
            "os": "Printer OS",
            "os_accuracy": 90,
            "open_ports": [
                {"port": 9100, "protocol": "tcp", "state": "open", "service": "jetdirect"},
                {"port": 80, "protocol": "tcp", "state": "open", "service": "http"},
            ],
            "vulnerability_count": 1,
        },
    ]

    devices = []
    for device_data in devices_data:
        device = Device(
            scan_id=scan_id,
            **device_data
        )
        db.add(device)
        devices.append(device)

    db.commit()
    for device in devices:
        db.refresh(device)
        logger.info(f"Created device: {device.hostname} ({device.ip})")

    return devices


def create_sample_vulnerabilities(db: Session, devices: List[Device]) -> List[Vulnerability]:
    """
    Create sample vulnerabilities for devices.

    Args:
        db: Database session
        devices: List of devices to add vulnerabilities to

    Returns:
        List of created Vulnerability instances
    """
    vulnerabilities_data = [
        # Router vulnerabilities
        {
            "device_id": devices[0].id,  # router
            "vuln_type": "default_credentials",
            "severity": "high",
            "title": "Default Admin Credentials",
            "description": "Router is using default username and password (admin/admin)",
            "remediation": "Change the default admin password immediately. Use a strong password with at least 16 characters.",
            "cve_id": None,
            "affected_service": "http",
            "affected_port": "80",
        },
        {
            "device_id": devices[0].id,  # router
            "vuln_type": "outdated_firmware",
            "severity": "medium",
            "title": "Outdated Router Firmware",
            "description": "Router firmware is 2 versions behind the latest release",
            "remediation": "Update router firmware to the latest version from manufacturer's website",
            "affected_service": "management",
        },
        # Desktop vulnerability
        {
            "device_id": devices[1].id,  # desktop
            "vuln_type": "open_rdp",
            "severity": "critical",
            "title": "Exposed RDP Service",
            "description": "Remote Desktop Protocol (RDP) is exposed to the network without proper security",
            "remediation": "Disable RDP if not needed, or configure firewall rules and use VPN access",
            "cve_id": None,
            "affected_service": "ms-wbt-server",
            "affected_port": "3389",
        },
        # Smart TV vulnerabilities
        {
            "device_id": devices[3].id,  # smart-tv
            "vuln_type": "upnp_enabled",
            "severity": "medium",
            "title": "UPnP Enabled",
            "description": "Universal Plug and Play (UPnP) is enabled, which can be exploited",
            "remediation": "Disable UPnP in device settings if not required",
        },
        {
            "device_id": devices[3].id,  # smart-tv
            "vuln_type": "outdated_firmware",
            "severity": "high",
            "title": "Outdated Smart TV Firmware",
            "description": "Smart TV firmware is significantly out of date with known security vulnerabilities",
            "remediation": "Update firmware through TV settings menu",
        },
        {
            "device_id": devices[3].id,  # smart-tv
            "vuln_type": "weak_encryption",
            "severity": "low",
            "title": "Weak WiFi Encryption",
            "description": "Device is using outdated encryption protocol",
            "remediation": "Update router to use WPA3 encryption",
        },
        # Printer vulnerability
        {
            "device_id": devices[4].id,  # printer
            "vuln_type": "open_port",
            "severity": "medium",
            "title": "Printer Management Interface Exposed",
            "description": "Printer web interface is accessible without authentication",
            "remediation": "Enable password protection on printer web interface",
            "affected_service": "http",
            "affected_port": "80",
        },
    ]

    vulnerabilities = []
    for vuln_data in vulnerabilities_data:
        vuln = Vulnerability(**vuln_data)
        db.add(vuln)
        vulnerabilities.append(vuln)

    db.commit()
    for vuln in vulnerabilities:
        db.refresh(vuln)
        logger.info(f"Created vulnerability: {vuln.title}")

    return vulnerabilities


def create_sample_topology(db: Session, devices: List[Device]) -> List[Topology]:
    """
    Create sample network topology connections.

    Args:
        db: Database session
        devices: List of devices

    Returns:
        List of created Topology instances
    """
    # All devices connect to the router (devices[0])
    router_id = devices[0].id
    topology_entries = []

    for device in devices[1:]:  # Skip router itself
        topology = Topology(
            device_id=device.id,
            connected_to_device_id=router_id,
            connection_type="ethernet",
            latency_ms=1.5,
        )
        db.add(topology)
        topology_entries.append(topology)

    db.commit()
    for topo in topology_entries:
        db.refresh(topo)

    logger.info(f"Created {len(topology_entries)} topology connections")
    return topology_entries


def create_sample_progress(db: Session) -> List[Progress]:
    """
    Create sample user progress for scenarios.

    Args:
        db: Database session

    Returns:
        List of created Progress instances
    """
    progress_data = [
        {
            "user_id": "local",
            "scenario_id": "home-basics-01",
            "completed": True,
            "score": 95,
            "completed_at": datetime.now(UTC) - timedelta(days=7),
        },
        {
            "user_id": "local",
            "scenario_id": "home-basics-02",
            "completed": True,
            "score": 88,
            "completed_at": datetime.now(UTC) - timedelta(days=5),
        },
        {
            "user_id": "local",
            "scenario_id": "home-basics-03",
            "completed": False,
            "score": 45,
            "last_accessed_at": datetime.now(UTC) - timedelta(days=1),
        },
    ]

    progress_entries = []
    for prog_data in progress_data:
        progress = Progress(**prog_data)
        db.add(progress)
        progress_entries.append(progress)

    db.commit()
    for prog in progress_entries:
        db.refresh(prog)

    logger.info(f"Created {len(progress_entries)} progress entries")
    return progress_entries


def create_sample_preferences(db: Session) -> List[Preference]:
    """
    Create sample user preferences.

    Args:
        db: Database session

    Returns:
        List of created Preference instances
    """
    preferences_data = [
        {"user_id": "local", "key": "theme", "value": "dark"},
        {"user_id": "local", "key": "color_mode", "value": "high-contrast"},
        {"user_id": "local", "key": "font_size", "value": "125"},
        {"user_id": "local", "key": "reduce_motion", "value": "true"},
        {"user_id": "local", "key": "llm_detail_level", "value": "standard"},
        {"user_id": "local", "key": "prefer_local_llm", "value": "true"},
    ]

    preferences = []
    for pref_data in preferences_data:
        pref = Preference(**pref_data)
        db.add(pref)
        preferences.append(pref)

    db.commit()
    for pref in preferences:
        db.refresh(pref)

    logger.info(f"Created {len(preferences)} preference entries")
    return preferences


def seed_database() -> None:
    """
    Seed the database with comprehensive sample data.

    Creates:
    - 1 sample network scan
    - 5 sample devices (router, desktop, laptop, smart TV, printer)
    - 7 vulnerabilities across devices
    - Network topology connections
    - User progress for 3 scenarios
    - User preferences
    """
    logger.info("Starting database seeding...")
    db = SessionLocal()

    try:
        # Create scan
        scan = create_sample_scan(db)

        # Create devices
        devices = create_sample_devices(db, scan.id)

        # Create vulnerabilities
        vulnerabilities = create_sample_vulnerabilities(db, devices)

        # Create topology
        topology = create_sample_topology(db, devices)

        # Create progress
        progress = create_sample_progress(db)

        # Create preferences
        preferences = create_sample_preferences(db)

        logger.info("Database seeding completed successfully!")
        logger.info(f"Created: {len(devices)} devices, {len(vulnerabilities)} vulnerabilities, "
                   f"{len(topology)} topology entries, {len(progress)} progress entries, "
                   f"{len(preferences)} preferences")

    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Allow running this script directly for development
    from app.db.init_db import init_db

    logger.info("Initializing database tables...")
    init_db()

    logger.info("Seeding database with sample data...")
    seed_database()

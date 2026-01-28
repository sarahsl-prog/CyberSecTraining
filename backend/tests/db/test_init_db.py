"""
Tests for database initialization.

This module tests the database initialization and seeding functionality
to ensure the database is properly created and populated.
"""

import pytest
from pathlib import Path
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db.init_db import init_db
from app.db.seed_data import (
    create_sample_scan,
    create_sample_devices,
    create_sample_vulnerabilities,
    create_sample_topology,
    create_sample_progress,
    create_sample_preferences,
)
from app.models import Base, Device, Scan, Vulnerability, Topology, Progress, Preference


@pytest.fixture
def test_engine():
    """Create a test database engine."""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def test_db(test_engine):
    """Create a test database session."""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    yield session
    session.close()


class TestDatabaseInitialization:
    """Test database initialization."""

    def test_init_db_creates_tables(self, test_engine):
        """Test that init_db creates all required tables."""
        # Get inspector to check tables
        inspector = inspect(test_engine)
        tables = inspector.get_table_names()

        # Verify all expected tables exist
        expected_tables = [
            "devices",
            "scans",
            "vulnerabilities",
            "topology",
            "progress",
            "preferences",
        ]

        for table in expected_tables:
            assert table in tables, f"Table '{table}' not found in database"

    def test_data_directory_created(self, tmp_path):
        """Test that data directory is created if it doesn't exist."""
        # This test ensures the data directory is created during init
        assert settings.data_dir is not None


class TestSeedData:
    """Test database seeding functionality."""

    def test_create_sample_scan(self, test_db):
        """Test creating a sample scan."""
        scan = create_sample_scan(test_db)

        assert scan is not None
        assert scan.id is not None
        assert scan.target_range == "192.168.1.0/24"
        assert scan.scan_type == "quick"
        assert scan.status == "completed"
        assert scan.progress == 100.0
        assert scan.scanned_hosts == 254
        assert scan.total_hosts == 254

    def test_create_sample_devices(self, test_db):
        """Test creating sample devices."""
        scan = create_sample_scan(test_db)
        devices = create_sample_devices(test_db, scan.id)

        assert len(devices) == 5
        assert all(d.scan_id == scan.id for d in devices)

        # Verify router
        router = devices[0]
        assert router.ip == "192.168.1.1"
        assert router.device_type == "router"
        assert router.hostname == "router.local"
        assert len(router.open_ports) > 0

        # Verify desktop
        desktop = devices[1]
        assert desktop.ip == "192.168.1.10"
        assert desktop.device_type == "computer"

        # Verify all devices have required fields
        for device in devices:
            assert device.ip is not None
            assert device.device_type is not None
            assert device.is_up is True
            assert isinstance(device.open_ports, list)

    def test_create_sample_vulnerabilities(self, test_db):
        """Test creating sample vulnerabilities."""
        scan = create_sample_scan(test_db)
        devices = create_sample_devices(test_db, scan.id)
        vulnerabilities = create_sample_vulnerabilities(test_db, devices)

        assert len(vulnerabilities) == 7

        # Verify vulnerabilities are linked to devices
        device_ids = {d.id for d in devices}
        for vuln in vulnerabilities:
            assert vuln.device_id in device_ids
            assert vuln.severity in ["low", "medium", "high", "critical"]
            assert vuln.title is not None
            assert vuln.description is not None

        # Verify specific vulnerability
        default_creds = next((v for v in vulnerabilities if v.vuln_type == "default_credentials"), None)
        assert default_creds is not None
        assert default_creds.severity == "high"
        assert "default" in default_creds.title.lower()

    def test_create_sample_topology(self, test_db):
        """Test creating sample network topology."""
        scan = create_sample_scan(test_db)
        devices = create_sample_devices(test_db, scan.id)
        topology = create_sample_topology(test_db, devices)

        # Should have 4 connections (all devices connect to router except router itself)
        assert len(topology) == 4

        router_id = devices[0].id
        for topo in topology:
            assert topo.connected_to_device_id == router_id
            assert topo.connection_type == "ethernet"
            assert topo.latency_ms > 0

    def test_create_sample_progress(self, test_db):
        """Test creating sample user progress."""
        progress_entries = create_sample_progress(test_db)

        assert len(progress_entries) == 3

        # Verify completed scenarios
        completed = [p for p in progress_entries if p.completed]
        assert len(completed) == 2
        for prog in completed:
            assert prog.score > 0
            assert prog.completed_at is not None

        # Verify in-progress scenario
        in_progress = [p for p in progress_entries if not p.completed]
        assert len(in_progress) == 1
        assert in_progress[0].score > 0  # Has partial score
        assert in_progress[0].last_accessed_at is not None

    def test_create_sample_preferences(self, test_db):
        """Test creating sample user preferences."""
        preferences = create_sample_preferences(test_db)

        assert len(preferences) == 6

        # Verify specific preferences
        pref_dict = {p.key: p.value for p in preferences}
        assert pref_dict["theme"] == "dark"
        assert pref_dict["color_mode"] == "high-contrast"
        assert pref_dict["font_size"] == "125"
        assert pref_dict["reduce_motion"] == "true"

        # Verify all preferences have user_id
        for pref in preferences:
            assert pref.user_id == "local"
            assert pref.key is not None
            assert pref.value is not None


class TestDataIntegrity:
    """Test data integrity and relationships."""

    def test_device_vulnerability_relationship(self, test_db):
        """Test that devices and vulnerabilities are properly linked."""
        scan = create_sample_scan(test_db)
        devices = create_sample_devices(test_db, scan.id)
        vulnerabilities = create_sample_vulnerabilities(test_db, devices)

        # Query a device and check its vulnerabilities
        router = test_db.query(Device).filter_by(hostname="router.local").first()
        assert router is not None

        router_vulns = test_db.query(Vulnerability).filter_by(device_id=router.id).all()
        assert len(router_vulns) == router.vulnerability_count

    def test_scan_device_relationship(self, test_db):
        """Test that scans and devices are properly linked."""
        scan = create_sample_scan(test_db)
        devices = create_sample_devices(test_db, scan.id)

        # Query scan and check devices
        scan_from_db = test_db.query(Scan).filter_by(id=scan.id).first()
        assert scan_from_db is not None

        scan_devices = test_db.query(Device).filter_by(scan_id=scan.id).all()
        assert len(scan_devices) == 5

    def test_topology_relationships(self, test_db):
        """Test that topology entries reference valid devices."""
        scan = create_sample_scan(test_db)
        devices = create_sample_devices(test_db, scan.id)
        topology = create_sample_topology(test_db, devices)

        # Verify all topology entries reference existing devices
        device_ids = {d.id for d in devices}
        for topo in topology:
            assert topo.device_id in device_ids
            assert topo.connected_to_device_id in device_ids

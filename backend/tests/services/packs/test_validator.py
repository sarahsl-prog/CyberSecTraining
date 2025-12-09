"""
Tests for the pack validator module.

These tests verify that:
- Pack manifests are correctly validated
- Vulnerability definitions are correctly validated
- Invalid data is properly rejected
"""

import pytest
import json
import tempfile
from pathlib import Path

from app.services.packs.validator import PackValidator, PackValidationError


class TestPackValidator:
    """Tests for the PackValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = PackValidator()

    # =========================================================================
    # Manifest Validation Tests
    # =========================================================================

    def test_validate_manifest_valid(self, tmp_path):
        """Test validation of valid manifest."""
        manifest = {
            "id": "test-pack",
            "name": "Test Pack",
            "version": "1.0.0",
            "description": "A test pack",
        }
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(manifest))

        errors = self.validator.validate_manifest(manifest_file)
        assert errors == []

    def test_validate_manifest_missing_required(self, tmp_path):
        """Test validation rejects missing required fields."""
        manifest = {
            "name": "Test Pack",
            # Missing id and version
        }
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(manifest))

        errors = self.validator.validate_manifest(manifest_file)
        assert any("id" in e for e in errors)
        assert any("version" in e for e in errors)

    def test_validate_manifest_invalid_json(self, tmp_path):
        """Test validation rejects invalid JSON."""
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text("{ invalid json }")

        errors = self.validator.validate_manifest(manifest_file)
        assert len(errors) == 1
        assert "Invalid JSON" in errors[0]

    def test_validate_manifest_not_found(self, tmp_path):
        """Test validation handles missing file."""
        errors = self.validator.validate_manifest(tmp_path / "nonexistent.json")
        assert len(errors) == 1
        assert "not found" in errors[0]

    def test_validate_manifest_invalid_version(self, tmp_path):
        """Test validation rejects invalid version format."""
        manifest = {
            "id": "test",
            "name": "Test",
            "version": "not-semver",
        }
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(manifest))

        errors = self.validator.validate_manifest(manifest_file)
        assert any("version" in e.lower() for e in errors)

    # =========================================================================
    # Vulnerability Validation Tests
    # =========================================================================

    def test_validate_vulnerability_valid(self):
        """Test validation of valid vulnerability."""
        vuln = {
            "id": "test_vuln",
            "title": "Test Vulnerability",
            "severity": "high",
            "description": "A test vulnerability",
        }

        errors = self.validator.validate_vulnerability(vuln)
        assert errors == []

    def test_validate_vulnerability_missing_required(self):
        """Test validation rejects missing required fields."""
        vuln = {
            "description": "Missing id, title, severity",
        }

        errors = self.validator.validate_vulnerability(vuln)
        assert len(errors) == 3
        assert any("id" in e for e in errors)
        assert any("title" in e for e in errors)
        assert any("severity" in e for e in errors)

    def test_validate_vulnerability_invalid_severity(self):
        """Test validation rejects invalid severity."""
        vuln = {
            "id": "test",
            "title": "Test",
            "severity": "super-critical",  # Invalid
        }

        errors = self.validator.validate_vulnerability(vuln)
        assert len(errors) == 1
        assert "severity" in errors[0].lower()

    def test_validate_vulnerability_valid_severities(self):
        """Test all valid severity levels are accepted."""
        for severity in ["critical", "high", "medium", "low", "info"]:
            vuln = {
                "id": "test",
                "title": "Test",
                "severity": severity,
            }
            errors = self.validator.validate_vulnerability(vuln)
            assert errors == [], f"Severity {severity} should be valid"

    def test_validate_vulnerability_detection_rules(self):
        """Test validation of detection rules."""
        vuln = {
            "id": "test",
            "title": "Test",
            "severity": "high",
            "detection_rules": [
                {"type": "port", "port": 22},
                {"type": "service", "service": "ssh"},
            ],
        }

        errors = self.validator.validate_vulnerability(vuln)
        assert errors == []

    def test_validate_vulnerability_invalid_detection_rule(self):
        """Test validation rejects invalid detection rules."""
        vuln = {
            "id": "test",
            "title": "Test",
            "severity": "high",
            "detection_rules": [
                {"type": "invalid_type"},  # Invalid type
            ],
        }

        errors = self.validator.validate_vulnerability(vuln)
        assert any("type" in e for e in errors)

    def test_validate_vulnerability_cve_format(self):
        """Test CVE format validation."""
        # Valid CVE
        vuln = {
            "id": "test",
            "title": "Test",
            "severity": "high",
            "cve_ids": ["CVE-2024-12345"],
        }
        errors = self.validator.validate_vulnerability(vuln)
        assert errors == []

        # Invalid CVE
        vuln["cve_ids"] = ["INVALID-2024-123"]
        errors = self.validator.validate_vulnerability(vuln)
        assert any("CVE" in e for e in errors)

    # =========================================================================
    # Pack Validation Tests
    # =========================================================================

    def test_validate_pack_valid(self, tmp_path):
        """Test validation of valid pack."""
        # Create manifest
        manifest = {
            "id": "test-pack",
            "name": "Test Pack",
            "version": "1.0.0",
        }
        (tmp_path / "manifest.json").write_text(json.dumps(manifest))

        # Create vulnerabilities directory
        vuln_dir = tmp_path / "vulnerabilities"
        vuln_dir.mkdir()

        vuln = {
            "id": "test_vuln",
            "title": "Test Vulnerability",
            "severity": "high",
        }
        (vuln_dir / "test.json").write_text(json.dumps(vuln))

        errors = self.validator.validate_pack(tmp_path)
        assert errors == []

    def test_validate_pack_not_found(self, tmp_path):
        """Test validation handles missing pack directory."""
        errors = self.validator.validate_pack(tmp_path / "nonexistent")
        assert len(errors) == 1
        assert "not found" in errors[0]

    def test_validate_pack_not_directory(self, tmp_path):
        """Test validation handles file instead of directory."""
        file_path = tmp_path / "not_a_dir"
        file_path.write_text("not a directory")

        errors = self.validator.validate_pack(file_path)
        assert len(errors) == 1
        assert "not a directory" in errors[0]

    # =========================================================================
    # Validation Report Tests
    # =========================================================================

    def test_create_validation_report(self, tmp_path):
        """Test validation report generation."""
        # Create a valid pack
        manifest = {
            "id": "test",
            "name": "Test",
            "version": "1.0.0",
        }
        (tmp_path / "manifest.json").write_text(json.dumps(manifest))

        vuln_dir = tmp_path / "vulnerabilities"
        vuln_dir.mkdir()

        report = self.validator.create_validation_report(tmp_path)

        assert "pack_path" in report
        assert "valid" in report
        assert "error_count" in report
        assert "vulnerability_count" in report
        assert "has_manifest" in report


class TestHelperMethods:
    """Tests for validator helper methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = PackValidator()

    def test_validate_semver_valid(self):
        """Test semver validation for valid versions."""
        valid_versions = [
            "1.0.0",
            "0.1.0",
            "10.20.30",
            "1.0.0-alpha",
            "1.0.0-beta.1",
            "1.0.0+build.123",
        ]
        for version in valid_versions:
            assert self.validator._validate_semver(version), f"{version} should be valid"

    def test_validate_semver_invalid(self):
        """Test semver validation for invalid versions."""
        invalid_versions = [
            "1.0",
            "1",
            "v1.0.0",
            "1.0.0.0",
            "one.two.three",
        ]
        for version in invalid_versions:
            assert not self.validator._validate_semver(version), f"{version} should be invalid"

    def test_validate_cve_format_valid(self):
        """Test CVE format validation for valid CVEs."""
        valid_cves = [
            "CVE-2024-12345",
            "CVE-2020-1234",
            "CVE-1999-0001",
            "CVE-2024-123456",
        ]
        for cve in valid_cves:
            assert self.validator._validate_cve_format(cve), f"{cve} should be valid"

    def test_validate_cve_format_invalid(self):
        """Test CVE format validation for invalid CVEs."""
        invalid_cves = [
            "CVE-24-12345",
            "cve-2024-12345",
            "CVE-2024-123",
            "CVE2024-12345",
            "VULN-2024-12345",
        ]
        for cve in invalid_cves:
            assert not self.validator._validate_cve_format(cve), f"{cve} should be invalid"

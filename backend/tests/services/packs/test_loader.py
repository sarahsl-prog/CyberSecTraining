"""
Tests for the pack loader module.

These tests verify that:
- Packs are correctly discovered
- Pack content is correctly loaded
- Invalid packs are handled gracefully
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.services.packs.loader import PackLoader, PackLoadError
from app.services.packs.validator import PackValidationError
from app.services.packs.models import PackManifest, VulnerabilityDefinition, Severity


class TestPackLoader:
    """Tests for the PackLoader class."""

    # =========================================================================
    # Discovery Tests
    # =========================================================================

    def test_discover_packs(self, tmp_path):
        """Test pack discovery."""
        # Create two valid packs
        for pack_name in ["pack1", "pack2"]:
            pack_dir = tmp_path / pack_name
            pack_dir.mkdir()
            manifest = {"id": pack_name, "name": f"Pack {pack_name}", "version": "1.0.0"}
            (pack_dir / "manifest.json").write_text(json.dumps(manifest))

        # Create a non-pack directory (no manifest)
        (tmp_path / "not-a-pack").mkdir()

        loader = PackLoader(packs_dir=tmp_path, validate=False)
        packs = loader.discover_packs()

        assert len(packs) == 2
        assert "pack1" in packs
        assert "pack2" in packs
        assert "not-a-pack" not in packs

    def test_discover_packs_empty_dir(self, tmp_path):
        """Test discovery with empty packs directory."""
        loader = PackLoader(packs_dir=tmp_path, validate=False)
        packs = loader.discover_packs()
        assert packs == []

    def test_discover_packs_nonexistent_dir(self, tmp_path):
        """Test discovery with nonexistent directory."""
        loader = PackLoader(packs_dir=tmp_path / "nonexistent", validate=False)
        packs = loader.discover_packs()
        assert packs == []

    # =========================================================================
    # Loading Tests
    # =========================================================================

    def test_load_pack_success(self, tmp_path):
        """Test successful pack loading."""
        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()

        # Create manifest
        manifest = {
            "id": "test-pack",
            "name": "Test Pack",
            "version": "1.0.0",
            "description": "A test pack",
        }
        (pack_dir / "manifest.json").write_text(json.dumps(manifest))

        # Create vulnerabilities
        vuln_dir = pack_dir / "vulnerabilities"
        vuln_dir.mkdir()

        vuln = {
            "id": "test_vuln",
            "title": "Test Vulnerability",
            "severity": "high",
            "description": "Test description",
        }
        (vuln_dir / "test_vuln.json").write_text(json.dumps(vuln))

        loader = PackLoader(packs_dir=tmp_path, validate=False)
        pack = loader.load_pack("test-pack")

        assert pack.manifest.id == "test-pack"
        assert pack.manifest.name == "Test Pack"
        assert len(pack.vulnerabilities) == 1
        assert "test_vuln" in pack.vulnerabilities

    def test_load_pack_not_found(self, tmp_path):
        """Test loading nonexistent pack."""
        loader = PackLoader(packs_dir=tmp_path, validate=False)

        with pytest.raises(PackLoadError) as exc_info:
            loader.load_pack("nonexistent")

        assert "not found" in str(exc_info.value).lower()

    def test_load_pack_with_validation(self, tmp_path):
        """Test loading with validation enabled."""
        pack_dir = tmp_path / "valid-pack"
        pack_dir.mkdir()

        manifest = {
            "id": "valid-pack",
            "name": "Valid Pack",
            "version": "1.0.0",
        }
        (pack_dir / "manifest.json").write_text(json.dumps(manifest))

        loader = PackLoader(packs_dir=tmp_path, validate=True)
        pack = loader.load_pack("valid-pack")

        assert pack.manifest.id == "valid-pack"

    def test_load_pack_validation_failure(self, tmp_path):
        """Test loading fails when validation fails."""
        pack_dir = tmp_path / "invalid-pack"
        pack_dir.mkdir()

        # Invalid manifest (missing required fields)
        manifest = {"description": "Missing id, name, version"}
        (pack_dir / "manifest.json").write_text(json.dumps(manifest))

        loader = PackLoader(packs_dir=tmp_path, validate=True)

        with pytest.raises(PackValidationError):
            loader.load_pack("invalid-pack")

    # =========================================================================
    # Vulnerability Loading Tests
    # =========================================================================

    def test_load_vulnerabilities(self, tmp_path):
        """Test vulnerability loading."""
        pack_dir = tmp_path / "vuln-pack"
        pack_dir.mkdir()

        manifest = {"id": "vuln-pack", "name": "Vuln Pack", "version": "1.0.0"}
        (pack_dir / "manifest.json").write_text(json.dumps(manifest))

        vuln_dir = pack_dir / "vulnerabilities"
        vuln_dir.mkdir()

        # Create multiple vulnerabilities
        for i in range(3):
            vuln = {
                "id": f"vuln_{i}",
                "title": f"Vulnerability {i}",
                "severity": ["critical", "high", "medium"][i],
            }
            (vuln_dir / f"vuln_{i}.json").write_text(json.dumps(vuln))

        loader = PackLoader(packs_dir=tmp_path, validate=False)
        pack = loader.load_pack("vuln-pack")

        assert len(pack.vulnerabilities) == 3
        assert pack.vulnerabilities["vuln_0"].severity == Severity.CRITICAL
        assert pack.vulnerabilities["vuln_1"].severity == Severity.HIGH
        assert pack.vulnerabilities["vuln_2"].severity == Severity.MEDIUM

    def test_load_vulnerabilities_with_detection_rules(self, tmp_path):
        """Test loading vulnerabilities with detection rules."""
        pack_dir = tmp_path / "detect-pack"
        pack_dir.mkdir()

        manifest = {"id": "detect-pack", "name": "Detection Pack", "version": "1.0.0"}
        (pack_dir / "manifest.json").write_text(json.dumps(manifest))

        vuln_dir = pack_dir / "vulnerabilities"
        vuln_dir.mkdir()

        vuln = {
            "id": "detected_vuln",
            "title": "Detected Vulnerability",
            "severity": "high",
            "detection_rules": [
                {"type": "port", "port": 22, "condition": "exists"},
                {"type": "service", "service": "ssh"},
            ],
        }
        (vuln_dir / "detected.json").write_text(json.dumps(vuln))

        loader = PackLoader(packs_dir=tmp_path, validate=False)
        pack = loader.load_pack("detect-pack")

        vuln = pack.vulnerabilities["detected_vuln"]
        assert len(vuln.detection_rules) == 2
        assert vuln.detection_rules[0].type == "port"
        assert vuln.detection_rules[0].port == 22

    def test_load_vulnerabilities_handles_invalid_json(self, tmp_path):
        """Test that invalid JSON files are skipped."""
        pack_dir = tmp_path / "mixed-pack"
        pack_dir.mkdir()

        manifest = {"id": "mixed-pack", "name": "Mixed Pack", "version": "1.0.0"}
        (pack_dir / "manifest.json").write_text(json.dumps(manifest))

        vuln_dir = pack_dir / "vulnerabilities"
        vuln_dir.mkdir()

        # Valid vulnerability
        vuln = {"id": "valid", "title": "Valid", "severity": "low"}
        (vuln_dir / "valid.json").write_text(json.dumps(vuln))

        # Invalid JSON file
        (vuln_dir / "invalid.json").write_text("{ invalid json }")

        loader = PackLoader(packs_dir=tmp_path, validate=False)
        pack = loader.load_pack("mixed-pack")

        # Should load the valid one and skip the invalid
        assert len(pack.vulnerabilities) == 1
        assert "valid" in pack.vulnerabilities

    # =========================================================================
    # Remediation Guide Loading Tests
    # =========================================================================

    def test_load_remediation_guides(self, tmp_path):
        """Test remediation guide loading."""
        pack_dir = tmp_path / "guide-pack"
        pack_dir.mkdir()

        manifest = {"id": "guide-pack", "name": "Guide Pack", "version": "1.0.0"}
        (pack_dir / "manifest.json").write_text(json.dumps(manifest))

        knowledge_dir = pack_dir / "knowledge"
        knowledge_dir.mkdir()

        guides = {
            "guides": [
                {
                    "vuln_id": "test_vuln",
                    "title": "How to Fix Test Vuln",
                    "steps": ["Step 1", "Step 2"],
                }
            ]
        }
        (knowledge_dir / "remediation_guides.json").write_text(json.dumps(guides))

        loader = PackLoader(packs_dir=tmp_path, validate=False)
        pack = loader.load_pack("guide-pack")

        assert len(pack.remediation_guides) == 1
        assert "test_vuln" in pack.remediation_guides
        assert pack.remediation_guides["test_vuln"].title == "How to Fix Test Vuln"

    # =========================================================================
    # Load All Tests
    # =========================================================================

    def test_load_all_packs(self, tmp_path):
        """Test loading all packs."""
        for name in ["pack1", "pack2"]:
            pack_dir = tmp_path / name
            pack_dir.mkdir()
            manifest = {"id": name, "name": f"Pack {name}", "version": "1.0.0"}
            (pack_dir / "manifest.json").write_text(json.dumps(manifest))

        loader = PackLoader(packs_dir=tmp_path, validate=False)
        packs = loader.load_all_packs()

        assert len(packs) == 2

    def test_load_all_skips_invalid(self, tmp_path):
        """Test that load_all skips packs that fail to load."""
        # Valid pack
        valid_dir = tmp_path / "valid"
        valid_dir.mkdir()
        (valid_dir / "manifest.json").write_text(
            json.dumps({"id": "valid", "name": "Valid", "version": "1.0.0"})
        )

        # Invalid pack (bad manifest)
        invalid_dir = tmp_path / "invalid"
        invalid_dir.mkdir()
        (invalid_dir / "manifest.json").write_text("{ invalid }")

        loader = PackLoader(packs_dir=tmp_path, validate=False)
        packs = loader.load_all_packs()

        assert len(packs) == 1
        assert packs[0].manifest.id == "valid"


class TestGetVulnerability:
    """Tests for vulnerability lookup."""

    def test_get_vulnerability_from_specific_pack(self, tmp_path):
        """Test getting vulnerability from specific pack."""
        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()
        (pack_dir / "manifest.json").write_text(
            json.dumps({"id": "test-pack", "name": "Test", "version": "1.0.0"})
        )

        vuln_dir = pack_dir / "vulnerabilities"
        vuln_dir.mkdir()
        (vuln_dir / "test.json").write_text(
            json.dumps({"id": "test_vuln", "title": "Test", "severity": "high"})
        )

        loader = PackLoader(packs_dir=tmp_path, validate=False)
        vuln = loader.get_vulnerability("test_vuln", pack_id="test-pack")

        assert vuln is not None
        assert vuln.id == "test_vuln"

    def test_get_vulnerability_not_found(self, tmp_path):
        """Test getting nonexistent vulnerability."""
        loader = PackLoader(packs_dir=tmp_path, validate=False)
        vuln = loader.get_vulnerability("nonexistent")
        assert vuln is None

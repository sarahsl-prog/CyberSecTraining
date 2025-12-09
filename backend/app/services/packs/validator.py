"""
Content pack validator.

This module provides validation for content packs, ensuring they
conform to the expected schema and contain valid data.
"""

import json
from pathlib import Path
from typing import Optional

from app.core.logging import get_logger
from app.services.packs.models import (
    PackManifest,
    VulnerabilityDefinition,
    Severity,
)

logger = get_logger("packs")


class PackValidationError(Exception):
    """
    Exception raised when pack validation fails.

    Attributes:
        message: Error description
        pack_path: Path to the pack that failed validation
        errors: List of specific validation errors
    """

    def __init__(
        self,
        message: str,
        pack_path: Optional[str] = None,
        errors: Optional[list[str]] = None,
    ):
        self.message = message
        self.pack_path = pack_path
        self.errors = errors or []
        super().__init__(self.message)


class PackValidator:
    """
    Validates content pack structure and data.

    This class provides methods to validate:
    - Pack manifest files
    - Vulnerability definitions
    - Remediation guides
    - Overall pack structure

    Example:
        >>> validator = PackValidator()
        >>> errors = validator.validate_pack("packs/core")
        >>> if errors:
        ...     print("Validation failed:", errors)
    """

    # Required fields in manifest
    REQUIRED_MANIFEST_FIELDS = ["id", "name", "version"]

    # Valid severity values
    VALID_SEVERITIES = [s.value for s in Severity]

    # Required fields in vulnerability definition
    REQUIRED_VULN_FIELDS = ["id", "title", "severity"]

    def __init__(self):
        """Initialize the validator."""
        logger.debug("PackValidator initialized")

    def validate_pack(self, pack_path: str | Path) -> list[str]:
        """
        Validate an entire content pack.

        Args:
            pack_path: Path to the pack directory

        Returns:
            List of validation error messages (empty if valid)
        """
        pack_path = Path(pack_path)
        errors = []

        logger.info(f"Validating pack at: {pack_path}")

        # Check pack exists
        if not pack_path.exists():
            return [f"Pack directory not found: {pack_path}"]

        if not pack_path.is_dir():
            return [f"Pack path is not a directory: {pack_path}"]

        # Validate manifest
        manifest_path = pack_path / "manifest.json"
        manifest_errors = self.validate_manifest(manifest_path)
        errors.extend(manifest_errors)

        # Validate vulnerabilities
        vuln_dir = pack_path / "vulnerabilities"
        if vuln_dir.exists():
            vuln_errors = self.validate_vulnerabilities_dir(vuln_dir)
            errors.extend(vuln_errors)

        # Log results
        if errors:
            logger.warning(f"Pack validation failed with {len(errors)} errors")
        else:
            logger.info(f"Pack validation passed: {pack_path}")

        return errors

    def validate_manifest(self, manifest_path: str | Path) -> list[str]:
        """
        Validate a pack manifest file.

        Args:
            manifest_path: Path to manifest.json

        Returns:
            List of validation error messages
        """
        manifest_path = Path(manifest_path)
        errors = []

        # Check file exists
        if not manifest_path.exists():
            return [f"Manifest not found: {manifest_path}"]

        # Parse JSON
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return [f"Invalid JSON in manifest: {e}"]

        # Check required fields
        for field in self.REQUIRED_MANIFEST_FIELDS:
            if field not in data:
                errors.append(f"Missing required manifest field: {field}")

        # Validate field types
        if "id" in data and not isinstance(data["id"], str):
            errors.append("Manifest 'id' must be a string")

        if "name" in data and not isinstance(data["name"], str):
            errors.append("Manifest 'name' must be a string")

        if "version" in data:
            if not isinstance(data["version"], str):
                errors.append("Manifest 'version' must be a string")
            elif not self._validate_semver(data["version"]):
                errors.append(f"Invalid version format: {data['version']}")

        if "tags" in data and not isinstance(data["tags"], list):
            errors.append("Manifest 'tags' must be a list")

        return errors

    def validate_vulnerability(self, vuln_data: dict) -> list[str]:
        """
        Validate a vulnerability definition.

        Args:
            vuln_data: Vulnerability definition dictionary

        Returns:
            List of validation error messages
        """
        errors = []

        # Check required fields
        for field in self.REQUIRED_VULN_FIELDS:
            if field not in vuln_data:
                errors.append(f"Missing required vulnerability field: {field}")

        # Validate severity
        if "severity" in vuln_data:
            if vuln_data["severity"] not in self.VALID_SEVERITIES:
                errors.append(
                    f"Invalid severity: {vuln_data['severity']}. "
                    f"Must be one of: {self.VALID_SEVERITIES}"
                )

        # Validate detection rules
        if "detection_rules" in vuln_data:
            if not isinstance(vuln_data["detection_rules"], list):
                errors.append("detection_rules must be a list")
            else:
                for i, rule in enumerate(vuln_data["detection_rules"]):
                    rule_errors = self._validate_detection_rule(rule, i)
                    errors.extend(rule_errors)

        # Validate references
        if "references" in vuln_data:
            if not isinstance(vuln_data["references"], list):
                errors.append("references must be a list")

        # Validate CVE IDs
        if "cve_ids" in vuln_data:
            if not isinstance(vuln_data["cve_ids"], list):
                errors.append("cve_ids must be a list")
            else:
                for cve in vuln_data["cve_ids"]:
                    if not self._validate_cve_format(cve):
                        errors.append(f"Invalid CVE format: {cve}")

        return errors

    def validate_vulnerabilities_dir(self, vuln_dir: str | Path) -> list[str]:
        """
        Validate all vulnerability definitions in a directory.

        Args:
            vuln_dir: Path to vulnerabilities directory

        Returns:
            List of validation error messages
        """
        vuln_dir = Path(vuln_dir)
        errors = []

        if not vuln_dir.exists():
            return []  # Optional directory

        for vuln_file in vuln_dir.glob("*.json"):
            try:
                with open(vuln_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                file_errors = self.validate_vulnerability(data)
                errors.extend([f"{vuln_file.name}: {e}" for e in file_errors])

            except json.JSONDecodeError as e:
                errors.append(f"{vuln_file.name}: Invalid JSON - {e}")

        return errors

    def _validate_detection_rule(self, rule: dict, index: int) -> list[str]:
        """
        Validate a detection rule.

        Args:
            rule: Detection rule dictionary
            index: Rule index for error messages

        Returns:
            List of validation error messages
        """
        errors = []
        prefix = f"detection_rules[{index}]"

        if not isinstance(rule, dict):
            return [f"{prefix}: must be an object"]

        if "type" not in rule:
            errors.append(f"{prefix}: missing 'type' field")
        elif rule["type"] not in ["port", "service", "banner", "pattern"]:
            errors.append(
                f"{prefix}: invalid type '{rule['type']}'. "
                "Must be: port, service, banner, or pattern"
            )

        # Type-specific validation
        if rule.get("type") == "port" and "port" not in rule:
            errors.append(f"{prefix}: port rule must specify 'port'")

        if rule.get("type") == "service" and "service" not in rule:
            errors.append(f"{prefix}: service rule must specify 'service'")

        if rule.get("type") == "pattern" and "pattern" not in rule:
            errors.append(f"{prefix}: pattern rule must specify 'pattern'")

        return errors

    def _validate_semver(self, version: str) -> bool:
        """
        Validate semantic version format.

        Args:
            version: Version string (e.g., "1.0.0")

        Returns:
            True if valid semver format
        """
        import re
        pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?(\+[a-zA-Z0-9.]+)?$"
        return bool(re.match(pattern, version))

    def _validate_cve_format(self, cve: str) -> bool:
        """
        Validate CVE ID format.

        Args:
            cve: CVE identifier (e.g., "CVE-2024-12345")

        Returns:
            True if valid CVE format
        """
        import re
        pattern = r"^CVE-\d{4}-\d{4,}$"
        return bool(re.match(pattern, cve))

    def create_validation_report(self, pack_path: str | Path) -> dict:
        """
        Create a detailed validation report for a pack.

        Args:
            pack_path: Path to the pack directory

        Returns:
            Dictionary with validation results and statistics
        """
        pack_path = Path(pack_path)
        errors = self.validate_pack(pack_path)

        # Count items
        vuln_count = 0
        vuln_dir = pack_path / "vulnerabilities"
        if vuln_dir.exists():
            vuln_count = len(list(vuln_dir.glob("*.json")))

        return {
            "pack_path": str(pack_path),
            "valid": len(errors) == 0,
            "error_count": len(errors),
            "errors": errors,
            "vulnerability_count": vuln_count,
            "has_manifest": (pack_path / "manifest.json").exists(),
        }

"""
Content pack loader.

This module provides functionality to load content packs from the filesystem,
parse their contents, and make them available for use in the application.
"""

import json
from pathlib import Path
from typing import Optional

from app.core.logging import get_logger
from app.config import settings
from app.services.packs.models import (
    PackManifest,
    VulnerabilityDefinition,
    RemediationGuide,
    ContentPack,
)
from app.services.packs.validator import PackValidator, PackValidationError

logger = get_logger("packs")


class PackLoadError(Exception):
    """
    Exception raised when pack loading fails.

    Attributes:
        message: Error description
        pack_id: ID of the pack that failed to load
    """

    def __init__(self, message: str, pack_id: Optional[str] = None):
        self.message = message
        self.pack_id = pack_id
        super().__init__(self.message)


class PackLoader:
    """
    Loads content packs from the filesystem.

    This class handles:
    - Discovering packs in the packs directory
    - Loading and parsing pack manifests
    - Loading vulnerability definitions
    - Loading remediation guides

    Example:
        >>> loader = PackLoader()
        >>> pack = loader.load_pack("core")
        >>> print(f"Loaded {len(pack.vulnerabilities)} vulnerabilities")
    """

    def __init__(
        self,
        packs_dir: Optional[Path] = None,
        validate: bool = True,
    ):
        """
        Initialize the pack loader.

        Args:
            packs_dir: Directory containing packs (defaults to settings)
            validate: Whether to validate packs before loading
        """
        self.packs_dir = Path(packs_dir or settings.packs_dir)
        self.validate = validate
        self._validator = PackValidator() if validate else None

        logger.info(f"PackLoader initialized. Packs directory: {self.packs_dir}")

    def discover_packs(self) -> list[str]:
        """
        Discover available packs in the packs directory.

        Returns:
            List of pack IDs (directory names)
        """
        if not self.packs_dir.exists():
            logger.warning(f"Packs directory not found: {self.packs_dir}")
            return []

        packs = []
        for item in self.packs_dir.iterdir():
            if item.is_dir() and (item / "manifest.json").exists():
                packs.append(item.name)

        logger.info(f"Discovered {len(packs)} packs: {packs}")
        return packs

    def load_pack(self, pack_id: str) -> ContentPack:
        """
        Load a content pack by ID.

        Args:
            pack_id: Pack identifier (directory name)

        Returns:
            Loaded ContentPack object

        Raises:
            PackLoadError: If pack cannot be loaded
            PackValidationError: If validation is enabled and fails
        """
        pack_path = self.packs_dir / pack_id

        logger.info(f"Loading pack: {pack_id}")

        # Check pack exists
        if not pack_path.exists():
            raise PackLoadError(f"Pack not found: {pack_id}", pack_id)

        # Validate if enabled
        if self._validator:
            errors = self._validator.validate_pack(pack_path)
            if errors:
                raise PackValidationError(
                    f"Pack validation failed: {pack_id}",
                    pack_path=str(pack_path),
                    errors=errors,
                )

        # Load manifest
        manifest = self._load_manifest(pack_path)

        # Create pack object
        pack = ContentPack(
            manifest=manifest,
            path=str(pack_path),
        )

        # Load vulnerabilities
        pack.vulnerabilities = self._load_vulnerabilities(pack_path)

        # Load remediation guides
        pack.remediation_guides = self._load_remediation_guides(pack_path)

        logger.info(
            f"Pack loaded: {pack_id} - "
            f"{len(pack.vulnerabilities)} vulnerabilities, "
            f"{len(pack.remediation_guides)} remediation guides"
        )

        return pack

    def _load_manifest(self, pack_path: Path) -> PackManifest:
        """
        Load pack manifest.

        Args:
            pack_path: Path to pack directory

        Returns:
            PackManifest object
        """
        manifest_path = pack_path / "manifest.json"

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return PackManifest.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            raise PackLoadError(f"Failed to load manifest: {e}")

    def _load_vulnerabilities(
        self,
        pack_path: Path,
    ) -> dict[str, VulnerabilityDefinition]:
        """
        Load vulnerability definitions from a pack.

        Args:
            pack_path: Path to pack directory

        Returns:
            Dictionary mapping vuln IDs to definitions
        """
        vuln_dir = pack_path / "vulnerabilities"
        vulnerabilities = {}

        if not vuln_dir.exists():
            logger.debug(f"No vulnerabilities directory in {pack_path}")
            return vulnerabilities

        for vuln_file in vuln_dir.glob("*.json"):
            try:
                with open(vuln_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                vuln = VulnerabilityDefinition.from_dict(data)
                vulnerabilities[vuln.id] = vuln
                logger.debug(f"Loaded vulnerability: {vuln.id}")

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load {vuln_file}: {e}")

        return vulnerabilities

    def _load_remediation_guides(
        self,
        pack_path: Path,
    ) -> dict[str, RemediationGuide]:
        """
        Load remediation guides from a pack.

        Args:
            pack_path: Path to pack directory

        Returns:
            Dictionary mapping vuln IDs to guides
        """
        knowledge_dir = pack_path / "knowledge"
        guides = {}

        if not knowledge_dir.exists():
            logger.debug(f"No knowledge directory in {pack_path}")
            return guides

        # Load from remediation_guides.json if it exists
        guides_file = knowledge_dir / "remediation_guides.json"
        if guides_file.exists():
            try:
                with open(guides_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Handle both list and dict formats
                if isinstance(data, list):
                    for item in data:
                        guide = RemediationGuide.from_dict(item)
                        guides[guide.vuln_id] = guide
                elif isinstance(data, dict):
                    if "guides" in data:
                        for item in data["guides"]:
                            guide = RemediationGuide.from_dict(item)
                            guides[guide.vuln_id] = guide

                logger.debug(f"Loaded {len(guides)} remediation guides")

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load remediation guides: {e}")

        return guides

    def load_all_packs(self) -> list[ContentPack]:
        """
        Load all discovered packs.

        Returns:
            List of loaded ContentPack objects
        """
        packs = []
        pack_ids = self.discover_packs()

        for pack_id in pack_ids:
            try:
                pack = self.load_pack(pack_id)
                packs.append(pack)
            except (PackLoadError, PackValidationError) as e:
                logger.error(f"Failed to load pack {pack_id}: {e}")

        return packs

    def get_vulnerability(
        self,
        vuln_id: str,
        pack_id: Optional[str] = None,
    ) -> Optional[VulnerabilityDefinition]:
        """
        Get a vulnerability definition by ID.

        If pack_id is not specified, searches all packs.

        Args:
            vuln_id: Vulnerability identifier
            pack_id: Optional specific pack to search

        Returns:
            VulnerabilityDefinition or None if not found
        """
        if pack_id:
            try:
                pack = self.load_pack(pack_id)
                return pack.get_vulnerability(vuln_id)
            except PackLoadError:
                return None

        # Search all packs
        for pid in self.discover_packs():
            try:
                pack = self.load_pack(pid)
                vuln = pack.get_vulnerability(vuln_id)
                if vuln:
                    return vuln
            except PackLoadError:
                continue

        return None

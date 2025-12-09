"""
Content pack registry.

This module provides a singleton registry for managing loaded content packs,
allowing efficient access to vulnerability definitions and other pack content.
"""

from typing import Optional

from app.core.logging import get_logger
from app.services.packs.loader import PackLoader
from app.services.packs.models import (
    ContentPack,
    VulnerabilityDefinition,
    RemediationGuide,
    Severity,
)

logger = get_logger("packs")


class PackRegistry:
    """
    Central registry for content packs.

    This class maintains a cache of loaded packs and provides methods
    for accessing vulnerability definitions across all packs.

    Example:
        >>> registry = PackRegistry()
        >>> registry.load_all()
        >>> vuln = registry.get_vulnerability("default_credentials")
        >>> print(vuln.title)
    """

    def __init__(self):
        """Initialize the pack registry."""
        self._loader = PackLoader()
        self._packs: dict[str, ContentPack] = {}
        self._vuln_index: dict[str, tuple[str, VulnerabilityDefinition]] = {}
        self._loaded = False

        logger.info("PackRegistry initialized")

    def load_all(self, reload: bool = False) -> int:
        """
        Load all available packs.

        Args:
            reload: Force reload even if already loaded

        Returns:
            Number of packs loaded
        """
        if self._loaded and not reload:
            logger.debug("Packs already loaded, skipping")
            return len(self._packs)

        logger.info("Loading all content packs...")

        # Clear existing data
        self._packs.clear()
        self._vuln_index.clear()

        # Load packs
        packs = self._loader.load_all_packs()

        for pack in packs:
            self._packs[pack.manifest.id] = pack

            # Index vulnerabilities
            for vuln_id, vuln in pack.vulnerabilities.items():
                self._vuln_index[vuln_id] = (pack.manifest.id, vuln)

        self._loaded = True

        logger.info(
            f"Loaded {len(self._packs)} packs with "
            f"{len(self._vuln_index)} total vulnerabilities"
        )

        return len(self._packs)

    def get_pack(self, pack_id: str) -> Optional[ContentPack]:
        """
        Get a pack by ID.

        Args:
            pack_id: Pack identifier

        Returns:
            ContentPack or None if not found
        """
        if not self._loaded:
            self.load_all()

        return self._packs.get(pack_id)

    def list_packs(self) -> list[ContentPack]:
        """
        Get all loaded packs.

        Returns:
            List of ContentPack objects
        """
        if not self._loaded:
            self.load_all()

        return list(self._packs.values())

    def get_vulnerability(
        self,
        vuln_id: str,
    ) -> Optional[VulnerabilityDefinition]:
        """
        Get a vulnerability definition by ID from any pack.

        Args:
            vuln_id: Vulnerability identifier

        Returns:
            VulnerabilityDefinition or None if not found
        """
        if not self._loaded:
            self.load_all()

        if vuln_id in self._vuln_index:
            return self._vuln_index[vuln_id][1]

        return None

    def get_remediation(self, vuln_id: str) -> Optional[RemediationGuide]:
        """
        Get a remediation guide by vulnerability ID.

        Args:
            vuln_id: Vulnerability identifier

        Returns:
            RemediationGuide or None if not found
        """
        if not self._loaded:
            self.load_all()

        # Find which pack has this vulnerability
        if vuln_id in self._vuln_index:
            pack_id = self._vuln_index[vuln_id][0]
            pack = self._packs.get(pack_id)
            if pack:
                return pack.get_remediation(vuln_id)

        return None

    def list_vulnerabilities(
        self,
        severity: Optional[Severity] = None,
        pack_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> list[VulnerabilityDefinition]:
        """
        List vulnerability definitions with optional filtering.

        Args:
            severity: Filter by severity level
            pack_id: Filter by pack
            tags: Filter by tags (any match)

        Returns:
            List of matching VulnerabilityDefinition objects
        """
        if not self._loaded:
            self.load_all()

        results = []

        # Get vulnerabilities from specified pack or all packs
        if pack_id:
            pack = self._packs.get(pack_id)
            if pack:
                results = list(pack.vulnerabilities.values())
        else:
            results = [vuln for _, vuln in self._vuln_index.values()]

        # Filter by severity
        if severity:
            results = [v for v in results if v.severity == severity]

        # Filter by tags
        if tags:
            tag_set = set(tags)
            results = [v for v in results if tag_set & set(v.tags)]

        return results

    def search_vulnerabilities(
        self,
        query: str,
    ) -> list[VulnerabilityDefinition]:
        """
        Search vulnerabilities by text query.

        Searches in title, description, and ID.

        Args:
            query: Search text

        Returns:
            List of matching VulnerabilityDefinition objects
        """
        if not self._loaded:
            self.load_all()

        query = query.lower()
        results = []

        for _, vuln in self._vuln_index.values():
            if (
                query in vuln.id.lower()
                or query in vuln.title.lower()
                or query in vuln.description.lower()
            ):
                results.append(vuln)

        return results

    def get_statistics(self) -> dict:
        """
        Get statistics about loaded packs.

        Returns:
            Dictionary with pack statistics
        """
        if not self._loaded:
            self.load_all()

        severity_counts = {}
        for sev in Severity:
            count = len(self.list_vulnerabilities(severity=sev))
            severity_counts[sev.value] = count

        return {
            "pack_count": len(self._packs),
            "vulnerability_count": len(self._vuln_index),
            "vulnerabilities_by_severity": severity_counts,
            "packs": [
                {
                    "id": pack.manifest.id,
                    "name": pack.manifest.name,
                    "version": pack.manifest.version,
                    "vulnerabilities": len(pack.vulnerabilities),
                }
                for pack in self._packs.values()
            ],
        }


# Singleton instance
_registry: Optional[PackRegistry] = None


def get_pack_registry() -> PackRegistry:
    """
    Get the global PackRegistry instance.

    This provides a singleton registry for the application.

    Returns:
        PackRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = PackRegistry()
    return _registry

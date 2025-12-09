"""
Data models for content packs.

This module defines the data structures used in content packs,
including vulnerability definitions, remediation guides, and pack manifests.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class Severity(str, Enum):
    """Vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class PackManifest:
    """
    Metadata for a content pack.

    This defines the structure of manifest.json files in each pack.

    Attributes:
        id: Unique identifier for the pack
        name: Human-readable name
        version: Semantic version string
        description: Brief description of the pack
        author: Pack author name
        license: License type
        requires_core: Minimum core version required
        vulnerabilities_count: Number of vulnerability definitions
        scenarios_count: Number of scenarios (optional)
        tags: Categorization tags
    """
    id: str
    name: str
    version: str
    description: str
    author: str = "CyberSec Teaching Tool"
    license: str = "MIT"
    requires_core: str = ">=0.1.0"
    vulnerabilities_count: int = 0
    scenarios_count: int = 0
    tags: list[str] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert manifest to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "requires_core": self.requires_core,
            "vulnerabilities_count": self.vulnerabilities_count,
            "scenarios_count": self.scenarios_count,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PackManifest":
        """Create manifest from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            author=data.get("author", "Unknown"),
            license=data.get("license", "MIT"),
            requires_core=data.get("requires_core", ">=0.1.0"),
            vulnerabilities_count=data.get("vulnerabilities_count", 0),
            scenarios_count=data.get("scenarios_count", 0),
            tags=data.get("tags", []),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


@dataclass
class DetectionRule:
    """
    Rule for detecting a vulnerability.

    Attributes:
        type: Detection method (port, service, banner, pattern)
        port: Port number to check
        service: Service name to match
        pattern: Regex pattern to match in banner/response
        condition: Condition type (exists, equals, matches)
    """
    type: str  # "port", "service", "banner", "pattern"
    port: Optional[int] = None
    service: Optional[str] = None
    pattern: Optional[str] = None
    condition: str = "exists"  # "exists", "equals", "matches"

    def to_dict(self) -> dict:
        """Convert rule to dictionary."""
        return {
            "type": self.type,
            "port": self.port,
            "service": self.service,
            "pattern": self.pattern,
            "condition": self.condition,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DetectionRule":
        """Create rule from dictionary."""
        return cls(
            type=data["type"],
            port=data.get("port"),
            service=data.get("service"),
            pattern=data.get("pattern"),
            condition=data.get("condition", "exists"),
        )


@dataclass
class VulnerabilityDefinition:
    """
    Definition of a vulnerability type.

    This defines how to detect a vulnerability and provides information
    for educating users about it.

    Attributes:
        id: Unique identifier (e.g., "default_credentials")
        title: Human-readable title
        severity: Severity level
        description: Detailed description
        detection_rules: Rules for detecting this vulnerability
        affected_device_types: Device types this applies to
        affected_services: Services that may be affected
        remediation: Steps to fix the vulnerability
        references: External reference URLs
        cve_ids: Related CVE identifiers
        mitre_attack: Related MITRE ATT&CK techniques
        tags: Categorization tags
    """
    id: str
    title: str
    severity: Severity
    description: str
    detection_rules: list[DetectionRule] = field(default_factory=list)
    affected_device_types: list[str] = field(default_factory=list)
    affected_services: list[str] = field(default_factory=list)
    remediation: str = ""
    references: list[str] = field(default_factory=list)
    cve_ids: list[str] = field(default_factory=list)
    mitre_attack: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert definition to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "severity": self.severity.value,
            "description": self.description,
            "detection_rules": [r.to_dict() for r in self.detection_rules],
            "affected_device_types": self.affected_device_types,
            "affected_services": self.affected_services,
            "remediation": self.remediation,
            "references": self.references,
            "cve_ids": self.cve_ids,
            "mitre_attack": self.mitre_attack,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VulnerabilityDefinition":
        """Create definition from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            severity=Severity(data["severity"]),
            description=data.get("description", ""),
            detection_rules=[
                DetectionRule.from_dict(r)
                for r in data.get("detection_rules", [])
            ],
            affected_device_types=data.get("affected_device_types", []),
            affected_services=data.get("affected_services", []),
            remediation=data.get("remediation", ""),
            references=data.get("references", []),
            cve_ids=data.get("cve_ids", []),
            mitre_attack=data.get("mitre_attack", []),
            tags=data.get("tags", []),
        )


@dataclass
class RemediationGuide:
    """
    Detailed remediation guide for a vulnerability.

    Attributes:
        vuln_id: ID of the related vulnerability
        title: Guide title
        difficulty: Difficulty level (easy, medium, hard)
        time_estimate: Estimated time to complete
        steps: Step-by-step instructions
        prerequisites: Required knowledge or tools
        verification: How to verify the fix worked
        common_mistakes: Common errors to avoid
    """
    vuln_id: str
    title: str
    difficulty: str = "medium"  # easy, medium, hard
    time_estimate: str = "5-10 minutes"
    steps: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    verification: str = ""
    common_mistakes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert guide to dictionary."""
        return {
            "vuln_id": self.vuln_id,
            "title": self.title,
            "difficulty": self.difficulty,
            "time_estimate": self.time_estimate,
            "steps": self.steps,
            "prerequisites": self.prerequisites,
            "verification": self.verification,
            "common_mistakes": self.common_mistakes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RemediationGuide":
        """Create guide from dictionary."""
        return cls(
            vuln_id=data["vuln_id"],
            title=data.get("title", ""),
            difficulty=data.get("difficulty", "medium"),
            time_estimate=data.get("time_estimate", "5-10 minutes"),
            steps=data.get("steps", []),
            prerequisites=data.get("prerequisites", []),
            verification=data.get("verification", ""),
            common_mistakes=data.get("common_mistakes", []),
        )


@dataclass
class ContentPack:
    """
    A loaded content pack with all its data.

    Attributes:
        manifest: Pack manifest
        vulnerabilities: Loaded vulnerability definitions
        remediation_guides: Loaded remediation guides
        path: Filesystem path to the pack
    """
    manifest: PackManifest
    vulnerabilities: dict[str, VulnerabilityDefinition] = field(default_factory=dict)
    remediation_guides: dict[str, RemediationGuide] = field(default_factory=dict)
    path: str = ""

    def get_vulnerability(self, vuln_id: str) -> Optional[VulnerabilityDefinition]:
        """Get a vulnerability definition by ID."""
        return self.vulnerabilities.get(vuln_id)

    def get_remediation(self, vuln_id: str) -> Optional[RemediationGuide]:
        """Get a remediation guide by vulnerability ID."""
        return self.remediation_guides.get(vuln_id)

    def list_vulnerabilities(self) -> list[VulnerabilityDefinition]:
        """Get all vulnerability definitions."""
        return list(self.vulnerabilities.values())

    def list_by_severity(self, severity: Severity) -> list[VulnerabilityDefinition]:
        """Get vulnerabilities filtered by severity."""
        return [v for v in self.vulnerabilities.values() if v.severity == severity]

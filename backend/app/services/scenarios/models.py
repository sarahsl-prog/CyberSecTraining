"""
Scenario data models.

Defines the data structures for educational cybersecurity scenarios.
"""

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DifficultyLevel(str, Enum):
    """Difficulty levels for scenarios."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ScenarioVulnerability(BaseModel):
    """
    A vulnerability within a scenario.

    Attributes:
        vuln_type: Type of vulnerability (e.g., 'default_credentials')
        severity: Severity level (critical, high, medium, low, info)
        service: Affected service name
        port: Affected port number
        hint: Optional hint for finding this vulnerability
    """

    vuln_type: str = Field(description="Vulnerability type identifier")
    severity: str = Field(description="Severity level")
    service: Optional[str] = Field(default=None, description="Affected service")
    port: Optional[int] = Field(default=None, description="Affected port")
    hint: Optional[str] = Field(default=None, description="Hint for finding this vulnerability")


class ScenarioDevice(BaseModel):
    """
    A simulated device within a scenario.

    Attributes:
        id: Unique device identifier within the scenario
        hostname: Device hostname
        ip: IP address
        device_type: Type of device (router, computer, etc.)
        os: Operating system
        open_ports: List of open ports
        vulnerabilities: List of vulnerabilities on this device
        is_gateway: Whether this is the network gateway
    """

    id: str = Field(description="Device identifier")
    hostname: str = Field(description="Device hostname")
    ip: str = Field(description="IP address")
    device_type: str = Field(default="computer", description="Device type")
    os: Optional[str] = Field(default=None, description="Operating system")
    open_ports: list[int] = Field(default_factory=list, description="Open ports")
    vulnerabilities: list[ScenarioVulnerability] = Field(
        default_factory=list,
        description="Device vulnerabilities"
    )
    is_gateway: bool = Field(default=False, description="Is network gateway")


class ScenarioMetadata(BaseModel):
    """
    Scenario metadata for display and filtering.

    Attributes:
        author: Scenario author
        created_at: Creation date
        updated_at: Last update date
        version: Scenario version
        tags: List of tags for categorization
        estimated_time: Estimated completion time in minutes
        prerequisites: Required knowledge or completed scenarios
    """

    author: str = Field(default="CyberSec Teaching Tool", description="Scenario author")
    created_at: Optional[str] = Field(default=None, description="Creation date")
    updated_at: Optional[str] = Field(default=None, description="Last update date")
    version: str = Field(default="1.0.0", description="Scenario version")
    tags: list[str] = Field(default_factory=list, description="Tags for filtering")
    estimated_time: Optional[int] = Field(
        default=None,
        description="Estimated completion time in minutes"
    )
    prerequisites: list[str] = Field(
        default_factory=list,
        description="Prerequisite scenario IDs"
    )


class Scenario(BaseModel):
    """
    A complete educational scenario.

    A scenario presents a simulated network environment with devices
    and vulnerabilities for users to discover and remediate.

    Attributes:
        id: Unique scenario identifier
        pack_id: ID of the content pack this scenario belongs to
        name: Display name
        description: Detailed description
        difficulty: Difficulty level
        learning_objectives: List of learning objectives
        devices: Simulated network devices
        metadata: Additional metadata
        success_criteria: Criteria for completing the scenario
    """

    id: str = Field(description="Unique scenario identifier")
    pack_id: str = Field(description="Parent pack ID")
    name: str = Field(description="Display name")
    description: str = Field(description="Detailed description")
    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.BEGINNER,
        description="Difficulty level"
    )
    learning_objectives: list[str] = Field(
        default_factory=list,
        description="What users will learn"
    )
    devices: list[ScenarioDevice] = Field(
        default_factory=list,
        description="Network devices"
    )
    metadata: ScenarioMetadata = Field(
        default_factory=ScenarioMetadata,
        description="Scenario metadata"
    )
    success_criteria: dict = Field(
        default_factory=dict,
        description="Criteria for scenario completion"
    )

    @property
    def total_vulnerabilities(self) -> int:
        """Count total vulnerabilities across all devices."""
        return sum(len(d.vulnerabilities) for d in self.devices)

    @property
    def device_count(self) -> int:
        """Count devices in the scenario."""
        return len(self.devices)


class ScenarioProgress(BaseModel):
    """
    User progress on a scenario.

    Attributes:
        scenario_id: The scenario being tracked
        user_id: User identifier (default 'local' for single-user)
        started_at: When the user started the scenario
        completed_at: When the user completed the scenario
        vulns_found: Number of vulnerabilities found
        vulns_fixed: Number of vulnerabilities remediated
        score: Score achieved (0-100)
        attempts: Number of attempts
    """

    scenario_id: str = Field(description="Scenario identifier")
    user_id: str = Field(default="local", description="User identifier")
    started_at: Optional[datetime] = Field(default=None, description="Start time")
    completed_at: Optional[datetime] = Field(default=None, description="Completion time")
    vulns_found: int = Field(default=0, description="Vulnerabilities found")
    vulns_fixed: int = Field(default=0, description="Vulnerabilities fixed")
    score: int = Field(default=0, ge=0, le=100, description="Score (0-100)")
    attempts: int = Field(default=0, description="Number of attempts")

    @property
    def is_completed(self) -> bool:
        """Check if scenario is completed."""
        return self.completed_at is not None

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage based on vulns fixed."""
        # This would be calculated based on total vulns in scenario
        return self.score


class ScenarioSummary(BaseModel):
    """
    Summary information for scenario listing.

    Lighter weight than full Scenario for list views.
    """

    id: str
    pack_id: str
    name: str
    description: str
    difficulty: DifficultyLevel
    device_count: int
    vulnerability_count: int
    estimated_time: Optional[int] = None
    tags: list[str] = Field(default_factory=list)
    is_completed: bool = False
    best_score: Optional[int] = None

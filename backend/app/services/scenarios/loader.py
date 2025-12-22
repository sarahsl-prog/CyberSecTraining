"""
Scenario loader service.

Loads and manages educational scenarios from content packs.
"""

import json
from pathlib import Path
from typing import Optional

from app.config import settings
from app.core.logging import get_logger
from .models import (
    Scenario,
    ScenarioDevice,
    ScenarioVulnerability,
    ScenarioMetadata,
    ScenarioSummary,
    DifficultyLevel,
)

logger = get_logger("scenarios")


class ScenarioLoader:
    """
    Service for loading and managing scenarios from content packs.

    Scenarios are stored as JSON files within content pack directories.
    Each pack can contain multiple scenarios in its 'scenarios/' subdirectory.
    """

    def __init__(self, packs_dir: Optional[Path] = None):
        """
        Initialize the scenario loader.

        Args:
            packs_dir: Path to the packs directory. Defaults to settings.packs_dir.
        """
        self.packs_dir = Path(packs_dir) if packs_dir else Path(settings.packs_dir)
        self._scenarios_cache: dict[str, Scenario] = {}
        self._initialized = False

        logger.info(f"ScenarioLoader initialized with packs_dir: {self.packs_dir}")

    def _ensure_initialized(self) -> None:
        """Load all scenarios if not already initialized."""
        if not self._initialized:
            self.reload()

    def reload(self) -> int:
        """
        Reload all scenarios from disk.

        Returns:
            Number of scenarios loaded
        """
        self._scenarios_cache.clear()
        count = 0

        if not self.packs_dir.exists():
            logger.warning(f"Packs directory does not exist: {self.packs_dir}")
            self._initialized = True
            return 0

        # Iterate through each pack directory
        for pack_dir in self.packs_dir.iterdir():
            if not pack_dir.is_dir():
                continue

            scenarios_dir = pack_dir / "scenarios"
            if not scenarios_dir.exists():
                continue

            pack_id = pack_dir.name
            logger.debug(f"Loading scenarios from pack: {pack_id}")

            # Load each scenario file
            for scenario_file in scenarios_dir.glob("*.json"):
                try:
                    scenario = self._load_scenario_file(scenario_file, pack_id)
                    if scenario:
                        self._scenarios_cache[scenario.id] = scenario
                        count += 1
                        logger.debug(f"Loaded scenario: {scenario.id}")
                except Exception as e:
                    logger.error(f"Failed to load scenario {scenario_file}: {e}")

        self._initialized = True
        logger.info(f"Loaded {count} scenarios from {len(list(self.packs_dir.iterdir()))} packs")
        return count

    def _load_scenario_file(self, file_path: Path, pack_id: str) -> Optional[Scenario]:
        """
        Load a scenario from a JSON file.

        Args:
            file_path: Path to the scenario JSON file
            pack_id: ID of the parent pack

        Returns:
            Scenario if successful, None otherwise
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Parse devices and vulnerabilities
            devices = []
            for device_data in data.get("devices", []):
                vulns = [
                    ScenarioVulnerability(**v)
                    for v in device_data.get("vulnerabilities", [])
                ]
                device = ScenarioDevice(
                    id=device_data.get("id", ""),
                    hostname=device_data.get("hostname", "unknown"),
                    ip=device_data.get("ip", "0.0.0.0"),
                    device_type=device_data.get("device_type", "computer"),
                    os=device_data.get("os"),
                    open_ports=device_data.get("open_ports", []),
                    vulnerabilities=vulns,
                    is_gateway=device_data.get("is_gateway", False),
                )
                devices.append(device)

            # Parse metadata
            meta_data = data.get("metadata", {})
            metadata = ScenarioMetadata(
                author=meta_data.get("author", "Unknown"),
                created_at=meta_data.get("created_at"),
                updated_at=meta_data.get("updated_at"),
                version=meta_data.get("version", "1.0.0"),
                tags=meta_data.get("tags", []),
                estimated_time=meta_data.get("estimated_time"),
                prerequisites=meta_data.get("prerequisites", []),
            )

            # Parse difficulty
            difficulty_str = data.get("difficulty", "beginner").lower()
            try:
                difficulty = DifficultyLevel(difficulty_str)
            except ValueError:
                difficulty = DifficultyLevel.BEGINNER

            # Create scenario
            scenario = Scenario(
                id=data.get("id", file_path.stem),
                pack_id=pack_id,
                name=data.get("name", file_path.stem),
                description=data.get("description", ""),
                difficulty=difficulty,
                learning_objectives=data.get("learning_objectives", []),
                devices=devices,
                metadata=metadata,
                success_criteria=data.get("success_criteria", {}),
            )

            return scenario

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None

    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """
        Get a scenario by ID.

        Args:
            scenario_id: The scenario identifier

        Returns:
            Scenario if found, None otherwise
        """
        self._ensure_initialized()
        return self._scenarios_cache.get(scenario_id)

    def list_scenarios(
        self,
        pack_id: Optional[str] = None,
        difficulty: Optional[DifficultyLevel] = None,
        tag: Optional[str] = None,
    ) -> list[ScenarioSummary]:
        """
        List scenarios with optional filtering.

        Args:
            pack_id: Filter by pack ID
            difficulty: Filter by difficulty level
            tag: Filter by tag

        Returns:
            List of scenario summaries
        """
        self._ensure_initialized()

        summaries = []
        for scenario in self._scenarios_cache.values():
            # Apply filters
            if pack_id and scenario.pack_id != pack_id:
                continue
            if difficulty and scenario.difficulty != difficulty:
                continue
            if tag and tag not in scenario.metadata.tags:
                continue

            summary = ScenarioSummary(
                id=scenario.id,
                pack_id=scenario.pack_id,
                name=scenario.name,
                description=scenario.description,
                difficulty=scenario.difficulty,
                device_count=scenario.device_count,
                vulnerability_count=scenario.total_vulnerabilities,
                estimated_time=scenario.metadata.estimated_time,
                tags=scenario.metadata.tags,
                is_completed=False,  # Would be populated from progress data
                best_score=None,  # Would be populated from progress data
            )
            summaries.append(summary)

        # Sort by difficulty, then name
        difficulty_order = {
            DifficultyLevel.BEGINNER: 0,
            DifficultyLevel.INTERMEDIATE: 1,
            DifficultyLevel.ADVANCED: 2,
            DifficultyLevel.EXPERT: 3,
        }
        summaries.sort(key=lambda s: (difficulty_order.get(s.difficulty, 0), s.name))

        return summaries

    def list_packs(self) -> list[dict]:
        """
        List all available content packs with scenario counts.

        Returns:
            List of pack information dictionaries
        """
        self._ensure_initialized()

        packs: dict[str, dict] = {}

        for scenario in self._scenarios_cache.values():
            if scenario.pack_id not in packs:
                # Try to load pack manifest
                manifest_path = self.packs_dir / scenario.pack_id / "manifest.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            manifest = json.load(f)
                        packs[scenario.pack_id] = {
                            "id": scenario.pack_id,
                            "name": manifest.get("name", scenario.pack_id),
                            "description": manifest.get("description", ""),
                            "version": manifest.get("version", "1.0.0"),
                            "scenario_count": 0,
                        }
                    except Exception as e:
                        logger.warning(f"Failed to load manifest for {scenario.pack_id}: {e}")
                        packs[scenario.pack_id] = {
                            "id": scenario.pack_id,
                            "name": scenario.pack_id,
                            "description": "",
                            "version": "unknown",
                            "scenario_count": 0,
                        }
                else:
                    packs[scenario.pack_id] = {
                        "id": scenario.pack_id,
                        "name": scenario.pack_id,
                        "description": "",
                        "version": "unknown",
                        "scenario_count": 0,
                    }

            packs[scenario.pack_id]["scenario_count"] += 1

        return list(packs.values())

    def get_tags(self) -> list[str]:
        """
        Get all unique tags across scenarios.

        Returns:
            Sorted list of unique tags
        """
        self._ensure_initialized()

        tags = set()
        for scenario in self._scenarios_cache.values():
            tags.update(scenario.metadata.tags)

        return sorted(tags)

    @property
    def scenario_count(self) -> int:
        """Get total number of loaded scenarios."""
        self._ensure_initialized()
        return len(self._scenarios_cache)


# Singleton instance
_scenario_loader: Optional[ScenarioLoader] = None


def get_scenario_loader() -> ScenarioLoader:
    """
    Get the singleton scenario loader instance.

    Returns:
        The global ScenarioLoader instance
    """
    global _scenario_loader

    if _scenario_loader is None:
        _scenario_loader = ScenarioLoader()

    return _scenario_loader

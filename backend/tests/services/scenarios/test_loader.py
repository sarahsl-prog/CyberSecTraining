"""
Tests for the scenario loader service.
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.services.scenarios.loader import ScenarioLoader
from app.services.scenarios.models import (
    DifficultyLevel,
    Scenario,
    ScenarioSummary,
)


@pytest.fixture
def temp_packs_dir():
    """Create a temporary packs directory with test scenarios."""
    with TemporaryDirectory() as tmpdir:
        packs_dir = Path(tmpdir)

        # Create test pack
        pack_dir = packs_dir / "test-pack"
        scenarios_dir = pack_dir / "scenarios"
        scenarios_dir.mkdir(parents=True)

        # Create manifest
        manifest = {
            "id": "test-pack",
            "name": "Test Pack",
            "description": "A test content pack",
            "version": "1.0.0",
        }
        with open(pack_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)

        # Create test scenario
        scenario_data = {
            "id": "test-scenario-1",
            "name": "Test Scenario",
            "description": "A test scenario for unit testing",
            "difficulty": "beginner",
            "learning_objectives": ["Learn testing", "Understand scenarios"],
            "devices": [
                {
                    "id": "router-1",
                    "hostname": "test-router",
                    "ip": "192.168.1.1",
                    "device_type": "router",
                    "is_gateway": True,
                    "open_ports": [80, 443],
                    "vulnerabilities": [
                        {
                            "vuln_type": "default_credentials",
                            "severity": "high",
                            "service": "http",
                            "port": 80,
                        }
                    ],
                },
                {
                    "id": "computer-1",
                    "hostname": "test-pc",
                    "ip": "192.168.1.100",
                    "device_type": "computer",
                    "is_gateway": False,
                    "open_ports": [22],
                    "vulnerabilities": [],
                },
            ],
            "metadata": {
                "author": "Test Author",
                "tags": ["test", "beginner"],
                "estimated_time": 10,
            },
            "success_criteria": {
                "vulnerabilities_to_find": 1,
            },
        }
        with open(scenarios_dir / "test-scenario-1.json", "w") as f:
            json.dump(scenario_data, f)

        # Create second scenario with different difficulty
        scenario_data_2 = {
            "id": "test-scenario-2",
            "name": "Advanced Test Scenario",
            "description": "An advanced test scenario",
            "difficulty": "advanced",
            "learning_objectives": ["Advanced testing"],
            "devices": [
                {
                    "id": "server-1",
                    "hostname": "test-server",
                    "ip": "192.168.1.10",
                    "device_type": "server",
                    "vulnerabilities": [
                        {"vuln_type": "open_ssh", "severity": "medium"},
                        {"vuln_type": "open_database", "severity": "critical"},
                    ],
                }
            ],
            "metadata": {
                "tags": ["test", "advanced", "servers"],
                "estimated_time": 30,
            },
        }
        with open(scenarios_dir / "test-scenario-2.json", "w") as f:
            json.dump(scenario_data_2, f)

        yield packs_dir


@pytest.fixture
def loader(temp_packs_dir):
    """Create a scenario loader with the temp directory."""
    return ScenarioLoader(packs_dir=temp_packs_dir)


class TestScenarioLoader:
    """Tests for ScenarioLoader."""

    def test_reload_loads_scenarios(self, loader):
        """Reload should load scenarios from disk."""
        count = loader.reload()
        assert count == 2

    def test_get_scenario_returns_scenario(self, loader):
        """Should return a scenario by ID."""
        loader.reload()
        scenario = loader.get_scenario("test-scenario-1")

        assert scenario is not None
        assert scenario.id == "test-scenario-1"
        assert scenario.name == "Test Scenario"
        assert scenario.pack_id == "test-pack"

    def test_get_scenario_returns_none_for_missing(self, loader):
        """Should return None for non-existent scenario."""
        loader.reload()
        scenario = loader.get_scenario("non-existent")
        assert scenario is None

    def test_scenario_has_correct_devices(self, loader):
        """Scenario should have correctly parsed devices."""
        loader.reload()
        scenario = loader.get_scenario("test-scenario-1")

        assert scenario.device_count == 2
        assert scenario.devices[0].hostname == "test-router"
        assert scenario.devices[0].is_gateway is True
        assert scenario.devices[1].hostname == "test-pc"
        assert scenario.devices[1].is_gateway is False

    def test_scenario_has_vulnerabilities(self, loader):
        """Scenario should have correctly parsed vulnerabilities."""
        loader.reload()
        scenario = loader.get_scenario("test-scenario-1")

        assert scenario.total_vulnerabilities == 1
        assert scenario.devices[0].vulnerabilities[0].vuln_type == "default_credentials"
        assert scenario.devices[0].vulnerabilities[0].severity == "high"

    def test_scenario_has_metadata(self, loader):
        """Scenario should have metadata."""
        loader.reload()
        scenario = loader.get_scenario("test-scenario-1")

        assert scenario.metadata.author == "Test Author"
        assert "test" in scenario.metadata.tags
        assert scenario.metadata.estimated_time == 10

    def test_list_scenarios_returns_all(self, loader):
        """Should list all scenarios."""
        loader.reload()
        summaries = loader.list_scenarios()

        assert len(summaries) == 2
        assert all(isinstance(s, ScenarioSummary) for s in summaries)

    def test_list_scenarios_filter_by_difficulty(self, loader):
        """Should filter scenarios by difficulty."""
        loader.reload()

        beginner = loader.list_scenarios(difficulty=DifficultyLevel.BEGINNER)
        assert len(beginner) == 1
        assert beginner[0].id == "test-scenario-1"

        advanced = loader.list_scenarios(difficulty=DifficultyLevel.ADVANCED)
        assert len(advanced) == 1
        assert advanced[0].id == "test-scenario-2"

    def test_list_scenarios_filter_by_tag(self, loader):
        """Should filter scenarios by tag."""
        loader.reload()

        # Both have 'test' tag
        test_tagged = loader.list_scenarios(tag="test")
        assert len(test_tagged) == 2

        # Only one has 'servers' tag
        server_tagged = loader.list_scenarios(tag="servers")
        assert len(server_tagged) == 1
        assert server_tagged[0].id == "test-scenario-2"

    def test_list_scenarios_filter_by_pack(self, loader):
        """Should filter scenarios by pack ID."""
        loader.reload()

        pack_scenarios = loader.list_scenarios(pack_id="test-pack")
        assert len(pack_scenarios) == 2

        empty = loader.list_scenarios(pack_id="non-existent-pack")
        assert len(empty) == 0

    def test_list_packs(self, loader):
        """Should list available packs."""
        loader.reload()
        packs = loader.list_packs()

        assert len(packs) == 1
        assert packs[0]["id"] == "test-pack"
        assert packs[0]["name"] == "Test Pack"
        assert packs[0]["scenario_count"] == 2

    def test_get_tags(self, loader):
        """Should return all unique tags."""
        loader.reload()
        tags = loader.get_tags()

        assert "test" in tags
        assert "beginner" in tags
        assert "advanced" in tags
        assert "servers" in tags

    def test_scenario_count(self, loader):
        """Should return correct scenario count."""
        loader.reload()
        assert loader.scenario_count == 2

    def test_lazy_initialization(self, loader):
        """Should lazily initialize on first access."""
        # Don't call reload explicitly
        scenarios = loader.list_scenarios()
        assert len(scenarios) == 2

    def test_handles_empty_directory(self):
        """Should handle empty packs directory."""
        with TemporaryDirectory() as tmpdir:
            loader = ScenarioLoader(packs_dir=Path(tmpdir))
            count = loader.reload()
            assert count == 0
            assert loader.scenario_count == 0

    def test_handles_invalid_json(self, temp_packs_dir):
        """Should skip scenarios with invalid JSON."""
        # Add invalid JSON file
        scenarios_dir = temp_packs_dir / "test-pack" / "scenarios"
        with open(scenarios_dir / "invalid.json", "w") as f:
            f.write("not valid json {{{")

        loader = ScenarioLoader(packs_dir=temp_packs_dir)
        count = loader.reload()
        # Should still load the valid scenarios
        assert count == 2

    def test_scenarios_sorted_by_difficulty(self, loader):
        """Scenarios should be sorted by difficulty then name."""
        loader.reload()
        summaries = loader.list_scenarios()

        # Beginner should come before advanced
        beginner_idx = next(
            i for i, s in enumerate(summaries) if s.difficulty == DifficultyLevel.BEGINNER
        )
        advanced_idx = next(
            i for i, s in enumerate(summaries) if s.difficulty == DifficultyLevel.ADVANCED
        )
        assert beginner_idx < advanced_idx

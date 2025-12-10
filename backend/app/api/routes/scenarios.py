"""
Scenario API routes.

Provides endpoints for browsing and managing educational scenarios.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.core.logging import get_api_logger
from app.services.scenarios import (
    ScenarioLoader,
    get_scenario_loader,
    Scenario,
    DifficultyLevel,
)
from app.services.scenarios.models import ScenarioSummary

logger = get_api_logger()

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.get(
    "",
    response_model=list[ScenarioSummary],
    summary="List scenarios",
    description="Get a list of available scenarios with optional filtering.",
)
async def list_scenarios(
    pack_id: Optional[str] = Query(
        default=None,
        description="Filter by content pack ID"
    ),
    difficulty: Optional[str] = Query(
        default=None,
        description="Filter by difficulty (beginner, intermediate, advanced, expert)"
    ),
    tag: Optional[str] = Query(
        default=None,
        description="Filter by tag"
    ),
) -> list[ScenarioSummary]:
    """
    List all available scenarios with optional filtering.

    Returns scenario summaries suitable for display in a list view.
    """
    logger.info(
        "Listing scenarios",
        extra={"pack_id": pack_id, "difficulty": difficulty, "tag": tag}
    )

    loader = get_scenario_loader()

    # Parse difficulty if provided
    difficulty_level = None
    if difficulty:
        try:
            difficulty_level = DifficultyLevel(difficulty.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid difficulty level: {difficulty}. "
                       f"Valid values: beginner, intermediate, advanced, expert"
            )

    scenarios = loader.list_scenarios(
        pack_id=pack_id,
        difficulty=difficulty_level,
        tag=tag,
    )

    logger.info(f"Found {len(scenarios)} scenarios")
    return scenarios


@router.get(
    "/packs",
    summary="List content packs",
    description="Get a list of available content packs with scenario counts.",
)
async def list_packs() -> list[dict]:
    """
    List all available content packs.

    Returns pack information including scenario counts.
    """
    logger.info("Listing content packs")
    loader = get_scenario_loader()
    packs = loader.list_packs()
    logger.info(f"Found {len(packs)} packs")
    return packs


@router.get(
    "/tags",
    summary="List all tags",
    description="Get a list of all unique tags used across scenarios.",
)
async def list_tags() -> list[str]:
    """
    Get all unique tags for filtering.

    Returns a sorted list of all tags used in scenarios.
    """
    loader = get_scenario_loader()
    return loader.get_tags()


@router.get(
    "/difficulties",
    summary="List difficulty levels",
    description="Get a list of all difficulty levels.",
)
async def list_difficulties() -> list[dict]:
    """
    Get all available difficulty levels.

    Returns difficulty levels with labels and descriptions.
    """
    return [
        {
            "value": DifficultyLevel.BEGINNER.value,
            "label": "Beginner",
            "description": "Perfect for newcomers to cybersecurity",
        },
        {
            "value": DifficultyLevel.INTERMEDIATE.value,
            "label": "Intermediate",
            "description": "For those with basic security knowledge",
        },
        {
            "value": DifficultyLevel.ADVANCED.value,
            "label": "Advanced",
            "description": "Challenging scenarios for experienced users",
        },
        {
            "value": DifficultyLevel.EXPERT.value,
            "label": "Expert",
            "description": "Complex scenarios requiring deep expertise",
        },
    ]


@router.get(
    "/{scenario_id}",
    response_model=Scenario,
    summary="Get scenario details",
    description="Get full details for a specific scenario.",
)
async def get_scenario(scenario_id: str) -> Scenario:
    """
    Get detailed information about a specific scenario.

    Returns the full scenario including all devices, vulnerabilities,
    and learning objectives.
    """
    logger.info(f"Getting scenario: {scenario_id}")

    loader = get_scenario_loader()
    scenario = loader.get_scenario(scenario_id)

    if not scenario:
        logger.warning(f"Scenario not found: {scenario_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Scenario not found: {scenario_id}"
        )

    return scenario


@router.post(
    "/reload",
    summary="Reload scenarios",
    description="Reload all scenarios from disk.",
)
async def reload_scenarios() -> dict:
    """
    Reload all scenarios from content packs.

    Use this after adding or modifying scenario files.
    """
    logger.info("Reloading scenarios")

    loader = get_scenario_loader()
    count = loader.reload()

    return {
        "message": "Scenarios reloaded successfully",
        "scenario_count": count,
    }


@router.get(
    "/{scenario_id}/start",
    summary="Start a scenario",
    description="Initialize a scenario for the user to begin.",
)
async def start_scenario(scenario_id: str) -> dict:
    """
    Start a scenario session.

    Returns the scenario data needed to begin the exercise.
    """
    logger.info(f"Starting scenario: {scenario_id}")

    loader = get_scenario_loader()
    scenario = loader.get_scenario(scenario_id)

    if not scenario:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario not found: {scenario_id}"
        )

    # Return scenario data for the session
    return {
        "scenario_id": scenario.id,
        "name": scenario.name,
        "difficulty": scenario.difficulty.value,
        "device_count": scenario.device_count,
        "vulnerability_count": scenario.total_vulnerabilities,
        "learning_objectives": scenario.learning_objectives,
        "devices": [
            {
                "id": d.id,
                "hostname": d.hostname,
                "ip": d.ip,
                "device_type": d.device_type,
                "is_gateway": d.is_gateway,
                # Don't reveal vulnerabilities - user must discover them
            }
            for d in scenario.devices
        ],
        "success_criteria": scenario.success_criteria,
    }

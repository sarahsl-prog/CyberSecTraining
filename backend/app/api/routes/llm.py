"""
LLM API routes.

Provides endpoints for getting AI-generated explanations of vulnerabilities
and security concepts.
"""

from fastapi import APIRouter, HTTPException, Query

from app.core.logging import get_api_logger
from app.services.llm import (
    LLMService,
    get_llm_service,
    ExplanationRequest,
    ExplanationResponse,
    ExplanationType,
)
from app.services.llm.models import LLMHealthStatus

logger = get_api_logger()

router = APIRouter(prefix="/llm", tags=["LLM"])


@router.post(
    "/explain",
    response_model=ExplanationResponse,
    summary="Get an explanation",
    description="Generate an AI-powered explanation for a security topic.",
)
async def get_explanation(
    request: ExplanationRequest,
    skip_cache: bool = Query(
        default=False,
        description="Skip cache lookup (force fresh generation)"
    ),
) -> ExplanationResponse:
    """
    Generate an explanation for a vulnerability or security concept.

    The service uses a fallback chain:
    1. Local Ollama (if available)
    2. Hosted API (if configured)
    3. Static knowledge base (always available)

    Results are cached to improve performance.
    """
    logger.info(
        "Explanation request received",
        extra={
            "topic": request.topic,
            "type": request.explanation_type.value,
            "difficulty": request.difficulty_level,
        }
    )

    try:
        service = get_llm_service()
        response = await service.get_explanation(request, skip_cache=skip_cache)

        logger.info(
            "Explanation generated",
            extra={
                "topic": request.topic,
                "provider": response.provider.value,
                "cached": response.cached,
            }
        )

        return response

    except Exception as e:
        logger.error(f"Error generating explanation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate explanation. Please try again later."
        )


@router.get(
    "/explain/vulnerability/{vuln_type}",
    response_model=ExplanationResponse,
    summary="Explain a vulnerability type",
    description="Get an explanation for a specific vulnerability type.",
)
async def explain_vulnerability(
    vuln_type: str,
    difficulty: str = Query(
        default="beginner",
        pattern="^(beginner|intermediate|advanced)$",
        description="Explanation difficulty level"
    ),
    context: str | None = Query(
        default=None,
        max_length=500,
        description="Additional context about the vulnerability"
    ),
) -> ExplanationResponse:
    """
    Shortcut endpoint to explain a vulnerability type.

    Provides a convenient way to get vulnerability explanations
    without constructing a full request body.
    """
    request = ExplanationRequest(
        explanation_type=ExplanationType.VULNERABILITY,
        topic=vuln_type,
        context=context,
        difficulty_level=difficulty,
    )

    service = get_llm_service()
    return await service.get_explanation(request)


@router.get(
    "/explain/remediation/{vuln_type}",
    response_model=ExplanationResponse,
    summary="Explain remediation steps",
    description="Get remediation steps for a specific vulnerability type.",
)
async def explain_remediation(
    vuln_type: str,
    difficulty: str = Query(
        default="beginner",
        pattern="^(beginner|intermediate|advanced)$",
        description="Explanation difficulty level"
    ),
    context: str | None = Query(
        default=None,
        max_length=500,
        description="Additional context about the environment"
    ),
) -> ExplanationResponse:
    """
    Shortcut endpoint to get remediation instructions.

    Provides step-by-step instructions for fixing a vulnerability.
    """
    request = ExplanationRequest(
        explanation_type=ExplanationType.REMEDIATION,
        topic=vuln_type,
        context=context,
        difficulty_level=difficulty,
    )

    service = get_llm_service()
    return await service.get_explanation(request)


@router.get(
    "/explain/concept/{concept}",
    response_model=ExplanationResponse,
    summary="Explain a security concept",
    description="Get an explanation for a security concept.",
)
async def explain_concept(
    concept: str,
    difficulty: str = Query(
        default="beginner",
        pattern="^(beginner|intermediate|advanced)$",
        description="Explanation difficulty level"
    ),
) -> ExplanationResponse:
    """
    Shortcut endpoint to explain a security concept.

    Provides educational explanations of cybersecurity concepts.
    """
    request = ExplanationRequest(
        explanation_type=ExplanationType.CONCEPT,
        topic=concept,
        difficulty_level=difficulty,
    )

    service = get_llm_service()
    return await service.get_explanation(request)


@router.get(
    "/health",
    response_model=LLMHealthStatus,
    summary="Check LLM service health",
    description="Check the availability of LLM providers.",
)
async def check_health() -> LLMHealthStatus:
    """
    Check the health status of LLM providers.

    Returns information about:
    - Ollama availability
    - Hosted API availability
    - Currently active provider
    - Cache size
    """
    service = get_llm_service()
    return await service.check_health()


@router.get(
    "/cache/stats",
    summary="Get cache statistics",
    description="Get statistics about the explanation cache.",
)
async def get_cache_stats() -> dict:
    """
    Get cache statistics.

    Returns:
    - Cache hits and misses
    - Hit rate
    - Current cache size
    - Number of evictions
    """
    service = get_llm_service()
    return service.get_cache_stats()


@router.post(
    "/cache/clear",
    summary="Clear the cache",
    description="Clear all cached explanations.",
)
async def clear_cache() -> dict:
    """
    Clear the explanation cache.

    Use this if you need to force fresh explanations
    or if cached content is outdated.
    """
    logger.info("Cache clear requested")

    service = get_llm_service()
    count = service.clear_cache()

    return {
        "message": "Cache cleared successfully",
        "entries_cleared": count,
    }

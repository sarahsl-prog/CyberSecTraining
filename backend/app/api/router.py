"""
Main API router that includes all route modules.

This module aggregates all API routes into a single router that is
mounted at /api/v1 in the main application.
"""

from fastapi import APIRouter

from app.api.routes import auth, settings, network, devices, vulnerabilities, llm, scenarios

api_router = APIRouter()

# Include route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(network.router)  # Already has prefix="/network"
api_router.include_router(devices.router)  # Already has prefix="/devices"
api_router.include_router(vulnerabilities.router)  # Already has prefix="/vulnerabilities"
api_router.include_router(llm.router)  # Already has prefix="/llm"

# Include scenarios router
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["Scenarios"])


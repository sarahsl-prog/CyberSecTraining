"""Main API router that includes all route modules."""

from fastapi import APIRouter

from app.api.routes import auth, settings

api_router = APIRouter()

# Include route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])

# Future route modules (to be implemented):
# api_router.include_router(network.router, prefix="/network", tags=["Network Scanning"])
# api_router.include_router(devices.router, prefix="/devices", tags=["Devices"])
# api_router.include_router(vulnerabilities.router, prefix="/vulnerabilities", tags=["Vulnerabilities"])
# api_router.include_router(scenarios.router, prefix="/scenarios", tags=["Scenarios"])
# api_router.include_router(llm.router, prefix="/llm", tags=["LLM"])

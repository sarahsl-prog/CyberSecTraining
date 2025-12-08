"""Authentication and user management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import get_datastore
from app.services.datastore.base import DataStore

router = APIRouter()


class UserProfile(BaseModel):
    """User profile data."""

    display_name: str = "Local User"
    knowledge_level: str = "beginner"  # beginner, intermediate, advanced
    has_completed_onboarding: bool = False
    has_accepted_eula: bool = False


class ProfileUpdate(BaseModel):
    """User profile update request."""

    display_name: str | None = None
    knowledge_level: str | None = None


class OnboardingStatus(BaseModel):
    """Onboarding completion status."""

    has_completed_onboarding: bool
    has_accepted_eula: bool


@router.post("/init")
async def init_user(datastore: DataStore = Depends(get_datastore)) -> dict[str, str]:
    """Initialize local user on first launch."""
    # Create default user profile if not exists
    profile = datastore.get_preference("local", "user_profile")
    if not profile:
        default_profile = UserProfile()
        datastore.save_preference("local", "user_profile", default_profile.model_dump_json())
    return {"status": "initialized"}


@router.get("/status")
async def get_auth_status(datastore: DataStore = Depends(get_datastore)) -> dict[str, bool]:
    """Check authentication/initialization status."""
    profile = datastore.get_preference("local", "user_profile")
    return {"initialized": profile is not None}


@router.get("/profile", response_model=UserProfile)
async def get_profile(datastore: DataStore = Depends(get_datastore)) -> UserProfile:
    """Get current user profile."""
    profile_json = datastore.get_preference("local", "user_profile")
    if not profile_json:
        raise HTTPException(status_code=404, detail="Profile not found. Initialize first.")
    return UserProfile.model_validate_json(profile_json)


@router.post("/profile", response_model=UserProfile)
async def update_profile(
    update: ProfileUpdate, datastore: DataStore = Depends(get_datastore)
) -> UserProfile:
    """Update user profile."""
    profile_json = datastore.get_preference("local", "user_profile")
    if not profile_json:
        raise HTTPException(status_code=404, detail="Profile not found. Initialize first.")

    profile = UserProfile.model_validate_json(profile_json)

    if update.display_name is not None:
        profile.display_name = update.display_name
    if update.knowledge_level is not None:
        profile.knowledge_level = update.knowledge_level

    datastore.save_preference("local", "user_profile", profile.model_dump_json())
    return profile


@router.post("/reset")
async def reset_data(datastore: DataStore = Depends(get_datastore)) -> dict[str, str]:
    """Reset all local user data."""
    # This would clear all user data - be careful with this!
    # For now, just reset the profile
    default_profile = UserProfile()
    datastore.save_preference("local", "user_profile", default_profile.model_dump_json())
    return {"status": "reset_complete"}


@router.get("/onboarding", response_model=OnboardingStatus)
async def get_onboarding_status(
    datastore: DataStore = Depends(get_datastore),
) -> OnboardingStatus:
    """Get onboarding completion status."""
    profile_json = datastore.get_preference("local", "user_profile")
    if not profile_json:
        return OnboardingStatus(has_completed_onboarding=False, has_accepted_eula=False)

    profile = UserProfile.model_validate_json(profile_json)
    return OnboardingStatus(
        has_completed_onboarding=profile.has_completed_onboarding,
        has_accepted_eula=profile.has_accepted_eula,
    )


@router.post("/onboarding/complete")
async def complete_onboarding(
    datastore: DataStore = Depends(get_datastore),
) -> dict[str, str]:
    """Mark onboarding as complete."""
    profile_json = datastore.get_preference("local", "user_profile")
    if not profile_json:
        raise HTTPException(status_code=404, detail="Profile not found. Initialize first.")

    profile = UserProfile.model_validate_json(profile_json)
    profile.has_completed_onboarding = True
    datastore.save_preference("local", "user_profile", profile.model_dump_json())
    return {"status": "onboarding_complete"}


@router.post("/eula/accept")
async def accept_eula(datastore: DataStore = Depends(get_datastore)) -> dict[str, str]:
    """Accept the EULA."""
    profile_json = datastore.get_preference("local", "user_profile")
    if not profile_json:
        raise HTTPException(status_code=404, detail="Profile not found. Initialize first.")

    profile = UserProfile.model_validate_json(profile_json)
    profile.has_accepted_eula = True
    datastore.save_preference("local", "user_profile", profile.model_dump_json())
    return {"status": "eula_accepted"}

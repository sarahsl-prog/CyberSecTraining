"""Settings management endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import get_datastore
from app.services.datastore.base import DataStore

router = APIRouter()


class AccessibilitySettings(BaseModel):
    """Accessibility preferences."""

    color_mode: str = "light"  # light, dark, high-contrast, protanopia, deuteranopia, tritanopia
    font_size: int = 100  # 100-200 percentage
    reduce_motion: bool = False
    screen_reader_optimized: bool = False
    show_focus_indicator: bool = True


class LLMSettings(BaseModel):
    """LLM preferences."""

    prefer_local: bool = True
    api_key: str | None = None
    response_detail_level: str = "moderate"  # brief, moderate, detailed
    language: str = "en"


class ScanSettings(BaseModel):
    """Network scanning preferences."""

    default_scan_type: str = "quick"  # quick, deep
    scan_timeout: int = 120  # seconds
    auto_scan_enabled: bool = False


class PrivacySettings(BaseModel):
    """Privacy preferences."""

    data_collection_enabled: bool = False
    telemetry_opt_in: bool = False


class AllSettings(BaseModel):
    """Combined settings response."""

    accessibility: AccessibilitySettings
    llm: LLMSettings
    scan: ScanSettings
    privacy: PrivacySettings


def _get_settings_with_default(
    datastore: DataStore, key: str, default_factory: type[BaseModel]
) -> BaseModel:
    """Get settings from datastore or return defaults."""
    settings_json = datastore.get_preference("local", key)
    if settings_json:
        return default_factory.model_validate_json(settings_json)
    return default_factory()


@router.get("", response_model=AllSettings)
async def get_all_settings(datastore: DataStore = Depends(get_datastore)) -> AllSettings:
    """Get all settings."""
    return AllSettings(
        accessibility=_get_settings_with_default(
            datastore, "accessibility_settings", AccessibilitySettings
        ),
        llm=_get_settings_with_default(datastore, "llm_settings", LLMSettings),
        scan=_get_settings_with_default(datastore, "scan_settings", ScanSettings),
        privacy=_get_settings_with_default(datastore, "privacy_settings", PrivacySettings),
    )


@router.get("/accessibility", response_model=AccessibilitySettings)
async def get_accessibility_settings(
    datastore: DataStore = Depends(get_datastore),
) -> AccessibilitySettings:
    """Get accessibility settings."""
    return _get_settings_with_default(datastore, "accessibility_settings", AccessibilitySettings)


@router.post("/accessibility", response_model=AccessibilitySettings)
async def update_accessibility_settings(
    settings: AccessibilitySettings, datastore: DataStore = Depends(get_datastore)
) -> AccessibilitySettings:
    """Update accessibility settings."""
    # Validate color mode
    valid_modes = ["light", "dark", "high-contrast", "protanopia", "deuteranopia", "tritanopia"]
    if settings.color_mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Invalid color mode. Must be one of: {valid_modes}")

    # Validate font size
    if not 100 <= settings.font_size <= 200:
        raise HTTPException(status_code=400, detail="Font size must be between 100 and 200")

    datastore.save_preference("local", "accessibility_settings", settings.model_dump_json())
    return settings


@router.get("/llm", response_model=LLMSettings)
async def get_llm_settings(datastore: DataStore = Depends(get_datastore)) -> LLMSettings:
    """Get LLM settings."""
    return _get_settings_with_default(datastore, "llm_settings", LLMSettings)


@router.post("/llm", response_model=LLMSettings)
async def update_llm_settings(
    settings: LLMSettings, datastore: DataStore = Depends(get_datastore)
) -> LLMSettings:
    """Update LLM settings."""
    valid_levels = ["brief", "moderate", "detailed"]
    if settings.response_detail_level not in valid_levels:
        raise HTTPException(
            status_code=400, detail=f"Invalid detail level. Must be one of: {valid_levels}"
        )

    datastore.save_preference("local", "llm_settings", settings.model_dump_json())
    return settings


@router.get("/scan", response_model=ScanSettings)
async def get_scan_settings(datastore: DataStore = Depends(get_datastore)) -> ScanSettings:
    """Get scan settings."""
    return _get_settings_with_default(datastore, "scan_settings", ScanSettings)


@router.post("/scan", response_model=ScanSettings)
async def update_scan_settings(
    settings: ScanSettings, datastore: DataStore = Depends(get_datastore)
) -> ScanSettings:
    """Update scan settings."""
    valid_types = ["quick", "deep"]
    if settings.default_scan_type not in valid_types:
        raise HTTPException(
            status_code=400, detail=f"Invalid scan type. Must be one of: {valid_types}"
        )

    if settings.scan_timeout < 30 or settings.scan_timeout > 600:
        raise HTTPException(status_code=400, detail="Scan timeout must be between 30 and 600 seconds")

    datastore.save_preference("local", "scan_settings", settings.model_dump_json())
    return settings


@router.get("/privacy", response_model=PrivacySettings)
async def get_privacy_settings(datastore: DataStore = Depends(get_datastore)) -> PrivacySettings:
    """Get privacy settings."""
    return _get_settings_with_default(datastore, "privacy_settings", PrivacySettings)


@router.post("/privacy", response_model=PrivacySettings)
async def update_privacy_settings(
    settings: PrivacySettings, datastore: DataStore = Depends(get_datastore)
) -> PrivacySettings:
    """Update privacy settings."""
    datastore.save_preference("local", "privacy_settings", settings.model_dump_json())
    return settings


@router.get("/{key}")
async def get_single_setting(
    key: str, datastore: DataStore = Depends(get_datastore)
) -> dict[str, Any]:
    """Get a single setting by key."""
    value = datastore.get_preference("local", key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    return {"key": key, "value": value}


@router.put("/{key}")
async def update_single_setting(
    key: str, value: str, datastore: DataStore = Depends(get_datastore)
) -> dict[str, Any]:
    """Update a single setting by key."""
    datastore.save_preference("local", key, value)
    return {"key": key, "value": value}

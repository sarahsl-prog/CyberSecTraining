"""
Content pack system module.

This module provides functionality for loading and managing content packs
that contain vulnerability definitions, scenarios, and knowledge base content.

Key Components:
- PackLoader: Loads and validates content packs
- PackValidator: Validates pack manifests and content
- PackRegistry: Manages loaded packs

Pack Structure:
    packs/
    ├── core/
    │   ├── manifest.json
    │   ├── vulnerabilities/
    │   │   ├── default_credentials.json
    │   │   └── ...
    │   └── knowledge/
    │       └── remediation_guides.json
    └── home-basics/
        ├── manifest.json
        ├── scenarios/
        └── ...
"""

from app.services.packs.loader import PackLoader
from app.services.packs.validator import PackValidator
from app.services.packs.registry import PackRegistry, get_pack_registry
from app.services.packs.models import (
    PackManifest,
    VulnerabilityDefinition,
    RemediationGuide,
)

__all__ = [
    "PackLoader",
    "PackValidator",
    "PackRegistry",
    "get_pack_registry",
    "PackManifest",
    "VulnerabilityDefinition",
    "RemediationGuide",
]

"""
Application configuration management.

This module centralizes all application configuration, loaded from environment
variables with sensible defaults. Configuration is validated using Pydantic.
"""

import secrets
from pathlib import Path
from typing import Optional, Literal

from pydantic import ConfigDict, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via environment variables or a .env file.
    The .env file should be placed in the project root directory.
    """

    # Application
    app_name: str = "CyberSec Teaching Tool API"
    app_version: str = "0.1.0"
    debug: bool = True
    log_level: str = "INFO"

    # Database
    database_url: str = "sqlite:///./data/cybersec.db"

    # LLM Configuration
    ollama_base_url: str = "http://localhost:11434"
    hosted_llm_api_key: Optional[str] = None
    hosted_llm_base_url: Optional[str] = None

    # Security
    secret_key: str = ""

    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        # Allow empty - will be generated in __init__ if needed
        return v

    # Feature flags
    enable_real_scanning: bool = True
    enable_telemetry: bool = False

    # Application Mode
    # Default mode for the application: 'training' (safe, fake data) or 'live' (real scanning)
    # Training mode is recommended for learning and classroom environments
    default_application_mode: Literal['training', 'live'] = 'training'

    # Network Scanning Configuration
    scan_timeout: int = 300  # Max scan duration in seconds (5 minutes)
    max_network_size: int = 256  # Maximum IPs to scan (/24 network)
    default_port_range: str = "1-1024"  # Default ports for quick scan
    deep_scan_port_range: str = "1-65535"  # Ports for deep scan

    @field_validator('max_network_size')
    @classmethod
    def validate_max_network_size(cls, v: int) -> int:
        if v < 1 or v > 65536:  # Max /16 network
            raise ValueError('max_network_size must be between 1 and 65536')
        return v

    # Rate Limiting
    max_concurrent_scans: int = 1  # Only one scan at a time
    scan_cooldown: int = 60  # Seconds between scans (Fix Issue #22 - already configurable)
    
    @field_validator('max_concurrent_scans')
    @classmethod
    def validate_max_concurrent_scans(cls, v: int) -> int:
        if v < 0 or v > 10:
            raise ValueError('max_concurrent_scans must be between 0 and 10')
        return v
    
    @field_validator('scan_cooldown')
    @classmethod
    def validate_scan_cooldown(cls, v: int) -> int:
        if v < 0 or v > 3600:
            raise ValueError('scan_cooldown must be between 0 and 3600 seconds (1 hour)')
        return v

    # Paths
    data_dir: Path = Path("./data")
    logs_dir: Path = Path("./logs")
    packs_dir: Path = Path("../packs")
    knowledge_base_dir: Path = Path("../knowledge-base")
    
    @field_validator('data_dir', 'logs_dir', 'packs_dir', 'knowledge_base_dir')
    @classmethod
    def validate_directories(cls, v: Path) -> Path:
        # Ensure Path object is created properly
        if isinstance(v, str):
            v = Path(v)
        return v

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate and create directories (Fix Issue #19)
        self._validate_and_create_paths()
        
        # Generate a secure key in debug mode if not set or is the placeholder
        if not self.secret_key or self.secret_key == "change-this-in-production":
            if self.debug:
                import warnings
                warnings.warn("Using auto-generated secret key for development. Set SECRET_KEY environment variable for production.", stacklevel=2)
                self.secret_key = secrets.token_hex(32)
            else:
                raise ValueError(
                    "SECRET_KEY must be set in production. "
                    "Generate a secure key: openssl rand -hex 32"
                )
    
    def _validate_and_create_paths(self):
        """Validate and create necessary directories."""
        import os
        
        for path_name, path_obj in [
            ('data_dir', self.data_dir),
            ('logs_dir', self.logs_dir),
        ]:
            if not path_obj.exists():
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                except (OSError, PermissionError) as e:
                    raise ValueError(
                        f"Cannot create {path_name} at {path_obj}: {e}"
                    )

    model_config = ConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
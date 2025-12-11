"""
Application configuration management.

This module centralizes all application configuration, loaded from environment
variables with sensible defaults. Configuration is validated using Pydantic.
"""

from pathlib import Path
from typing import Optional

from pydantic import ConfigDict
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
    secret_key: str = "change-this-in-production"

    # Feature flags
    enable_real_scanning: bool = True
    enable_telemetry: bool = False

    # Network Scanning Configuration
    scan_timeout: int = 300  # Max scan duration in seconds (5 minutes)
    max_network_size: int = 256  # Maximum IPs to scan (/24 network)
    default_port_range: str = "1-1024"  # Default ports for quick scan
    deep_scan_port_range: str = "1-65535"  # Ports for deep scan

    # Rate Limiting
    max_concurrent_scans: int = 1  # Only one scan at a time
    scan_cooldown: int = 60  # Seconds between scans

    # Paths
    data_dir: Path = Path("./data")
    logs_dir: Path = Path("./logs")
    packs_dir: Path = Path("../packs")
    knowledge_base_dir: Path = Path("../knowledge-base")

    model_config = ConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()

"""Application configuration management."""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "CyberSec Teaching Tool API"
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

    # Paths
    data_dir: Path = Path("./data")
    packs_dir: Path = Path("../packs")
    knowledge_base_dir: Path = Path("../knowledge-base")

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

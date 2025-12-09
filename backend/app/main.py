"""
FastAPI application entry point.

This module creates and configures the main FastAPI application instance,
including middleware, routers, and lifecycle management.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.init_db import init_db

# Initialize logging first
setup_logging()
logger = get_logger("api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler for startup/shutdown events.

    This context manager handles:
    - Startup: Initialize database, logging, and other services
    - Shutdown: Clean up resources
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}...")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {settings.log_level}")

    init_db()
    logger.info("Database initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down application...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="Backend API for the CyberSec Teaching Tool - an accessible cybersecurity education platform.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:1420",  # Tauri dev
            "http://localhost:5173",  # Vite dev
            "tauri://localhost",  # Tauri production
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    # Health check endpoint
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "version": "0.1.0"}

    return app


# Create app instance
app = create_app()

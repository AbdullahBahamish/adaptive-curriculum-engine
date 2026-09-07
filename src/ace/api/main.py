"""FastAPI application entry point for the ACE AI Engine.

This module creates the FastAPI app, registers middleware, and mounts
all API routers. It is the single entry point consumed by Uvicorn.
"""
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ace.core.config import settings
from ace.core.logging import configure_logging, get_logger
from ace.api.routes import health, skills, careers, prerequisites, gap_analysis, learning_path

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown logic."""
    configure_logging()
    logger.info(
        "ace_startup",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        llm_enabled=settings.llm_enabled,
    )
    yield
    logger.info("ace_shutdown")


def create_app() -> FastAPI:
    """Application factory — creates and configures the FastAPI instance."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "AI-powered skill gap analysis and learning path generation engine. "
            "Consumed by the C# ASP.NET Core backend via REST."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS — allow C# backend and local frontend dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routers
    prefix = settings.api_prefix
    app.include_router(health.router, tags=["Health"])
    app.include_router(skills.router, prefix=f"{prefix}/skills", tags=["Skills"])
    app.include_router(careers.router, prefix=f"{prefix}/careers", tags=["Careers"])
    app.include_router(prerequisites.router, prefix=f"{prefix}/prerequisites", tags=["Prerequisites"])
    app.include_router(gap_analysis.router, prefix=prefix, tags=["Gap Analysis"])
    app.include_router(learning_path.router, prefix=prefix, tags=["Learning Path"])

    return app


app = create_app()
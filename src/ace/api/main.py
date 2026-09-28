"""FastAPI application entry point for the ACE AI Engine.

This module creates the FastAPI app, registers middleware, and mounts
all API routers. It is the single entry point consumed by Uvicorn.
"""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ace.api.routes import (
    careers,
    gap_analysis,
    health,
    learning_path,
    mastery,
    prerequisites,
    semantic,
    skills,
)
from ace.core.config import settings
from ace.core.logging import configure_logging, get_logger

logger = get_logger(__name__)



@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
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
    app.include_router(mastery.router, prefix=prefix, tags=["Mastery"])
    app.include_router(semantic.router, prefix=prefix, tags=["Semantic Matching"])

    from pathlib import Path
    from fastapi.responses import HTMLResponse

    @app.get(
        "/graph",
        response_class=HTMLResponse,
        tags=["Visualization"],
        summary="Interactive DAG Curriculum Graph Visualizer",
    )
    def view_graph_visualizer() -> HTMLResponse:
        """Serve the interactive topological curriculum graph visualizer."""
        graph_file = Path("docs/graph_visualizer.html")
        if graph_file.exists():
            return HTMLResponse(content=graph_file.read_text(encoding="utf-8"))
        return HTMLResponse("<h3>Graph visualizer not generated yet. Run scripts/generate_graph_visualizer.py</h3>")

    @app.get(
        "/docs/swagger",
        response_class=HTMLResponse,
        tags=["Documentation"],
        summary="Standalone OpenAPI Swagger UI Documentation",
    )
    def view_swagger_standalone() -> HTMLResponse:
        """Serve the standalone OpenAPI Swagger UI document."""
        swagger_file = Path("docs/api_docs.html")
        if swagger_file.exists():
            return HTMLResponse(content=swagger_file.read_text(encoding="utf-8"))
        return HTMLResponse("<h3>Standalone docs not generated yet. Run scripts/export_openapi.py</h3>")

    return app



app = create_app()

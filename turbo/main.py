"""Main application entry point for Turbo."""

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from turbo.api.middleware import APIKeyMiddleware, RateLimitMiddleware
from turbo.utils.config import Settings, get_settings

_logger = logging.getLogger("turbo.main")


def _validate_production_env(settings: Settings) -> None:
    """Fail fast if required environment variables are missing in production."""
    if not settings.is_production():
        return

    missing = []
    if not os.getenv("TURBO_API_KEY"):
        missing.append("TURBO_API_KEY")
    if not settings.security.secret_key:
        missing.append("SECURITY_SECRET_KEY")
    if not settings.database.url or "sqlite" in settings.database.url:
        missing.append("DATABASE_URL (must be PostgreSQL in production)")

    if missing:
        msg = (
            "Production startup blocked — missing required environment variables: "
            + ", ".join(missing)
        )
        _logger.critical(msg)
        raise SystemExit(msg)

    # Warnings for recommended but non-blocking vars
    if not settings.anthropic.api_key:
        _logger.warning("ANTHROPIC_API_KEY not set — AI features will be unavailable")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    is_production = settings.is_production()

    app = FastAPI(
        title="Turbo API",
        description="AI-powered local project management and development platform",
        version="1.0.0",
        debug=False if is_production else settings.debug,
        docs_url=None if is_production else "/api/docs",
        redoc_url=None if is_production else "/api/redoc",
    )

    # Rate limiting (runs after auth — don't count unauthenticated requests)
    app.add_middleware(RateLimitMiddleware)

    # API key authentication (enabled when TURBO_API_KEY is set)
    app.add_middleware(APIKeyMiddleware)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    )

    # Add API routes
    from turbo.api.v1 import router as api_router

    app.include_router(api_router)

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"message": "Turbo API", "version": "1.0.0"}

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    @app.on_event("startup")
    async def startup_event():
        """Initialize database and agent tracker on startup."""
        _validate_production_env(settings)
        from turbo.core.database import init_database
        from turbo.core.services.agent_activity import tracker
        await init_database()
        await tracker.start()

    # Mount documentation if site directory exists
    site_dir = Path(__file__).parent.parent / "site"
    if site_dir.exists():
        app.mount(
            "/docs",
            StaticFiles(directory=str(site_dir), html=True),
            name="documentation"
        )

    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "turbo.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.reload,
    )

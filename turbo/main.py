"""Main application entry point for Turbo."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from turbo.utils.config import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Turbo API",
        description="AI-powered local project management and development platform",
        version="1.0.0",
        debug=settings.debug,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
        from turbo.core.database import init_database
        from turbo.core.services.agent_activity import tracker
        await init_database()
        await tracker.start()

    # Mount documentation if site directory exists
    site_dir = Path("site")
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

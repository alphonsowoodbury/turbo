"""API v1 package - Minimal deployment for task management."""

from fastapi import APIRouter

# Import only the core endpoints for task management
from turbo.api.v1.endpoints import (
    comments,
    documents,
    initiatives,
    issues,
    milestones,
    projects,
    tags,
)

# Create the main API router
router = APIRouter(prefix="/api/v1")

# Include only core endpoint routers
router.include_router(projects.router, prefix="/projects", tags=["projects"])
router.include_router(issues.router, prefix="/issues", tags=["issues"])
router.include_router(milestones.router, prefix="/milestones", tags=["milestones"])
router.include_router(initiatives.router, prefix="/initiatives", tags=["initiatives"])
router.include_router(documents.router, prefix="/documents", tags=["documents"])
router.include_router(tags.router, prefix="/tags", tags=["tags"])
router.include_router(comments.router, prefix="/comments", tags=["comments"])

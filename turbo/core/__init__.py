"""Core business logic and data models for Turbo."""

# Wrapped in try/except to support lightweight imports without database dependencies
try:
    from turbo.core.database import Base, get_db_session
    from turbo.core.models import Document, Issue, Project, Tag
    from turbo.core.schemas import (
        DocumentCreate,
        DocumentResponse,
        IssueCreate,
        IssueResponse,
        ProjectCreate,
        ProjectResponse,
    )

    __all__ = [
        "Base",
        "Document",
        "DocumentCreate",
        "DocumentResponse",
        "Issue",
        "IssueCreate",
        "IssueResponse",
        "Project",
        "ProjectCreate",
        "ProjectResponse",
        "Tag",
        "get_db_session",
    ]
except ImportError:
    # Running in lightweight mode - only utils and services available
    __all__ = []

"""Turbo: AI-powered local project management and development platform.

Turbo is a local-first project management platform that integrates with Claude Code
to provide AI-assisted development workflows, automated documentation generation,
and intelligent project insights.
"""

__version__ = "1.0.0"
__author__ = "Turbo Development Team"
__email__ = "dev@turbo.local"

# Public API exports - wrapped in try/except to support lightweight imports
# (e.g., for webhook server that only needs action detection utils)
try:
    from turbo.core.models import Document, Issue, Project
    from turbo.core.schemas import (
        IssueCreate,
        IssueResponse,
        ProjectCreate,
        ProjectResponse,
    )

    __all__ = [
        "Document",
        "Issue",
        "IssueCreate",
        "IssueResponse",
        "Project",
        "ProjectCreate",
        "ProjectResponse",
        "__version__",
    ]
except ImportError:
    # Running in lightweight mode (e.g., webhook server)
    # Only core modules available, no database dependencies
    __all__ = ["__version__"]

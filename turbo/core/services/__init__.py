"""Business logic services for Turbo core functionality."""

# Core services only - optional dependencies handled via try/except
from turbo.core.services.document import DocumentService
from turbo.core.services.graph import GraphService
from turbo.core.services.initiative import InitiativeService
from turbo.core.services.issue import IssueService
from turbo.core.services.milestone import MilestoneService
from turbo.core.services.project import ProjectService
from turbo.core.services.tag import TagService

# Optional services - import with fallbacks
try:
    from turbo.core.services.claude_webhook import ClaudeWebhookService, get_webhook_service
except ImportError:
    ClaudeWebhookService = None  # type: ignore
    get_webhook_service = None  # type: ignore

try:
    from turbo.core.services.podcast import PodcastService
except ImportError:
    PodcastService = None  # type: ignore

__all__ = [
    "ClaudeWebhookService",
    "DocumentService",
    "GraphService",
    "InitiativeService",
    "IssueService",
    "MilestoneService",
    "PodcastService",
    "ProjectService",
    "TagService",
    "get_webhook_service",
]

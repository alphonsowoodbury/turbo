"""Pydantic schemas for API request/response validation."""

from turbo.core.schemas.calendar_event import (
    CalendarEventCreate,
    CalendarEventResponse,
    CalendarEventSummary,
    CalendarEventUpdate,
)
from turbo.core.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
)
from turbo.core.schemas.favorite import (
    FavoriteCreate,
    FavoriteResponse,
    FavoriteWithDetails,
)
from turbo.core.schemas.graph import (
    GraphNodeCreate,
    GraphSearchQuery,
    GraphSearchResponse,
    GraphSearchResult,
    GraphStats,
)
from turbo.core.schemas.initiative import (
    InitiativeCreate,
    InitiativeResponse,
    InitiativeUpdate,
)
from turbo.core.schemas.issue import (
    IssueCreate,
    IssueResponse,
    IssueUpdate,
)
from turbo.core.schemas.milestone import (
    MilestoneCreate,
    MilestoneResponse,
    MilestoneSummary,
    MilestoneUpdate,
)
from turbo.core.schemas.podcast import (
    PlayProgress,
    PodcastEpisodeCreate,
    PodcastEpisodeFilter,
    PodcastEpisodeResponse,
    PodcastEpisodeUpdate,
    PodcastEpisodeWithShow,
    PodcastFeedFetch,
    PodcastFeedURL,
    PodcastShowCreate,
    PodcastShowFilter,
    PodcastShowResponse,
    PodcastShowUpdate,
    PodcastShowWithEpisodes,
    TranscriptGenerate,
)
from turbo.core.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ProjectWithStats,
)
from turbo.core.schemas.saved_filter import (
    SavedFilterCreate,
    SavedFilterResponse,
    SavedFilterUpdate,
)
from turbo.core.schemas.skill import (
    SkillCreate,
    SkillResponse,
    SkillSummary,
    SkillUpdate,
)
from turbo.core.schemas.tag import (
    TagCreate,
    TagResponse,
    TagUpdate,
)

__all__ = [
    "CalendarEventCreate",
    "CalendarEventResponse",
    "CalendarEventSummary",
    "CalendarEventUpdate",
    "DocumentCreate",
    "DocumentResponse",
    "DocumentUpdate",
    "FavoriteCreate",
    "FavoriteResponse",
    "FavoriteWithDetails",
    "GraphNodeCreate",
    "GraphSearchQuery",
    "GraphSearchResponse",
    "GraphSearchResult",
    "GraphStats",
    "InitiativeCreate",
    "InitiativeResponse",
    "InitiativeUpdate",
    "IssueCreate",
    "IssueResponse",
    "IssueUpdate",
    "MilestoneCreate",
    "MilestoneResponse",
    "MilestoneSummary",
    "MilestoneUpdate",
    "PlayProgress",
    "PodcastEpisodeCreate",
    "PodcastEpisodeFilter",
    "PodcastEpisodeResponse",
    "PodcastEpisodeUpdate",
    "PodcastEpisodeWithShow",
    "PodcastFeedFetch",
    "PodcastFeedURL",
    "PodcastShowCreate",
    "PodcastShowFilter",
    "PodcastShowResponse",
    "PodcastShowUpdate",
    "PodcastShowWithEpisodes",
    "ProjectCreate",
    "ProjectResponse",
    "ProjectUpdate",
    "ProjectWithStats",
    "SavedFilterCreate",
    "SavedFilterResponse",
    "SavedFilterUpdate",
    "SkillCreate",
    "SkillResponse",
    "SkillSummary",
    "SkillUpdate",
    "TagCreate",
    "TagResponse",
    "TagUpdate",
    "TranscriptGenerate",
]

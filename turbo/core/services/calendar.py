"""Calendar service for aggregating events from across the application."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.issue import Issue
from turbo.core.models.initiative import Initiative
from turbo.core.models.milestone import Milestone
from turbo.core.models.podcast import PodcastEpisode
from turbo.core.models.literature import Literature
from turbo.core.models.project import Project
from turbo.core.schemas.calendar import (
    CalendarEvent,
    CalendarEventsResponse,
    CalendarEventFilter,
    CalendarStats,
    EventType,
    EventCategory,
)


class CalendarService:
    """Service for aggregating calendar events from multiple sources."""

    def __init__(self, session: AsyncSession):
        """Initialize calendar service."""
        self._session = session

    async def get_events(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        filter_params: CalendarEventFilter | None = None,
    ) -> CalendarEventsResponse:
        """
        Get calendar events from all sources.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            filter_params: Additional filtering parameters

        Returns:
            CalendarEventsResponse with aggregated events
        """
        # Default to current month if no dates provided
        if start_date is None:
            now = datetime.now(timezone.utc)
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if end_date is None:
            # End of current month
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1, day=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1, day=1)

        # Aggregate events from all sources
        events = []

        # Get events from each source
        events.extend(await self._get_issue_events(start_date, end_date, filter_params))
        events.extend(await self._get_milestone_events(start_date, end_date, filter_params))
        events.extend(await self._get_initiative_events(start_date, end_date, filter_params))
        events.extend(await self._get_podcast_events(start_date, end_date, filter_params))
        events.extend(await self._get_literature_events(start_date, end_date, filter_params))

        # Sort events by date
        events.sort(key=lambda e: e.date)

        return CalendarEventsResponse(
            events=events,
            total=len(events),
            start_date=start_date,
            end_date=end_date,
        )

    async def _get_issue_events(
        self,
        start_date: datetime,
        end_date: datetime,
        filter_params: CalendarEventFilter | None,
    ) -> list[CalendarEvent]:
        """Get events from issues with due dates."""
        # Check filter
        if filter_params and filter_params.event_types:
            if EventType.ISSUE not in filter_params.event_types:
                return []

        # Query issues with due dates in range
        query = select(Issue, Project).outerjoin(Project, Issue.project_id == Project.id).where(
            and_(Issue.due_date.isnot(None), Issue.due_date >= start_date, Issue.due_date <= end_date)
        )

        # Apply additional filters
        if filter_params:
            if filter_params.project_ids:
                query = query.where(Issue.project_id.in_(filter_params.project_ids))
            if filter_params.statuses:
                query = query.where(Issue.status.in_(filter_params.statuses))
            if filter_params.priorities:
                query = query.where(Issue.priority.in_(filter_params.priorities))

        result = await self._session.execute(query)
        rows = result.all()

        events = []
        for issue, project in rows:
            events.append(
                CalendarEvent(
                    id=issue.id,
                    title=issue.title,
                    description=issue.description,
                    date=issue.due_date,
                    event_type=EventType.ISSUE,
                    category=EventCategory.DEADLINE,
                    status=issue.status,
                    priority=issue.priority,
                    project_id=project.id if project else None,
                    project_name=project.name if project else None,
                    url=f"/projects/{project.id}/issues/{issue.id}" if project else f"/issues/{issue.id}",
                    color=self._get_priority_color(issue.priority),
                    icon="issue",
                )
            )

        return events

    async def _get_milestone_events(
        self,
        start_date: datetime,
        end_date: datetime,
        filter_params: CalendarEventFilter | None,
    ) -> list[CalendarEvent]:
        """Get events from milestones."""
        if filter_params and filter_params.event_types:
            if EventType.MILESTONE not in filter_params.event_types:
                return []

        events = []

        # Get milestone start dates
        query_start = (
            select(Milestone, Project)
            .join(Project, Milestone.project_id == Project.id)
            .where(
                and_(
                    Milestone.start_date.isnot(None),
                    Milestone.start_date >= start_date,
                    Milestone.start_date <= end_date,
                )
            )
        )

        if filter_params and filter_params.project_ids:
            query_start = query_start.where(Milestone.project_id.in_(filter_params.project_ids))

        result = await self._session.execute(query_start)
        for milestone, project in result.all():
            events.append(
                CalendarEvent(
                    id=milestone.id,
                    title=f"{milestone.name} (Start)",
                    description=milestone.description,
                    date=milestone.start_date,
                    event_type=EventType.MILESTONE,
                    category=EventCategory.START,
                    status=milestone.status,
                    project_id=project.id,
                    project_name=project.name,
                    url=f"/projects/{project.id}/milestones/{milestone.id}",
                    color=self._get_status_color(milestone.status),
                    icon="milestone",
                )
            )

        # Get milestone due dates
        query_due = (
            select(Milestone, Project)
            .join(Project, Milestone.project_id == Project.id)
            .where(and_(Milestone.due_date >= start_date, Milestone.due_date <= end_date))
        )

        if filter_params and filter_params.project_ids:
            query_due = query_due.where(Milestone.project_id.in_(filter_params.project_ids))

        result = await self._session.execute(query_due)
        for milestone, project in result.all():
            events.append(
                CalendarEvent(
                    id=milestone.id,
                    title=f"{milestone.name} (Due)",
                    description=milestone.description,
                    date=milestone.due_date,
                    event_type=EventType.MILESTONE,
                    category=EventCategory.DEADLINE,
                    status=milestone.status,
                    project_id=project.id,
                    project_name=project.name,
                    url=f"/projects/{project.id}/milestones/{milestone.id}",
                    color=self._get_status_color(milestone.status),
                    icon="milestone",
                )
            )

        return events

    async def _get_initiative_events(
        self,
        start_date: datetime,
        end_date: datetime,
        filter_params: CalendarEventFilter | None,
    ) -> list[CalendarEvent]:
        """Get events from initiatives."""
        if filter_params and filter_params.event_types:
            if EventType.INITIATIVE not in filter_params.event_types:
                return []

        events = []

        # Get initiative start dates
        query_start = (
            select(Initiative, Project)
            .outerjoin(Project, Initiative.project_id == Project.id)
            .where(
                and_(
                    Initiative.start_date.isnot(None),
                    Initiative.start_date >= start_date,
                    Initiative.start_date <= end_date,
                )
            )
        )

        if filter_params and filter_params.project_ids:
            query_start = query_start.where(Initiative.project_id.in_(filter_params.project_ids))

        result = await self._session.execute(query_start)
        for initiative, project in result.all():
            events.append(
                CalendarEvent(
                    id=initiative.id,
                    title=f"{initiative.name} (Start)",
                    description=initiative.description,
                    date=initiative.start_date,
                    event_type=EventType.INITIATIVE,
                    category=EventCategory.START,
                    status=initiative.status,
                    project_id=project.id if project else None,
                    project_name=project.name if project else None,
                    url=f"/initiatives/{initiative.id}",
                    color=self._get_status_color(initiative.status),
                    icon="initiative",
                )
            )

        # Get initiative target dates
        query_target = (
            select(Initiative, Project)
            .outerjoin(Project, Initiative.project_id == Project.id)
            .where(
                and_(
                    Initiative.target_date.isnot(None),
                    Initiative.target_date >= start_date,
                    Initiative.target_date <= end_date,
                )
            )
        )

        if filter_params and filter_params.project_ids:
            query_target = query_target.where(Initiative.project_id.in_(filter_params.project_ids))

        result = await self._session.execute(query_target)
        for initiative, project in result.all():
            events.append(
                CalendarEvent(
                    id=initiative.id,
                    title=f"{initiative.name} (Target)",
                    description=initiative.description,
                    date=initiative.target_date,
                    event_type=EventType.INITIATIVE,
                    category=EventCategory.DEADLINE,
                    status=initiative.status,
                    project_id=project.id if project else None,
                    project_name=project.name if project else None,
                    url=f"/initiatives/{initiative.id}",
                    color=self._get_status_color(initiative.status),
                    icon="initiative",
                )
            )

        return events

    async def _get_podcast_events(
        self,
        start_date: datetime,
        end_date: datetime,
        filter_params: CalendarEventFilter | None,
    ) -> list[CalendarEvent]:
        """Get events from podcast episodes."""
        if filter_params and filter_params.event_types:
            if EventType.PODCAST_EPISODE not in filter_params.event_types:
                return []

        query = select(PodcastEpisode).where(
            and_(
                PodcastEpisode.published_at.isnot(None),
                PodcastEpisode.published_at >= start_date,
                PodcastEpisode.published_at <= end_date,
            )
        )

        result = await self._session.execute(query)
        episodes = result.scalars().all()

        events = []
        for episode in episodes:
            events.append(
                CalendarEvent(
                    id=episode.id,
                    title=episode.title,
                    description=episode.description,
                    date=episode.published_at,
                    event_type=EventType.PODCAST_EPISODE,
                    category=EventCategory.RELEASE,
                    url=f"/podcasts/{episode.show_id}/episodes/{episode.id}",
                    color="#8B5CF6",  # Purple for podcasts
                    icon="podcast",
                )
            )

        return events

    async def _get_literature_events(
        self,
        start_date: datetime,
        end_date: datetime,
        filter_params: CalendarEventFilter | None,
    ) -> list[CalendarEvent]:
        """Get events from literature."""
        if filter_params and filter_params.event_types:
            if EventType.LITERATURE not in filter_params.event_types:
                return []

        query = select(Literature).where(
            and_(
                Literature.published_at.isnot(None),
                Literature.published_at >= start_date,
                Literature.published_at <= end_date,
            )
        )

        result = await self._session.execute(query)
        items = result.scalars().all()

        events = []
        for item in items:
            events.append(
                CalendarEvent(
                    id=item.id,
                    title=item.title,
                    description=f"{item.type.title()} by {item.author}" if item.author else item.type.title(),
                    date=item.published_at,
                    event_type=EventType.LITERATURE,
                    category=EventCategory.RELEASE,
                    url=f"/literature/{item.id}",
                    color="#10B981",  # Green for literature
                    icon="book",
                )
            )

        return events

    async def get_stats(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> CalendarStats:
        """Get statistics about calendar events."""
        response = await self.get_events(start_date, end_date)
        events = response.events

        # Calculate stats
        by_type = {}
        by_category = {}

        for event in events:
            # Count by type
            type_key = event.event_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

            # Count by category
            cat_key = event.category.value
            by_category[cat_key] = by_category.get(cat_key, 0) + 1

        # Count upcoming (next 7 days)
        now = datetime.now(timezone.utc)
        seven_days = now + timedelta(days=7)
        upcoming_count = sum(1 for e in events if now <= e.date <= seven_days)

        # Count overdue (past deadlines for incomplete items)
        overdue_count = sum(
            1
            for e in events
            if e.category == EventCategory.DEADLINE
            and e.date < now
            and e.status not in ["closed", "completed", "cancelled"]
        )

        return CalendarStats(
            total_events=len(events),
            by_type=by_type,
            by_category=by_category,
            upcoming_count=upcoming_count,
            overdue_count=overdue_count,
        )

    @staticmethod
    def _get_priority_color(priority: str) -> str:
        """Get color based on priority."""
        colors = {
            "critical": "#EF4444",  # Red
            "high": "#F59E0B",  # Amber
            "medium": "#3B82F6",  # Blue
            "low": "#6B7280",  # Gray
        }
        return colors.get(priority, "#6B7280")

    @staticmethod
    def _get_status_color(status: str) -> str:
        """Get color based on status."""
        colors = {
            "open": "#3B82F6",  # Blue
            "planned": "#3B82F6",  # Blue
            "planning": "#3B82F6",  # Blue
            "in_progress": "#8B5CF6",  # Purple
            "review": "#F59E0B",  # Amber
            "testing": "#F59E0B",  # Amber
            "completed": "#10B981",  # Green
            "closed": "#10B981",  # Green
            "cancelled": "#6B7280",  # Gray
            "on_hold": "#6B7280",  # Gray
        }
        return colors.get(status, "#3B82F6")

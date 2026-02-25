"""Issue service for business logic operations."""

import logging
from datetime import datetime
from uuid import UUID

from turbo.core.repositories.issue import IssueRepository
from turbo.core.repositories.issue_dependency import IssueDependencyRepository
from turbo.core.repositories.milestone import MilestoneRepository
from turbo.core.repositories.project import ProjectRepository
from turbo.core.repositories.work_log import WorkLogRepository
from turbo.core.schemas.issue import (
    IssueCreate,
    IssueResponse,
    IssueUpdate,
)
from turbo.core.schemas.graph import GraphNodeCreate
from turbo.core.schemas.work_log import WorkLogCreate, WorkLogResponse
from turbo.core.services.graph import GraphService
from turbo.core.utils import strip_emojis
from turbo.utils.config import get_settings
from turbo.utils.exceptions import IssueNotFoundError, ProjectNotFoundError

logger = logging.getLogger(__name__)


class IssueService:
    """Service for issue business logic."""

    def __init__(
        self,
        issue_repository: IssueRepository,
        project_repository: ProjectRepository,
        milestone_repository: MilestoneRepository,
        dependency_repository: IssueDependencyRepository,
        work_log_repository: WorkLogRepository | None = None,
        webhook_service=None,  # Optional - for event emission
        key_generator_service=None,  # Optional - for key generation
        worktree_service=None,  # Optional - for git worktree management
    ) -> None:
        self._issue_repository = issue_repository
        self._project_repository = project_repository
        self._milestone_repository = milestone_repository
        self._dependency_repository = dependency_repository
        self._work_log_repository = work_log_repository
        self._webhook_service = webhook_service
        self._key_generator = key_generator_service
        self._worktree_service = worktree_service
        self._settings = get_settings()

    async def _index_issue_in_graph(self, issue) -> None:
        """
        Index an issue in the knowledge graph for semantic search.

        This is called automatically when issues are created or updated.
        Failures are logged but don't affect the main operation.

        Args:
            issue: The issue model instance to index
        """
        # Only index if graph is enabled
        if not self._settings.graph.enabled:
            return

        try:
            # Build content string from issue data
            content_parts = [
                f"Title: {issue.title}",
                f"\nDescription:\n{issue.description}",
                f"\nType: {issue.type}",
                f"Status: {issue.status}",
                f"Priority: {issue.priority}",
            ]

            if issue.assignee:
                content_parts.append(f"Assignee: {issue.assignee}")

            if issue.discovery_status:
                content_parts.append(f"Discovery Status: {issue.discovery_status}")

            content = "\n".join(content_parts)

            # Create node data for graph
            node_data = GraphNodeCreate(
                entity_id=issue.id,
                entity_type="issue",
                content=content,
                metadata={
                    "title": issue.title,
                    "type": issue.type,
                    "status": issue.status,
                    "priority": issue.priority,
                    "project_id": str(issue.project_id) if issue.project_id else None,
                },
            )

            # Index in graph
            graph_service = GraphService()
            try:
                await graph_service.add_episode(node_data)
                logger.debug(f"Indexed issue {issue.id} in knowledge graph")
            finally:
                await graph_service.close()

        except Exception as e:
            # Log error but don't fail the main operation
            logger.warning(f"Failed to index issue {issue.id} in knowledge graph: {e}")

    async def _enrich_issue_with_dependencies(self, issue) -> IssueResponse:
        """Helper to enrich an issue with dependency information."""
        issue_response = IssueResponse.model_validate(issue)
        deps = await self._dependency_repository.get_all_dependencies(issue.id)
        issue_response.blocking = deps["blocking"]
        issue_response.blocked_by = deps["blocked_by"]
        return issue_response

    async def create_issue(self, issue_data: IssueCreate) -> IssueResponse:
        """Create a new issue."""
        # Strip emojis from text fields
        if issue_data.title:
            issue_data.title = strip_emojis(issue_data.title)
        if issue_data.description:
            issue_data.description = strip_emojis(issue_data.description)

        # Validate project_id requirements
        if issue_data.type == "discovery":
            # Discovery issues can exist without a project
            if issue_data.project_id:
                # If project_id provided, verify it exists
                project = await self._project_repository.get_by_id(issue_data.project_id)
                if not project:
                    raise ProjectNotFoundError(issue_data.project_id)
        else:
            # Non-discovery issues require a project
            if not issue_data.project_id:
                raise ValueError("Non-discovery issues must be associated with a project")
            project = await self._project_repository.get_by_id(issue_data.project_id)
            if not project:
                raise ProjectNotFoundError(issue_data.project_id)

        # Validate discovery status
        if issue_data.type == "discovery" and not issue_data.discovery_status:
            # Set default discovery_status for discovery issues
            issue_data.discovery_status = "proposed"
        elif issue_data.type != "discovery" and issue_data.discovery_status:
            # Clear discovery_status for non-discovery issues
            issue_data.discovery_status = None

        # Extract milestone IDs before creating the issue
        milestone_ids = issue_data.milestone_ids

        # Generate issue key if project_id exists and key generator is available
        issue_dict = issue_data.model_dump(exclude={"milestone_ids"})
        if issue_data.project_id and self._key_generator:
            issue_key, issue_number = await self._key_generator.generate_entity_key(
                issue_data.project_id, "issue"
            )
            issue_dict["issue_key"] = issue_key
            issue_dict["issue_number"] = issue_number

        # Create issue without milestone_ids field
        issue = await self._issue_repository.create(IssueCreate(**issue_dict))

        # Commit the issue first
        await self._issue_repository._session.commit()
        await self._issue_repository._session.refresh(issue)

        # Handle milestone associations after commit
        if milestone_ids:
            # Reload issue to get the relationships collection
            await self._issue_repository._session.refresh(issue, ["milestones"])
            for milestone_id in milestone_ids:
                milestone = await self._milestone_repository.get_by_id(milestone_id)
                if milestone:
                    issue.milestones.append(milestone)
            await self._issue_repository._session.commit()
            await self._issue_repository._session.refresh(issue)

        # Index in knowledge graph for semantic search
        await self._index_issue_in_graph(issue)

        return IssueResponse.model_validate(issue)

    async def get_issue_by_id(self, issue_id: UUID) -> IssueResponse:
        """Get issue by ID with dependencies."""
        issue = await self._issue_repository.get_by_id(issue_id)
        if not issue:
            raise IssueNotFoundError(issue_id)
        return await self._enrich_issue_with_dependencies(issue)

    async def get_issue_by_key(self, issue_key: str) -> IssueResponse | None:
        """Get issue by key (e.g., 'TURBOCODE-1') with dependencies."""
        issue = await self._issue_repository.get_by_key(issue_key)
        if not issue:
            return None
        return await self._enrich_issue_with_dependencies(issue)

    async def get_all_issues(
        self, limit: int | None = None, offset: int | None = None, sort_by: str | None = None, sort_order: str = "desc"
    ) -> list[IssueResponse]:
        """Get all issues with optional pagination."""
        issues = await self._issue_repository.get_all(limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order)
        return [IssueResponse.model_validate(issue) for issue in issues]

    async def get_issues_by_workspace(
        self,
        workspace: str,
        work_company: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        sort_order: str = "desc",
    ) -> list[IssueResponse]:
        """Get issues filtered by workspace."""
        issues = await self._issue_repository.get_by_workspace(
            workspace=workspace,
            work_company=work_company,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return [IssueResponse.model_validate(issue) for issue in issues]

    async def update_issue(
        self, issue_id: UUID, update_data: IssueUpdate
    ) -> IssueResponse:
        """Update an issue."""
        # Strip emojis from text fields
        if update_data.title:
            update_data.title = strip_emojis(update_data.title)
        if update_data.description:
            update_data.description = strip_emojis(update_data.description)

        issue = await self._issue_repository.get_by_id(issue_id)
        if not issue:
            raise IssueNotFoundError(issue_id)

        # Track if status changed to 'ready'
        old_status = issue.status
        status_changed_to_ready = update_data.status == "ready" and old_status != "ready"

        # Update basic fields
        issue = await self._issue_repository.update(issue_id, update_data)
        if not issue:
            raise IssueNotFoundError(issue_id)

        # Handle milestone associations
        if update_data.milestone_ids is not None:
            issue.milestones.clear()
            for milestone_id in update_data.milestone_ids:
                milestone = await self._milestone_repository.get_by_id(milestone_id)
                if milestone:
                    issue.milestones.append(milestone)
            await self._issue_repository._session.commit()
            await self._issue_repository._session.refresh(issue)

        # Re-index in knowledge graph to update search
        await self._index_issue_in_graph(issue)

        # Emit webhook event if issue was assigned
        if self._webhook_service and update_data.assigned_to_id is not None:
            try:
                issue_response = IssueResponse.model_validate(issue)
                payload = {
                    "issue": issue_response.model_dump(mode="json"),
                    "assigned_to_type": issue.assigned_to_type,
                    "assigned_to_id": str(issue.assigned_to_id) if issue.assigned_to_id else None,
                    "project_id": str(issue.project_id) if issue.project_id else None,
                }
                await self._webhook_service.emit_event("issue.assigned", payload)
                logger.info(f"Emitted issue.assigned event for issue {issue_id}")
            except Exception as e:
                # Log webhook errors but don't fail the update
                logger.error(f"Failed to emit webhook for issue {issue_id}: {str(e)}")

        # Emit webhook event if status changed to 'ready' for automatic subagent spawning
        if self._webhook_service and status_changed_to_ready:
            try:
                issue_response = IssueResponse.model_validate(issue)
                payload = {
                    "issue": issue_response.model_dump(mode="json"),
                    "old_status": old_status,
                    "new_status": "ready",
                    "project_id": str(issue.project_id) if issue.project_id else None,
                }
                await self._webhook_service.emit_event("issue.ready", payload)
                logger.info(f"Emitted issue.ready event for issue {issue_id}")
            except Exception as e:
                # Log webhook errors but don't fail the update
                logger.error(f"Failed to emit issue.ready webhook for issue {issue_id}: {str(e)}")

        return IssueResponse.model_validate(issue)

    async def delete_issue(self, issue_id: UUID) -> bool:
        """Delete an issue."""
        success = await self._issue_repository.delete(issue_id)
        if not success:
            raise IssueNotFoundError(issue_id)
        return success

    async def assign_issue(self, issue_id: UUID, assignee: str) -> IssueResponse:
        """Assign an issue to someone."""
        update_data = IssueUpdate(assignee=assignee)
        issue = await self._issue_repository.update(issue_id, update_data)
        if not issue:
            raise IssueNotFoundError(issue_id)
        return IssueResponse.model_validate(issue)

    async def unassign_issue(self, issue_id: UUID) -> IssueResponse:
        """Remove assignee from an issue."""
        update_data = IssueUpdate(assignee=None)
        issue = await self._issue_repository.update(issue_id, update_data)
        if not issue:
            raise IssueNotFoundError(issue_id)
        return IssueResponse.model_validate(issue)

    async def close_issue(self, issue_id: UUID) -> IssueResponse:
        """Close an issue."""
        update_data = IssueUpdate(status="closed")
        issue = await self._issue_repository.update(issue_id, update_data)
        if not issue:
            raise IssueNotFoundError(issue_id)
        return IssueResponse.model_validate(issue)

    async def reopen_issue(self, issue_id: UUID) -> IssueResponse:
        """Reopen a closed issue."""
        update_data = IssueUpdate(status="open")
        issue = await self._issue_repository.update(issue_id, update_data)
        if not issue:
            raise IssueNotFoundError(issue_id)
        return IssueResponse.model_validate(issue)

    async def start_work_on_issue(self, issue_id: UUID) -> IssueResponse:
        """Mark issue as in progress."""
        update_data = IssueUpdate(status="in_progress")
        issue = await self._issue_repository.update(issue_id, update_data)
        if not issue:
            raise IssueNotFoundError(issue_id)
        return IssueResponse.model_validate(issue)

    async def get_issues_by_project(self, project_id: UUID, sort_by: str | None = None, sort_order: str = "desc") -> list[IssueResponse]:
        """Get all issues for a project."""
        # Verify project exists
        project = await self._project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(project_id)

        issues = await self._issue_repository.get_by_project(project_id, sort_by=sort_by, sort_order=sort_order)
        return [IssueResponse.model_validate(issue) for issue in issues]

    async def get_issues_by_status(self, status: str, sort_by: str | None = None, sort_order: str = "desc") -> list[IssueResponse]:
        """Get issues by status."""
        issues = await self._issue_repository.get_by_status(status, sort_by=sort_by, sort_order=sort_order)
        return [IssueResponse.model_validate(issue) for issue in issues]

    async def get_issues_by_assignee(self, assignee: str, sort_by: str | None = None, sort_order: str = "desc") -> list[IssueResponse]:
        """Get issues assigned to a specific person."""
        issues = await self._issue_repository.get_by_assignee(assignee, sort_by=sort_by, sort_order=sort_order)
        return [IssueResponse.model_validate(issue) for issue in issues]

    async def get_open_issues(self) -> list[IssueResponse]:
        """Get all open issues."""
        issues = await self._issue_repository.get_open_issues()
        return [IssueResponse.model_validate(issue) for issue in issues]

    async def get_closed_issues(self) -> list[IssueResponse]:
        """Get all closed issues."""
        issues = await self._issue_repository.get_closed_issues()
        return [IssueResponse.model_validate(issue) for issue in issues]

    async def get_unassigned_issues(self) -> list[IssueResponse]:
        """Get issues without assignee."""
        issues = await self._issue_repository.get_unassigned_issues()
        return [IssueResponse.model_validate(issue) for issue in issues]

    async def get_high_priority_issues(self) -> list[IssueResponse]:
        """Get high priority and critical issues."""
        issues = await self._issue_repository.get_high_priority_issues()
        return [IssueResponse.model_validate(issue) for issue in issues]

    async def search_issues(self, title_pattern: str) -> list[IssueResponse]:
        """Search issues by title pattern."""
        issues = await self._issue_repository.search_by_title(title_pattern)
        return [IssueResponse.model_validate(issue) for issue in issues]

    async def get_project_open_issues(self, project_id: UUID) -> list[IssueResponse]:
        """Get open issues for a specific project."""
        # Verify project exists
        project = await self._project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(project_id)

        issues = await self._issue_repository.get_project_open_issues(project_id)
        return [IssueResponse.model_validate(issue) for issue in issues]

    async def get_project_closed_issues(self, project_id: UUID) -> list[IssueResponse]:
        """Get closed issues for a specific project."""
        # Verify project exists
        project = await self._project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(project_id)

        issues = await self._issue_repository.get_project_closed_issues(project_id)
        return [IssueResponse.model_validate(issue) for issue in issues]

    # Work Queue Methods

    async def get_work_queue(
        self,
        status: str | None = None,
        priority: str | None = None,
        limit: int | None = 100,
        offset: int | None = 0,
        include_unranked: bool = False,
    ) -> list[IssueResponse]:
        """
        Get work queue - issues sorted by work_rank.

        Args:
            status: Optional status filter
            priority: Optional priority filter
            limit: Maximum number of results
            offset: Offset for pagination
            include_unranked: If True, include issues without work_rank

        Returns:
            List of issues sorted by work_rank (ascending)
        """
        issues = await self._issue_repository.get_work_queue(
            status=status,
            priority=priority,
            limit=limit,
            offset=offset,
            include_unranked=include_unranked,
        )
        return [IssueResponse.model_validate(issue) for issue in issues]

    async def get_next_issue(self) -> IssueResponse | None:
        """
        Get THE next issue to work on (highest ranked).

        Returns the issue with the lowest work_rank value (highest priority)
        that is in open or in_progress status.

        Returns:
            The next issue to work on, or None if no ranked issues exist
        """
        issue = await self._issue_repository.get_next_issue()
        if issue:
            return IssueResponse.model_validate(issue)
        return None

    async def set_work_rank(
        self, issue_id: UUID, work_rank: int | None
    ) -> IssueResponse:
        """
        Set or clear work rank for an issue.

        Args:
            issue_id: ID of the issue
            work_rank: New rank (1=highest priority) or None to remove from queue

        Returns:
            Updated issue

        Raises:
            IssueNotFoundError: If issue doesn't exist
        """
        from datetime import datetime

        issue = await self._issue_repository.get_by_id(issue_id)
        if not issue:
            raise IssueNotFoundError(issue_id)

        # Update rank and timestamp
        issue.work_rank = work_rank
        issue.last_ranked_at = datetime.utcnow() if work_rank is not None else None

        # Commit the changes (issue is already an ORM object)
        await self._issue_repository._session.commit()
        await self._issue_repository._session.refresh(issue)
        return IssueResponse.model_validate(issue)

    async def bulk_rerank(self, issue_ranks: list[dict]) -> int:
        """
        Bulk update work ranks for multiple issues.

        Args:
            issue_ranks: List of dicts with 'issue_id' and 'rank' keys

        Returns:
            Number of issues updated

        Example:
            await bulk_rerank([
                {"issue_id": "uuid1", "rank": 1},
                {"issue_id": "uuid2", "rank": 2},
            ])
        """
        from datetime import datetime

        updated_count = 0
        now = datetime.utcnow()

        for item in issue_ranks:
            issue_id = UUID(item["issue_id"])
            rank = item["rank"]

            issue = await self._issue_repository.get_by_id(issue_id)
            if issue:
                issue.work_rank = rank
                issue.last_ranked_at = now
                await self._issue_repository.update(issue)
                updated_count += 1

        return updated_count

    async def auto_rank_issues(self) -> int:
        """
        Auto-rank all open/in_progress issues using intelligent scoring.

        Ranking factors:
        - Priority (critical=100, high=50, medium=25, low=10)
        - Age (older issues get higher priority)
        - Blockers (issues not blocked rank higher)
        - Dependencies (issues that block others rank higher)

        Returns:
            Number of issues ranked
        """
        from datetime import datetime

        # Get all open and in_progress issues
        issues = await self._issue_repository.get_all()
        eligible_issues = [
            i for i in issues if i.status in ["open", "in_progress"]
        ]

        if not eligible_issues:
            return 0

        # Calculate scores for each issue
        scored_issues = []
        for issue in eligible_issues:
            score = await self._calculate_auto_rank_score(issue)
            scored_issues.append((issue, score))

        # Sort by score (descending) and assign ranks
        scored_issues.sort(key=lambda x: x[1], reverse=True)

        now = datetime.utcnow()
        for rank, (issue, score) in enumerate(scored_issues, start=1):
            # Directly update the issue object
            issue.work_rank = rank
            issue.last_ranked_at = now

        # Flush and commit all changes at once
        await self._issue_repository._session.flush()
        await self._issue_repository._session.commit()

        return len(scored_issues)

    async def _calculate_auto_rank_score(self, issue) -> float:
        """Calculate auto-ranking score for an issue."""
        from datetime import datetime

        score = 0.0

        # Priority weight (most important factor)
        priority_weights = {"critical": 100, "high": 50, "medium": 25, "low": 10}
        score += priority_weights.get(issue.priority, 25)

        # Age factor (older issues get higher priority)
        age_days = (datetime.utcnow() - issue.created_at.replace(tzinfo=None)).days
        score += min(age_days * 0.5, 20)  # Cap at 20 points

        # Blocker penalty (check if issue is blocked)
        blockers = await self._dependency_repository.get_blocking_issues(issue.id)
        if blockers:
            score -= 15  # Reduce priority if blocked

        # Dependency boost (issues that block others are more important)
        blocked_issues = await self._dependency_repository.get_blocked_issues(issue.id)
        score += len(blocked_issues) * 5  # +5 points per issue blocked

        return score

    async def start_work(
        self, issue_id: UUID, started_by: str, project_path: str | None = None
    ) -> tuple[IssueResponse, WorkLogResponse]:
        """
        Start work on an issue (ready -> in_progress).

        This method:
        1. Validates issue is in 'ready' status
        2. Updates status to 'in_progress'
        3. Creates a git worktree (if project_path provided and worktree service available)
        4. Creates a work log entry
        5. Adds an automatic comment

        Args:
            issue_id: ID of the issue
            started_by: Who is starting work ('user', 'ai:context', 'ai:turbo')
            project_path: Path to project git repository (optional, for worktree creation)

        Returns:
            Tuple of (updated issue, new work log)

        Raises:
            IssueNotFoundError: If issue doesn't exist
            ValueError: If issue is not in 'ready' status or work is already active
        """
        if not self._work_log_repository:
            raise RuntimeError("WorkLogRepository not initialized")

        # Get the issue
        issue = await self._issue_repository.get_by_id(issue_id)
        if not issue:
            raise IssueNotFoundError(issue_id)

        # Validate status
        if issue.status != "ready":
            raise ValueError(
                f"Cannot start work on issue with status '{issue.status}'. "
                f"Issue must be in 'ready' status."
            )

        # Check for active work log
        active_log = await self._work_log_repository.get_active_work_log(issue_id)
        if active_log:
            raise ValueError(
                f"Work is already in progress on this issue (started by {active_log.started_by})"
            )

        # Create git worktree if service and path provided
        worktree_info = None
        if self._worktree_service and project_path and issue.issue_key:
            try:
                worktree_info = await self._worktree_service.create_worktree(
                    issue_id=issue_id,
                    project_path=project_path,
                    base_branch="main"
                )
                logger.info(
                    f"Created worktree for {issue.issue_key} at {worktree_info['worktree_path']}"
                )
            except Exception as e:
                logger.warning(f"Failed to create worktree for {issue.issue_key}: {e}")
                # Don't fail the start_work operation if worktree creation fails

        # Update issue status
        issue.status = "in_progress"
        await self._issue_repository._session.commit()
        await self._issue_repository._session.refresh(issue)

        # Create work log with worktree path if available
        work_log_data = WorkLogCreate(
            issue_id=issue_id,
            started_by=started_by,
            started_at=datetime.utcnow(),
        )
        work_log = await self._work_log_repository.create(work_log_data)

        # Store worktree path in work log if created
        if worktree_info:
            work_log.worktree_path = worktree_info['worktree_path']
            work_log.branch_name = worktree_info['branch_name']
            await self._work_log_repository._session.commit()
            await self._work_log_repository._session.refresh(work_log)

        # Add automatic comment
        from turbo.core.models.comment import Comment

        comment = Comment(
            entity_type="issue",
            entity_id=issue_id,
            content=f"Work started by {started_by}",
            author_type="ai" if started_by.startswith("ai:") else "user",
            author_name=started_by,
        )
        self._issue_repository._session.add(comment)
        await self._issue_repository._session.commit()
        await self._issue_repository._session.refresh(comment)

        return (
            IssueResponse.model_validate(issue),
            WorkLogResponse.model_validate(work_log),
        )

    async def submit_for_review(
        self, issue_id: UUID, commit_url: str, cleanup_worktree: bool = True
    ) -> tuple[IssueResponse, WorkLogResponse]:
        """
        Submit issue for review (in_progress -> review).

        This method:
        1. Validates issue is in 'in_progress' status
        2. Validates there's an active work log
        3. Updates status to 'review'
        4. Ends the work log with commit URL
        5. Cleans up git worktree (if enabled and service available)
        6. Adds an automatic comment

        Args:
            issue_id: ID of the issue
            commit_url: Git commit URL for the work
            cleanup_worktree: Whether to remove worktree after completion (default: True)

        Returns:
            Tuple of (updated issue, completed work log)

        Raises:
            IssueNotFoundError: If issue doesn't exist
            ValueError: If issue is not in 'in_progress' status or no active work log
        """
        if not self._work_log_repository:
            raise RuntimeError("WorkLogRepository not initialized")

        # Get the issue
        issue = await self._issue_repository.get_by_id(issue_id)
        if not issue:
            raise IssueNotFoundError(issue_id)

        # Validate status
        if issue.status != "in_progress":
            raise ValueError(
                f"Cannot submit issue with status '{issue.status}'. "
                f"Issue must be in 'in_progress' status."
            )

        # Get active work log
        work_log = await self._work_log_repository.get_active_work_log(issue_id)
        if not work_log:
            raise ValueError("No active work log found for this issue")

        # Clean up git worktree if enabled and worktree exists
        if cleanup_worktree and self._worktree_service and work_log.worktree_path:
            try:
                # Check for uncommitted changes before removing
                if work_log.worktree_path:
                    status = await self._worktree_service.get_worktree_status(
                        work_log.worktree_path
                    )
                    if status['has_changes']:
                        logger.warning(
                            f"Worktree at {work_log.worktree_path} has uncommitted changes. "
                            f"Forcing removal."
                        )

                # Remove worktree (force=True to handle uncommitted changes)
                removed = await self._worktree_service.remove_worktree(
                    issue_id=issue_id,
                    force=True
                )
                if removed:
                    logger.info(f"Removed worktree for {issue.issue_key}")
            except Exception as e:
                logger.warning(f"Failed to remove worktree for {issue.issue_key}: {e}")
                # Don't fail the submit operation if worktree cleanup fails

        # Update issue status
        issue.status = "review"
        await self._issue_repository._session.commit()
        await self._issue_repository._session.refresh(issue)

        # End work log
        work_log.ended_at = datetime.utcnow()
        work_log.commit_url = commit_url
        await self._work_log_repository._session.commit()
        await self._work_log_repository._session.refresh(work_log)

        # Add automatic comment
        from turbo.core.repositories.comment import CommentRepository
        from turbo.core.schemas.comment import CommentCreate

        comment_repo = CommentRepository(self._issue_repository._session)
        time_spent = work_log.time_spent_minutes or 0
        comment_data = CommentCreate(
            entity_type="issue",
            entity_id=issue_id,
            content=f"Work completed by {work_log.started_by} (Time: {time_spent} minutes)\nCommit: {commit_url}",
            author_type="ai" if work_log.started_by.startswith("ai:") else "user",
            author_name=work_log.started_by,
        )
        await comment_repo.create(comment_data)

        return (
            IssueResponse.model_validate(issue),
            WorkLogResponse.model_validate(work_log),
        )

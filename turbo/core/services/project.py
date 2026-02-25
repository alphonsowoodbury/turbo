"""Project service for business logic operations."""

from typing import Any
from uuid import UUID

from turbo.core.repositories.document import DocumentRepository
from turbo.core.repositories.issue import IssueRepository
from turbo.core.repositories.project import ProjectRepository
from turbo.core.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ProjectWithStats,
)
from turbo.core.utils import strip_emojis
from turbo.utils.exceptions import ProjectNotFoundError


class ProjectService:
    """Service for project business logic."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        issue_repository: IssueRepository,
        document_repository: DocumentRepository,
        key_generator_service=None,  # Optional - for key validation
    ) -> None:
        self._project_repository = project_repository
        self._issue_repository = issue_repository
        self._document_repository = document_repository
        self._key_generator = key_generator_service

    async def create_project(self, project_data: ProjectCreate) -> ProjectResponse:
        """Create a new project."""
        # Strip emojis from text fields
        if project_data.name:
            project_data.name = strip_emojis(project_data.name)
        if project_data.description:
            project_data.description = strip_emojis(project_data.description)

        # Validate project key if key generator is available
        if self._key_generator and project_data.project_key:
            # Validate format
            is_valid, error_msg = self._key_generator.validate_project_key(project_data.project_key)
            if not is_valid:
                raise ValueError(f"Invalid project key: {error_msg}")

            # Check availability
            is_available = await self._key_generator.is_project_key_available(project_data.project_key)
            if not is_available:
                raise ValueError(f"Project key '{project_data.project_key}' is already in use")

        project = await self._project_repository.create(project_data)
        return ProjectResponse.model_validate(project)

    async def get_project_by_id(self, project_id: UUID) -> ProjectResponse:
        """Get project by ID."""
        project = await self._project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(project_id)
        return ProjectResponse.model_validate(project)

    async def get_all_projects(
        self, limit: int | None = None, offset: int | None = None, sort_by: str | None = None, sort_order: str = "desc"
    ) -> list[ProjectResponse]:
        """Get all projects with optional pagination."""
        projects = await self._project_repository.get_all(limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order)
        return [ProjectResponse.model_validate(project) for project in projects]

    async def update_project(
        self, project_id: UUID, update_data: ProjectUpdate
    ) -> ProjectResponse:
        """Update a project."""
        # Strip emojis from text fields
        if update_data.name:
            update_data.name = strip_emojis(update_data.name)
        if update_data.description:
            update_data.description = strip_emojis(update_data.description)

        project = await self._project_repository.update(project_id, update_data)
        if not project:
            raise ProjectNotFoundError(project_id)
        return ProjectResponse.model_validate(project)

    async def delete_project(self, project_id: UUID) -> bool:
        """Delete a project."""
        success = await self._project_repository.delete(project_id)
        if not success:
            raise ProjectNotFoundError(project_id)
        return success

    async def archive_project(self, project_id: UUID) -> ProjectResponse:
        """Archive a project."""
        update_data = ProjectUpdate(is_archived=True)
        return await self.update_project(project_id, update_data)

    async def unarchive_project(self, project_id: UUID) -> ProjectResponse:
        """Unarchive a project."""
        update_data = ProjectUpdate(is_archived=False)
        return await self.update_project(project_id, update_data)

    async def get_project_statistics(self, project_id: UUID) -> dict[str, Any]:
        """Get project statistics including issue counts and completion rates."""
        # Verify project exists
        project = await self._project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(project_id)

        # Get project issues
        issues = await self._issue_repository.get_by_project(project_id)

        # Calculate statistics
        total_issues = len(issues)
        open_issues = len([issue for issue in issues if issue.status == "open"])
        closed_issues = len([issue for issue in issues if issue.status == "closed"])
        in_progress_issues = len(
            [issue for issue in issues if issue.status == "in_progress"]
        )

        completion_rate = 0.0
        if total_issues > 0:
            completion_rate = (closed_issues / total_issues) * 100

        return {
            "project_id": project_id,
            "total_issues": total_issues,
            "open_issues": open_issues,
            "closed_issues": closed_issues,
            "in_progress_issues": in_progress_issues,
            "completion_rate": completion_rate,
        }

    async def get_project_with_stats(self, project_id: UUID) -> ProjectWithStats:
        """Get project with statistics included."""
        # Get basic project info
        project_response = await self.get_project_by_id(project_id)

        # Get statistics
        stats = await self.get_project_statistics(project_id)

        # Combine into ProjectWithStats
        return ProjectWithStats(
            **project_response.model_dump(),
            total_issues=stats["total_issues"],
            open_issues=stats["open_issues"],
            closed_issues=stats["closed_issues"],
            completion_rate=stats["completion_rate"],
        )

    async def get_projects_by_status(self, status: str, sort_by: str | None = None, sort_order: str = "desc") -> list[ProjectResponse]:
        """Get projects by status."""
        projects = await self._project_repository.get_by_status(status, sort_by=sort_by, sort_order=sort_order)
        return [ProjectResponse.model_validate(project) for project in projects]

    async def get_active_projects(
        self, limit: int | None = None, offset: int | None = None, sort_by: str | None = None, sort_order: str = "desc"
    ) -> list[ProjectResponse]:
        """Get active (non-archived) projects."""
        projects = await self._project_repository.get_active(limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order)
        return [ProjectResponse.model_validate(project) for project in projects]

    async def get_archived_projects(
        self, limit: int | None = None, offset: int | None = None
    ) -> list[ProjectResponse]:
        """Get archived projects."""
        projects = await self._project_repository.get_archived(
            limit=limit, offset=offset
        )
        return [ProjectResponse.model_validate(project) for project in projects]

    async def search_projects(self, name_pattern: str) -> list[ProjectResponse]:
        """Search projects by name pattern."""
        projects = await self._project_repository.search_by_name(name_pattern)
        return [ProjectResponse.model_validate(project) for project in projects]

    async def get_high_priority_projects(self) -> list[ProjectResponse]:
        """Get high priority and critical projects."""
        projects = await self._project_repository.get_high_priority_projects()
        return [ProjectResponse.model_validate(project) for project in projects]

    async def update_project_completion(
        self, project_id: UUID, completion_percentage: float
    ) -> ProjectResponse:
        """Update project completion percentage."""
        update_data = ProjectUpdate(completion_percentage=completion_percentage)
        return await self.update_project(project_id, update_data)

    async def get_projects_by_workspace(
        self,
        workspace: str,
        work_company: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        sort_order: str = "desc",
    ) -> list[ProjectResponse]:
        """Get projects filtered by workspace."""
        projects = await self._project_repository.get_by_workspace(
            workspace=workspace,
            work_company=work_company,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return [ProjectResponse.model_validate(project) for project in projects]

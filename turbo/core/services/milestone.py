"""Milestone service for business logic operations."""

from uuid import UUID

from sqlalchemy import inspect

from turbo.core.models.milestone import Milestone
from turbo.core.repositories.document import DocumentRepository
from turbo.core.repositories.issue import IssueRepository
from turbo.core.repositories.milestone import MilestoneRepository
from turbo.core.repositories.project import ProjectRepository
from turbo.core.repositories.tag import TagRepository
from turbo.core.schemas.issue import IssueResponse
from turbo.core.schemas.milestone import (
    MilestoneCreate,
    MilestoneResponse,
    MilestoneUpdate,
)
from turbo.core.utils import strip_emojis
from turbo.utils.exceptions import (
    MilestoneNotFoundError,
    ProjectNotFoundError,
)


class MilestoneService:
    """Service for milestone business logic."""

    def __init__(
        self,
        milestone_repository: MilestoneRepository,
        project_repository: ProjectRepository,
        issue_repository: IssueRepository,
        tag_repository: TagRepository,
        document_repository: DocumentRepository,
        key_generator_service=None,  # Optional - for key generation
    ) -> None:
        self._milestone_repository = milestone_repository
        self._project_repository = project_repository
        self._issue_repository = issue_repository
        self._tag_repository = tag_repository
        self._document_repository = document_repository
        self._key_generator = key_generator_service

    async def create_milestone(self, milestone_data: MilestoneCreate) -> MilestoneResponse:
        """Create a new milestone."""
        # Strip emojis from text fields
        if milestone_data.name:
            milestone_data.name = strip_emojis(milestone_data.name)
        if milestone_data.description:
            milestone_data.description = strip_emojis(milestone_data.description)

        # Verify project exists
        project = await self._project_repository.get_by_id(milestone_data.project_id)
        if not project:
            raise ProjectNotFoundError(milestone_data.project_id)

        # Extract association IDs before creating the milestone
        issue_ids = milestone_data.issue_ids
        tag_ids = milestone_data.tag_ids
        document_ids = milestone_data.document_ids

        # Generate milestone key if key generator is available
        milestone_dict = milestone_data.model_dump(exclude={"issue_ids", "tag_ids", "document_ids"})
        if self._key_generator:
            milestone_key, milestone_number = await self._key_generator.generate_entity_key(
                milestone_data.project_id, "milestone"
            )
            milestone_dict["milestone_key"] = milestone_key
            milestone_dict["milestone_number"] = milestone_number

        # Create milestone without association fields
        milestone = await self._milestone_repository.create(MilestoneCreate(**milestone_dict))

        # Commit the milestone first
        await self._milestone_repository._session.commit()
        await self._milestone_repository._session.refresh(milestone)

        # Handle associations after commit
        has_associations = False
        if issue_ids:
            # Reload milestone to get the relationships collection
            session = self._milestone_repository._session
            await session.refresh(milestone, ["issues"])
            for issue_id in issue_ids:
                issue = await self._issue_repository.get_by_id(issue_id)
                if issue:
                    milestone.issues.append(issue)
                    has_associations = True

        if tag_ids:
            await self._milestone_repository._session.refresh(milestone, ["tags"])
            for tag_id in tag_ids:
                tag = await self._tag_repository.get_by_id(tag_id)
                if tag:
                    milestone.tags.append(tag)
                    has_associations = True

        if document_ids:
            await self._milestone_repository._session.refresh(milestone, ["documents"])
            for document_id in document_ids:
                document = await self._document_repository.get_by_id(document_id)
                if document:
                    milestone.documents.append(document)
                    has_associations = True

        # Commit associations if any were added
        if has_associations:
            await self._milestone_repository._session.commit()
            await self._milestone_repository._session.refresh(milestone)

        # Return response with actual counts
        response_dict = {
            "id": milestone.id,
            "name": milestone.name,
            "description": milestone.description,
            "status": milestone.status,
            "start_date": milestone.start_date,
            "due_date": milestone.due_date,
            "project_id": milestone.project_id,
            "milestone_key": milestone.milestone_key,
            "milestone_number": milestone.milestone_number,
            "created_at": milestone.created_at,
            "updated_at": milestone.updated_at,
            "issue_count": len(issue_ids) if issue_ids else 0,
            "tag_count": len(tag_ids) if tag_ids else 0,
            "document_count": len(document_ids) if document_ids else 0,
        }
        return MilestoneResponse(**response_dict)

    async def get_milestone_by_id(self, milestone_id: UUID) -> MilestoneResponse:
        """Get milestone by ID."""
        milestone = await self._milestone_repository.get_with_all_relations(milestone_id)
        if not milestone:
            raise MilestoneNotFoundError(milestone_id)
        return self._to_response(milestone)

    async def get_all_milestones(
        self, limit: int | None = None, offset: int | None = None
    ) -> list[MilestoneResponse]:
        """Get all milestones with optional pagination."""
        milestones = await self._milestone_repository.get_all(limit=limit, offset=offset)
        # For list views, don't try to access relationships - just return basic data
        return [
            MilestoneResponse(
                id=m.id,
                name=m.name,
                description=m.description,
                status=m.status,
                start_date=m.start_date,
                due_date=m.due_date,
                project_id=m.project_id,
                created_at=m.created_at,
                updated_at=m.updated_at,
                issue_count=0,
                tag_count=0,
                document_count=0,
            )
            for m in milestones
        ]

    async def get_milestones_by_project(self, project_id: UUID) -> list[MilestoneResponse]:
        """Get all milestones for a project."""
        # Verify project exists
        project = await self._project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(project_id)

        milestones = await self._milestone_repository.get_by_project(project_id)
        # For list views, don't try to access relationships - just return basic data
        return [
            MilestoneResponse(
                id=m.id,
                name=m.name,
                description=m.description,
                status=m.status,
                start_date=m.start_date,
                due_date=m.due_date,
                project_id=m.project_id,
                created_at=m.created_at,
                updated_at=m.updated_at,
                issue_count=0,
                tag_count=0,
                document_count=0,
            )
            for m in milestones
        ]

    async def update_milestone(
        self, milestone_id: UUID, update_data: MilestoneUpdate
    ) -> MilestoneResponse:
        """Update a milestone."""
        # Strip emojis from text fields
        if update_data.name:
            update_data.name = strip_emojis(update_data.name)
        if update_data.description:
            update_data.description = strip_emojis(update_data.description)

        milestone = await self._milestone_repository.get_by_id(milestone_id)
        if not milestone:
            raise MilestoneNotFoundError(milestone_id)

        # Update basic fields
        milestone = await self._milestone_repository.update(milestone_id, update_data)
        if not milestone:
            raise MilestoneNotFoundError(milestone_id)

        # Handle association updates - refresh relationships before accessing them
        if update_data.issue_ids is not None:
            await self._milestone_repository._session.refresh(milestone, ["issues"])
            milestone.issues.clear()
            for issue_id in update_data.issue_ids:
                issue = await self._issue_repository.get_by_id(issue_id)
                if issue:
                    milestone.issues.append(issue)

        if update_data.tag_ids is not None:
            await self._milestone_repository._session.refresh(milestone, ["tags"])
            milestone.tags.clear()
            for tag_id in update_data.tag_ids:
                tag = await self._tag_repository.get_by_id(tag_id)
                if tag:
                    milestone.tags.append(tag)

        if update_data.document_ids is not None:
            await self._milestone_repository._session.refresh(milestone, ["documents"])
            milestone.documents.clear()
            for document_id in update_data.document_ids:
                document = await self._document_repository.get_by_id(document_id)
                if document:
                    milestone.documents.append(document)

        await self._milestone_repository._session.commit()
        await self._milestone_repository._session.refresh(milestone)

        return self._to_response(milestone)

    async def delete_milestone(self, milestone_id: UUID) -> bool:
        """Delete a milestone."""
        success = await self._milestone_repository.delete(milestone_id)
        if not success:
            raise MilestoneNotFoundError(milestone_id)
        return success

    async def get_milestones_by_status(self, status: str) -> list[MilestoneResponse]:
        """Get milestones by status."""
        milestones = await self._milestone_repository.get_by_status(status)
        # For list views, don't try to access relationships - just return basic data
        return [
            MilestoneResponse(
                id=m.id,
                name=m.name,
                description=m.description,
                status=m.status,
                start_date=m.start_date,
                due_date=m.due_date,
                project_id=m.project_id,
                created_at=m.created_at,
                updated_at=m.updated_at,
                issue_count=0,
                tag_count=0,
                document_count=0,
            )
            for m in milestones
        ]

    async def get_milestones_by_workspace(
        self,
        workspace: str,
        work_company: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[MilestoneResponse]:
        """Get milestones filtered by workspace."""
        milestones = await self._milestone_repository.get_by_workspace(
            workspace=workspace,
            work_company=work_company,
            limit=limit,
            offset=offset,
        )
        # For list views, don't try to access relationships - just return basic data
        return [
            MilestoneResponse(
                id=m.id,
                name=m.name,
                description=m.description,
                status=m.status,
                start_date=m.start_date,
                due_date=m.due_date,
                project_id=m.project_id,
                created_at=m.created_at,
                updated_at=m.updated_at,
                issue_count=0,
                tag_count=0,
                document_count=0,
            )
            for m in milestones
        ]

    async def get_milestone_issues(self, milestone_id: UUID) -> list[IssueResponse]:
        """Get all issues associated with a milestone."""
        milestone = await self._milestone_repository.get_with_issues(milestone_id)
        if not milestone:
            raise MilestoneNotFoundError(milestone_id)

        # Convert issues to IssueResponse
        return [IssueResponse.model_validate(issue) for issue in milestone.issues]

    def _to_response(self, milestone: Milestone) -> MilestoneResponse:
        """Convert milestone model to response.

        Note: Only use this method when relationships have been eagerly loaded
        (e.g., via get_with_all_relations). For list views, construct the
        response directly without accessing relationships.
        """
        # Check if relationships are loaded using SQLAlchemy inspection
        insp = inspect(milestone)

        # Only access relationships if they're loaded (NOT in unloaded set)
        issue_count = len(milestone.issues) if "issues" not in insp.unloaded else 0
        tag_count = len(milestone.tags) if "tags" not in insp.unloaded else 0
        document_count = len(milestone.documents) if "documents" not in insp.unloaded else 0

        response_dict = {
            "id": milestone.id,
            "name": milestone.name,
            "description": milestone.description,
            "status": milestone.status,
            "start_date": milestone.start_date,
            "due_date": milestone.due_date,
            "project_id": milestone.project_id,
            "milestone_key": milestone.milestone_key,
            "milestone_number": milestone.milestone_number,
            "created_at": milestone.created_at,
            "updated_at": milestone.updated_at,
            "issue_count": issue_count,
            "tag_count": tag_count,
            "document_count": document_count,
        }
        return MilestoneResponse(**response_dict)
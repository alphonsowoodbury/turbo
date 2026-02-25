"""Initiative service for business logic operations."""

from uuid import UUID

from sqlalchemy import inspect

from turbo.core.models.initiative import Initiative
from turbo.core.repositories.document import DocumentRepository
from turbo.core.repositories.initiative import InitiativeRepository
from turbo.core.repositories.issue import IssueRepository
from turbo.core.repositories.project import ProjectRepository
from turbo.core.repositories.tag import TagRepository
from turbo.core.schemas.initiative import (
    InitiativeCreate,
    InitiativeResponse,
    InitiativeUpdate,
)
from turbo.core.schemas.issue import IssueResponse
from turbo.core.utils import strip_emojis
from turbo.utils.exceptions import (
    InitiativeNotFoundError,
    ProjectNotFoundError,
)


class InitiativeService:
    """Service for initiative business logic."""

    def __init__(
        self,
        initiative_repository: InitiativeRepository,
        project_repository: ProjectRepository,
        issue_repository: IssueRepository,
        tag_repository: TagRepository,
        document_repository: DocumentRepository,
        key_generator_service=None,  # Optional - for key generation
    ) -> None:
        self._initiative_repository = initiative_repository
        self._project_repository = project_repository
        self._issue_repository = issue_repository
        self._tag_repository = tag_repository
        self._document_repository = document_repository
        self._key_generator = key_generator_service

    async def create_initiative(self, initiative_data: InitiativeCreate) -> InitiativeResponse:
        """Create a new initiative."""
        # Strip emojis from text fields
        if initiative_data.name:
            initiative_data.name = strip_emojis(initiative_data.name)
        if initiative_data.description:
            initiative_data.description = strip_emojis(initiative_data.description)

        # Verify project exists if provided (optional for initiatives)
        if initiative_data.project_id:
            project = await self._project_repository.get_by_id(initiative_data.project_id)
            if not project:
                raise ProjectNotFoundError(initiative_data.project_id)

        # Extract association IDs before creating the initiative
        issue_ids = initiative_data.issue_ids
        tag_ids = initiative_data.tag_ids
        document_ids = initiative_data.document_ids

        # Generate initiative key if project_id exists and key generator is available
        initiative_dict = initiative_data.model_dump(exclude={"issue_ids", "tag_ids", "document_ids"})
        if initiative_data.project_id and self._key_generator:
            initiative_key, initiative_number = await self._key_generator.generate_entity_key(
                initiative_data.project_id, "initiative"
            )
            initiative_dict["initiative_key"] = initiative_key
            initiative_dict["initiative_number"] = initiative_number

        # Create initiative without association fields
        initiative = await self._initiative_repository.create(InitiativeCreate(**initiative_dict))

        # Commit the initiative first
        await self._initiative_repository._session.commit()
        await self._initiative_repository._session.refresh(initiative)

        # Handle associations after commit
        has_associations = False
        if issue_ids:
            # Reload initiative to get the relationships collection
            session = self._initiative_repository._session
            await session.refresh(initiative, ["issues"])
            for issue_id in issue_ids:
                issue = await self._issue_repository.get_by_id(issue_id)
                if issue:
                    initiative.issues.append(issue)
                    has_associations = True

        if tag_ids:
            await self._initiative_repository._session.refresh(initiative, ["tags"])
            for tag_id in tag_ids:
                tag = await self._tag_repository.get_by_id(tag_id)
                if tag:
                    initiative.tags.append(tag)
                    has_associations = True

        if document_ids:
            await self._initiative_repository._session.refresh(initiative, ["documents"])
            for document_id in document_ids:
                document = await self._document_repository.get_by_id(document_id)
                if document:
                    initiative.documents.append(document)
                    has_associations = True

        # Commit associations if any were added
        if has_associations:
            await self._initiative_repository._session.commit()
            await self._initiative_repository._session.refresh(initiative)

        # Return response with actual counts
        response_dict = {
            "id": initiative.id,
            "name": initiative.name,
            "description": initiative.description,
            "status": initiative.status,
            "start_date": initiative.start_date,
            "target_date": initiative.target_date,
            "project_id": initiative.project_id,
            "initiative_key": initiative.initiative_key,
            "initiative_number": initiative.initiative_number,
            "created_at": initiative.created_at,
            "updated_at": initiative.updated_at,
            "issue_count": len(issue_ids) if issue_ids else 0,
            "tag_count": len(tag_ids) if tag_ids else 0,
            "document_count": len(document_ids) if document_ids else 0,
        }
        return InitiativeResponse(**response_dict)

    async def get_initiative_by_id(self, initiative_id: UUID) -> InitiativeResponse:
        """Get initiative by ID."""
        initiative = await self._initiative_repository.get_with_all_relations(initiative_id)
        if not initiative:
            raise InitiativeNotFoundError(initiative_id)
        return self._to_response(initiative)

    async def get_all_initiatives(
        self,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        sort_order: str = "desc",
    ) -> list[InitiativeResponse]:
        """Get all initiatives with optional pagination."""
        initiatives = await self._initiative_repository.get_all_with_relations(
            limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
        )
        return [self._to_response(i) for i in initiatives]

    async def get_initiatives_by_project(
        self,
        project_id: UUID,
        sort_by: str | None = None,
        sort_order: str = "desc",
    ) -> list[InitiativeResponse]:
        """Get all initiatives for a project."""
        # Verify project exists
        project = await self._project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(project_id)

        initiatives = await self._initiative_repository.get_by_project(
            project_id, sort_by=sort_by, sort_order=sort_order
        )
        return [self._to_response(i) for i in initiatives]

    async def update_initiative(
        self, initiative_id: UUID, update_data: InitiativeUpdate
    ) -> InitiativeResponse:
        """Update an initiative."""
        # Strip emojis from text fields
        if update_data.name:
            update_data.name = strip_emojis(update_data.name)
        if update_data.description:
            update_data.description = strip_emojis(update_data.description)

        initiative = await self._initiative_repository.get_by_id(initiative_id)
        if not initiative:
            raise InitiativeNotFoundError(initiative_id)

        # Update basic fields
        initiative = await self._initiative_repository.update(initiative_id, update_data)
        if not initiative:
            raise InitiativeNotFoundError(initiative_id)

        # Handle association updates - refresh relationships before accessing them
        if update_data.issue_ids is not None:
            await self._initiative_repository._session.refresh(initiative, ["issues"])
            initiative.issues.clear()
            for issue_id in update_data.issue_ids:
                issue = await self._issue_repository.get_by_id(issue_id)
                if issue:
                    initiative.issues.append(issue)

        if update_data.tag_ids is not None:
            await self._initiative_repository._session.refresh(initiative, ["tags"])
            initiative.tags.clear()
            for tag_id in update_data.tag_ids:
                tag = await self._tag_repository.get_by_id(tag_id)
                if tag:
                    initiative.tags.append(tag)

        if update_data.document_ids is not None:
            await self._initiative_repository._session.refresh(initiative, ["documents"])
            initiative.documents.clear()
            for document_id in update_data.document_ids:
                document = await self._document_repository.get_by_id(document_id)
                if document:
                    initiative.documents.append(document)

        await self._initiative_repository._session.commit()
        await self._initiative_repository._session.refresh(initiative)

        return self._to_response(initiative)

    async def delete_initiative(self, initiative_id: UUID) -> bool:
        """Delete an initiative."""
        success = await self._initiative_repository.delete(initiative_id)
        if not success:
            raise InitiativeNotFoundError(initiative_id)
        return success

    async def get_initiatives_by_status(
        self, status: str, sort_by: str | None = None, sort_order: str = "desc"
    ) -> list[InitiativeResponse]:
        """Get initiatives by status."""
        initiatives = await self._initiative_repository.get_by_status(
            status, sort_by=sort_by, sort_order=sort_order
        )
        return [self._to_response(i) for i in initiatives]

    async def get_initiatives_by_workspace(
        self,
        workspace: str,
        work_company: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        sort_order: str = "desc",
    ) -> list[InitiativeResponse]:
        """Get initiatives filtered by workspace."""
        initiatives = await self._initiative_repository.get_by_workspace(
            workspace=workspace,
            work_company=work_company,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return [self._to_response(i) for i in initiatives]

    async def get_initiative_issues(self, initiative_id: UUID) -> list[IssueResponse]:
        """Get all issues associated with an initiative."""
        initiative = await self._initiative_repository.get_with_issues(initiative_id)
        if not initiative:
            raise InitiativeNotFoundError(initiative_id)

        # Convert issues to IssueResponse
        return [IssueResponse.model_validate(issue) for issue in initiative.issues]

    def _to_response(self, initiative: Initiative) -> InitiativeResponse:
        """Convert initiative model to response.

        Note: Only use this method when relationships have been eagerly loaded
        (e.g., via get_with_all_relations). For list views, construct the
        response directly without accessing relationships.
        """
        # Check if relationships are loaded using SQLAlchemy inspection
        insp = inspect(initiative)

        # Only access relationships if they're loaded (NOT in unloaded set)
        issue_count = len(initiative.issues) if "issues" not in insp.unloaded else 0
        tag_count = len(initiative.tags) if "tags" not in insp.unloaded else 0
        document_count = len(initiative.documents) if "documents" not in insp.unloaded else 0

        response_dict = {
            "id": initiative.id,
            "name": initiative.name,
            "description": initiative.description,
            "status": initiative.status,
            "start_date": initiative.start_date,
            "target_date": initiative.target_date,
            "project_id": initiative.project_id,
            "initiative_key": initiative.initiative_key,
            "initiative_number": initiative.initiative_number,
            "created_at": initiative.created_at,
            "updated_at": initiative.updated_at,
            "issue_count": issue_count,
            "tag_count": tag_count,
            "document_count": document_count,
        }
        return InitiativeResponse(**response_dict)

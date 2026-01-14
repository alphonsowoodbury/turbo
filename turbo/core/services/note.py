"""Note service for business logic operations."""

import logging
from uuid import UUID

from turbo.core.repositories.note import NoteRepository
from turbo.core.repositories.tag import TagRepository
from turbo.core.schemas.note import (
    NoteCreate,
    NoteResponse,
    NoteUpdate,
)
from turbo.core.schemas.graph import GraphNodeCreate
from turbo.core.services.graph import GraphService
from turbo.utils.config import get_settings
from turbo.utils.exceptions import NoteNotFoundError

logger = logging.getLogger(__name__)


class NoteService:
    """Service for note business logic."""

    def __init__(
        self,
        note_repository: NoteRepository,
        tag_repository: TagRepository,
        webhook_service=None,  # Optional - for event emission
    ) -> None:
        self._note_repository = note_repository
        self._tag_repository = tag_repository
        self._webhook_service = webhook_service
        self._settings = get_settings()

    async def _index_note_in_graph(self, note) -> None:
        """
        Index a note in the knowledge graph for semantic search.

        This is called automatically when notes are created or updated.
        Failures are logged but don't affect the main operation.

        Args:
            note: The note model instance to index
        """
        # Only index if graph is enabled
        if not self._settings.graph.enabled:
            return

        try:
            # Build content string from note data
            content_parts = [
                f"Title: {note.title}",
            ]

            if note.content:
                content_parts.append(f"\nContent:\n{note.content}")

            content_parts.append(f"\nWorkspace: {note.workspace}")

            if note.work_company:
                content_parts.append(f"Company: {note.work_company}")

            content = "\n".join(content_parts)

            # Create node data for graph
            node_data = GraphNodeCreate(
                entity_id=note.id,
                entity_type="note",
                content=content,
                metadata={
                    "title": note.title,
                    "workspace": note.workspace,
                    "work_company": note.work_company,
                    "is_archived": note.is_archived,
                },
            )

            # Index in graph
            graph_service = GraphService()
            try:
                await graph_service.add_episode(node_data)
                logger.debug(f"Indexed note {note.id} in knowledge graph")
            finally:
                await graph_service.close()

        except Exception as e:
            # Log error but don't fail the main operation
            logger.warning(f"Failed to index note {note.id} in knowledge graph: {e}")

    async def create_note(self, note_data: NoteCreate) -> NoteResponse:
        """Create a new note."""
        # Extract tag IDs if provided
        tag_ids = note_data.tag_ids

        # Create note (pass Pydantic model directly)
        note = await self._note_repository.create(note_data)

        # Add tags if provided
        if tag_ids:
            tags = []
            for tag_id in tag_ids:
                tag = await self._tag_repository.get_by_id(tag_id)
                if tag:
                    tags.append(tag)
            note.tags = tags
            await self._note_repository.update(note.id, {})

        # Index in knowledge graph
        await self._index_note_in_graph(note)

        # Emit webhook event
        if self._webhook_service:
            try:
                await self._webhook_service.emit_event(
                    event_type="note.created",
                    data={
                        "note_id": str(note.id),
                        "title": note.title,
                        "workspace": note.workspace,
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to emit webhook event: {e}")

        return NoteResponse.model_validate(note)

    async def get_note(self, note_id: UUID) -> NoteResponse:
        """Get a note by ID."""
        note = await self._note_repository.get_by_id(note_id)
        if not note:
            raise NoteNotFoundError(f"Note with ID {note_id} not found")
        return NoteResponse.model_validate(note)

    async def update_note(self, note_id: UUID, note_data: NoteUpdate) -> NoteResponse:
        """Update a note."""
        note = await self._note_repository.get_by_id(note_id)
        if not note:
            raise NoteNotFoundError(f"Note with ID {note_id} not found")

        # Extract tag IDs if provided
        tag_ids = note_data.tag_ids
        note_update_dict = note_data.model_dump(exclude_unset=True, exclude={"tag_ids"})

        # Update note
        updated_note = await self._note_repository.update(note_id, note_update_dict)

        # Update tags if provided
        if tag_ids is not None:
            tags = []
            for tag_id in tag_ids:
                tag = await self._tag_repository.get_by_id(tag_id)
                if tag:
                    tags.append(tag)
            updated_note.tags = tags
            await self._note_repository.update(note_id, {})

        # Re-index in knowledge graph
        await self._index_note_in_graph(updated_note)

        # Emit webhook event
        if self._webhook_service:
            try:
                await self._webhook_service.emit_event(
                    event_type="note.updated",
                    data={
                        "note_id": str(note_id),
                        "title": updated_note.title,
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to emit webhook event: {e}")

        return NoteResponse.model_validate(updated_note)

    async def delete_note(self, note_id: UUID) -> None:
        """Delete a note."""
        note = await self._note_repository.get_by_id(note_id)
        if not note:
            raise NoteNotFoundError(f"Note with ID {note_id} not found")

        await self._note_repository.delete(note_id)

        # Emit webhook event
        if self._webhook_service:
            try:
                await self._webhook_service.emit_event(
                    event_type="note.deleted",
                    data={
                        "note_id": str(note_id),
                        "title": note.title,
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to emit webhook event: {e}")

    async def list_notes(
        self,
        workspace: str | None = None,
        work_company: str | None = None,
        include_archived: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[NoteResponse]:
        """List notes with optional filtering."""
        if workspace:
            notes = await self._note_repository.get_by_workspace(workspace, include_archived)
        elif work_company:
            notes = await self._note_repository.get_by_work_company(work_company, include_archived)
        else:
            notes = await self._note_repository.get_all()
            if not include_archived:
                notes = [n for n in notes if not n.is_archived]

        # Apply pagination
        notes = notes[offset : offset + limit]

        return [NoteResponse.model_validate(note) for note in notes]

    async def search_notes(
        self,
        query: str,
        workspace: str | None = None,
        include_archived: bool = False,
    ) -> list[NoteResponse]:
        """Search notes by title or content."""
        title_results = await self._note_repository.search_by_title(query, include_archived)
        content_results = await self._note_repository.search_by_content(query, include_archived)

        # Combine and deduplicate results
        note_ids = set()
        notes = []
        for note in title_results + content_results:
            if note.id not in note_ids:
                if workspace is None or note.workspace == workspace:
                    note_ids.add(note.id)
                    notes.append(note)

        return [NoteResponse.model_validate(note) for note in notes]

"""Note repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from turbo.core.models.note import Note
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.note import NoteCreate, NoteUpdate


class NoteRepository(BaseRepository[Note, NoteCreate, NoteUpdate]):
    """Repository for note data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Note)

    async def create(self, obj_in: NoteCreate) -> Note:
        """Create a new note, excluding tag_ids from model creation."""
        obj_data = obj_in.model_dump(exclude_unset=True, exclude={"tag_ids"})
        db_obj = self._model(**obj_data)
        self._session.add(db_obj)
        await self._session.commit()
        await self._session.refresh(db_obj, ["tags"])
        return db_obj

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        sort_by: str | None = None,
        sort_order: str = "desc",
    ) -> list[Note]:
        """Get all notes with tags eagerly loaded."""
        stmt = select(self._model).options(selectinload(self._model.tags))
        stmt = self._apply_sorting(stmt, sort_by, sort_order)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, id: UUID) -> Note | None:
        """Get note by ID with tags eagerly loaded."""
        stmt = select(self._model).options(selectinload(self._model.tags)).where(self._model.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, id: UUID, obj_in: NoteUpdate | dict) -> Note:
        """Update a note, excluding tag_ids from model update."""
        db_obj = await self.get_by_id(id)
        if not db_obj:
            raise ValueError(f"Note with id {id} not found")

        # Handle both Pydantic models and dicts
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True, exclude={"tag_ids"})

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await self._session.commit()
        await self._session.refresh(db_obj, ["tags"])
        return db_obj

    async def get_by_workspace(
        self,
        workspace: str,
        include_archived: bool = False,
        sort_by: str | None = None,
        sort_order: str = "desc",
    ) -> list[Note]:
        """Get notes by workspace."""
        stmt = select(self._model).options(selectinload(self._model.tags)).where(self._model.workspace == workspace)
        if not include_archived:
            stmt = stmt.where(self._model.is_archived == False)
        stmt = self._apply_sorting(stmt, sort_by, sort_order)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_work_company(
        self,
        work_company: str,
        include_archived: bool = False,
        sort_by: str | None = None,
        sort_order: str = "desc",
    ) -> list[Note]:
        """Get notes by work company."""
        stmt = select(self._model).options(selectinload(self._model.tags)).where(self._model.work_company == work_company)
        if not include_archived:
            stmt = stmt.where(self._model.is_archived == False)
        stmt = self._apply_sorting(stmt, sort_by, sort_order)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_title(self, title_pattern: str, include_archived: bool = False) -> list[Note]:
        """Search notes by title pattern."""
        stmt = select(self._model).options(selectinload(self._model.tags)).where(self._model.title.ilike(f"%{title_pattern}%"))
        if not include_archived:
            stmt = stmt.where(self._model.is_archived == False)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_content(self, content_pattern: str, include_archived: bool = False) -> list[Note]:
        """Search notes by content pattern."""
        stmt = select(self._model).options(selectinload(self._model.tags)).where(self._model.content.ilike(f"%{content_pattern}%"))
        if not include_archived:
            stmt = stmt.where(self._model.is_archived == False)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_archived(self, workspace: str | None = None) -> list[Note]:
        """Get archived notes."""
        stmt = select(self._model).options(selectinload(self._model.tags)).where(self._model.is_archived == True)
        if workspace:
            stmt = stmt.where(self._model.workspace == workspace)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

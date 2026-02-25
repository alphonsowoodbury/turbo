"""Document repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from turbo.core.models.document import Document
from turbo.core.models.project import Project
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.document import DocumentCreate, DocumentUpdate


class DocumentRepository(BaseRepository[Document, DocumentCreate, DocumentUpdate]):
    """Repository for document data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Document)

    async def get_by_project(
        self, project_id: UUID, sort_by: str | None = None, sort_order: str = "desc"
    ) -> list[Document]:
        """Get documents by project ID."""
        stmt = select(self._model).where(self._model.project_id == project_id)
        stmt = self._apply_sorting(stmt, sort_by, sort_order)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_type(
        self, document_type: str, sort_by: str | None = None, sort_order: str = "desc"
    ) -> list[Document]:
        """Get documents by type."""
        stmt = select(self._model).where(self._model.type == document_type)
        stmt = self._apply_sorting(stmt, sort_by, sort_order)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_format(
        self, document_format: str, sort_by: str | None = None, sort_order: str = "desc"
    ) -> list[Document]:
        """Get documents by format."""
        stmt = select(self._model).where(self._model.format == document_format)
        stmt = self._apply_sorting(stmt, sort_by, sort_order)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_author(self, author: str) -> list[Document]:
        """Get documents by author."""
        stmt = select(self._model).where(self._model.author == author)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_title(self, title_pattern: str) -> list[Document]:
        """Search documents by title pattern."""
        stmt = select(self._model).where(self._model.title.ilike(f"%{title_pattern}%"))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_content(self, content_pattern: str) -> list[Document]:
        """Search documents by content pattern."""
        stmt = select(self._model).where(
            self._model.content.ilike(f"%{content_pattern}%")
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_project_specifications(self, project_id: UUID) -> list[Document]:
        """Get specification documents for a project."""
        stmt = select(self._model).where(
            (self._model.project_id == project_id)
            & (self._model.type == "specification")
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_project_documentation(self, project_id: UUID) -> list[Document]:
        """Get documentation documents for a project."""
        stmt = select(self._model).where(
            (self._model.project_id == project_id)
            & (self._model.type.in_(["user_guide", "api_doc", "readme"]))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_version(
        self, project_id: UUID, document_type: str
    ) -> Document | None:
        """Get the latest version of a document type for a project."""
        stmt = (
            select(self._model)
            .where(
                (self._model.project_id == project_id)
                & (self._model.type == document_type)
            )
            .order_by(self._model.updated_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_project(self, id: UUID) -> Document | None:
        """Get document with its project loaded."""
        stmt = (
            select(self._model)
            .options(selectinload(self._model.project))
            .where(self._model.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_version(self, version: str) -> list[Document]:
        """Get documents by version."""
        stmt = select(self._model).where(self._model.version == version)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_documents(
        self, limit: int = 10, project_id: UUID | None = None
    ) -> list[Document]:
        """Get recently updated documents."""
        stmt = select(self._model).order_by(self._model.updated_at.desc())

        if project_id:
            stmt = stmt.where(self._model.project_id == project_id)

        stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_workspace(
        self,
        workspace: str,
        work_company: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        sort_order: str = "desc",
    ) -> list[Document]:
        """Get documents by workspace (filtering by project's workspace)."""
        stmt = (
            select(self._model)
            .join(Project, self._model.project_id == Project.id)
            .where(Project.workspace == workspace)
        )

        # For work workspace, optionally filter by company
        if workspace == "work" and work_company:
            stmt = stmt.where(Project.work_company == work_company)

        stmt = self._apply_sorting(stmt, sort_by, sort_order)

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_key(self, document_key: str) -> Document | None:
        """Get document by its human-readable key (e.g., 'CNTXT-D1')."""
        stmt = select(self._model).where(self._model.document_key == document_key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


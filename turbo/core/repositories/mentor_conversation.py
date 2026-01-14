"""MentorConversation repository implementation."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.mentor_conversation import MentorConversation
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.mentor_conversation import (
    MentorConversationCreate,
    MentorConversationUpdate,
)


class MentorConversationRepository(
    BaseRepository[MentorConversation, MentorConversationCreate, MentorConversationUpdate]
):
    """Repository for mentor conversation data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MentorConversation)

    async def get_by_mentor(
        self,
        mentor_id: UUID,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[MentorConversation]:
        """Get conversation messages for a mentor."""
        stmt = (
            select(self._model)
            .where(self._model.mentor_id == mentor_id)
            .order_by(self._model.created_at.asc())
        )

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_messages(
        self,
        mentor_id: UUID,
        limit: int = 20,
    ) -> list[MentorConversation]:
        """Get recent conversation messages for a mentor."""
        stmt = (
            select(self._model)
            .where(self._model.mentor_id == mentor_id)
            .order_by(self._model.created_at.desc())
            .limit(limit)
        )

        result = await self._session.execute(stmt)
        # Reverse to get chronological order (oldest to newest)
        return list(reversed(list(result.scalars().all())))

    async def count_messages(self, mentor_id: UUID) -> int:
        """Count total messages for a mentor."""
        stmt = (
            select(self._model)
            .where(self._model.mentor_id == mentor_id)
        )
        result = await self._session.execute(stmt)
        return len(list(result.scalars().all()))

    async def clear_conversation(self, mentor_id: UUID) -> int:
        """Delete all conversation messages for a mentor. Returns count of deleted messages."""
        stmt = delete(self._model).where(self._model.mentor_id == mentor_id)
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount  # type: ignore

    async def delete_message(self, mentor_id: UUID, message_id: UUID) -> bool:
        """Delete a specific message from mentor conversation. Returns True if deleted."""
        stmt = delete(self._model).where(
            self._model.mentor_id == mentor_id,
            self._model.id == message_id
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount > 0  # type: ignore

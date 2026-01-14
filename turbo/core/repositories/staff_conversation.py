"""StaffConversation repository for data access operations."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.staff_conversation import StaffConversation
from turbo.core.repositories.base import BaseRepository


class StaffConversationRepository(
    BaseRepository[StaffConversation, dict, dict]
):
    """Repository for staff conversation data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, StaffConversation)

    async def get_by_staff(
        self,
        staff_id: UUID,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[StaffConversation]:
        """
        Get conversation messages for a staff member.

        Args:
            staff_id: UUID of the staff member
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of conversation messages ordered chronologically
        """
        stmt = (
            select(self._model)
            .where(self._model.staff_id == staff_id)
            .order_by(self._model.created_at.asc())
        )

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_group_discussion(
        self,
        group_discussion_id: UUID,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[StaffConversation]:
        """
        Get all messages for a group discussion.

        Args:
            group_discussion_id: UUID of the group discussion
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of messages from all staff in this discussion, ordered chronologically
        """
        stmt = (
            select(self._model)
            .where(self._model.group_discussion_id == group_discussion_id)
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
        staff_id: UUID,
        limit: int = 20,
    ) -> list[StaffConversation]:
        """
        Get recent conversation messages for a staff member.

        Used for building context when generating AI responses.

        Args:
            staff_id: UUID of the staff member
            limit: Maximum number of messages to return (default: 20)

        Returns:
            List of recent messages in chronological order (oldest to newest)
        """
        stmt = (
            select(self._model)
            .where(self._model.staff_id == staff_id)
            .order_by(self._model.created_at.desc())
            .limit(limit)
        )

        result = await self._session.execute(stmt)
        # Reverse to get chronological order (oldest to newest)
        return list(reversed(list(result.scalars().all())))

    async def count_messages(self, staff_id: UUID) -> int:
        """
        Count total messages for a staff member.

        Args:
            staff_id: UUID of the staff member

        Returns:
            Number of messages
        """
        stmt = select(self._model).where(self._model.staff_id == staff_id)
        result = await self._session.execute(stmt)
        return len(list(result.scalars().all()))

    async def clear_conversation(self, staff_id: UUID) -> int:
        """
        Delete all conversation messages for a staff member.

        Args:
            staff_id: UUID of the staff member

        Returns:
            Count of deleted messages
        """
        stmt = delete(self._model).where(self._model.staff_id == staff_id)
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount  # type: ignore

    async def delete_message(self, staff_id: UUID, message_id: UUID) -> bool:
        """
        Delete a specific message from staff conversation.

        Args:
            staff_id: UUID of the staff member
            message_id: UUID of the message to delete

        Returns:
            True if deleted, False if not found
        """
        stmt = delete(self._model).where(
            self._model.staff_id == staff_id,
            self._model.id == message_id
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount > 0  # type: ignore

    async def get_user_messages(
        self, staff_id: UUID, limit: int | None = None
    ) -> list[StaffConversation]:
        """
        Get only user messages for a staff member.

        Args:
            staff_id: UUID of the staff member
            limit: Maximum number of messages to return

        Returns:
            List of user messages ordered chronologically
        """
        stmt = (
            select(self._model)
            .where(
                self._model.staff_id == staff_id,
                self._model.message_type == "user",
            )
            .order_by(self._model.created_at.asc())
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_assistant_messages(
        self, staff_id: UUID, limit: int | None = None
    ) -> list[StaffConversation]:
        """
        Get only assistant messages for a staff member.

        Args:
            staff_id: UUID of the staff member
            limit: Maximum number of messages to return

        Returns:
            List of assistant messages ordered chronologically
        """
        stmt = (
            select(self._model)
            .where(
                self._model.staff_id == staff_id,
                self._model.message_type == "assistant",
            )
            .order_by(self._model.created_at.asc())
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_from_dict(self, message_data: dict) -> StaffConversation:
        """
        Create a new message from a dictionary.

        Args:
            message_data: Dictionary with message data

        Returns:
            Created StaffConversation instance
        """
        db_obj = StaffConversation(**message_data)
        self._session.add(db_obj)
        await self._session.commit()
        await self._session.refresh(db_obj)
        return db_obj

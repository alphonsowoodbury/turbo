"""Repository for GroupDiscussion model."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.group_discussion import GroupDiscussion
from turbo.core.models.staff_conversation import StaffConversation
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.group_discussion import (
    GroupDiscussionCreate,
    GroupDiscussionUpdate,
)


class GroupDiscussionRepository(
    BaseRepository[GroupDiscussion, GroupDiscussionCreate, GroupDiscussionUpdate]
):
    """Repository for group discussion operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, GroupDiscussion)

    async def get_by_type(
        self,
        discussion_type: str,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[GroupDiscussion]:
        """Get discussions by type with optional status filter."""
        stmt = select(GroupDiscussion).where(
            GroupDiscussion.discussion_type == discussion_type
        )

        if status:
            stmt = stmt.where(GroupDiscussion.status == status)

        stmt = stmt.order_by(GroupDiscussion.last_activity_at.desc().nulls_last())

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_discussions(
        self, limit: int | None = None, offset: int | None = None
    ) -> list[GroupDiscussion]:
        """Get all active discussions ordered by last activity."""
        stmt = (
            select(GroupDiscussion)
            .where(GroupDiscussion.status == "active")
            .order_by(GroupDiscussion.last_activity_at.desc().nulls_last())
        )

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_hands(self) -> GroupDiscussion | None:
        """Get the All Hands discussion room."""
        stmt = select(GroupDiscussion).where(
            GroupDiscussion.name == "All Hands",
            GroupDiscussion.discussion_type == "all_hands",
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_messages(
        self,
        discussion_id: UUID,
        limit: int | None = 50,
        offset: int | None = None,
    ) -> list[StaffConversation]:
        """Get messages for a group discussion."""
        stmt = (
            select(StaffConversation)
            .where(
                StaffConversation.group_discussion_id == discussion_id,
                StaffConversation.is_group_discussion == True,
            )
            .order_by(StaffConversation.created_at.asc())
        )

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_messages(self, discussion_id: UUID) -> int:
        """Count total messages in a discussion."""
        stmt = select(func.count(StaffConversation.id)).where(
            StaffConversation.group_discussion_id == discussion_id,
            StaffConversation.is_group_discussion == True,
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def update_activity(
        self, discussion_id: UUID, timestamp: datetime
    ) -> GroupDiscussion | None:
        """Update last activity timestamp for a discussion."""
        discussion = await self.get_by_id(discussion_id)
        if not discussion:
            return None

        discussion.last_activity_at = timestamp
        discussion.message_count = await self.count_messages(discussion_id)

        await self._session.commit()
        await self._session.refresh(discussion)
        return discussion

    async def add_participant(
        self, discussion_id: UUID, staff_id: UUID
    ) -> GroupDiscussion | None:
        """Add a participant to the discussion."""
        discussion = await self.get_by_id(discussion_id)
        if not discussion:
            return None

        if staff_id not in discussion.participant_ids:
            discussion.participant_ids.append(staff_id)
            # Mark the column as modified since SQLAlchemy doesn't track JSONB changes
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(discussion, "participant_ids")

            await self._session.commit()
            await self._session.refresh(discussion)

        return discussion

    async def remove_participant(
        self, discussion_id: UUID, staff_id: UUID
    ) -> GroupDiscussion | None:
        """Remove a participant from the discussion."""
        discussion = await self.get_by_id(discussion_id)
        if not discussion:
            return None

        if staff_id in discussion.participant_ids:
            discussion.participant_ids.remove(staff_id)
            # Mark the column as modified
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(discussion, "participant_ids")

            await self._session.commit()
            await self._session.refresh(discussion)

        return discussion

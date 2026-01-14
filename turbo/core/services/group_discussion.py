"""Service layer for group discussions."""

from datetime import datetime
from uuid import UUID

from turbo.core.models.staff_conversation import StaffConversation
from turbo.core.repositories.group_discussion import GroupDiscussionRepository
from turbo.core.repositories.staff_conversation import StaffConversationRepository
from turbo.core.schemas.group_discussion import (
    GroupDiscussionCreate,
    GroupDiscussionResponse,
    GroupDiscussionUpdate,
)
from turbo.core.schemas.staff import StaffConversationResponse
from turbo.utils.exceptions import GroupDiscussionNotFoundError


class GroupDiscussionService:
    """Service for group discussion business logic."""

    def __init__(
        self,
        discussion_repo: GroupDiscussionRepository,
        conversation_repo: StaffConversationRepository,
    ) -> None:
        self.discussion_repo = discussion_repo
        self.conversation_repo = conversation_repo

    async def create_discussion(
        self, discussion_data: GroupDiscussionCreate
    ) -> GroupDiscussionResponse:
        """Create a new group discussion."""
        discussion = await self.discussion_repo.create(discussion_data)
        return GroupDiscussionResponse.model_validate(discussion)

    async def get_discussion(self, discussion_id: UUID) -> GroupDiscussionResponse:
        """Get a discussion by ID."""
        discussion = await self.discussion_repo.get_by_id(discussion_id)
        if not discussion:
            raise GroupDiscussionNotFoundError(
                f"Group discussion with id {discussion_id} not found"
            )
        return GroupDiscussionResponse.model_validate(discussion)

    async def get_all_hands(self) -> GroupDiscussionResponse:
        """Get the All Hands discussion room."""
        discussion = await self.discussion_repo.get_all_hands()
        if not discussion:
            raise GroupDiscussionNotFoundError("All Hands discussion room not found")
        return GroupDiscussionResponse.model_validate(discussion)

    async def list_discussions(
        self,
        discussion_type: str | None = None,
        status: str | None = "active",
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[GroupDiscussionResponse]:
        """List all discussions with optional filters."""
        if discussion_type:
            discussions = await self.discussion_repo.get_by_type(
                discussion_type=discussion_type,
                status=status,
                limit=limit,
                offset=offset,
            )
        else:
            if status == "active":
                discussions = await self.discussion_repo.get_active_discussions(
                    limit=limit, offset=offset
                )
            else:
                discussions = await self.discussion_repo.get_all(
                    limit=limit, offset=offset
                )

        return [
            GroupDiscussionResponse.model_validate(d) for d in discussions
        ]

    async def update_discussion(
        self, discussion_id: UUID, discussion_data: GroupDiscussionUpdate
    ) -> GroupDiscussionResponse:
        """Update a discussion."""
        discussion = await self.discussion_repo.update(discussion_id, discussion_data)
        if not discussion:
            raise GroupDiscussionNotFoundError(
                f"Group discussion with id {discussion_id} not found"
            )
        return GroupDiscussionResponse.model_validate(discussion)

    async def delete_discussion(self, discussion_id: UUID) -> bool:
        """Delete a discussion."""
        success = await self.discussion_repo.delete(discussion_id)
        if not success:
            raise GroupDiscussionNotFoundError(
                f"Group discussion with id {discussion_id} not found"
            )
        return success

    async def get_messages(
        self,
        discussion_id: UUID,
        limit: int | None = 50,
        offset: int | None = None,
    ) -> list[StaffConversationResponse]:
        """Get messages for a discussion."""
        # Verify discussion exists
        discussion = await self.discussion_repo.get_by_id(discussion_id)
        if not discussion:
            raise GroupDiscussionNotFoundError(
                f"Group discussion with id {discussion_id} not found"
            )

        messages = await self.discussion_repo.get_messages(
            discussion_id=discussion_id,
            limit=limit,
            offset=offset,
        )

        return [StaffConversationResponse.model_validate(m) for m in messages]

    async def add_message(
        self,
        discussion_id: UUID,
        staff_id: UUID | None,
        content: str,
        message_type: str = "assistant",
    ) -> StaffConversationResponse:
        """Add a message to a group discussion.

        Args:
            discussion_id: ID of the group discussion
            staff_id: ID of the staff member (None for user messages)
            content: Message content
            message_type: "user" for user messages, "assistant" for staff responses
        """
        # Verify discussion exists
        discussion = await self.discussion_repo.get_by_id(discussion_id)
        if not discussion:
            raise GroupDiscussionNotFoundError(
                f"Group discussion with id {discussion_id} not found"
            )

        # Create message
        message_data = {
            "staff_id": staff_id,
            "message_type": message_type,
            "content": content,
            "is_group_discussion": True,
            "group_discussion_id": discussion_id,
        }

        message = await self.conversation_repo.create_from_dict(message_data)

        # Update discussion activity
        await self.discussion_repo.update_activity(
            discussion_id=discussion_id,
            timestamp=message.created_at,
        )

        return StaffConversationResponse.model_validate(message)

    async def add_participant(
        self, discussion_id: UUID, staff_id: UUID
    ) -> GroupDiscussionResponse:
        """Add a participant to a discussion."""
        discussion = await self.discussion_repo.add_participant(
            discussion_id=discussion_id,
            staff_id=staff_id,
        )
        if not discussion:
            raise GroupDiscussionNotFoundError(
                f"Group discussion with id {discussion_id} not found"
            )
        return GroupDiscussionResponse.model_validate(discussion)

    async def remove_participant(
        self, discussion_id: UUID, staff_id: UUID
    ) -> GroupDiscussionResponse:
        """Remove a participant from a discussion."""
        discussion = await self.discussion_repo.remove_participant(
            discussion_id=discussion_id,
            staff_id=staff_id,
        )
        if not discussion:
            raise GroupDiscussionNotFoundError(
                f"Group discussion with id {discussion_id} not found"
            )
        return GroupDiscussionResponse.model_validate(discussion)

"""Service for staff business logic operations."""

import logging
from uuid import UUID

from turbo.core.repositories.staff import StaffRepository
from turbo.core.repositories.staff_conversation import StaffConversationRepository
from turbo.core.schemas.staff import (
    StaffCreate,
    StaffResponse,
    StaffSummary,
    StaffUpdate,
    StaffConversationMessage,
    StaffConversationResponse,
    StaffProfileResponse,
    StaffActivityItem,
)
from turbo.core.utils import strip_emojis
from turbo.utils.exceptions import StaffNotFoundError

logger = logging.getLogger(__name__)


class StaffService:
    """Service for staff operations including @ mention and assignment logic."""

    def __init__(
        self,
        staff_repository: StaffRepository,
        conversation_repository: StaffConversationRepository,
    ) -> None:
        self._staff_repository = staff_repository
        self._conversation_repository = conversation_repository

    async def create_staff(self, staff_data: StaffCreate) -> StaffResponse:
        """Create a new staff member."""
        # Strip emojis from text fields
        if staff_data.name:
            staff_data.name = strip_emojis(staff_data.name)
        if staff_data.description:
            staff_data.description = strip_emojis(staff_data.description)
        if staff_data.persona:
            staff_data.persona = strip_emojis(staff_data.persona)

        # Validate handle doesn't start with @
        if staff_data.handle.startswith("@"):
            raise ValueError("Handle should not start with @ symbol")

        staff = await self._staff_repository.create(staff_data)
        return StaffResponse.model_validate(staff)

    async def get_staff(self, staff_id: UUID) -> StaffResponse:
        """Get staff by ID."""
        staff = await self._staff_repository.get_by_id(staff_id)
        if not staff:
            raise StaffNotFoundError(staff_id)
        return StaffResponse.model_validate(staff)

    async def get_staff_profile(self, staff_id: UUID) -> StaffProfileResponse:
        """
        Get comprehensive staff profile with analytics and activity.

        Args:
            staff_id: Staff UUID

        Returns:
            Complete profile with performance metrics, assignments, and activity
        """
        # Get basic staff info with relationships eagerly loaded
        staff = await self._staff_repository.get_by_id_with_relationships(staff_id)
        if not staff:
            raise StaffNotFoundError(staff_id)

        staff_response = StaffResponse.model_validate(staff)

        # Get review requests (from relationship)
        review_requests = []
        for req in staff.review_requests:
            review_requests.append({
                "id": str(req.id),
                "title": req.title,
                "status": req.status,
                "priority": req.priority,
                "created_at": req.created_at.isoformat(),
            })

        # Calculate conversation metrics
        total_messages = await self._conversation_repository.count_messages(staff_id)
        active_conversations_count = 1 if total_messages > 0 else 0

        # Build computed metrics
        computed_metrics = {
            "response_rate": 0.0,  # TODO: Calculate based on review requests
            "avg_completion_time_hours": staff.performance_metrics.get("avg_response_time_hours", 0.0),
            "active_conversations": active_conversations_count,
            "total_messages": total_messages,
        }

        # Build activity feed from conversations and review requests
        recent_activity = []

        # Add recent conversations to activity
        recent_messages = await self._conversation_repository.get_by_staff(
            staff_id=staff_id, limit=10
        )
        for msg in recent_messages:
            activity_type = "message_sent" if msg.message_type == "assistant" else "message_received"
            recent_activity.append(StaffActivityItem(
                id=msg.id,
                activity_type=activity_type,
                title=f"{'Sent' if msg.message_type == 'assistant' else 'Received'} message",
                description=msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
                entity_type="conversation",
                entity_id=staff_id,
                created_at=msg.created_at,
            ))

        # Add review requests to activity
        for req in staff.review_requests[:10]:  # Limit to 10 most recent
            recent_activity.append(StaffActivityItem(
                id=req.id,
                activity_type="review_request",
                title=req.title,
                description=req.description[:100] + "..." if req.description and len(req.description) > 100 else req.description,
                entity_type="review_request",
                entity_id=req.id,
                created_at=req.created_at,
            ))

        # Sort activity by created_at descending
        recent_activity.sort(key=lambda x: x.created_at, reverse=True)

        return StaffProfileResponse(
            staff=staff_response,
            assigned_review_requests=review_requests,
            assigned_issues_count=0,  # TODO: Query issues assigned to this staff
            pending_approvals_count=0,  # TODO: Query pending action approvals
            computed_metrics=computed_metrics,
            recent_activity=recent_activity[:20],  # Limit to 20 most recent
        )

    async def get_staff_by_handle(self, handle: str) -> StaffResponse:
        """
        Get staff by handle (for @ mention resolution).

        Args:
            handle: Staff handle without @ prefix (e.g., "ChiefOfStaff")

        Returns:
            Staff response

        Raises:
            StaffNotFoundError: If no staff found with this handle
        """
        # Remove @ prefix if present
        if handle.startswith("@"):
            handle = handle[1:]

        staff = await self._staff_repository.get_by_handle(handle)
        if not staff:
            raise ValueError(f"No staff found with handle: @{handle}")
        return StaffResponse.model_validate(staff)

    async def get_all_staff(
        self,
        role_type: str | None = None,
        is_active: bool | None = True,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[StaffResponse]:
        """Get all staff with optional filters."""
        if is_active is not None:
            staff_list = await self._staff_repository.get_active_staff(
                role_type=role_type
            )
        else:
            staff_list = await self._staff_repository.get_all(
                limit=limit, offset=offset
            )

        return [StaffResponse.model_validate(s) for s in staff_list]

    async def get_leadership_staff(self) -> list[StaffSummary]:
        """
        Get all active leadership staff (have universal edit permissions).

        Returns:
            List of leadership staff summaries
        """
        staff_list = await self._staff_repository.get_leadership_staff()
        return [StaffSummary.model_validate(s) for s in staff_list]

    async def get_domain_staff(self) -> list[StaffSummary]:
        """
        Get all active domain expert staff (can only edit assigned entities).

        Returns:
            List of domain expert staff summaries
        """
        staff_list = await self._staff_repository.get_domain_staff()
        return [StaffSummary.model_validate(s) for s in staff_list]

    async def get_staff_for_entity(
        self, entity_type: str, tags: list[str] | None = None
    ) -> list[StaffResponse]:
        """
        Get staff that monitor a specific entity type or tags.

        Useful for automatic notification/assignment when entities are created.

        Args:
            entity_type: Entity type (issue, initiative, milestone, project)
            tags: Optional list of tags to match

        Returns:
            List of staff monitoring this scope
        """
        staff_list = await self._staff_repository.get_by_monitoring_scope(
            entity_type=entity_type, tags=tags
        )
        return [StaffResponse.model_validate(s) for s in staff_list]

    async def update_staff(
        self, staff_id: UUID, update_data: StaffUpdate
    ) -> StaffResponse:
        """Update a staff member."""
        # Strip emojis from text fields
        if update_data.name:
            update_data.name = strip_emojis(update_data.name)
        if update_data.description:
            update_data.description = strip_emojis(update_data.description)
        if update_data.persona:
            update_data.persona = strip_emojis(update_data.persona)

        # Validate handle doesn't start with @ if provided
        if update_data.handle and update_data.handle.startswith("@"):
            raise ValueError("Handle should not start with @ symbol")

        staff = await self._staff_repository.update(staff_id, update_data)
        if not staff:
            raise StaffNotFoundError(staff_id)

        return StaffResponse.model_validate(staff)

    async def delete_staff(self, staff_id: UUID) -> bool:
        """Delete a staff member (cascade deletes conversations and review requests)."""
        success = await self._staff_repository.delete(staff_id)
        if not success:
            raise StaffNotFoundError(staff_id)
        return success

    async def deactivate_staff(self, staff_id: UUID) -> StaffResponse:
        """Deactivate a staff member (soft delete)."""
        update_data = StaffUpdate(is_active=False)
        return await self.update_staff(staff_id, update_data)

    async def activate_staff(self, staff_id: UUID) -> StaffResponse:
        """Activate a staff member."""
        update_data = StaffUpdate(is_active=True)
        return await self.update_staff(staff_id, update_data)

    async def search_staff(self, query: str) -> list[StaffSummary]:
        """
        Search staff by name or handle.

        Args:
            query: Search query string

        Returns:
            List of matching staff
        """
        staff_list = await self._staff_repository.search_by_name_or_handle(query)
        return [StaffSummary.model_validate(s) for s in staff_list]

    # Conversation methods

    async def add_user_message(
        self,
        staff_id: UUID,
        content: str,
        is_group_discussion: bool = False,
        group_discussion_id: UUID | None = None,
    ) -> StaffConversationResponse:
        """
        Add a user message to staff conversation.

        Called when user sends a message to staff (via @ mention or direct chat).

        Args:
            staff_id: Staff UUID
            content: Message content
            is_group_discussion: Whether this is part of a group discussion
            group_discussion_id: Optional group discussion ID

        Returns:
            Created conversation message
        """
        # Verify staff exists
        staff = await self._staff_repository.get_by_id(staff_id)
        if not staff:
            raise StaffNotFoundError(staff_id)

        # Create conversation message
        message_data = StaffConversationMessage(
            staff_id=staff_id,
            message_type="user",
            content=strip_emojis(content),
            is_group_discussion=is_group_discussion,
            group_discussion_id=group_discussion_id,
        )

        message = await self._conversation_repository.create(message_data)
        return StaffConversationResponse.model_validate(message)

    async def add_assistant_message(
        self,
        staff_id: UUID,
        content: str,
        is_group_discussion: bool = False,
        group_discussion_id: UUID | None = None,
    ) -> StaffConversationResponse:
        """
        Add an assistant message (staff response).

        Called by webhook server after generating AI response.

        Args:
            staff_id: Staff UUID
            content: AI-generated response content
            is_group_discussion: Whether this is part of a group discussion
            group_discussion_id: Optional group discussion ID

        Returns:
            Created conversation message
        """
        # Verify staff exists
        staff = await self._staff_repository.get_by_id(staff_id)
        if not staff:
            raise StaffNotFoundError(staff_id)

        # Create conversation message
        message_data = StaffConversationMessage(
            staff_id=staff_id,
            message_type="assistant",
            content=strip_emojis(content),
            is_group_discussion=is_group_discussion,
            group_discussion_id=group_discussion_id,
        )

        message = await self._conversation_repository.create(message_data)
        return StaffConversationResponse.model_validate(message)

    async def get_conversation(
        self,
        staff_id: UUID,
        limit: int | None = 50,
        offset: int | None = None,
    ) -> list[StaffConversationResponse]:
        """
        Get conversation history with a staff member.

        Args:
            staff_id: Staff UUID
            limit: Maximum messages to return (default: 50)
            offset: Offset for pagination

        Returns:
            List of conversation messages ordered by created_at
        """
        # Verify staff exists
        staff = await self._staff_repository.get_by_id(staff_id)
        if not staff:
            raise StaffNotFoundError(staff_id)

        messages = await self._conversation_repository.get_by_staff(
            staff_id=staff_id, limit=limit, offset=offset
        )
        return [StaffConversationResponse.model_validate(m) for m in messages]

    async def get_group_discussion(
        self, group_discussion_id: UUID
    ) -> list[StaffConversationResponse]:
        """
        Get all messages for a group discussion.

        Args:
            group_discussion_id: UUID of the group discussion

        Returns:
            List of messages across all staff in this discussion
        """
        messages = await self._conversation_repository.get_by_group_discussion(
            group_discussion_id=group_discussion_id
        )
        return [StaffConversationResponse.model_validate(m) for m in messages]

    async def clear_conversation(self, staff_id: UUID) -> int:
        """
        Clear all conversation messages for a staff member.

        Args:
            staff_id: Staff UUID

        Returns:
            Number of messages deleted
        """
        # Verify staff exists
        staff = await self._staff_repository.get_by_id(staff_id)
        if not staff:
            raise StaffNotFoundError(staff_id)

        deleted_count = await self._conversation_repository.clear_conversation(
            staff_id=staff_id
        )
        return deleted_count

    async def delete_message(self, staff_id: UUID, message_id: UUID) -> bool:
        """
        Delete a specific message from the conversation.

        Args:
            staff_id: Staff UUID
            message_id: Message UUID to delete

        Returns:
            True if deleted successfully

        Raises:
            StaffNotFoundError: If staff doesn't exist
            ValueError: If message not found or doesn't belong to staff
        """
        # Verify staff exists
        staff = await self._staff_repository.get_by_id(staff_id)
        if not staff:
            raise StaffNotFoundError(staff_id)

        success = await self._conversation_repository.delete_message(staff_id, message_id)
        if not success:
            raise ValueError(f"Message {message_id} not found or does not belong to staff {staff_id}")

        return success

    # Permission checking

    async def can_edit_entity(
        self, staff_id: UUID, entity_type: str, entity_id: UUID
    ) -> bool:
        """
        Check if a staff member can edit a specific entity.

        Leadership staff can edit anything.
        Domain staff can only edit entities assigned to them.

        Args:
            staff_id: Staff UUID
            entity_type: Entity type (issue, initiative, milestone, project)
            entity_id: Entity UUID

        Returns:
            True if staff can edit, False otherwise
        """
        staff = await self._staff_repository.get_by_id(staff_id)
        if not staff:
            return False

        # Leadership can edit anything
        if staff.is_leadership_role:
            return True

        # Domain staff can only edit assigned entities
        # TODO: Check if entity is assigned to this staff
        # This requires checking the assigned_to_type/assigned_to_id fields
        # on the entity. Will implement when adding assignment service.
        return False

    async def has_capability(self, staff_id: UUID, capability: str) -> bool:
        """
        Check if a staff member has a specific capability.

        Args:
            staff_id: Staff UUID
            capability: Capability to check

        Returns:
            True if staff has capability, False otherwise
        """
        staff = await self._staff_repository.get_by_id(staff_id)
        if not staff:
            return False

        return capability in staff.capabilities

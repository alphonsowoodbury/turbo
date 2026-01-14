"""Service for detecting and handling @ mentions of Staff in comments."""

import logging
import re
from uuid import UUID, uuid4

from turbo.core.repositories.staff import StaffRepository
from turbo.core.schemas.staff import StaffResponse
from turbo.core.services.staff import StaffService

logger = logging.getLogger(__name__)


class MentionDetectorService:
    """Service for detecting @ mentions and triggering staff responses."""

    # Regex pattern for @ mentions
    # Matches @handle where handle is alphanumeric + underscores
    MENTION_PATTERN = re.compile(r"@([a-zA-Z0-9_]+)")

    def __init__(
        self,
        staff_repository: StaffRepository,
        staff_service: StaffService,
    ) -> None:
        self._staff_repository = staff_repository
        self._staff_service = staff_service

    def extract_mentions(self, text: str) -> list[str]:
        """
        Extract @ mention handles from text.

        Args:
            text: Text to search for mentions

        Returns:
            List of mentioned handles (without @ prefix)
        """
        matches = self.MENTION_PATTERN.findall(text)
        # Remove duplicates while preserving order
        seen = set()
        unique_mentions = []
        for handle in matches:
            if handle not in seen:
                seen.add(handle)
                unique_mentions.append(handle)
        return unique_mentions

    async def detect_and_resolve_mentions(
        self, text: str
    ) -> dict[str, StaffResponse]:
        """
        Detect @ mentions in text and resolve them to Staff members.

        Args:
            text: Text to search for mentions

        Returns:
            Dictionary mapping handle to StaffResponse for valid mentions only
        """
        mentions = self.extract_mentions(text)
        resolved = {}

        for handle in mentions:
            try:
                staff = await self._staff_repository.get_by_handle(handle)
                if staff and staff.is_active:
                    resolved[handle] = StaffResponse.model_validate(staff)
                else:
                    logger.debug(
                        f"@ mention '{handle}' not found or inactive, skipping"
                    )
            except Exception as e:
                logger.warning(f"Error resolving @ mention '{handle}': {e}")

        return resolved

    async def process_comment_mentions(
        self,
        comment_content: str,
        entity_type: str,
        entity_id: UUID,
        comment_id: UUID,
    ) -> dict:
        """
        Process @ mentions in a comment and trigger appropriate actions.

        This is the main entry point called when a comment is created or updated.

        Args:
            comment_content: The comment text
            entity_type: Type of entity (issue, initiative, milestone, project, document)
            entity_id: UUID of the entity
            comment_id: UUID of the comment

        Returns:
            Dictionary with mention processing results:
            {
                "mentions_found": ["ChiefOfStaff", "AgilityLead"],
                "mentions_resolved": {"ChiefOfStaff": StaffResponse, ...},
                "is_group_discussion": True/False,
                "group_discussion_id": UUID or None,
                "webhooks_triggered": ["ChiefOfStaff", "AgilityLead"]
            }
        """
        # Detect and resolve mentions
        resolved_mentions = await self.detect_and_resolve_mentions(comment_content)

        if not resolved_mentions:
            logger.debug(f"No valid staff mentions found in comment {comment_id}")
            return {
                "mentions_found": [],
                "mentions_resolved": {},
                "is_group_discussion": False,
                "group_discussion_id": None,
                "webhooks_triggered": [],
            }

        # Determine if this is a group discussion (2+ staff mentioned)
        is_group_discussion = len(resolved_mentions) > 1
        group_discussion_id = uuid4() if is_group_discussion else None

        logger.info(
            f"Found {len(resolved_mentions)} staff mention(s) in {entity_type} "
            f"{entity_id}: {list(resolved_mentions.keys())}"
        )

        # Create user messages in staff conversations
        webhooks_triggered = []
        for handle, staff_response in resolved_mentions.items():
            try:
                # Create user message in staff conversation
                await self._staff_service.add_user_message(
                    staff_id=staff_response.id,
                    content=comment_content,
                    is_group_discussion=is_group_discussion,
                    group_discussion_id=group_discussion_id,
                )

                # TODO: Trigger webhook to generate staff response
                # This will be implemented when webhook server is updated
                # await self._trigger_staff_webhook(
                #     staff_id=staff_response.id,
                #     entity_type=entity_type,
                #     entity_id=entity_id,
                #     comment_id=comment_id,
                #     is_group_discussion=is_group_discussion,
                #     group_discussion_id=group_discussion_id,
                # )

                webhooks_triggered.append(handle)
                logger.info(
                    f"Triggered webhook for @{handle} on {entity_type} {entity_id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to process mention for @{handle}: {e}", exc_info=True
                )

        return {
            "mentions_found": list(resolved_mentions.keys()),
            "mentions_resolved": resolved_mentions,
            "is_group_discussion": is_group_discussion,
            "group_discussion_id": str(group_discussion_id)
            if group_discussion_id
            else None,
            "webhooks_triggered": webhooks_triggered,
        }

    async def should_trigger_scope_validation(
        self, entity_type: str, mentions: dict[str, StaffResponse]
    ) -> bool:
        """
        Determine if scope validation should be triggered automatically.

        Scope validation is triggered when:
        - Agility Lead is mentioned in an issue/initiative/milestone
        - OR when creating a new issue/initiative/milestone

        Args:
            entity_type: Type of entity
            mentions: Resolved staff mentions

        Returns:
            True if scope validation should run
        """
        if entity_type not in ["issue", "initiative", "milestone"]:
            return False

        # Check if Agility Lead is mentioned
        for handle, staff in mentions.items():
            if handle == "AgilityLead":
                return True

        return False

    async def get_staff_by_monitoring_scope(
        self, entity_type: str, tags: list[str] | None = None
    ) -> list[StaffResponse]:
        """
        Get staff that should be automatically notified about an entity.

        Uses the monitoring_scope JSONB field to match staff interests.

        Args:
            entity_type: Type of entity
            tags: Optional entity tags to match

        Returns:
            List of staff that monitor this scope
        """
        staff_list = await self._staff_repository.get_by_monitoring_scope(
            entity_type=entity_type, tags=tags
        )
        return [StaffResponse.model_validate(s) for s in staff_list]

    async def auto_mention_staff_for_entity(
        self,
        entity_type: str,
        entity_id: UUID,
        tags: list[str] | None = None,
    ) -> list[str]:
        """
        Automatically mention staff based on monitoring scope.

        Called when creating new entities to notify interested staff.

        Args:
            entity_type: Type of entity
            entity_id: UUID of the entity
            tags: Optional entity tags

        Returns:
            List of staff handles that were auto-mentioned
        """
        staff_list = await self.get_staff_by_monitoring_scope(
            entity_type=entity_type, tags=tags
        )

        auto_mentioned = []
        for staff in staff_list:
            try:
                # Create notification message
                message = (
                    f"New {entity_type} created matching your monitoring scope. "
                    f"Entity ID: {entity_id}"
                )

                await self._staff_service.add_user_message(
                    staff_id=staff.id,
                    content=message,
                    is_group_discussion=False,
                    group_discussion_id=None,
                )

                auto_mentioned.append(staff.handle)
                logger.info(
                    f"Auto-mentioned @{staff.handle} for new {entity_type} {entity_id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to auto-mention @{staff.handle}: {e}", exc_info=True
                )

        return auto_mentioned

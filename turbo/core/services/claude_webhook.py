"""Claude webhook service for automatic AI responses to comments."""

import logging
import os
from uuid import UUID

import httpx
from turbo.core.services.websocket_manager import manager
from turbo.core.services.agent_activity import tracker, AgentStatus
from turbo.core.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class ClaudeWebhookService:
    """Service for triggering Claude Code responses to user comments.

    This service makes HTTP requests to a webhook server running on the host machine,
    which then calls Claude Code CLI in headless mode to generate responses.
    """

    def __init__(
        self, api_url: str | None = None, webhook_url: str | None = None
    ):
        """Initialize the webhook service.

        Args:
            api_url: Base URL for the Turbo API (defaults to localhost:8001)
            webhook_url: URL of the Claude webhook server on host machine
        """
        self.api_url = api_url or os.getenv(
            "TURBO_API_URL", "http://localhost:8001/api/v1"
        )
        self.webhook_url = webhook_url or os.getenv(
            "CLAUDE_WEBHOOK_URL", "http://host.docker.internal:9002/webhook/comment"
        )
        self.claude_enabled = os.getenv("CLAUDE_AUTO_RESPOND", "true").lower() == "true"

    async def trigger_entity_response(
        self, entity_type: str, entity_id: UUID, staff_id: UUID | None = None
    ) -> None:
        """Trigger Claude to analyze an entity and respond with a comment.

        This is called as a background task when a user @mentions AI or staff in a comment.
        Makes an HTTP request to the webhook server running on the host machine.

        Args:
            entity_type: Type of entity (issue, project, milestone, etc.)
            entity_id: UUID of the entity to respond to
            staff_id: Optional staff member ID if a specific staff was mentioned
        """
        if not self.claude_enabled:
            logger.info("Claude auto-response is disabled")
            return

        # Create agent session
        session_id = tracker.create_session(
            entity_type=entity_type,
            entity_id=str(entity_id)
        )

        # Broadcast session started
        session = tracker.get_session(session_id)
        if session:
            await manager.send_agent_started(session.to_dict())

        try:
            logger.info(
                f"Triggering Claude response for {entity_type} {entity_id}"
            )

            # Update status to processing
            tracker.update_status(session_id, AgentStatus.PROCESSING)
            if session:
                await manager.send_agent_status_update(tracker.get_session(session_id).to_dict())

            # Broadcast typing start to WebSocket clients
            await manager.send_ai_typing_start(entity_type, str(entity_id))

            # Update status to typing
            tracker.update_status(session_id, AgentStatus.TYPING)
            if session:
                await manager.send_agent_status_update(tracker.get_session(session_id).to_dict())

            # Send webhook request to host machine
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "entity_type": entity_type,
                    "entity_id": str(entity_id),
                }
                if staff_id:
                    payload["staff_id"] = str(staff_id)

                response = await client.post(
                    self.webhook_url,
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()

                if result.get("success"):
                    logger.info(
                        f"Claude generated response for {entity_type} {entity_id} "
                        f"(cost: ${result.get('cost_usd', 0):.4f})"
                    )

                    # Complete session with metrics
                    tracker.complete_session(
                        session_id,
                        cost_usd=result.get("cost_usd", 0.0)
                    )

                    # Persist to database
                    try:
                        async with DatabaseConnection() as db:
                            await tracker.persist_session(session_id, db)
                    except Exception as e:
                        logger.error(f"Failed to persist session to DB: {e}")

                    # Broadcast completion
                    completed_session = None
                    for s in tracker.get_recent(limit=1):
                        if s.session_id == session_id:
                            completed_session = s
                            break

                    if completed_session:
                        await manager.send_agent_completed(completed_session.to_dict())

                else:
                    error_msg = result.get("error", "Unknown error")
                    logger.warning(
                        f"Claude webhook failed for {entity_type} {entity_id}: {error_msg}"
                    )

                    # Fail session
                    tracker.fail_session(session_id, error_msg)

                    # Persist to database
                    try:
                        async with DatabaseConnection() as db:
                            await tracker.persist_session(session_id, db)
                    except Exception as e:
                        logger.error(f"Failed to persist session to DB: {e}")

                    # Broadcast failure
                    for s in tracker.get_recent(limit=1):
                        if s.session_id == session_id:
                            await manager.send_agent_failed(s.to_dict())
                            break

        except httpx.HTTPError as e:
            error_msg = f"Failed to reach webhook server: {e}"
            logger.error(error_msg)

            # Fail session
            tracker.fail_session(session_id, error_msg)

            # Persist to database
            try:
                async with DatabaseConnection() as db:
                    await tracker.persist_session(session_id, db)
            except Exception as e:
                logger.error(f"Failed to persist session to DB: {e}")

            # Broadcast failure
            for s in tracker.get_recent(limit=1):
                if s.session_id == session_id:
                    await manager.send_agent_failed(s.to_dict())
                    break

        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(error_msg, exc_info=True)

            # Fail session
            tracker.fail_session(session_id, error_msg)

            # Persist to database
            try:
                async with DatabaseConnection() as db:
                    await tracker.persist_session(session_id, db)
            except Exception as persist_error:
                logger.error(f"Failed to persist session to DB: {persist_error}")

            # Broadcast failure
            for s in tracker.get_recent(limit=1):
                if s.session_id == session_id:
                    await manager.send_agent_failed(s.to_dict())
                    break

        finally:
            # Always broadcast typing stop, even on error
            await manager.send_ai_typing_stop(entity_type, str(entity_id))

    async def trigger_group_discussion_response(
        self, discussion_id: UUID, initiating_staff_id: UUID
    ) -> None:
        """Trigger staff responses in a group discussion.

        This is called when a message is sent to a group discussion. It triggers
        responses from other staff members in the discussion.

        Args:
            discussion_id: UUID of the group discussion
            initiating_staff_id: ID of the staff member who sent the message
        """
        if not self.claude_enabled:
            logger.info("Claude auto-response is disabled")
            return

        try:
            logger.info(
                f"Triggering group discussion responses for discussion {discussion_id}"
            )

            # Send webhook request to host machine
            webhook_url = self.webhook_url.replace("/webhook/comment", "/webhook/group-discussion")
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "discussion_id": str(discussion_id),
                    "initiating_staff_id": str(initiating_staff_id),
                }

                response = await client.post(
                    webhook_url,
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()

                if result.get("success"):
                    logger.info(
                        f"Generated group discussion responses for {discussion_id} "
                        f"(cost: ${result.get('cost_usd', 0):.4f})"
                    )
                else:
                    error_msg = result.get("error", "Unknown error")
                    logger.warning(
                        f"Group discussion webhook failed for {discussion_id}: {error_msg}"
                    )

        except httpx.HTTPError as e:
            logger.error(f"Failed to reach webhook server for group discussion: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in group discussion webhook: {e}", exc_info=True)


# Singleton instance
_webhook_service: ClaudeWebhookService | None = None


def get_webhook_service() -> ClaudeWebhookService:
    """Get or create the webhook service singleton."""
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = ClaudeWebhookService()
    return _webhook_service
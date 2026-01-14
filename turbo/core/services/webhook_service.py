"""Webhook service for managing webhooks and emitting events."""

import asyncio
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.webhook import Webhook, WebhookDelivery
from turbo.core.repositories.webhook import WebhookRepository
from turbo.core.schemas.webhook import (
    WebhookCreate,
    WebhookUpdate,
    WebhookDeliveryCreate,
)
from turbo.utils.exceptions import WebhookNotFoundError

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for webhook operations and event emission."""

    def __init__(self, repository: WebhookRepository):
        self._repository = repository

    async def create_webhook(self, webhook_data: WebhookCreate) -> Webhook:
        """Create a new webhook."""
        return await self._repository.create(webhook_data)

    async def get_webhook(self, webhook_id: UUID) -> Webhook:
        """Get webhook by ID."""
        webhook = await self._repository.get_by_id(webhook_id)
        if not webhook:
            raise WebhookNotFoundError(f"Webhook with id {webhook_id} not found")
        return webhook

    async def list_webhooks(
        self,
        limit: int | None = None,
        offset: int | None = None,
        active_only: bool = False,
    ) -> list[Webhook]:
        """List all webhooks."""
        if active_only:
            return await self._repository.get_active_webhooks()
        return await self._repository.get_all(limit=limit, offset=offset)

    async def update_webhook(
        self, webhook_id: UUID, webhook_data: WebhookUpdate
    ) -> Webhook:
        """Update a webhook."""
        webhook = await self._repository.update(webhook_id, webhook_data)
        if not webhook:
            raise WebhookNotFoundError(f"Webhook with id {webhook_id} not found")
        return webhook

    async def delete_webhook(self, webhook_id: UUID) -> bool:
        """Delete a webhook."""
        deleted = await self._repository.delete(webhook_id)
        if not deleted:
            raise WebhookNotFoundError(f"Webhook with id {webhook_id} not found")
        return deleted

    async def get_webhook_deliveries(
        self, webhook_id: UUID, limit: int | None = None, offset: int | None = None
    ) -> list[WebhookDelivery]:
        """Get delivery history for a webhook."""
        return await self._repository.get_webhook_deliveries(
            webhook_id, limit=limit, offset=offset
        )

    async def emit_event(self, event_type: str, payload: dict) -> None:
        """
        Emit an event to all subscribed webhooks.

        This is the core event emission system that triggers webhooks.
        """
        logger.info(f"Emitting event: {event_type}")

        # Get all webhooks subscribed to this event
        webhooks = await self._repository.get_webhooks_for_event(event_type)
        logger.info(f"Found {len(webhooks)} webhooks subscribed to {event_type}")

        if not webhooks:
            return

        # Fire webhooks asynchronously
        tasks = [
            self._fire_webhook(webhook, event_type, payload)
            for webhook in webhooks
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _fire_webhook(
        self, webhook: Webhook, event_type: str, payload: dict
    ) -> None:
        """
        Fire a single webhook with retry logic.

        This creates a delivery record and attempts to send the webhook.
        """
        # Create delivery record
        delivery = await self._repository.create_delivery(
            WebhookDeliveryCreate(
                webhook_id=webhook.id,
                event_type=event_type,
                payload=payload,
                status="pending",
            )
        )

        # Attempt delivery
        await self._attempt_delivery(webhook, delivery)

    async def _attempt_delivery(
        self, webhook: Webhook, delivery: WebhookDelivery
    ) -> None:
        """
        Attempt to deliver a webhook.

        Handles HTTP request, HMAC signing, retries, and status updates.
        """
        try:
            # Prepare payload
            payload_json = json.dumps(delivery.payload)

            # Generate HMAC signature
            signature = self._generate_signature(payload_json, webhook.secret)

            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
                "X-Webhook-Event": delivery.event_type,
                "X-Webhook-Delivery-Id": str(delivery.id),
                **(webhook.headers or {}),
            }

            # Send webhook
            async with httpx.AsyncClient(timeout=webhook.timeout_seconds) as client:
                response = await client.post(
                    webhook.url,
                    content=payload_json,
                    headers=headers,
                )

                # Update delivery status
                if response.status_code >= 200 and response.status_code < 300:
                    # Success
                    await self._repository.update_delivery_status(
                        delivery.id,
                        status="success",
                        response_status_code=response.status_code,
                        response_body=response.text[:1000],  # Limit response size
                        delivered_at=datetime.now(),
                    )
                    logger.info(
                        f"Webhook {webhook.id} delivered successfully (status {response.status_code})"
                    )
                else:
                    # Failed but might retry
                    await self._handle_failed_delivery(
                        webhook, delivery, response.status_code, response.text
                    )

        except Exception as e:
            logger.error(f"Error delivering webhook {webhook.id}: {str(e)}")
            await self._handle_failed_delivery(
                webhook, delivery, error_message=str(e)
            )

    async def _handle_failed_delivery(
        self,
        webhook: Webhook,
        delivery: WebhookDelivery,
        response_status_code: int | None = None,
        response_body: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """Handle failed webhook delivery with retry logic."""
        # Increment attempt number
        delivery.attempt_number += 1

        if delivery.attempt_number <= webhook.max_retries:
            # Schedule retry with exponential backoff
            retry_delay = 2 ** (delivery.attempt_number - 1) * 60  # Minutes
            next_retry = datetime.now() + timedelta(minutes=retry_delay)

            await self._repository.update_delivery_status(
                delivery.id,
                status="retrying",
                response_status_code=response_status_code,
                response_body=response_body[:1000] if response_body else None,
                error_message=error_message,
                next_retry_at=next_retry,
            )
            logger.warning(
                f"Webhook {webhook.id} failed (attempt {delivery.attempt_number}/{webhook.max_retries}), "
                f"retrying at {next_retry}"
            )
        else:
            # Max retries exceeded
            await self._repository.update_delivery_status(
                delivery.id,
                status="failed",
                response_status_code=response_status_code,
                response_body=response_body[:1000] if response_body else None,
                error_message=error_message,
            )
            logger.error(
                f"Webhook {webhook.id} failed permanently after {delivery.attempt_number} attempts"
            )

    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC-SHA256 signature for webhook payload."""
        signature = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"

    async def test_webhook(self, webhook_id: UUID, test_payload: dict | None = None) -> WebhookDelivery:
        """Test fire a webhook with a test payload."""
        webhook = await self.get_webhook(webhook_id)

        if test_payload is None:
            test_payload = {
                "test": True,
                "message": "This is a test webhook delivery",
                "timestamp": datetime.now().isoformat(),
            }

        # Create delivery record
        delivery = await self._repository.create_delivery(
            WebhookDeliveryCreate(
                webhook_id=webhook.id,
                event_type="test.ping",
                payload=test_payload,
                status="pending",
            )
        )

        # Fire webhook
        await self._attempt_delivery(webhook, delivery)

        # Refresh and return delivery
        return await self._repository._session.get(WebhookDelivery, delivery.id)


def create_webhook_service(session: AsyncSession) -> WebhookService:
    """Factory function to create webhook service."""
    repository = WebhookRepository(session)
    return WebhookService(repository)

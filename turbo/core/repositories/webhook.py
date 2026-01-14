"""Webhook repository for database operations."""

from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from turbo.core.models.webhook import Webhook, WebhookDelivery
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.webhook import (
    WebhookCreate,
    WebhookUpdate,
    WebhookDeliveryCreate,
)


class WebhookRepository(BaseRepository[Webhook, WebhookCreate, WebhookUpdate]):
    """Repository for webhook operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Webhook)

    async def get_active_webhooks(self) -> list[Webhook]:
        """Get all active webhooks."""
        stmt = select(Webhook).where(Webhook.is_active == True)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_webhooks_for_event(self, event_type: str) -> list[Webhook]:
        """Get all active webhooks subscribed to a specific event."""
        stmt = select(Webhook).where(
            and_(
                Webhook.is_active == True,
                Webhook.events.contains([event_type])
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_webhook_deliveries(
        self,
        webhook_id: UUID,
        limit: int | None = None,
        offset: int | None = None
    ) -> list[WebhookDelivery]:
        """Get delivery history for a webhook."""
        stmt = select(WebhookDelivery).where(
            WebhookDelivery.webhook_id == webhook_id
        ).order_by(WebhookDelivery.created_at.desc())

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_delivery(self, delivery_data: WebhookDeliveryCreate) -> WebhookDelivery:
        """Create a new webhook delivery record."""
        delivery = WebhookDelivery(**delivery_data.model_dump(exclude_unset=True))
        self._session.add(delivery)
        await self._session.commit()
        await self._session.refresh(delivery)
        return delivery

    async def update_delivery_status(
        self,
        delivery_id: UUID,
        status: str,
        response_status_code: int | None = None,
        response_body: str | None = None,
        error_message: str | None = None,
        delivered_at: datetime | None = None,
        next_retry_at: datetime | None = None,
    ) -> WebhookDelivery | None:
        """Update webhook delivery status after attempt."""
        stmt = select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
        result = await self._session.execute(stmt)
        delivery = result.scalar_one_or_none()

        if not delivery:
            return None

        delivery.status = status
        if response_status_code is not None:
            delivery.response_status_code = response_status_code
        if response_body is not None:
            delivery.response_body = response_body
        if error_message is not None:
            delivery.error_message = error_message
        if delivered_at is not None:
            delivery.delivered_at = delivered_at
        if next_retry_at is not None:
            delivery.next_retry_at = next_retry_at

        await self._session.commit()
        await self._session.refresh(delivery)
        return delivery

    async def get_pending_deliveries(self) -> list[WebhookDelivery]:
        """Get all deliveries pending retry."""
        now = datetime.now()
        stmt = select(WebhookDelivery).where(
            and_(
                WebhookDelivery.status.in_(["pending", "retrying"]),
                WebhookDelivery.next_retry_at <= now
            )
        ).options(selectinload(WebhookDelivery.webhook))

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

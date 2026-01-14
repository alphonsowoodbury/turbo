"""Webhook API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from turbo.api.dependencies import get_db_session
from turbo.core.schemas.webhook import (
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookDeliveryResponse,
    WebhookTestRequest,
)
from turbo.core.services.webhook_service import create_webhook_service
from turbo.utils.exceptions import WebhookNotFoundError

router = APIRouter()


@router.post("/", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    webhook_data: WebhookCreate,
    session=Depends(get_db_session),
) -> WebhookResponse:
    """Create a new webhook."""
    service = create_webhook_service(session)
    return await service.create_webhook(webhook_data)


@router.get("/", response_model=list[WebhookResponse])
async def list_webhooks(
    active_only: bool | None = Query(False, description="Filter for active webhooks only"),
    limit: int | None = Query(100, ge=1, le=500),
    offset: int | None = Query(None, ge=0),
    session=Depends(get_db_session),
) -> list[WebhookResponse]:
    """List all webhooks with optional filtering."""
    service = create_webhook_service(session)
    return await service.list_webhooks(
        limit=limit,
        offset=offset,
        active_only=active_only or False,
    )


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: UUID,
    session=Depends(get_db_session),
) -> WebhookResponse:
    """Get a webhook by ID."""
    service = create_webhook_service(session)
    try:
        return await service.get_webhook(webhook_id)
    except WebhookNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook with id {webhook_id} not found",
        )


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: UUID,
    webhook_data: WebhookUpdate,
    session=Depends(get_db_session),
) -> WebhookResponse:
    """Update a webhook."""
    service = create_webhook_service(session)
    try:
        return await service.update_webhook(webhook_id, webhook_data)
    except WebhookNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook with id {webhook_id} not found",
        )


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: UUID,
    session=Depends(get_db_session),
) -> None:
    """Delete a webhook."""
    service = create_webhook_service(session)
    try:
        await service.delete_webhook(webhook_id)
    except WebhookNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook with id {webhook_id} not found",
        )


@router.get("/{webhook_id}/deliveries", response_model=list[WebhookDeliveryResponse])
async def get_webhook_deliveries(
    webhook_id: UUID,
    limit: int | None = Query(50, ge=1, le=100),
    offset: int | None = Query(None, ge=0),
    session=Depends(get_db_session),
) -> list[WebhookDeliveryResponse]:
    """Get delivery history for a webhook."""
    service = create_webhook_service(session)
    try:
        # Verify webhook exists
        await service.get_webhook(webhook_id)
        return await service.get_webhook_deliveries(
            webhook_id, limit=limit, offset=offset
        )
    except WebhookNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook with id {webhook_id} not found",
        )


@router.post("/{webhook_id}/test", response_model=WebhookDeliveryResponse)
async def test_webhook(
    webhook_id: UUID,
    test_request: WebhookTestRequest | None = None,
    session=Depends(get_db_session),
) -> WebhookDeliveryResponse:
    """Test fire a webhook with a test payload."""
    service = create_webhook_service(session)
    try:
        test_payload = test_request.payload if test_request else None
        return await service.test_webhook(webhook_id, test_payload)
    except WebhookNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook with id {webhook_id} not found",
        )

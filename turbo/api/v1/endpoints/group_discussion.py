"""Group discussion API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from turbo.api.dependencies import (
    get_group_discussion_service,
    get_staff_service,
)
from turbo.core.schemas.group_discussion import (
    GroupDiscussionCreate,
    GroupDiscussionResponse,
    GroupDiscussionUpdate,
)
from turbo.core.schemas.staff import StaffConversationResponse
from turbo.core.services import get_webhook_service
from turbo.utils.exceptions import GroupDiscussionNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response models
from pydantic import BaseModel, Field


class SendMessageRequest(BaseModel):
    """Request body for sending messages to group discussions."""

    staff_id: UUID | None = Field(None, description="ID of the staff member sending the message (null for user messages)")
    content: str = Field(..., min_length=1, max_length=10000)
    is_user_message: bool = Field(False, description="True if this is a message from the user (not a staff member)")


class MessagesResponse(BaseModel):
    """Response with discussion messages."""

    messages: list[StaffConversationResponse]
    total: int
    discussion_id: UUID


@router.post("/", response_model=GroupDiscussionResponse, status_code=status.HTTP_201_CREATED)
async def create_discussion(
    discussion_data: GroupDiscussionCreate,
    service=Depends(get_group_discussion_service),
) -> GroupDiscussionResponse:
    """Create a new group discussion."""
    try:
        return await service.create_discussion(discussion_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/", response_model=list[GroupDiscussionResponse])
async def list_discussions(
    discussion_type: str | None = Query(None, pattern="^(all_hands|department|ad_hoc)$"),
    status_filter: str | None = Query("active", alias="status", pattern="^(active|archived)$"),
    limit: int | None = Query(100, ge=1, le=500),
    offset: int | None = Query(None, ge=0),
    service=Depends(get_group_discussion_service),
) -> list[GroupDiscussionResponse]:
    """List all group discussions with optional filters."""
    return await service.list_discussions(
        discussion_type=discussion_type,
        status=status_filter,
        limit=limit,
        offset=offset,
    )


@router.get("/all-hands", response_model=GroupDiscussionResponse)
async def get_all_hands(
    service=Depends(get_group_discussion_service),
) -> GroupDiscussionResponse:
    """Get the All Hands discussion room."""
    try:
        return await service.get_all_hands()
    except GroupDiscussionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="All Hands discussion room not found",
        )


@router.get("/{discussion_id}", response_model=GroupDiscussionResponse)
async def get_discussion(
    discussion_id: UUID,
    service=Depends(get_group_discussion_service),
) -> GroupDiscussionResponse:
    """Get a discussion by ID."""
    try:
        return await service.get_discussion(discussion_id)
    except GroupDiscussionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discussion with id {discussion_id} not found",
        )


@router.put("/{discussion_id}", response_model=GroupDiscussionResponse)
async def update_discussion(
    discussion_id: UUID,
    discussion_data: GroupDiscussionUpdate,
    service=Depends(get_group_discussion_service),
) -> GroupDiscussionResponse:
    """Update a discussion."""
    try:
        return await service.update_discussion(discussion_id, discussion_data)
    except GroupDiscussionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discussion with id {discussion_id} not found",
        )


@router.delete("/{discussion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_discussion(
    discussion_id: UUID,
    service=Depends(get_group_discussion_service),
) -> None:
    """Delete a discussion."""
    try:
        await service.delete_discussion(discussion_id)
    except GroupDiscussionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discussion with id {discussion_id} not found",
        )


@router.get("/{discussion_id}/messages", response_model=MessagesResponse)
async def get_messages(
    discussion_id: UUID,
    limit: int | None = Query(50, ge=1, le=100),
    offset: int | None = Query(None, ge=0),
    service=Depends(get_group_discussion_service),
) -> MessagesResponse:
    """Get messages for a discussion."""
    try:
        messages = await service.get_messages(
            discussion_id=discussion_id,
            limit=limit,
            offset=offset,
        )

        # Get total count
        from turbo.api.dependencies import get_group_discussion_repository, get_db_session

        async for session in get_db_session():
            repo = get_group_discussion_repository(session)
            total = await repo.count_messages(discussion_id)
            break

        return MessagesResponse(
            messages=messages,
            total=total,
            discussion_id=discussion_id,
        )
    except GroupDiscussionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discussion with id {discussion_id} not found",
        )


@router.post("/{discussion_id}/messages", response_model=StaffConversationResponse)
async def send_message(
    discussion_id: UUID,
    message_request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    service=Depends(get_group_discussion_service),
) -> StaffConversationResponse:
    """
    Send a message to a group discussion.

    The message is saved immediately and triggers responses from other
    staff members via webhook in the background.
    """
    try:
        # Determine message type and staff ID
        if message_request.is_user_message:
            # User message - no staff_id needed
            message_type = "user"
            staff_id_for_message = message_request.staff_id  # Will be None for user messages
        else:
            # Staff member message
            message_type = "assistant"
            staff_id_for_message = message_request.staff_id
            if not staff_id_for_message:
                raise ValueError("staff_id required when is_user_message is False")

        # Add the message
        message = await service.add_message(
            discussion_id=discussion_id,
            staff_id=staff_id_for_message,
            content=message_request.content,
            message_type=message_type,
        )

        # Trigger webhook to generate staff responses
        # For user messages: all staff can respond
        # For staff messages: exclude the sender so they don't respond to themselves
        webhook_service = get_webhook_service()
        background_tasks.add_task(
            webhook_service.trigger_group_discussion_response,
            discussion_id,
            staff_id_for_message,  # None for user messages, staff_id for staff messages
        )

        return message
    except GroupDiscussionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discussion with id {discussion_id} not found",
        )
    except Exception:
        logger.exception("Failed to send group discussion message")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message",
        )


@router.post("/{discussion_id}/participants/{staff_id}", response_model=GroupDiscussionResponse)
async def add_participant(
    discussion_id: UUID,
    staff_id: UUID,
    service=Depends(get_group_discussion_service),
) -> GroupDiscussionResponse:
    """Add a participant to a discussion."""
    try:
        return await service.add_participant(
            discussion_id=discussion_id,
            staff_id=staff_id,
        )
    except GroupDiscussionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discussion with id {discussion_id} not found",
        )


@router.delete("/{discussion_id}/participants/{staff_id}", response_model=GroupDiscussionResponse)
async def remove_participant(
    discussion_id: UUID,
    staff_id: UUID,
    service=Depends(get_group_discussion_service),
) -> GroupDiscussionResponse:
    """Remove a participant from a discussion."""
    try:
        return await service.remove_participant(
            discussion_id=discussion_id,
            staff_id=staff_id,
        )
    except GroupDiscussionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discussion with id {discussion_id} not found",
        )

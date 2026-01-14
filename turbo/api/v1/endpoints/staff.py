"""Staff API endpoints."""

from uuid import UUID
import json
import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from turbo.api.dependencies import (
    get_staff_repository,
    get_staff_conversation_repository,
    get_staff_service,
)
from turbo.core.schemas.staff import (
    StaffCreate,
    StaffResponse,
    StaffSummary,
    StaffUpdate,
    StaffConversationResponse,
    StaffProfileResponse,
    StaffActivityItem,
)
from turbo.core.services import get_webhook_service
from turbo.core.services.staff import StaffService
from turbo.utils.exceptions import StaffNotFoundError

router = APIRouter()


# Request/Response models for messaging
from pydantic import BaseModel, Field


class SendMessageRequest(BaseModel):
    """Request body for sending messages to staff."""

    content: str = Field(..., min_length=1, max_length=10000)


class ConversationHistoryResponse(BaseModel):
    """Response with conversation history."""

    messages: list[StaffConversationResponse]
    total: int
    staff_id: UUID


@router.post("/", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    staff_data: StaffCreate,
    staff_service: StaffService = Depends(get_staff_service),
) -> StaffResponse:
    """Create a new staff member."""
    try:
        return await staff_service.create_staff(staff_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create staff: {str(e)}",
        )


@router.get("/", response_model=list[StaffResponse])
async def get_staff_list(
    role_type: str | None = Query(None, pattern="^(leadership|domain_expert)$"),
    is_active: bool | None = Query(True),
    limit: int | None = Query(None, ge=1, le=100),
    offset: int | None = Query(None, ge=0),
    staff_service: StaffService = Depends(get_staff_service),
) -> list[StaffResponse]:
    """Get all staff with optional filtering."""
    return await staff_service.get_all_staff(
        role_type=role_type,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.get("/leadership", response_model=list[StaffSummary])
async def get_leadership_staff(
    staff_service: StaffService = Depends(get_staff_service),
) -> list[StaffSummary]:
    """Get all active leadership staff (with universal edit permissions)."""
    return await staff_service.get_leadership_staff()


@router.get("/domain", response_model=list[StaffSummary])
async def get_domain_staff(
    staff_service: StaffService = Depends(get_staff_service),
) -> list[StaffSummary]:
    """Get all active domain expert staff (can only edit assigned entities)."""
    return await staff_service.get_domain_staff()


@router.get("/search", response_model=list[StaffSummary])
async def search_staff(
    query: str = Query(..., min_length=1, max_length=100),
    staff_service: StaffService = Depends(get_staff_service),
) -> list[StaffSummary]:
    """Search staff by name or handle."""
    return await staff_service.search_staff(query)


@router.get("/handle/{handle}", response_model=StaffResponse)
async def get_staff_by_handle(
    handle: str,
    staff_service: StaffService = Depends(get_staff_service),
) -> StaffResponse:
    """Get staff by handle (for @ mention resolution)."""
    try:
        return await staff_service.get_staff_by_handle(handle)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(
    staff_id: UUID,
    staff_service: StaffService = Depends(get_staff_service),
) -> StaffResponse:
    """Get a staff member by ID."""
    try:
        return await staff_service.get_staff(staff_id)
    except StaffNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with id {staff_id} not found",
        )


@router.get("/{staff_id}/profile", response_model=StaffProfileResponse)
async def get_staff_profile(
    staff_id: UUID,
    staff_service: StaffService = Depends(get_staff_service),
) -> StaffProfileResponse:
    """
    Get comprehensive staff profile with analytics, work assignments, and activity feed.

    Includes:
    - Basic staff information with rating
    - Performance metrics
    - Assigned review requests and issues
    - Recent activity feed
    """
    try:
        return await staff_service.get_staff_profile(staff_id)
    except StaffNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with id {staff_id} not found",
        )


@router.put("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: UUID,
    staff_data: StaffUpdate,
    staff_service: StaffService = Depends(get_staff_service),
) -> StaffResponse:
    """Update a staff member."""
    try:
        return await staff_service.update_staff(staff_id, staff_data)
    except StaffNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with id {staff_id} not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update staff: {str(e)}",
        )


@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff(
    staff_id: UUID,
    staff_service: StaffService = Depends(get_staff_service),
) -> None:
    """Delete a staff member (cascade deletes conversations and review requests)."""
    try:
        await staff_service.delete_staff(staff_id)
    except StaffNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with id {staff_id} not found",
        )


@router.post("/{staff_id}/deactivate", response_model=StaffResponse)
async def deactivate_staff(
    staff_id: UUID,
    staff_service: StaffService = Depends(get_staff_service),
) -> StaffResponse:
    """Deactivate a staff member (soft delete)."""
    try:
        return await staff_service.deactivate_staff(staff_id)
    except StaffNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with id {staff_id} not found",
        )


@router.post("/{staff_id}/activate", response_model=StaffResponse)
async def activate_staff(
    staff_id: UUID,
    staff_service: StaffService = Depends(get_staff_service),
) -> StaffResponse:
    """Activate a staff member."""
    try:
        return await staff_service.activate_staff(staff_id)
    except StaffNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with id {staff_id} not found",
        )


# Conversation endpoints


@router.post("/{staff_id}/messages", response_model=StaffConversationResponse)
async def send_message(
    staff_id: UUID,
    message_request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    staff_service: StaffService = Depends(get_staff_service),
) -> StaffConversationResponse:
    """
    Send a message to a staff member and get async response via webhook.

    The message is saved immediately and a webhook is triggered in the background
    to generate the staff's response asynchronously.
    """
    try:
        user_message = await staff_service.add_user_message(
            staff_id=staff_id,
            content=message_request.content,
            is_group_discussion=False,
            group_discussion_id=None,
        )

        # Trigger webhook in background to generate staff response
        webhook_service = get_webhook_service()
        background_tasks.add_task(
            webhook_service.trigger_entity_response,
            "staff",
            staff_id
        )

        return user_message
    except StaffNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with id {staff_id} not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}",
        )


@router.post("/{staff_id}/assistant-message", response_model=StaffConversationResponse)
async def add_assistant_message(
    staff_id: UUID,
    message_request: SendMessageRequest,
    staff_service: StaffService = Depends(get_staff_service),
) -> StaffConversationResponse:
    """Add an assistant message to the conversation (called by webhook after generation)."""
    try:
        return await staff_service.add_assistant_message(
            staff_id=staff_id,
            content=message_request.content,
            is_group_discussion=False,
            group_discussion_id=None,
        )
    except StaffNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with id {staff_id} not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add assistant message: {str(e)}",
        )


@router.get("/{staff_id}/messages", response_model=ConversationHistoryResponse)
async def get_conversation(
    staff_id: UUID,
    limit: int | None = Query(50, ge=1, le=100),
    offset: int | None = Query(None, ge=0),
    staff_service: StaffService = Depends(get_staff_service),
) -> ConversationHistoryResponse:
    """Get conversation history for a staff member."""
    try:
        messages = await staff_service.get_conversation(
            staff_id=staff_id, limit=limit, offset=offset
        )

        # Get total count
        from turbo.api.dependencies import get_staff_conversation_repository
        from turbo.api.dependencies import get_db_session

        async for session in get_db_session():
            repo = get_staff_conversation_repository(session)
            total = await repo.count_messages(staff_id)
            break

        return ConversationHistoryResponse(
            messages=messages, total=total, staff_id=staff_id
        )
    except StaffNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with id {staff_id} not found",
        )


@router.delete("/{staff_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    staff_id: UUID,
    message_id: UUID,
    staff_service: StaffService = Depends(get_staff_service),
) -> None:
    """Delete a specific message from the conversation."""
    try:
        await staff_service.delete_message(staff_id, message_id)
    except StaffNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with id {staff_id} not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/{staff_id}/messages", status_code=status.HTTP_200_OK)
async def clear_conversation(
    staff_id: UUID,
    staff_service: StaffService = Depends(get_staff_service),
) -> dict:
    """Clear conversation history for a staff member."""
    try:
        deleted_count = await staff_service.clear_conversation(staff_id)
        return {
            "deleted_count": deleted_count,
            "message": "Conversation cleared successfully",
        }
    except StaffNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with id {staff_id} not found",
        )


@router.post("/{staff_id}/messages/stream")
async def send_message_stream(
    staff_id: UUID,
    message_request: SendMessageRequest,
    staff_service: StaffService = Depends(get_staff_service),
):
    """
    Send a message to a staff member and receive streaming response.

    Returns Server-Sent Events (SSE) stream with real-time AI response.
    Each event contains a JSON chunk with either:
    - {"type": "token", "content": "..."} - A chunk of the response
    - {"type": "done", "message_id": "..."} - Stream complete with saved message ID
    - {"type": "error", "detail": "..."} - Error occurred
    """
    try:
        # Verify staff exists
        staff = await staff_service.get_staff(staff_id)

        # Save user message immediately
        user_message = await staff_service.add_user_message(
            staff_id=staff_id,
            content=message_request.content,
            is_group_discussion=False,
            group_discussion_id=None,
        )

        async def generate():
            """Generate SSE stream for AI response."""
            try:
                # Import streaming service
                from turbo.core.services.streaming import get_streaming_response

                accumulated_content = ""

                # Stream the AI response
                async for chunk in get_streaming_response(
                    entity_type="staff",
                    entity_id=staff_id,
                    user_message_content=message_request.content
                ):
                    accumulated_content += chunk
                    # Send token event
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
                    await asyncio.sleep(0)  # Allow other tasks to run

                # Save the complete assistant message
                assistant_message = await staff_service.add_assistant_message(
                    staff_id=staff_id,
                    content=accumulated_content,
                    is_group_discussion=False,
                    group_discussion_id=None,
                )

                # Send done event with message ID
                yield f"data: {json.dumps({'type': 'done', 'message_id': str(assistant_message.id)})}\n\n"

            except Exception as e:
                # Send error event
                yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )

    except StaffNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with id {staff_id} not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send streaming message: {str(e)}",
        )

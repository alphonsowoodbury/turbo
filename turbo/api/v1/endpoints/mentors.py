"""Mentor API endpoints."""

from uuid import UUID
import json
import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from turbo.api.dependencies import (
    get_mentor_context_service,
    get_mentor_conversation_repository,
    get_mentor_repository,
    get_mentor_service,
)
from turbo.core.schemas.mentor import MentorCreate, MentorResponse, MentorUpdate
from turbo.core.schemas.mentor_conversation import (
    ConversationHistoryResponse,
    MentorConversationResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from turbo.core.services import get_webhook_service
from turbo.core.services.mentor import MentorService
from turbo.utils.exceptions import MentorNotFoundError

router = APIRouter()


@router.post("/", response_model=MentorResponse, status_code=status.HTTP_201_CREATED)
async def create_mentor(
    mentor_data: MentorCreate,
    mentor_service: MentorService = Depends(get_mentor_service),
) -> MentorResponse:
    """Create a new mentor."""
    try:
        return await mentor_service.create_mentor(mentor_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create mentor: {str(e)}",
        )


@router.get("/", response_model=list[MentorResponse])
async def get_mentors(
    workspace: str | None = Query(None, pattern="^(all|personal|freelance|work)$"),
    work_company: str | None = Query(None),
    is_active: bool | None = Query(True),
    limit: int | None = Query(None, ge=1, le=100),
    offset: int | None = Query(None, ge=0),
    mentor_service: MentorService = Depends(get_mentor_service),
) -> list[MentorResponse]:
    """Get all mentors with optional filtering by workspace."""
    if workspace and workspace != "all":
        return await mentor_service.get_mentors_by_workspace(
            workspace=workspace,
            work_company=work_company,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )
    else:
        # Get all mentors (no workspace filter)
        return await mentor_service.get_all_mentors(
            is_active=is_active,
            limit=limit,
            offset=offset,
        )


@router.get("/{mentor_id}", response_model=MentorResponse)
async def get_mentor(
    mentor_id: UUID,
    mentor_service: MentorService = Depends(get_mentor_service),
) -> MentorResponse:
    """Get a mentor by ID."""
    try:
        return await mentor_service.get_mentor(mentor_id)
    except MentorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mentor with id {mentor_id} not found",
        )


@router.put("/{mentor_id}", response_model=MentorResponse)
async def update_mentor(
    mentor_id: UUID,
    mentor_data: MentorUpdate,
    mentor_service: MentorService = Depends(get_mentor_service),
) -> MentorResponse:
    """Update a mentor."""
    try:
        return await mentor_service.update_mentor(mentor_id, mentor_data)
    except MentorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mentor with id {mentor_id} not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update mentor: {str(e)}",
        )


@router.delete("/{mentor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mentor(
    mentor_id: UUID,
    mentor_service: MentorService = Depends(get_mentor_service),
) -> None:
    """Delete a mentor."""
    try:
        await mentor_service.delete_mentor(mentor_id)
    except MentorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mentor with id {mentor_id} not found",
        )


@router.post("/{mentor_id}/messages", response_model=SendMessageResponse)
async def send_message(
    mentor_id: UUID,
    message_request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    mentor_service: MentorService = Depends(get_mentor_service),
) -> SendMessageResponse:
    """Send a message to a mentor and get async response via webhook.

    The message is saved immediately and a webhook is triggered in the background
    to generate the mentor's response asynchronously.
    """
    try:
        response = await mentor_service.send_message(mentor_id, message_request.content)

        # Trigger webhook in background to generate mentor response
        webhook_service = get_webhook_service()
        background_tasks.add_task(
            webhook_service.trigger_entity_response,
            "mentor",
            mentor_id
        )

        return response
    except MentorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mentor with id {mentor_id} not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}",
        )


@router.post("/{mentor_id}/messages/stream")
async def send_message_stream(
    mentor_id: UUID,
    message_request: SendMessageRequest,
    mentor_service: MentorService = Depends(get_mentor_service),
):
    """
    Send a message to a mentor and receive streaming response.

    Returns Server-Sent Events (SSE) stream with real-time AI response.
    Each event contains a JSON chunk with either:
    - {"type": "token", "content": "..."} - A chunk of the response
    - {"type": "done", "message_id": "..."} - Stream complete with saved message ID
    - {"type": "error", "detail": "..."} - Error occurred
    """
    try:
        # Verify mentor exists
        mentor = await mentor_service.get_mentor(mentor_id)

        # Save user message immediately
        user_message = await mentor_service.send_message(mentor_id, message_request.content)

        async def generate():
            """Generate SSE stream for AI response."""
            try:
                # Import streaming service
                from turbo.core.services.streaming import get_streaming_response

                accumulated_content = ""

                # Stream the AI response
                async for chunk in get_streaming_response(
                    entity_type="mentor",
                    entity_id=mentor_id,
                    user_message_content=message_request.content
                ):
                    accumulated_content += chunk
                    # Send token event
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
                    await asyncio.sleep(0)  # Allow other tasks to run

                # Save the complete assistant message
                assistant_message = await mentor_service.add_assistant_message(
                    mentor_id=mentor_id,
                    content=accumulated_content,
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

    except MentorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mentor with id {mentor_id} not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send streaming message: {str(e)}",
        )


@router.post("/{mentor_id}/assistant-message", response_model=MentorConversationResponse)
async def add_assistant_message(
    mentor_id: UUID,
    message_request: SendMessageRequest,
    mentor_service: MentorService = Depends(get_mentor_service),
) -> MentorConversationResponse:
    """Add an assistant message to the conversation (called by webhook after generation)."""
    try:
        return await mentor_service.add_assistant_message(mentor_id, message_request.content)
    except MentorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mentor with id {mentor_id} not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add assistant message: {str(e)}",
        )


@router.get("/{mentor_id}/messages", response_model=ConversationHistoryResponse)
async def get_conversation(
    mentor_id: UUID,
    limit: int | None = Query(None, ge=1, le=100),
    offset: int | None = Query(None, ge=0),
    mentor_service: MentorService = Depends(get_mentor_service),
) -> ConversationHistoryResponse:
    """Get conversation history for a mentor."""
    try:
        return await mentor_service.get_conversation(mentor_id, limit=limit, offset=offset)
    except MentorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mentor with id {mentor_id} not found",
        )


@router.put("/{mentor_id}/messages/{message_id}", response_model=MentorConversationResponse)
async def update_message(
    mentor_id: UUID,
    message_id: UUID,
    message_update: SendMessageRequest,
    mentor_service: MentorService = Depends(get_mentor_service),
) -> MentorConversationResponse:
    """Update a message in the conversation."""
    try:
        return await mentor_service.update_message(mentor_id, message_id, message_update.content)
    except MentorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mentor with id {mentor_id} not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update message: {str(e)}",
        )


@router.delete("/{mentor_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    mentor_id: UUID,
    message_id: UUID,
    mentor_service: MentorService = Depends(get_mentor_service),
) -> None:
    """Delete a specific message from the conversation."""
    try:
        await mentor_service.delete_message(mentor_id, message_id)
    except MentorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mentor with id {mentor_id} not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/{mentor_id}/messages", status_code=status.HTTP_200_OK)
async def clear_conversation(
    mentor_id: UUID,
    mentor_service: MentorService = Depends(get_mentor_service),
) -> dict:
    """Clear conversation history for a mentor."""
    try:
        deleted_count = await mentor_service.clear_conversation(mentor_id)
        return {"deleted_count": deleted_count, "message": "Conversation cleared successfully"}
    except MentorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mentor with id {mentor_id} not found",
        )


@router.get("/{mentor_id}/response-status", response_model=dict)
async def check_response_status(
    mentor_id: UUID,
    mentor_service: MentorService = Depends(get_mentor_service),
) -> dict:
    """Check if Claude Code has written a response (for polling)."""
    # This is a simple status check endpoint for the frontend to poll
    # The actual response waiting logic is in the send_message endpoint
    try:
        # Just verify mentor exists
        await mentor_service.get_mentor(mentor_id)
        return {"status": "ready"}
    except MentorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mentor with id {mentor_id} not found",
        )

"""Comment API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.database.connection import get_db_session
from turbo.core.models import Comment, Issue, Project, Document, Initiative, Milestone, Blueprint
from turbo.core.schemas.comment import CommentCreate, CommentResponse, CommentUpdate
from turbo.core.services import get_webhook_service
from turbo.core.services.websocket_manager import manager
from turbo.core.utils.comment_parser import should_trigger_ai_response, extract_staff_mentions
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_entity_owner_staff_id(db: AsyncSession, entity_type: str, entity_id: UUID) -> UUID | None:
    """Get the staff owner ID for an entity if it has one.

    Returns the staff UUID if the entity has assigned_to_type='staff', otherwise None.
    """
    # Map entity types to models
    entity_model_map = {
        "issue": Issue,
        "project": Project,
        "document": Document,
        "initiative": Initiative,
        "milestone": Milestone,
        "blueprint": Blueprint,
    }

    model = entity_model_map.get(entity_type)
    if not model:
        return None

    # Fetch the entity
    result = await db.execute(select(model).where(model.id == entity_id))
    entity = result.scalar_one_or_none()

    if not entity:
        return None

    # Check if entity has assigned_to_type and assigned_to_id attributes
    if not hasattr(entity, 'assigned_to_type') or not hasattr(entity, 'assigned_to_id'):
        return None

    # Return staff_id only if assigned to staff
    if entity.assigned_to_type == "staff" and entity.assigned_to_id:
        return entity.assigned_to_id

    return None


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
) -> CommentResponse:
    """Create a new comment on any entity (issue, project, milestone, etc.).

    If the comment is from a user on an issue, triggers a background task to have Claude respond.
    """
    comment = Comment(
        entity_type=comment_data.entity_type,
        entity_id=comment_data.entity_id,
        content=comment_data.content,
        author_name=comment_data.author_name,
        author_type=comment_data.author_type,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    # Broadcast to WebSocket clients
    comment_response = CommentResponse.model_validate(comment)
    await manager.send_comment_created(
        comment.entity_type,
        str(comment.entity_id),
        comment_response.model_dump(mode='json')
    )

    # Trigger Claude response when user @mentions AI or staff (avoid infinite loops)
    if comment.author_type == "user" and should_trigger_ai_response(comment.content):
        webhook_service = get_webhook_service()

        # Extract staff mentions and resolve to staff IDs
        mentioned_staff = extract_staff_mentions(comment.content)
        staff_id = None

        if mentioned_staff:
            # Get the first mentioned staff member
            from turbo.core.repositories.staff import StaffRepository
            staff_repo = StaffRepository(db)

            # Try to find staff by alias or handle
            for mention in mentioned_staff:
                staff_member = await staff_repo.get_by_handle(mention)
                if staff_member:
                    staff_id = staff_member.id
                    logger.info(f"Resolved @{mention} to staff member: {staff_member.name} ({staff_id})")
                    break

        background_tasks.add_task(
            webhook_service.trigger_entity_response,
            comment.entity_type,
            comment.entity_id,
            staff_id
        )

    # AUTO-NOTIFY OWNER: Always trigger notification for assigned owner (if exists)
    # This ensures owners are notified of ALL comments without needing to @mention them
    if comment.author_type == "user":
        # Fetch the entity to check if it has an assigned owner
        entity_owner_staff_id = await get_entity_owner_staff_id(db, comment.entity_type, comment.entity_id)

        if entity_owner_staff_id:
            # Only trigger if owner wasn't already mentioned (avoid duplicate notifications)
            mentioned_staff = extract_staff_mentions(comment.content)
            owner_already_mentioned = False

            if mentioned_staff:
                from turbo.core.repositories.staff import StaffRepository
                staff_repo = StaffRepository(db)

                for mention in mentioned_staff:
                    staff_member = await staff_repo.get_by_handle(mention)
                    if staff_member and staff_member.id == entity_owner_staff_id:
                        owner_already_mentioned = True
                        break

            # Trigger owner notification if not already mentioned
            if not owner_already_mentioned:
                webhook_service = get_webhook_service()
                background_tasks.add_task(
                    webhook_service.trigger_entity_response,
                    comment.entity_type,
                    comment.entity_id,
                    entity_owner_staff_id
                )
                logger.info(f"Auto-notifying owner (staff_id={entity_owner_staff_id}) of comment on {comment.entity_type} {comment.entity_id}")

    return comment_response


@router.get("/entity/{entity_type}/{entity_id}", response_model=list[CommentResponse])
async def get_entity_comments(
    entity_type: str,
    entity_id: UUID,
    db: AsyncSession = Depends(get_db_session)
) -> list[CommentResponse]:
    """Get all comments for an entity (issue, project, milestone, etc.)."""
    # Validate entity type
    valid_types = ["issue", "project", "milestone", "initiative", "document", "literature", "blueprint"]
    if entity_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid entity type. Must be one of: {', '.join(valid_types)}"
        )

    result = await db.execute(
        select(Comment)
        .where(Comment.entity_type == entity_type, Comment.entity_id == entity_id)
        .order_by(Comment.created_at.asc())
    )
    comments = result.scalars().all()
    return [CommentResponse.model_validate(comment) for comment in comments]


@router.get("/id/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: UUID, db: AsyncSession = Depends(get_db_session)
) -> CommentResponse:
    """Get a comment by ID."""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with id {comment_id} not found",
        )

    return CommentResponse.model_validate(comment)


@router.put("/id/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: UUID,
    comment_data: CommentUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> CommentResponse:
    """Update a comment."""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with id {comment_id} not found",
        )

    if comment_data.content is not None:
        comment.content = comment_data.content

    await db.commit()
    await db.refresh(comment)

    # Broadcast to WebSocket clients
    comment_response = CommentResponse.model_validate(comment)
    await manager.send_comment_updated(
        comment.entity_type,
        str(comment.entity_id),
        comment_response.model_dump(mode='json')
    )

    return comment_response


@router.delete("/id/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID, db: AsyncSession = Depends(get_db_session)
) -> None:
    """Delete a comment."""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with id {comment_id} not found",
        )

    # Store entity info before deletion
    entity_type = comment.entity_type
    entity_id = str(comment.entity_id)
    comment_id_str = str(comment.id)

    await db.delete(comment)
    await db.commit()

    # Broadcast to WebSocket clients
    await manager.send_comment_deleted(entity_type, entity_id, comment_id_str)

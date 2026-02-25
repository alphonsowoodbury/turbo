"""Note API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from turbo.api.dependencies import get_note_service
from turbo.core.schemas.note import NoteCreate, NoteResponse, NoteUpdate
from turbo.core.services.note import NoteService
from turbo.utils.exceptions import (
    NoteNotFoundError,
    ValidationError as TurboValidationError,
)

router = APIRouter()


@router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_data: NoteCreate, note_service: NoteService = Depends(get_note_service)
) -> NoteResponse:
    """Create a new note."""
    try:
        return await note_service.create_note(note_data)
    except TurboValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: UUID, note_service: NoteService = Depends(get_note_service)
) -> NoteResponse:
    """Get a note by ID."""
    try:
        return await note_service.get_note(note_id)
    except NoteNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with id {note_id} not found",
        )


@router.get("/", response_model=list[NoteResponse])
async def get_notes(
    workspace: str | None = Query(None, pattern="^(personal|freelance|work)$"),
    work_company: str | None = Query(None),
    include_archived: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str | None = Query(None),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    note_service: NoteService = Depends(get_note_service),
) -> list[NoteResponse]:
    """Get all notes with optional filtering by workspace and company."""
    return await note_service.list_notes(
        workspace=workspace,
        work_company=work_company,
        include_archived=include_archived,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/search/", response_model=list[NoteResponse])
async def search_notes(
    q: str = Query(..., min_length=1),
    workspace: str | None = Query(None, pattern="^(personal|freelance|work)$"),
    include_archived: bool = Query(False),
    note_service: NoteService = Depends(get_note_service),
) -> list[NoteResponse]:
    """Search notes by title or content."""
    return await note_service.search_notes(
        query=q,
        workspace=workspace,
        include_archived=include_archived,
    )


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: UUID,
    note_data: NoteUpdate,
    note_service: NoteService = Depends(get_note_service),
) -> NoteResponse:
    """Update a note."""
    try:
        return await note_service.update_note(note_id, note_data)
    except NoteNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with id {note_id} not found",
        )
    except TurboValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: UUID, note_service: NoteService = Depends(get_note_service)
) -> None:
    """Delete a note."""
    try:
        await note_service.delete_note(note_id)
    except NoteNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with id {note_id} not found",
        )

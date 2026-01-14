"""API endpoints for forms."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.api.dependencies import get_db_session
from turbo.core.repositories.form import FormRepository, FormResponseRepository
from turbo.core.schemas.form import (
    FormCreate,
    FormResponse as FormResponseSchema,
    FormResponseCreate,
    FormResponseResponse,
    FormResponseUpdate,
    FormUpdate,
)

router = APIRouter(prefix="/forms", tags=["forms"])


@router.post("/", response_model=FormResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_form(
    form_data: FormCreate,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new form.

    Can be attached to an issue, document, or project.
    """
    repo = FormRepository(session)
    form = await repo.create_form(form_data.model_dump())
    return FormResponseSchema.model_validate(form)


@router.get("/{form_id}", response_model=FormResponseSchema)
async def get_form(
    form_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Get a form by ID."""
    repo = FormRepository(session)
    form = await repo.get_form(form_id)

    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Form with ID {form_id} not found",
        )

    return FormResponseSchema.model_validate(form)


@router.put("/{form_id}", response_model=FormResponseSchema)
async def update_form(
    form_id: str,
    form_data: FormUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    """Update a form."""
    repo = FormRepository(session)
    form = await repo.update_form(form_id, form_data.model_dump(exclude_unset=True))

    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Form with ID {form_id} not found",
        )

    return FormResponseSchema.model_validate(form)


@router.delete("/{form_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_form(
    form_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Delete a form."""
    repo = FormRepository(session)
    success = await repo.delete_form(form_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Form with ID {form_id} not found",
        )


# Form Responses


@router.post(
    "/{form_id}/responses",
    response_model=FormResponseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_form_response(
    form_id: str,
    response_data: FormResponseCreate,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Submit a response to a form.

    For single-response forms, checks if user already responded.
    If yes, updates existing response instead of creating new one.
    """
    form_repo = FormRepository(session)
    response_repo = FormResponseRepository(session)

    # Verify form exists
    form = await form_repo.get_form(form_id)
    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Form with ID {form_id} not found",
        )

    # Check if user already has a response (single response model)
    existing_response = await response_repo.get_response_by_user_and_form(
        form_id, response_data.responded_by
    )

    if existing_response:
        # Update existing response
        updated_response = await response_repo.update_response(
            existing_response.id,
            response_data.model_dump(),
            changed_by=response_data.responded_by,
            changed_by_type=response_data.responded_by_type,
        )
        return FormResponseResponse.model_validate(updated_response)
    else:
        # Create new response
        response = await response_repo.create_response(
            {**response_data.model_dump(), "form_id": form_id}
        )
        return FormResponseResponse.model_validate(response)


@router.get("/{form_id}/responses", response_model=list[FormResponseResponse])
async def get_form_responses(
    form_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Get all responses for a form."""
    form_repo = FormRepository(session)
    response_repo = FormResponseRepository(session)

    # Verify form exists
    form = await form_repo.get_form(form_id)
    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Form with ID {form_id} not found",
        )

    responses = await response_repo.get_responses_by_form(form_id)
    return [FormResponseResponse.model_validate(r) for r in responses]


@router.get("/responses/{response_id}", response_model=FormResponseResponse)
async def get_response(
    response_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Get a specific form response."""
    repo = FormResponseRepository(session)
    response = await repo.get_response(response_id)

    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Response with ID {response_id} not found",
        )

    return FormResponseResponse.model_validate(response)


@router.put("/responses/{response_id}", response_model=FormResponseResponse)
async def update_response(
    response_id: str,
    response_data: FormResponseUpdate,
    changed_by: str = "user",  # TODO: Get from auth
    session: AsyncSession = Depends(get_db_session),
):
    """Update a form response."""
    repo = FormResponseRepository(session)
    response = await repo.update_response(
        response_id, response_data.model_dump(exclude_unset=True), changed_by=changed_by
    )

    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Response with ID {response_id} not found",
        )

    return FormResponseResponse.model_validate(response)


# Issue/Document/Project specific endpoints


@router.get("/issues/{issue_id}/forms", response_model=list[FormResponseSchema])
async def get_issue_forms(
    issue_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Get all forms attached to an issue."""
    repo = FormRepository(session)
    forms = await repo.get_forms_by_issue(issue_id)
    return [FormResponseSchema.model_validate(f) for f in forms]


@router.get("/documents/{document_id}/forms", response_model=list[FormResponseSchema])
async def get_document_forms(
    document_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Get all forms attached to a document."""
    repo = FormRepository(session)
    forms = await repo.get_forms_by_document(document_id)
    return [FormResponseSchema.model_validate(f) for f in forms]


@router.get("/projects/{project_id}/forms", response_model=list[FormResponseSchema])
async def get_project_forms(
    project_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Get all forms attached to a project."""
    repo = FormRepository(session)
    forms = await repo.get_forms_by_project(project_id)
    return [FormResponseSchema.model_validate(f) for f in forms]

"""JobApplication API endpoints for career management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from turbo.api.dependencies import get_job_application_service
from turbo.core.schemas.job_application import (
    JobApplicationCreate,
    JobApplicationResponse,
    JobApplicationUpdate,
)
from turbo.core.services.job_application import JobApplicationService
from turbo.utils.exceptions import (
    JobApplicationNotFoundError,
    ValidationError as TurboValidationError,
)

router = APIRouter()


@router.post("/", response_model=JobApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_job_application(
    application_data: JobApplicationCreate,
    application_service: JobApplicationService = Depends(get_job_application_service),
) -> JobApplicationResponse:
    """Create a new job application."""
    try:
        return await application_service.create_job_application(application_data)
    except TurboValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.get("/{application_id}", response_model=JobApplicationResponse)
async def get_job_application(
    application_id: UUID,
    application_service: JobApplicationService = Depends(get_job_application_service),
) -> JobApplicationResponse:
    """Get a job application by ID."""
    try:
        return await application_service.get_job_application_by_id(application_id)
    except JobApplicationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job application with id {application_id} not found",
        )


@router.get("/", response_model=list[JobApplicationResponse])
async def get_job_applications(
    status_filter: str | None = Query(None, alias="status"),
    company_id: UUID | None = Query(None),
    active_only: bool | None = Query(False, description="Filter for active applications only"),
    limit: int | None = Query(None, ge=1, le=100),
    offset: int | None = Query(None, ge=0),
    application_service: JobApplicationService = Depends(get_job_application_service),
) -> list[JobApplicationResponse]:
    """Get all job applications with optional filtering."""
    if active_only:
        return await application_service.get_active_applications()
    elif company_id:
        return await application_service.get_applications_by_company(company_id)
    elif status_filter:
        return await application_service.get_applications_by_status(status_filter)
    else:
        return await application_service.get_all_job_applications(
            limit=limit, offset=offset
        )


@router.get("/followups/pending", response_model=list[JobApplicationResponse])
async def get_applications_needing_followup(
    application_service: JobApplicationService = Depends(get_job_application_service),
) -> list[JobApplicationResponse]:
    """Get applications with upcoming or overdue follow-ups."""
    return await application_service.get_applications_needing_followup()


@router.put("/{application_id}", response_model=JobApplicationResponse)
async def update_job_application(
    application_id: UUID,
    application_data: JobApplicationUpdate,
    application_service: JobApplicationService = Depends(get_job_application_service),
) -> JobApplicationResponse:
    """Update a job application."""
    try:
        return await application_service.update_job_application(
            application_id, application_data
        )
    except JobApplicationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job application with id {application_id} not found",
        )
    except TurboValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_application(
    application_id: UUID,
    application_service: JobApplicationService = Depends(get_job_application_service),
) -> None:
    """Delete a job application."""
    try:
        await application_service.delete_job_application(application_id)
    except JobApplicationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job application with id {application_id} not found",
        )

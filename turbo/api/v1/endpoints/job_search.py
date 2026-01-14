"""API endpoints for job search functionality."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.api.dependencies import get_db_session
from turbo.core.repositories.job_posting import (
    JobPostingRepository,
    SearchCriteriaRepository,
    JobSearchHistoryRepository,
)
from turbo.core.schemas.job_posting import (
    JobPostingResponse,
    JobPostingUpdate,
    SearchCriteriaCreate,
    SearchCriteriaResponse,
    SearchCriteriaUpdate,
    JobSearchHistoryResponse,
)
from turbo.core.services.job_search import JobSearchService

router = APIRouter(prefix="/job-search", tags=["job-search"])


def get_job_search_service(session: AsyncSession = Depends(get_db_session)) -> JobSearchService:
    """Dependency for job search service."""
    job_posting_repo = JobPostingRepository(session)
    criteria_repo = SearchCriteriaRepository(session)
    history_repo = JobSearchHistoryRepository(session)
    return JobSearchService(job_posting_repo, criteria_repo, history_repo)


# ====================================================================================
# Search Criteria Endpoints
# ====================================================================================

@router.post("/criteria", response_model=SearchCriteriaResponse)
async def create_search_criteria(
    data: SearchCriteriaCreate,
    service: JobSearchService = Depends(get_job_search_service),
):
    """Create new job search criteria."""
    return await service.create_search_criteria(data)


@router.get("/criteria", response_model=list[SearchCriteriaResponse])
async def list_search_criteria(
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: JobSearchService = Depends(get_job_search_service),
):
    """List all search criteria with optional filters."""
    return await service.list_search_criteria(is_active=is_active, limit=limit, offset=offset)


@router.get("/criteria/{criteria_id}", response_model=SearchCriteriaResponse)
async def get_search_criteria(
    criteria_id: UUID,
    service: JobSearchService = Depends(get_job_search_service),
):
    """Get search criteria by ID."""
    return await service.get_search_criteria(criteria_id)


@router.put("/criteria/{criteria_id}", response_model=SearchCriteriaResponse)
async def update_search_criteria(
    criteria_id: UUID,
    data: SearchCriteriaUpdate,
    service: JobSearchService = Depends(get_job_search_service),
):
    """Update search criteria."""
    return await service.update_search_criteria(criteria_id, data)


@router.delete("/criteria/{criteria_id}")
async def delete_search_criteria(
    criteria_id: UUID,
    service: JobSearchService = Depends(get_job_search_service),
):
    """Delete search criteria."""
    success = await service.delete_search_criteria(criteria_id)
    return {"success": success}


# ====================================================================================
# Job Search Execution
# ====================================================================================

@router.post("/execute/{criteria_id}", response_model=JobSearchHistoryResponse)
async def execute_job_search(
    criteria_id: UUID,
    sources: Optional[list[str]] = Query(None),
    service: JobSearchService = Depends(get_job_search_service),
):
    """Execute a job search based on criteria."""
    return await service.execute_search(criteria_id, sources=sources)


@router.get("/history", response_model=list[JobSearchHistoryResponse])
async def get_search_history(
    criteria_id: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    service: JobSearchService = Depends(get_job_search_service),
):
    """Get job search history."""
    return await service.get_search_history(criteria_id=criteria_id, limit=limit)


# ====================================================================================
# Job Postings Endpoints
# ====================================================================================

@router.get("/postings", response_model=list[JobPostingResponse])
async def list_job_postings(
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: JobSearchService = Depends(get_job_search_service),
):
    """List job postings with optional filters."""
    return await service.list_job_postings(
        status=status,
        source=source,
        min_score=min_score,
        limit=limit,
        offset=offset,
    )


@router.get("/postings/{posting_id}", response_model=JobPostingResponse)
async def get_job_posting(
    posting_id: UUID,
    service: JobSearchService = Depends(get_job_search_service),
):
    """Get job posting by ID."""
    return await service.get_job_posting(posting_id)


@router.put("/postings/{posting_id}", response_model=JobPostingResponse)
async def update_job_posting(
    posting_id: UUID,
    data: JobPostingUpdate,
    service: JobSearchService = Depends(get_job_search_service),
):
    """Update a job posting (e.g., mark as interested)."""
    return await service.update_job_posting(posting_id, data)


@router.delete("/postings/{posting_id}")
async def delete_job_posting(
    posting_id: UUID,
    service: JobSearchService = Depends(get_job_search_service),
):
    """Delete a job posting."""
    success = await service.delete_job_posting(posting_id)
    return {"success": success}

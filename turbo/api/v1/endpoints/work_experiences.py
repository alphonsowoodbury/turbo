"""Work experience API endpoints for career management."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from turbo.api.dependencies import get_db_session
from turbo.core.repositories.company import CompanyRepository
from turbo.core.repositories.work_experience import WorkExperienceRepository, AchievementFactRepository
from turbo.core.schemas.work_experience import (
    WorkExperienceCreate,
    WorkExperienceUpdate,
    WorkExperiencePublic,
    WorkExperienceWithCompany,
    WorkExperienceQuery,
    AchievementFactCreate,
    AchievementFactUpdate,
    AchievementFactPublic,
    AchievementFactQuery,
)
from turbo.core.services.work_experience import WorkExperienceService, AchievementFactService
from turbo.utils.exceptions import TurboBaseException, ValidationError as TurboValidationError

router = APIRouter()


# Dependency to get work experience service
async def get_work_experience_service(
    session=Depends(get_db_session),
):
    """Get work experience service with dependencies."""
    work_exp_repo = WorkExperienceRepository(session)
    achievement_repo = AchievementFactRepository(session)
    company_repo = CompanyRepository(session)
    return WorkExperienceService(work_exp_repo, achievement_repo, company_repo)


# Dependency to get achievement fact service
async def get_achievement_service(
    session=Depends(get_db_session),
):
    """Get achievement fact service with dependencies."""
    achievement_repo = AchievementFactRepository(session)
    work_exp_repo = WorkExperienceRepository(session)
    return AchievementFactService(achievement_repo, work_exp_repo)


# ============================================================================
# Work Experience Endpoints
# ============================================================================

@router.post("/", response_model=WorkExperiencePublic, status_code=status.HTTP_201_CREATED)
async def create_work_experience(
    data: WorkExperienceCreate,
    service: WorkExperienceService = Depends(get_work_experience_service),
) -> WorkExperiencePublic:
    """Create a new work experience."""
    try:
        return await service.create_work_experience(data)
    except TurboBaseException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TurboValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/{experience_id}", response_model=WorkExperienceWithCompany)
async def get_work_experience(
    experience_id: UUID,
    service: WorkExperienceService = Depends(get_work_experience_service),
) -> WorkExperienceWithCompany:
    """Get a work experience by ID with company details."""
    try:
        return await service.get_work_experience_with_company(experience_id)
    except TurboBaseException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work experience with id {experience_id} not found",
        )


@router.get("/", response_model=List[WorkExperiencePublic])
async def list_work_experiences(
    company_id: UUID | None = Query(None, description="Filter by company"),
    is_current: bool | None = Query(None, description="Filter by current employment"),
    employment_type: str | None = Query(None, description="Filter by employment type"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    service: WorkExperienceService = Depends(get_work_experience_service),
) -> List[WorkExperiencePublic]:
    """List all work experiences with optional filtering."""
    query = WorkExperienceQuery(
        company_id=company_id,
        is_current=is_current,
        employment_type=employment_type,
        limit=limit,
        offset=offset
    )
    return await service.list_work_experiences(query)


@router.put("/{experience_id}", response_model=WorkExperiencePublic)
async def update_work_experience(
    experience_id: UUID,
    data: WorkExperienceUpdate,
    service: WorkExperienceService = Depends(get_work_experience_service),
) -> WorkExperiencePublic:
    """Update a work experience."""
    try:
        return await service.update_work_experience(experience_id, data)
    except TurboBaseException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work experience with id {experience_id} not found",
        )
    except TurboValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete("/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_experience(
    experience_id: UUID,
    service: WorkExperienceService = Depends(get_work_experience_service),
) -> None:
    """Delete a work experience."""
    try:
        await service.delete_work_experience(experience_id)
    except TurboBaseException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work experience with id {experience_id} not found",
        )


# ============================================================================
# Achievement Fact Endpoints
# ============================================================================

@router.post("/achievements/", response_model=AchievementFactPublic, status_code=status.HTTP_201_CREATED)
async def create_achievement(
    data: AchievementFactCreate,
    service: AchievementFactService = Depends(get_achievement_service),
) -> AchievementFactPublic:
    """Create a new achievement fact."""
    try:
        return await service.create_achievement(data)
    except TurboBaseException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TurboValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/achievements/{achievement_id}", response_model=AchievementFactPublic)
async def get_achievement(
    achievement_id: UUID,
    service: AchievementFactService = Depends(get_achievement_service),
) -> AchievementFactPublic:
    """Get an achievement fact by ID."""
    try:
        return await service.get_achievement(achievement_id)
    except TurboBaseException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Achievement with id {achievement_id} not found",
        )


@router.get("/achievements/", response_model=List[AchievementFactPublic])
async def list_achievements(
    experience_id: UUID | None = Query(None, description="Filter by work experience"),
    metric_type: str | None = Query(None, description="Filter by metric type"),
    dimensions: List[str] | None = Query(None, description="Filter by dimensions (must contain all)"),
    leadership_principles: List[str] | None = Query(None, description="Filter by leadership principles"),
    skills_used: List[str] | None = Query(None, description="Filter by skills used"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    service: AchievementFactService = Depends(get_achievement_service),
) -> List[AchievementFactPublic]:
    """List all achievement facts with optional filtering."""
    query = AchievementFactQuery(
        experience_id=experience_id,
        metric_type=metric_type,
        dimensions=dimensions,
        leadership_principles=leadership_principles,
        skills_used=skills_used,
        limit=limit,
        offset=offset
    )
    return await service.list_achievements(query)


@router.get("/achievements/search/", response_model=List[AchievementFactPublic])
async def search_achievements(
    q: str = Query(..., min_length=1, description="Search query text"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    service: AchievementFactService = Depends(get_achievement_service),
) -> List[AchievementFactPublic]:
    """Search achievement facts by text."""
    return await service.search_achievements(q, limit=limit)


@router.put("/achievements/{achievement_id}", response_model=AchievementFactPublic)
async def update_achievement(
    achievement_id: UUID,
    data: AchievementFactUpdate,
    service: AchievementFactService = Depends(get_achievement_service),
) -> AchievementFactPublic:
    """Update an achievement fact."""
    try:
        return await service.update_achievement(achievement_id, data)
    except TurboBaseException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Achievement with id {achievement_id} not found",
        )
    except TurboValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete("/achievements/{achievement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_achievement(
    achievement_id: UUID,
    service: AchievementFactService = Depends(get_achievement_service),
) -> None:
    """Delete an achievement fact."""
    try:
        await service.delete_achievement(achievement_id)
    except TurboBaseException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Achievement with id {achievement_id} not found",
        )

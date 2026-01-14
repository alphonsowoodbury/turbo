"""Skill API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.api.dependencies import get_db_session
from turbo.core.repositories.skill import SkillRepository
from turbo.core.schemas.skill import (
    SkillCreate,
    SkillResponse,
    SkillSummary,
    SkillUpdate,
)

router = APIRouter()


def get_skill_repo(
    session: AsyncSession = Depends(get_db_session),
) -> SkillRepository:
    """Get skill repository dependency."""
    return SkillRepository(session)


@router.post("/", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillCreate,
    repo: SkillRepository = Depends(get_skill_repo),
) -> SkillResponse:
    """Create a new skill."""
    skill = await repo.create(skill_data)
    return SkillResponse.model_validate(skill)


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: UUID,
    repo: SkillRepository = Depends(get_skill_repo),
) -> SkillResponse:
    """Get a skill by ID."""
    skill = await repo.get_by_id(skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with id {skill_id} not found",
        )
    return SkillResponse.model_validate(skill)


@router.get("/", response_model=list[SkillResponse])
async def get_skills(
    category: str | None = Query(None),
    proficiency_level: str | None = Query(None),
    is_endorsed: bool | None = Query(None),
    limit: int | None = Query(100, ge=1, le=500),
    offset: int | None = Query(0, ge=0),
    repo: SkillRepository = Depends(get_skill_repo),
) -> list[SkillResponse]:
    """Get all skills with optional filtering."""
    # Get by category
    if category:
        skills = await repo.get_by_category(
            category=category,
            limit=limit,
            offset=offset,
        )
    # Get by proficiency level
    elif proficiency_level:
        skills = await repo.get_by_proficiency(
            proficiency_level=proficiency_level,
            limit=limit,
            offset=offset,
        )
    # Get endorsed skills
    elif is_endorsed is not None and is_endorsed:
        skills = await repo.get_endorsed(limit=limit, offset=offset)
    # Get all
    else:
        skills = await repo.get_all(limit=limit, offset=offset)

    return [SkillResponse.model_validate(skill) for skill in skills]


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: UUID,
    skill_data: SkillUpdate,
    repo: SkillRepository = Depends(get_skill_repo),
) -> SkillResponse:
    """Update a skill."""
    skill = await repo.update(skill_id, skill_data)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with id {skill_id} not found",
        )
    return SkillResponse.model_validate(skill)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: UUID,
    repo: SkillRepository = Depends(get_skill_repo),
) -> None:
    """Delete a skill."""
    success = await repo.delete(skill_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with id {skill_id} not found",
        )


@router.get("/recent/", response_model=list[SkillResponse])
async def get_recent_skills(
    limit: int | None = Query(10, ge=1, le=100),
    repo: SkillRepository = Depends(get_skill_repo),
) -> list[SkillResponse]:
    """Get recently used skills."""
    skills = await repo.get_recent(limit=limit)
    return [SkillResponse.model_validate(skill) for skill in skills]


@router.get("/search/", response_model=list[SkillResponse])
async def search_skills(
    q: str = Query(..., min_length=1),
    repo: SkillRepository = Depends(get_skill_repo),
) -> list[SkillResponse]:
    """Search skills by name."""
    skills = await repo.search_by_name(q)
    return [SkillResponse.model_validate(skill) for skill in skills]

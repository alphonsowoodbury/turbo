"""Blueprint API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.database.connection import get_db_session
from turbo.core.models import Blueprint
from turbo.core.schemas.blueprint import (
    BlueprintCreate,
    BlueprintResponse,
    BlueprintSummary,
    BlueprintUpdate,
)

router = APIRouter()


@router.post("/", response_model=BlueprintResponse, status_code=status.HTTP_201_CREATED)
async def create_blueprint(
    blueprint_data: BlueprintCreate, db: AsyncSession = Depends(get_db_session)
) -> BlueprintResponse:
    """Create a new blueprint."""
    # Check if blueprint with same name and version already exists
    result = await db.execute(
        select(Blueprint).where(
            Blueprint.name == blueprint_data.name,
            Blueprint.version == blueprint_data.version
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Blueprint '{blueprint_data.name}' version '{blueprint_data.version}' already exists",
        )

    blueprint = Blueprint(
        name=blueprint_data.name,
        description=blueprint_data.description,
        category=blueprint_data.category,
        content=blueprint_data.content,
        version=blueprint_data.version,
        is_active=blueprint_data.is_active,
    )
    db.add(blueprint)
    await db.commit()
    await db.refresh(blueprint)
    return BlueprintResponse.model_validate(blueprint)


@router.get("/", response_model=list[BlueprintSummary])
async def list_blueprints(
    category: str | None = Query(None, description="Filter by category"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db_session),
) -> list[BlueprintSummary]:
    """Get all blueprints with optional filters."""
    query = select(Blueprint)

    if category:
        query = query.where(Blueprint.category == category)
    if is_active is not None:
        query = query.where(Blueprint.is_active == is_active)

    query = query.order_by(Blueprint.category, Blueprint.name)

    result = await db.execute(query)
    blueprints = result.scalars().all()
    return [BlueprintSummary.model_validate(blueprint) for blueprint in blueprints]


@router.get("/by-name/{blueprint_name}/versions", response_model=list[BlueprintSummary])
async def get_blueprint_versions(
    blueprint_name: str, db: AsyncSession = Depends(get_db_session)
) -> list[BlueprintSummary]:
    """Get all versions of a blueprint by name."""
    result = await db.execute(
        select(Blueprint)
        .where(Blueprint.name == blueprint_name)
        .order_by(Blueprint.version.desc())
    )
    blueprints = result.scalars().all()
    return [BlueprintSummary.model_validate(bp) for bp in blueprints]


@router.get("/{blueprint_id}", response_model=BlueprintResponse)
async def get_blueprint(
    blueprint_id: UUID, db: AsyncSession = Depends(get_db_session)
) -> BlueprintResponse:
    """Get a blueprint by ID."""
    result = await db.execute(select(Blueprint).where(Blueprint.id == blueprint_id))
    blueprint = result.scalar_one_or_none()

    if not blueprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blueprint with id {blueprint_id} not found",
        )

    return BlueprintResponse.model_validate(blueprint)


@router.put("/{blueprint_id}", response_model=BlueprintResponse)
async def update_blueprint(
    blueprint_id: UUID,
    blueprint_data: BlueprintUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> BlueprintResponse:
    """Update a blueprint."""
    result = await db.execute(select(Blueprint).where(Blueprint.id == blueprint_id))
    blueprint = result.scalar_one_or_none()

    if not blueprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blueprint with id {blueprint_id} not found",
        )

    # Check for name conflict if name is being updated
    if blueprint_data.name and blueprint_data.name != blueprint.name:
        name_check = await db.execute(
            select(Blueprint).where(Blueprint.name == blueprint_data.name)
        )
        existing = name_check.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Blueprint with name '{blueprint_data.name}' already exists",
            )

    # Update fields
    if blueprint_data.name is not None:
        blueprint.name = blueprint_data.name
    if blueprint_data.description is not None:
        blueprint.description = blueprint_data.description
    if blueprint_data.category is not None:
        blueprint.category = blueprint_data.category
    if blueprint_data.content is not None:
        blueprint.content = blueprint_data.content
    if blueprint_data.version is not None:
        blueprint.version = blueprint_data.version
    if blueprint_data.is_active is not None:
        blueprint.is_active = blueprint_data.is_active

    await db.commit()
    await db.refresh(blueprint)
    return BlueprintResponse.model_validate(blueprint)


@router.delete("/{blueprint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blueprint(
    blueprint_id: UUID, db: AsyncSession = Depends(get_db_session)
) -> None:
    """Delete a blueprint."""
    result = await db.execute(select(Blueprint).where(Blueprint.id == blueprint_id))
    blueprint = result.scalar_one_or_none()

    if not blueprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blueprint with id {blueprint_id} not found",
        )

    await db.delete(blueprint)
    await db.commit()

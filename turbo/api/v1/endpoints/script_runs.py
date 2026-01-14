"""Script Runs API endpoints."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.api.dependencies import get_db_session
from turbo.core.models.script_run import ScriptRun, ScriptRunStatus
from turbo.core.schemas.script_run import (
    ScriptRunCreate,
    ScriptRunResponse,
    ScriptRunUpdate,
)

router = APIRouter()


@router.post("/", response_model=ScriptRunResponse, status_code=status.HTTP_201_CREATED)
async def create_script_run(
    script_run_data: ScriptRunCreate,
    db: AsyncSession = Depends(get_db_session),
) -> ScriptRunResponse:
    """Create a new script run."""
    # Create new script run
    script_run = ScriptRun(
        script_name=script_run_data.script_name,
        script_path=script_run_data.script_path,
        command=script_run_data.command,
        arguments=script_run_data.arguments,
        triggered_by=script_run_data.triggered_by,
        status=ScriptRunStatus.RUNNING,
    )

    db.add(script_run)
    await db.commit()
    await db.refresh(script_run)

    return ScriptRunResponse.model_validate(script_run)


@router.get("/", response_model=list[ScriptRunResponse])
async def list_script_runs(
    script_name: str | None = Query(None, description="Filter by script name"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db_session),
) -> list[ScriptRunResponse]:
    """List script runs with optional filtering."""
    query = select(ScriptRun)

    # Apply filters
    if script_name:
        query = query.where(ScriptRun.script_name == script_name)
    if status:
        query = query.where(ScriptRun.status == status)

    # Order by most recent first
    query = query.order_by(desc(ScriptRun.started_at))

    # Apply pagination
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    script_runs = result.scalars().all()

    return [ScriptRunResponse.model_validate(sr) for sr in script_runs]


@router.get("/{script_run_id}", response_model=ScriptRunResponse)
async def get_script_run(
    script_run_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> ScriptRunResponse:
    """Get a script run by ID."""
    result = await db.execute(select(ScriptRun).where(ScriptRun.id == str(script_run_id)))
    script_run = result.scalar_one_or_none()

    if not script_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Script run {script_run_id} not found",
        )

    return ScriptRunResponse.model_validate(script_run)


@router.patch("/{script_run_id}", response_model=ScriptRunResponse)
async def update_script_run(
    script_run_id: UUID,
    update_data: ScriptRunUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> ScriptRunResponse:
    """Update a script run."""
    result = await db.execute(select(ScriptRun).where(ScriptRun.id == str(script_run_id)))
    script_run = result.scalar_one_or_none()

    if not script_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Script run {script_run_id} not found",
        )

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if field == "status" and value:
            setattr(script_run, field, ScriptRunStatus(value))
        else:
            setattr(script_run, field, value)

    # Set completed_at if status is completed/failed/cancelled
    if update_data.status in ["completed", "failed", "cancelled"] and not script_run.completed_at:
        script_run.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(script_run)

    return ScriptRunResponse.model_validate(script_run)


@router.delete("/{script_run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_script_run(
    script_run_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a script run."""
    result = await db.execute(select(ScriptRun).where(ScriptRun.id == str(script_run_id)))
    script_run = result.scalar_one_or_none()

    if not script_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Script run {script_run_id} not found",
        )

    await db.delete(script_run)
    await db.commit()

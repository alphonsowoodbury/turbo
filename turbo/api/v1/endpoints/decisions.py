"""Decision API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from turbo.core.repositories.decision import DecisionRepository
from turbo.core.schemas.decision import (
    DecisionApprove,
    DecisionCreate,
    DecisionList,
    DecisionResponse,
    DecisionUpdate,
)
from turbo.api.dependencies import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def get_decision_repo(
    session: AsyncSession = Depends(get_db_session),
) -> DecisionRepository:
    """Get decision repository."""
    return DecisionRepository(session)


@router.post("/", response_model=DecisionResponse, status_code=status.HTTP_201_CREATED)
async def create_decision(
    decision_data: DecisionCreate,
    repo: DecisionRepository = Depends(get_decision_repo),
) -> DecisionResponse:
    """Create a new decision."""
    # Generate key if not provided
    if not decision_data.decision_key:
        next_num = await repo.get_next_key_number()
        decision_data.decision_key = f"DEC-{next_num}"

    decision = await repo.create(decision_data)

    return DecisionResponse(
        id=decision.id,
        decision_key=decision.decision_key,
        title=decision.title,
        summary=decision.summary,
        rationale=decision.rationale,
        context=decision.context,
        constraints=decision.constraints,
        options_considered=decision.options_considered,
        decision_type=decision.decision_type,
        status=decision.status,
        impact_areas=decision.impact_areas,
        decided_by=decision.decided_by,
        decided_at=decision.decided_at,
        superseded_at=decision.superseded_at,
        superseded_by_id=decision.superseded_by_id,
        created_at=decision.created_at,
        updated_at=decision.updated_at,
        initiative_count=len(decision.initiatives) if decision.initiatives else 0,
    )


@router.get("/", response_model=DecisionList)
async def list_decisions(
    status_filter: str | None = Query(None, alias="status"),
    decision_type: str | None = Query(None, alias="type"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str | None = Query(None),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    repo: DecisionRepository = Depends(get_decision_repo),
) -> DecisionList:
    """List all decisions with optional filtering."""
    offset = (page - 1) * per_page

    if status_filter:
        decisions = await repo.get_by_status(
            status_filter, sort_by=sort_by, sort_order=sort_order
        )
    elif decision_type:
        decisions = await repo.get_by_type(
            decision_type, sort_by=sort_by, sort_order=sort_order
        )
    else:
        decisions = await repo.get_all_with_relations(
            limit=per_page, offset=offset, sort_by=sort_by, sort_order=sort_order
        )

    total = await repo.count()

    items = [
        DecisionResponse(
            id=d.id,
            decision_key=d.decision_key,
            title=d.title,
            summary=d.summary,
            rationale=d.rationale,
            context=d.context,
            constraints=d.constraints,
            options_considered=d.options_considered,
            decision_type=d.decision_type,
            status=d.status,
            impact_areas=d.impact_areas,
            decided_by=d.decided_by,
            decided_at=d.decided_at,
            superseded_at=d.superseded_at,
            superseded_by_id=d.superseded_by_id,
            created_at=d.created_at,
            updated_at=d.updated_at,
            initiative_count=len(d.initiatives) if d.initiatives else 0,
        )
        for d in decisions
    ]

    return DecisionList(items=items, total=total, page=page, per_page=per_page)


@router.get("/{decision_id}", response_model=DecisionResponse)
async def get_decision(
    decision_id: UUID,
    repo: DecisionRepository = Depends(get_decision_repo),
) -> DecisionResponse:
    """Get a decision by ID."""
    decision = await repo.get_with_initiatives(decision_id)

    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision {decision_id} not found",
        )

    return DecisionResponse(
        id=decision.id,
        decision_key=decision.decision_key,
        title=decision.title,
        summary=decision.summary,
        rationale=decision.rationale,
        context=decision.context,
        constraints=decision.constraints,
        options_considered=decision.options_considered,
        decision_type=decision.decision_type,
        status=decision.status,
        impact_areas=decision.impact_areas,
        decided_by=decision.decided_by,
        decided_at=decision.decided_at,
        superseded_at=decision.superseded_at,
        superseded_by_id=decision.superseded_by_id,
        created_at=decision.created_at,
        updated_at=decision.updated_at,
        initiative_count=len(decision.initiatives) if decision.initiatives else 0,
    )


@router.patch("/{decision_id}", response_model=DecisionResponse)
async def update_decision(
    decision_id: UUID,
    update_data: DecisionUpdate,
    repo: DecisionRepository = Depends(get_decision_repo),
) -> DecisionResponse:
    """Update a decision."""
    decision = await repo.update(decision_id, update_data)

    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision {decision_id} not found",
        )

    return DecisionResponse(
        id=decision.id,
        decision_key=decision.decision_key,
        title=decision.title,
        summary=decision.summary,
        rationale=decision.rationale,
        context=decision.context,
        constraints=decision.constraints,
        options_considered=decision.options_considered,
        decision_type=decision.decision_type,
        status=decision.status,
        impact_areas=decision.impact_areas,
        decided_by=decision.decided_by,
        decided_at=decision.decided_at,
        superseded_at=decision.superseded_at,
        superseded_by_id=decision.superseded_by_id,
        created_at=decision.created_at,
        updated_at=decision.updated_at,
        initiative_count=len(decision.initiatives) if decision.initiatives else 0,
    )


@router.post("/{decision_id}/approve", response_model=DecisionResponse)
async def approve_decision(
    decision_id: UUID,
    approval: DecisionApprove | None = None,
    repo: DecisionRepository = Depends(get_decision_repo),
) -> DecisionResponse:
    """Approve a decision."""
    decided_by = approval.decided_by if approval else None
    decision = await repo.approve(decision_id, decided_by)

    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision {decision_id} not found",
        )

    return DecisionResponse(
        id=decision.id,
        decision_key=decision.decision_key,
        title=decision.title,
        summary=decision.summary,
        rationale=decision.rationale,
        context=decision.context,
        constraints=decision.constraints,
        options_considered=decision.options_considered,
        decision_type=decision.decision_type,
        status=decision.status,
        impact_areas=decision.impact_areas,
        decided_by=decision.decided_by,
        decided_at=decision.decided_at,
        superseded_at=decision.superseded_at,
        superseded_by_id=decision.superseded_by_id,
        created_at=decision.created_at,
        updated_at=decision.updated_at,
        initiative_count=len(decision.initiatives) if decision.initiatives else 0,
    )


@router.delete("/{decision_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_decision(
    decision_id: UUID,
    repo: DecisionRepository = Depends(get_decision_repo),
) -> None:
    """Delete a decision."""
    success = await repo.delete(decision_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision {decision_id} not found",
        )

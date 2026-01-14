"""API endpoints for issue dependencies."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.api.dependencies import get_db_session
from turbo.core.repositories.issue_dependency import IssueDependencyRepository
from turbo.core.schemas.issue_dependency import (
    DependencyChain,
    IssueDependencies,
    IssueDependencyCreate,
    IssueDependencyResponse,
)

router = APIRouter(prefix="/dependencies", tags=["dependencies"])


@router.post("/", response_model=IssueDependencyResponse, status_code=status.HTTP_201_CREATED)
async def create_dependency(
    dependency: IssueDependencyCreate,
    session: AsyncSession = Depends(get_db_session),
) -> IssueDependencyResponse:
    """Create a new issue dependency.

    Creates a blocking relationship between two issues.
    Validates that the dependency won't create a circular reference.

    Args:
        dependency: Dependency details
        session: Database session

    Returns:
        Created dependency

    Raises:
        HTTPException: If dependency would create a cycle
    """
    repo = IssueDependencyRepository(session)

    try:
        created = await repo.create_dependency(
            blocking_issue_id=dependency.blocking_issue_id,
            blocked_issue_id=dependency.blocked_issue_id,
            dependency_type=dependency.dependency_type,
        )
        await session.commit()
        return IssueDependencyResponse.model_validate(created)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.delete("/{blocking_issue_id}/{blocked_issue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dependency(
    blocking_issue_id: UUID,
    blocked_issue_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete an issue dependency.

    Args:
        blocking_issue_id: ID of the blocking issue
        blocked_issue_id: ID of the blocked issue
        session: Database session

    Raises:
        HTTPException: If dependency not found
    """
    repo = IssueDependencyRepository(session)

    deleted = await repo.delete_dependency(blocking_issue_id, blocked_issue_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency not found",
        )

    await session.commit()


@router.get("/{issue_id}", response_model=IssueDependencies)
async def get_issue_dependencies(
    issue_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> IssueDependencies:
    """Get all dependencies for an issue.

    Returns both issues that block this issue and issues blocked by this issue.

    Args:
        issue_id: ID of the issue
        session: Database session

    Returns:
        Issue dependencies
    """
    repo = IssueDependencyRepository(session)
    deps = await repo.get_all_dependencies(issue_id)
    return IssueDependencies(**deps)


@router.get("/{issue_id}/chain", response_model=DependencyChain)
async def get_dependency_chain(
    issue_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> DependencyChain:
    """Get the full dependency chain for an issue.

    Returns all issues that must be completed before this issue can start,
    in topological order.

    Args:
        issue_id: ID of the issue
        session: Database session

    Returns:
        Dependency chain
    """
    repo = IssueDependencyRepository(session)
    chain = await repo.get_dependency_chain(issue_id)
    return DependencyChain(issue_id=issue_id, chain=chain)
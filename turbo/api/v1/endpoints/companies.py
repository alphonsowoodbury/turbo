"""Company API endpoints for career management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from turbo.api.dependencies import get_company_service
from turbo.core.schemas.company import (
    CompanyCreate,
    CompanyResponse,
    CompanyUpdate,
)
from turbo.core.services.company import CompanyService
from turbo.utils.exceptions import (
    CompanyNotFoundError,
    ValidationError as TurboValidationError,
)

router = APIRouter()


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    company_service: CompanyService = Depends(get_company_service),
) -> CompanyResponse:
    """Create a new company."""
    try:
        return await company_service.create_company(company_data)
    except TurboValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID, company_service: CompanyService = Depends(get_company_service)
) -> CompanyResponse:
    """Get a company by ID."""
    try:
        return await company_service.get_company_by_id(company_id)
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with id {company_id} not found",
        )


@router.get("/", response_model=list[CompanyResponse])
async def get_companies(
    target_status: str | None = Query(None),
    industry: str | None = Query(None),
    search: str | None = Query(None, description="Search by company name"),
    limit: int | None = Query(None, ge=1, le=100),
    offset: int | None = Query(None, ge=0),
    company_service: CompanyService = Depends(get_company_service),
) -> list[CompanyResponse]:
    """Get all companies with optional filtering."""
    if search:
        return await company_service.search_companies(search)
    elif target_status:
        return await company_service.get_companies_by_target_status(target_status)
    elif industry:
        return await company_service.get_companies_by_industry(industry)
    else:
        return await company_service.get_all_companies(limit=limit, offset=offset)


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: UUID,
    company_data: CompanyUpdate,
    company_service: CompanyService = Depends(get_company_service),
) -> CompanyResponse:
    """Update a company."""
    try:
        return await company_service.update_company(company_id, company_data)
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with id {company_id} not found",
        )
    except TurboValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: UUID, company_service: CompanyService = Depends(get_company_service)
) -> None:
    """Delete a company."""
    try:
        await company_service.delete_company(company_id)
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with id {company_id} not found",
        )

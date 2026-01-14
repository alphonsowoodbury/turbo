"""NetworkContact API endpoints for career management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from turbo.api.dependencies import get_network_contact_service
from turbo.core.schemas.network_contact import (
    NetworkContactCreate,
    NetworkContactResponse,
    NetworkContactUpdate,
)
from turbo.core.services.network_contact import NetworkContactService
from turbo.utils.exceptions import (
    NetworkContactNotFoundError,
    ValidationError as TurboValidationError,
)

router = APIRouter()


@router.post("/", response_model=NetworkContactResponse, status_code=status.HTTP_201_CREATED)
async def create_network_contact(
    contact_data: NetworkContactCreate,
    contact_service: NetworkContactService = Depends(get_network_contact_service),
) -> NetworkContactResponse:
    """Create a new network contact."""
    try:
        return await contact_service.create_network_contact(contact_data)
    except TurboValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.get("/{contact_id}", response_model=NetworkContactResponse)
async def get_network_contact(
    contact_id: UUID,
    contact_service: NetworkContactService = Depends(get_network_contact_service),
) -> NetworkContactResponse:
    """Get a network contact by ID."""
    try:
        return await contact_service.get_network_contact_by_id(contact_id)
    except NetworkContactNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Network contact with id {contact_id} not found",
        )


@router.get("/", response_model=list[NetworkContactResponse])
async def get_network_contacts(
    contact_type: str | None = Query(None),
    company_id: UUID | None = Query(None),
    warm_only: bool | None = Query(False, description="Filter for warm/hot contacts only"),
    search: str | None = Query(None, description="Search by name"),
    limit: int | None = Query(None, ge=1, le=100),
    offset: int | None = Query(None, ge=0),
    contact_service: NetworkContactService = Depends(get_network_contact_service),
) -> list[NetworkContactResponse]:
    """Get all network contacts with optional filtering."""
    if search:
        return await contact_service.search_contacts(search)
    elif warm_only:
        return await contact_service.get_warm_contacts()
    elif company_id:
        return await contact_service.get_contacts_by_company(company_id)
    elif contact_type:
        return await contact_service.get_contacts_by_type(contact_type)
    else:
        return await contact_service.get_all_network_contacts(limit=limit, offset=offset)


@router.get("/followups/pending", response_model=list[NetworkContactResponse])
async def get_contacts_needing_followup(
    contact_service: NetworkContactService = Depends(get_network_contact_service),
) -> list[NetworkContactResponse]:
    """Get contacts with upcoming or overdue follow-ups."""
    return await contact_service.get_contacts_needing_followup()


@router.put("/{contact_id}", response_model=NetworkContactResponse)
async def update_network_contact(
    contact_id: UUID,
    contact_data: NetworkContactUpdate,
    contact_service: NetworkContactService = Depends(get_network_contact_service),
) -> NetworkContactResponse:
    """Update a network contact."""
    try:
        return await contact_service.update_network_contact(contact_id, contact_data)
    except NetworkContactNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Network contact with id {contact_id} not found",
        )
    except TurboValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_network_contact(
    contact_id: UUID,
    contact_service: NetworkContactService = Depends(get_network_contact_service),
) -> None:
    """Delete a network contact."""
    try:
        await contact_service.delete_network_contact(contact_id)
    except NetworkContactNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Network contact with id {contact_id} not found",
        )

"""Email template API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from turbo.api.dependencies import get_email_template_service
from turbo.core.schemas.document import DocumentResponse
from turbo.core.services.email_template import EmailTemplateService
from turbo.utils.exceptions import DocumentNotFoundError, ValidationError

router = APIRouter()


class EmailTemplateCreate(BaseModel):
    """Request model for creating email templates."""
    project_id: UUID
    name: str
    content: str
    category: str
    variables: list[str] | None = None
    version: str = "1.0"


class EmailTemplateRender(BaseModel):
    """Request model for rendering templates."""
    variables: dict[str, str]


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_email_template(
    template_data: EmailTemplateCreate,
    template_service: EmailTemplateService = Depends(get_email_template_service),
) -> DocumentResponse:
    """Create a new email template."""
    try:
        return await template_service.create_template(
            project_id=template_data.project_id,
            name=template_data.name,
            content=template_data.content,
            category=template_data.category,
            variables=template_data.variables,
            version=template_data.version,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.get("/{template_id}", response_model=DocumentResponse)
async def get_email_template(
    template_id: UUID,
    template_service: EmailTemplateService = Depends(get_email_template_service),
) -> DocumentResponse:
    """Get an email template by ID."""
    try:
        return await template_service.get_template(template_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email template {template_id} not found",
        )


@router.get("/", response_model=list[DocumentResponse])
async def list_email_templates(
    project_id: UUID | None = Query(None),
    category: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    limit: int | None = Query(None, ge=1, le=100),
    offset: int | None = Query(None, ge=0),
    template_service: EmailTemplateService = Depends(get_email_template_service),
) -> list[DocumentResponse]:
    """List email templates with optional filtering."""
    return await template_service.list_templates(
        project_id=project_id,
        category=category,
        status=status_filter,
        limit=limit,
        offset=offset,
    )


@router.put("/{template_id}", response_model=DocumentResponse)
async def update_email_template(
    template_id: UUID,
    update_data: dict,
    template_service: EmailTemplateService = Depends(get_email_template_service),
) -> DocumentResponse:
    """Update an email template."""
    try:
        return await template_service.update_template(template_id, update_data)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email template {template_id} not found",
        )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_email_template(
    template_id: UUID,
    template_service: EmailTemplateService = Depends(get_email_template_service),
) -> None:
    """Delete an email template."""
    try:
        await template_service.delete_template(template_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email template {template_id} not found",
        )


@router.post("/{template_id}/render", response_model=dict)
async def render_email_template(
    template_id: UUID,
    render_data: EmailTemplateRender,
    template_service: EmailTemplateService = Depends(get_email_template_service),
) -> dict:
    """Render template with variable substitution."""
    try:
        content = await template_service.render_template(template_id, render_data.variables)
        return {"content": content}
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email template {template_id} not found",
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.post("/{template_id}/usage", status_code=status.HTTP_204_NO_CONTENT)
async def track_template_usage(
    template_id: UUID,
    template_service: EmailTemplateService = Depends(get_email_template_service),
) -> None:
    """Track template usage (increment counter)."""
    await template_service.track_usage(template_id)


@router.post("/{template_id}/response", status_code=status.HTTP_204_NO_CONTENT)
async def track_template_response(
    template_id: UUID,
    response_time_hours: float | None = None,
    template_service: EmailTemplateService = Depends(get_email_template_service),
) -> None:
    """Track response to email sent using this template."""
    await template_service.track_response(template_id, response_time_hours)


@router.post("/{template_id}/variants", response_model=dict)
async def create_ab_variant(
    template_id: UUID,
    variant_name: str,
    variant_content: str,
    template_service: EmailTemplateService = Depends(get_email_template_service),
) -> dict:
    """Create A/B test variant of a template."""
    try:
        variant_id = await template_service.create_ab_variant(
            template_id, variant_name, variant_content
        )
        return {"variant_id": str(variant_id)}
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email template {template_id} not found",
        )

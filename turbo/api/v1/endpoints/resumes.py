"""Resume API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.api.dependencies import get_db_session
from turbo.core.schemas.resume import (
    ResumeListResponse,
    ResumeResponse,
    ResumeSectionCreate,
    ResumeSectionResponse,
    ResumeSectionUpdate,
    ResumeUpdate,
    ResumeUploadResponse,
)
from turbo.core.services.resume import ResumeService
from turbo.core.services.resume_aggregator import ResumeAggregatorService
from turbo.core.services.resume_deduplicator import ResumeDeduplicatorService

# Optional knowledge graph import
try:
    from turbo.core.services.knowledge_graph import KnowledgeGraphService
except ImportError:
    KnowledgeGraphService = None  # type: ignore

router = APIRouter()


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse resume",
)
async def upload_resume(
    file: Annotated[UploadFile, File(description="Resume file (PDF or Markdown)")],
    title: Annotated[str, Form(description="Resume title")],
    target_role: Annotated[str | None, Form(description="Target job role")] = None,
    target_company: Annotated[
        str | None, Form(description="Target company")
    ] = None,
    use_ai_extraction: Annotated[
        bool, Form(description="Use AI for data extraction")
    ] = True,
    session: AsyncSession = Depends(get_db_session),
) -> ResumeUploadResponse:
    """Upload and parse a resume file.

    Accepts PDF or Markdown files. Automatically parses content and
    optionally uses AI to extract structured data.
    """
    service = ResumeService(session)

    return await service.upload_and_parse_resume(
        file=file.file,
        filename=file.filename or "resume",
        title=title,
        target_role=target_role,
        target_company=target_company,
        use_ai_extraction=use_ai_extraction,
        content_type=file.content_type,
    )


@router.get(
    "/",
    response_model=ResumeListResponse,
    summary="List all resumes",
)
async def list_resumes(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session),
) -> ResumeListResponse:
    """List all resumes with pagination."""
    service = ResumeService(session)
    resumes, total = await service.list_resumes(skip=skip, limit=limit)

    return ResumeListResponse(
        resumes=[ResumeResponse.model_validate(r) for r in resumes],
        total=total,
    )


@router.get(
    "/primary",
    response_model=ResumeResponse | None,
    summary="Get primary resume",
)
async def get_primary_resume(
    session: AsyncSession = Depends(get_db_session),
) -> ResumeResponse | None:
    """Get the primary resume."""
    service = ResumeService(session)
    resume = await service.get_primary_resume()

    if not resume:
        return None

    return ResumeResponse.model_validate(resume)


@router.get(
    "/by-role/{target_role}",
    response_model=list[ResumeResponse],
    summary="Get resumes by target role",
)
async def get_resumes_by_role(
    target_role: str,
    session: AsyncSession = Depends(get_db_session),
) -> list[ResumeResponse]:
    """Get resumes filtered by target job role."""
    service = ResumeService(session)
    resumes = await service.get_resumes_by_role(target_role)

    return [ResumeResponse.model_validate(r) for r in resumes]


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="Get resume by ID",
)
async def get_resume(
    resume_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ResumeResponse:
    """Get resume by ID with all sections."""
    service = ResumeService(session)
    resume = await service.get_resume(resume_id)

    return ResumeResponse.model_validate(resume)


@router.put(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="Update resume",
)
async def update_resume(
    resume_id: UUID,
    update_data: ResumeUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ResumeResponse:
    """Update resume details (partial update)."""
    service = ResumeService(session)
    resume = await service.update_resume(resume_id, update_data)

    return ResumeResponse.model_validate(resume)


@router.post(
    "/{resume_id}/set-primary",
    response_model=ResumeResponse,
    summary="Set as primary resume",
)
async def set_primary_resume(
    resume_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ResumeResponse:
    """Set a resume as the primary resume (unsets all others)."""
    service = ResumeService(session)
    resume = await service.set_primary_resume(resume_id)

    return ResumeResponse.model_validate(resume)


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete resume",
)
async def delete_resume(
    resume_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete resume and associated file."""
    service = ResumeService(session)
    await service.delete_resume(resume_id)


# Section endpoints


@router.get(
    "/{resume_id}/sections",
    response_model=list[ResumeSectionResponse],
    summary="Get resume sections",
)
async def get_resume_sections(
    resume_id: UUID,
    active_only: bool = False,
    session: AsyncSession = Depends(get_db_session),
) -> list[ResumeSectionResponse]:
    """Get all sections for a resume."""
    service = ResumeService(session)
    sections = await service.get_resume_sections(resume_id, active_only=active_only)

    return [ResumeSectionResponse.model_validate(s) for s in sections]


@router.post(
    "/{resume_id}/sections",
    response_model=ResumeSectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create resume section",
)
async def create_section(
    resume_id: UUID,
    section_data: ResumeSectionCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ResumeSectionResponse:
    """Create a new section for a resume."""
    # Ensure resume_id matches
    section_data.resume_id = resume_id

    service = ResumeService(session)
    section = await service.create_section(section_data)

    return ResumeSectionResponse.model_validate(section)


@router.put(
    "/{resume_id}/sections/{section_id}",
    response_model=ResumeSectionResponse,
    summary="Update section",
)
async def update_section(
    resume_id: UUID,
    section_id: UUID,
    update_data: ResumeSectionUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ResumeSectionResponse:
    """Update a resume section (partial update)."""
    service = ResumeService(session)
    section = await service.update_section(section_id, update_data)

    return ResumeSectionResponse.model_validate(section)


@router.delete(
    "/{resume_id}/sections/{section_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete section",
)
async def delete_section(
    resume_id: UUID,
    section_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a resume section."""
    service = ResumeService(session)
    await service.delete_section(section_id)


@router.post(
    "/{resume_id}/sections/reorder",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reorder sections",
)
async def reorder_sections(
    resume_id: UUID,
    section_orders: dict[UUID, int],
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Reorder sections by providing a mapping of section IDs to new order values."""
    service = ResumeService(session)
    await service.reorder_sections(resume_id, section_orders)


@router.get(
    "/aggregate/profile",
    summary="Get aggregated profile from all resumes",
)
async def get_aggregated_profile(
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Aggregate data from all resumes into a single deduplicated profile.

    This endpoint merges all parsed resume data, removing duplicates to create
    a comprehensive profile with all experience, education, skills, projects, etc.
    """
    aggregator = ResumeAggregatorService(session)
    return await aggregator.aggregate_all_resumes()


@router.get(
    "/aggregate/profile/smart",
    summary="Get smart-deduplicated profile from all resumes",
)
async def get_smart_deduplicated_profile(
    use_graph: bool = True,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Aggregate and smart-deduplicate data from all resumes.

    This endpoint performs advanced deduplication using:
    - Fuzzy string matching (rapidfuzz) for skills, certifications
    - AWS service name normalization
    - Experience/project merging with description consolidation
    - Technology overlap analysis (Jaccard similarity)
    - Semantic similarity using sentence-transformers embeddings
    - Optional: Knowledge graph integration for entity resolution

    Args:
        use_graph: Whether to use knowledge graph for enhanced deduplication

    Returns:
        Comprehensive profile with smart deduplication applied. Includes metadata
        about deduplication method and statistics.
    """
    # First aggregate all resumes
    aggregator = ResumeAggregatorService(session)
    aggregated_data = await aggregator.aggregate_all_resumes()

    # Initialize knowledge graph service if needed
    kg_service = None
    if use_graph and KnowledgeGraphService is not None:
        try:
            kg_service = KnowledgeGraphService()
        except Exception as e:
            # Fall back to non-graph deduplication if graph unavailable
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Knowledge graph unavailable: {e}. Using fuzzy-only mode.")

    # Apply smart deduplication
    deduplicator = ResumeDeduplicatorService(kg_service=kg_service)
    return await deduplicator.smart_deduplicate_async(
        aggregated_data, use_graph=use_graph
    )

"""Resume generation API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from turbo.api.dependencies import get_resume_generation_service
from turbo.core.services.resume_generation import ResumeGenerationService
from turbo.utils.exceptions import ValidationError

router = APIRouter()


class ResumeGenerationRequest(BaseModel):
    """Request model for generating tailored resumes."""

    base_resume_id: UUID = Field(..., description="Base resume to customize")
    job_description: str = Field(..., description="Full job description text")
    job_title: str | None = Field(None, description="Job title")
    company_name: str | None = Field(None, description="Company name")
    job_application_id: UUID | None = Field(
        None, description="Job application to link"
    )
    output_format: str = Field(
        "markdown",
        description="Output format",
        pattern="^(markdown|pdf|docx)$",
    )


class ApplicationResumeRequest(BaseModel):
    """Request model for generating resume from application."""

    base_resume_id: UUID | None = Field(
        None, description="Base resume (uses primary if not provided)"
    )
    output_format: str = Field(
        "markdown",
        description="Output format",
        pattern="^(markdown|pdf|docx)$",
    )


class BatchGenerationRequest(BaseModel):
    """Request model for batch resume generation."""

    base_resume_id: UUID = Field(..., description="Base resume to customize")
    application_ids: list[UUID] = Field(
        ..., description="List of job application UUIDs"
    )
    output_format: str = Field(
        "markdown",
        description="Output format",
        pattern="^(markdown|pdf|docx)$",
    )


class ResumeGenerationResponse(BaseModel):
    """Response model for resume generation."""

    resume_id: str
    file_path: str
    match_score: float
    suggestions: list[str]
    title: str
    format: str


class BatchGenerationResponse(BaseModel):
    """Response model for batch generation."""

    results: list[dict]
    total: int
    successful: int
    failed: int


@router.post(
    "/generate",
    response_model=ResumeGenerationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_tailored_resume(
    request: ResumeGenerationRequest,
    generation_service: ResumeGenerationService = Depends(
        get_resume_generation_service
    ),
) -> ResumeGenerationResponse:
    """
    Generate a tailored resume for a specific job.

    This endpoint:
    1. Analyzes the job description to extract requirements
    2. Tailors resume content based on job requirements
    3. Reorders sections by relevance
    4. Generates custom summary
    5. Creates resume file in requested format
    6. Links to job application if provided

    Returns resume ID, file path, match score, and improvement suggestions.
    """
    try:
        result = await generation_service.generate_tailored_resume(
            base_resume_id=request.base_resume_id,
            job_description=request.job_description,
            job_title=request.job_title,
            company_name=request.company_name,
            job_application_id=request.job_application_id,
            output_format=request.output_format,
        )
        return ResumeGenerationResponse(**result)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume generation failed: {str(e)}",
        )


@router.post(
    "/generate/application/{application_id}",
    response_model=ResumeGenerationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_from_application(
    application_id: UUID,
    request: ApplicationResumeRequest,
    generation_service: ResumeGenerationService = Depends(
        get_resume_generation_service
    ),
) -> ResumeGenerationResponse:
    """
    Generate resume directly from a job application.

    Uses the job description, title, and company from the application.
    If no base resume is provided, uses the primary resume.
    """
    try:
        result = await generation_service.generate_from_application(
            job_application_id=application_id,
            base_resume_id=request.base_resume_id,
            output_format=request.output_format,
        )
        return ResumeGenerationResponse(**result)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume generation failed: {str(e)}",
        )


@router.post(
    "/generate/batch",
    response_model=BatchGenerationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def batch_generate_resumes(
    request: BatchGenerationRequest,
    generation_service: ResumeGenerationService = Depends(
        get_resume_generation_service
    ),
) -> BatchGenerationResponse:
    """
    Generate resumes for multiple job applications.

    Useful for bulk resume generation when applying to multiple positions.
    Returns results for each application, including successes and failures.
    """
    try:
        results = await generation_service.batch_generate_resumes(
            base_resume_id=request.base_resume_id,
            applications=request.application_ids,
            output_format=request.output_format,
        )

        successful = sum(1 for r in results if r.get("success"))
        failed = len(results) - successful

        return BatchGenerationResponse(
            results=results,
            total=len(results),
            successful=successful,
            failed=failed,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch generation failed: {str(e)}",
        )

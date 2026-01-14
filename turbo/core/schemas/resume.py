"""Resume Pydantic schemas for validation and serialization."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ResumeSectionBase(BaseModel):
    """Base schema for ResumeSection."""

    section_type: str = Field(..., max_length=50, description="Type: summary, experience, education, project, skill, other")
    title: str = Field(..., max_length=200, description="Section title")
    content: str = Field(..., description="Section content (markdown supported)")
    order: int = Field(0, description="Display order")
    is_active: bool = Field(True, description="Whether section is visible")
    section_metadata: dict = Field(default_factory=dict, description="Section-specific metadata (dates, company, etc.)")


class ResumeSectionCreate(ResumeSectionBase):
    """Schema for creating a resume section."""

    resume_id: UUID


class ResumeSectionUpdate(BaseModel):
    """Schema for updating a resume section."""

    section_type: str | None = Field(None, max_length=50)
    title: str | None = Field(None, max_length=200)
    content: str | None = None
    order: int | None = None
    is_active: bool | None = None
    section_metadata: dict | None = None


class ResumeSectionResponse(ResumeSectionBase):
    """Schema for resume section response."""

    id: UUID
    resume_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeBase(BaseModel):
    """Base schema for Resume."""

    title: str = Field(..., max_length=200, description="Resume title")
    file_type: str = Field(..., pattern="^(pdf|markdown)$", description="File type")
    is_primary: bool = Field(False, description="Is this the primary resume")
    target_role: str | None = Field(None, max_length=200, description="Target job role")
    target_company: str | None = Field(None, max_length=200, description="Target company")
    parsed_data: dict = Field(default_factory=dict, description="AI-extracted data from file")


class ResumeCreate(ResumeBase):
    """Schema for creating a resume."""

    file_path: str | None = Field(None, max_length=500, description="Path to uploaded file")


class ResumeUpdate(BaseModel):
    """Schema for updating a resume."""

    title: str | None = Field(None, max_length=200)
    file_path: str | None = Field(None, max_length=500)
    is_primary: bool | None = None
    target_role: str | None = Field(None, max_length=200)
    target_company: str | None = Field(None, max_length=200)
    parsed_data: dict | None = None


class ResumeResponse(ResumeBase):
    """Schema for resume response."""

    id: UUID
    file_path: str | None
    created_at: datetime
    updated_at: datetime
    sections: list[ResumeSectionResponse] = []

    model_config = {"from_attributes": True}


class ResumeListResponse(BaseModel):
    """Schema for list of resumes."""

    resumes: list[ResumeResponse]
    total: int


class ResumeUploadResponse(BaseModel):
    """Schema for resume upload response."""

    resume_id: UUID
    file_path: str
    message: str


class ParsedResumeData(BaseModel):
    """Schema for AI-parsed resume data."""

    personal: dict = Field(default_factory=dict, description="Name, email, phone, linkedin, location")
    summary: str | None = Field(None, description="Professional summary")
    experience: list[dict] = Field(default_factory=list, description="Work experiences")
    education: list[dict] = Field(default_factory=list, description="Education history")
    skills: list[str] = Field(default_factory=list, description="Skills list")
    projects: list[dict] = Field(default_factory=list, description="Projects")
    other: dict = Field(default_factory=dict, description="Additional sections")

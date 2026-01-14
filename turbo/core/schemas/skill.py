"""Skill Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SkillBase(BaseModel):
    """Base skill schema with common fields."""

    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(
        default="technical",
        pattern="^(technical|soft_skills|tools|languages|certifications|other)$",
    )
    proficiency_level: str = Field(
        default="intermediate",
        pattern="^(beginner|intermediate|advanced|expert)$",
    )
    description: str | None = Field(None, max_length=1000)
    years_of_experience: int | None = Field(None, ge=0, le=100)
    is_endorsed: bool = Field(default=False)
    last_used_at: datetime | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate skill name."""
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """Validate skill description."""
        if v is not None and not v.strip():
            return None
        return v.strip() if v else v


class SkillCreate(SkillBase):
    """Schema for creating new skills."""

    pass


class SkillUpdate(BaseModel):
    """Schema for updating skills (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=200)
    category: str | None = Field(
        None,
        pattern="^(technical|soft_skills|tools|languages|certifications|other)$",
    )
    proficiency_level: str | None = Field(
        None,
        pattern="^(beginner|intermediate|advanced|expert)$",
    )
    description: str | None = Field(None, max_length=1000)
    years_of_experience: int | None = Field(None, ge=0, le=100)
    is_endorsed: bool | None = None
    last_used_at: datetime | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate skill name."""
        if v is not None and not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip() if v else v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """Validate skill description."""
        if v is not None and not v.strip():
            return None
        return v.strip() if v else v


class SkillResponse(SkillBase):
    """Schema for skill API responses."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillSummary(BaseModel):
    """Summary information about a skill."""

    id: UUID
    name: str
    category: str
    proficiency_level: str
    is_endorsed: bool

    model_config = ConfigDict(from_attributes=True)

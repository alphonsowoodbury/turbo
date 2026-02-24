"""
Settings Schemas

Pydantic schemas for settings validation
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SettingBase(BaseModel):
    """Base setting schema"""
    key: str = Field(..., max_length=255)
    value: dict[str, Any]
    category: str = Field(default="general", max_length=100)
    description: str | None = Field(None, max_length=500)
    is_public: bool = Field(default=False)


class SettingCreate(SettingBase):
    """Schema for creating a setting"""
    pass


class SettingUpdate(BaseModel):
    """Schema for updating a setting"""
    value: dict[str, Any] | None = None
    category: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)
    is_public: bool | None = None


class SettingResponse(SettingBase):
    """Schema for setting response"""
    id: str
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


# Specific setting schemas

class ClaudeBackendSetting(BaseModel):
    """Claude backend configuration"""
    backend: str = Field(..., pattern="^(api|claude-cli)$", description="Backend type: 'api' or 'claude-cli'")
    api_key_configured: bool = Field(..., description="Whether API key is set")


class ClaudeBackendUpdate(BaseModel):
    """Update Claude backend"""
    backend: str = Field(..., pattern="^(api|claude-cli)$")

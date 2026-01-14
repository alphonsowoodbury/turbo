"""
Settings Schemas

Pydantic schemas for settings validation
"""

from pydantic import BaseModel, Field
from typing import Any, Optional


class SettingBase(BaseModel):
    """Base setting schema"""
    key: str = Field(..., max_length=255)
    value: dict[str, Any]
    category: str = Field(default="general", max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_public: bool = Field(default=False)


class SettingCreate(SettingBase):
    """Schema for creating a setting"""
    pass


class SettingUpdate(BaseModel):
    """Schema for updating a setting"""
    value: Optional[dict[str, Any]] = None
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_public: Optional[bool] = None


class SettingResponse(SettingBase):
    """Schema for setting response"""
    id: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# Specific setting schemas

class ClaudeBackendSetting(BaseModel):
    """Claude backend configuration"""
    backend: str = Field(..., pattern="^(api|claude-cli)$", description="Backend type: 'api' or 'claude-cli'")
    api_key_configured: bool = Field(..., description="Whether API key is set")


class ClaudeBackendUpdate(BaseModel):
    """Update Claude backend"""
    backend: str = Field(..., pattern="^(api|claude-cli)$")

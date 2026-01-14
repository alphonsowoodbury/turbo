"""
Settings API Endpoints

Manage application settings
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import os
import httpx

from turbo.core.database.connection import get_db_session
from turbo.core.schemas.settings import (
    SettingResponse,
    SettingCreate,
    SettingUpdate
)
from turbo.core.models.settings import Setting

router = APIRouter(prefix="/settings", tags=["settings"])


# Helper functions

async def get_or_create_setting(
    db: AsyncSession,
    key: str,
    default_value: dict,
    category: str = "general",
    description: str = ""
) -> Setting:
    """Get setting by key or create with default value"""
    from sqlalchemy import select

    stmt = select(Setting).where(Setting.key == key)
    result = await db.execute(stmt)
    setting = result.scalar_one_or_none()

    if not setting:
        setting = Setting(
            key=key,
            value=default_value,
            category=category,
            description=description,
            is_public=True
        )
        db.add(setting)
        await db.commit()
        await db.refresh(setting)

    return setting


async def update_setting_value(
    db: AsyncSession,
    key: str,
    value: dict
) -> Setting:
    """Update setting value"""
    from sqlalchemy import select

    stmt = select(Setting).where(Setting.key == key)
    result = await db.execute(stmt)
    setting = result.scalar_one_or_none()

    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

    setting.value = value
    await db.commit()
    await db.refresh(setting)

    return setting


# General Settings Endpoints

@router.get("/", response_model=List[SettingResponse])
async def list_settings(
    public_only: bool = True,
    db: AsyncSession = Depends(get_db_session)
):
    """List all settings"""
    from sqlalchemy import select

    stmt = select(Setting)
    if public_only:
        stmt = stmt.where(Setting.is_public == True)

    result = await db.execute(stmt)
    settings = result.scalars().all()

    return settings


@router.get("/{key}", response_model=SettingResponse)
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific setting"""
    from sqlalchemy import select

    stmt = select(Setting).where(Setting.key == key)
    result = await db.execute(stmt)
    setting = result.scalar_one_or_none()

    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

    if not setting.is_public:
        raise HTTPException(status_code=403, detail="Setting is not public")

    return setting


@router.put("/{key}", response_model=SettingResponse)
async def update_setting(
    key: str,
    update: SettingUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update a setting"""
    from sqlalchemy import select

    stmt = select(Setting).where(Setting.key == key)
    result = await db.execute(stmt)
    setting = result.scalar_one_or_none()

    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

    # Update fields
    if update.value is not None:
        setting.value = update.value
    if update.category is not None:
        setting.category = update.category
    if update.description is not None:
        setting.description = update.description
    if update.is_public is not None:
        setting.is_public = update.is_public

    await db.commit()
    await db.refresh(setting)

    return setting


# Claude-specific Settings


@router.put("/claude/api-key")
async def update_claude_api_key(
    request: dict,
    db: AsyncSession = Depends(get_db_session)
):
    """Update Claude API key (stored in database, masked in responses)"""
    api_key = request.get("api_key", "").strip()

    if not api_key:
        raise HTTPException(status_code=400, detail="API key cannot be empty")

    if not api_key.startswith("sk-ant-"):
        raise HTTPException(status_code=400, detail="Invalid Anthropic API key format")

    # Get or create the setting, then update it
    setting = await get_or_create_setting(
        db=db,
        key="anthropic_api_key",
        default_value={"api_key": api_key},
        category="claude",
        description="Anthropic API key for Claude AI"
    )

    # Update the value
    setting.value = {"api_key": api_key}
    await db.commit()
    await db.refresh(setting)

    # Notify Claude service to reload with new key
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                "http://turbo-claude-code:9000/reload",
                json={"api_key": api_key}
            )
    except Exception as e:
        print(f"Could not notify Claude service: {e}")

    return {
        "success": True,
        "message": "API key updated successfully",
        "api_key_configured": True
    }


@router.get("/claude/api-key")
async def get_claude_api_key_status(
    db: AsyncSession = Depends(get_db_session)
):
    """Get API key status (masked for security)"""
    from sqlalchemy import select

    # Check database
    stmt = select(Setting).where(Setting.key == "anthropic_api_key")
    result = await db.execute(stmt)
    setting = result.scalar_one_or_none()

    db_configured = setting is not None and bool(setting.value.get("api_key"))
    env_configured = bool(os.getenv("ANTHROPIC_API_KEY"))

    api_key = None
    if db_configured:
        api_key = setting.value.get("api_key")
    elif env_configured:
        api_key = os.getenv("ANTHROPIC_API_KEY")

    # Mask the key
    masked_key = None
    if api_key:
        masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "sk-ant-..."

    return {
        "configured": db_configured or env_configured,
        "source": "database" if db_configured else ("environment" if env_configured else "none"),
        "masked_key": masked_key
    }


@router.get("/claude/status")
async def get_claude_status():
    """Get Claude service status"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://turbo-claude-code:9000/health")
            health = response.json()

            config_response = await client.get("http://turbo-claude-code:9000/config")
            config = config_response.json()

            return {
                "available": True,
                "backend": health.get("backend", "unknown"),
                "authenticated": health.get("authenticated", False),
                "subagents_count": config.get("subagents_count", 0)
            }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


@router.get("/claude/api-key/raw")
async def get_claude_api_key_raw(
    db: AsyncSession = Depends(get_db_session)
):
    """Get unmasked API key for internal services only.

    WARNING: This endpoint should only be accessible from internal Docker network.
    """
    from sqlalchemy import select

    # Check database first
    stmt = select(Setting).where(Setting.key == "anthropic_api_key")
    result = await db.execute(stmt)
    setting = result.scalar_one_or_none()

    if setting and setting.value.get("api_key"):
        return {"api_key": setting.value.get("api_key")}

    # Fallback to environment
    env_key = os.getenv("ANTHROPIC_API_KEY")
    if env_key and not env_key.startswith("your_api_key"):
        return {"api_key": env_key}

    return {"api_key": None}

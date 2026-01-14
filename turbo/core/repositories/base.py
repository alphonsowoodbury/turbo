"""Base repository with common CRUD operations."""

from abc import ABC
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.database.base import Base

# Type variables for generic repository
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository with common CRUD operations."""

    def __init__(self, session: AsyncSession, model: type[ModelType]) -> None:
        self._session = session
        self._model = model

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        obj_data = obj_in.model_dump(exclude_unset=True)
        db_obj = self._model(**obj_data)
        self._session.add(db_obj)
        await self._session.commit()
        await self._session.refresh(db_obj)
        return db_obj

    async def get_by_id(self, id: UUID) -> ModelType | None:
        """Get record by ID."""
        stmt = select(self._model).where(self._model.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self, limit: int | None = None, offset: int | None = None
    ) -> list[ModelType]:
        """Get all records with optional pagination."""
        stmt = select(self._model)
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: UUID, obj_in: UpdateSchemaType) -> ModelType | None:
        """Update a record by ID."""
        # Get the existing record
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return None

        # Update with new values
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        await self._session.commit()
        await self._session.refresh(db_obj)
        return db_obj

    async def delete(self, id: UUID) -> bool:
        """Delete a record by ID."""
        stmt = delete(self._model).where(self._model.id == id)
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount > 0

    async def exists(self, id: UUID) -> bool:
        """Check if record exists."""
        stmt = select(self._model.id).where(self._model.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def count(self) -> int:
        """Count total records."""
        stmt = select(self._model.id)
        result = await self._session.execute(stmt)
        return len(list(result.scalars().all()))

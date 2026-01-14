"""SQLAlchemy declarative base and base model."""

from typing import Any
import uuid

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, declared_attr


class BaseModel:
    """Base model with common fields and functionality."""

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower() + "s"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation of the model."""
        if hasattr(self, "name"):
            return f"<{self.__class__.__name__}(id={self.id}, name='{self.name}')>"
        elif hasattr(self, "title"):
            return f"<{self.__class__.__name__}(id={self.id}, title='{self.title}')>"
        else:
            return f"<{self.__class__.__name__}(id={self.id})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }


class CompositeKeyModel:
    """Base model for tables with composite primary keys (no auto-generated UUID id)."""

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower() + "s"

    # Timestamps only (no id column)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation of the model."""
        # Get primary key column names
        pk_cols = [col.name for col in self.__table__.primary_key.columns]
        pk_values = ", ".join(f"{col}={getattr(self, col)}" for col in pk_cols)
        return f"<{self.__class__.__name__}({pk_values})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }


# Create the declarative base with our custom base class
Base = declarative_base(cls=BaseModel)

# Create separate base for composite-key models that shares the same metadata registry
# This allows CompositeBase models to reference tables from Base models via foreign keys
CompositeBase = declarative_base(cls=CompositeKeyModel, metadata=Base.metadata)

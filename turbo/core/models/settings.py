"""
Settings Model

Stores application-wide configuration settings
"""

from sqlalchemy import String, Boolean, JSON, Column
from turbo.core.database.base import Base


class Setting(Base):
    """Application settings model"""

    __tablename__ = "settings"

    # Setting key (unique identifier)
    key = Column(String(255), unique=True, nullable=False, index=True)

    # Setting value (stored as JSON for flexibility)
    value = Column(JSON, nullable=False)

    # Setting metadata
    category = Column(String(100), nullable=False, default="general")
    description = Column(String(500), nullable=True)
    is_public = Column(Boolean, default=False)  # Can be exposed to frontend

    def __repr__(self) -> str:
        return f"<Setting(key='{self.key}', category='{self.category}')>"

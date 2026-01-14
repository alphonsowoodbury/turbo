"""Favorite model definition."""

from sqlalchemy import Column, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from turbo.core.database.base import Base


class Favorite(Base):
    """Favorite model for bookmarking items."""

    __tablename__ = "favorites"

    # Item reference
    item_type = Column(String(50), nullable=False, index=True)  # issue, document, tag, blueprint
    item_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Ensure unique favorites per item
    __table_args__ = (
        UniqueConstraint("item_type", "item_id", name="unique_favorite_item"),
    )

    def __repr__(self) -> str:
        """String representation of the favorite."""
        return f"<Favorite(id={self.id}, item_type='{self.item_type}', item_id={self.item_id})>"
"""Knowledge Graph Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GraphNodeCreate(BaseModel):
    """Schema for creating a graph node."""

    entity_id: UUID = Field(..., description="ID of the entity (issue, project, etc.)")
    entity_type: str = Field(..., description="Type of entity (issue, project, etc.)")
    content: str = Field(..., description="Text content to index")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class GraphSearchQuery(BaseModel):
    """Schema for graph search queries."""

    query: str = Field(..., min_length=1, description="Search query text")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results to return")
    entity_types: list[str] | None = Field(
        default=None, description="Filter by entity types"
    )
    min_relevance: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum relevance score"
    )


class GraphSearchResult(BaseModel):
    """Schema for graph search results."""

    entity_id: UUID
    entity_type: str
    content: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class GraphSearchResponse(BaseModel):
    """Schema for graph search response."""

    query: str
    results: list[GraphSearchResult]
    total_results: int
    execution_time_ms: float


class GraphStats(BaseModel):
    """Schema for graph statistics."""

    total_nodes: int
    total_edges: int
    entities_by_type: dict[str, int]
    last_updated: datetime | None = None

"""Knowledge Graph API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from turbo.core.schemas.graph import (
    GraphNodeCreate,
    GraphSearchQuery,
    GraphSearchResponse,
    GraphSearchResult,
    GraphStats,
)
from turbo.core.services.graph import GraphService
from turbo.utils.config import get_settings

router = APIRouter()


async def get_graph_service() -> GraphService:
    """Dependency to get graph service instance."""
    settings = get_settings()
    if not settings.graph.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Knowledge graph is disabled in settings",
        )
    return GraphService()


@router.post("/search", response_model=GraphSearchResponse)
async def search_graph(
    query: GraphSearchQuery, graph_service: GraphService = Depends(get_graph_service)
) -> GraphSearchResponse:
    """
    Perform semantic search across the knowledge graph.

    Searches all indexed entities using vector embeddings to find
    semantically similar content based on meaning, not just keywords.

    Args:
        query: Search parameters including query text, limit, entity types, and min relevance

    Returns:
        Search results with relevance scores and metadata

    Example:
        ```
        POST /api/v1/graph/search
        {
            "query": "user authentication problems",
            "limit": 10,
            "entity_types": ["issue"],
            "min_relevance": 0.7
        }
        ```
    """
    try:
        health = await graph_service.health_check()
        if health["status"] != "healthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Neo4j is not available. Make sure it's running.",
            )

        results = await graph_service.search(query)
        return results

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )
    finally:
        await graph_service.close()


@router.get("/related/{entity_id}", response_model=list[GraphSearchResult])
async def get_related_entities(
    entity_id: UUID,
    entity_type: str = Query(..., description="Type of the entity (issue, project, etc.)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    graph_service: GraphService = Depends(get_graph_service),
) -> list[GraphSearchResult]:
    """
    Find entities semantically related to a specific entity.

    Uses vector similarity to find other entities with similar content
    or context to the specified entity.

    Args:
        entity_id: UUID of the source entity
        entity_type: Type of the entity (issue, project, etc.)
        limit: Maximum number of related entities to return

    Returns:
        List of related entities ordered by relevance

    Example:
        ```
        GET /api/v1/graph/related/123e4567-e89b-12d3-a456-426614174000?entity_type=issue&limit=5
        ```
    """
    try:
        health = await graph_service.health_check()
        if health["status"] != "healthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Neo4j is not available",
            )

        related = await graph_service.get_related_entities(
            entity_id=entity_id,
            entity_type=entity_type,
            limit=limit,
        )

        return related

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get related entities: {str(e)}",
        )
    finally:
        await graph_service.close()


@router.post("/index", status_code=status.HTTP_201_CREATED)
async def index_entity(
    node_data: GraphNodeCreate,
    graph_service: GraphService = Depends(get_graph_service),
) -> dict:
    """
    Index an entity in the knowledge graph.

    Creates or updates an entity node with semantic embeddings for
    searchability. This is typically called automatically when entities
    are created or updated.

    Args:
        node_data: Entity data including ID, type, content, and metadata

    Returns:
        Indexing confirmation with entity details

    Example:
        ```
        POST /api/v1/graph/index
        {
            "entity_id": "123e4567-e89b-12d3-a456-426614174000",
            "entity_type": "issue",
            "content": "Title: Fix login bug\\n\\nDescription: Users cannot login...",
            "metadata": {
                "title": "Fix login bug",
                "status": "open",
                "priority": "high"
            }
        }
        ```
    """
    try:
        health = await graph_service.health_check()
        if health["status"] != "healthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Neo4j is not available",
            )

        result = await graph_service.add_episode(node_data)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}",
        )
    finally:
        await graph_service.close()


@router.get("/stats", response_model=GraphStats)
async def get_graph_stats(
    graph_service: GraphService = Depends(get_graph_service),
) -> GraphStats:
    """
    Get knowledge graph statistics.

    Returns information about the current state of the graph including
    node counts, edge counts, and distribution by entity type.

    Returns:
        Graph statistics including total nodes, edges, and entity type breakdown

    Example:
        ```
        GET /api/v1/graph/stats
        ```
    """
    try:
        health = await graph_service.health_check()
        if health["status"] != "healthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Neo4j is not available",
            )

        stats = await graph_service.get_statistics()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )
    finally:
        await graph_service.close()


@router.get("/health")
async def check_graph_health(
    graph_service: GraphService = Depends(get_graph_service),
) -> dict:
    """
    Check knowledge graph health status.

    Verifies connectivity to Neo4j and returns the current health status.
    Useful for monitoring and debugging.

    Returns:
        Health status including connection state and any error messages

    Example:
        ```
        GET /api/v1/graph/health
        ```
    """
    try:
        health = await graph_service.health_check()
        return health
    except Exception as e:
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e),
        }
    finally:
        await graph_service.close()
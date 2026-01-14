"""Knowledge Graph service with local embeddings for semantic search."""

import os
import time
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any
from uuid import UUID

from turbo.core.schemas.graph import (
    GraphNodeCreate,
    GraphSearchQuery,
    GraphSearchResponse,
    GraphSearchResult,
    GraphStats,
)
from turbo.utils.config import get_settings

# Check if graph is enabled and dependencies are available
GRAPH_ENABLED = os.getenv("GRAPH_ENABLED", "false").lower() == "true"

try:
    import numpy as np
    from neo4j import AsyncGraphDatabase
    from sentence_transformers import SentenceTransformer
    GRAPH_DEPS_AVAILABLE = True
except ImportError:
    GRAPH_DEPS_AVAILABLE = False
    np = None  # type: ignore
    AsyncGraphDatabase = None  # type: ignore
    SentenceTransformer = None  # type: ignore


if GRAPH_DEPS_AVAILABLE:
    @lru_cache(maxsize=1)
    def get_embedding_model(model_name: str):
        """
        Get or create embedding model (cached).

        First run downloads ~90MB model, then cached in memory.
        Model: all-MiniLM-L6-v2
        - Embedding dim: 384
        - Speed: ~3000 sentences/sec on CPU
        - Quality: Excellent for semantic search
        """
        return SentenceTransformer(model_name)

    def cosine_similarity(a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a_arr = np.array(a)
        b_arr = np.array(b)
        dot_product = np.dot(a_arr, b_arr)
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        return float(dot_product / (norm_a * norm_b))
else:
    def get_embedding_model(model_name: str):
        """Stub when dependencies not available."""
        return None

    def cosine_similarity(a: list[float], b: list[float]) -> float:
        """Stub when dependencies not available."""
        return 0.0


class GraphService:
    """Service for knowledge graph operations with local embeddings."""

    def __init__(self) -> None:
        """Initialize graph service with Neo4j and local embeddings."""
        self._enabled = GRAPH_ENABLED and GRAPH_DEPS_AVAILABLE
        self._driver = None
        self._model = None
        if self._enabled:
            settings = get_settings()
            self._settings = settings.graph

    async def _get_driver(self):
        """Get or create Neo4j driver."""
        if not self._enabled:
            return None
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                self._settings.uri,
                auth=(self._settings.user, self._settings.password),
            )
        return self._driver

    def _get_model(self):
        """Get or create embedding model."""
        if not self._enabled:
            return None
        if self._model is None:
            self._model = get_embedding_model(self._settings.embedding_model)
        return self._model

    def _generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector from text using local model."""
        if not self._enabled:
            return []
        model = self._get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    async def health_check(self) -> dict[str, Any]:
        """Check Neo4j connection health."""
        if not self._enabled:
            return {
                "status": "disabled",
                "connected": False,
                "message": "Graph service is disabled",
            }
        try:
            driver = await self._get_driver()
            async with driver.session() as session:
                result = await session.run("RETURN 1 as health")
                record = await result.single()
                return {
                    "status": "healthy" if record else "unhealthy",
                    "connected": True,
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
            }

    async def add_episode(self, node_data: GraphNodeCreate) -> dict[str, Any]:
        """
        Add an entity (issue, project, etc.) to the knowledge graph.

        Args:
            node_data: Node creation data with entity_id, entity_type, content, and metadata

        Returns:
            dict with the created episode information
        """
        if not self._enabled:
            return {
                "entity_id": node_data.entity_id,
                "entity_type": node_data.entity_type,
                "indexed": False,
                "message": "Graph service is disabled",
            }

        driver = await self._get_driver()

        # Generate embedding locally
        embedding = self._generate_embedding(node_data.content)

        async with driver.session() as session:
            # Create or merge node with embedding
            query = """
            MERGE (e:Entity {id: $entity_id, type: $entity_type})
            SET e.content = $content,
                e.embedding = $embedding,
                e.created_at = datetime($created_at),
                e.updated_at = datetime($updated_at)
            SET e += $metadata
            RETURN e
            """

            await session.run(
                query,
                entity_id=str(node_data.entity_id),
                entity_type=node_data.entity_type,
                content=node_data.content,
                embedding=embedding,
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
                metadata=node_data.metadata,
            )

        return {
            "entity_id": node_data.entity_id,
            "entity_type": node_data.entity_type,
            "indexed": True,
            "created_at": datetime.now(timezone.utc),
            "embedding_dimensions": len(embedding),
        }

    async def search(self, query: GraphSearchQuery) -> GraphSearchResponse:
        """
        Search the knowledge graph for relevant entities using semantic similarity.

        Args:
            query: Search query with text, limit, filters, and relevance threshold

        Returns:
            GraphSearchResponse with matching results and metadata
        """
        if not self._enabled:
            return GraphSearchResponse(
                query=query.query,
                results=[],
                total_results=0,
                execution_time_ms=0.0,
            )

        start_time = time.time()
        driver = await self._get_driver()

        # Generate query embedding locally
        query_embedding = self._generate_embedding(query.query)

        async with driver.session() as session:
            # Fetch all entities (we'll do similarity in Python)
            # For production with many nodes, consider Neo4j vector index
            cypher_query = """
            MATCH (e:Entity)
            """

            # Add type filter if specified
            if query.entity_types:
                type_list = ", ".join([f"'{t}'" for t in query.entity_types])
                cypher_query += f" WHERE e.type IN [{type_list}]"

            cypher_query += """
            RETURN e.id as id, e.type as type, e.content as content,
                   e.embedding as embedding, e.created_at as created_at,
                   properties(e) as metadata
            """

            result = await session.run(cypher_query)
            records = [record async for record in result]

        # Calculate similarities and sort
        results = []
        for record in records:
            if not record["embedding"]:
                continue

            # Calculate cosine similarity
            similarity = cosine_similarity(query_embedding, record["embedding"])

            # Filter by minimum relevance
            if similarity < query.min_relevance:
                continue

            # Clean metadata (remove internal fields)
            metadata = dict(record["metadata"])
            for key in ["id", "type", "content", "embedding", "created_at", "updated_at"]:
                metadata.pop(key, None)

            # Convert Neo4j DateTime to Python datetime if needed
            created_at = record.get("created_at")
            if created_at and hasattr(created_at, "to_native"):
                created_at = created_at.to_native()

            graph_result = GraphSearchResult(
                entity_id=UUID(record["id"]),
                entity_type=record["type"],
                content=record["content"],
                relevance_score=similarity,
                metadata=metadata,
                created_at=created_at,
            )
            results.append(graph_result)

        # Sort by relevance and limit
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        results = results[: query.limit]

        execution_time_ms = (time.time() - start_time) * 1000

        return GraphSearchResponse(
            query=query.query,
            results=results,
            total_results=len(results),
            execution_time_ms=execution_time_ms,
        )

    async def get_related_entities(
        self, entity_id: UUID, entity_type: str, limit: int = 10
    ) -> list[GraphSearchResult]:
        """
        Get entities related to a specific entity.

        Args:
            entity_id: ID of the entity to find relations for
            entity_type: Type of the entity (issue, project, etc.)
            limit: Maximum number of related entities to return

        Returns:
            List of related entities as GraphSearchResult objects
        """
        if not self._enabled:
            return []

        driver = await self._get_driver()

        async with driver.session() as session:
            # Get the source entity's embedding
            source_query = """
            MATCH (e:Entity {id: $entity_id, type: $entity_type})
            RETURN e.embedding as embedding, e.content as content
            """

            source_result = await session.run(
                source_query,
                entity_id=str(entity_id),
                entity_type=entity_type,
            )
            source_record = await source_result.single()

            if not source_record or not source_record["embedding"]:
                return []

            source_embedding = source_record["embedding"]

            # Get all other entities
            others_query = """
            MATCH (e:Entity)
            WHERE e.id <> $entity_id
            RETURN e.id as id, e.type as type, e.content as content,
                   e.embedding as embedding, e.created_at as created_at,
                   properties(e) as metadata
            """

            result = await session.run(others_query, entity_id=str(entity_id))
            records = [record async for record in result]

        # Calculate similarities
        related_entities = []
        for record in records:
            if not record["embedding"]:
                continue

            similarity = cosine_similarity(source_embedding, record["embedding"])

            # Clean metadata
            metadata = dict(record["metadata"])
            for key in ["id", "type", "content", "embedding", "created_at", "updated_at"]:
                metadata.pop(key, None)

            # Convert Neo4j DateTime to Python datetime if needed
            created_at = record.get("created_at")
            if created_at and hasattr(created_at, "to_native"):
                created_at = created_at.to_native()

            related_entities.append(
                GraphSearchResult(
                    entity_id=UUID(record["id"]),
                    entity_type=record["type"],
                    content=record["content"],
                    relevance_score=similarity,
                    metadata=metadata,
                    created_at=created_at,
                )
            )

        # Sort by similarity and limit
        related_entities.sort(key=lambda x: x.relevance_score, reverse=True)
        return related_entities[:limit]

    async def get_statistics(self) -> GraphStats:
        """Get knowledge graph statistics."""
        if not self._enabled:
            return GraphStats(
                total_nodes=0,
                total_edges=0,
                entities_by_type={},
                last_updated=datetime.now(timezone.utc),
            )

        driver = await self._get_driver()

        async with driver.session() as session:
            # Count total nodes
            node_result = await session.run("MATCH (n:Entity) RETURN count(n) as count")
            node_record = await node_result.single()
            total_nodes = node_record["count"] if node_record else 0

            # Count total relationships
            edge_result = await session.run("MATCH ()-[r]->() RETURN count(r) as count")
            edge_record = await edge_result.single()
            total_edges = edge_record["count"] if edge_record else 0

            # Count entities by type
            type_result = await session.run(
                """
                MATCH (n:Entity)
                RETURN n.type as type, count(n) as count
                """
            )

            entities_by_type = {}
            async for record in type_result:
                if record["type"]:
                    entities_by_type[record["type"]] = record["count"]

            return GraphStats(
                total_nodes=total_nodes,
                total_edges=total_edges,
                entities_by_type=entities_by_type,
                last_updated=datetime.now(timezone.utc),
            )

    async def close(self) -> None:
        """Close Neo4j driver connection."""
        if self._driver:
            await self._driver.close()
            self._driver = None

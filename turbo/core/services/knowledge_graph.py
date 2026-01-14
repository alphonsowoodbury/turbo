"""Knowledge Graph service for entity resolution and semantic search using Neo4j."""

import logging
from typing import Any, Optional

from neo4j import AsyncGraphDatabase, AsyncDriver
from pydantic import BaseModel

from turbo.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EntityNode(BaseModel):
    """Represents an entity node in the knowledge graph."""

    id: str
    name: str
    type: str
    canonical_name: Optional[str] = None
    embedding: Optional[list[float]] = None
    metadata: dict[str, Any] = {}


class KnowledgeGraphService:
    """Service for interacting with Neo4j knowledge graph.

    Provides entity resolution, semantic search, and relationship management
    for skills, technologies, projects, and other resume entities.
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Initialize knowledge graph service.

        Args:
            uri: Neo4j connection URI (defaults to settings.NEO4J_URI)
            user: Neo4j username (defaults to settings.NEO4J_USER)
            password: Neo4j password (defaults to settings.NEO4J_PASSWORD)
        """
        self.uri = uri or settings.graph.uri
        self.user = user or settings.graph.user
        self.password = password or settings.graph.password
        self.driver: Optional[AsyncDriver] = None
        self._embedder = None

    async def __aenter__(self) -> "KnowledgeGraphService":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """Establish connection to Neo4j database."""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            # Verify connectivity
            await self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.uri}")

            # Initialize schema
            await self._initialize_schema()
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    async def close(self) -> None:
        """Close Neo4j connection."""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")

    async def _initialize_schema(self) -> None:
        """Initialize Neo4j schema with indexes and constraints."""
        if not self.driver:
            return

        async with self.driver.session() as session:
            # Create constraints for unique entity IDs
            constraints = [
                "CREATE CONSTRAINT skill_id IF NOT EXISTS FOR (s:Skill) REQUIRE s.id IS UNIQUE",
                "CREATE CONSTRAINT project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
                "CREATE CONSTRAINT technology_id IF NOT EXISTS FOR (t:Technology) REQUIRE t.id IS UNIQUE",
                "CREATE CONSTRAINT company_id IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE",
            ]

            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Exception as e:
                    logger.debug(f"Constraint may already exist: {e}")

            # Create indexes for faster lookups
            indexes = [
                "CREATE INDEX skill_name IF NOT EXISTS FOR (s:Skill) ON (s.name)",
                "CREATE INDEX skill_canonical IF NOT EXISTS FOR (s:Skill) ON (s.canonical_name)",
                "CREATE INDEX project_name IF NOT EXISTS FOR (p:Project) ON (p.name)",
                "CREATE INDEX technology_name IF NOT EXISTS FOR (t:Technology) ON (t.name)",
            ]

            for index in indexes:
                try:
                    await session.run(index)
                except Exception as e:
                    logger.debug(f"Index may already exist: {e}")

            # Create vector index for semantic search (Neo4j 5.11+)
            try:
                await session.run(
                    """
                    CREATE VECTOR INDEX skill_embedding IF NOT EXISTS
                    FOR (s:Skill) ON (s.embedding)
                    OPTIONS {indexConfig: {
                        `vector.dimensions`: 384,
                        `vector.similarity_function`: 'cosine'
                    }}
                    """
                )
                logger.info("Vector index created for skill embeddings")
            except Exception as e:
                logger.warning(f"Failed to create vector index (requires Neo4j 5.11+): {e}")

    def _load_embedder(self) -> Any:
        """Load sentence transformer model for embeddings."""
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Loaded sentence transformer model for embeddings")
            except Exception as e:
                logger.warning(f"Failed to load embedder: {e}")
        return self._embedder

    async def find_related_entities(
        self,
        entity_id: str,
        entity_type: str,
        limit: int = 5,
        similarity_threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """Find entities related to a given entity using various strategies.

        Args:
            entity_id: ID or name of the entity
            entity_type: Type of entity (skill, project, technology, etc.)
            limit: Maximum number of related entities to return
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of related entity dictionaries with similarity scores
        """
        if not self.driver:
            await self.connect()

        # Normalize entity type to Neo4j label
        label = entity_type.capitalize()

        async with self.driver.session() as session:
            # First, try exact name match to get canonical entity
            result = await session.run(
                f"""
                MATCH (e:{label})
                WHERE e.name = $entity_id OR e.id = $entity_id OR e.canonical_name = $entity_id
                RETURN e.id as id, e.name as name, e.canonical_name as canonical_name,
                       e.embedding as embedding, e AS entity
                LIMIT 1
                """,
                entity_id=entity_id,
            )

            record = await result.single()
            if not record:
                # Entity not in graph, try fuzzy search
                return await self._fuzzy_search_entities(
                    entity_id, entity_type, limit, similarity_threshold
                )

            entity_name = record["canonical_name"] or record["name"]
            embedding = record.get("embedding")

            # Strategy 1: Find entities connected via relationships
            relationship_matches = await self._find_by_relationships(
                session, record["id"], label, limit
            )

            # Strategy 2: Find entities with similar embeddings (if available)
            if embedding:
                vector_matches = await self._find_by_vector_similarity(
                    session, embedding, label, limit, similarity_threshold
                )
            else:
                vector_matches = []

            # Strategy 3: Find entities in same technology stack
            stack_matches = await self._find_by_technology_stack(
                session, record["id"], label, limit
            )

            # Combine and deduplicate results
            all_matches = {}
            for match in relationship_matches + vector_matches + stack_matches:
                entity_id_key = match["id"]
                if entity_id_key not in all_matches:
                    all_matches[entity_id_key] = match
                else:
                    # Keep highest similarity score
                    if match.get("similarity", 0) > all_matches[entity_id_key].get(
                        "similarity", 0
                    ):
                        all_matches[entity_id_key] = match

            # Sort by similarity and return top N
            results = sorted(
                all_matches.values(),
                key=lambda x: x.get("similarity", 0),
                reverse=True,
            )
            return results[:limit]

    async def _fuzzy_search_entities(
        self,
        query: str,
        entity_type: str,
        limit: int,
        threshold: float,
    ) -> list[dict[str, Any]]:
        """Perform fuzzy search for entities not in graph."""
        if not self.driver:
            return []

        label = entity_type.capitalize()

        async with self.driver.session() as session:
            # Use Levenshtein distance or similar for fuzzy matching
            result = await session.run(
                f"""
                MATCH (e:{label})
                WITH e, apoc.text.levenshteinSimilarity(toLower(e.name), toLower($query)) AS similarity
                WHERE similarity >= $threshold
                RETURN e.id as id, e.name as name, e.canonical_name as canonical_name,
                       similarity
                ORDER BY similarity DESC
                LIMIT $limit
                """,
                query=query,
                threshold=threshold,
                limit=limit,
            )

            records = await result.data()
            return [
                {
                    "id": r["id"],
                    "name": r["canonical_name"] or r["name"],
                    "similarity": r["similarity"],
                }
                for r in records
            ]

    async def _find_by_relationships(
        self,
        session: Any,
        entity_id: str,
        label: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Find related entities via graph relationships."""
        result = await session.run(
            f"""
            MATCH (e:{label})-[r]-(related:{label})
            WHERE e.id = $entity_id AND e.id <> related.id
            RETURN related.id as id, related.name as name,
                   related.canonical_name as canonical_name,
                   type(r) as relationship_type,
                   0.9 as similarity
            LIMIT $limit
            """,
            entity_id=entity_id,
            limit=limit,
        )

        records = await result.data()
        return [
            {
                "id": r["id"],
                "name": r["canonical_name"] or r["name"],
                "similarity": r["similarity"],
                "relationship": r["relationship_type"],
            }
            for r in records
        ]

    async def _find_by_vector_similarity(
        self,
        session: Any,
        embedding: list[float],
        label: str,
        limit: int,
        threshold: float,
    ) -> list[dict[str, Any]]:
        """Find similar entities using vector similarity search."""
        try:
            # Use Neo4j 5.11+ vector index query
            result = await session.run(
                f"""
                CALL db.index.vector.queryNodes('{label.lower()}_embedding', $limit * 2, $embedding)
                YIELD node, score
                WHERE score >= $threshold
                RETURN node.id as id, node.name as name,
                       node.canonical_name as canonical_name,
                       score as similarity
                LIMIT $limit
                """,
                embedding=embedding,
                limit=limit,
                threshold=threshold,
            )

            records = await result.data()
            return [
                {
                    "id": r["id"],
                    "name": r["canonical_name"] or r["name"],
                    "similarity": r["similarity"],
                }
                for r in records
            ]
        except Exception as e:
            logger.debug(f"Vector search not available: {e}")
            return []

    async def _find_by_technology_stack(
        self,
        session: Any,
        entity_id: str,
        label: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Find entities that frequently appear together in projects."""
        result = await session.run(
            f"""
            MATCH (e:{label})<-[:USES]-(p:Project)-[:USES]->(related:{label})
            WHERE e.id = $entity_id AND e.id <> related.id
            WITH related, COUNT(p) as co_occurrence
            RETURN related.id as id, related.name as name,
                   related.canonical_name as canonical_name,
                   co_occurrence,
                   0.8 as similarity
            ORDER BY co_occurrence DESC
            LIMIT $limit
            """,
            entity_id=entity_id,
            limit=limit,
        )

        records = await result.data()
        return [
            {
                "id": r["id"],
                "name": r["canonical_name"] or r["name"],
                "similarity": r["similarity"],
                "co_occurrence": r["co_occurrence"],
            }
            for r in records
        ]

    async def add_skill(
        self,
        name: str,
        canonical_name: Optional[str] = None,
        category: Optional[str] = None,
    ) -> str:
        """Add a skill to the knowledge graph.

        Args:
            name: Skill name
            canonical_name: Canonical/normalized form of the skill
            category: Skill category (e.g., 'language', 'framework', 'tool')

        Returns:
            Skill ID
        """
        if not self.driver:
            await self.connect()

        # Generate embedding for the skill
        embedder = self._load_embedder()
        embedding = None
        if embedder:
            try:
                embedding = embedder.encode(canonical_name or name).tolist()
            except Exception as e:
                logger.warning(f"Failed to generate embedding: {e}")

        async with self.driver.session() as session:
            result = await session.run(
                """
                MERGE (s:Skill {name: $name})
                ON CREATE SET
                    s.id = randomUUID(),
                    s.canonical_name = $canonical_name,
                    s.category = $category,
                    s.embedding = $embedding,
                    s.created_at = datetime()
                ON MATCH SET
                    s.canonical_name = COALESCE($canonical_name, s.canonical_name),
                    s.category = COALESCE($category, s.category),
                    s.embedding = COALESCE($embedding, s.embedding),
                    s.updated_at = datetime()
                RETURN s.id as id
                """,
                name=name,
                canonical_name=canonical_name,
                category=category,
                embedding=embedding,
            )

            record = await result.single()
            return record["id"]

    async def add_project_technology_relationship(
        self,
        project_name: str,
        technology_name: str,
    ) -> None:
        """Create relationship between project and technology.

        Args:
            project_name: Name of the project
            technology_name: Name of the technology
        """
        if not self.driver:
            await self.connect()

        async with self.driver.session() as session:
            await session.run(
                """
                MERGE (p:Project {name: $project_name})
                ON CREATE SET p.id = randomUUID()
                MERGE (t:Technology {name: $technology_name})
                ON CREATE SET t.id = randomUUID()
                MERGE (p)-[:USES]->(t)
                """,
                project_name=project_name,
                technology_name=technology_name,
            )

    async def get_canonical_skill_name(self, skill: str) -> Optional[str]:
        """Get canonical name for a skill from the graph.

        Args:
            skill: Skill name to look up

        Returns:
            Canonical skill name or None if not found
        """
        if not self.driver:
            try:
                await self.connect()
            except Exception:
                return None

        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (s:Skill)
                WHERE s.name = $skill OR s.canonical_name = $skill
                RETURN s.canonical_name as canonical_name
                LIMIT 1
                """,
                skill=skill,
            )

            record = await result.single()
            if record and record["canonical_name"]:
                return record["canonical_name"]

        return None

    async def search_entities(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Semantic search across entities in the knowledge graph.

        Args:
            query: Search query text
            entity_type: Optional entity type filter (skill, project, etc.)
            limit: Maximum results

        Returns:
            List of matching entities with scores
        """
        if not self.driver:
            await self.connect()

        # Generate query embedding
        embedder = self._load_embedder()
        if not embedder:
            logger.warning("Embedder not available for semantic search")
            return []

        query_embedding = embedder.encode(query).tolist()

        # Search across entity types
        label = entity_type.capitalize() if entity_type else "Skill"

        async with self.driver.session() as session:
            try:
                result = await session.run(
                    f"""
                    CALL db.index.vector.queryNodes('{label.lower()}_embedding', $limit, $embedding)
                    YIELD node, score
                    RETURN node.id as id, node.name as name,
                           node.canonical_name as canonical_name,
                           labels(node) as types,
                           score
                    ORDER BY score DESC
                    LIMIT $limit
                    """,
                    embedding=query_embedding,
                    limit=limit,
                )

                records = await result.data()
                return [
                    {
                        "id": r["id"],
                        "name": r["canonical_name"] or r["name"],
                        "type": r["types"][0] if r["types"] else label,
                        "score": r["score"],
                    }
                    for r in records
                ]
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")
                # Fallback to text search
                return []

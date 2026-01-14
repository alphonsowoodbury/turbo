"""Conversation memory service for long-term AI chat memory management."""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.conversation_memory import ConversationMemory, ConversationSummary
from turbo.core.models.staff_conversation import StaffConversation

logger = logging.getLogger(__name__)

# Lazy load embedding model
_embedding_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """Get or create sentence transformer model for embeddings."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Loaded sentence transformer model for memory embeddings")
    return _embedding_model


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a_arr = np.array(a)
    b_arr = np.array(b)
    dot_product = np.dot(a_arr, b_arr)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot_product / (norm_a * norm_b))


class ConversationMemoryService:
    """
    Service for managing long-term conversation memory.

    Handles extraction, storage, and retrieval of conversation memories
    including facts, preferences, decisions, and insights.
    """

    def __init__(self, db: AsyncSession, anthropic_api_key: str | None = None):
        """Initialize memory service.

        Args:
            db: Database session
            anthropic_api_key: Anthropic API key for Claude calls
        """
        self.db = db
        self.anthropic_api_key = anthropic_api_key
        self.model = get_embedding_model()

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector from text."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    async def extract_memories_from_conversation(
        self,
        entity_type: str,
        entity_id: UUID,
        messages: list[dict[str, Any]],
        min_importance: float = 0.3,
    ) -> list[ConversationMemory]:
        """
        Extract key memories from conversation messages using Claude.

        Args:
            entity_type: "staff" or "mentor"
            entity_id: UUID of the staff member or mentor
            messages: List of conversation messages
            min_importance: Minimum importance score to store

        Returns:
            List of extracted ConversationMemory objects
        """
        if not self.anthropic_api_key or len(messages) < 3:
            return []

        # Build conversation context
        conversation_text = "\n\n".join([
            f"{'User' if msg['message_type'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in messages
        ])

        # Prompt for memory extraction
        extraction_prompt = f"""Analyze this conversation and extract key memories that should be preserved long-term.

Conversation:
{conversation_text}

Extract the following types of memories:
1. **Facts**: Important factual information mentioned (e.g., "User uses PostgreSQL", "Project deadline is next Friday")
2. **Preferences**: User preferences or opinions (e.g., "User prefers TypeScript over JavaScript")
3. **Decisions**: Decisions made during the conversation (e.g., "Decided to use AWS for deployment")
4. **Insights**: Important insights or learnings (e.g., "User struggles with async/await patterns")
5. **Entity Mentions**: Important references to projects, issues, or documents

For each memory, rate its importance from 0.0 to 1.0:
- 0.8-1.0: Critical information (core preferences, major decisions)
- 0.5-0.7: Important information (useful facts, minor decisions)
- 0.3-0.4: Contextual information (nice to know, temporary relevance)
- 0.0-0.2: Low importance (trivial facts)

Return a JSON array of memories:
[
  {{
    "type": "fact|preference|decision|insight|entity_mention",
    "content": "Clear, concise description of the memory",
    "importance": 0.7,
    "entities": {{"issues": ["uuid1"], "projects": [], "documents": []}}
  }}
]

Only extract memories with importance >= {min_importance}. If there are no significant memories, return an empty array.
"""

        try:
            # Call Claude for extraction
            headers = {
                "x-api-key": self.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json={
                        "model": "claude-sonnet-4-5-20250929",
                        "max_tokens": 2048,
                        "messages": [{"role": "user", "content": extraction_prompt}]
                    }
                )

                if response.status_code != 200:
                    logger.error(f"Claude API error: {response.status_code}")
                    return []

                result = response.json()
                content = result["content"][0]["text"]

                # Parse JSON from response
                # Extract JSON array from markdown code blocks if present
                json_match = re.search(r'```(?:json)?\n?([\s\S]*?)\n?```', content)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = content

                memories_data = json.loads(json_str.strip())

                # Create ConversationMemory objects
                memories = []
                for mem_data in memories_data:
                    # Generate embedding
                    embedding = self.generate_embedding(mem_data["content"])

                    memory = ConversationMemory(
                        entity_type=entity_type,
                        entity_id=entity_id,
                        memory_type=mem_data["type"],
                        content=mem_data["content"],
                        importance=mem_data["importance"],
                        relevance_score=1.0,  # Starts at full relevance
                        entities_mentioned=mem_data.get("entities"),
                        embedding=embedding,
                        source_message_ids=[str(msg["id"]) for msg in messages],
                        first_mentioned_at=datetime.utcnow(),
                        last_accessed_at=datetime.utcnow(),
                        access_count=0
                    )

                    self.db.add(memory)
                    memories.append(memory)

                if memories:
                    await self.db.commit()
                    logger.info(f"Extracted {len(memories)} memories from conversation")

                return memories

        except Exception as e:
            logger.error(f"Failed to extract memories: {e}", exc_info=True)
            return []

    async def get_relevant_memories(
        self,
        entity_type: str,
        entity_id: UUID,
        query_text: str,
        limit: int = 5,
        min_relevance: float = 0.6,
        decay_days: int = 30,
    ) -> list[ConversationMemory]:
        """
        Retrieve relevant memories for a query using semantic search.

        Args:
            entity_type: "staff" or "mentor"
            entity_id: UUID of the staff member or mentor
            query_text: Current message or query to find relevant memories for
            limit: Maximum number of memories to return
            min_relevance: Minimum relevance score (0-1)
            decay_days: Number of days for relevance to decay to 50%

        Returns:
            List of relevant ConversationMemory objects
        """
        # Generate query embedding
        query_embedding = self.generate_embedding(query_text)

        # Fetch all memories for this entity
        result = await self.db.execute(
            select(ConversationMemory)
            .where(
                and_(
                    ConversationMemory.entity_type == entity_type,
                    ConversationMemory.entity_id == entity_id
                )
            )
        )
        memories = result.scalars().all()

        if not memories:
            return []

        # Calculate relevance scores with temporal decay
        scored_memories = []
        for memory in memories:
            if not memory.embedding:
                continue

            # Semantic similarity
            similarity = cosine_similarity(query_embedding, memory.embedding)

            # Temporal decay (exponential decay over time)
            days_old = (datetime.utcnow() - memory.first_mentioned_at).days
            time_factor = np.exp(-days_old / decay_days)

            # Combined score: semantic similarity * importance * temporal decay
            relevance = similarity * memory.importance * time_factor

            if relevance >= min_relevance:
                scored_memories.append((memory, relevance))

        # Sort by relevance and limit
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        relevant_memories = [mem for mem, _ in scored_memories[:limit]]

        # Update access metadata
        for memory in relevant_memories:
            memory.last_accessed_at = datetime.utcnow()
            memory.access_count += 1

        await self.db.commit()

        logger.info(f"Retrieved {len(relevant_memories)} relevant memories (from {len(memories)} total)")
        return relevant_memories

    async def create_conversation_summary(
        self,
        entity_type: str,
        entity_id: UUID,
        message_range_start: int,
        message_range_end: int,
        messages: list[dict[str, Any]],
    ) -> ConversationSummary | None:
        """
        Create a summary of a conversation segment.

        Args:
            entity_type: "staff" or "mentor"
            entity_id: UUID of the staff member or mentor
            message_range_start: Starting message index
            message_range_end: Ending message index
            messages: List of conversation messages to summarize

        Returns:
            ConversationSummary object or None if creation fails
        """
        if not self.anthropic_api_key or len(messages) < 5:
            return None

        # Build conversation context
        conversation_text = "\n\n".join([
            f"{'User' if msg['message_type'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in messages
        ])

        # Prompt for summarization
        summary_prompt = f"""Summarize this conversation segment concisely, preserving key information.

Conversation:
{conversation_text}

Provide a summary with:
1. **Main Topics**: 2-5 key topics discussed
2. **Summary**: Concise 2-3 paragraph summary capturing the essential information
3. **Entities**: Any projects, issues, or documents mentioned
4. **Decisions**: Key decisions made (if any)

Return JSON:
{{
  "summary": "The summary text...",
  "key_topics": ["topic1", "topic2", "topic3"],
  "entities": {{"issues": ["uuid1"], "projects": [], "documents": []}},
  "decisions": ["Decision 1", "Decision 2"]
}}
"""

        try:
            headers = {
                "x-api-key": self.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json={
                        "model": "claude-sonnet-4-5-20250929",
                        "max_tokens": 1024,
                        "messages": [{"role": "user", "content": summary_prompt}]
                    }
                )

                if response.status_code != 200:
                    logger.error(f"Claude API error: {response.status_code}")
                    return None

                result = response.json()
                content = result["content"][0]["text"]

                # Parse JSON
                json_match = re.search(r'```(?:json)?\n?([\s\S]*?)\n?```', content)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = content

                summary_data = json.loads(json_str.strip())

                # Generate embedding for summary
                embedding = self.generate_embedding(summary_data["summary"])

                # Get time range - parse ISO format strings to datetime
                time_range_start_str = messages[0].get("created_at")
                time_range_end_str = messages[-1].get("created_at")

                # Parse ISO datetime strings
                time_range_start = datetime.fromisoformat(time_range_start_str.replace('Z', '+00:00')) if isinstance(time_range_start_str, str) else time_range_start_str
                time_range_end = datetime.fromisoformat(time_range_end_str.replace('Z', '+00:00')) if isinstance(time_range_end_str, str) else time_range_end_str

                summary = ConversationSummary(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    summary_text=summary_data["summary"],
                    message_range_start=message_range_start,
                    message_range_end=message_range_end,
                    message_count=len(messages),
                    key_topics=summary_data.get("key_topics", []),
                    entities_discussed=summary_data.get("entities", {}),
                    decisions_made=summary_data.get("decisions", []),
                    embedding=embedding,
                    time_range_start=time_range_start,
                    time_range_end=time_range_end
                )

                self.db.add(summary)
                await self.db.commit()

                logger.info(f"Created summary for messages {message_range_start}-{message_range_end}")
                return summary

        except Exception as e:
            logger.error(f"Failed to create summary: {e}", exc_info=True)
            return None

    async def get_or_create_summary(
        self,
        entity_type: str,
        entity_id: UUID,
        message_range_start: int,
        message_range_end: int,
        messages: list[dict[str, Any]],
    ) -> ConversationSummary | None:
        """
        Get existing summary or create a new one if it doesn't exist.

        Args:
            entity_type: "staff" or "mentor"
            entity_id: UUID of the staff member or mentor
            message_range_start: Starting message index
            message_range_end: Ending message index
            messages: List of conversation messages

        Returns:
            ConversationSummary object or None
        """
        # Check if summary already exists
        result = await self.db.execute(
            select(ConversationSummary)
            .where(
                and_(
                    ConversationSummary.entity_type == entity_type,
                    ConversationSummary.entity_id == entity_id,
                    ConversationSummary.message_range_start == message_range_start,
                    ConversationSummary.message_range_end == message_range_end
                )
            )
        )
        existing_summary = result.scalar_one_or_none()

        if existing_summary:
            logger.info(f"Using existing summary for messages {message_range_start}-{message_range_end}")
            return existing_summary

        # Create new summary
        return await self.create_conversation_summary(
            entity_type, entity_id, message_range_start, message_range_end, messages
        )

    async def decay_old_memories(self, days_threshold: int = 90, decay_factor: float = 0.5):
        """
        Apply relevance decay to old memories.

        Args:
            days_threshold: Memories older than this many days will be decayed
            decay_factor: Factor to multiply relevance_score by (0.0 to 1.0)
        """
        threshold_date = datetime.utcnow() - timedelta(days=days_threshold)

        result = await self.db.execute(
            select(ConversationMemory)
            .where(ConversationMemory.first_mentioned_at < threshold_date)
        )
        old_memories = result.scalars().all()

        for memory in old_memories:
            memory.relevance_score *= decay_factor

        await self.db.commit()
        logger.info(f"Applied decay to {len(old_memories)} old memories")

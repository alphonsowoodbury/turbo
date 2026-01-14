"""Context manager for intelligent conversation window management."""

import logging
import re
from typing import Any
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.conversation_memory import ConversationMemory, ConversationSummary
from turbo.core.models.staff_conversation import StaffConversation
from turbo.core.models.staff import Staff
from turbo.core.models.issue import Issue
from turbo.core.models.project import Project
from turbo.core.models.document import Document
from turbo.core.models.milestone import Milestone
from turbo.core.models.job_application import JobApplication
from turbo.core.models.company import Company
from turbo.core.models.network_contact import NetworkContact
from turbo.core.models.resume import Resume
from turbo.core.services.conversation_memory import ConversationMemoryService
from turbo.core.services.graph import GraphService

logger = logging.getLogger(__name__)


class ConversationContextManager:
    """
    Manages conversation context with intelligent windowing.

    Token Budget: ~6000 tokens
    - Recent messages (last 5): Full detail (1500 tokens)
    - Mid-range messages (6-20): Summaries (1000 tokens)
    - Old messages (21+): Key facts from memories (500 tokens)
    - Related entities: Auto-fetched from graph (2000 tokens)
    - Long-term memory: User preferences, patterns (1000 tokens)
    """

    def __init__(
        self,
        db: AsyncSession,
        memory_service: ConversationMemoryService,
        graph_service: GraphService | None = None
    ):
        """Initialize context manager.

        Args:
            db: Database session
            memory_service: Service for long-term memory management
            graph_service: Service for knowledge graph operations (optional)
        """
        self.db = db
        self.memory_service = memory_service
        self.graph_service = graph_service

    async def build_context(
        self,
        entity_type: str,
        entity_id: UUID,
        current_message: str,
        max_messages: int = 100,
        max_tokens: int = 6000
    ) -> dict[str, Any]:
        """
        Build optimized conversation context.

        Args:
            entity_type: "staff" (mentor is deprecated)
            entity_id: UUID of the staff member
            current_message: The current user message being responded to
            max_messages: Maximum number of messages to fetch
            max_tokens: Target token budget for context

        Returns:
            dict with:
                - recent_messages: Last 5 messages (full)
                - conversation_summary: Summary of messages 6-20
                - key_facts: Important facts from old messages
                - related_entities: Entities from knowledge graph
                - memories: Relevant long-term memories
                - user_context: Active projects, issues, career data (if staff has career capabilities)
                - total_message_count: Total messages in conversation
        """
        logger.info(f"Building context for {entity_type} {entity_id}")

        # 1. Get all messages
        messages = await self._get_messages(entity_type, entity_id, limit=max_messages)
        total_count = len(messages)

        if total_count == 0:
            return self._empty_context()

        # 2. Recent messages (last 5) - full detail
        recent_messages = messages[-5:] if total_count >= 5 else messages
        logger.info(f"Using {len(recent_messages)} recent messages")

        # 3. Mid-range summary (messages 6-20)
        conversation_summary = None
        if total_count > 20:
            midrange_start = total_count - 20
            midrange_end = total_count - 5
            midrange = messages[midrange_start:midrange_end]

            # Get or create summary
            conversation_summary = await self.memory_service.get_or_create_summary(
                entity_type=entity_type,
                entity_id=entity_id,
                message_range_start=midrange_start,
                message_range_end=midrange_end,
                messages=[self._message_to_dict(m) for m in midrange]
            )
            logger.info(f"Using conversation summary for messages {midrange_start}-{midrange_end}")

        # 4. Key facts from old messages (21+)
        key_facts = []
        if total_count > 20:
            # Get memories for old portion
            old_memories = await self.memory_service.get_relevant_memories(
                entity_type=entity_type,
                entity_id=entity_id,
                query_text=current_message,
                limit=5
            )
            key_facts = [
                {
                    "type": m.memory_type,
                    "content": m.content,
                    "importance": m.importance
                }
                for m in old_memories
                if m.memory_type in ["fact", "decision", "preference"]
            ]
            logger.info(f"Retrieved {len(key_facts)} key facts from old messages")

        # 5. Search knowledge graph for related entities
        related_entities = {}
        if self.graph_service:
            try:
                related_entities = await self._search_graph_for_related(
                    messages=messages,
                    current_message=current_message
                )
                logger.info(f"Found related entities from knowledge graph")
            except Exception as e:
                logger.warning(f"Knowledge graph search failed: {e}")
                related_entities = {}

        # 6. Get relevant long-term memories
        memories = await self.memory_service.get_relevant_memories(
            entity_type=entity_type,
            entity_id=entity_id,
            query_text=current_message,
            limit=5,
            min_relevance=0.6
        )
        logger.info(f"Retrieved {len(memories)} relevant memories")

        # 7. User context (active work and career data for mentors)
        user_context = await self._get_user_context(entity_type, entity_id)

        # 8. Extract entities mentioned in conversation
        entities_discussed = self._extract_all_entities(messages + [
            type('Message', (), {'content': current_message})()
        ])

        return {
            "recent_messages": [self._message_to_dict(m) for m in recent_messages],
            "conversation_summary": self._summary_to_dict(conversation_summary) if conversation_summary else None,
            "key_facts": key_facts,
            "related_entities": related_entities,
            "memories": [self._memory_to_dict(m) for m in memories],
            "user_context": user_context,
            "entities_discussed": entities_discussed,
            "total_message_count": total_count,
            "metadata": {
                "has_summary": conversation_summary is not None,
                "has_old_messages": total_count > 20,
                "memory_count": len(memories),
                "related_count": sum(len(v) for v in related_entities.values())
            }
        }

    async def _get_messages(
        self,
        entity_type: str,
        entity_id: UUID,
        limit: int = 100
    ) -> list[StaffConversation]:
        """Fetch messages from database.

        Args:
            entity_type: "staff" (mentor is deprecated)
            entity_id: UUID of the staff member
            limit: Maximum number of messages to fetch

        Returns:
            List of message objects ordered by creation time
        """
        result = await self.db.execute(
            select(StaffConversation)
            .where(StaffConversation.staff_id == entity_id)
            .order_by(StaffConversation.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _search_graph_for_related(
        self,
        messages: list,
        current_message: str
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Extract entities from messages and find related content from graph.

        Args:
            messages: List of conversation messages
            current_message: Current message text

        Returns:
            Dict with related entities by type
        """
        if not self.graph_service:
            return {}

        # Extract entity references from messages
        entity_ids = self._extract_entity_ids(messages, current_message)

        related = {
            "issues": [],
            "projects": [],
            "documents": [],
            "milestones": []
        }

        # For each mentioned entity, get related entities from graph
        for entity_type, ids in entity_ids.items():
            for entity_id in ids[:3]:  # Limit to 3 per type
                try:
                    # Search knowledge graph
                    related_results = await self.graph_service.get_related_entities(
                        entity_id=UUID(entity_id),
                        entity_type=entity_type,
                        limit=2
                    )

                    # Fetch full entity details
                    for result in related_results:
                        entity_data = await self._fetch_entity_details(
                            result.entity_type,
                            result.entity_id
                        )
                        if entity_data:
                            related[f"{result.entity_type}s"].append({
                                "id": str(result.entity_id),
                                "relevance": result.relevance_score,
                                **entity_data
                            })

                except Exception as e:
                    logger.debug(f"Failed to get related entities for {entity_type} {entity_id}: {e}")

        return related

    async def _fetch_entity_details(
        self,
        entity_type: str,
        entity_id: UUID
    ) -> dict[str, Any] | None:
        """Fetch full details for an entity from database.

        Args:
            entity_type: Type of entity (issue, project, document, milestone)
            entity_id: UUID of the entity

        Returns:
            Dict with entity details or None if not found
        """
        model_map = {
            "issue": Issue,
            "project": Project,
            "document": Document,
            "milestone": Milestone
        }

        model = model_map.get(entity_type)
        if not model:
            return None

        try:
            result = await self.db.execute(
                select(model).where(model.id == entity_id)
            )
            entity = result.scalar_one_or_none()

            if not entity:
                return None

            # Return basic details
            if entity_type == "issue":
                return {
                    "title": entity.title,
                    "status": entity.status,
                    "priority": entity.priority,
                    "type": entity.type
                }
            elif entity_type == "project":
                return {
                    "name": entity.name,
                    "status": entity.status,
                    "completion_percentage": entity.completion_percentage
                }
            elif entity_type == "document":
                return {
                    "title": entity.title,
                    "type": entity.type
                }
            elif entity_type == "milestone":
                return {
                    "name": entity.name,
                    "status": entity.status,
                    "due_date": entity.due_date.isoformat() if entity.due_date else None
                }

        except Exception as e:
            logger.warning(f"Failed to fetch {entity_type} {entity_id}: {e}")

        return None

    def _extract_entity_ids(
        self,
        messages: list,
        current_message: str
    ) -> dict[str, list[str]]:
        """
        Extract entity UUIDs from message content.

        Looks for patterns like:
        - "issue uuid"
        - "project uuid"
        - "document uuid"
        - "#uuid" (shorthand for issue)

        Args:
            messages: List of message objects
            current_message: Current message text

        Returns:
            Dict mapping entity types to lists of UUIDs
        """
        # UUID regex pattern
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

        entity_ids = {
            "issue": [],
            "project": [],
            "document": [],
            "milestone": []
        }

        # Combine all message content
        all_content = current_message
        for msg in messages[-20:]:  # Only check recent messages
            all_content += " " + (msg.content if hasattr(msg, 'content') else str(msg))

        # Look for entity mentions
        for entity_type in entity_ids.keys():
            # Pattern: "entity_type uuid" or "entity_type: uuid"
            pattern = rf'{entity_type}[:\s]+({uuid_pattern})'
            matches = re.findall(pattern, all_content, re.IGNORECASE)
            entity_ids[entity_type].extend(matches)

            # Also check plural forms
            plural = entity_type + "s"
            pattern_plural = rf'{plural}[:\s]+({uuid_pattern})'
            matches_plural = re.findall(pattern_plural, all_content, re.IGNORECASE)
            entity_ids[entity_type].extend(matches_plural)

        # Look for shorthand patterns
        # "#uuid" usually means issue
        shorthand_pattern = rf'#({uuid_pattern})'
        shorthand_matches = re.findall(shorthand_pattern, all_content)
        entity_ids["issue"].extend(shorthand_matches)

        # Deduplicate
        for key in entity_ids:
            entity_ids[key] = list(set(entity_ids[key]))

        return entity_ids

    def _extract_all_entities(self, messages: list) -> dict[str, list[str]]:
        """
        Extract all entity IDs mentioned in the conversation.

        Args:
            messages: List of message objects

        Returns:
            Dict with all entity IDs by type
        """
        all_text = " ".join([
            (msg.content if hasattr(msg, 'content') else str(msg))
            for msg in messages
        ])

        return self._extract_entity_ids(messages, "")

    async def _get_user_context(
        self,
        entity_type: str,
        entity_id: UUID
    ) -> dict[str, Any]:
        """
        Get user's current work context (active projects, issues).
        For staff with career capabilities, also includes career data.

        Args:
            entity_type: "staff" (mentor is deprecated)
            entity_id: UUID of the staff member

        Returns:
            Dict with user context information
        """
        try:
            context = {}

            # Get active projects
            project_result = await self.db.execute(
                select(Project)
                .where(Project.status == "active")
                .order_by(desc(Project.updated_at))
                .limit(5)
            )
            active_projects = project_result.scalars().all()

            # Get open issues
            issue_result = await self.db.execute(
                select(Issue)
                .where(Issue.status.in_(["open", "in_progress"]))
                .order_by(desc(Issue.updated_at))
                .limit(5)
            )
            active_issues = issue_result.scalars().all()

            context["active_projects"] = [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "status": p.status,
                    "completion": p.completion_percentage
                }
                for p in active_projects
            ]

            context["active_issues"] = [
                {
                    "id": str(i.id),
                    "title": i.title,
                    "status": i.status,
                    "priority": i.priority
                }
                for i in active_issues
            ]

            # For staff with career capabilities, include career data
            staff_result = await self.db.execute(
                select(Staff).where(Staff.id == entity_id)
            )
            staff = staff_result.scalar_one_or_none()

            if staff and staff.capabilities:
                # Check if staff has career-related capabilities
                career_capabilities = [
                    "career_guidance", "resume_review", "interview_prep",
                    "salary_negotiation", "job_search_strategy"
                ]
                has_career_capability = any(
                    cap in staff.capabilities for cap in career_capabilities
                )

                if has_career_capability:
                    max_items = 20

                    # Include job applications
                    app_result = await self.db.execute(
                        select(JobApplication)
                        .order_by(desc(JobApplication.updated_at))
                        .limit(max_items)
                    )
                    applications = app_result.scalars().all()
                    context["job_applications"] = [
                        {
                            "id": str(a.id),
                            "position_title": a.position_title,
                            "company_name": a.company_name,
                            "status": a.status,
                            "application_date": a.application_date.isoformat() if a.application_date else None
                        }
                        for a in applications
                    ]

                    # Include resumes
                    resume_result = await self.db.execute(
                        select(Resume)
                        .order_by(desc(Resume.updated_at))
                        .limit(max_items)
                    )
                    resumes = resume_result.scalars().all()
                    context["resumes"] = [
                        {
                            "id": str(r.id),
                            "title": r.title,
                            "is_primary": r.is_primary,
                            "target_role": r.target_role,
                            "target_company": r.target_company
                        }
                        for r in resumes
                    ]

                    # Include companies
                    company_result = await self.db.execute(
                        select(Company)
                        .order_by(desc(Company.updated_at))
                        .limit(max_items)
                    )
                    companies = company_result.scalars().all()
                    context["companies"] = [
                        {
                            "id": str(c.id),
                            "name": c.name,
                            "target_status": c.target_status,
                            "industry": c.industry,
                            "application_count": c.application_count
                        }
                        for c in companies
                    ]

                    # Include contacts
                    contact_result = await self.db.execute(
                        select(NetworkContact)
                        .where(NetworkContact.is_active == True)
                        .order_by(desc(NetworkContact.updated_at))
                        .limit(max_items)
                    )
                    contacts = contact_result.scalars().all()
                    context["network_contacts"] = [
                        {
                            "id": str(c.id),
                            "name": f"{c.first_name} {c.last_name}",
                            "current_title": c.current_title,
                            "current_company": c.current_company,
                            "contact_type": c.contact_type,
                            "relationship_strength": c.relationship_strength,
                            "referral_status": c.referral_status
                        }
                        for c in contacts
                    ]

            return context

        except Exception as e:
            logger.warning(f"Failed to get user context: {e}", exc_info=True)
            return {"active_projects": [], "active_issues": []}

    def _message_to_dict(self, message: StaffConversation) -> dict[str, Any]:
        """Convert message object to dict."""
        return {
            "id": str(message.id),
            "message_type": message.message_type,
            "content": message.content,
            "created_at": message.created_at.isoformat() if message.created_at else None
        }

    def _summary_to_dict(self, summary: ConversationSummary) -> dict[str, Any]:
        """Convert summary object to dict."""
        return {
            "summary_text": summary.summary_text,
            "message_range": f"{summary.message_range_start}-{summary.message_range_end}",
            "key_topics": summary.key_topics or [],
            "decisions": summary.decisions_made or []
        }

    def _memory_to_dict(self, memory: ConversationMemory) -> dict[str, Any]:
        """Convert memory object to dict."""
        return {
            "type": memory.memory_type,
            "content": memory.content,
            "importance": memory.importance,
            "relevance": memory.relevance_score,
            "first_mentioned": memory.first_mentioned_at.isoformat() if memory.first_mentioned_at else None
        }

    def _empty_context(self) -> dict[str, Any]:
        """Return empty context structure."""
        return {
            "recent_messages": [],
            "conversation_summary": None,
            "key_facts": [],
            "related_entities": {},
            "memories": [],
            "user_context": {"active_projects": [], "active_issues": []},
            "entities_discussed": {},
            "total_message_count": 0,
            "metadata": {
                "has_summary": False,
                "has_old_messages": False,
                "memory_count": 0,
                "related_count": 0
            }
        }

    async def trigger_memory_extraction(
        self,
        entity_type: str,
        entity_id: UUID,
        force: bool = False
    ):
        """
        Trigger memory extraction for a conversation.

        Should be called periodically (e.g., every 10-20 messages).

        Args:
            entity_type: "staff" (mentor is deprecated)
            entity_id: UUID of the staff member
            force: Force extraction even if recently done
        """
        messages = await self._get_messages(entity_type, entity_id, limit=100)

        if len(messages) < 5:
            logger.info("Too few messages for memory extraction")
            return

        # Extract memories from recent messages (last 20)
        recent = messages[-20:]
        await self.memory_service.extract_memories_from_conversation(
            entity_type=entity_type,
            entity_id=entity_id,
            messages=[self._message_to_dict(m) for m in recent],
            min_importance=0.3
        )

        logger.info(f"Triggered memory extraction for {entity_type} {entity_id}")

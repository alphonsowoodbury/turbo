#!/usr/bin/env python3
"""
Claude Webhook Server

Runs on the host machine (outside Docker) and receives webhook requests
from the Turbo API to trigger Claude AI responses to comments via Anthropic API.

Usage:
    python scripts/claude_webhook_server.py

Environment Variables:
    ANTHROPIC_API_KEY: Your Anthropic API key (required)
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any
from uuid import UUID

import httpx
from aiohttp import web

# Add turbo module to path for action detection imports
sys.path.insert(0, '/app')

# Import database and memory services for enhanced context
from turbo.core.database.connection import get_db_session
from turbo.core.services.conversation_context import ConversationContextManager
from turbo.core.services.conversation_memory import ConversationMemoryService
from turbo.core.services.graph import GraphService
try:
    from turbo.core.utils.action_parser import detect_action_intent, should_detect_actions
    from turbo.core.services.action_classifier import ActionClassifier
    ACTION_DETECTION_ENABLED = True
except ImportError:
    # Fallback if imports fail (e.g., running outside Docker)
    logger = logging.getLogger(__name__)
    logger.warning("Action detection modules not available - action detection disabled")
    ACTION_DETECTION_ENABLED = False

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "9002"))
TURBO_API_URL = os.getenv("TURBO_API_URL", "http://localhost:8001/api/v1")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-5-20250929"

# Global API key (fetched from Turbo API at startup)
ANTHROPIC_API_KEY = ""

# Entity type configuration - add new entity types here without code changes
ENTITY_CONFIGS = {
    "document": {
        "api_endpoint": "documents",  # Plural API endpoint
        "entity_name_singular": "document",
        "title_field": "title",
        "description_fields": ["content"],  # Fields to include in prompt
        "has_comments": True,
        "role_description": "Document Reviewer",
        "guidance": [
            "Review document structure and completeness",
            "Suggest improvements to clarity and organization",
            "Identify missing sections or information",
            "Provide actionable feedback on content quality"
        ]
    },
    "issue": {
        "api_endpoint": "issues",
        "entity_name_singular": "issue",
        "title_field": "title",
        "description_fields": ["description", "type", "priority", "status"],
        "has_comments": True,
        "role_description": "Issue Analyst",
        "guidance": [
            "Technical implementation details",
            "Architecture decisions",
            "Best practices",
            "Breaking down complex tasks",
            "Suggesting solutions to problems"
        ]
    },
    "project": {
        "api_endpoint": "projects",
        "entity_name_singular": "project",
        "title_field": "name",
        "description_fields": ["description", "status", "priority", "completion_percentage"],
        "has_comments": True,
        "role_description": "Project Advisor",
        "guidance": [
            "Assess overall project health",
            "Review completion percentage and milestones",
            "Suggest process improvements",
            "Identify dependencies and risks",
            "Recommend resource allocation"
        ]
    },
    "initiative": {
        "api_endpoint": "initiatives",
        "entity_name_singular": "initiative",
        "title_field": "name",
        "description_fields": ["description", "status", "start_date", "target_date"],
        "has_comments": True,
        "role_description": "Initiative Coordinator",
        "guidance": [
            "Define scope and technical approach",
            "Break down into actionable issues",
            "Identify technical dependencies",
            "Recommend architecture patterns",
            "Set success criteria"
        ]
    },
    "blueprint": {
        "api_endpoint": "blueprints",
        "entity_name_singular": "blueprint",
        "title_field": "name",
        "description_fields": ["description", "category", "version"],
        "has_comments": True,
        "role_description": "Blueprint Architect",
        "guidance": [
            "Review technical designs",
            "Suggest architectural patterns",
            "Identify potential issues",
            "Recommend best practices",
            "Guide implementation strategy"
        ]
    },
    "milestone": {
        "api_endpoint": "milestones",
        "entity_name_singular": "milestone",
        "title_field": "name",
        "description_fields": ["description", "status", "start_date", "due_date"],
        "has_comments": True,
        "role_description": "Milestone Tracker",
        "guidance": [
            "Monitor progress toward due dates",
            "Identify risks to on-time delivery",
            "Review associated issues and their status",
            "Suggest actions to keep milestones on track",
            "Coordinate across dependencies"
        ]
    },
    "literature": {
        "api_endpoint": "literature",
        "entity_name_singular": "literature item",
        "title_field": "title",
        "description_fields": ["content", "type", "url", "author"],
        "has_comments": True,
        "role_description": "Knowledge Curator",
        "guidance": [
            "Summarize key concepts",
            "Connect ideas to their projects",
            "Suggest practical applications",
            "Recommend related resources",
            "Facilitate knowledge sharing"
        ]
    }
}


async def fetch_generic_entity_context(entity_type: str, entity_id: str) -> dict[str, Any]:
    """Fetch generic entity details and comment thread from API.

    Works for any entity type configured in ENTITY_CONFIGS.

    Args:
        entity_type: Type of entity (e.g., "document", "issue", "project")
        entity_id: UUID of the entity

    Returns:
        Dict with entity info and formatted comment thread
    """
    config = ENTITY_CONFIGS.get(entity_type)
    if not config:
        raise ValueError(f"No configuration found for entity type: {entity_type}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch entity details
        api_endpoint = config["api_endpoint"]
        entity_response = await client.get(f"{TURBO_API_URL}/{api_endpoint}/{entity_id}")
        entity_response.raise_for_status()
        entity = entity_response.json()

        # Fetch comments if entity supports them
        comment_thread = "_No comments yet_"
        comment_count = 0

        if config.get("has_comments", False):
            comments_response = await client.get(
                f"{TURBO_API_URL}/comments/entity/{entity_type}/{entity_id}"
            )
            comments_response.raise_for_status()
            comments = comments_response.json()

            # Format comment thread
            comment_lines = []
            for comment in comments:
                author = comment.get("author_name", "Unknown")
                author_type = comment.get("author_type", "user")
                content = comment.get("content", "")
                created_at = comment.get("created_at", "")

                role_label = "AI" if author_type == "ai" else "User"
                comment_lines.append(f"**{role_label} ({author})** - {created_at}:\n{content}\n")

            comment_thread = "\n".join(comment_lines) if comment_lines else "_No comments yet_"
            comment_count = len(comments)

        return {
            "entity": entity,
            "entity_type": entity_type,
            "comment_thread": comment_thread,
            "comment_count": comment_count,
        }


async def fetch_api_key_from_api() -> str:
    """Fetch the Anthropic API key from Turbo API internal endpoint.

    This allows the webhook to use the API key configured in the UI
    without requiring it in environment variables.

    Returns:
        API key string, or empty string if not configured
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Fetch from internal raw key endpoint (only accessible from Docker network)
            response = await client.get(f"{TURBO_API_URL}/settings/claude/api-key/raw")

            if response.status_code == 200:
                data = response.json()
                api_key = data.get("api_key")
                if api_key:
                    logger.info("Successfully fetched API key from Turbo API database")
                    return api_key
                else:
                    logger.warning("No API key configured in database")
            else:
                logger.error(f"Failed to fetch API key: HTTP {response.status_code}")

    except Exception as e:
        logger.error(f"Failed to fetch API key from Turbo API: {e}")

    return ""


async def fetch_project_context(project_id: str) -> dict[str, Any]:
    """Fetch project details and comment thread from API.

    Args:
        project_id: UUID of the project

    Returns:
        Dict with project info and formatted comment thread
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch project details
        project_response = await client.get(f"{TURBO_API_URL}/projects/{project_id}")
        project_response.raise_for_status()
        project = project_response.json()

        # Fetch comments using the unified comments endpoint
        comments_response = await client.get(f"{TURBO_API_URL}/comments/entity/project/{project_id}")
        comments_response.raise_for_status()
        comments = comments_response.json()

        # Format comment thread
        comment_lines = []
        for comment in comments:
            author = comment.get("author_name", "Unknown")
            author_type = comment.get("author_type", "user")
            content = comment.get("content", "")
            created_at = comment.get("created_at", "")

            role_label = "AI" if author_type == "ai" else "User"
            comment_lines.append(f"**{role_label} ({author})** - {created_at}:\n{content}\n")

        comment_thread = "\n".join(comment_lines) if comment_lines else "_No comments yet_"

        return {
            "project": project,
            "comment_thread": comment_thread,
            "comment_count": len(comments),
        }


async def fetch_issue_context(issue_id: str) -> dict[str, Any]:
    """Fetch issue details and comment thread from API.

    Args:
        issue_id: UUID of the issue

    Returns:
        Dict with issue info and formatted comment thread
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch issue details
        issue_response = await client.get(f"{TURBO_API_URL}/issues/{issue_id}")
        issue_response.raise_for_status()
        issue = issue_response.json()

        # Fetch comments using the unified comments endpoint
        comments_response = await client.get(f"{TURBO_API_URL}/comments/entity/issue/{issue_id}")
        comments_response.raise_for_status()
        comments = comments_response.json()

        # Format comment thread
        comment_lines = []
        for comment in comments:
            author = comment.get("author_name", "Unknown")
            author_type = comment.get("author_type", "user")
            content = comment.get("content", "")
            created_at = comment.get("created_at", "")

            role_label = "AI" if author_type == "ai" else "User"
            comment_lines.append(f"**{role_label} ({author})** - {created_at}:\n{content}\n")

        comment_thread = "\n".join(comment_lines) if comment_lines else "_No comments yet_"

        return {
            "issue": issue,
            "comment_thread": comment_thread,
            "comment_count": len(comments),
        }


async def fetch_mentor_context(mentor_id: str) -> dict[str, Any]:
    """Fetch mentor details and conversation history from API.

    Args:
        mentor_id: UUID of the mentor

    Returns:
        Dict with mentor info and formatted conversation history
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch mentor details
        mentor_response = await client.get(f"{TURBO_API_URL}/mentors/{mentor_id}")
        mentor_response.raise_for_status()
        mentor = mentor_response.json()

        # Fetch conversation history (last 20 messages)
        messages_response = await client.get(
            f"{TURBO_API_URL}/mentors/{mentor_id}/messages",
            params={"limit": 20}
        )
        messages_response.raise_for_status()
        messages_data = messages_response.json()
        messages = messages_data.get("messages", [])

        # Format conversation history
        conversation_lines = []
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Mentor"
            conversation_lines.append(f"**{role}:** {msg['content']}\n")

        conversation_history = "\n".join(conversation_lines) if conversation_lines else "_No previous conversation_"

        return {
            "mentor": mentor,
            "conversation_history": conversation_history,
            "message_count": len(messages),
        }


async def fetch_enhanced_mentor_context(mentor_id: str) -> dict[str, Any]:
    """
    Fetch enhanced mentor context with memory, knowledge graph, and career data.

    This replaces the old fetch_mentor_context function for mentors that need
    access to career management data (applications, resumes, companies, contacts).

    Args:
        mentor_id: UUID of the mentor

    Returns:
        Dict with mentor info, enhanced context, and metadata
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch mentor details
        mentor_response = await client.get(f"{TURBO_API_URL}/mentors/{mentor_id}")
        mentor_response.raise_for_status()
        mentor = mentor_response.json()

        # Get messages to determine if we need enhanced context
        messages_response = await client.get(
            f"{TURBO_API_URL}/mentors/{mentor_id}/messages",
            params={"limit": 100}
        )
        messages_response.raise_for_status()
        messages_data = messages_response.json()
        messages = messages_data.get("messages", [])

        if not messages:
            return {
                "mentor": mentor,
                "context": None,
                "conversation_history": "_No previous conversation_",
                "message_count": 0
            }

        # Use async generator to get database session
        async for db in get_db_session():
            try:
                # Initialize services
                graph_service = GraphService()
                memory_service = ConversationMemoryService(db, ANTHROPIC_API_KEY)
                context_manager = ConversationContextManager(db, memory_service, graph_service)

                # Get current message
                current_message = messages[-1]["content"] if messages else ""

                # Build enhanced context (includes career data based on context_preferences)
                context = await context_manager.build_context(
                    entity_type="mentor",
                    entity_id=UUID(mentor_id),
                    current_message=current_message
                )

                # Trigger memory extraction every 10 messages
                if len(messages) % 10 == 0 and len(messages) > 0:
                    await context_manager.trigger_memory_extraction(
                        entity_type="mentor",
                        entity_id=UUID(mentor_id)
                    )

                return {
                    "mentor": mentor,
                    "context": context,
                    "message_count": len(messages)
                }

            except Exception as e:
                logger.error(f"Failed to build enhanced mentor context: {e}", exc_info=True)
                # Fallback to basic context
                conversation_lines = []
                for msg in messages[-20:]:
                    role = "User" if msg["role"] == "user" else "Mentor"
                    conversation_lines.append(f"**{role}:** {msg['content']}\n")

                conversation_history = "\n".join(conversation_lines) if conversation_lines else "_No previous conversation_"

                return {
                    "mentor": mentor,
                    "context": None,
                    "conversation_history": conversation_history,
                    "message_count": len(messages)
                }

            finally:
                # Make sure to break after first iteration
                break


async def fetch_enhanced_staff_context(staff_id: str) -> dict[str, Any]:
    """
    Fetch enhanced context with memory and knowledge graph integration.

    This replaces the old fetch_staff_context function.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch staff details
        staff_response = await client.get(f"{TURBO_API_URL}/staff/{staff_id}")
        staff_response.raise_for_status()
        staff = staff_response.json()

        # Get messages to determine if we need enhanced context
        messages_response = await client.get(
            f"{TURBO_API_URL}/staff/{staff_id}/messages",
            params={"limit": 100}
        )
        messages_response.raise_for_status()
        messages_data = messages_response.json()
        messages = messages_data.get("messages", [])

        if not messages:
            return {
                "staff": staff,
                "context": None,
                "conversation_history": "_No previous conversation_",
                "message_count": 0
            }

        # Use async generator to get database session
        async for db in get_db_session():
            try:
                # Initialize services
                graph_service = GraphService()
                memory_service = ConversationMemoryService(db, ANTHROPIC_API_KEY)
                context_manager = ConversationContextManager(db, memory_service, graph_service)

                # Get current message
                current_message = messages[-1]["content"] if messages else ""

                # Build enhanced context
                context = await context_manager.build_context(
                    entity_type="staff",
                    entity_id=UUID(staff_id),
                    current_message=current_message
                )

                # Trigger memory extraction every 10 messages
                if len(messages) % 10 == 0 and len(messages) > 0:
                    await context_manager.trigger_memory_extraction(
                        entity_type="staff",
                        entity_id=UUID(staff_id)
                    )

                return {
                    "staff": staff,
                    "context": context,
                    "message_count": len(messages)
                }

            except Exception as e:
                logger.error(f"Failed to build enhanced context: {e}", exc_info=True)
                # Fallback to basic context
                conversation_lines = []
                for msg in messages[-20:]:
                    role = "User" if msg["message_type"] == "user" else "Staff"
                    conversation_lines.append(f"**{role}:** {msg['content']}\n")

                conversation_history = "\n".join(conversation_lines) if conversation_lines else "_No previous conversation_"

                return {
                    "staff": staff,
                    "context": None,
                    "conversation_history": conversation_history,
                    "message_count": len(messages)
                }

            finally:
                # Make sure to break after first iteration
                break


async def fetch_initiative_context(initiative_id: str) -> dict[str, Any]:
    """Fetch initiative details and comment thread from API.

    Args:
        initiative_id: UUID of the initiative

    Returns:
        Dict with initiative info and formatted comment thread
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch initiative details
        initiative_response = await client.get(f"{TURBO_API_URL}/initiatives/{initiative_id}")
        initiative_response.raise_for_status()
        initiative = initiative_response.json()

        # Fetch comments using the unified comments endpoint
        comments_response = await client.get(f"{TURBO_API_URL}/comments/entity/initiative/{initiative_id}")
        comments_response.raise_for_status()
        comments = comments_response.json()

        # Format comment thread
        comment_lines = []
        for comment in comments:
            author = comment.get("author_name", "Unknown")
            author_type = comment.get("author_type", "user")
            content = comment.get("content", "")
            created_at = comment.get("created_at", "")

            role_label = "AI" if author_type == "ai" else "User"
            comment_lines.append(f"**{role_label} ({author})** - {created_at}:\n{content}\n")

        comment_thread = "\n".join(comment_lines) if comment_lines else "_No comments yet_"

        return {
            "initiative": initiative,
            "comment_thread": comment_thread,
            "comment_count": len(comments),
        }


def build_enhanced_staff_prompt(staff: dict, context: dict) -> str:
    """
    Build enhanced staff prompt with full context integration.

    Args:
        staff: Staff member data
        context: Enhanced context from ConversationContextManager

    Returns:
        Formatted user prompt
    """
    staff_name = staff.get("name", "Unknown")
    staff_persona = staff.get("persona", "")
    staff_role = staff.get("role_type", "leadership")
    staff_capabilities = staff.get("capabilities", [])

    # 1. Format recent messages
    recent_messages = context.get("recent_messages", [])
    recent_text = "\n\n".join([
        f"**{'User' if msg['message_type'] == 'user' else 'Staff'}:** {msg['content']}"
        for msg in recent_messages
    ])

    # 2. Format conversation summary (if available)
    summary = context.get("conversation_summary")
    summary_text = ""
    if summary:
        summary_text = f"""
## Previous Conversation Summary (Messages {summary['message_range']})

{summary['summary_text']}

**Key Topics Discussed**: {', '.join(summary.get('key_topics', []))}
"""
        if summary.get('decisions'):
            summary_text += f"\n**Decisions Made**: {', '.join(summary['decisions'])}\n"

    # 3. Format long-term memories
    memories = context.get("memories", [])
    memory_text = ""
    if memories:
        memory_items = "\n".join([
            f"- **[{m['type'].upper()}]** {m['content']} (importance: {m['importance']:.1f}, relevance: {m['relevance']:.1f})"
            for m in memories
        ])
        memory_text = f"""
## Long-term Memory & Key Facts

{memory_items}
"""

    # 4. Format related entities from knowledge graph
    related = context.get("related_entities", {})
    related_text = ""
    if any(related.values()):
        related_text = "## Related Work Context\n\n"

        for entity_type, entities in related.items():
            if entities:
                related_text += f"**Related {entity_type.title()}**:\n"
                for entity in entities[:3]:  # Limit to top 3
                    if entity_type == "issues":
                        related_text += f"  - {entity.get('title', 'Unknown')} [{entity.get('status', '')}] (priority: {entity.get('priority', 'medium')})\n"
                    elif entity_type == "projects":
                        related_text += f"  - {entity.get('name', 'Unknown')} [{entity.get('status', '')}] ({entity.get('completion', 0)}% complete)\n"
                    elif entity_type == "documents":
                        related_text += f"  - {entity.get('title', 'Unknown')} ({entity.get('type', 'document')})\n"
                    elif entity_type == "milestones":
                        due = entity.get('due_date', 'No due date')
                        related_text += f"  - {entity.get('name', 'Unknown')} [due: {due}]\n"
                related_text += "\n"

    # 5. Format user's active work
    user_context = context.get("user_context", {})
    active_work_text = ""
    if user_context.get("active_projects") or user_context.get("active_issues"):
        active_work_text = "## Current Active Work\n\n"

        if user_context.get("active_projects"):
            active_work_text += "**Active Projects**:\n"
            for proj in user_context["active_projects"][:3]:
                active_work_text += f"  - {proj['name']} [{proj['status']}] ({proj.get('completion', 0)}% complete)\n"
            active_work_text += "\n"

        if user_context.get("active_issues"):
            active_work_text += "**In-Progress Issues**:\n"
            for issue in user_context["active_issues"][:3]:
                active_work_text += f"  - {issue['title']} [{issue['status']}] (priority: {issue['priority']})\n"
            active_work_text += "\n"

    # 6. Build final prompt
    metadata = context.get("metadata", {})
    context_stats = f"(Total messages: {context.get('total_message_count', 0)}, Memories: {metadata.get('memory_count', 0)}, Related entities: {metadata.get('related_count', 0)})"

    user_prompt = f"""A user has sent you a message. You are "{staff_name}", a {staff_role} staff member.

## Your Identity & Role

**Name**: {staff_name}
**Role**: {staff_role.replace('_', ' ').title()}

**Your Persona**:
{staff_persona}

**Your Capabilities**:
{', '.join(staff_capabilities) if staff_capabilities else 'General guidance and support'}

{summary_text}

{memory_text}

{related_text}

{active_work_text}

## Recent Conversation {context_stats}

{recent_text}

---

## Your Task

Respond to the user's latest message with:
- **Full awareness** of conversation history, summaries, and long-term memories
- **Reference to relevant context** when appropriate (past discussions, related work, decisions)
- **Integration of knowledge graph insights** (related entities, similar issues, connected projects)
- **Your characteristic persona** and communication style
- **Actionable guidance** within your domain expertise

**Context Note**: You have access to {context.get('total_message_count', 0)} total messages. The recent messages above are the latest exchange, but you also have summaries and memories from earlier parts of the conversation.

**Important**: All context is already provided above - respond directly without fetching additional data unless using your allowed tools.
"""

    return user_prompt


def build_basic_staff_prompt(staff: dict, conversation_history: str) -> str:
    """
    Build basic staff prompt (fallback when enhanced context unavailable).

    Args:
        staff: Staff member data
        conversation_history: Formatted conversation history string

    Returns:
        Formatted user prompt
    """
    staff_name = staff.get("name", "Unknown")
    staff_persona = staff.get("persona", "")
    staff_role = staff.get("role_type", "leadership")
    staff_capabilities = staff.get("capabilities", [])

    user_prompt = f"""A user has sent you a message. You are "{staff_name}", a {staff_role} staff member.

## Your Persona
{staff_persona}

## Your Capabilities
{', '.join(staff_capabilities) if staff_capabilities else 'General guidance'}

## Conversation History (Last 20 Messages)
{conversation_history}

## Your Task
Respond to the user's latest message as {staff_name}:
- Match the persona and communication style defined above
- Build naturally on the conversation history
- Provide expert guidance within your domain and capabilities
- Be direct, actionable, and professional
- Reference specific context when helpful

**Important**: The conversation history above is already complete - you do NOT need to call get_staff or get_staff_messages. Just respond based on the context provided.
"""

    return user_prompt


def build_enhanced_mentor_prompt(mentor: dict, context: dict) -> str:
    """
    Build enhanced mentor prompt with career data and full context integration.

    Args:
        mentor: Mentor data
        context: Enhanced context from ConversationContextManager (includes career data)

    Returns:
        Formatted user prompt
    """
    mentor_name = mentor.get("name", "Unknown")
    mentor_persona = mentor.get("persona", "")
    mentor_workspace = mentor.get("workspace", "personal")

    # 1. Format recent messages
    recent_messages = context.get("recent_messages", [])
    recent_text = "\n\n".join([
        f"**{'User' if msg.get('role') == 'user' else 'Mentor'}:** {msg['content']}"
        for msg in recent_messages
    ])

    # 2. Format conversation summary (if available)
    summary = context.get("conversation_summary")
    summary_text = ""
    if summary:
        summary_text = f"""
## Previous Conversation Summary (Messages {summary['message_range']})

{summary['summary_text']}

**Key Topics Discussed**: {', '.join(summary.get('key_topics', []))}
"""
        if summary.get('decisions'):
            summary_text += f"\n**Decisions Made**: {', '.join(summary['decisions'])}\n"

    # 3. Format long-term memories
    memories = context.get("memories", [])
    memory_text = ""
    if memories:
        memory_items = "\n".join([
            f"- **[{m['type'].upper()}]** {m['content']} (importance: {m['importance']:.1f})"
            for m in memories
        ])
        memory_text = f"""
## Long-term Memory & Key Facts

{memory_items}
"""

    # 4. Format user's active work
    user_context = context.get("user_context", {})
    career_data_text = ""

    # Career-specific data (for Career Coach and similar mentors)
    if user_context.get("job_applications"):
        career_data_text += "\n## Job Applications\n\n"
        for app in user_context["job_applications"][:10]:
            career_data_text += f"  - **{app['position_title']}** at {app['company_name']} [{app['status']}]"
            if app.get('application_date'):
                career_data_text += f" (applied: {app['application_date']})"
            career_data_text += "\n"

    if user_context.get("resumes"):
        career_data_text += "\n## Resumes\n\n"
        for resume in user_context["resumes"][:5]:
            career_data_text += f"  - {resume['title']}"
            if resume.get('is_primary'):
                career_data_text += " **(PRIMARY)**"
            if resume.get('target_role') or resume.get('target_company'):
                career_data_text += f" - targeting: {resume.get('target_role', 'any role')} at {resume.get('target_company', 'any company')}"
            career_data_text += "\n"

    if user_context.get("companies"):
        career_data_text += "\n## Companies Tracking\n\n"
        for company in user_context["companies"][:10]:
            career_data_text += f"  - **{company['name']}** [{company['target_status']}]"
            if company.get('industry'):
                career_data_text += f" - {company['industry']}"
            if company.get('application_count', 0) > 0:
                career_data_text += f" ({company['application_count']} applications)"
            career_data_text += "\n"

    if user_context.get("network_contacts"):
        career_data_text += "\n## Network Contacts\n\n"
        for contact in user_context["network_contacts"][:10]:
            career_data_text += f"  - **{contact['name']}**"
            if contact.get('current_title'):
                career_data_text += f" - {contact['current_title']}"
            if contact.get('current_company'):
                career_data_text += f" at {contact['current_company']}"
            career_data_text += f" [{contact['relationship_strength']} relationship, {contact['contact_type']}]"
            if contact.get('referral_status') and contact['referral_status'] != 'none':
                career_data_text += f" (referral: {contact['referral_status']})"
            career_data_text += "\n"

    # Standard work context (projects and issues)
    work_context_text = ""
    if user_context.get("active_projects") or user_context.get("active_issues"):
        work_context_text = "\n## Current Active Work\n\n"

        if user_context.get("active_projects"):
            work_context_text += "**Active Projects**:\n"
            for proj in user_context["active_projects"][:3]:
                work_context_text += f"  - {proj['name']} [{proj['status']}] ({proj.get('completion', 0)}% complete)\n"

        if user_context.get("active_issues"):
            work_context_text += "\n**In-Progress Issues**:\n"
            for issue in user_context["active_issues"][:3]:
                work_context_text += f"  - {issue['title']} [{issue['status']}] (priority: {issue['priority']})\n"

    # 5. Build final prompt
    metadata = context.get("metadata", {})
    context_stats = f"(Total messages: {context.get('total_message_count', 0)}, Memories: {metadata.get('memory_count', 0)})"

    user_prompt = f"""A user has sent a message to their mentor "{mentor_name}".

## Mentor Persona

{mentor_persona}

## Workspace

{mentor_workspace}

{summary_text}

{memory_text}

{career_data_text}

{work_context_text}

## Recent Conversation {context_stats}

{recent_text}

---

## Your Task

Respond to the user's latest message as this mentor:
1. Use the MCP tool `add_mentor_message` with mentor_id to post your response
2. Your response should:
   - **Match the mentor's persona and communication style** defined above
   - **Leverage all available context**: career data, work progress, conversation history, and memories
   - **Provide personalized, data-driven guidance** based on their specific situation
   - **Be conversational and supportive** while being honest and actionable
   - **Reference specific context** when helpful (e.g., their applications, network contacts, current projects)
   - **Use web search** when you need current information, industry trends, or specific company/role details

**Context Note**: You have access to {context.get('total_message_count', 0)} total messages plus comprehensive career and work data. The information above represents their complete tracked career search and professional development activities.

**Important**: All context is already provided above - respond directly using the `add_mentor_message` tool. Use WebSearch only when you need current external information.
"""

    return user_prompt


def build_basic_mentor_prompt(mentor: dict, conversation_history: str) -> str:
    """
    Build basic mentor prompt (fallback when enhanced context unavailable).

    Args:
        mentor: Mentor data
        conversation_history: Formatted conversation history string

    Returns:
        Formatted user prompt
    """
    mentor_name = mentor.get("name", "Unknown")
    mentor_persona = mentor.get("persona", "")
    mentor_workspace = mentor.get("workspace", "personal")

    user_prompt = f"""A user has sent a message to their mentor "{mentor_name}".

## Mentor Persona
{mentor_persona}

## Workspace
{mentor_workspace}

## Conversation History (Last 20 Messages)
{conversation_history}

## Your Task
Please respond to the user's latest message as this mentor:
1. Use the MCP tool `add_mentor_message` to post your response
2. Your response should:
   - Match the mentor's persona and communication style defined above
   - Build naturally on the conversation history
   - Be conversational and supportive
   - Provide actionable guidance relevant to their work
   - Reference specific context when helpful
   - Use web search when you need current information, industry trends, or specific technical details

**Important**: The conversation history above is already complete - you do NOT need to call get_mentor or get_mentor_messages. Just respond based on the context provided.
"""

    return user_prompt


def build_entity_prompt(entity_type: str, entity_id: str, extra_context: dict[str, Any] | None = None) -> tuple[str, str, list[str]]:
    """Build entity-specific prompt, system prompt, and allowed tools.

    Args:
        entity_type: Type of entity (issue, project, milestone, initiative, literature, blueprint)
        entity_id: UUID of the entity

    Returns:
        Tuple of (user_prompt, system_prompt, allowed_tools)
    """
    # Common system prompt with project context
    base_system_prompt = """You are an AI assistant integrated into Turbo, a project management platform.

**Project Context:**
Turbo is a modern project management system built with:
- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Frontend: Next.js + React + TypeScript + Tailwind CSS
- CLI: Typer + Rich
- Integration: Claude Code via MCP (Model Context Protocol)

**Action Approval System:**
You can express intent to take actions (like closing issues, updating status, adding tags, etc.).
When you express intent using phrases like "I'll close this issue" or "I'll update the priority to high",
your actions are automatically detected and queued for human approval. Once approved, they execute safely.

**Guidelines:**
- Be concise but thorough
- Express intent to take helpful actions when appropriate (e.g., "I'll close this issue")
- Suggest concrete next steps when appropriate
- If you don't have enough context, ask clarifying questions
- Do NOT use emojis in your responses
"""

    if entity_type == "issue":
        # Extract pre-fetched context
        issue = extra_context.get("issue", {}) if extra_context else {}
        comment_thread = extra_context.get("comment_thread", "_No comments yet_") if extra_context else "_No comments yet_"
        staff = extra_context.get("staff") if extra_context else None

        issue_title = issue.get("title", "Unknown")
        issue_type = issue.get("type", "unknown")
        issue_priority = issue.get("priority", "unknown")
        issue_status = issue.get("status", "unknown")
        issue_description = issue.get("description", "")

        # Use staff persona if staff was mentioned
        if staff:
            staff_name = staff.get("name", "Unknown")
            staff_persona = staff.get("persona", "")
            staff_role = staff.get("role_type", "leadership")
            staff_capabilities = staff.get("capabilities", [])
            staff_monitoring_scope = staff.get("monitoring_scope", {})

            user_prompt = f"""A user has @mentioned you in a comment on an issue. You are "{staff_name}", a {staff_role} staff member.

## Your Persona
{staff_persona}

## Your Capabilities
{', '.join(staff_capabilities) if staff_capabilities else 'General guidance'}

## Your Monitoring Scope
- Focus: {staff_monitoring_scope.get('focus', 'General')}
- Entity Types: {', '.join(staff_monitoring_scope.get('entity_types', []))}
- Metrics: {', '.join(staff_monitoring_scope.get('metrics', []))}

## Issue Details
**Title:** {issue_title}
**Type:** {issue_type}
**Priority:** {issue_priority}
**Status:** {issue_status}

**Description:**
{issue_description}

## Comment Thread
{comment_thread}

## Your Task
Respond to the user's latest comment as {staff_name}:
- Match your persona and communication style defined above
- Provide expert guidance within your domain and capabilities
- Be direct, actionable, and professional
- Consider the issue type, priority, and status
- Reference specific context when helpful

**Important:** The issue details and comment thread are complete - respond based on the context provided.
"""
            system_prompt = base_system_prompt + f"""
**Your Role as {staff_name}:**
You are a {staff_role} staff member in the organization. Adopt the persona and capabilities defined above to provide expert guidance on this issue.
"""
        else:
            user_prompt = f"""A user has @mentioned you in a comment on an issue.

## Issue Details
**Title:** {issue_title}
**Type:** {issue_type}
**Priority:** {issue_priority}
**Status:** {issue_status}

**Description:**
{issue_description}

## Comment Thread
{comment_thread}

## Your Task
Please respond to the user's latest comment. Your response should be:
- Helpful and actionable
- Relevant to the issue context (type, priority, status)
- Professional and concise
- Based on the full conversation thread above
- Provide specific technical guidance, suggestions, or next steps

**Important:** The issue details and comment thread above are already complete - you do NOT need to fetch any data. Just analyze the context and provide your response directly.
"""
            system_prompt = base_system_prompt + """
**Your Role for Issues:**
When users comment on issues, you provide expert guidance on:
- Technical implementation details
- Architecture decisions
- Best practices
- Breaking down complex tasks
- Suggesting solutions to problems

**Issue-Specific Context:**
- Consider the issue type (feature/bug/task/enhancement/documentation/discovery)
- Respect the priority level (low/medium/high/critical)
- Check current status (open/in_progress/review/testing/closed)
"""
        allowed_tools = []

    elif entity_type == "project":
        # Extract pre-fetched context
        project = extra_context.get("project", {}) if extra_context else {}
        comment_thread = extra_context.get("comment_thread", "_No comments yet_") if extra_context else "_No comments yet_"

        project_name = project.get("name", "Unknown")
        project_status = project.get("status", "unknown")
        project_priority = project.get("priority", "unknown")
        project_description = project.get("description", "")
        completion_percentage = project.get("completion_percentage", 0)

        user_prompt = f"""A user has @mentioned you in a comment on a project.

## Project Details
**Name:** {project_name}
**Status:** {project_status}
**Priority:** {project_priority}
**Completion:** {completion_percentage}%

**Description:**
{project_description}

## Comment Thread
{comment_thread}

## Your Task
Please respond to the user's latest comment. Your response should provide insights on:
- Project progress and completion status
- Overall health and any blockers
- Strategic recommendations
- Resource allocation suggestions
- Specific actionable next steps

**Important:** The project details and comment thread above are already complete - you do NOT need to fetch any data. Just analyze the context and provide your response directly.
"""
        system_prompt = base_system_prompt + """
**Your Role for Projects:**
You help with project-level strategic planning and oversight:
- Assess overall project health
- Review completion percentage and milestones
- Suggest process improvements
- Identify dependencies and risks
- Recommend resource allocation
"""
        allowed_tools = []

    elif entity_type == "milestone":
        user_prompt = f"""A user has @mentioned you in a comment on milestone {entity_id}.

Please:
1. Use the MCP tool `get_milestone` with milestone_id: {entity_id} to read the milestone details
2. Use the MCP tool `get_milestone_issues` with milestone_id: {entity_id} to see associated issues
3. Use the MCP tool `get_entity_comments` with entity_type: "milestone" and entity_id: {entity_id} to read all comments
4. Use the MCP tool `add_comment` to post your response with entity_type: "milestone" and entity_id: {entity_id}

Your response should address:
- Milestone progress toward due date
- Risk assessment for on-time delivery
- Blocking issues or dependencies
- Recommendations for achieving milestone goals
"""
        system_prompt = base_system_prompt + """
**Your Role for Milestones:**
You help with milestone planning and tracking:
- Monitor progress toward due dates
- Identify risks to on-time delivery
- Review associated issues and their status
- Suggest actions to keep milestones on track
- Coordinate across dependencies
"""
        allowed_tools = ["mcp__turbo__get_milestone", "mcp__turbo__get_milestone_issues", "mcp__turbo__get_entity_comments", "mcp__turbo__add_comment"]

    elif entity_type == "initiative":
        # Extract pre-fetched context
        initiative = extra_context.get("initiative", {}) if extra_context else {}
        comment_thread = extra_context.get("comment_thread", "_No comments yet_") if extra_context else "_No comments yet_"
        staff = extra_context.get("staff") if extra_context else None

        initiative_name = initiative.get("name", "Unknown")
        initiative_description = initiative.get("description", "")
        initiative_status = initiative.get("status", "unknown")
        start_date = initiative.get("start_date", "Not set")
        target_date = initiative.get("target_date", "Not set")

        # Use staff persona if staff was mentioned
        if staff:
            staff_name = staff.get("name", "Unknown")
            staff_persona = staff.get("persona", "")
            staff_role = staff.get("role_type", "leadership")
            staff_capabilities = staff.get("capabilities", [])
            staff_monitoring_scope = staff.get("monitoring_scope", {})

            user_prompt = f"""A user has @mentioned you in a comment on an initiative. You are "{staff_name}", a {staff_role} staff member.

## Your Persona
{staff_persona}

## Your Capabilities
{', '.join(staff_capabilities) if staff_capabilities else 'General guidance'}

## Your Monitoring Scope
- Focus: {staff_monitoring_scope.get('focus', 'General')}
- Entity Types: {', '.join(staff_monitoring_scope.get('entity_types', []))}
- Metrics: {', '.join(staff_monitoring_scope.get('metrics', []))}

## Initiative Details
**Name:** {initiative_name}
**Status:** {initiative_status}
**Start Date:** {start_date}
**Target Date:** {target_date}

**Description:**
{initiative_description}

## Comment Thread
{comment_thread}

## Your Task
Respond to the user's latest comment as {staff_name}:
- Match your persona and communication style defined above
- Provide expert guidance within your domain and capabilities
- Be direct, actionable, and professional
- Address the user's specific question or concern directly
- Consider the initiative status, timeline, and scope
- Reference specific context when helpful

**Important:** The initiative details and comment thread are complete - respond based on the context provided.
"""
            system_prompt = base_system_prompt + f"""
**Your Role as {staff_name}:**
You are a {staff_role} staff member in the organization. Adopt the persona and capabilities defined above to provide expert guidance on this initiative.
"""
        else:
            user_prompt = f"""A user has @mentioned you in a comment on an initiative.

## Initiative Details
**Name:** {initiative_name}
**Status:** {initiative_status}
**Start Date:** {start_date}
**Target Date:** {target_date}

**Description:**
{initiative_description}

## Comment Thread
{comment_thread}

## Your Task
Please respond to the user's latest comment. Your response should:
- Answer the user's specific question or address their concern directly
- Provide insights on initiative scope and strategic alignment
- Offer guidance on technical approach and architecture
- Suggest actionable next steps
- Be concise, professional, and helpful

**Important:** The initiative details and comment thread above are already complete - you do NOT need to fetch any data. Just analyze the context and provide your response directly.
"""
            system_prompt = base_system_prompt + """
**Your Role for Initiatives:**
You help with feature/technology initiative planning:
- Define scope and technical approach
- Break down into actionable issues
- Identify technical dependencies
- Recommend architecture patterns
- Set success criteria
"""
        allowed_tools = []

    elif entity_type == "literature":
        user_prompt = f"""A user has @mentioned you in a comment on a literature item {entity_id}.

Please:
1. Use the MCP tool `get_literature` with literature_id: {entity_id} to read the article/podcast/book details
2. Use the MCP tool `get_entity_comments` with entity_type: "literature" and entity_id: {entity_id} to read all comments
3. Analyze the content and respond to the user's question
4. Use the MCP tool `add_comment` to post your response with entity_type: "literature" and entity_id: {entity_id}

Your response should provide:
- Key insights from the literature
- Connections to their projects or work
- Actionable takeaways
- Related concepts or further reading
"""
        system_prompt = base_system_prompt + """
**Your Role for Literature:**
You help users extract value from articles, podcasts, books, and papers:
- Summarize key concepts
- Connect ideas to their projects
- Suggest practical applications
- Recommend related resources
- Facilitate knowledge sharing
"""
        allowed_tools = ["mcp__turbo__get_literature", "mcp__turbo__get_entity_comments", "mcp__turbo__add_comment"]

    elif entity_type == "blueprint":
        user_prompt = f"""A user has @mentioned you in a comment on a blueprint {entity_id}.

Please:
1. Use the MCP tool `get_blueprint` with blueprint_id: {entity_id} to read the blueprint details
2. Use the MCP tool `get_entity_comments` with entity_type: "blueprint" and entity_id: {entity_id} to read all comments
3. Analyze the blueprint and respond to the user's question
4. Use the MCP tool `add_comment` to post your response with entity_type: "blueprint" and entity_id: {entity_id}

Your response should provide:
- Technical guidance on the blueprint
- Architecture recommendations
- Implementation suggestions
- Risk assessment
"""
        system_prompt = base_system_prompt + """
**Your Role for Blueprints:**
You help with technical blueprints and architecture planning:
- Review technical designs
- Suggest architectural patterns
- Identify potential issues
- Recommend best practices
- Guide implementation strategy
"""
        allowed_tools = ["mcp__turbo__get_blueprint", "mcp__turbo__get_entity_comments", "mcp__turbo__add_comment"]

    elif entity_type == "mentor":
        # Extract pre-fetched context
        mentor = extra_context.get("mentor", {}) if extra_context else {}
        context = extra_context.get("context")

        # Build prompt based on whether we have enhanced context
        if context:
            # Enhanced context with memory, knowledge graph, and career data
            user_prompt = build_enhanced_mentor_prompt(mentor, context)
        else:
            # Fallback to basic context
            conversation_history = extra_context.get("conversation_history", "_No previous conversation_")
            user_prompt = build_basic_mentor_prompt(mentor, conversation_history)

        system_prompt = base_system_prompt + """
**Your Role for Mentors:**
You act as a personalized AI mentor for the user:
- Adopt the mentor's defined persona and communication style
- Use workspace context (projects, issues, documents, career data) to give specific, personalized guidance
- Provide coaching, feedback, and strategic advice
- Help with career development and technical growth
- Be supportive and encouraging while being honest
- Use web search to find current information, best practices, industry trends, or specific technical details

**Internet Access:**
You have access to web search via the WebSearch tool. Use it when:
- User asks about current events, trends, or recent developments
- You need up-to-date information about technologies, tools, or frameworks
- Looking for specific examples, documentation, or best practices
- Researching company information, industry standards, market data, or salary information
- Finding relevant articles, tutorials, or resources
- Getting details about specific job opportunities or companies

**Important Guidelines:**
- Read the mentor's persona carefully and embody it in your responses
- Reference specific projects, issues, applications, or contacts from their data
- Leverage career data (applications, resumes, companies, contacts) for personalized guidance
- Ask clarifying questions when needed
- Provide actionable next steps
- Remember conversation context and long-term memories
- Search the web proactively when it would enhance your guidance
"""
        # Include web search for mentors to access current information
        allowed_tools = ["mcp__turbo__add_mentor_message", "WebSearch"]

    elif entity_type == "staff":
        staff = extra_context.get("staff", {}) if extra_context else {}
        context = extra_context.get("context")
        allowed_tools_from_db = staff.get("allowed_tools", ["list_projects", "get_project", "create_document"])

        staff_name = staff.get("name", "Unknown")
        staff_role = staff.get("role_type", "leadership")

        # Build prompt based on whether we have enhanced context
        if context:
            # Enhanced context with memory and knowledge graph
            user_prompt = build_enhanced_staff_prompt(staff, context)
        else:
            # Fallback to basic context
            conversation_history = extra_context.get("conversation_history", "_No previous conversation_")
            user_prompt = build_basic_staff_prompt(staff, conversation_history)

        system_prompt = base_system_prompt + f"""
**Your Role as {staff_name}:**
You are a {staff_role} staff member in the organization:
- Adopt the staff member's defined persona and communication style
- Provide expert guidance within your domain
- Be direct, professional, and action-oriented
- Help coordinate work and remove blockers
- Provide strategic and tactical guidance
- You can discover projects and create documents - use list_projects to find project IDs, then create_document to produce deliverables
"""

        allowed_tools = allowed_tools_from_db

    elif entity_type == "resume":
        user_prompt = f"""A user has uploaded a resume (ID: {entity_id}) that needs structured data extraction.

Please:
1. Use the MCP tool `get_resume` with resume_id: {entity_id} to read the resume text and sections
2. Analyze the content and extract structured data
3. Use the MCP tool `update_resume` with resume_id: {entity_id} to save the extracted data

Extract the following structured data in JSON format:
{{
  "personal": {{
    "name": "Full name",
    "email": "Email address",
    "phone": "Phone number",
    "linkedin": "LinkedIn URL",
    "github": "GitHub URL",
    "website": "Personal website",
    "location": "City, State/Country"
  }},
  "summary": "Professional summary (single paragraph)",
  "experience": [
    {{
      "company": "Company name",
      "title": "Job title",
      "location": "Location",
      "start_date": "Start date (YYYY-MM or YYYY)",
      "end_date": "End date (YYYY-MM or YYYY or 'Present')",
      "description": "Job description and key achievements",
      "technologies": ["Tech1", "Tech2"]
    }}
  ],
  "education": [
    {{
      "institution": "School/University name",
      "degree": "Degree type and field",
      "location": "Location",
      "graduation_date": "Graduation date (YYYY or YYYY-MM)",
      "gpa": "GPA (if mentioned)",
      "honors": "Any honors or distinctions"
    }}
  ],
  "skills": ["Skill1", "Skill2", "Skill3"],
  "projects": [
    {{
      "name": "Project name",
      "description": "Project description",
      "technologies": ["Tech1", "Tech2"],
      "url": "Project URL (if available)",
      "date": "Project date or date range"
    }}
  ],
  "other": {{
    "certifications": ["Cert1", "Cert2"],
    "awards": ["Award1", "Award2"],
    "publications": ["Publication1"],
    "languages": ["Language: Proficiency"],
    "volunteer": ["Volunteer experience"]
  }}
}}

Save this data using `update_resume` with the parsed_data field.
"""
        system_prompt = base_system_prompt + """
**Your Role for Resumes:**
You are an expert resume parser that extracts structured data from resume text:
- Parse personal information accurately
- Extract all work experience with dates and details
- Identify education credentials
- List technical and soft skills
- Find projects and achievements
- Capture certifications, awards, and other relevant information

**Important Guidelines:**
- Be thorough and extract all relevant information
- Use consistent date formats (YYYY-MM or YYYY)
- If information is not found, use null for strings, [] for arrays
- Preserve the original content while structuring it
- Save the extracted data immediately using the update_resume MCP tool
"""
        allowed_tools = ["mcp__turbo__get_resume", "mcp__turbo__update_resume"]

    else:
        # Generic entity handling using ENTITY_CONFIGS
        config = ENTITY_CONFIGS.get(entity_type)
        if not config:
            raise ValueError(f"Unknown entity type: {entity_type}")

        # Extract entity data from extra_context
        entity = extra_context.get("entity", {}) if extra_context else {}
        comment_thread = extra_context.get("comment_thread", "_No comments yet_") if extra_context else "_No comments yet_"
        staff = extra_context.get("staff") if extra_context else None

        # Get entity title and build field details
        title_field = config["title_field"]
        entity_title = entity.get(title_field, "Unknown")
        entity_name = config["entity_name_singular"]

        # Build entity details section from configured fields
        entity_details_lines = []
        for field in config["description_fields"]:
            value = entity.get(field, "Not set")
            # Format field name nicely (e.g., "start_date" -> "Start Date")
            field_display = field.replace("_", " ").title()
            entity_details_lines.append(f"**{field_display}:** {value}")
        entity_details = "\n".join(entity_details_lines)

        # Use staff persona if staff was mentioned
        if staff:
            staff_name = staff.get("name", "Unknown")
            staff_persona = staff.get("persona", "")
            staff_role = staff.get("role_type", "leadership")
            staff_capabilities = staff.get("capabilities", [])
            staff_monitoring_scope = staff.get("monitoring_scope", {})

            user_prompt = f"""A user has @mentioned you in a comment on a {entity_name}. You are "{staff_name}", a {staff_role} staff member.

## Your Persona
{staff_persona}

## Your Capabilities
{', '.join(staff_capabilities) if staff_capabilities else 'General guidance'}

## Your Monitoring Scope
- Focus: {staff_monitoring_scope.get('focus', 'General')}
- Entity Types: {', '.join(staff_monitoring_scope.get('entity_types', []))}
- Metrics: {', '.join(staff_monitoring_scope.get('metrics', []))}

## {entity_name.title()} Details
**Title:** {entity_title}

{entity_details}

## Comment Thread
{comment_thread}

## Your Task
Respond to the user's latest comment as {staff_name}:
- Match your persona and communication style defined above
- Provide expert guidance within your domain and capabilities
- Be direct, actionable, and professional
- Reference specific context when helpful

**Important:** The {entity_name} details and comment thread are complete - respond based on the context provided.
"""
            system_prompt = base_system_prompt + f"""
**Your Role as {staff_name}:**
You are a {staff_role} staff member in the organization. Adopt the persona and capabilities defined above to provide expert guidance on this {entity_name}.
"""
        else:
            # Generic AI response without staff persona
            guidance_list = "\n".join([f"- {item}" for item in config["guidance"]])

            user_prompt = f"""A user has @mentioned you in a comment on a {entity_name}.

## {entity_name.title()} Details
**Title:** {entity_title}

{entity_details}

## Comment Thread
{comment_thread}

## Your Task
Please respond to the user's latest comment. Your response should:
- Be helpful and actionable
- Provide specific guidance and suggestions
- Be professional and concise
- Based on the full conversation thread above

**Important:** The {entity_name} details and comment thread above are already complete - you do NOT need to fetch any data. Just analyze the context and provide your response directly.
"""
            system_prompt = base_system_prompt + f"""
**Your Role for {entity_name.title()}s:**
You are a {config["role_description"]} providing guidance on {entity_name}s:
{guidance_list}
"""
        allowed_tools = []

    return user_prompt, system_prompt, allowed_tools


def get_tool_definitions(allowed_tools: list[str]) -> list[dict]:
    """Map allowed tool names to Anthropic tool definitions.

    Args:
        allowed_tools: List of tool names

    Returns:
        List of tool definitions in Anthropic format
    """
    tool_definitions = {
        "create_document": {
            "name": "create_document",
            "description": "Create a markdown document in a project. Use this to create documentation, guides, reports, team charters, or any written artifacts. IMPORTANT: Provide metadata separately from content - do NOT include metadata in the document body.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The document title"
                    },
                    "content": {
                        "type": "string",
                        "description": "The document content in Markdown format. Do NOT include metadata like 'Document Maintenance', 'Owner', 'Update Frequency', etc. in the content - use the metadata field instead."
                    },
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project to attach this document to"
                    },
                    "doc_type": {
                        "type": "string",
                        "description": "Document type: specification, user_guide, api_doc, readme, changelog, requirements, design, or other",
                        "enum": ["specification", "user_guide", "api_doc", "readme", "changelog", "requirements", "design", "other"],
                        "default": "other"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Structured metadata for the document (owner, update_frequency, review_cycle, status, etc.). Provide this separately from content to keep the document body clean.",
                        "properties": {
                            "owner": {"type": "string"},
                            "update_frequency": {"type": "string"},
                            "review_cycle": {"type": "string"},
                            "document_status": {"type": "string"},
                            "version": {"type": "string"},
                            "last_updated": {"type": "string"}
                        }
                    }
                },
                "required": ["title", "content", "project_id"]
            }
        },
        "list_projects": {
            "name": "list_projects",
            "description": "List all projects in the system. Returns project name, ID, status, and description. Use this to find the project_id you need for creating documents.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by project status (optional)",
                        "enum": ["active", "on_hold", "completed", "archived"]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of projects to return (default: 100)",
                        "default": 100
                    }
                },
                "required": []
            }
        },
        "get_project": {
            "name": "get_project",
            "description": "Get detailed information about a specific project by ID. Returns full project details including name, description, status, and completion percentage.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project to retrieve"
                    }
                },
                "required": ["project_id"]
            }
        }
    }

    # Map allowed tools to their definitions
    tools = []
    for tool_name in allowed_tools:
        if tool_name in tool_definitions:
            tools.append(tool_definitions[tool_name])

    return tools


async def create_document_tool(
    title: str,
    content: str,
    project_id: str,
    doc_type: str = "other",
    metadata: dict | None = None
) -> dict:
    """Tool for staff to create documents via API.

    Args:
        title: Document title
        content: Document content (Markdown) - should NOT include metadata
        project_id: UUID of the project to attach document to
        doc_type: Document type (default: "other")
        metadata: Structured metadata (owner, update_frequency, review_cycle, etc.)

    Returns:
        Created document info
    """
    payload = {
        "title": title,
        "content": content,
        "project_id": project_id,
        "type": doc_type,  # API uses 'type' not 'doc_type'
        "format": "markdown",
        "status": "draft",
    }

    # Add metadata if provided (use doc_metadata to avoid SQLAlchemy reserved word)
    if metadata:
        payload["doc_metadata"] = metadata

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{TURBO_API_URL}/documents/",
            json=payload
        )
        response.raise_for_status()
        document = response.json()

        metadata_info = f" (with metadata: {list(metadata.keys())})" if metadata else ""
        logger.info(f"Created document '{title}' (ID: {document['id']}){metadata_info}")
        return document


async def list_projects_tool(status: str | None = None, limit: int = 100) -> list[dict]:
    """Tool for staff to list projects via API.

    Args:
        status: Optional status filter (active, on_hold, completed, archived)
        limit: Maximum number of projects to return

    Returns:
        List of projects with id, name, status, description
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        params = {"limit": limit}
        if status:
            params["status"] = status

        response = await client.get(
            f"{TURBO_API_URL}/projects/",
            params=params
        )
        response.raise_for_status()
        projects = response.json()
        logger.info(f"Listed {len(projects)} projects")
        return projects


async def get_project_tool(project_id: str) -> dict:
    """Tool for staff to get project details via API.

    Args:
        project_id: UUID of the project

    Returns:
        Project details
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{TURBO_API_URL}/projects/{project_id}")
        response.raise_for_status()
        project = response.json()
        logger.info(f"Retrieved project '{project['name']}' (ID: {project_id})")
        return project


async def get_work_queue_tool(
    status: str | None = None,
    priority: str | None = None,
    limit: int = 100,
    include_unranked: bool = False
) -> list[dict]:
    """Tool for staff to get the work queue via API.

    Args:
        status: Optional status filter (open, in_progress, review, testing, closed)
        priority: Optional priority filter (low, medium, high, critical)
        limit: Maximum number of issues to return
        include_unranked: Include issues without work_rank

    Returns:
        List of ranked issues
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        params = {"limit": limit, "include_unranked": include_unranked}
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority

        response = await client.get(
            f"{TURBO_API_URL}/work-queue/",
            params=params
        )
        response.raise_for_status()
        issues = response.json()
        logger.info(f"Retrieved {len(issues)} issues from work queue")
        return issues


async def get_next_issue_tool() -> dict | None:
    """Tool for staff to get the next issue to work on via API.

    Returns:
        Next highest-ranked issue or None
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{TURBO_API_URL}/work-queue/next")
        response.raise_for_status()
        issue = response.json()
        if issue:
            logger.info(f"Retrieved next issue: '{issue.get('title')}' (Rank: {issue.get('work_rank')})")
        else:
            logger.info("No next issue available")
        return issue


async def set_issue_rank_tool(issue_id: str, work_rank: int) -> dict:
    """Tool for staff to set work rank for an issue via API.

    Args:
        issue_id: UUID of the issue
        work_rank: New rank position (1=highest priority)

    Returns:
        Updated issue
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{TURBO_API_URL}/work-queue/{issue_id}/rank",
            json={"work_rank": work_rank}
        )
        response.raise_for_status()
        issue = response.json()
        logger.info(f"Set issue '{issue.get('title')}' to rank {work_rank}")
        return issue


async def remove_issue_rank_tool(issue_id: str) -> dict:
    """Tool for staff to remove an issue from the work queue via API.

    Args:
        issue_id: UUID of the issue

    Returns:
        Updated issue
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.delete(f"{TURBO_API_URL}/work-queue/{issue_id}/rank")
        response.raise_for_status()
        issue = response.json()
        logger.info(f"Removed issue '{issue.get('title')}' from work queue")
        return issue


async def auto_rank_issues_tool() -> dict:
    """Tool for staff to auto-rank all issues via API.

    Returns:
        Result with count of ranked issues
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{TURBO_API_URL}/work-queue/auto-rank")
        response.raise_for_status()
        result = response.json()
        logger.info(f"Auto-ranked {result.get('ranked_count')} issues")
        return result


async def create_issue_tool(
    project_id: str,
    title: str,
    description: str,
    type: str = "feature",
    priority: str = "medium",
    status: str = "open"
) -> dict:
    """Tool for staff to create a new issue via API.

    Args:
        project_id: UUID of the project
        title: Issue title
        description: Issue description
        type: Issue type (feature, bug, discovery, task, epic)
        priority: Priority level (low, medium, high, critical)
        status: Initial status (open, in_progress, review, testing, closed)

    Returns:
        Created issue
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{TURBO_API_URL}/issues/",
            json={
                "project_id": project_id,
                "title": title,
                "description": description,
                "type": type,
                "priority": priority,
                "status": status
            }
        )
        response.raise_for_status()
        issue = response.json()
        logger.info(f"Created issue '{issue.get('title')}' (ID: {issue.get('id')})")
        return issue


async def call_claude_api_with_tools(
    system_prompt: str,
    user_prompt: str,
    tools: list[dict] | None = None,
    max_iterations: int = 5
) -> tuple[str, float]:
    """Call Claude API with function calling support.

    Args:
        system_prompt: System instructions for Claude
        user_prompt: User message/prompt
        tools: List of tool definitions (optional)
        max_iterations: Maximum number of tool call iterations

    Returns:
        Tuple of (response_text, total_cost_usd)
    """
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    messages = [{"role": "user", "content": user_prompt}]
    total_cost = 0.0

    for iteration in range(max_iterations):
        payload = {
            "model": MODEL,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": messages,
        }

        # Add tools if provided
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                ANTHROPIC_API_URL,
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                error_text = response.text
                logger.error(f"Anthropic API error: {response.status_code} - {error_text}")
                raise Exception(f"Anthropic API error: {response.status_code}")

            result = response.json()

            # Calculate cost for this turn
            input_tokens = result.get("usage", {}).get("input_tokens", 0)
            output_tokens = result.get("usage", {}).get("output_tokens", 0)
            turn_cost = (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)
            total_cost += turn_cost

            logger.info(f"Turn {iteration + 1}: {input_tokens} input, {output_tokens} output tokens (${turn_cost:.4f})")

            # Add assistant's response to messages
            content = result["content"]
            messages.append({"role": "assistant", "content": content})

            # Check stop reason
            stop_reason = result.get("stop_reason")

            if stop_reason == "end_turn":
                # Extract text from final response
                response_text = ""
                for block in content:
                    if block.get("type") == "text":
                        response_text += block.get("text", "")
                return response_text, total_cost

            elif stop_reason == "tool_use":
                # Execute tools and continue
                tool_results = []

                for block in content:
                    if block.get("type") == "tool_use":
                        tool_name = block.get("name")
                        tool_input = block.get("input", {})
                        tool_use_id = block.get("id")

                        logger.info(f"Executing tool: {tool_name} with input: {tool_input}")

                        # Execute the tool
                        try:
                            if tool_name == "create_document":
                                result = await create_document_tool(**tool_input)
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": json.dumps(result)
                                })
                            elif tool_name == "list_projects":
                                result = await list_projects_tool(**tool_input)
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": json.dumps(result)
                                })
                            elif tool_name == "get_project":
                                result = await get_project_tool(**tool_input)
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": json.dumps(result)
                                })
                            elif tool_name == "get_work_queue":
                                result = await get_work_queue_tool(**tool_input)
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": json.dumps(result)
                                })
                            elif tool_name == "get_next_issue":
                                result = await get_next_issue_tool(**tool_input)
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": json.dumps(result)
                                })
                            elif tool_name == "set_issue_rank":
                                result = await set_issue_rank_tool(**tool_input)
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": json.dumps(result)
                                })
                            elif tool_name == "remove_issue_rank":
                                result = await remove_issue_rank_tool(**tool_input)
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": json.dumps(result)
                                })
                            elif tool_name == "auto_rank_issues":
                                result = await auto_rank_issues_tool(**tool_input)
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": json.dumps(result)
                                })
                            elif tool_name == "create_issue":
                                result = await create_issue_tool(**tool_input)
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": json.dumps(result)
                                })
                            else:
                                logger.warning(f"Unknown tool: {tool_name}")
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "is_error": True,
                                    "content": f"Unknown tool: {tool_name}"
                                })
                        except Exception as e:
                            logger.error(f"Tool execution error: {e}")
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "is_error": True,
                                "content": f"Error executing {tool_name}: {str(e)}"
                            })

                # Add tool results to messages and continue
                messages.append({"role": "user", "content": tool_results})

            else:
                # Unknown stop reason - return what we have
                response_text = ""
                for block in content:
                    if block.get("type") == "text":
                        response_text += block.get("text", "")
                return response_text or "No response generated", total_cost

    # Max iterations reached
    logger.warning(f"Max iterations ({max_iterations}) reached")
    return "Maximum tool iterations reached", total_cost


async def call_claude_api(system_prompt: str, user_prompt: str) -> tuple[str, float]:
    """Call Claude API and return response text and cost.

    Args:
        system_prompt: System instructions for Claude
        user_prompt: User message/prompt

    Returns:
        Tuple of (response_text, cost_usd)
    """
    # Use the tool-enabled version without any tools (backwards compatible)
    return await call_claude_api_with_tools(system_prompt, user_prompt, tools=None)


async def post_comment_to_api(entity_type: str, entity_id: str, content: str, author_name: str = "Claude") -> None:
    """Post a comment back to the Turbo API.

    Args:
        entity_type: Type of entity (issue, project, etc.)
        entity_id: UUID of the entity
        content: Comment content to post
        author_name: Name of the AI author (default: "Claude")
    """
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        # Use the unified comments endpoint (with trailing slash to avoid redirect)
        response = await client.post(
            f"{TURBO_API_URL}/comments/",
            json={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "content": content,
                "author_type": "ai",
                "author_name": author_name
            }
        )
        response.raise_for_status()
        logger.info(f"Posted AI comment to {entity_type} {entity_id} (author: {author_name})")


async def post_mentor_message(mentor_id: str, content: str) -> None:
    """Post a mentor message back to the Turbo API.

    Args:
        mentor_id: UUID of the mentor
        content: Message content to post
    """
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.post(
            f"{TURBO_API_URL}/mentors/{mentor_id}/messages",
            json={
                "content": content
            }
        )
        response.raise_for_status()
        logger.info(f"Posted mentor message to {mentor_id}")


async def post_staff_message(staff_id: str, content: str) -> None:
    """Post a staff message back to the Turbo API.

    Args:
        staff_id: UUID of the staff member
        content: Message content to post
    """
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.post(
            f"{TURBO_API_URL}/staff/{staff_id}/assistant-message",
            json={
                "content": content
            }
        )
        response.raise_for_status()
        logger.info(f"Posted staff message to {staff_id}")


async def check_staff_wants_to_continue(staff_id: str, system_prompt: str, tools: list[dict] | None = None) -> tuple[bool, str | None, float]:
    """Check if staff wants to send another message without waiting for user.

    Args:
        staff_id: UUID of the staff member
        system_prompt: System prompt for the staff
        tools: Available tools

    Returns:
        Tuple of (wants_to_continue, message_content, cost)
    """
    try:
        # Fetch updated conversation context
        staff_context = await fetch_staff_context(staff_id)
        conversation_history = staff_context.get("conversation_history", "")
        staff = staff_context["staff"]

        staff_name = staff.get("name", "Unknown")
        staff_persona = staff.get("persona", "")

        # Ask Staff if they want to send a follow-up message
        continuation_prompt = f"""You are "{staff_name}", reviewing your recent conversation.

## Your Persona
{staff_persona}

## Recent Conversation
{conversation_history}

## Your Task
Review the conversation above. If you want to send another message immediately (without waiting for the user to respond), respond with your message.

**Only send a follow-up message if:**
- You have additional important information to share
- You need to provide a multi-part update
- You're working on a task and want to share progress
- You're providing a detailed response that makes sense to break into multiple messages

**Do NOT send a follow-up if:**
- Your previous message was complete
- You're waiting for user input
- There's nothing more to add right now

If you want to send a follow-up, respond with your message. If not, respond with exactly: "NO_FOLLOWUP"
"""

        response_text, cost = await call_claude_api_with_tools(system_prompt, continuation_prompt, tools)

        # Check if Staff wants to continue
        if response_text.strip() == "NO_FOLLOWUP":
            return False, None, cost
        else:
            return True, response_text, cost

    except Exception as e:
        logger.error(f"Error checking staff continuation: {e}")
        return False, None, 0.0


async def queue_action_for_approval(
    entity_type: str,
    entity_id: str,
    entity_title: str,
    action_intent,
    response_text: str
) -> None:
    """Queue a detected action for approval via the approval API.

    Args:
        entity_type: Type of entity (issue, project)
        entity_id: UUID of the entity
        entity_title: Title of the entity (for context)
        action_intent: ActionIntent object with action details
        response_text: Full AI response text (for context)
    """
    if not ACTION_DETECTION_ENABLED:
        return

    try:
        # Classify the action to determine risk level and auto-execute
        risk_level, auto_execute = ActionClassifier.classify_action(
            action_intent.action_type,
            action_intent.params
        )

        # Build approval request
        approval_data = {
            "action_type": action_intent.action_type,
            "action_description": action_intent.description,
            "risk_level": risk_level.value,
            "action_params": action_intent.params,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity_title": entity_title,
            "ai_reasoning": action_intent.reasoning or response_text[:500],
            "auto_execute": auto_execute
        }

        # Queue action via API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{TURBO_API_URL}/action-approvals/",
                json=approval_data
            )
            response.raise_for_status()
            result = response.json()

            logger.info(
                f"Queued {action_intent.action_type} for approval "
                f"(risk: {risk_level.value}, auto_execute: {auto_execute}, id: {result.get('id')})"
            )

    except Exception as e:
        logger.error(f"Failed to queue action for approval: {e}", exc_info=True)


async def handle_comment_webhook(request: web.Request) -> web.Response:
    """Handle incoming webhook requests to trigger Claude responses."""
    try:
        data = await request.json()
        entity_type = data.get("entity_type")
        entity_id = data.get("entity_id")
        staff_id = data.get("staff_id")  # Optional: specific staff member mentioned

        if not entity_type or not entity_id:
            logger.error("Missing entity_type or entity_id in webhook request")
            return web.json_response(
                {"error": "Missing entity_type or entity_id"}, status=400
            )

        if staff_id:
            logger.info(f"Received webhook for {entity_type} {entity_id} (staff: {staff_id})")
        else:
            logger.info(f"Received webhook for {entity_type} {entity_id}")

        # Fetch extra context (pre-fetch data before calling Claude)
        extra_context = None
        staff_context = None

        # Fetch staff context if a staff member was mentioned
        if staff_id:
            try:
                logger.info(f"Fetching staff context for {staff_id}")
                staff_context = await fetch_staff_context(staff_id)
                logger.info(f"Fetched staff: {staff_context['staff']['name']}")
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch staff context: {e}")
                # Continue anyway with generic AI response
                staff_context = None

        # Fetch entity context based on entity type
        # Special cases with custom message formats (mentor, staff)
        if entity_type == "mentor":
            try:
                logger.info(f"Fetching enhanced mentor context for {entity_id}")
                extra_context = await fetch_enhanced_mentor_context(entity_id)
                logger.info(f"Fetched context with {extra_context['message_count']} messages for mentor {entity_id}")
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch mentor context: {e}")
                return web.json_response({"error": f"Failed to fetch mentor context: {str(e)}"}, status=500)
        elif entity_type == "staff":
            try:
                logger.info(f"Fetching enhanced staff context for {entity_id}")
                extra_context = await fetch_enhanced_staff_context(entity_id)
                logger.info(f"Fetched context with {extra_context['message_count']} messages for staff {entity_id}")
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch staff context: {e}")
                return web.json_response({"error": f"Failed to fetch staff context: {str(e)}"}, status=500)
        elif entity_type in ENTITY_CONFIGS:
            # Generic entity handling using configuration
            try:
                logger.info(f"Fetching {entity_type} context for {entity_id}")
                extra_context = await fetch_generic_entity_context(entity_type, entity_id)
                logger.info(f"Fetched {entity_type} with {extra_context['comment_count']} comments")
                # Add staff context if available
                if staff_context:
                    extra_context["staff"] = staff_context["staff"]
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch {entity_type} context: {e}")
                return web.json_response({"error": f"Failed to fetch {entity_type} context: {str(e)}"}, status=500)
        else:
            # Unknown entity type
            logger.error(f"Unknown entity type: {entity_type}")
            return web.json_response({"error": f"Unknown entity type: {entity_type}"}, status=400)

        # Build entity-specific prompt
        try:
            user_prompt, system_prompt, allowed_tools = build_entity_prompt(
                entity_type, entity_id, extra_context
            )
        except ValueError as e:
            logger.error(f"Invalid entity type: {e}")
            return web.json_response({"error": str(e)}, status=400)

        # Prepare tools if any are allowed
        tools = None
        if allowed_tools:
            tools = get_tool_definitions(allowed_tools)
            if tools:
                logger.info(f"Using {len(tools)} tool(s): {[t['name'] for t in tools]}")

        # Call Claude API
        logger.info(f"Calling Claude API for {entity_type} {entity_id}")
        try:
            if tools:
                response_text, cost_usd = await call_claude_api_with_tools(system_prompt, user_prompt, tools)
            else:
                response_text, cost_usd = await call_claude_api(system_prompt, user_prompt)
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            return web.json_response({"success": False, "error": str(e)}, status=500)
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return web.json_response({"success": False, "error": str(e)}, status=500)

        # Detect and queue actions for approval (if applicable)
        if ACTION_DETECTION_ENABLED and should_detect_actions(entity_type):
            try:
                # Extract entity title for context
                entity_title = "Unknown"
                if extra_context and "entity" in extra_context:
                    # Generic entity from ENTITY_CONFIGS
                    config = ENTITY_CONFIGS.get(entity_type)
                    if config:
                        title_field = config["title_field"]
                        entity_title = extra_context["entity"].get(title_field, "Unknown")
                elif entity_type == "issue" and extra_context:
                    # Legacy: specific fetch functions still return "issue" key
                    entity_title = extra_context.get("issue", {}).get("title", "Unknown")
                elif entity_type == "project" and extra_context:
                    # Legacy: specific fetch functions still return "project" key
                    entity_title = extra_context.get("project", {}).get("name", "Unknown")

                # Detect actions in AI response
                detected_actions = detect_action_intent(response_text)

                if detected_actions:
                    logger.info(f"Detected {len(detected_actions)} action(s) in AI response")

                    # Queue each detected action for approval
                    for action_intent in detected_actions:
                        await queue_action_for_approval(
                            entity_type=entity_type,
                            entity_id=entity_id,
                            entity_title=entity_title,
                            action_intent=action_intent,
                            response_text=response_text
                        )
                else:
                    logger.info("No actions detected in AI response")

            except Exception as e:
                # Don't fail the whole webhook if action detection fails
                logger.error(f"Action detection failed (continuing anyway): {e}", exc_info=True)

        # Post the response back to the API
        try:
            if entity_type == "mentor":
                await post_mentor_message(entity_id, response_text)
            elif entity_type == "staff":
                # Post staff message (single response per user message)
                await post_staff_message(entity_id, response_text)
                logger.info(f"Posted staff response for {entity_id}")

            else:
                # Use staff member's alias (or handle as fallback) as author if staff was mentioned
                author_name = "Claude"
                if staff_context and staff_context.get("staff"):
                    staff = staff_context["staff"]
                    # Prefer alias, fallback to handle, then to "Claude"
                    author_name = staff.get("alias") or staff.get("handle") or "Claude"
                await post_comment_to_api(entity_type, entity_id, response_text, author_name)
        except httpx.HTTPError as e:
            logger.error(f"Failed to post response: {e}")
            return web.json_response({"success": False, "error": f"Failed to post response: {str(e)}"}, status=500)

        logger.info(f"Claude completed for {entity_type} {entity_id} (cost: ${cost_usd:.4f})")
        return web.json_response(
            {
                "success": True,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "cost_usd": cost_usd,
            }
        )

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return web.json_response({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return web.json_response({"error": str(e)}, status=500)


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "ok", "service": "claude-webhook"})


async def handle_group_discussion_webhook(request: web.Request) -> web.Response:
    """Handle incoming webhook requests for group discussions.

    Generates AI responses from all active staff members based on the conversation context.
    """
    try:
        data = await request.json()
        discussion_id = data.get("discussion_id")
        initiating_staff_id = data.get("initiating_staff_id")

        if not discussion_id:
            logger.error("Missing discussion_id in webhook request")
            return web.json_response(
                {"error": "Missing discussion_id"}, status=400
            )

        logger.info(f"Received group discussion webhook for discussion {discussion_id}")

        total_cost = 0.0
        responses_generated = 0

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Fetch conversation history
            logger.info(f"Fetching conversation history for discussion {discussion_id}")
            messages_response = await client.get(
                f"{TURBO_API_URL}/group-discussions/{discussion_id}/messages",
                params={"limit": 20}  # Last 20 messages for context
            )
            messages_response.raise_for_status()
            messages_data = messages_response.json()
            messages = messages_data.get("messages", [])

            # Format conversation history and track time since last user message
            from datetime import datetime, timezone

            conversation_history = []
            consecutive_staff_messages = 0
            last_user_message_time = None

            for msg in reversed(messages):  # Check from most recent
                if msg["message_type"] == "user":
                    last_user_message_time = datetime.fromisoformat(msg["created_at"].replace('Z', '+00:00'))
                    break  # Stop counting at the last user message
                consecutive_staff_messages += 1

            # Calculate time since last user message
            minutes_since_user = 999  # Default to high value if no user message found
            if last_user_message_time:
                time_since_user_message = datetime.now(timezone.utc) - last_user_message_time
                minutes_since_user = time_since_user_message.total_seconds() / 60

            for msg in messages:
                role = "User" if msg["message_type"] == "user" else "AI"
                staff_id = msg.get("staff_id")
                if staff_id and role == "AI":
                    # Try to get staff handle/alias for display
                    role = f"Staff Member ({staff_id[:8]}...)"
                conversation_history.append(f"{role}: {msg['content']}")

            conversation_text = "\n\n".join(conversation_history)
            logger.info(f"Fetched {len(messages)} messages ({consecutive_staff_messages} consecutive staff messages, {minutes_since_user:.1f} min since user)")

            # Get all active staff members
            logger.info("Fetching all active staff members")
            staff_response = await client.get(
                f"{TURBO_API_URL}/staff/",
                params={"is_active": True}
            )
            staff_response.raise_for_status()
            all_staff = staff_response.json()

            # Filter out the initiating staff member (if any) to avoid self-response
            staff_to_respond = [
                s for s in all_staff
                if not initiating_staff_id or s["id"] != str(initiating_staff_id)
            ]

            logger.info(f"Found {len(staff_to_respond)} staff members who can respond")

            # Prioritize staff members based on context
            def calculate_staff_priority(staff):
                """Calculate priority score for staff member (higher = respond sooner)."""
                score = 0
                handle = staff.get("alias") or staff.get("handle", "")
                description = staff.get("description", "").lower()
                persona = staff.get("persona", "").lower()

                # Check if directly mentioned in recent messages
                recent_conversation = conversation_text.lower()
                if f"@{handle.lower()}" in recent_conversation:
                    score += 100  # Highest priority for direct mentions

                # Check if their role/expertise is relevant to conversation topics
                # Extract keywords from conversation
                conversation_lower = recent_conversation.lower()
                expertise_keywords = {
                    "product": ["feature", "user", "product", "roadmap", "requirement"],
                    "engineering": ["technical", "code", "bug", "deploy", "architecture", "api"],
                    "agility": ["sprint", "standup", "velocity", "retrospective", "planning"],
                    "design": ["ui", "ux", "design", "interface", "user experience"],
                    "data": ["analytics", "metrics", "data", "reporting", "insights"],
                }

                for domain, keywords in expertise_keywords.items():
                    if domain in description or domain in persona:
                        if any(keyword in conversation_lower for keyword in keywords):
                            score += 50  # High priority for domain experts

                # Leadership roles get moderate priority for strategic discussions
                if staff.get("is_leadership_role"):
                    strategic_keywords = ["strategy", "vision", "goal", "priority", "decision"]
                    if any(keyword in conversation_lower for keyword in strategic_keywords):
                        score += 30

                # Slight boost for leadership to ensure they can chime in
                if staff.get("is_leadership_role"):
                    score += 10

                return score

            # Sort staff by priority (highest first)
            staff_to_respond_sorted = sorted(
                staff_to_respond,
                key=calculate_staff_priority,
                reverse=True
            )

            # Log the priority order
            logger.info("Staff response priority order:")
            for idx, staff in enumerate(staff_to_respond_sorted[:5], 1):
                priority = calculate_staff_priority(staff)
                handle = staff.get("alias") or staff.get("handle", "Unknown")
                logger.info(f"  {idx}. {staff['name']} (@{handle}) - priority: {priority}")

            # Generate response for each staff member (in priority order)
            for staff in staff_to_respond_sorted:
                try:
                    staff_id = staff["id"]
                    staff_name = staff["name"]
                    staff_handle = staff.get("alias") or staff.get("handle", "Unknown")
                    staff_persona = staff.get("persona", "")

                    logger.info(f"Generating response for {staff_name} (@{staff_handle})")

                    # Build prompt for this staff member
                    # Make it stricter if there are many consecutive staff messages AND less than 2 minutes since user
                    strictness_note = ""
                    if consecutive_staff_messages >= 3 and minutes_since_user < 2:
                        strictness_note = f"""

⚠️ IMPORTANT: There have already been {consecutive_staff_messages} consecutive staff responses without user input.
Only respond if you are directly @mentioned or have CRITICAL new information. Otherwise, say SKIP."""
                    elif consecutive_staff_messages >= 3 and minutes_since_user >= 2:
                        # Been quiet for 2+ minutes - allow natural conversation restart
                        strictness_note = """

💡 NOTE: It's been quiet for a few minutes. Feel free to start a new discussion or check in with the team if relevant to your role."""

                    system_prompt = f"""You are {staff_name} (@{staff_handle}), participating in an All Hands team discussion.

Your persona and role:
{staff_persona}

IMPORTANT INSTRUCTIONS:
1. Review the conversation history carefully
2. Decide if you should respond based on:
   - Whether you are directly @mentioned
   - Whether the topic relates to your expertise/role
   - Whether you have something NEW and valuable to add
   - Whether someone asked a question you can answer
3. If you choose to respond:
   - Be concise and focused (1-2 sentences max)
   - Speak naturally as your character
   - Address others by name when relevant
   - Stay in character based on your persona
4. If the conversation doesn't require your input, respond with just "SKIP" (nothing else){strictness_note}

Response format:
- If responding: Your message (1-2 sentences, NEW information only)
- If not responding: SKIP"""

                    user_prompt = f"""Here's the recent conversation in All Hands:

{conversation_text}

Should you respond? If yes, what do you say?"""

                    # Call Claude API
                    response_text, cost = await call_claude_api(system_prompt, user_prompt)
                    total_cost += cost

                    # Check if staff member wants to skip
                    if response_text.strip().upper() == "SKIP":
                        logger.info(f"{staff_name} chose not to respond")
                        continue

                    # Post the response back to the discussion
                    logger.info(f"Posting response from {staff_name}")
                    post_response = await client.post(
                        f"{TURBO_API_URL}/group-discussions/{discussion_id}/messages",
                        json={
                            "staff_id": staff_id,
                            "content": response_text,
                            "is_user_message": False
                        }
                    )
                    post_response.raise_for_status()

                    responses_generated += 1
                    logger.info(f"✓ Posted response from {staff_name} (cost: ${cost:.4f})")

                except Exception as e:
                    logger.error(f"Failed to generate response for {staff.get('name', 'unknown')}: {e}", exc_info=True)
                    # Continue with other staff members
                    continue

        logger.info(f"Group discussion complete: {responses_generated} responses generated (total cost: ${total_cost:.4f})")

        return web.json_response({
            "success": True,
            "discussion_id": discussion_id,
            "responses_generated": responses_generated,
            "cost_usd": total_cost
        })

    except Exception as e:
        logger.error(f"Group discussion webhook failed: {e}", exc_info=True)
        return web.json_response(
            {"success": False, "error": str(e)}, status=500
        )


async def handle_issue_ready_webhook(request: web.Request) -> web.Response:
    """
    Handle issue.ready event - automatically start work on issue with worktree.

    When an issue status changes to 'ready', this handler:
    1. Fetches issue and project details
    2. Creates a git worktree for isolated development
    3. Updates issue status to 'in_progress'
    4. Creates a work log entry
    """
    try:
        data = await request.json()
        issue_data = data.get("issue", {})
        issue_id = issue_data.get("id")
        project_id = data.get("project_id")

        if not issue_id:
            logger.error("Missing issue ID in webhook request")
            return web.json_response({"error": "Missing issue ID"}, status=400)

        logger.info(f"Received issue.ready event for issue {issue_id}")

        # Get project path from environment or config
        # This should be the path to the turboCode project
        project_path = os.getenv("TURBO_PROJECT_PATH", "/app")

        # Call the Turbo API to start work on the issue (creates worktree)
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{TURBO_API_URL}/issues/{issue_id}/start-work",
                json={
                    "started_by": "ai:context",
                    "project_path": project_path
                }
            )

            if response.status_code == 200:
                result = response.json()
                worktree_path = result.get("worktree_path")
                issue_key = result.get("issue_key")

                logger.info(f"✓ Started work on {issue_key}")
                logger.info(f"  Worktree: {worktree_path}")
                logger.info(f"  Status: ready → in_progress")

                return web.json_response({
                    "success": True,
                    "issue_id": issue_id,
                    "issue_key": issue_key,
                    "worktree_path": worktree_path,
                    "status": "in_progress"
                })
            else:
                error_msg = response.text
                logger.error(f"Failed to start work on issue: {error_msg}")
                return web.json_response({
                    "success": False,
                    "error": error_msg
                }, status=response.status_code)

    except Exception as e:
        logger.error(f"Issue ready webhook failed: {e}", exc_info=True)
        return web.json_response(
            {"success": False, "error": str(e)}, status=500
        )


async def startup_fetch_api_key(app):
    """Fetch API key from Turbo API at startup."""
    global ANTHROPIC_API_KEY
    logger.info("Fetching API key from Turbo API...")
    ANTHROPIC_API_KEY = await fetch_api_key_from_api()

    if ANTHROPIC_API_KEY:
        logger.info("✓ API key successfully loaded from database")
    else:
        logger.warning("⚠️  No API key configured - webhook will fail!")
        logger.warning("   Please configure your Anthropic API key in the Turbo UI Settings page")


def main():
    """Start the webhook server."""
    app = web.Application()
    app.router.add_post("/webhook/comment", handle_comment_webhook)
    app.router.add_post("/webhook/group-discussion", handle_group_discussion_webhook)
    app.router.add_post("/webhook/issue-ready", handle_issue_ready_webhook)
    app.router.add_get("/health", health_check)

    # Register startup hook to fetch API key
    app.on_startup.append(startup_fetch_api_key)

    logger.info(f"Starting Claude webhook server on port {WEBHOOK_PORT}")
    logger.info(f"Model: {MODEL}")
    logger.info(f"Endpoints:")
    logger.info(f"  - http://localhost:{WEBHOOK_PORT}/webhook/comment")
    logger.info(f"  - http://localhost:{WEBHOOK_PORT}/webhook/group-discussion")
    logger.info(f"  - http://localhost:{WEBHOOK_PORT}/webhook/issue-ready")
    logger.info(f"Turbo API: {TURBO_API_URL}")

    web.run_app(app, host="0.0.0.0", port=WEBHOOK_PORT)


if __name__ == "__main__":
    main()
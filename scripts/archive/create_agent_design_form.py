#!/usr/bin/env python3
"""
Script to create the Agent Design Questions form and attach it to the agent design issue.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from turbo.core.database.connection import get_db_session
from turbo.core.services.form_builder import FormBuilder
from turbo.core.repositories.form import FormRepository


async def create_agent_design_form():
    """Create the Agent Design Questions form using FormBuilder."""

    # Agent design issue ID from previous conversation
    agent_design_issue_id = "c66d73cc-e01e-47c1-a844-a2e240109e6b"

    # Build the form using FormBuilder
    form_builder = FormBuilder(
        title="Agent Design Questions",
        description="Please answer these questions to help design the autonomous agent system. Your responses will guide the implementation."
    )

    # 1. Agent Capabilities
    form_builder.add_text(
        field_id="agent_name",
        label="What should we call this agent?",
        placeholder="e.g., PM Agent, Research Agent, etc.",
        required=True,
        max_length=100
    )

    form_builder.add_radio(
        field_id="primary_role",
        label="What is the primary role of this agent?",
        options=[
            "Project Management",
            "Research & Analysis",
            "Code Review",
            "Workflow Automation",
            "Documentation",
        ],
        required=True
    )

    # 2. Autonomy Level
    form_builder.add_radio(
        field_id="autonomy_level",
        label="What level of autonomy should this agent have?",
        options=[
            "Full Autonomy - Make decisions and execute without user approval",
            "Semi-Autonomous - Execute routine tasks, ask for approval on complex decisions",
            "Supervised - Always ask for user approval before taking actions",
        ],
        required=True
    )

    form_builder.add_textarea(
        field_id="autonomous_actions",
        label="What actions can the agent perform autonomously? (List specific actions)",
        placeholder="e.g., Close completed issues, add tags, create comments, etc.",
        required=True,
        min_length=20,
        rows=4
    )

    form_builder.add_textarea(
        field_id="approval_required",
        label="What actions require user approval? (List specific actions)",
        placeholder="e.g., Delete issues, modify code, create new initiatives, etc.",
        required=True,
        min_length=20,
        rows=4
    )

    # 3. Context & Tools
    form_builder.add_checkbox(
        field_id="data_access",
        label="What data should the agent have access to?",
        options=[
            "All issues in database",
            "All projects in database",
            "All documents in database",
            "Literature/research library",
            "Git repository access",
            "Code files in workspace",
        ],
        required=True,
        min_selections=1
    )

    form_builder.add_checkbox(
        field_id="allowed_tools",
        label="What tools should the agent be able to use?",
        options=[
            "Database queries (read-only)",
            "Database mutations (write)",
            "File system access",
            "Git operations",
            "API calls to external services",
            "Code execution",
        ],
        required=True,
        min_selections=1
    )

    # 4. Triggers & Scheduling
    form_builder.add_radio(
        field_id="trigger_type",
        label="How should the agent be triggered?",
        options=[
            "Manual - User explicitly runs the agent",
            "Event-based - Triggered by specific events (issue created, status changed, etc.)",
            "Scheduled - Runs on a regular schedule",
            "Hybrid - Combination of the above",
        ],
        required=True
    )

    form_builder.add_textarea(
        field_id="trigger_details",
        label="Describe the trigger conditions in detail",
        placeholder="e.g., Run every night at 2am, or when an issue is created with 'needs-triage' tag",
        required=False,
        rows=3,
        show_if={"trigger_type": ["Event-based", "Scheduled", "Hybrid"]}
    )

    # 5. Communication & Notifications
    form_builder.add_checkbox(
        field_id="notification_methods",
        label="How should the agent notify you?",
        options=[
            "@ mention in comments",
            "Email",
            "System notifications",
            "Dashboard alerts",
            "Slack/Discord webhooks",
        ],
        required=True,
        min_selections=1
    )

    form_builder.add_radio(
        field_id="verbosity_level",
        label="How verbose should the agent be?",
        options=[
            "Minimal - Only notify on important decisions",
            "Standard - Notify on all actions taken",
            "Detailed - Include reasoning and full logs",
        ],
        required=True
    )

    # 6. Quality & Validation
    form_builder.add_textarea(
        field_id="quality_criteria",
        label="What quality criteria should the agent use when evaluating work?",
        placeholder="e.g., All issues must have descriptions, closed issues need resolution notes, etc.",
        required=True,
        min_length=50,
        rows=4
    )

    # 7. Error Handling
    form_builder.add_radio(
        field_id="error_handling",
        label="How should the agent handle errors?",
        options=[
            "Fail silently and log",
            "Retry automatically (up to 3 times)",
            "Stop and notify user immediately",
            "Rollback changes and notify user",
        ],
        required=True
    )

    # 8. Constraints & Safety
    form_builder.add_textarea(
        field_id="safety_constraints",
        label="What safety constraints should the agent follow?",
        placeholder="e.g., Never delete data, never modify main branch, always create backups, etc.",
        required=True,
        min_length=30,
        rows=4
    )

    form_builder.add_number(
        field_id="rate_limit",
        label="Maximum number of actions per run (rate limit for safety)",
        required=True,
        min_value=1,
        max_value=1000,
        step=1,
        placeholder="50"
    )

    # 9. First Use Case
    form_builder.add_textarea(
        field_id="first_task",
        label="Describe the first task you want the agent to perform",
        placeholder="e.g., Audit all open issues and identify which ones are actually complete",
        required=True,
        min_length=50,
        rows=4
    )

    form_builder.add_textarea(
        field_id="success_criteria",
        label="How will you know the agent succeeded?",
        placeholder="e.g., All completed issues are closed, initiatives are properly organized, etc.",
        required=True,
        min_length=30,
        rows=3
    )

    # 10. Implementation Priority
    form_builder.add_radio(
        field_id="priority",
        label="What is the priority for implementing this agent?",
        options=[
            "Critical - Need this ASAP",
            "High - Important for workflow",
            "Medium - Nice to have soon",
            "Low - Can wait",
        ],
        required=True
    )

    form_builder.add_date(
        field_id="target_date",
        label="Target completion date (optional)",
        required=False
    )

    # Build the schema
    schema = form_builder.build()

    # Save to database
    async for session in get_db_session():
        repo = FormRepository(session)

        form_data = {
            "title": schema["title"],
            "description": schema.get("description"),
            "schema": schema,
            "status": "active",
            "issue_id": agent_design_issue_id,
            "created_by": "Claude",
            "created_by_type": "ai",
        }

        form = await repo.create_form(form_data)

        print(f"\n✓ Successfully created Agent Design Questions form!")
        print(f"  Form ID: {form.id}")
        print(f"  Title: {form.title}")
        print(f"  Attached to issue: {agent_design_issue_id}")
        print(f"  Fields: {len(schema['fields'])}")
        print(f"\nView the form at: http://localhost:3001/issues/{agent_design_issue_id}")

        return form


if __name__ == "__main__":
    asyncio.run(create_agent_design_form())

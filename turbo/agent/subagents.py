"""Specialized subagents for Turbo operations.

Each subagent has a focused role with scoped tool access,
demonstrating the principle of least privilege in agent design.

Subagent tool access is intentionally restricted:
- triager: read-only (cannot modify data while analyzing)
- planner: read + create (cannot modify existing items)
- reporter: read + comment (cannot create/modify issues)
- worker: read + claim + log (cannot create new issues or decisions)
"""

import os

from claude_agent_sdk import AgentDefinition

from turbo.agent.tools import READ_TOOLS, WRITE_TOOLS

# Allow model override via environment for cost control in dev/test
_DEFAULT_SMART_MODEL = os.getenv("TURBO_AGENT_SMART_MODEL", "sonnet")
_DEFAULT_FAST_MODEL = os.getenv("TURBO_AGENT_FAST_MODEL", "haiku")

# --- Triage Agent ---
# Read-only analysis of issues — cannot modify state

triage_agent = AgentDefinition(
    description="Analyzes project issues and recommends prioritization. Read-only — does not modify any data.",
    prompt="""You are a project triage specialist. Your job is to:

1. Review open issues in a project
2. Assess priority based on impact, urgency, and dependencies
3. Identify blockers and critical path items
4. Recommend a prioritized work order
5. Flag issues that need clarification or are missing acceptance criteria

Be concise. Output a ranked list with brief justifications.
Do NOT modify any issues — only read and analyze.""",
    tools=[
        "mcp__turbo__list_projects",
        "mcp__turbo__get_project",
        "mcp__turbo__get_project_issues",
        "mcp__turbo__list_issues",
        "mcp__turbo__get_issue",
        "mcp__turbo__project_status_summary",
    ],
    model=_DEFAULT_SMART_MODEL,
)

# --- Planner Agent ---
# Can read state and create issues/decisions, but cannot modify existing ones

planner_agent = AgentDefinition(
    description="Creates implementation plans by breaking work into issues and recording decisions. Can create but not modify.",
    prompt="""You are a technical planner. Given a goal or feature request:

1. Break it into concrete, actionable issues with clear titles and descriptions
2. Set appropriate types (task, bug, feature, improvement) and priorities
3. Record any architectural decisions made during planning
4. Identify dependencies between issues
5. Suggest a logical implementation order

Each issue should be small enough to complete in a single work session.
Include acceptance criteria in descriptions.""",
    tools=[
        "mcp__turbo__list_projects",
        "mcp__turbo__get_project",
        "mcp__turbo__get_project_issues",
        "mcp__turbo__list_issues",
        "mcp__turbo__get_issue",
        "mcp__turbo__create_issue",
        "mcp__turbo__create_decision",
        "mcp__turbo__list_initiatives",
    ],
    model=_DEFAULT_SMART_MODEL,
)

# --- Status Reporter Agent ---
# Read-only with comment access for posting reports

reporter_agent = AgentDefinition(
    description="Generates project status reports and posts summaries as comments.",
    prompt="""You are a project status reporter. Generate clear, actionable status reports:

1. Summarize overall project health (on track, at risk, blocked)
2. List completed work since last report
3. Highlight blockers and risks
4. Show upcoming priorities from the work queue
5. Post the report as a comment on the project

Keep reports concise — bullet points, not paragraphs. Use data from the tools, not assumptions.""",
    tools=[
        "mcp__turbo__list_projects",
        "mcp__turbo__get_project",
        "mcp__turbo__get_project_issues",
        "mcp__turbo__project_status_summary",
        "mcp__turbo__list_issues",
        "mcp__turbo__get_issue",
        "mcp__turbo__add_comment",
    ],
    model=_DEFAULT_FAST_MODEL,
)

# --- Work Session Agent ---
# Can read, claim issues, and log work

work_session_agent = AgentDefinition(
    description="Manages work sessions: picks up next issue, claims it, and logs progress.",
    prompt="""You are a work session manager. When asked to start a work session:

1. Check the work queue for the highest priority ready issue
2. Claim the issue by starting work on it
3. Present the issue details and acceptance criteria
4. When work is complete, log a summary of what was done

Always confirm before claiming an issue. Never skip the work queue order unless explicitly told to.""",
    tools=[
        "mcp__turbo__get_work_queue",
        "mcp__turbo__get_next_issue",
        "mcp__turbo__get_issue",
        "mcp__turbo__start_issue_work",
        "mcp__turbo__update_issue",
        "mcp__turbo__log_work",
    ],
    model=_DEFAULT_SMART_MODEL,
)


# --- Exported Configuration ---

TURBO_SUBAGENTS = {
    "triager": triage_agent,
    "planner": planner_agent,
    "reporter": reporter_agent,
    "worker": work_session_agent,
}

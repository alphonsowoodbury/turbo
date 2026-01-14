#!/usr/bin/env python3
"""
Turbo Event Listener - Comprehensive monitoring of Turbo-Plan with Claude Code agent responses.

Monitors ALL entity types and triggers Claude Code agents for:
- New issues, ideas, comments
- Assignments and status changes
- Work logs and progress updates
- Initiative and milestone changes
- Document updates
- Mentor conversations

Usage:
    python turbo_event_listener.py [--poll-interval 30] [--dry-run]

To run as a background service:
    launchctl load ~/Library/LaunchAgents/com.turbo.eventlistener.plist
"""

import argparse
import asyncio
import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

# Configuration
TURBO_API_URL = "https://turbo-plan.fly.dev/api/v1"
STATE_FILE = Path.home() / ".turbo_listener_state.json"
AGENT_LOG_FILE = Path("/tmp/turbo_agent_responses.log")
MCP_CONFIG_FILE = Path("/Volumes/Claude/.claude/.mcp.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


@dataclass
class EntityMonitor:
    """Configuration for monitoring an entity type."""
    name: str
    endpoint: str
    id_field: str = "id"
    title_field: str = "title"
    agent_prompt: str = ""
    extract_context: callable = None


# Define all monitored entities and their agent prompts
MONITORS = {
    "issues": EntityMonitor(
        name="issues",
        endpoint="/issues/",
        title_field="title",
        agent_prompt="""New issue in Turbo-Plan - ID: {id}
Title: {title} | Priority: {priority} | Status: {status}

ACTION REQUIRED: Use add_comment to post your analysis to this issue.

Your comment should include:
- Assessment of issue clarity (is the description sufficient?)
- Suggested priority if different from current
- Any questions for the author

Call add_comment with entity_type="issue", entity_id="{id}", and your analysis as content."""
    ),

    # Comments are fetched per-entity, skip global monitoring
    # WebSocket is better for real-time comment monitoring

    "initiatives": EntityMonitor(
        name="initiatives",
        endpoint="/initiatives/",
        title_field="name",
        agent_prompt="""New initiative created in Turbo-Plan:
- Name: {name}
- Description: {description}
- Status: {status}

Use turbo MCP tools to:
1. Review the initiative scope
2. Suggest initial milestones
3. Identify which existing projects might contribute
4. Draft an initial roadmap structure"""
    ),

    "projects": EntityMonitor(
        name="projects",
        endpoint="/projects/",
        title_field="name",
        agent_prompt="""New project created in Turbo-Plan:
- Name: {name}
- Description: {description}
- Key Prefix: {key_prefix}

Use turbo MCP tools to:
1. Set up initial project structure
2. Create a "Getting Started" document
3. Suggest initial issue categories/labels
4. Check if this should link to an initiative"""
    ),

    "documents": EntityMonitor(
        name="documents",
        endpoint="/documents/",
        title_field="title",
        agent_prompt="""New document created in Turbo-Plan:
- Title: {title}
- Type: {document_type}
- Project: {project_id}

Use turbo MCP tools to:
1. Review the document content
2. Suggest improvements or missing sections
3. Link to related issues or documents
4. Add appropriate tags"""
    ),

    "milestones": EntityMonitor(
        name="milestones",
        endpoint="/milestones/",
        title_field="title",
        agent_prompt="""New milestone created in Turbo-Plan:
- Title: {title}
- Due Date: {due_date}
- Initiative: {initiative_id}

Use turbo MCP tools to:
1. Review milestone scope
2. Identify issues that should be linked
3. Check if due date is realistic based on linked issues
4. Suggest success criteria"""
    ),

    # work_logs and notes endpoints not implemented yet
    # Uncomment when available:
    # "work_logs": EntityMonitor(...),
    # "notes": EntityMonitor(...),

    "tags": EntityMonitor(
        name="tags",
        endpoint="/tags/",
        title_field="name",
        agent_prompt="""New tag created in Turbo-Plan:
- Name: {name}
- Color: {color}
- Project: {project_id}

Use turbo MCP tools to:
1. Check for similar existing tags (potential duplicates)
2. Suggest which existing issues might use this tag
3. Consider if this should be a project-wide or global tag"""
    ),
}


def load_state() -> dict:
    """Load the last known state from disk."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            logger.warning("Corrupted state file, starting fresh")
    return {"entities": {}, "last_check": None}


def save_state(state: dict) -> None:
    """Save state to disk."""
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


def trigger_claude_agent(prompt: str, dry_run: bool = False) -> bool:
    """Trigger Claude Code in headless mode with the given prompt."""
    if dry_run:
        logger.info(f"[DRY RUN] Would trigger Claude with prompt:\n{prompt[:300]}...")
        return True

    try:
        logger.info("Triggering Claude Code agent...")
        result = subprocess.run(
            [
                "claude",
                "-p", prompt,
                "--mcp-config", str(MCP_CONFIG_FILE),
                "--allowedTools", "mcp__turbo__*",
                "--max-turns", "5",
            ],
            capture_output=True,
            text=True,
            timeout=180,  # 3 minute timeout
            cwd=str(Path.home()),
        )
        if result.returncode == 0:
            logger.info("Claude agent completed successfully")
            if result.stdout:
                # Log full response to dedicated file
                with open(AGENT_LOG_FILE, "a") as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
                    f.write(f"PROMPT:\n{prompt[:500]}...\n\n")
                    f.write(f"RESPONSE:\n{result.stdout}\n")
                logger.info(f"Agent response logged to {AGENT_LOG_FILE}")
            return True
        else:
            logger.warning(f"Claude agent exited with code {result.returncode}")
            if result.stderr:
                logger.debug(f"Stderr: {result.stderr[:300]}")
            return False
    except subprocess.TimeoutExpired:
        logger.warning("Claude agent timed out after 180 seconds")
        return False
    except FileNotFoundError:
        logger.error("Claude CLI not found. Make sure 'claude' is in your PATH.")
        return False
    except Exception as e:
        logger.error(f"Failed to trigger Claude agent: {e}")
        return False


async def fetch_entities(client: httpx.AsyncClient, endpoint: str) -> list[dict]:
    """Fetch all entities from an endpoint."""
    try:
        response = await client.get(f"{TURBO_API_URL}{endpoint}")
        if response.status_code == 404:
            return []
        response.raise_for_status()
        data = response.json()
        # Handle both list and paginated responses
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "items" in data:
            return data["items"]
        return []
    except httpx.HTTPStatusError as e:
        if e.response.status_code != 404:
            logger.error(f"HTTP error fetching {endpoint}: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to fetch {endpoint}: {e}")
        return []


def format_prompt(template: str, entity: dict) -> str:
    """Format a prompt template with entity data."""
    # Create a safe dict that returns 'N/A' for missing keys
    class SafeDict(dict):
        def __missing__(self, key):
            return "N/A"

    safe_entity = SafeDict(entity)

    # Handle nested or computed fields
    if "content" in entity and len(str(entity.get("content", ""))) > 200:
        safe_entity["content"] = str(entity["content"])[:200] + "..."

    try:
        return template.format_map(safe_entity)
    except Exception as e:
        logger.warning(f"Error formatting prompt: {e}")
        return template


async def check_entity_changes(
    client: httpx.AsyncClient,
    monitor: EntityMonitor,
    known_ids: set[str],
    dry_run: bool = False
) -> tuple[set[str], int]:
    """Check for new entities of a given type."""
    entities = await fetch_entities(client, monitor.endpoint)
    current_ids = {str(e.get(monitor.id_field)) for e in entities}

    # Find new entities
    new_ids = current_ids - known_ids
    triggered = 0

    for entity in entities:
        entity_id = str(entity.get(monitor.id_field))
        if entity_id in new_ids:
            title = entity.get(monitor.title_field, entity_id)
            logger.info(f"New {monitor.name}: {title[:50]}")

            if monitor.agent_prompt:
                prompt = format_prompt(monitor.agent_prompt, entity)
                if trigger_claude_agent(prompt, dry_run):
                    triggered += 1

    return current_ids, triggered


async def check_all_entities(
    client: httpx.AsyncClient,
    state: dict,
    dry_run: bool = False
) -> dict:
    """Check all monitored entity types for changes."""
    entities_state = state.get("entities", {})
    total_triggered = 0

    for name, monitor in MONITORS.items():
        known_ids = set(entities_state.get(name, []))
        current_ids, triggered = await check_entity_changes(
            client, monitor, known_ids, dry_run
        )
        entities_state[name] = list(current_ids)
        total_triggered += triggered

    if total_triggered > 0:
        logger.info(f"Triggered {total_triggered} Claude agents this cycle")

    state["entities"] = entities_state
    state["last_check"] = datetime.now(timezone.utc).isoformat()
    return state


async def initialize_state(client: httpx.AsyncClient) -> dict:
    """Initialize state with current entity IDs (without triggering agents)."""
    logger.info("Initializing state with current entities...")
    state = {"entities": {}, "last_check": None}

    for name, monitor in MONITORS.items():
        entities = await fetch_entities(client, monitor.endpoint)
        ids = [str(e.get(monitor.id_field)) for e in entities]
        state["entities"][name] = ids
        logger.info(f"  {name}: {len(ids)} existing items")

    state["last_check"] = datetime.now(timezone.utc).isoformat()
    return state


async def main(poll_interval: int = 30, dry_run: bool = False):
    """Main event loop."""
    logger.info("=" * 60)
    logger.info("Turbo Event Listener - Starting")
    logger.info("=" * 60)
    logger.info(f"API URL: {TURBO_API_URL}")
    logger.info(f"Poll interval: {poll_interval}s")
    logger.info(f"Dry run: {dry_run}")
    logger.info(f"Monitoring: {', '.join(MONITORS.keys())}")
    logger.info("=" * 60)

    state = load_state()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test API connection
        try:
            response = await client.get(f"{TURBO_API_URL.replace('/api/v1', '')}/")
            logger.info(f"API connection successful: {response.json()}")
        except Exception as e:
            logger.error(f"Cannot connect to API: {e}")
            logger.error("Make sure the Turbo API is running at the configured URL")
            sys.exit(1)

        # Initialize state if needed
        if not state.get("entities"):
            state = await initialize_state(client)
            save_state(state)
            logger.info("State initialized - now monitoring for changes")

        logger.info("Entering main loop...")

        while True:
            try:
                state = await check_all_entities(client, state, dry_run)
                save_state(state)
            except Exception as e:
                logger.error(f"Error during check cycle: {e}")
                import traceback
                logger.debug(traceback.format_exc())

            await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Turbo Event Listener - Monitor Turbo-Plan and trigger Claude agents"
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=30,
        help="Seconds between API polls (default: 30)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log events without triggering Claude agents"
    )
    parser.add_argument(
        "--reset-state",
        action="store_true",
        help="Clear saved state and start fresh"
    )
    args = parser.parse_args()

    if args.reset_state and STATE_FILE.exists():
        STATE_FILE.unlink()
        logger.info("State file cleared")

    try:
        asyncio.run(main(poll_interval=args.poll_interval, dry_run=args.dry_run))
    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")

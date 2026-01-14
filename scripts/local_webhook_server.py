#!/usr/bin/env python3
"""
Local Webhook Server for Turbo Code

Runs on the host machine and handles issue.ready webhooks by:
1. Creating git worktrees locally
2. Updating work logs in Turbo DB
3. Spawning Claude Code to work on the issue

Usage:
    python scripts/local_webhook_server.py

Environment Variables:
    TURBO_API_URL: Turbo API URL (default: http://localhost:8001/api/v1)
    WEBHOOK_PORT: Port to listen on (default: 9003)
    TURBO_PROJECT_PATH: Path to turboCode project (default: current directory)
    WORKTREE_BASE_PATH: Base path for worktrees (default: ~/worktrees)
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from aiohttp import web

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "9003"))
TURBO_API_URL = os.getenv("TURBO_API_URL", "http://localhost:8001/api/v1")
TURBO_PROJECT_PATH = Path(os.getenv("TURBO_PROJECT_PATH", os.getcwd()))
WORKTREE_BASE_PATH = Path(os.getenv("WORKTREE_BASE_PATH", Path.home() / "worktrees"))

# Ensure worktree base path exists
WORKTREE_BASE_PATH.mkdir(parents=True, exist_ok=True)


def sanitize_branch_name(text: str) -> str:
    """Sanitize text for use in git branch names."""
    # Replace spaces and special chars with hyphens
    sanitized = text.lower()
    sanitized = "".join(c if c.isalnum() or c in "-_" else "-" for c in sanitized)
    # Remove consecutive hyphens
    while "--" in sanitized:
        sanitized = sanitized.replace("--", "-")
    # Trim hyphens from ends
    sanitized = sanitized.strip("-")
    # Limit length
    return sanitized[:50]


def get_git_root(project_path: Path) -> Optional[Path]:
    """Find the git repository root for a project."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(project_path),
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        return None


async def create_worktree_locally(
    issue_key: str,
    issue_title: str,
    project_name: str,
    repository_path: Optional[str] = None,
    base_branch: str = "main"
) -> Dict[str, str]:
    """
    Create a git worktree locally on the host.

    Args:
        issue_key: Issue key (e.g., TURBOCODE-1)
        issue_title: Issue title for branch name
        project_name: Project name for worktree directory
        repository_path: Path to the project's git repository (if None, uses TURBO_PROJECT_PATH)
        base_branch: Base branch to create worktree from

    Returns:
        Dictionary with worktree_path and branch_name
    """
    # Use provided repository_path or fall back to TURBO_PROJECT_PATH
    project_path = Path(repository_path) if repository_path else TURBO_PROJECT_PATH

    # Verify project_path is a git repo
    git_root = get_git_root(project_path)
    if not git_root:
        raise ValueError(f"{project_path} is not a git repository")

    # Create branch name: TURBOCODE-1/fix-auth-bug
    sanitized_title = sanitize_branch_name(issue_title)
    branch_name = f"{issue_key}/{sanitized_title}"

    # Create worktree path: ~/worktrees/turboCode-TURBOCODE-1/
    worktree_name = f"{sanitize_branch_name(project_name)}-{issue_key.lower()}"
    worktree_path = WORKTREE_BASE_PATH / worktree_name

    # Check if worktree already exists and clean up if needed
    if worktree_path.exists():
        logger.warning(f"Worktree already exists at {worktree_path}, cleaning up...")
        # Remove the worktree directory
        subprocess.run(["git", "worktree", "remove", str(worktree_path), "--force"],
                      cwd=str(git_root), capture_output=True)
        # Prune worktree references
        subprocess.run(["git", "worktree", "prune"], cwd=str(git_root), capture_output=True)

    # Check if branch already exists and delete it
    branch_check = subprocess.run(
        ["git", "branch", "--list", branch_name],
        cwd=str(git_root),
        capture_output=True,
        text=True
    )
    if branch_check.stdout.strip():
        logger.warning(f"Branch {branch_name} already exists, deleting...")
        subprocess.run(["git", "branch", "-D", branch_name], cwd=str(git_root), capture_output=True)

    # Create the worktree
    try:
        subprocess.run(
            ["git", "worktree", "add", "-b", branch_name, str(worktree_path), base_branch],
            cwd=str(git_root),
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info(f"✓ Created worktree at {worktree_path}")
        logger.info(f"  Branch: {branch_name}")
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Failed to create worktree: {e.stderr}")

    return {
        "worktree_path": str(worktree_path),
        "branch_name": branch_name,
    }


async def update_work_log(
    issue_id: str,
    worktree_path: str,
    branch_name: str
) -> None:
    """
    Update the work log in Turbo DB with worktree information.

    Directly inserts into the database since there's no work-logs API endpoint.
    """
    import asyncpg
    from datetime import datetime
    import uuid

    # Connect directly to the database
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="turbo",
        password="turbo_password",
        database="turbo",
    )

    try:
        # Insert work log
        await conn.execute("""
            INSERT INTO issue_work_logs (id, issue_id, started_at, started_by, worktree_path, branch_name, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, uuid.uuid4(), uuid.UUID(issue_id), datetime.utcnow(), "ai:local-webhook",
            worktree_path, branch_name, datetime.utcnow(), datetime.utcnow())

        # Update issue status to in_progress
        await conn.execute("""
            UPDATE issues SET status = 'in_progress', updated_at = $1 WHERE id = $2
        """, datetime.utcnow(), uuid.UUID(issue_id))

        logger.info(f"✓ Created work log for issue {issue_id}")
        logger.info(f"✓ Updated issue status to in_progress")
    finally:
        await conn.close()


async def spawn_claude_code(
    worktree_path: str,
    issue_key: str,
    issue_title: str,
    issue_description: str,
    issue_id: str
) -> None:
    """
    Spawn a Claude Code process to work on the issue.

    Runs Claude Code CLI in non-interactive mode to implement the issue.
    """
    logger.info(f"🤖 Spawning Claude Code for {issue_key}")
    logger.info(f"   Working directory: {worktree_path}")

    # Generate a session ID for tracking
    import uuid
    session_id = str(uuid.uuid4())

    # Create the prompt for Claude Code
    prompt = f"""You are an AI developer working on issue {issue_key}: {issue_title}

## Issue Description
{issue_description}

## Context
- You are in a git worktree at: {worktree_path}
- Branch: {issue_key}/...
- This is an isolated environment for this specific issue

## Your Task
1. Analyze the issue requirements
2. Implement the necessary changes
3. Follow the project's coding standards (check CLAUDE.md if present)
4. Test your changes
5. Commit with a clear message: "{issue_key}: {issue_title}"

## Important Guidelines
- Make focused, incremental changes
- Write clear, maintainable code
- Add tests if applicable
- Update documentation if needed
- Use meaningful commit messages

Please proceed with implementing this issue. When complete, commit your changes.
"""

    # Prepare Claude Code command
    claude_cmd = [
        "claude",
        "--print",  # Non-interactive mode
        "--dangerously-skip-permissions",  # Auto-approve all operations (safe in isolated worktree)
        "--output-format", "json",
        "--session-id", session_id,
        "--model", "sonnet",  # Use latest Sonnet
        "--append-system-prompt", f"You are working on issue {issue_key} in a git worktree. Always commit your changes when done.",
        prompt
    ]

    logger.info(f"🚀 Starting Claude Code session {session_id[:8]}...")

    # Run Claude Code asynchronously in the worktree directory
    try:
        # Create log directory for session output
        log_dir = Path.home() / ".turbo" / "sessions" / issue_key
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{session_id[:8]}.log"

        # Spawn Claude Code process
        process = await asyncio.create_subprocess_exec(
            *claude_cmd,
            cwd=worktree_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        logger.info(f"✓ Claude Code process started (PID: {process.pid})")
        logger.info(f"📝 Session logs: {log_file}")

        # Register session with agent activity tracker
        async with httpx.AsyncClient() as client:
            # Start agent session
            try:
                await client.post(
                    f"{TURBO_API_URL}/agents/activity/start",
                    json={
                        "session_id": session_id,
                        "entity_type": "issue",
                        "entity_id": issue_id,
                        "entity_title": f"{issue_key}: {issue_title}",
                        "started_by": "AutoCoder"
                    },
                    timeout=30.0,
                )
                logger.info(f"✓ Registered agent session {session_id[:8]}")
            except Exception as e:
                logger.error(f"Failed to register agent session: {e}")

        # Run in background and capture output
        async def capture_output():
            stdout, stderr = await process.communicate()

            # Write logs
            with open(log_file, 'w') as f:
                f.write(f"=== Claude Code Session {session_id} ===\n")
                f.write(f"Issue: {issue_key}\n")
                f.write(f"Worktree: {worktree_path}\n\n")
                f.write("=== STDOUT ===\n")
                f.write(stdout.decode('utf-8', errors='replace'))
                f.write("\n\n=== STDERR ===\n")
                f.write(stderr.decode('utf-8', errors='replace'))

            # Parse JSON output
            try:
                result = json.loads(stdout.decode('utf-8'))
                usage = result.get('usage', {})
                input_tokens = usage.get('input_tokens', 0)
                output_tokens = usage.get('output_tokens', 0)

                logger.info(f"✓ Claude Code session completed for {issue_key}")
                logger.info(f"   Output tokens: {output_tokens}")

                # Complete agent session
                async with httpx.AsyncClient() as client:
                    try:
                        await client.post(
                            f"{TURBO_API_URL}/agents/activity/complete",
                            json={
                                "session_id": session_id,
                                "status": "completed",
                                "input_tokens": input_tokens,
                                "output_tokens": output_tokens
                            },
                            timeout=30.0,
                        )
                        logger.info(f"✓ Completed agent session {session_id[:8]}")
                    except Exception as e:
                        logger.error(f"Failed to complete agent session: {e}")

            except json.JSONDecodeError:
                logger.error(f"Failed to parse Claude Code output for {issue_key}")

                # Mark session as error
                async with httpx.AsyncClient() as client:
                    try:
                        await client.post(
                            f"{TURBO_API_URL}/agents/activity/complete",
                            json={
                                "session_id": session_id,
                                "status": "error",
                                "error": "Failed to parse Claude Code output"
                            },
                            timeout=30.0,
                        )
                    except Exception as e:
                        logger.error(f"Failed to mark session as error: {e}")

        # Schedule background task
        asyncio.create_task(capture_output())

    except Exception as e:
        logger.error(f"Failed to spawn Claude Code for {issue_key}: {str(e)}", exc_info=True)
        # Post error comment
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{TURBO_API_URL}/comments/entity/issue/{issue_id}",
                json={
                    "content": f"❌ Failed to start automated implementation\n\n**Error:** {str(e)}",
                    "author_type": "ai",
                    "author_name": "AutoCoder"
                },
                timeout=30.0,
            )


async def handle_issue_ready(request: web.Request) -> web.Response:
    """Handle issue.ready webhook event."""
    try:
        payload = await request.json()
        logger.info(f"Received issue.ready event: {json.dumps(payload, indent=2)}")

        issue = payload.get("issue", {})
        issue_id = issue.get("id")
        issue_key = issue.get("issue_key")
        issue_title = issue.get("title")
        issue_description = issue.get("description", "")
        project_id = payload.get("project_id")

        if not all([issue_id, issue_key, issue_title]):
            return web.json_response(
                {"error": "Missing required fields"},
                status=400
            )

        # Fetch project details to get project name and repository path
        async with httpx.AsyncClient() as client:
            project_response = await client.get(
                f"{TURBO_API_URL}/projects/{project_id}",
                timeout=30.0,
            )
            project_response.raise_for_status()
            project = project_response.json()
            project_name = project.get("name", "unknown")
            repository_path = project.get("repository_path")

        logger.info(f"📋 Processing {issue_key}: {issue_title}")
        logger.info(f"   Project: {project_name}")
        if repository_path:
            logger.info(f"   Repository: {repository_path}")
        else:
            logger.warning(f"   No repository_path configured, using default: {TURBO_PROJECT_PATH}")

        # Step 1: Create worktree locally
        worktree_info = await create_worktree_locally(
            issue_key=issue_key,
            issue_title=issue_title,
            project_name=project_name,
            repository_path=repository_path,
        )

        # Step 2: Update work log in Turbo DB
        await update_work_log(
            issue_id=issue_id,
            worktree_path=worktree_info["worktree_path"],
            branch_name=worktree_info["branch_name"],
        )

        # Step 3: Spawn Claude Code in the worktree
        await spawn_claude_code(
            worktree_path=worktree_info["worktree_path"],
            issue_key=issue_key,
            issue_title=issue_title,
            issue_description=issue_description,
            issue_id=issue_id,
        )

        return web.json_response({
            "status": "success",
            "issue_key": issue_key,
            "worktree_path": worktree_info["worktree_path"],
            "branch_name": worktree_info["branch_name"],
        })

    except Exception as e:
        logger.error(f"Error handling issue.ready webhook: {str(e)}", exc_info=True)
        return web.json_response(
            {"error": str(e)},
            status=500
        )


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({
        "status": "healthy",
        "service": "turbo-local-webhook",
        "worktree_base": str(WORKTREE_BASE_PATH),
        "project_path": str(TURBO_PROJECT_PATH),
    })


async def start_server():
    """Start the webhook server."""
    app = web.Application()
    app.router.add_post("/webhook/issue-ready", handle_issue_ready)
    app.router.add_get("/health", health_check)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
    await site.start()

    logger.info(f"🚀 Local webhook server started on port {WEBHOOK_PORT}")
    logger.info(f"📂 Project path: {TURBO_PROJECT_PATH}")
    logger.info(f"🌳 Worktree base: {WORKTREE_BASE_PATH}")
    logger.info(f"🔗 Turbo API: {TURBO_API_URL}")
    logger.info(f"")
    logger.info(f"Endpoints:")
    logger.info(f"  POST http://localhost:{WEBHOOK_PORT}/webhook/issue-ready")
    logger.info(f"  GET  http://localhost:{WEBHOOK_PORT}/health")

    # Keep the server running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(start_server())

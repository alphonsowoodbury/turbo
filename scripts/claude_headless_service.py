#!/usr/bin/env python3
"""
Claude Headless Service for Turbo

This service provides AI subagents using Claude Code CLI in headless mode.

Agent set:
- turbo: In-app agents for end users (this service)
"""

import asyncio
import hashlib
import hmac
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import httpx
import asyncpg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Turbo Claude Service")

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUBAGENTS_DIR = Path("/app/subagents")
SKILLS_DIR = Path("/app/skills")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://turbo-api:8000")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://turbo:turbo_password@postgres:5432/turbo")
CLAUDE_API_KEY = ""  # Will be fetched from database at startup
WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", "/workspace"))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "turbo-webhook-secret-change-me")


class SubagentRequest(BaseModel):
    """Request to invoke a subagent"""
    agent: str
    prompt: str
    context: Optional[Dict[str, Any]] = None
    agent_set: str = "turbo"


class SubagentResponse(BaseModel):
    """Response from subagent"""
    agent: str
    response: str
    actions: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class IssueWebhookPayload(BaseModel):
    """Webhook payload for issue events (assigned, implementation_requested)"""
    issue: Dict[str, Any]
    assigned_to_type: Optional[str] = None
    assigned_to_id: Optional[str] = None
    project_id: Optional[str] = None
    request_notes: Optional[str] = None
    priority_override: Optional[str] = None


class ClaudeAPIClient:
    """Anthropic API client for Claude invocations"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-sonnet-4-5-20250929"

    async def invoke(
        self,
        system_prompt: str,
        prompt: str,
        context: Dict,
        tools: List[str]
    ) -> str:
        """Invoke Claude via Anthropic API"""

        # Build full prompt with context
        full_prompt = prompt
        if context:
            full_prompt = f"Context:\n{json.dumps(context, indent=2)}\n\n{prompt}"

        # Build API request
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": full_prompt
                }
            ]
        }

        # Note: MCP tools not yet supported in direct API calls
        logger.info(f"Invoking Claude API (model: {payload['model']})")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                error_msg = f"API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)

            result = response.json()
            return result["content"][0]["text"]


class ClaudeCodeCLI:
    """Claude Code CLI client for headless invocations"""

    def __init__(self):
        self.claude_command = "claude"
        self._check_cli_available()

    def _check_cli_available(self):
        """Check if Claude Code CLI is installed"""
        try:
            result = subprocess.run(
                [self.claude_command, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"Claude Code CLI available: {result.stdout.strip()}")
            else:
                logger.warning("Claude Code CLI not responding correctly")
        except FileNotFoundError:
            logger.error("Claude Code CLI not found - ensure 'claude' is installed and in PATH")
        except Exception as e:
            logger.error(f"Error checking Claude CLI: {e}")

    async def invoke(
        self,
        prompt: str,
        working_dir: Optional[Path] = None,
        allowed_tools: Optional[List[str]] = None,
        output_format: str = "stream-json"
    ) -> str:
        """
        Invoke Claude Code CLI in headless mode.

        Args:
            prompt: The prompt to send to Claude
            working_dir: Working directory for Claude execution
            allowed_tools: List of tools Claude can use (e.g., ["Bash", "Read", "Write"])
            output_format: Output format (text, json, stream-json)

        Returns:
            Claude's response text
        """
        command = [
            self.claude_command,
            "-p", prompt,
            "--output-format", output_format
        ]

        # Add --verbose flag for stream-json format (required by Claude CLI)
        if output_format == "stream-json":
            command.append("--verbose")

        if allowed_tools:
            command.extend(["--allowedTools", ",".join(allowed_tools)])

        logger.info(f"Invoking Claude Code CLI: {command[0]} -p <prompt> --output-format {output_format}")

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(working_dir) if working_dir else None
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300.0  # 5 minute timeout
            )

            if process.returncode != 0:
                error_msg = f"Claude CLI error (code {process.returncode}): {stderr.decode()}"
                logger.error(error_msg)
                raise Exception(error_msg)

            # Parse streaming JSON output
            output = stdout.decode()
            response_text = self._parse_claude_output(output, output_format)

            return response_text

        except asyncio.TimeoutError:
            raise Exception("Claude CLI timed out after 5 minutes")
        except Exception as e:
            logger.error(f"Error invoking Claude CLI: {e}")
            raise

    def _parse_claude_output(self, output: str, format: str) -> str:
        """Parse Claude CLI output based on format"""
        if format == "text":
            return output

        # For JSON and stream-json, extract assistant messages
        response_parts = []
        for line in output.strip().split("\n"):
            if not line.strip():
                continue

            try:
                msg = json.loads(line)
                if msg.get("type") == "message" and msg.get("role") == "assistant":
                    content = msg.get("content", [])
                    for block in content:
                        if block.get("type") == "text":
                            response_parts.append(block.get("text", ""))
            except json.JSONDecodeError:
                # Not JSON, might be final message
                continue

        if response_parts:
            return "\n".join(response_parts)

        # Fallback to raw output
        return output


class GitWorkflowHandler:
    """Handles git operations for issue implementation"""

    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    async def setup_workspace(self, issue: Dict) -> Path:
        """
        Set up a workspace for implementing an issue.

        Args:
            issue: Issue data including id, title, project_id, etc.

        Returns:
            Path to the working directory
        """
        issue_id = issue["id"]
        work_dir = self.workspace_dir / f"issue-{issue_id}"

        # Clean up existing workspace
        if work_dir.exists():
            shutil.rmtree(work_dir)

        work_dir.mkdir(parents=True)
        logger.info(f"Created workspace: {work_dir}")

        return work_dir

    async def clone_repo(self, repo_url: str, work_dir: Path) -> bool:
        """Clone a repository to the work directory"""
        try:
            process = await asyncio.create_subprocess_exec(
                "git", "clone", repo_url, str(work_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"Git clone failed: {stderr.decode()}")
                return False

            logger.info(f"Cloned repo: {repo_url}")
            return True

        except Exception as e:
            logger.error(f"Error cloning repo: {e}")
            return False

    async def create_branch(self, work_dir: Path, branch_name: str) -> bool:
        """Create and checkout a new git branch"""
        try:
            # Create branch
            process = await asyncio.create_subprocess_exec(
                "git", "checkout", "-b", branch_name,
                cwd=str(work_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"Git branch creation failed: {stderr.decode()}")
                return False

            logger.info(f"Created branch: {branch_name}")
            return True

        except Exception as e:
            logger.error(f"Error creating branch: {e}")
            return False

    async def commit_changes(self, work_dir: Path, message: str) -> bool:
        """Commit all changes with the given message"""
        try:
            # Stage all changes
            process = await asyncio.create_subprocess_exec(
                "git", "add", "-A",
                cwd=str(work_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()

            # Commit
            process = await asyncio.create_subprocess_exec(
                "git", "commit", "-m", message,
                cwd=str(work_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                # Check if it's just "nothing to commit"
                if "nothing to commit" in stderr.decode():
                    logger.info("No changes to commit")
                    return True
                logger.error(f"Git commit failed: {stderr.decode()}")
                return False

            logger.info(f"Committed changes: {message}")
            return True

        except Exception as e:
            logger.error(f"Error committing changes: {e}")
            return False


class ClaudeCodeService:
    """Manages Claude subagent invocations"""

    def __init__(self):
        self.subagent_registry = self._load_registry()
        self.api_client = self._create_api_client()
        self.cli_client = ClaudeCodeCLI()
        self.git_handler = GitWorkflowHandler(WORKSPACE_DIR)
        self._check_claude_auth()

    async def post_comment_to_issue(self, issue_id: str, content: str) -> bool:
        """
        Post a comment to an issue via Turbo API

        Args:
            issue_id: UUID of the issue
            content: Comment text

        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{MCP_SERVER_URL}/api/v1/comments/"
            payload = {
                "entity_type": "issue",
                "entity_id": issue_id,
                "content": content,
                "author_type": "ai",
                "author_name": "Claude Code"
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)

                if response.status_code in [200, 201]:
                    logger.info(f"Posted comment to issue {issue_id}")
                    return True
                else:
                    logger.warning(f"Failed to post comment: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error posting comment to issue {issue_id}: {e}")
            return False

    def _create_api_client(self) -> ClaudeAPIClient:
        """Create the Claude API client"""
        if not CLAUDE_API_KEY:
            logger.warning("No API key configured")
            return None
        return ClaudeAPIClient(CLAUDE_API_KEY)

    def _load_registry(self) -> Dict:
        """Load subagent configurations"""
        registry_path = SUBAGENTS_DIR / "registry.json"
        if not registry_path.exists():
            logger.warning(f"Registry not found at {registry_path}")
            return {"subagents": []}

        with open(registry_path) as f:
            return json.load(f)

    def _check_claude_auth(self):
        """Verify Claude Code is authenticated"""
        if not CLAUDE_API_KEY:
            logger.error("ANTHROPIC_API_KEY not set!")
            return

        # Set API key for Claude CLI
        os.environ["ANTHROPIC_API_KEY"] = CLAUDE_API_KEY
        logger.info("Claude Code authentication configured")

    def _get_subagent_config(self, agent_name: str, agent_set: str) -> Optional[Dict]:
        """Get subagent configuration"""
        for subagent in self.subagent_registry.get("subagents", []):
            if subagent["name"] == agent_name and subagent.get("agent_set") == agent_set:
                return subagent
        return None

    async def invoke_subagent(
        self,
        agent_name: str,
        prompt: str,
        context: Optional[Dict] = None,
        agent_set: str = "turbo"
    ) -> SubagentResponse:
        """
        Invoke a Claude Code subagent headlessly

        Args:
            agent_name: Name of subagent (e.g., "issue-triager")
            prompt: User prompt
            context: Additional context data
            agent_set: "turbo" (in-container) or "turbodev" (host)
        """
        logger.info(f"Invoking subagent: {agent_name} (set: {agent_set})")

        # Only handle "turbo" agents in this service
        if agent_set != "turbo":
            return SubagentResponse(
                agent=agent_name,
                response="",
                error=f"This service only handles 'turbo' agents. '{agent_set}' agents are not available."
            )

        # Get configuration
        config = self._get_subagent_config(agent_name, agent_set)
        if not config:
            return SubagentResponse(
                agent=agent_name,
                response="",
                error=f"Subagent '{agent_name}' not found in '{agent_set}' agent set"
            )

        # Check if API client is available
        if not self.api_client:
            return SubagentResponse(
                agent=agent_name,
                response="",
                error="API key not configured. Please add your Anthropic API key in Settings."
            )

        try:
            # Invoke Claude using API
            result = await self.api_client.invoke(
                system_prompt=config["systemPrompt"],
                prompt=prompt,
                context=context or {},
                tools=config.get("tools", [])
            )

            # Parse response
            response_text, actions = self._parse_response(result)

            return SubagentResponse(
                agent=agent_name,
                response=response_text,
                actions=actions
            )

        except Exception as e:
            logger.error(f"Error invoking subagent {agent_name}: {e}")
            return SubagentResponse(
                agent=agent_name,
                response="",
                error=str(e)
            )

    def _parse_response(self, response: str) -> tuple[str, Optional[List[Dict]]]:
        """Parse Claude response and extract actions if present"""
        actions = None
        response_text = response

        # Look for JSON actions block (format: ```json\n{...}\n```)
        if "```json" in response:
            try:
                start = response.index("```json") + 7
                end = response.index("```", start)
                actions_json = response[start:end].strip()
                actions = json.loads(actions_json)

                # Remove actions block from response text
                before = response[:response.index("```json")]
                after = response[end + 3:]
                response_text = (before + after).strip()

            except (ValueError, json.JSONDecodeError) as e:
                logger.warning(f"Could not parse actions block: {e}")

        return response_text, actions

    def list_subagents(self, agent_set: str = "turbo") -> List[Dict]:
        """List available subagents for an agent set"""
        return [
            {
                "name": sub["name"],
                "description": sub.get("description", ""),
                "capabilities": sub.get("capabilities", []),
                "agent_set": sub.get("agent_set", "turbo")
            }
            for sub in self.subagent_registry.get("subagents", [])
            if sub.get("agent_set") == agent_set
        ]

    async def implement_issue(self, payload: IssueWebhookPayload) -> Dict:
        """
        Implement an issue using Claude Code CLI

        Args:
            payload: Webhook payload containing issue details

        Returns:
            Dict with implementation results
        """
        issue = payload.issue
        issue_id = issue.get("id")
        issue_title = issue.get("title", "Untitled Issue")
        issue_description = issue.get("description", "")
        project_id = payload.project_id

        logger.info(f"Starting implementation for issue {issue_id}: {issue_title}")

        # Post a comment to the issue indicating work has started
        from datetime import datetime, timezone
        comment_parts = [
            f"🤖 **Claude Code** is beginning autonomous implementation of this issue.",
            f"**Started:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
        ]

        if payload.request_notes:
            comment_parts.append(f"**Notes:** {payload.request_notes}")

        if payload.priority_override:
            comment_parts.append(f"**Priority Override:** {payload.priority_override}")

        comment_text = "\n\n".join(comment_parts)
        await self.post_comment_to_issue(issue_id, comment_text)

        try:
            # Setup workspace
            work_dir = await self.git_handler.setup_workspace(issue)
            logger.info(f"Workspace created at {work_dir}")

            # For now, we'll assume the repo is mounted or available
            # In production, you'd clone from a git URL
            # repo_url = issue.get("repository_url")
            # if repo_url:
            #     await self.git_handler.clone_repo(repo_url, work_dir)

            # Create branch for this issue
            branch_name = f"issue-{issue_id}"
            await self.git_handler.create_branch(work_dir, branch_name)
            logger.info(f"Created branch: {branch_name}")

            # Build prompt for Claude
            priority = payload.priority_override or issue.get("priority", "medium")
            prompt = f"""You are implementing the following issue:

Title: {issue_title}

Description:
{issue_description}

Type: {issue.get("type", "feature")}
Priority: {priority}"""

            if payload.request_notes:
                prompt += f"""

Implementation Notes:
{payload.request_notes}"""

            prompt += """

Please implement this issue by:
1. Analyzing the requirements
2. Making necessary code changes
3. Following best practices for the codebase

You have access to all necessary tools (Bash, Read, Write, Edit, Grep, Glob).
Work in the current directory which is the project repository.
"""

            # Invoke Claude Code CLI
            logger.info("Invoking Claude Code CLI...")
            result = await self.cli_client.invoke(
                prompt=prompt,
                working_dir=work_dir,
                allowed_tools=["Bash", "Read", "Write", "Edit", "Grep", "Glob"],
                output_format="stream-json"
            )

            logger.info("Claude Code CLI execution completed")

            # Commit changes
            commit_message = f"Implement issue #{issue_id}: {issue_title}\n\n{issue_description}"
            commit_success = await self.git_handler.commit_changes(work_dir, commit_message)

            if commit_success:
                logger.info(f"Changes committed successfully for issue {issue_id}")
            else:
                logger.warning(f"No changes to commit for issue {issue_id}")

            return {
                "success": True,
                "issue_id": issue_id,
                "branch_name": branch_name,
                "work_dir": str(work_dir),
                "committed": commit_success,
                "result": result
            }

        except Exception as e:
            logger.error(f"Error implementing issue {issue_id}: {e}", exc_info=True)
            return {
                "success": False,
                "issue_id": issue_id,
                "error": str(e)
            }


# Initialize service
service = ClaudeCodeService()


# API Endpoints

@app.post("/api/v1/subagents/invoke", response_model=SubagentResponse)
async def invoke_subagent(request: SubagentRequest):
    """Invoke a subagent with a prompt"""
    return await service.invoke_subagent(
        agent_name=request.agent,
        prompt=request.prompt,
        context=request.context,
        agent_set=request.agent_set
    )


@app.get("/api/v1/subagents/list")
async def list_subagents(agent_set: str = "turbo"):
    """List available subagents"""
    return {
        "agent_set": agent_set,
        "subagents": service.list_subagents(agent_set)
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "claude-api",
        "authenticated": bool(CLAUDE_API_KEY)
    }


@app.get("/config")
async def get_config():
    """Get current configuration"""
    return {
        "mcp_server": MCP_SERVER_URL,
        "subagents_count": len(service.list_subagents("turbo")),
        "model": "claude-sonnet-4-5-20250929"
    }


@app.post("/webhook/implementation-requested")
async def handle_implementation_requested_webhook(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None)
):
    """
    Handle issue.implementation_requested webhook from Turbo

    This endpoint receives webhooks when autonomous implementation is requested
    for an issue via the /request-implementation endpoint.
    """
    # Read raw body for signature verification
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")

    # Verify HMAC signature
    if x_webhook_signature:
        expected_signature = f"sha256={hmac.new(WEBHOOK_SECRET.encode('utf-8'), body_bytes, hashlib.sha256).hexdigest()}"
        if not hmac.compare_digest(x_webhook_signature, expected_signature):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
    else:
        logger.warning("No webhook signature provided")
        # In development, you might want to allow this, but in production it should be required
        # raise HTTPException(status_code=401, detail="Missing signature")

    try:
        # Parse payload
        payload_dict = json.loads(body_str)
        payload = IssueWebhookPayload(**payload_dict)

        logger.info(f"Received issue.implementation_requested webhook for issue {payload.issue.get('id')}")

        # Process the issue implementation asynchronously
        # Note: In production, you might want to use a background task queue
        result = await service.implement_issue(payload)

        return {
            "status": "accepted",
            "message": f"Issue implementation started for issue {payload.issue.get('id')}",
            "result": result
        }

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reload")
async def reload_api_key(request: dict):
    """Reload API key"""
    global CLAUDE_API_KEY

    # Update API key if provided
    new_api_key = request.get("api_key")
    if not new_api_key:
        raise HTTPException(status_code=400, detail="API key required")

    CLAUDE_API_KEY = new_api_key
    os.environ["ANTHROPIC_API_KEY"] = new_api_key
    logger.info("API key updated successfully")

    # Recreate API client with new key
    service.api_client = service._create_api_client()

    return {
        "success": True,
        "api_key_configured": bool(CLAUDE_API_KEY)
    }


async def fetch_api_key_from_database():
    """Fetch Anthropic API key from database settings table"""
    global CLAUDE_API_KEY

    try:
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            # Query settings table for anthropic_api_key
            row = await conn.fetchrow(
                "SELECT value FROM settings WHERE key = $1",
                "anthropic_api_key"
            )

            if row and row['value']:
                # Parse JSON value
                value_data = json.loads(row['value']) if isinstance(row['value'], str) else row['value']
                api_key = value_data.get('api_key', '')

                if api_key:
                    CLAUDE_API_KEY = api_key
                    os.environ["ANTHROPIC_API_KEY"] = api_key
                    logger.info("API key fetched from database successfully")
                    return True
                else:
                    logger.warning("API key found in database but is empty")
                    return False
            else:
                logger.warning("No API key found in database settings")
                return False
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error fetching API key from database: {e}")
        return False


if __name__ == "__main__":
    import uvicorn

    # Fetch API key from database before starting
    asyncio.run(fetch_api_key_from_database())

    port = int(os.getenv("SERVICE_PORT", "9000"))
    logger.info(f"Starting Claude API Service on port {port}")
    logger.info(f"Model: claude-sonnet-4-5-20250929")
    logger.info(f"MCP Server: {MCP_SERVER_URL}")
    logger.info(f"API Key configured: {bool(CLAUDE_API_KEY)}")

    uvicorn.run(app, host="0.0.0.0", port=port)

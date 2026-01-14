"""
Claude Code Service for Turbo

This service integrates Claude Code CLI into Turbo, providing two agent sets:
1. turbo - In-app agents for end users (project management, organization)
2. turbodev - External agents for development work (code editing, refactoring)
"""

import asyncio
import json
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Turbo Claude Service")

# Subagent registry
SUBAGENTS_DIR = Path("/workspace/subagents")
SKILLS_DIR = Path("/workspace/skills")


class SubagentRequest(BaseModel):
    """Request to invoke a subagent"""
    agent: str  # e.g., "issue-triager", "project-manager"
    prompt: str
    context: Optional[Dict[str, Any]] = None
    agent_set: str = "turbo"  # "turbo" or "turbodev"


class SubagentResponse(BaseModel):
    """Response from subagent invocation"""
    agent: str
    response: str
    actions: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class ClaudeCodeService:
    """Service for managing Claude Code subagents"""

    def __init__(self):
        self.subagent_registry = self._load_subagent_registry()
        self.mcp_server_url = "http://turbo-api:8000"

    def _load_subagent_registry(self) -> Dict[str, Any]:
        """Load subagent configurations"""
        registry_path = SUBAGENTS_DIR / "registry.json"
        if registry_path.exists():
            with open(registry_path) as f:
                return json.load(f)
        return {"subagents": []}

    async def invoke_subagent(
        self,
        agent_name: str,
        prompt: str,
        context: Optional[Dict] = None,
        agent_set: str = "turbo"
    ) -> SubagentResponse:
        """
        Invoke a Claude Code subagent

        Args:
            agent_name: Name of the subagent (e.g., "issue-triager")
            prompt: User prompt for the subagent
            context: Additional context (issue IDs, project ID, etc.)
            agent_set: "turbo" (in-app) or "turbodev" (development)
        """
        # Find subagent config
        subagent_config = self._get_subagent_config(agent_name, agent_set)
        if not subagent_config:
            return SubagentResponse(
                agent=agent_name,
                response="",
                error=f"Subagent '{agent_name}' not found in '{agent_set}' agent set"
            )

        # Build Claude Code command
        command = self._build_claude_command(
            agent_name=agent_name,
            system_prompt=subagent_config["systemPrompt"],
            prompt=prompt,
            context=context,
            tools=subagent_config.get("tools", [])
        )

        try:
            # Execute Claude Code CLI
            result = await self._execute_claude_code(command)

            # Parse response and extract actions
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

    def _get_subagent_config(self, agent_name: str, agent_set: str) -> Optional[Dict]:
        """Get subagent configuration from registry"""
        for subagent in self.subagent_registry.get("subagents", []):
            if subagent["name"] == agent_name and subagent.get("agent_set") == agent_set:
                return subagent
        return None

    def _build_claude_command(
        self,
        agent_name: str,
        system_prompt: str,
        prompt: str,
        context: Optional[Dict],
        tools: List[str]
    ) -> List[str]:
        """Build Claude Code CLI command"""

        # Create system prompt file
        system_prompt_file = SUBAGENTS_DIR / f"{agent_name}_system.txt"
        system_prompt_file.write_text(system_prompt)

        # Build full prompt with context
        full_prompt = prompt
        if context:
            full_prompt = f"Context: {json.dumps(context, indent=2)}\n\n{prompt}"

        # Claude Code CLI command
        command = [
            "claude-code",
            "--api-key", "$ANTHROPIC_API_KEY",
            "--mcp-server", self.mcp_server_url,
            "--system-prompt-file", str(system_prompt_file),
            "--tools", ",".join(tools),
            "--message", full_prompt
        ]

        return command

    async def _execute_claude_code(self, command: List[str]) -> str:
        """Execute Claude Code CLI command"""
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"Claude Code CLI error: {stderr.decode()}")

        return stdout.decode()

    def _parse_response(self, response: str) -> tuple[str, Optional[List[Dict]]]:
        """Parse Claude Code response and extract suggested actions"""
        # Try to extract JSON actions block if present
        actions = None
        response_text = response

        # Look for JSON actions block
        if "```json" in response:
            try:
                start = response.index("```json") + 7
                end = response.index("```", start)
                actions_json = response[start:end].strip()
                actions = json.loads(actions_json)

                # Remove actions block from response text
                response_text = response[:response.index("```json")] + response[end+3:]
            except (ValueError, json.JSONDecodeError) as e:
                logger.warning(f"Could not parse actions block: {e}")

        return response_text.strip(), actions

    def list_subagents(self, agent_set: str = "turbo") -> List[Dict[str, Any]]:
        """List available subagents for an agent set"""
        return [
            {
                "name": subagent["name"],
                "description": subagent.get("description", ""),
                "capabilities": subagent.get("capabilities", []),
                "agent_set": subagent.get("agent_set", "turbo")
            }
            for subagent in self.subagent_registry.get("subagents", [])
            if subagent.get("agent_set") == agent_set
        ]


# Initialize service
claude_service = ClaudeCodeService()


# API Endpoints

@app.post("/api/v1/subagents/invoke", response_model=SubagentResponse)
async def invoke_subagent(request: SubagentRequest):
    """Invoke a subagent with a prompt"""
    return await claude_service.invoke_subagent(
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
        "subagents": claude_service.list_subagents(agent_set)
    }


@app.get("/api/v1/subagents/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "claude-code"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)

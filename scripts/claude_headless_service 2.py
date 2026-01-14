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
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY", os.getenv("CLAUDE_API_KEY", ""))


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


class ClaudeCodeService:
    """Manages Claude subagent invocations"""

    def __init__(self):
        self.subagent_registry = self._load_registry()
        self.api_client = self._create_api_client()
        self._check_claude_auth()

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


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("SERVICE_PORT", "9000"))
    logger.info(f"Starting Claude API Service on port {port}")
    logger.info(f"Model: claude-sonnet-4-5-20250929")
    logger.info(f"MCP Server: {MCP_SERVER_URL}")
    logger.info(f"API Key configured: {bool(CLAUDE_API_KEY)}")

    uvicorn.run(app, host="0.0.0.0", port=port)

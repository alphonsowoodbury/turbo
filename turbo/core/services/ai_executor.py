"""AI Executor service for LLM-powered task execution."""

import json
import logging
from typing import Any
from uuid import UUID

import ollama
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.services.issue import IssueService
from turbo.core.services.project import ProjectService
from turbo.core.services.initiative import InitiativeService
from turbo.core.services.milestone import MilestoneService
from turbo.core.services.graph import GraphService
from turbo.core.schemas.issue import IssueCreate, IssueUpdate
from turbo.core.schemas.project import ProjectCreate, ProjectUpdate
from turbo.core.schemas.graph import GraphNodeCreate
from turbo.utils.config import get_settings

logger = logging.getLogger(__name__)


class AIExecutorService:
    """
    Service for executing user requests via LLM with tool calling.

    This service provides stateless, single-shot execution of tasks
    using an LLM that can call Turbo MCP tools.
    """

    def __init__(
        self,
        session: AsyncSession,
        issue_service: IssueService,
        project_service: ProjectService,
        initiative_service: InitiativeService,
        milestone_service: MilestoneService,
        graph_service: GraphService | None = None,
    ) -> None:
        self._session = session
        self._issue_service = issue_service
        self._project_service = project_service
        self._initiative_service = initiative_service
        self._milestone_service = milestone_service
        self._graph_service = graph_service or GraphService()
        self._settings = get_settings()

        # Ollama client
        self._client = ollama.Client(
            host=self._settings.llm.base_url
        )

        # Default model (can be overridden per request)
        self._default_model = self._settings.llm.default_model

    def list_available_models(self) -> list[dict[str, Any]]:
        """List all available models in Ollama."""
        try:
            response = self._client.list()
            return response.get("models", [])
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    def _get_tools(self) -> list[dict[str, Any]]:
        """Define available tools for the LLM."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_projects",
                    "description": "List all projects in the system",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of projects to return"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["active", "on_hold", "completed", "archived"],
                                "description": "Filter by project status"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_issue",
                    "description": "Create a new issue in a project",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Issue title"
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of the issue"
                            },
                            "project_id": {
                                "type": "string",
                                "description": "UUID of the project (required)"
                            },
                            "type": {
                                "type": "string",
                                "enum": ["bug", "feature", "task", "enhancement", "documentation", "discovery"],
                                "description": "Type of issue"
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high", "critical"],
                                "description": "Priority level"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["open", "in_progress", "review", "testing", "closed"],
                                "description": "Current status"
                            }
                        },
                        "required": ["title", "description", "project_id", "type", "priority"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_issues",
                    "description": "List issues with optional filters",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "Filter by project UUID"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["open", "in_progress", "review", "testing", "closed"],
                                "description": "Filter by status"
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high", "critical"],
                                "description": "Filter by priority"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number to return"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_issue",
                    "description": "Update an existing issue",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "issue_id": {
                                "type": "string",
                                "description": "UUID of the issue to update"
                            },
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "status": {
                                "type": "string",
                                "enum": ["open", "in_progress", "review", "testing", "closed"]
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high", "critical"]
                            }
                        },
                        "required": ["issue_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "semantic_search",
                    "description": "Search for related issues, projects, or documents using semantic similarity (meaning-based, not keyword matching)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language query describing what to search for"
                            },
                            "entity_type": {
                                "type": "string",
                                "enum": ["issue", "project", "document", "all"],
                                "description": "Type of entities to search (default: all)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 5)"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_related_issues",
                    "description": "Find issues related to a given issue through the knowledge graph (similar topics, dependencies, etc.)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "issue_id": {
                                "type": "string",
                                "description": "UUID of the issue to find relations for"
                            },
                            "relationship_type": {
                                "type": "string",
                                "enum": ["similar", "blocking", "blocked_by", "related_to", "all"],
                                "description": "Type of relationship to find (default: all)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 10)"
                            }
                        },
                        "required": ["issue_id"]
                    }
                }
            }
        ]

    async def _execute_tool(
        self, tool_name: str, arguments: dict[str, Any], context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute a tool call and return the result."""
        try:
            if tool_name == "list_projects":
                projects = await self._project_service.get_all_projects(
                    limit=arguments.get("limit")
                )
                return {
                    "success": True,
                    "data": [p.model_dump(mode="json") for p in projects]
                }

            elif tool_name == "create_issue":
                # Get AI model from context for creator tracking
                ai_model = context.get("_ai_model", "unknown") if context else "unknown"

                issue_data = IssueCreate(
                    title=arguments["title"],
                    description=arguments["description"],
                    project_id=UUID(arguments["project_id"]),
                    type=arguments["type"],
                    priority=arguments["priority"],
                    status=arguments.get("status", "open"),
                    created_by=f"AI: {ai_model}"
                )
                issue = await self._issue_service.create_issue(issue_data)
                return {
                    "success": True,
                    "data": issue.model_dump(mode="json"),
                    "message": f"Created issue: {issue.title}"
                }

            elif tool_name == "list_issues":
                if "project_id" in arguments:
                    issues = await self._issue_service.get_issues_by_project(
                        UUID(arguments["project_id"])
                    )
                elif "status" in arguments:
                    issues = await self._issue_service.get_issues_by_status(
                        arguments["status"]
                    )
                else:
                    issues = await self._issue_service.get_all_issues(
                        limit=arguments.get("limit")
                    )
                return {
                    "success": True,
                    "data": [i.model_dump(mode="json") for i in issues]
                }

            elif tool_name == "update_issue":
                issue_id = UUID(arguments.pop("issue_id"))
                update_data = IssueUpdate(**{k: v for k, v in arguments.items() if v is not None})
                issue = await self._issue_service.update_issue(issue_id, update_data)
                return {
                    "success": True,
                    "data": issue.model_dump(mode="json"),
                    "message": f"Updated issue: {issue.title}"
                }

            elif tool_name == "semantic_search":
                query = arguments["query"]
                entity_type = arguments.get("entity_type", "all")
                limit = arguments.get("limit", 5)

                # Perform semantic search using graph
                results = await self._graph_service.semantic_search(
                    query=query,
                    entity_type=entity_type if entity_type != "all" else None,
                    limit=limit
                )

                return {
                    "success": True,
                    "data": results,
                    "message": f"Found {len(results)} semantically similar results"
                }

            elif tool_name == "find_related_issues":
                issue_id = UUID(arguments["issue_id"])
                relationship_type = arguments.get("relationship_type", "all")
                limit = arguments.get("limit", 10)

                # Get issue from database first
                issue = await self._issue_service.get_issue_by_id(issue_id)
                if not issue:
                    return {
                        "success": False,
                        "error": f"Issue {issue_id} not found"
                    }

                # Find related entities in graph
                related = await self._graph_service.find_related(
                    entity_id=issue_id,
                    entity_type="issue",
                    relationship_type=relationship_type if relationship_type != "all" else None,
                    limit=limit
                )

                return {
                    "success": True,
                    "data": related,
                    "message": f"Found {len(related)} related issues"
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }

        except Exception as e:
            logger.error(f"Tool execution error: {tool_name} - {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def execute(
        self,
        request: str,
        context: dict[str, Any] | None = None,
        model: str | None = None
    ) -> dict[str, Any]:
        """
        Execute a user request using the LLM.

        Args:
            request: Natural language request from the user
            context: Optional context (e.g., current project_id, issue_id)
            model: Optional model override (e.g., "llama3.1:8b", "qwen2.5:14b")

        Returns:
            Dictionary with execution result
        """
        try:
            # Use specified model or default
            selected_model = model or self._default_model

            # Add model info to context for creator tracking
            if context is None:
                context = {}
            context["_ai_model"] = selected_model
            # Build system prompt
            system_prompt = (
                "You are an AI assistant for the Turbo project management system. "
                "Execute user requests by calling the appropriate tools. "
                "Be concise and efficient. Only call the tools needed to fulfill the request. "
                "Return results in a clear, structured format."
            )

            if context:
                system_prompt += f"\n\nContext: {json.dumps(context)}"

            # Initial LLM call with tools
            response = self._client.chat(
                model=selected_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request}
                ],
                tools=self._get_tools(),
            )

            # Check if LLM wants to call tools
            if not response.get("message", {}).get("tool_calls"):
                # Direct response, no tools needed
                return {
                    "success": True,
                    "response": response["message"]["content"],
                    "tool_calls": []
                }

            # Execute tool calls
            tool_results = []
            for tool_call in response["message"]["tool_calls"]:
                function_name = tool_call["function"]["name"]
                arguments = tool_call["function"]["arguments"]

                logger.info(f"Executing tool: {function_name} with args: {arguments}")

                result = await self._execute_tool(function_name, arguments, context)
                tool_results.append({
                    "tool": function_name,
                    "arguments": arguments,
                    "result": result
                })

            # Get final response from LLM with tool results
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request},
                response["message"],
            ]

            # Add tool results
            for tool_call, tool_result in zip(response["message"]["tool_calls"], tool_results):
                messages.append({
                    "role": "tool",
                    "content": json.dumps(tool_result["result"]),
                })

            # Final LLM response
            final_response = self._client.chat(
                model=selected_model,
                messages=messages
            )

            return {
                "success": True,
                "response": final_response["message"]["content"],
                "tool_calls": tool_results
            }

        except Exception as e:
            logger.error(f"AI execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Failed to execute request: {str(e)}"
            }

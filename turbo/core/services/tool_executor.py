"""Tool executor for staff member AI tool calls."""

import logging
from typing import Any
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes MCP tools by calling Turbo API endpoints."""

    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url

    async def execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Tool execution result
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if tool_name == "list_projects":
                    params = {}
                    if "status" in tool_input:
                        params["status"] = tool_input["status"]
                    if "priority" in tool_input:
                        params["priority"] = tool_input["priority"]
                    if "limit" in tool_input:
                        params["limit"] = tool_input["limit"]

                    response = await client.get(f"{self.api_base_url}/projects/", params=params)
                    response.raise_for_status()
                    return {"projects": response.json()}

                elif tool_name == "get_project":
                    project_id = tool_input["project_id"]
                    response = await client.get(f"{self.api_base_url}/projects/{project_id}")
                    response.raise_for_status()
                    return {"project": response.json()}

                elif tool_name == "get_project_issues":
                    project_id = tool_input["project_id"]
                    response = await client.get(f"{self.api_base_url}/projects/{project_id}/issues")
                    response.raise_for_status()
                    return {"issues": response.json()}

                elif tool_name == "list_issues":
                    params = {}
                    if "project_id" in tool_input:
                        params["project_id"] = tool_input["project_id"]
                    if "status" in tool_input:
                        params["status"] = tool_input["status"]
                    if "priority" in tool_input:
                        params["priority"] = tool_input["priority"]
                    if "assignee" in tool_input:
                        params["assignee"] = tool_input["assignee"]
                    if "limit" in tool_input:
                        params["limit"] = tool_input["limit"]

                    response = await client.get(f"{self.api_base_url}/issues/", params=params)
                    response.raise_for_status()
                    return {"issues": response.json()}

                elif tool_name == "get_issue":
                    issue_id = tool_input["issue_id"]
                    response = await client.get(f"{self.api_base_url}/issues/{issue_id}")
                    response.raise_for_status()
                    return {"issue": response.json()}

                elif tool_name == "create_issue":
                    response = await client.post(
                        f"{self.api_base_url}/issues/",
                        json=tool_input
                    )
                    response.raise_for_status()
                    return {"issue": response.json(), "message": "Issue created successfully"}

                elif tool_name == "update_issue":
                    issue_id = tool_input.pop("issue_id")
                    response = await client.put(
                        f"{self.api_base_url}/issues/{issue_id}",
                        json=tool_input
                    )
                    response.raise_for_status()
                    return {"issue": response.json(), "message": "Issue updated successfully"}

                elif tool_name == "list_documents":
                    params = {}
                    if "project_id" in tool_input:
                        params["project_id"] = tool_input["project_id"]
                    if "type" in tool_input:
                        params["type"] = tool_input["type"]
                    if "limit" in tool_input:
                        params["limit"] = tool_input["limit"]

                    response = await client.get(f"{self.api_base_url}/documents/", params=params)
                    response.raise_for_status()
                    return {"documents": response.json()}

                elif tool_name == "get_document":
                    document_id = tool_input["document_id"]
                    response = await client.get(f"{self.api_base_url}/documents/{document_id}")
                    response.raise_for_status()
                    return {"document": response.json()}

                elif tool_name == "search_documents":
                    params = {"query": tool_input["query"]}
                    response = await client.get(f"{self.api_base_url}/documents/search", params=params)
                    response.raise_for_status()
                    return {"documents": response.json()}

                elif tool_name == "semantic_search":
                    payload = {"query": tool_input["query"]}
                    if "entity_types" in tool_input:
                        payload["entity_types"] = tool_input["entity_types"]
                    if "limit" in tool_input:
                        payload["limit"] = tool_input["limit"]
                    if "min_relevance" in tool_input:
                        payload["min_relevance"] = tool_input["min_relevance"]

                    response = await client.post(
                        f"{self.api_base_url}/graph/search",
                        json=payload
                    )
                    response.raise_for_status()
                    return {"results": response.json()}

                # Career management tools
                elif tool_name == "list_job_applications":
                    params = {}
                    if "status" in tool_input:
                        params["status"] = tool_input["status"]
                    if "company_name" in tool_input:
                        params["company_name"] = tool_input["company_name"]
                    if "limit" in tool_input:
                        params["limit"] = tool_input["limit"]

                    response = await client.get(f"{self.api_base_url}/job-applications/", params=params)
                    response.raise_for_status()
                    return {"applications": response.json()}

                elif tool_name == "get_job_application":
                    application_id = tool_input["application_id"]
                    response = await client.get(f"{self.api_base_url}/job-applications/{application_id}")
                    response.raise_for_status()
                    return {"application": response.json()}

                elif tool_name == "create_job_application":
                    response = await client.post(
                        f"{self.api_base_url}/job-applications/",
                        json=tool_input
                    )
                    response.raise_for_status()
                    return {"application": response.json(), "message": "Job application created successfully"}

                elif tool_name == "update_job_application":
                    application_id = tool_input.pop("application_id")
                    response = await client.put(
                        f"{self.api_base_url}/job-applications/{application_id}",
                        json=tool_input
                    )
                    response.raise_for_status()
                    return {"application": response.json(), "message": "Job application updated successfully"}

                elif tool_name == "list_resumes":
                    params = {}
                    if "limit" in tool_input:
                        params["limit"] = tool_input["limit"]

                    response = await client.get(f"{self.api_base_url}/resumes/", params=params)
                    response.raise_for_status()
                    return {"resumes": response.json()}

                elif tool_name == "get_resume":
                    resume_id = tool_input["resume_id"]
                    response = await client.get(f"{self.api_base_url}/resumes/{resume_id}")
                    response.raise_for_status()
                    return {"resume": response.json()}

                elif tool_name == "list_companies":
                    params = {}
                    if "target_status" in tool_input:
                        params["target_status"] = tool_input["target_status"]
                    if "industry" in tool_input:
                        params["industry"] = tool_input["industry"]
                    if "limit" in tool_input:
                        params["limit"] = tool_input["limit"]

                    response = await client.get(f"{self.api_base_url}/companies/", params=params)
                    response.raise_for_status()
                    return {"companies": response.json()}

                elif tool_name == "get_company":
                    company_id = tool_input["company_id"]
                    response = await client.get(f"{self.api_base_url}/companies/{company_id}")
                    response.raise_for_status()
                    return {"company": response.json()}

                elif tool_name == "create_company":
                    response = await client.post(
                        f"{self.api_base_url}/companies/",
                        json=tool_input
                    )
                    response.raise_for_status()
                    return {"company": response.json(), "message": "Company created successfully"}

                elif tool_name == "list_network_contacts":
                    params = {}
                    if "current_company" in tool_input:
                        params["current_company"] = tool_input["current_company"]
                    if "contact_type" in tool_input:
                        params["contact_type"] = tool_input["contact_type"]
                    if "is_active" in tool_input:
                        params["is_active"] = tool_input["is_active"]
                    if "limit" in tool_input:
                        params["limit"] = tool_input["limit"]

                    response = await client.get(f"{self.api_base_url}/network-contacts/", params=params)
                    response.raise_for_status()
                    return {"contacts": response.json()}

                elif tool_name == "get_network_contact":
                    contact_id = tool_input["contact_id"]
                    response = await client.get(f"{self.api_base_url}/network-contacts/{contact_id}")
                    response.raise_for_status()
                    return {"contact": response.json()}

                elif tool_name == "create_network_contact":
                    response = await client.post(
                        f"{self.api_base_url}/network-contacts/",
                        json=tool_input
                    )
                    response.raise_for_status()
                    return {"contact": response.json(), "message": "Network contact created successfully"}

                elif tool_name == "list_skills":
                    params = {}
                    if "category" in tool_input:
                        params["category"] = tool_input["category"]
                    if "proficiency_level" in tool_input:
                        params["proficiency_level"] = tool_input["proficiency_level"]
                    if "limit" in tool_input:
                        params["limit"] = tool_input["limit"]

                    response = await client.get(f"{self.api_base_url}/skills/", params=params)
                    response.raise_for_status()
                    return {"skills": response.json()}

                # Work experience tools
                elif tool_name == "list_work_experiences":
                    params = {}
                    if "company_id" in tool_input:
                        params["company_id"] = tool_input["company_id"]
                    if "is_current" in tool_input:
                        params["is_current"] = tool_input["is_current"]
                    if "employment_type" in tool_input:
                        params["employment_type"] = tool_input["employment_type"]
                    if "limit" in tool_input:
                        params["limit"] = tool_input["limit"]

                    response = await client.get(f"{self.api_base_url}/work-experiences/", params=params)
                    response.raise_for_status()
                    return {"work_experiences": response.json()}

                elif tool_name == "get_work_experience":
                    experience_id = tool_input["experience_id"]
                    response = await client.get(f"{self.api_base_url}/work-experiences/{experience_id}")
                    response.raise_for_status()
                    return {"work_experience": response.json()}

                elif tool_name == "create_work_experience":
                    response = await client.post(
                        f"{self.api_base_url}/work-experiences/",
                        json=tool_input
                    )
                    response.raise_for_status()
                    return {"work_experience": response.json(), "message": "Work experience created successfully"}

                elif tool_name == "list_achievements":
                    params = {}
                    if "experience_id" in tool_input:
                        params["experience_id"] = tool_input["experience_id"]
                    if "metric_type" in tool_input:
                        params["metric_type"] = tool_input["metric_type"]
                    if "dimensions" in tool_input:
                        params["dimensions"] = tool_input["dimensions"]
                    if "leadership_principles" in tool_input:
                        params["leadership_principles"] = tool_input["leadership_principles"]
                    if "skills_used" in tool_input:
                        params["skills_used"] = tool_input["skills_used"]
                    if "limit" in tool_input:
                        params["limit"] = tool_input["limit"]

                    response = await client.get(f"{self.api_base_url}/work-experiences/achievements/", params=params)
                    response.raise_for_status()
                    return {"achievements": response.json()}

                elif tool_name == "get_achievement":
                    achievement_id = tool_input["achievement_id"]
                    response = await client.get(f"{self.api_base_url}/work-experiences/achievements/{achievement_id}")
                    response.raise_for_status()
                    return {"achievement": response.json()}

                elif tool_name == "create_achievement":
                    response = await client.post(
                        f"{self.api_base_url}/work-experiences/achievements/",
                        json=tool_input
                    )
                    response.raise_for_status()
                    return {"achievement": response.json(), "message": "Achievement created successfully"}

                elif tool_name == "search_achievements":
                    params = {"q": tool_input["query"]}
                    if "limit" in tool_input:
                        params["limit"] = tool_input["limit"]

                    response = await client.get(f"{self.api_base_url}/work-experiences/achievements/search/", params=params)
                    response.raise_for_status()
                    return {"achievements": response.json()}

                else:
                    return {"error": f"Unknown tool: {tool_name}"}

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error executing tool {tool_name}: {e}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return {"error": str(e)}

"""Tool registry for Claude API staff members."""

from typing import Any


def get_turbo_tools() -> list[dict[str, Any]]:
    """
    Get tool definitions in Claude API format.

    These tools are available to all staff members and can be filtered
    based on staff capabilities.
    """
    return [
        {
            "name": "list_projects",
            "description": "List all projects in the system with optional filtering by status or priority",
            "input_schema": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["active", "on_hold", "completed", "archived"],
                        "description": "Filter projects by status"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Filter projects by priority level"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of projects to return (default: 50)"
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_project",
            "description": "Get detailed information about a specific project including stats and metadata",
            "input_schema": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "UUID of the project to retrieve"
                    }
                },
                "required": ["project_id"]
            }
        },
        {
            "name": "list_issues",
            "description": "List issues with optional filtering by project, status, priority, or assignee",
            "input_schema": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Filter issues by project UUID"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["open", "in_progress", "review", "testing", "closed"],
                        "description": "Filter by issue status"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Filter by priority level"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Filter by assignee email"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of issues to return (default: 50)"
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_issue",
            "description": "Get detailed information about a specific issue",
            "input_schema": {
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "UUID of the issue to retrieve"
                    }
                },
                "required": ["issue_id"]
            }
        },
        {
            "name": "create_issue",
            "description": "Create a new issue in a project",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Issue title (clear and concise)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the issue with context and requirements"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "UUID of the project this issue belongs to"
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
                        "description": "Initial status (default: open)"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Email of person to assign this issue to (optional)"
                    }
                },
                "required": ["title", "description", "project_id", "type", "priority"]
            }
        },
        {
            "name": "update_issue",
            "description": "Update an existing issue's properties",
            "input_schema": {
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "UUID of the issue to update"
                    },
                    "title": {
                        "type": "string",
                        "description": "New title"
                    },
                    "description": {
                        "type": "string",
                        "description": "New description"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["open", "in_progress", "review", "testing", "closed"],
                        "description": "New status"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "New priority level"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "New assignee email"
                    }
                },
                "required": ["issue_id"]
            }
        },
        {
            "name": "list_documents",
            "description": "List documents with optional filtering by type, format, or project",
            "input_schema": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Filter documents by project UUID"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["specification", "user_guide", "api_doc", "readme", "changelog", "requirements", "design", "other"],
                        "description": "Filter by document type"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of documents to return (default: 50)"
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_document",
            "description": "Get detailed information about a specific document including full content",
            "input_schema": {
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "UUID of the document to retrieve"
                    }
                },
                "required": ["document_id"]
            }
        },
        {
            "name": "search_documents",
            "description": "Search documents by title and content using keywords",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to match against document title and content"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "semantic_search",
            "description": "Perform semantic search across the knowledge graph to find related entities by meaning (not just keywords)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language description of what you're looking for"
                    },
                    "entity_types": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["issue", "project", "document", "milestone", "initiative"]
                        },
                        "description": "Types of entities to search (leave empty for all types)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)"
                    },
                    "min_relevance": {
                        "type": "number",
                        "description": "Minimum relevance score 0.0-1.0 (default: 0.7)"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "get_work_queue",
            "description": "Get all issues in the work queue, sorted by priority rank. Lower rank number = higher priority (rank 1 is most important). Only returns issues that have been explicitly ranked.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["open", "in_progress", "review", "testing", "closed"],
                        "description": "Filter by status"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Filter by priority level"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of issues to return (default: 100)"
                    },
                    "include_unranked": {
                        "type": "boolean",
                        "description": "Include issues without work_rank (default: false)"
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_next_issue",
            "description": "Get THE next issue to work on. Returns the highest-ranked issue (work_rank=1) that is open or in_progress. Use this when asked 'what should I work on next' or 'work the next issue'. Returns null if no ranked issues exist.",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "set_issue_rank",
            "description": "Set the work queue rank for a specific issue. Rank 1 is highest priority. This manually positions an issue in the work queue.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "UUID of the issue to rank"
                    },
                    "work_rank": {
                        "type": "integer",
                        "description": "New rank position (1=highest priority)"
                    }
                },
                "required": ["issue_id", "work_rank"]
            }
        },
        {
            "name": "remove_issue_rank",
            "description": "Remove an issue from the work queue by clearing its rank. The issue will no longer appear in the prioritized work queue.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "UUID of the issue to remove from queue"
                    }
                },
                "required": ["issue_id"]
            }
        },
        {
            "name": "auto_rank_issues",
            "description": "Automatically rank all open/in_progress issues using intelligent scoring based on priority, age, blockers, and dependencies. This will recalculate and assign ranks to all eligible issues.",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "list_job_applications",
            "description": "List job applications with optional filtering by status or company",
            "input_schema": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["saved", "applied", "screening", "interviewing", "offered", "accepted", "rejected", "withdrawn"],
                        "description": "Filter applications by status"
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Filter by company name (partial match)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of applications to return (default: 50)"
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_job_application",
            "description": "Get detailed information about a specific job application including all tracking data",
            "input_schema": {
                "type": "object",
                "properties": {
                    "application_id": {
                        "type": "string",
                        "description": "UUID of the job application to retrieve"
                    }
                },
                "required": ["application_id"]
            }
        },
        {
            "name": "create_job_application",
            "description": "Create a new job application record to track your job search",
            "input_schema": {
                "type": "object",
                "properties": {
                    "position_title": {
                        "type": "string",
                        "description": "Job title/position name"
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Company name"
                    },
                    "job_url": {
                        "type": "string",
                        "description": "URL to job posting"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["saved", "applied", "screening", "interviewing", "offered", "accepted", "rejected", "withdrawn"],
                        "description": "Current application status (default: saved)"
                    },
                    "salary_range_min": {
                        "type": "integer",
                        "description": "Minimum salary in dollars"
                    },
                    "salary_range_max": {
                        "type": "integer",
                        "description": "Maximum salary in dollars"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Notes about this application"
                    }
                },
                "required": ["position_title", "company_name"]
            }
        },
        {
            "name": "update_job_application",
            "description": "Update an existing job application with new information or status",
            "input_schema": {
                "type": "object",
                "properties": {
                    "application_id": {
                        "type": "string",
                        "description": "UUID of the application to update"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["saved", "applied", "screening", "interviewing", "offered", "accepted", "rejected", "withdrawn"],
                        "description": "New status"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Updated notes"
                    }
                },
                "required": ["application_id"]
            }
        },
        {
            "name": "list_resumes",
            "description": "List all resumes with their metadata",
            "input_schema": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of resumes to return (default: 50)"
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_resume",
            "description": "Get detailed information about a specific resume including all sections and parsed data",
            "input_schema": {
                "type": "object",
                "properties": {
                    "resume_id": {
                        "type": "string",
                        "description": "UUID of the resume to retrieve"
                    }
                },
                "required": ["resume_id"]
            }
        },
        {
            "name": "list_companies",
            "description": "List companies with optional filtering by target status or industry",
            "input_schema": {
                "type": "object",
                "properties": {
                    "target_status": {
                        "type": "string",
                        "enum": ["researching", "targeting", "applied", "interviewing", "not_interested"],
                        "description": "Filter by target status"
                    },
                    "industry": {
                        "type": "string",
                        "description": "Filter by industry"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of companies to return (default: 50)"
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_company",
            "description": "Get detailed information about a specific company including notes and application history",
            "input_schema": {
                "type": "object",
                "properties": {
                    "company_id": {
                        "type": "string",
                        "description": "UUID of the company to retrieve"
                    }
                },
                "required": ["company_id"]
            }
        },
        {
            "name": "create_company",
            "description": "Create a new company record to track for job search",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Company name"
                    },
                    "industry": {
                        "type": "string",
                        "description": "Industry/sector"
                    },
                    "size": {
                        "type": "string",
                        "description": "Company size (e.g., '100-500', '1000+')"
                    },
                    "website": {
                        "type": "string",
                        "description": "Company website URL"
                    },
                    "target_status": {
                        "type": "string",
                        "enum": ["researching", "targeting", "applied", "interviewing", "not_interested"],
                        "description": "Current target status (default: researching)"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Notes about this company"
                    }
                },
                "required": ["name"]
            }
        },
        {
            "name": "list_network_contacts",
            "description": "List network contacts with optional filtering by company or contact type",
            "input_schema": {
                "type": "object",
                "properties": {
                    "current_company": {
                        "type": "string",
                        "description": "Filter by current company (partial match)"
                    },
                    "contact_type": {
                        "type": "string",
                        "enum": ["recruiter", "hiring_manager", "employee", "alumni", "referral", "other"],
                        "description": "Filter by contact type"
                    },
                    "is_active": {
                        "type": "boolean",
                        "description": "Filter by active status (default: true)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of contacts to return (default: 50)"
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_network_contact",
            "description": "Get detailed information about a specific network contact",
            "input_schema": {
                "type": "object",
                "properties": {
                    "contact_id": {
                        "type": "string",
                        "description": "UUID of the contact to retrieve"
                    }
                },
                "required": ["contact_id"]
            }
        },
        {
            "name": "create_network_contact",
            "description": "Create a new network contact to track for job search and networking",
            "input_schema": {
                "type": "object",
                "properties": {
                    "first_name": {
                        "type": "string",
                        "description": "Contact's first name"
                    },
                    "last_name": {
                        "type": "string",
                        "description": "Contact's last name"
                    },
                    "email": {
                        "type": "string",
                        "description": "Contact's email address"
                    },
                    "current_company": {
                        "type": "string",
                        "description": "Current company where contact works"
                    },
                    "current_title": {
                        "type": "string",
                        "description": "Current job title"
                    },
                    "contact_type": {
                        "type": "string",
                        "enum": ["recruiter", "hiring_manager", "employee", "alumni", "referral", "other"],
                        "description": "Type of contact"
                    },
                    "linkedin_url": {
                        "type": "string",
                        "description": "LinkedIn profile URL"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Notes about this contact"
                    }
                },
                "required": ["first_name", "last_name"]
            }
        },
        {
            "name": "list_skills",
            "description": "List skills with optional filtering by category or proficiency level",
            "input_schema": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["technical", "soft_skills", "tools", "languages", "certifications", "other"],
                        "description": "Filter by skill category"
                    },
                    "proficiency_level": {
                        "type": "string",
                        "enum": ["beginner", "intermediate", "advanced", "expert"],
                        "description": "Filter by proficiency level"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of skills to return (default: 100)"
                    }
                },
                "required": []
            }
        },
        {
            "name": "list_work_experiences",
            "description": "List work experiences (employment history) with optional filtering by company, current status, or employment type",
            "input_schema": {
                "type": "object",
                "properties": {
                    "company_id": {
                        "type": "string",
                        "description": "Filter by company UUID"
                    },
                    "is_current": {
                        "type": "boolean",
                        "description": "Filter by current employment status"
                    },
                    "employment_type": {
                        "type": "string",
                        "enum": ["full_time", "part_time", "contract", "freelance"],
                        "description": "Filter by employment type"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 100)"
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_work_experience",
            "description": "Get detailed information about a specific work experience including all achievements",
            "input_schema": {
                "type": "object",
                "properties": {
                    "experience_id": {
                        "type": "string",
                        "description": "UUID of the work experience"
                    }
                },
                "required": ["experience_id"]
            }
        },
        {
            "name": "create_work_experience",
            "description": "Create a new work experience entry. Use this to document employment history.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "company_id": {
                        "type": "string",
                        "description": "Company UUID (optional)"
                    },
                    "role_title": {
                        "type": "string",
                        "description": "Job title/role"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD format)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD format, null if current)"
                    },
                    "is_current": {
                        "type": "boolean",
                        "description": "Whether this is current employment"
                    },
                    "location": {
                        "type": "string",
                        "description": "Work location"
                    },
                    "employment_type": {
                        "type": "string",
                        "enum": ["full_time", "part_time", "contract", "freelance"],
                        "description": "Employment type"
                    },
                    "team_context": {
                        "type": "object",
                        "description": "Team structure context (team_size, reporting_to, etc.)"
                    },
                    "technologies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Technologies/tools used"
                    }
                },
                "required": ["role_title", "start_date"]
            }
        },
        {
            "name": "list_achievements",
            "description": "List achievement facts with filtering by work experience, metric type, dimensions (leadership, technical, etc.), leadership principles, or skills used. These are granular, factual accomplishments that prevent AI hallucination.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "experience_id": {
                        "type": "string",
                        "description": "Filter by work experience UUID"
                    },
                    "metric_type": {
                        "type": "string",
                        "description": "Filter by metric type (cost_savings, time_reduction, scale, etc.)"
                    },
                    "dimensions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by dimensions (must contain all) - e.g., ['leadership', 'technical', 'cost_optimization']"
                    },
                    "leadership_principles": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by Amazon Leadership Principles - e.g., ['frugality', 'bias_for_action']"
                    },
                    "skills_used": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by skills used"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 100)"
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_achievement",
            "description": "Get detailed information about a specific achievement fact",
            "input_schema": {
                "type": "object",
                "properties": {
                    "achievement_id": {
                        "type": "string",
                        "description": "UUID of the achievement fact"
                    }
                },
                "required": ["achievement_id"]
            }
        },
        {
            "name": "create_achievement",
            "description": "Create a new achievement fact for a work experience. Use this to document specific, quantifiable accomplishments with metrics. These factual statements prevent hallucination and enable multi-dimensional extraction for leadership stories, technical examples, etc.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "experience_id": {
                        "type": "string",
                        "description": "Work experience UUID this achievement belongs to"
                    },
                    "fact_text": {
                        "type": "string",
                        "description": "Core factual statement - atomic, verifiable, quantifiable"
                    },
                    "metric_type": {
                        "type": "string",
                        "description": "Type of metric (cost_savings, time_reduction, scale, performance_improvement, etc.)"
                    },
                    "metric_value": {
                        "type": "number",
                        "description": "Numerical value of the metric"
                    },
                    "metric_unit": {
                        "type": "string",
                        "description": "Unit of measurement (percentage, dollars, days, gigabytes_daily, etc.)"
                    },
                    "dimensions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Dimensional tags (leadership, technical, customer_obsession, innovation, etc.)"
                    },
                    "leadership_principles": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Amazon Leadership Principles demonstrated (frugality, bias_for_action, deliver_results, etc.)"
                    },
                    "skills_used": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Skills demonstrated in this achievement"
                    },
                    "context": {
                        "type": "string",
                        "description": "Situation/Task context for STAR format"
                    },
                    "impact": {
                        "type": "string",
                        "description": "Result/Impact for STAR format"
                    }
                },
                "required": ["experience_id", "fact_text"]
            }
        },
        {
            "name": "search_achievements",
            "description": "Search achievement facts by text query across fact_text, context, and impact fields",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query text"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 100)"
                    }
                },
                "required": ["query"]
            }
        }
    ]


def filter_tools_by_capabilities(tools: list[dict[str, Any]], capabilities: list[str]) -> list[dict[str, Any]]:
    """
    Filter tools based on staff member capabilities.

    Args:
        tools: Full list of available tools
        capabilities: List of capability strings from staff record

    Returns:
        Filtered list of tools this staff member can access
    """
    # Capability to tool mapping
    capability_tool_map = {
        "team_coordination": ["list_projects", "list_issues", "get_project", "get_issue", "create_issue", "get_work_queue", "get_next_issue"],
        "resource_allocation": ["list_projects", "list_issues", "create_issue", "update_issue", "get_work_queue", "set_issue_rank", "auto_rank_issues"],
        "priority_alignment": ["list_issues", "create_issue", "update_issue", "get_work_queue", "get_next_issue", "set_issue_rank", "auto_rank_issues"],
        "capacity_planning": ["list_projects", "list_issues", "create_issue", "update_issue", "get_work_queue", "get_next_issue", "set_issue_rank", "auto_rank_issues", "list_documents", "get_document", "search_documents"],
        "technical_prioritization": ["list_projects", "list_issues", "create_issue", "update_issue", "get_work_queue", "get_next_issue", "set_issue_rank", "list_documents", "get_document", "search_documents"],
        "staff_recruitment": [],  # No direct tools - conversational capability
        "cross_functional_analysis": ["semantic_search", "list_documents", "get_document", "search_documents", "get_work_queue"],
        "conflict_resolution": ["list_issues", "get_issue", "get_work_queue"],
        "strategic_planning": ["list_projects", "get_project", "create_issue", "list_documents", "get_work_queue", "get_next_issue", "auto_rank_issues"],
        # Domain expert capabilities (documents, technical work)
        "document_management": ["list_documents", "get_document", "search_documents"],
        "code_review": ["list_issues", "get_issue", "update_issue", "get_work_queue"],
        "architecture": ["list_documents", "search_documents", "semantic_search", "get_work_queue"],
        "testing": ["list_issues", "create_issue", "update_issue", "get_work_queue", "get_next_issue"],
        "design": ["list_documents", "search_documents", "get_work_queue"],
        # Engineering Manager specific capabilities
        "architecture_review": ["list_documents", "get_document", "search_documents", "semantic_search", "list_issues", "get_issue", "get_work_queue"],
        "code_quality_oversight": ["list_documents", "get_document", "search_documents", "list_issues", "get_issue", "update_issue"],
        "engineering_standards": ["list_documents", "get_document", "search_documents"],
        "performance_analysis": ["list_documents", "get_document", "search_documents", "list_issues", "get_issue"],
        "technical_mentorship": ["list_documents", "get_document", "search_documents", "list_issues", "get_issue"],
        # Career Coach capabilities
        "career_guidance": ["list_job_applications", "get_job_application", "create_job_application", "update_job_application", "list_resumes", "get_resume", "list_companies", "get_company", "create_company", "list_network_contacts", "get_network_contact", "create_network_contact", "list_skills", "list_work_experiences", "get_work_experience", "create_work_experience", "list_achievements", "get_achievement", "create_achievement", "search_achievements", "list_documents", "get_document", "search_documents"],
        "resume_review": ["list_resumes", "get_resume", "list_skills", "list_work_experiences", "get_work_experience", "list_achievements", "search_achievements", "list_documents", "get_document", "search_documents"],
        "interview_prep": ["list_job_applications", "get_job_application", "list_companies", "get_company", "list_network_contacts", "get_network_contact", "list_work_experiences", "get_work_experience", "list_achievements", "get_achievement", "search_achievements", "list_documents", "get_document", "search_documents"],
        "salary_negotiation": ["list_job_applications", "get_job_application", "update_job_application", "list_companies", "get_company", "list_work_experiences", "get_work_experience", "list_achievements", "search_achievements", "list_documents", "get_document", "search_documents"],
        "job_search_strategy": ["list_job_applications", "get_job_application", "create_job_application", "update_job_application", "list_companies", "get_company", "create_company", "list_network_contacts", "get_network_contact", "create_network_contact", "list_work_experiences", "get_work_experience", "create_work_experience", "list_achievements", "create_achievement", "list_documents", "get_document", "search_documents"],
        "networking_advice": ["list_network_contacts", "get_network_contact", "create_network_contact", "list_companies", "get_company", "list_work_experiences", "get_work_experience", "list_achievements", "search_achievements", "list_documents", "get_document", "search_documents"],
    }

    # Collect all allowed tool names
    allowed_tool_names = set()
    for capability in capabilities:
        if capability in capability_tool_map:
            allowed_tool_names.update(capability_tool_map[capability])

    # If no specific capabilities mapped to tools, give access to read-only tools including work queue
    if not allowed_tool_names:
        allowed_tool_names = {"list_projects", "list_issues", "get_project", "get_issue", "get_work_queue", "get_next_issue"}

    # Filter tools
    return [tool for tool in tools if tool["name"] in allowed_tool_names]

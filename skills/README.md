# Turbo Skills

Skills are reusable capabilities that can be attached to subagents to enhance their functionality.

## Status

Skills are planned for future implementation. Currently, all subagent capabilities are defined directly in their system prompts and tool access lists in `../subagents/registry.json`.

## Future Implementation

Skills will allow:
- Reusable code snippets that multiple agents can share
- Common patterns for MCP tool usage
- Specialized analysis algorithms
- Custom validation logic

## Placeholder

This directory is currently a placeholder to maintain Docker build compatibility.

## Example Skill Structure

```json
{
  "name": "priority-analyzer",
  "description": "Analyzes issue descriptions to suggest priority levels",
  "code": "...",
  "dependencies": ["mcp__turbo__get_issue"],
  "used_by": ["issue-triager", "project-manager"]
}
```

---

For now, all agent logic is contained in:
- `../subagents/registry.json` - Agent definitions with system prompts and tool access
- `../scripts/claude_headless_service.py` - Service that invokes agents

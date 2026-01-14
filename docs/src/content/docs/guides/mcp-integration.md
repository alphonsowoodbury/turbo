---
title: MCP Integration
description: Connect Turbo-Plan to Claude Code via MCP
---

The Model Context Protocol (MCP) integration allows you to manage Turbo-Plan directly from Claude Code using natural language.

## Setup

### 1. Configure MCP Server

Add Turbo-Plan to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "turbo": {
      "command": "python",
      "args": ["-m", "turbo_mcp"],
      "cwd": "/path/to/turbo-plan/turbo",
      "env": {
        "TURBO_API_URL": "https://turbo-plan.fly.dev"
      }
    }
  }
}
```

### 2. Verify Connection

In Claude Code, ask:

```
List all projects in Turbo
```

You should see your Turbo-Plan projects listed.

## Available Tools

### Project Management

| Tool | Description |
|------|-------------|
| `list_projects` | List all projects |
| `get_project` | Get project details |
| `create_project` | Create a new project |
| `update_project` | Update project |

### Issue Management

| Tool | Description |
|------|-------------|
| `list_issues` | List issues (with filters) |
| `get_issue` | Get issue details |
| `create_issue` | Create a new issue |
| `update_issue` | Update issue status/details |
| `add_comment` | Add comment to issue |

### Work Tracking

| Tool | Description |
|------|-------------|
| `log_work` | Log work progress |
| `get_work_queue` | Get prioritized work |

## Example Usage

### Create an Issue

```
Create an issue in the frontend project:
"Add dark mode toggle to settings page"
Priority: medium
```

### Update Issue Status

```
Mark issue #42 as in progress
```

### Log Work

```
Log 2 hours of work on issue #42:
"Implemented toggle component and state management"
```

### Get Work Queue

```
What should I work on next?
```

## Best Practices

1. **Be specific** - Include project names and issue details
2. **Use natural language** - The AI understands context
3. **Reference by ID** - Use issue IDs for precise updates
4. **Log progress** - Keep work logs updated for visibility

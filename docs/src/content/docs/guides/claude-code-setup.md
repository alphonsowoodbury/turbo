---
title: Claude Code Setup
description: Configure Claude Code for optimal Turbo-Plan integration
---

This guide covers setting up Claude Code with Turbo-Plan for the best development experience.

## Prerequisites

- Claude Code CLI installed
- Access to Turbo-Plan (hosted or self-hosted)

## MCP Configuration

### Global Configuration

Add to `~/.claude/.mcp.json`:

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

### Project-Specific Configuration

Add to your project's `.claude/mcp.json` for project-specific settings.

## Custom Skills

Add Turbo skills to your Claude Code configuration:

### /turbo-status

Check current project status:

```markdown
# Turbo Status Skill

Check the current status of issues and projects.

## Usage
/turbo-status [project-name]
```

### /turbo-log

Log work progress:

```markdown
# Turbo Log Skill

Log work progress on an issue.

## Usage
/turbo-log <issue-id> <hours> <description>
```

### /turbo-issue

Create a new issue:

```markdown
# Turbo Issue Skill

Create a new issue in a project.

## Usage
/turbo-issue <project> <title>
```

## Workflow Integration

### Starting Work

1. Ask Claude Code: "What should I work on next?"
2. Claude fetches your work queue from Turbo
3. Pick an issue and start working
4. Claude automatically logs progress

### During Development

- Ask about issue context: "What are the requirements for issue #42?"
- Get suggestions: "How should I implement this feature?"
- Log blockers: "I'm blocked on issue #42 because..."

### Finishing Work

1. Mark issue as review: "Mark #42 as ready for review"
2. Create PR with context from the issue
3. Close issue when merged

## Tips

- **Use worktrees** - Claude Code can manage git worktrees per issue
- **Reference issues** - Use `#42` format for quick issue references
- **Log regularly** - Small, frequent logs are better than large summaries

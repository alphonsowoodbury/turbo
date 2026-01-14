---
title: Projects
description: Understanding projects in Turbo-Plan
---

Projects are the core organizational unit in Turbo-Plan. They represent a codebase, application, or distinct piece of work.

## Project Properties

| Property | Description |
|----------|-------------|
| **Name** | The project name |
| **Description** | Detailed description of the project |
| **Status** | Active, Paused, or Archived |
| **Repository** | Optional Git repository URL |
| **Initiative** | Parent initiative (optional) |

## Creating Projects

### Via UI

1. Press `Cmd+K` / `Ctrl+K` to open the command palette
2. Select "Create Project"
3. Fill in the project details
4. Click "Create"

### Via MCP

```
Create a new project called "my-api" for building a REST API
```

Claude Code will use the MCP tools to create the project.

## Project Hierarchy

```
Initiative
└── Project
    ├── Issues
    ├── Milestones
    ├── Documents
    └── Blueprints
```

## Best Practices

- **One project per codebase** - Keep projects aligned with repositories
- **Clear naming** - Use descriptive names that identify the project
- **Link to repository** - Connect projects to their Git repositories
- **Use initiatives** - Group related projects under initiatives

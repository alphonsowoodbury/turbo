---
title: Issues
description: Track work with issues in Turbo-Plan
---

Issues represent individual pieces of work - bugs to fix, features to build, or tasks to complete.

## Issue Properties

| Property | Description |
|----------|-------------|
| **Title** | Brief summary of the issue |
| **Description** | Detailed description (Markdown supported) |
| **Status** | Backlog, Todo, In Progress, Review, Done |
| **Priority** | Low, Medium, High, Urgent |
| **Project** | The parent project |
| **Milestone** | Optional milestone target |
| **Assignee** | Who's working on it |
| **Labels** | Custom tags for organization |

## Issue Workflow

```
Backlog → Todo → In Progress → Review → Done
```

### Status Meanings

- **Backlog**: Captured but not yet prioritized
- **Todo**: Ready to work on
- **In Progress**: Currently being worked on
- **Review**: Awaiting review or testing
- **Done**: Completed

## Creating Issues

### Via UI

1. Press `Cmd+I` / `Ctrl+I` to open the issue creator
2. Fill in title and description
3. Set priority and assign to project
4. Click "Create"

### Via MCP

```
Create an issue in my-api project: "Add user authentication endpoint"
```

## AI Analysis

When issues are created, AI agents automatically analyze them and add comments with:

- Suggested implementation approach
- Related files to modify
- Potential edge cases
- Estimated complexity

## Work Queue

The Work Queue shows prioritized issues across all projects based on:

- Priority level
- Due date proximity
- Dependencies
- Your assignment

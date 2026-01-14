---
title: Initiatives
description: Organize projects under strategic initiatives
---

Initiatives are high-level goals that group related projects together. They represent strategic objectives like "Launch Mobile App" or "Improve Performance."

## Initiative Properties

| Property | Description |
|----------|-------------|
| **Name** | The initiative name |
| **Description** | Strategic context and goals |
| **Status** | Planning, Active, Completed |
| **Target Date** | Optional deadline |
| **Projects** | Child projects |

## When to Use Initiatives

Use initiatives when you have:

- Multiple projects contributing to one goal
- A strategic objective spanning several codebases
- A product launch involving frontend, backend, and infrastructure
- A refactoring effort across services

## Example Structure

```
Initiative: "Launch Mobile App"
├── Project: mobile-app (React Native)
├── Project: api-v2 (Backend updates)
├── Project: push-notifications (New service)
└── Project: docs (Documentation updates)
```

## Creating Initiatives

### Via UI

1. Navigate to Initiatives in the sidebar
2. Click "New Initiative"
3. Add name, description, and target date
4. Link existing projects or create new ones

### Via MCP

```
Create an initiative called "Q1 Performance Sprint" for optimizing API response times
```

## Tracking Progress

Initiative progress is calculated from:

- Percentage of linked issues completed
- Project milestone completion
- Child project statuses

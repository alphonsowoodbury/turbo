---
title: API Overview
description: Turbo-Plan REST API reference
---

The Turbo-Plan API is a RESTful API that provides programmatic access to all features.

## Base URL

```
https://turbo-plan.fly.dev/api
```

## Authentication

All API requests require authentication via Bearer token:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://turbo-plan.fly.dev/api/projects
```

## Endpoints

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects` | List all projects |
| POST | `/projects` | Create project |
| GET | `/projects/{id}` | Get project |
| PUT | `/projects/{id}` | Update project |
| DELETE | `/projects/{id}` | Delete project |

### Issues

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/issues` | List issues |
| POST | `/issues` | Create issue |
| GET | `/issues/{id}` | Get issue |
| PUT | `/issues/{id}` | Update issue |
| DELETE | `/issues/{id}` | Delete issue |

### Comments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/comments/entity/{type}/{id}` | List comments |
| POST | `/comments` | Create comment |

### Work Logs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/work-logs` | List work logs |
| POST | `/work-logs` | Create work log |

## Response Format

All responses are JSON:

```json
{
  "id": "uuid",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  ...
}
```

## Error Handling

Errors return appropriate HTTP status codes:

| Code | Description |
|------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Server Error |

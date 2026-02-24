# Turbo-Plan Fly.io Deployment Plan

## Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Fly.io                               │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ turbo-api    │  │ turbo-db     │  │ turbo-web    │       │
│  │ FastAPI      │──│ Fly Postgres │  │ Next.js      │       │
│  │ + MCP Server │  │ (managed)    │  │ Frontend     │       │
│  │ Port 8080    │  │              │  │ Port 3000    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         ↑                                                   │
│         │ HTTPS + API Key Auth                              │
└─────────│───────────────────────────────────────────────────┘
          │
          │ MCP over HTTPS
          │
┌─────────│───────────────────────────────────────────────────┐
│  Local Development (any machine)                            │
│         ↓                                                   │
│  ┌──────────────┐     ┌──────────────┐                      │
│  │ Claude Code  │────→│ turbo MCP    │                      │
│  │ CLI          │     │ (remote)     │                      │
│  └──────────────┘     └──────────────┘                      │
│                                                             │
│  All projects get access to turbo tools:                    │
│  - Create issues, initiatives, decisions                    │
│  - Log work, track progress                                 │
│  - AI mentor conversations                                  │
│  - Document management                                      │
└─────────────────────────────────────────────────────────────┘
```

## Fly.io Apps Required

| App | Purpose | Resources | Est. Cost |
|-----|---------|-----------|-----------|
| `turbo-api` | FastAPI + MCP Server | 512MB, shared CPU | $5-7/mo |
| `turbo-db` | Fly Postgres | 1GB, single node | $7-10/mo |
| `turbo-web` | Next.js Frontend | 256MB, shared CPU | $3-5/mo |
| **Total** | | | **~$15-22/mo** |

## Phase 1: Database Migration

### 1.1 Create Fly Postgres

```bash
cd /Volumes/Meristem/turbo-plan
fly postgres create --name turbo-db --region ewr
```

### 1.2 Update fly.toml for Postgres

```toml
app = 'turbo-api'
primary_region = 'ewr'

[build]
  dockerfile = "Dockerfile.fly"

[env]
  GRAPH_ENABLED = "false"
  TURBO_ENVIRONMENT = "production"
  API_HOST = "0.0.0.0"
  API_PORT = "8080"
  # DATABASE_URL set via fly secrets

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = 'stop'
  auto_start_machines = true
  min_machines_running = 0
  processes = ['app']

[[vm]]
  memory = '512mb'
  cpu_kind = 'shared'
  cpus = 1
```

### 1.3 Attach Database & Set Secrets

```bash
fly postgres attach turbo-db --app turbo-api
fly secrets set ANTHROPIC_API_KEY="sk-ant-..." --app turbo-api
fly secrets set TURBO_API_KEY="your-secure-api-key" --app turbo-api
```

## Phase 2: API Authentication for Remote MCP

### 2.1 Add API Key Middleware

Create `turbo/api/middleware/auth.py`:

```python
from fastapi import Header, HTTPException, Depends
from starlette.middleware.base import BaseHTTPMiddleware
import os

TURBO_API_KEY = os.getenv("TURBO_API_KEY")

async def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key for remote MCP access."""
    if not TURBO_API_KEY:
        return  # No auth configured (local dev)
    if x_api_key != TURBO_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
```

### 2.2 Apply to MCP Endpoints

```python
# In turbo/mcp_server.py or routes
from turbo.api.middleware.auth import verify_api_key

@router.post("/mcp/tools/{tool_name}", dependencies=[Depends(verify_api_key)])
async def call_tool(tool_name: str, ...):
    ...
```

## Phase 3: Frontend Deployment

### 3.1 Create frontend/fly.toml

```toml
app = 'turbo-web'
primary_region = 'ewr'

[build]
  dockerfile = "Dockerfile"

[env]
  NEXT_PUBLIC_API_URL = "https://turbo-api.fly.dev"
  PORT = "3000"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = 'stop'
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  memory = '256mb'
  cpu_kind = 'shared'
  cpus = 1
```

### 3.2 Deploy Frontend

```bash
cd /Volumes/Meristem/turbo-plan/frontend
fly deploy
```

## Phase 4: Local Claude Code Integration

### 4.1 Global MCP Configuration

Add to `~/.claude/settings.json` (or `/Volumes/Claude/.claude/settings.json`):

```json
{
  "mcpServers": {
    "turbo": {
      "transport": "http",
      "url": "https://turbo-api.fly.dev/mcp",
      "headers": {
        "X-API-Key": "${TURBO_API_KEY}"
      }
    }
  }
}
```

### 4.2 Environment Variable

Add to shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export TURBO_API_KEY="your-secure-api-key"
```

## Phase 5: Slash Commands for Turbo

Create global slash commands in `~/.claude/commands/`:

### turbo-issue.md
```markdown
Create a new issue in Turbo-Plan:

Project: $ARGUMENTS (or ask if not provided)

1. Use turbo MCP to list projects if needed
2. Create issue with title and description
3. Return the issue key (e.g., TURBO-123)
```

### turbo-log.md
```markdown
Log work on the current task:

1. Identify current issue from context or ask
2. Create work log entry with description
3. Update issue status if needed
```

### turbo-status.md
```markdown
Show current turbo-plan status:

1. List in-progress issues assigned to me
2. Show upcoming due dates
3. Display work queue priority
```

## Deployment Commands

```bash
# Initial setup
cd /Volumes/Meristem/turbo-plan

# Create Postgres
fly postgres create --name turbo-db --region ewr

# Deploy API
fly deploy --app turbo-api

# Attach database
fly postgres attach turbo-db --app turbo-api

# Set secrets
fly secrets set ANTHROPIC_API_KEY="..." --app turbo-api
fly secrets set TURBO_API_KEY="..." --app turbo-api

# Deploy frontend
cd frontend
fly deploy --app turbo-web

# Verify
curl https://turbo-api.fly.dev/health
curl https://turbo-web.fly.dev/
```

## Migration from SQLite (if existing data)

```bash
# Export from SQLite
sqlite3 /data/turbo.db .dump > backup.sql

# Import to Postgres
fly postgres connect --app turbo-db
\i backup.sql
```

## Rollback Plan

If issues arise:
1. Keep SQLite fly.toml as `fly.toml.sqlite`
2. Can redeploy with `fly deploy -c fly.toml.sqlite`
3. Data persists in Fly volume

## Success Criteria

- [ ] API responds at https://turbo-api.fly.dev/health
- [ ] Frontend loads at https://turbo-web.fly.dev
- [ ] MCP tools accessible from local Claude Code
- [ ] Can create issue via `/turbo-issue` command
- [ ] Can log work via `/turbo-log` command
- [ ] Auto-scaling to zero works (cost efficiency)

## Future Enhancements

1. **Webhook Service** — Deploy `turbo-webhook` for AI auto-responses
2. **Redis/Upstash** — Add caching layer
3. **Custom Domain** — turbo.yourdomain.com
4. **GitHub Sync** — Push key issues to GitHub for visibility

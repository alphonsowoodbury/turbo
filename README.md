# Turbo Plan

The executive brain of TurboSoft. All state lives here.

**Decision → Initiative → Feature → Task**

## What Turbo Plan Does

- **Decision Capture**: Strategic and tactical decisions with full rationale, options considered, and constraints
- **Product Decomposition**: Initiatives → Features (Projects) → Tasks (Issues)
- **Task Queue**: Tasks with acceptance criteria for daemon execution
- **Knowledge Graph**: Neo4j-powered semantic relationships
- **Status Tracking**: Execution state flows back from daemon

## What Turbo Plan Does NOT Do

- Terminal/shell access (moved to daemon)
- Git worktree management (moved to daemon)
- Autonomous AI execution (moved to daemon)
- Job search features (removed)
- Resume management (removed)

## Stack

- **Backend**: FastAPI, SQLAlchemy 2.0, PostgreSQL, Neo4j
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind
- **API**: REST + MCP tools for state management

## Quick Start

```bash
# Start databases
docker-compose up -d postgres neo4j

# Run backend
cd turbo
uvicorn main:app --reload --port 8000

# Run frontend (another terminal)
cd frontend
npm install
npm run dev
```

## Key Endpoints

### Core Hierarchy

```
# Decisions (top of hierarchy)
GET    /api/v1/decisions              # List decisions
POST   /api/v1/decisions              # Create decision
GET    /api/v1/decisions/{id}         # Get decision
PATCH  /api/v1/decisions/{id}         # Update decision
POST   /api/v1/decisions/{id}/approve # Approve decision

# Initiatives
GET    /api/v1/initiatives            # List initiatives
POST   /api/v1/initiatives            # Create initiative
GET    /api/v1/initiatives/{id}       # Get initiative

# Projects (Features)
GET    /api/v1/projects               # List projects
POST   /api/v1/projects               # Create project
GET    /api/v1/projects/{id}          # Get project

# Issues (standard CRUD)
GET    /api/v1/issues                 # List issues
POST   /api/v1/issues                 # Create issue
GET    /api/v1/issues/{id}            # Get issue
```

### Daemon Task API

```
# Task endpoints for daemon polling
GET    /api/v1/tasks?status=queued    # Get queued tasks
GET    /api/v1/tasks/{id}             # Full task with context
POST   /api/v1/tasks/{id}/claim       # Claim task for execution
POST   /api/v1/tasks/{id}/complete    # Mark task completed with PR URL
POST   /api/v1/tasks/{id}/fail        # Mark task failed
POST   /api/v1/tasks/{id}/needs-human # Flag for human review
```

## Data Model

```
Decision
  ├── title, summary, rationale
  ├── context, constraints, options_considered
  ├── decision_type: strategic | tactical | technical | product
  └── status: proposed | approved | implemented | superseded | rejected
        │
        ▼
Initiative
  ├── name, description, status
  ├── start_date, target_date
  └── decision_id (FK to Decision)
        │
        ▼
Project (Feature)
  ├── name, description, status
  ├── workspace, priority
  └── acceptance_criteria
        │
        ▼
Issue (Task)
  ├── title, description, type, status, priority
  ├── acceptance_criteria (for daemon)
  ├── assigned_agent, claimed_at (daemon tracking)
  └── pr_url, execution_notes (daemon output)
```

## Issue Status Flow

```
open → ready → queued → in_progress → review → testing → closed
                  ↓
            needs_review (flagged by daemon)
```

- `queued`: Ready for daemon pickup
- `in_progress`: Claimed by an agent
- `review`: PR created, awaiting human review
- `needs_review`: Agent flagged for human intervention (low confidence)

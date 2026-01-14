# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Turbo Code** is an AI-powered local project management and development platform with integrated AI mentors, knowledge graphs, job search, and autonomous development capabilities.

### Technology Stack

**Backend:**
- **API**: FastAPI with async/await (Python 3.10+)
- **Database**: PostgreSQL (production), SQLite (dev) via SQLAlchemy 2.0
- **Graph DB**: Neo4j for knowledge graph and semantic search
- **AI Integration**: Anthropic Claude API, Ollama for local LLMs
- **Architecture**: Clean Architecture (Repository → Service → API/MCP layers)
- **Testing**: pytest with 352 tests (async support, 85% coverage target)

**Frontend:**
- **Framework**: Next.js 15.5 with React 19, TypeScript, Tailwind CSS v4
- **State**: Zustand for global state, React Query for server state
- **UI**: Radix UI primitives, Framer Motion animations
- **Dev Tools**: Turbopack, ESLint 9

**Infrastructure:**
- **MCP Server**: Model Context Protocol for Claude Code integration
- **Services**: Webhook server, docs watcher, headless agent executor
- **Deployment**: Docker Compose stack with 9 services

### Project Structure
```
turbo/
├── api/                    # FastAPI REST API
│   ├── v1/endpoints/      # API endpoints (60+ entity types)
│   └── dependencies.py    # Dependency injection
├── core/                  # Core business logic
│   ├── database/          # Database connection & session management
│   ├── models/            # SQLAlchemy models (30+ entities)
│   ├── repositories/      # Data access layer (CRUD operations)
│   ├── schemas/           # Pydantic schemas (validation)
│   └── services/          # Business logic (65+ service modules)
│       └── agents/        # AI agent implementations
├── cli/                   # Typer-based CLI with Rich formatting
│   └── commands/          # Command groups (projects, issues, tags, etc.)
├── utils/                 # Shared utilities (config, exceptions)
└── mcp_server.py          # MCP server for Claude integration

frontend/
├── app/                   # Next.js App Router pages
│   ├── projects/[id]/    # Dynamic routes for entities
│   ├── work/             # Job search & career management
│   └── ...               # 20+ feature pages
├── components/            # React components
│   ├── ui/               # Radix UI + shadcn components
│   └── [feature]/        # Feature-specific components
└── hooks/                 # Custom React hooks

scripts/                   # Utility scripts
├── claude_webhook_server.py      # Async AI mentor responses
├── claude_headless_service.py    # Autonomous agent executor
└── docs_watcher.py               # Auto-upload documentation
```

## Architecture Patterns

### Data Flow
```
MCP/API → Services → Repositories → Models → Database
         ↓
    Schemas (validation)
```

### Key Locations
- **Models**: `turbo/core/models/` - SQLAlchemy ORM models with relationships
- **Repositories**: `turbo/core/repositories/base.py:19` - BaseRepository with CRUD
- **Services**: `turbo/core/services/` - Business logic orchestration
- **API Endpoints**: `turbo/api/v1/endpoints/` - FastAPI routes
- **MCP Server**: `turbo/mcp_server.py` - MCP tools for Claude
- **Database**: `turbo/core/database/connection.py:69` - Session management

## ⚠️ CRITICAL: Git Worktree Workflow

### Workspace Rules - READ THIS FIRST

**NEVER edit files directly in the main working directory.** All code changes MUST happen in isolated git worktrees.

### Before Making ANY Code Changes:

1. **Check your current directory**:
   ```bash
   pwd
   ```

2. **If you're NOT in `~/worktrees/*`**:
   - ❌ STOP immediately
   - ❌ DO NOT make any edits
   - ✅ Create a worktree first (see workflow below)

3. **If you ARE in `~/worktrees/*`**:
   - ✅ Proceed with changes
   - ✅ Commit your work when done
   - ✅ Submit for review

### Required Workflow for Code Changes

```python
# Step 1: Find an issue to work on
mcp__turbo__list_issues(status="open", priority="high")

# Step 2: Create a worktree for the issue
mcp__turbo__start_work_on_issue(
    issue_id="TURBOCODE-X",  # Can use key or UUID
    started_by="ai:claude",
    project_path="/Users/alphonso/Documents/Code/PycharmProjects/turboCode"
)
# This creates: ~/worktrees/turboCode-TURBOCODE-X/

# Step 3: Change to the worktree directory
cd ~/worktrees/turboCode-TURBOCODE-X

# Step 4: Make your code changes
# ... edit files ...

# Step 5: Commit your changes
git add .
git commit -m "TURBOCODE-X: Description of changes"

# Step 6: Submit for review (removes worktree)
mcp__turbo__submit_issue_for_review(
    issue_id="TURBOCODE-X",
    commit_url="https://github.com/org/repo/commit/abc123"
)
```

### Why This Matters

- **Isolation**: Each issue gets its own branch and working directory
- **Safety**: Main working directory stays clean
- **Parallel Work**: Multiple issues can be worked on simultaneously
- **Tracking**: Work logs automatically track time and changes
- **Cleanup**: Worktrees are automatically removed after review

### Enforcement

A pre-edit hook at `~/.config/claude-code/hooks/pre-edit.sh` will **block** any file edits outside of worktrees. If you see an error about editing outside worktrees, follow the workflow above.

---

## MCP Integration (Primary Interface)

### Using MCP Tools

**ALWAYS use MCP tools** (prefixed with `mcp__turbo__`) for all database operations. These tools provide automatic validation, error handling, and consistent interfaces.

### Common MCP Operations

#### Projects
```python
# List projects
mcp__turbo__list_projects(status="active", limit=10)

# Get project details
mcp__turbo__get_project(project_id="uuid")

# Update project
mcp__turbo__update_project(
    project_id="uuid",
    name="New Name",
    completion_percentage=75.0
)

# Get project issues
mcp__turbo__get_project_issues(project_id="uuid")
```

#### Issues
```python
# Create issue
mcp__turbo__create_issue(
    title="Issue Title",
    description="Description",
    type="feature",
    priority="high",
    project_id="uuid"
)

# List issues with filters
mcp__turbo__list_issues(
    project_id="uuid",
    status="open",
    priority="high"
)

# Update issue
mcp__turbo__update_issue(
    issue_id="uuid",
    status="in_progress",
    priority="critical"
)

# Get issue details (supports both UUID and issue key)
mcp__turbo__get_issue(issue_id="TURBOCODE-123")
```

#### Mentors
```python
# Get mentor
mcp__turbo__get_mentor(mentor_id="uuid")

# Get conversation history
mcp__turbo__get_mentor_messages(mentor_id="uuid", limit=50)

# Add message to conversation
mcp__turbo__add_mentor_message(
    mentor_id="uuid",
    content="Response content"
)
```

#### Tags & Organization
```python
# Create tag
mcp__turbo__create_tag(
    name="frontend",
    color="#3b82f6",
    description="Frontend tasks"
)

# Add tag to entity
mcp__turbo__add_tag_to_entity(
    entity_type="issue",
    entity_id="uuid",
    tag_id="tag-uuid"
)
```

#### Comments
```python
# Add comment (works on any entity)
mcp__turbo__add_comment(
    entity_type="issue",
    entity_id="uuid",
    content="Comment text",
    author_type="ai",
    author_name="Claude"
)

# Get entity comments
mcp__turbo__get_entity_comments(
    entity_type="issue",
    entity_id="uuid"
)
```

#### Dependencies & Relationships
```python
# Add blocker (issue A blocks issue B)
mcp__turbo__add_blocker(
    blocking_issue_id="uuid-a",
    blocked_issue_id="uuid-b"
)

# Get related entities via knowledge graph
mcp__turbo__get_related_entities(
    entity_type="issue",
    entity_id="uuid",
    limit=10
)

# Semantic search
mcp__turbo__search_knowledge_graph(
    query="authentication bug",
    entity_types=["issue", "document"],
    min_relevance=0.7
)
```

### MCP Best Practices

1. **Always use MCP tools first** - Don't use API or direct database access unless MCP doesn't support the operation
2. **Let MCP handle validation** - All MCP tools validate inputs automatically
3. **Use semantic search** - `search_knowledge_graph` is powerful for finding related content
4. **Partial updates** - Only specify fields you want to change
5. **Check responses** - MCP tools return detailed error messages

## Database Operations

### Connection & Sessions
- **Session Factory**: `turbo/core/database/connection.py:56`
- **Async Session**: Uses `AsyncSession` with automatic commit/rollback
- **Context Manager**: `DatabaseConnection` class for manual transaction control
- **Connection Pooling**: Configured for PostgreSQL, StaticPool for SQLite

### Transaction Handling
```python
# Automatic via get_db_session (used by MCP/API)
async for session in get_db_session():
    service = create_project_service(session)
    await service.update_project(id, data)  # Auto-commit on success
```

### Update Pattern
All updates use **partial updates** via `model_dump(exclude_unset=True)`:
- Only send/update changed fields
- Automatic timestamp updates (`updated_at`)
- Validation before database operations
- Rollback on any error

## API Usage Guide

### Starting the API Server
```bash
# Docker (recommended)
docker-compose up -d

# Development with auto-reload
uvicorn turbo.main:app --reload

# Production
uvicorn turbo.main:app --host 0.0.0.0 --port 8000
```

API will be available at `http://localhost:8000` with docs at `http://localhost:8000/docs`

### Key API Endpoints

#### Projects
- `POST /api/v1/projects/` - Create project
- `GET /api/v1/projects/` - List projects (supports ?status=, ?priority=, ?limit=, ?offset=)
- `GET /api/v1/projects/{id}` - Get project
- `PUT /api/v1/projects/{id}` - Update project (partial updates)
- `DELETE /api/v1/projects/{id}` - Delete project

#### Issues
- `POST /api/v1/issues/` - Create issue
- `GET /api/v1/issues/` - List issues
- `GET /api/v1/issues/{id}` - Get issue
- `PUT /api/v1/issues/{id}` - Update issue
- `DELETE /api/v1/issues/{id}` - Delete issue

#### Mentors
- `GET /api/v1/mentors/` - List mentors
- `GET /api/v1/mentors/{id}` - Get mentor
- `POST /api/v1/mentors/{id}/messages` - Send message
- `GET /api/v1/mentors/{id}/messages` - Get conversation
- `DELETE /api/v1/mentors/{id}/conversation` - Clear conversation

### API Implementation
- **Endpoints**: `turbo/api/v1/endpoints/` - All REST endpoints (60+ entity types)
- **Dependencies**: `turbo/api/dependencies.py` - Dependency injection
- **Validation**: Automatic via Pydantic request/response models
- **Session**: Injected via `Depends(get_db_session)`
- **Docs**: OpenAPI at `http://localhost:8000/docs`

### Frontend Architecture

**State Management:**
- **Server State**: React Query with SWR for caching and revalidation
- **Global State**: Zustand stores for UI state and preferences
- **Forms**: React Hook Form with client-side validation

**Key Patterns:**
- **API Client**: `hooks/` contain custom hooks wrapping API calls
- **Components**: Feature-based organization (`components/[feature]/`)
- **Routing**: Next.js App Router with dynamic segments (`[id]`)
- **Real-time**: Server-Sent Events (SSE) for streaming AI responses
- **Terminal**: xterm.js integration for embedded shell access

**Styling:**
- **Tailwind v4**: Utility-first CSS with custom theme
- **shadcn/ui**: Composable Radix UI components in `components/ui/`
- **Animations**: Framer Motion for transitions and gestures
- **Dark Mode**: next-themes with system detection

**Notable Features:**
- **Unified Create**: Multi-entity creation dialog with context switching
- **Drag & Drop**: @dnd-kit for kanban boards and reordering
- **Markdown**: @uiw/react-md-editor with syntax highlighting
- **Diagrams**: Mermaid.js for flowcharts and diagrams

## Configuration

### Docker Deployment
```bash
# Start complete stack (API + DB + Frontend + Webhook Server)
docker-compose up -d

# View logs
docker-compose logs -f turbo-api
docker-compose logs -f turbo-frontend

# Stop
docker-compose down

# Rebuild after changes
docker-compose build api
docker-compose up -d
```

### Environment Configuration
- **Database URL**: Set in `docker-compose.yml` or `.env`
- **API Port**: 8000 (configurable)
- **Frontend Port**: 3001 (configurable)
- **MCP Server**: Runs within Claude Code environment

## Development Commands

### Running the Stack

```bash
# Full Docker stack (all services)
docker-compose up -d

# View logs for specific services
docker-compose logs -f api          # Backend API
docker-compose logs -f frontend     # Next.js frontend
docker-compose logs -f webhook      # AI webhook server
docker-compose logs -f neo4j        # Knowledge graph

# Development mode (local backend, Docker databases)
docker-compose up -d postgres neo4j redis
uvicorn turbo.main:app --reload     # API on :8000
cd frontend && npm run dev          # Frontend on :3001

# Stop services
docker-compose down
```

### Testing

```bash
# Run all tests
pytest

# Run specific test types
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests
pytest -m "not slow"            # Skip slow tests
pytest -k "test_project"        # Run tests matching pattern

# Run with coverage
pytest --cov=turbo --cov-report=html
open htmlcov/index.html

# Run single test file
pytest tests/unit/services/test_project.py -v
```

### Code Quality

```bash
# Format code (auto-fix)
black .
ruff --fix .

# Linting (check only)
ruff check .
mypy .

# Pre-commit hooks (recommended)
pre-commit install
pre-commit run --all-files
```

### Frontend Development

```bash
cd frontend

# Development server (with Turbopack)
npm run dev              # Runs on port 3001

# Build for production
npm run build
npm run start

# Linting
npm run lint
```

### Database Operations

```bash
# Initialize database (first time)
python -c "import asyncio; from turbo.core.database.connection import init_database; asyncio.run(init_database())"

# Access PostgreSQL (when Docker is running)
docker exec -it turbo-postgres psql -U turbo -d turbo

# Access pgAdmin UI
open http://localhost:5050  # admin@admin.com / admin

# Access Neo4j Browser
open http://localhost:7474  # neo4j / turbo_graph_password
```

### CLI Usage

```bash
# Configure database (one-time setup)
turbo config database --type sqlite      # Local development
turbo config database --type postgres    # Production

# Common operations
turbo projects list
turbo issues create --title "Fix bug" --type bug --priority high
turbo init                               # Initialize workspace
```

## Common Patterns for Claude

### When Asked to Update Database:

**ALWAYS use MCP tools first:**
```python
# Update issue status
mcp__turbo__update_issue(
    issue_id="uuid",
    status="closed"
)

# Update project completion
mcp__turbo__update_project(
    project_id="uuid",
    completion_percentage=100.0
)
```

### Getting Entity Information:

```python
# List to find UUIDs
projects = mcp__turbo__list_projects(status="active")

# Get detailed information
project = mcp__turbo__get_project(project_id="uuid")
issues = mcp__turbo__get_project_issues(project_id="uuid")

# Search for entities
results = mcp__turbo__search_knowledge_graph(
    query="authentication",
    entity_types=["issue", "document"]
)
```

### Best Practices:

- **Use MCP tools exclusively** - They handle all validation and error handling
- **Partial updates only** - Only specify fields that need to change
- **Leverage semantic search** - Use knowledge graph for finding related content
- **Check entity relationships** - Use get_related_entities for discovering connections
- **Add context via comments** - Use add_comment to document changes
- **Transaction safety** - All MCP tools auto-rollback on error

## Entity Field Patterns

### Project
- Required: `name`, `description`
- Optional: `priority` (low|medium|high|critical), `status` (active|on_hold|completed|archived), `completion_percentage` (0-100), `workspace` (personal|freelance|work)
- Auto-generated: `project_key` (e.g., "TURBOCODE")

### Issue
- Required: `title`, `description`, `project_id`, `type`, `priority`
- Optional: `status` (open|in_progress|review|testing|closed), `assignee` (email), `due_date`
- Auto-generated: `issue_key` (e.g., "TURBOCODE-123")

### Mentor
- Required: `name`, `description`, `persona`, `workspace`
- Optional: `work_company`, `context_preferences`, `is_active`

### Document
- Required: `title`, `content`, `project_id`
- Optional: `doc_type`, `version`, `format`

### Tag
- Required: `name`, `color`
- Optional: `description`

## Key Services & Infrastructure

### Webhook System

The platform includes a webhook server (`scripts/claude_webhook_server.py`) that handles asynchronous AI responses for mentor conversations:

- Listens for incoming mentor messages via HTTP POST
- Builds context from projects, issues, and documents
- Calls Claude API with mentor persona and context
- Posts responses back via MCP tools
- Supports WebSearch for current information
- Enables real-time AI mentor conversations without blocking main app

### Knowledge Graph (Neo4j)

Semantic search and relationship tracking powered by Neo4j (`turbo/core/services/knowledge_graph.py`):

- **Entity Nodes**: Projects, Issues, Documents, Mentors, etc.
- **Relationships**: BLOCKS, RELATES_TO, TAGGED_WITH, etc.
- **Embeddings**: sentence-transformers for semantic search
- **Operations**: `search_knowledge_graph()`, `get_related_entities()`
- **Sync**: Automatic sync from PostgreSQL to Neo4j on entity changes

### Git Worktree Integration

Isolated development environments via git worktrees (`turbo/core/services/git_worktree.py`):

- **MCP Tools**: `start_work_on_issue()`, `submit_issue_for_review()`
- **Workflow**: Create branch → Isolated worktree → Commit → Cleanup
- **Location**: `~/worktrees/{project}-{issue-key}/`
- **Tracking**: Automatic work logs with time tracking
- **Enforcement**: Pre-edit hook blocks edits outside worktrees

### AI Agent System

Multiple AI capabilities integrated throughout the platform:

- **Mentors** (`turbo/core/services/mentor.py`): Persona-based AI assistants with conversation memory
- **PM Agent** (`turbo/core/services/agents/pm_agent.py`): Project management automation
- **Headless Service** (`scripts/claude_headless_service.py`): Autonomous issue implementation
- **Action Classifier** (`turbo/core/services/action_classifier.py`): Intent detection from user input
- **Streaming** (`turbo/core/services/streaming.py`): Server-sent events for real-time AI responses

### Document & Content Services

- **PDF Generation** (`turbo/core/services/pdf_generator.py`): WeasyPrint-based PDF creation with templates
- **Resume Services**: AI extraction, tailoring, generation, deduplication
- **Literature** (`turbo/core/services/literature.py`): RSS/web content extraction with readability
- **Podcasts** (`turbo/core/services/podcast.py`): Audio transcription with faster-whisper + speaker diarization
- **Markdown Parser** (`turbo/core/services/markdown_parser.py`): Extract tasks, mentions, and structure

### Job Search Ecosystem

Multi-source job aggregation and tracking (`turbo/core/services/job_scrapers/`):

- **Scrapers**: Adzuna, Indeed, Reed, Remotive, JSearch, WeWorkRemotely, etc.
- **Deduplication** (`turbo/core/services/job_deduplication.py`): Fuzzy matching with rapidfuzz
- **Applications**: Full application lifecycle tracking
- **Resume Generation**: AI-powered tailoring to job descriptions
- **Network Contacts**: Professional network management

### Work Queue System

Auto-ranking queue for prioritizing tasks (`turbo/api/v1/endpoints/work_queue.py`):

- **Priority Score**: Combines due date, priority, type, and staleness
- **Auto-refresh**: Real-time updates as issues change
- **Filtering**: By workspace, tags, assignee
- **Integration**: Issue creation/updates automatically update queue

## Important Notes

### Entity Keys
- Projects and issues have auto-generated keys (e.g., "TURBOCODE", "TURBOCODE-123")
- Keys can be used in place of UUIDs for `get_issue()` and similar operations
- Keys are human-readable and appear in worktree paths and branch names

### Async/Await Pattern
- All database operations are async
- Use `await` for all service methods
- Sessions are managed via async context managers

### Service Architecture
- Services receive repositories via dependency injection
- Business logic lives in services, not repositories
- Repositories handle only CRUD operations

### Testing Philosophy
- TDD approach: Write tests first
- Target 85% code coverage
- Use pytest fixtures for common setup
- Mock external dependencies

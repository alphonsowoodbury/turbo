# Turbo Agent

Autonomous project management agents built on the [Claude Agent SDK](https://docs.anthropic.com/en/docs/agents/agent-sdk).

## Quick Start

```bash
# 1. Start the Turbo API
cd /Volumes/TURBO/turbo-plan
uvicorn turbo.main:app --port 8001

# 2. Install dependencies
pip install -e ".[agent]"

# 3. Set your API key
export ANTHROPIC_API_KEY=sk-ant-...

# 4. Run the agent
turbo-agent "Triage all open issues and recommend priorities"

# 5. Or use Python directly
python -c "
import asyncio
from turbo.agent import TurboAgent

async def main():
    agent = TurboAgent(project_id='your-project-id')
    result = await agent.run('What is the status of this project?')
    print(result)

asyncio.run(main())
"
```

## What This Is

Turbo Plan has an **MCP server** (`mcp_server.py`) that exposes 160+ tools to Claude Code. That's a **tool server** -- Claude Code calls it, and it responds.

Turbo Agent is the opposite: an **agent client** that uses the Claude Agent SDK to autonomously reason, plan, and act. You give a goal, the agent figures out the steps, delegates to specialists, and reports back.

```
  BEFORE (MCP only)                      AFTER (Agent SDK)

  You ──> Claude Code ──> MCP ──> API    You ──> TurboAgent ──> SDK Tools ──> API
                                                     |
  You drive every step.                              +──> triager (read-only)
                                                     +──> planner (create)
                                                     +──> reporter (comment)
                                                     +──> worker (claim + log)

                                          Agent drives itself.
```

## Architecture

```
turbo/agent/
├── __init__.py      # Public exports
├── http.py          # Resilient HTTP client (retry, circuit breaker)
├── tools.py         # 16 SDK-native tools with Pydantic validation
├── hooks.py         # Security: scope enforcement, audit, rate limits
├── subagents.py     # 4 specialized agents with restricted tools
├── client.py        # TurboAgent — the main orchestrator
├── cli.py           # Command-line interface
└── logging.py       # Structured JSON logging
```

### Data Flow

```
User Prompt
    |
    v
TurboAgent (client.py)
    |
    +-- builds ClaudeAgentOptions (model, tools, hooks, subagents)
    |
    v
Claude Agent SDK (query / ClaudeSDKClient)
    |
    v
PreToolUse Hooks (hooks.py)
    |-- 1. audit_log_tool_call      ── log every attempt
    |-- 2. rate_limit_tool_calls    ── sliding window check
    |-- 3. enforce_project_scope    ── multi-tenant isolation
    |-- 4. block_destructive_cmds   ── Bash safety net
    |
    v  (if all hooks pass)
Tool Execution (tools.py)
    |-- Pydantic validation         ── reject bad input early
    |-- _safe_call wrapper          ── catch all errors
    |
    v
TurboHTTPClient (http.py)
    |-- Connection pooling          ── reuse connections
    |-- Retry with backoff          ── handle transient failures
    |-- Circuit breaker             ── fail fast when API is down
    |
    v
Turbo API (FastAPI)
    |
    v
PostToolUse Hooks
    |-- audit_log_tool_result       ── log outcome
    |
    v
Response back to Claude Agent SDK
```

---

## File-by-File

### `http.py` -- Resilient HTTP Client

Every tool talks to the Turbo API through `TurboHTTPClient`, a singleton that provides:

- **Connection pooling.** One `httpx.AsyncClient` reused across all tool calls, not created per-request.
- **Retry with exponential backoff.** 3 retries at 1s, 2s, 4s intervals for status codes 429, 502, 503, 504 and connection/timeout errors.
- **Circuit breaker.** After 5 consecutive failures, all requests are short-circuited for 30 seconds. Prevents hammering a downed API.
- **Structured errors.** `TurboAPIError` carries the endpoint, status code, and response body. Its `agent_message()` method returns guidance the agent can act on:

```python
# 404 → "Error: GET /projects/xyz not found (404). Try: Use a list tool to find valid IDs."
# 422 → "Error: Invalid input for POST /issues (422). Details: ... Try: Check required fields."
# 500 → "Error: Server error on GET /issues (500). Try: Wait a moment and retry."
```

### `tools.py` -- 16 Validated Tools

Each tool validates input with Pydantic before making any API call:

```python
class CreateIssueInput(BaseModel):
    project_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=500)
    priority: Literal["critical", "high", "medium", "low"] | None = None

@tool("create_issue", "Create a new issue", CreateIssueInput.model_json_schema())
async def create_issue(args: dict) -> dict:
    validated, err = _validate(CreateIssueInput, args)
    if err:
        return err  # {"isError": True, "content": [{"text": "Invalid input: ..."}]}
    return await _safe_call(
        get_http_client().post("/issues", validated.model_dump(exclude_none=True))
    )
```

**Key design choice:** `_validate()` returns `(model, None)` on success or `(None, error_dict)` on failure -- no exceptions for flow control. The agent sees a structured error response, not a stack trace.

| Group | Tools | Access |
|-------|-------|--------|
| **Projects** | `list_projects`, `get_project`, `get_project_issues` | Read |
| **Issues** | `list_issues`, `get_issue`, `create_issue`, `update_issue`, `start_issue_work` | Read + Write |
| **Work queue** | `get_work_queue`, `get_next_issue` | Read |
| **Work logs** | `log_work` | Write |
| **Initiatives** | `list_initiatives` | Read |
| **Decisions** | `list_decisions`, `create_decision` | Read + Write |
| **Comments** | `add_comment` | Write |
| **Analysis** | `project_status_summary` | Read |

Tools are categorized into `READ_TOOLS` and `WRITE_TOOLS` sets, which subagents use to enforce least-privilege access.

### `hooks.py` -- Security Enforcement

Four hooks intercept every tool call before and after execution:

**1. `enforce_project_scope`** -- Multi-tenant isolation

Handles three cases:
- Tools with `project_id` in args: direct check against `TURBO_ALLOWED_PROJECT_IDS`
- Tools with `issue_id` (like `update_issue`): resolves the issue's project via API, caches the mapping, then checks scope
- Cross-project read tools (like `list_projects`): allowed, but if they pass an explicit `project_id`, it's validated

If scope can't be verified (API failure during issue resolution), the call is **denied for safety**.

**2. `block_destructive_commands`** -- Bash safety net

Pattern-matches against 14 dangerous commands (`rm -rf`, `DROP TABLE`, `git push --force`, etc.). Case-insensitive.

**3. `audit_log_tool_call` / `audit_log_tool_result`** -- Observability

Every tool call is logged to `~/.turbo/agent-audit.jsonl` with:
- Tool name, input hash, truncated input summary
- Timestamp, tool_use_id, is_error flag
- Log rotation at 10 MB, 5 backups kept
- Async file writes via `asyncio.Lock` (non-blocking)

**4. `rate_limit_tool_calls`** -- Runaway prevention

Thread-safe sliding window (60 seconds) using `asyncio.Lock` + `collections.deque`. Default: 30 calls/minute per tool. Configurable via `TURBO_AGENT_RATE_LIMIT`.

### `subagents.py` -- Least-Privilege Specialists

| Subagent | Can do | Cannot do | Model |
|----------|--------|-----------|-------|
| **triager** | Read projects, issues, summaries | Any write operation | Sonnet |
| **planner** | Read + create issues and decisions | Update or delete existing | Sonnet |
| **reporter** | Read + post comments | Create, update, or delete issues | Haiku |
| **worker** | Read + claim issues + log work | Create issues or decisions | Sonnet |

Models are configurable via `TURBO_AGENT_SMART_MODEL` and `TURBO_AGENT_FAST_MODEL` environment variables.

### `client.py` -- The Orchestrator

Three usage modes:

```python
agent = TurboAgent(project_id="abc-123", max_budget_usd=2.0)

# One-shot
result = await agent.run("Triage all open issues")

# Streaming (for UIs)
async for event in agent.stream("Generate a status report"):
    print(event["type"], event["content"])

# Multi-turn session
async with agent.session() as s:
    await s.send("What projects do I have?")
    await s.send("Show issues for the first one")
```

Features:
- Input validation: `max_turns >= 1`, `max_budget_usd > 0`
- Cost tracking: logs final cost, warns at 80% of budget
- Resource cleanup: `await agent.close()` shuts down HTTP client

### `cli.py` -- Terminal Interface

```bash
turbo-agent "Triage all open issues"              # One-shot
turbo-agent -p abc-123 "Generate a status report"  # Project-scoped
turbo-agent -s -v "Break down auth feature"        # Stream + verbose
turbo-agent -i                                     # Interactive REPL
turbo-agent -o report.md "Status report"           # Save to file
```

| Flag | Short | Default | Purpose |
|------|-------|---------|---------|
| `--project` | `-p` | None | Scope to project |
| `--model` | `-m` | claude-sonnet-4 | Model selection |
| `--max-turns` | | 25 | Turn limit |
| `--max-budget` | | 2.0 | Cost ceiling (USD) |
| `--stream` | `-s` | false | Stream events |
| `--verbose` | `-v` | false | Show tool calls |
| `--output` | `-o` | None | Save result to file |
| `--interactive` | `-i` | false | Multi-turn REPL |

### `logging.py` -- Structured Output

JSON-formatted logging with contextual fields:

```json
{"timestamp": "2026-02-24T...", "level": "INFO", "logger": "turbo.agent.client", "message": "Run complete (cost=$0.19, turns=3)"}
{"timestamp": "2026-02-24T...", "level": "WARNING", "logger": "turbo.agent.http", "message": "Retryable 503 on GET /issues (attempt 2/4, backoff 2.0s)"}
```

---

## Test Suite

168 tests, 85.7% coverage, runs in <0.5 seconds with zero network calls.

```bash
# Run tests
python -m pytest tests/agent/ -v --override-ini="asyncio_mode=auto" --rootdir=tests/agent -c /dev/null

# With coverage
python -m pytest tests/agent/ --cov=turbo/agent --cov-report=term-missing \
    --override-ini="asyncio_mode=auto" --rootdir=tests/agent -c /dev/null
```

| Test File | Tests | What it covers |
|-----------|-------|---------------|
| `test_http.py` | 24 | Retry, circuit breaker, errors, close, singleton |
| `test_tools.py` | 44 | All 16 handlers, Pydantic validation, error formatting |
| `test_hooks.py` | 27 | Scope enforcement, destructive blocking, audit, rate limiting |
| `test_client.py` | 19 | Config, prompts, options, run/stream mocking |
| `test_integration.py` | 11 | Full pipeline, hook chain, subagent scoping |
| `test_cli.py` | 28 | Arg parsing, oneshot/stream/interactive modes |
| `test_subagents.py` | 11 | Role access, tool validation, model assignments |

---

## MCP Server vs Agent Module

| | MCP Server (`mcp_server.py`) | Agent Module (`turbo/agent/`) |
|---|---|---|
| **Direction** | Claude Code calls Turbo | Turbo runs Claude autonomously |
| **SDK** | MCP SDK (`mcp` package) | Claude Agent SDK (`claude-agent-sdk`) |
| **Who decides** | You type every command | Agent decides what to do |
| **Tool count** | 160+ (everything) | 16 (curated core set) |
| **Transport** | stdio (subprocess) | In-process (function calls) |
| **Validation** | Server-side only | Pydantic on every input |
| **Security** | `is_project_allowed()` | Hooks: scope + audit + rate limit + destructive blocking |
| **Resilience** | None | Retry + circuit breaker + structured errors |
| **Multi-agent** | No | 4 specialized subagents |
| **Session memory** | No (stateless) | Yes (multi-turn via ClaudeSDKClient) |

They complement each other. The MCP server is for **you** working interactively with Claude Code. The agent module is for **autonomous execution**.

---

## Further Reading

- [ARCHITECTURE.md](ARCHITECTURE.md) -- Security model, resilience patterns, design decisions
- [OPERATIONS.md](OPERATIONS.md) -- Environment variables, audit logs, troubleshooting

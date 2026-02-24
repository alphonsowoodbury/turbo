# Architecture

Deep dive into security, resilience, and design decisions in the Turbo Agent module.

---

## Security Model

### Threat Model

The agent executes autonomously — no human approves each tool call. This creates three risk surfaces:

1. **Scope creep.** Agent accesses projects it shouldn't.
2. **Runaway execution.** Agent enters an infinite loop burning tokens and API calls.
3. **Destructive actions.** Agent executes dangerous shell commands via the Bash tool.

Every hook in `hooks.py` maps directly to one of these risks.

### Hook Execution Order

Hooks execute sequentially on every `PreToolUse` event. Order matters — auditing runs first so denied calls are still logged.

```
Tool call arrives
    │
    ├── 1. audit_log_tool_call (matcher: .*)
    │       Always runs. Logs tool name, input hash, timestamp.
    │       Never denies.
    │
    ├── 2. rate_limit_tool_calls (matcher: .*)
    │       Sliding 60-second window. Denies if count >= MAX_CALLS_PER_MINUTE.
    │       Blocks runaway loops before they hit the API.
    │
    ├── 3. enforce_project_scope (matcher: mcp__turbo__.*)
    │       Multi-tenant isolation. Only runs on Turbo tools.
    │       Three resolution paths (see below).
    │
    └── 4. block_destructive_commands (matcher: Bash)
            Pattern-matches against 14 dangerous commands.
            Only runs on Bash tool calls.
```

After tool execution, `PostToolUse` runs `audit_log_tool_result` to record outcome and error status.

### Project Scope Enforcement

The scope hook handles three categories of tool calls:

```
Tool call with project_id in args?
    │
    ├── YES → Direct check against TURBO_ALLOWED_PROJECT_IDS
    │         Denied if not in set. Allowed if in set.
    │
    └── NO → Is it an issue-scoped tool? (get_issue, update_issue, etc.)
              │
              ├── YES → Extract issue_id from args
              │         Check _issue_project_cache
              │         If miss: resolve via GET /issues/{id} → get project_id
              │         Cache result. Check resolved project_id against allowed set.
              │         If API fails: DENY (fail closed, not open)
              │
              └── NO → Is it a cross-project read tool? (list_projects, etc.)
                        │
                        ├── YES → Allow (server returns filtered data)
                        │         BUT: if args contain project_id, validate it
                        │
                        └── NO → Allow (tool doesn't carry project context)
```

**Key design choice: fail closed.** If an issue_id can't be resolved to a project (API error, malformed ID), the call is denied. This prevents a bypass where an attacker passes a nonexistent issue_id to skip scope checks.

**Caching.** The `_issue_project_cache` dict maps `issue_id → project_id`. This avoids re-resolving the same issue on repeated calls. The cache persists for the agent's lifetime and can be cleared with `clear_issue_cache()`.

### Issue-Scoped Tools

These tools take `issue_id` instead of `project_id`, which requires the extra resolution step:

| Tool | Why it's issue-scoped |
|------|-----------------------|
| `get_issue` | Fetch by ID/key, no project context in args |
| `update_issue` | Modify by ID, must verify project ownership |
| `start_issue_work` | Claims issue, must verify project ownership |
| `log_work` | Writes to issue, must verify project ownership |

### Cross-Project Read Tools

These read across all projects and are allowed even under scope enforcement:

| Tool | Why allowed |
|------|-------------|
| `list_projects` | Agent needs to discover available projects |
| `list_issues` | May filter by status across projects |
| `list_initiatives` | Read-only cross-project data |
| `list_decisions` | Read-only cross-project data |
| `get_work_queue` | May read global queue |
| `get_next_issue` | May read global queue |

However, if any of these tools pass an explicit `project_id` in args, that ID is validated against the allowed set.

### Rate Limiting

**Algorithm:** Sliding window with `collections.deque`.

```
Window: 60 seconds
Max: 30 calls per tool per minute (configurable via TURBO_AGENT_RATE_LIMIT)
Storage: dict[tool_name, deque[float]] — timestamps of recent calls
Lock: asyncio.Lock (one lock for all tools)
```

On each call:
1. Acquire `_rate_lock`
2. Prune entries older than 60 seconds from the front of the deque
3. If `len(deque) >= MAX_CALLS_PER_MINUTE` → deny
4. Append `time.monotonic()` to deque
5. Release lock

**Why deque?** `maxlen` prevents unbounded memory growth even if pruning is delayed. The `maxlen` is set to `MAX_CALLS_PER_MINUTE + 10` to avoid premature eviction during normal operation.

**Why asyncio.Lock?** Multiple subagents or concurrent tool calls could race on `_call_timestamps`. The lock serializes access. It's non-blocking for other async tasks (only blocks coroutines contending for the same lock).

### Destructive Command Blocking

Pattern list (case-insensitive substring match):

```
rm -rf, rm -r /, git push --force, git push -f, git reset --hard,
DROP TABLE, DROP DATABASE, DELETE FROM, TRUNCATE TABLE,
git branch -D, git branch -d main, git branch -d master,
chmod -R 777, :(){ :|:& };:
```

This is a defense-in-depth measure. The agent shouldn't have Bash access in most configurations, but if it does (via `allowed_tools`), this prevents the worst outcomes.

### Audit Trail

**Format:** JSONL (one JSON object per line).

```json
{"event":"tool_call","tool":"mcp__turbo__list_projects","tool_use_id":"tu-abc","input_hash":"a1b2c3d4e5f6g7h8","input_summary":{"status":"active"},"timestamp":"2026-02-24T10:30:00+00:00"}
{"event":"tool_result","tool":"mcp__turbo__list_projects","tool_use_id":"tu-abc","is_error":false,"timestamp":"2026-02-24T10:30:01+00:00"}
```

**Fields:**

| Field | Purpose |
|-------|---------|
| `event` | `tool_call` or `tool_result` |
| `tool` | Full tool name including `mcp__turbo__` prefix |
| `tool_use_id` | SDK-assigned ID for correlating call/result pairs |
| `input_hash` | SHA-256 of canonical JSON (sorted keys) — tamper detection |
| `input_summary` | Truncated input (values > 200 chars are clipped) |
| `is_error` | Whether the tool returned an error (result events only) |
| `timestamp` | UTC ISO 8601 |

**Rotation:** 10 MB per file, 5 backups kept. Uses Python's `RotatingFileHandler`.

**Concurrency:** Writes are serialized via `_audit_lock` (asyncio.Lock). The lock scope is minimal — just the `logger.info()` call.

---

## Resilience Model

### HTTP Client

All tool→API communication goes through `TurboHTTPClient`, a singleton.

#### Connection Pooling

One `httpx.AsyncClient` instance is created on first use and reused for all subsequent requests. This avoids:
- TCP handshake overhead per request
- Connection limit exhaustion under concurrent tool calls
- SSL negotiation costs (if HTTPS is configured)

The client is configured with:
- `connect=5.0s` — fail fast if API is unreachable
- `read=30.0s` — allow time for expensive queries
- `write=10.0s` — POST/PATCH bodies should be small
- `pool=5.0s` — don't wait long for a connection from the pool
- `follow_redirects=True` — handle FastAPI's trailing-slash redirects

#### Retry Strategy

```
Attempt 1 → fail (retryable) → wait 1s
Attempt 2 → fail (retryable) → wait 2s
Attempt 3 → fail (retryable) → wait 4s
Attempt 4 → fail → raise TurboAPIError
```

**Retryable conditions:**
- HTTP status codes: 429 (rate limited), 502, 503, 504 (infrastructure)
- `httpx.ConnectError` — API process crashed/restarting
- `httpx.ConnectTimeout` — network partition
- `httpx.TimeoutException` — slow response

**Non-retryable conditions (fail immediately):**
- 400, 404, 409, 422 — client errors that won't resolve by retrying
- Any other 4xx status

#### Circuit Breaker

State machine:

```
                  success
    CLOSED ──────────────── CLOSED
       │
       │  5 consecutive failures
       ▼
     OPEN ── (all requests short-circuited with CircuitOpenError)
       │
       │  30 seconds elapsed
       ▼
   HALF-OPEN ── (one probe request allowed)
       │
       ├── success → CLOSED (reset failure count)
       └── failure → OPEN (restart 30s timer)
```

**Why a circuit breaker?** Without it, a downed API causes every tool call to burn through 4 retry attempts (1 + 2 + 4 = 7 seconds each). With 16 tools and an active agent, that's minutes of wasted time. The circuit breaker fails the first tool call after 5 failures, then all subsequent calls fail instantly for 30 seconds.

### Error Propagation

Errors flow through three layers, each adding context:

```
Layer 1: httpx raises HTTPStatusError or ConnectError
    │
    ▼
Layer 2: TurboHTTPClient wraps as TurboAPIError
         Adds: endpoint, status_code, body
         Adds: agent_message() with actionable guidance
    │
    ▼
Layer 3: _safe_call() in tools.py catches and formats
         Returns: {"isError": true, "content": [{"text": "Error: ..."}]}
         Agent sees structured error, not a stack trace
```

The agent never sees raw exceptions. Every error includes:
1. What happened (status code, endpoint)
2. What to try next (use a list tool, check fields, wait and retry)

Example messages:

| Status | Agent sees |
|--------|-----------|
| 404 | `Error: GET /projects/xyz not found (404). Try: Use a list tool to find valid IDs.` |
| 422 | `Error: Invalid input for POST /issues (422). Details: ... Try: Check required fields and value formats.` |
| 500 | `Error: Turbo API server error on GET /issues (500). Try: Wait a moment and retry.` |
| Circuit open | `Error: Circuit breaker open. API calls paused for 25s.` |

---

## Design Decisions

### Why In-Process Tools (Not MCP stdio)

The MCP server (`mcp_server.py`) communicates via stdio subprocess transport. The agent module uses `create_sdk_mcp_server()` which creates an in-process tool server — no subprocess, no serialization overhead.

**Trade-off:** In-process tools share the agent's memory space, so a bug in a tool handler could crash the agent. This is acceptable because:
1. Tools are simple HTTP wrappers — no complex state
2. `_safe_call()` catches all exceptions
3. The HTTP client has its own error handling layer

**Benefit:** Eliminates the ProcessTransport timing issues that plague stdio MCP servers in the Agent SDK (see `_wrap_prompt()` workaround).

### Why Tuple-Return Validation

```python
# Pattern used in every tool:
validated, err = _validate(CreateIssueInput, args)
if err:
    return err
```

**Alternative considered:** Raising `ValidationError` and catching in `_safe_call()`. Rejected because:
1. Validation is a normal control flow case, not an exceptional condition
2. The error response needs different formatting than API errors
3. It would require `_safe_call()` to know about Pydantic — coupling unrelated concerns

The tuple pattern keeps each tool function's logic linear (no try/except) and makes the validation→proceed→API-call flow visible at a glance.

### Why Deque for Rate Limiting (Not Counter)

**Alternative considered:** Simple counter that resets every 60 seconds. Rejected because a counter has a burst problem at window boundaries — 30 calls at second 59, counter resets, 30 more calls at second 61 = 60 calls in 2 seconds.

The sliding window with deque tracks exact timestamps. Each call prunes expired entries, so the limit is truly "30 calls in any 60-second window."

### Why Module-Level Singleton HTTP Client

```python
_default_client: TurboHTTPClient | None = None

def get_http_client() -> TurboHTTPClient:
    global _default_client
    if _default_client is None:
        _default_client = TurboHTTPClient()
    return _default_client
```

**Alternative considered:** Dependency injection via constructor. Rejected for agent SDK compatibility — the `@tool` decorator requires plain async functions, not methods on an instance. Passing state through tool arguments would require SDK modifications.

The singleton is initialized lazily and can be replaced in tests via `monkeypatch.setattr("turbo.agent.tools.get_http_client", lambda: mock)`.

### Subagent Least-Privilege

Each subagent gets a curated tool list, not all 16 tools:

| Subagent | Principle | Tools withheld |
|----------|-----------|----------------|
| triager | Read-only analysis shouldn't have side effects | All write tools |
| planner | Can create but shouldn't modify existing work | `update_issue`, `start_issue_work`, `log_work` |
| reporter | Can observe and comment, not change state | `create_issue`, `update_issue`, `start_issue_work` |
| worker | Can claim and log, not create new work items | `create_issue`, `create_decision` |

This prevents a misbehaving subagent from causing damage beyond its role. The orchestrator (TurboAgent) has all tools and delegates to subagents for focused tasks.

### Why _wrap_prompt() Exists

The Claude Agent SDK has a timing bug (#386) where string prompts passed to `query()` cause `ProcessTransport is not ready for writing` errors when SDK MCP servers are configured. The async generator path triggers proper MCP initialization.

```python
async def _wrap_prompt(text: str) -> AsyncIterator[dict[str, Any]]:
    yield {"type": "user", "message": {"role": "user", "content": text}}
```

This adds zero overhead and will be removed when the SDK fixes the bug.

---

## Data Flow

### One-Shot Execution

```
User: "Triage all open issues"
    │
    ▼
TurboAgent.run(prompt)
    │
    ├── _build_options() → ClaudeAgentOptions
    │     model, tools, hooks, subagents, budget
    │
    ├── _wrap_prompt(prompt) → async generator
    │
    ▼
query(prompt, options) → async iterator of messages
    │
    ├── Claude decides: call mcp__turbo__list_projects
    │     │
    │     ├── PreToolUse hooks fire:
    │     │     audit_log → rate_limit → enforce_scope
    │     │
    │     ├── Tool executes:
    │     │     _validate(ListProjectsInput, args)
    │     │     _safe_call(get_http_client().get("/projects"))
    │     │
    │     ├── PostToolUse hooks fire:
    │     │     audit_log_result
    │     │
    │     └── Tool result returned to Claude
    │
    ├── Claude decides: delegate to triager subagent
    │     │
    │     └── triager runs with READ-ONLY tool set
    │           Same hook chain applies to each tool call
    │
    ├── Claude produces final response
    │
    ▼
ResultMessage
    ├── result text → returned to caller
    ├── total_cost_usd → logged, budget check
    └── num_turns → logged
```

### Multi-Turn Session

```
async with agent.session() as s:
    │
    ├── ClaudeSDKClient created with agent options
    │
    ├── s.send("What projects do I have?")
    │     └── query + receive_response cycle
    │
    ├── s.send("Show issues for the first one")
    │     └── Same cycle, with conversation context preserved
    │
    └── __aexit__ → client cleanup
```

---

## Test Architecture

168 tests, 85.7% coverage, <0.5s execution, zero network calls.

### Test Isolation

- **No real HTTP calls.** `mock_http_transport` fixture creates an `httpx.MockTransport`. Tool tests monkeypatch `get_http_client`.
- **No real files.** Audit log tests use `tmp_path`. Environment variables cleaned via `clean_env` autouse fixture.
- **No real SDK calls.** `client.py` tests mock `query()` to yield fake messages.
- **No root conftest.** Tests use `--rootdir=tests/agent -c /dev/null` to avoid importing unrelated project modules that have Pydantic v1/v2 conflicts.

### What Each Test File Validates

| File | Layer | Key assertions |
|------|-------|----------------|
| `test_http.py` | Network | Retry count, circuit breaker state transitions, error types |
| `test_tools.py` | Validation | Pydantic rejects bad input, _safe_call catches errors, all 16 handlers work |
| `test_hooks.py` | Security | Scope denial, rate limit enforcement, audit log structure, destructive blocking |
| `test_client.py` | Orchestration | Options built correctly, prompts wrapped, run/stream return expected formats |
| `test_subagents.py` | Access control | Tool lists correct, no write tools in read-only agents |
| `test_cli.py` | Interface | Arg parsing, validation, mode selection |
| `test_integration.py` | End-to-end | Full pipeline: hooks → tool → HTTP → response, hook chain order |

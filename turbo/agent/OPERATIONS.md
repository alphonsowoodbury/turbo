# Operations

Environment variables, audit logs, cost monitoring, and troubleshooting for the Turbo Agent module.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TURBO_API_URL` | `http://localhost:8001/api/v1` | Base URL for the Turbo API. Set to production URL for deployed agents. |
| `TURBO_API_KEY` | *(empty)* | Bearer token for API authentication. If empty, no auth header is sent. |
| `ANTHROPIC_API_KEY` | *(required)* | API key for Claude. The Agent SDK reads this directly. |
| `TURBO_ALLOWED_PROJECT_IDS` | *(empty)* | Comma-separated project UUIDs. When set, the scope hook restricts all operations to these projects. When empty, all projects are accessible. |
| `TURBO_AGENT_RATE_LIMIT` | `30` | Maximum tool calls per tool per 60-second window. Increase for high-throughput automation, decrease for cost control. |
| `TURBO_AGENT_AUDIT_LOG` | `~/.turbo/agent-audit.jsonl` | Path to the audit log file. Directory is created automatically. |
| `TURBO_AGENT_SMART_MODEL` | `sonnet` | Model used for triager, planner, and worker subagents. |
| `TURBO_AGENT_FAST_MODEL` | `haiku` | Model used for reporter subagent. |

### Example Configurations

**Local development:**

```bash
export TURBO_API_URL=http://localhost:8001/api/v1
export ANTHROPIC_API_KEY=sk-ant-...
# No scope restriction, default rate limits
turbo-agent "List all projects"
```

**Production with scope restriction:**

```bash
export TURBO_API_URL=https://turbo-plan.fly.dev/api/v1
export TURBO_API_KEY=your-api-key
export ANTHROPIC_API_KEY=sk-ant-...
export TURBO_ALLOWED_PROJECT_IDS=proj-abc-123,proj-def-456
export TURBO_AGENT_RATE_LIMIT=20
turbo-agent -p proj-abc-123 "Generate a status report"
```

**Cost-sensitive testing:**

```bash
export TURBO_AGENT_SMART_MODEL=haiku
export TURBO_AGENT_FAST_MODEL=haiku
turbo-agent --max-budget 0.50 --max-turns 5 "Quick triage of open issues"
```

---

## Audit Log

### Location

Default: `~/.turbo/agent-audit.jsonl`

Override with `TURBO_AGENT_AUDIT_LOG`.

### Format

One JSON object per line. Two event types:

**tool_call** — emitted before tool execution:

```json
{
  "event": "tool_call",
  "tool": "mcp__turbo__create_issue",
  "tool_use_id": "toolu_01ABC123",
  "input_hash": "a1b2c3d4e5f6g7h8",
  "input_summary": {
    "project_id": "proj-abc",
    "title": "Add authentication"
  },
  "timestamp": "2026-02-24T10:30:00.123456+00:00"
}
```

**tool_result** — emitted after tool execution:

```json
{
  "event": "tool_result",
  "tool": "mcp__turbo__create_issue",
  "tool_use_id": "toolu_01ABC123",
  "is_error": false,
  "timestamp": "2026-02-24T10:30:01.456789+00:00"
}
```

### Rotation

- Max file size: 10 MB
- Backups kept: 5
- Naming: `agent-audit.jsonl`, `agent-audit.jsonl.1`, ..., `agent-audit.jsonl.5`
- Rotation is handled by Python's `RotatingFileHandler`

### Querying

```bash
# All tool calls in the last hour
jq 'select(.event == "tool_call")' ~/.turbo/agent-audit.jsonl

# All errors
jq 'select(.is_error == true)' ~/.turbo/agent-audit.jsonl

# Calls to a specific tool
jq 'select(.tool == "mcp__turbo__create_issue")' ~/.turbo/agent-audit.jsonl

# Correlate call + result by tool_use_id
jq 'select(.tool_use_id == "toolu_01ABC123")' ~/.turbo/agent-audit.jsonl

# Count calls per tool
jq -r 'select(.event == "tool_call") | .tool' ~/.turbo/agent-audit.jsonl | sort | uniq -c | sort -rn
```

### Input Hash

Each `tool_call` entry includes an `input_hash` — the first 16 characters of a SHA-256 hash of the canonicalized input (keys sorted, values stringified). This allows you to detect if audit log entries were tampered with by recomputing the hash from known inputs.

---

## Cost Monitoring

### Budget Controls

The agent enforces a cost ceiling set via `--max-budget` (CLI) or `max_budget_usd` (Python):

```bash
turbo-agent --max-budget 1.0 "Triage all issues"
```

The Agent SDK will stop execution when the budget is exceeded.

### Budget Warnings

At 80% of budget, the agent logs a warning:

```json
{"level": "WARNING", "message": "Cost $0.82 exceeds 80% of budget $1.00"}
```

### Cost Tracking in Logs

Every completed run logs its final cost:

```json
{"level": "INFO", "message": "Run complete (cost=$0.19, turns=3)"}
```

### Cost Reduction Strategies

1. **Use cheaper models.** Set `TURBO_AGENT_SMART_MODEL=haiku` for development.
2. **Limit turns.** `--max-turns 5` prevents long reasoning chains.
3. **Scope narrowly.** `--project` limits the data the agent reads, reducing context.
4. **Use one-shot mode.** Multi-turn sessions accumulate context across messages.

---

## Structured Logging

### Configuration

```python
from turbo.agent.logging import configure_agent_logging

# JSON output (production)
configure_agent_logging(level="INFO", json_output=True)

# Plain text (development)
configure_agent_logging(level="DEBUG", json_output=False)
```

The CLI configures logging automatically:
- Default: `WARNING` level, JSON format
- With `--verbose`: `DEBUG` level, plain text format

### Log Levels

| Level | What's logged |
|-------|---------------|
| `DEBUG` | Tool inputs/outputs, HTTP request details |
| `INFO` | Agent init, run start/complete, session events, cost summary |
| `WARNING` | Rate limit hits, retry attempts, budget warnings, scope denials |
| `ERROR` | Unexpected exceptions, circuit breaker open |

### JSON Format

```json
{
  "timestamp": "2026-02-24T10:30:00.123456+00:00",
  "level": "INFO",
  "logger": "turbo.agent.client",
  "message": "Run complete (cost=$0.19, turns=3)"
}
```

Optional contextual fields appear when set on the log record: `agent_id`, `session_id`, `project_id`, `tool_name`, `cost_usd`.

Error entries include `error` and `error_type` fields.

---

## Troubleshooting

### Circuit Breaker Open

**Symptom:** All tool calls fail immediately with `Circuit breaker open. API calls paused for Xs.`

**Cause:** 5 consecutive HTTP failures (timeouts, 5xx errors, connection refused).

**Fix:**
1. Check if the Turbo API is running: `curl http://localhost:8001/api/v1/projects/`
2. If API is down, start it: `uvicorn turbo.main:app --port 8001`
3. The circuit breaker auto-recovers after 30 seconds. One successful request resets it.

### Rate Limit Hit

**Symptom:** Tool calls denied with `Rate limit exceeded: {tool} called N times in the last minute (max 30).`

**Cause:** Agent is calling the same tool too frequently (often a loop).

**Fix:**
- If expected (high-throughput automation): increase `TURBO_AGENT_RATE_LIMIT`
- If unexpected (agent looping): reduce `--max-turns` or check the agent's prompt for unclear instructions

### Scope Denial

**Symptom:** Tool calls denied with `Project {id} is not in the allowed scope.`

**Cause:** `TURBO_ALLOWED_PROJECT_IDS` is set and the tool call targets a different project.

**Fix:**
- Verify the project ID: `echo $TURBO_ALLOWED_PROJECT_IDS`
- Add the needed project: `export TURBO_ALLOWED_PROJECT_IDS=proj-1,proj-2`
- Remove restriction entirely: `unset TURBO_ALLOWED_PROJECT_IDS`

**For issue-scoped tools** (get_issue, update_issue, etc.): The hook resolves the issue's project_id via the API. If the API is unreachable during resolution, the call is denied with `Cannot verify project scope for issue {id}. Access denied for safety.` Fix: ensure the API is running.

### Scope Denial for Issue-Based Tools

**Symptom:** `Cannot verify project scope for issue {id}. Access denied for safety.`

**Cause:** The scope hook tried to look up which project an issue belongs to (via `GET /issues/{id}`) but the API call failed.

**Fix:**
1. Check API connectivity
2. Verify the issue ID exists: `curl http://localhost:8001/api/v1/issues/{id}/`
3. The issue→project mapping is cached after first successful resolution

### ProcessTransport Errors

**Symptom:** `ProcessTransport is not ready for writing` or similar errors from the Agent SDK.

**Cause:** Claude Agent SDK bug (#386) with string prompts and in-process MCP servers.

**Status:** Worked around in `client.py` via `_wrap_prompt()`. If you see this error, it means `_wrap_prompt()` was bypassed (e.g., calling `query()` directly with a string prompt).

### Import Errors

**Symptom:** `ModuleNotFoundError: No module named 'claude_agent_sdk'`

**Fix:** Install the agent extras: `pip install -e ".[agent]"`

### Test Failures

**Running tests:**

```bash
# From the project root
.venv/bin/python -m pytest tests/agent/ -v \
    --override-ini="asyncio_mode=auto" \
    --rootdir=tests/agent \
    -c /dev/null

# With coverage
.venv/bin/python -m pytest tests/agent/ -v \
    --override-ini="asyncio_mode=auto" \
    --rootdir=tests/agent \
    -c /dev/null \
    --cov=turbo/agent \
    --cov-report=term-missing
```

**Why `--rootdir=tests/agent -c /dev/null`?** The root `tests/conftest.py` imports `turbo.core.database` which triggers a Pydantic v1/v2 conflict in `turbo/core/schemas/podcast.py`. Isolating the rootdir prevents the root conftest from loading.

**Common test issues:**

- `SdkMcpTool object is not callable`: Use `.handler` attribute to call tool functions in tests (e.g., `await list_projects.handler({})`)
- `MagicMock comparison error`: When mocking ResultMessage, set numeric attributes explicitly (`mock.total_cost_usd = 0.05`) — MagicMock auto-creates attributes as MagicMock objects that can't compare with `>`

---

## Deployment Checklist

Before deploying an agent to production:

- [ ] Set `TURBO_API_URL` to production API
- [ ] Set `TURBO_API_KEY` with a valid token
- [ ] Set `ANTHROPIC_API_KEY` with sufficient credits
- [ ] Set `TURBO_ALLOWED_PROJECT_IDS` to restrict scope
- [ ] Set `TURBO_AGENT_RATE_LIMIT` appropriately
- [ ] Set `TURBO_AGENT_AUDIT_LOG` to a persistent path
- [ ] Configure `--max-budget` to prevent cost overruns
- [ ] Configure `--max-turns` to prevent infinite loops
- [ ] Verify API connectivity: `curl $TURBO_API_URL/projects/`
- [ ] Run the test suite to verify installation

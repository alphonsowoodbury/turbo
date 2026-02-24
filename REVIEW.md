# Senior Principal Code Review — turbo-plan

**Date:** 2026-02-24
**Scope:** Full repository audit — security, code quality, test coverage, architecture
**Codebase:** ~56,000 LOC Python, 66 tables, 48 API endpoints, 4,699-line MCP server

---

## Critical — Fix Before Anything Else

### C1. Zero Authentication on the Public API

Every endpoint on `turbo-plan.fly.dev` is wide open. No JWT, no API key, no session cookies, no auth middleware. Anyone who finds the URL can read, create, update, and delete all data — projects, issues, resumes, job applications, network contacts.

**Files:** `turbo/main.py`, `turbo/api/v1/__init__.py`, all endpoint files
**CWE:** CWE-306 (Missing Authentication for Critical Function)

```python
# turbo/main.py — no auth dependency anywhere
app.include_router(api_router)
```

**Fix:** Add authentication middleware (API key at minimum, JWT for proper auth). Require it on all non-health-check endpoints.

---

### C2. Raw Anthropic API Key Endpoint Exposed

`GET /api/v1/settings/claude/api-key/raw` returns the unmasked Anthropic API key. The comment says "should only be accessible from internal Docker network" but there is no enforcement. It runs on the same public FastAPI server.

**File:** `turbo/api/v1/endpoints/settings.py:255-278`
**CWE:** CWE-200 (Exposure of Sensitive Information)

```python
@router.get("/claude/api-key/raw")
async def get_claude_api_key_raw(db):
    # WARNING: This endpoint should only be accessible from internal Docker network.
    return {"api_key": setting.value.get("api_key")}
```

**Fix:** Remove this endpoint entirely. If internal services need the key, pass it via environment variable.

---

### C3. Terminal Endpoint = Remote Shell for Anyone

`POST /api/v1/terminal/sessions` spawns a PTY shell. Combined with C1 (no auth), anyone gets remote code execution on the Fly.io instance. The `working_directory` and `environment_vars` are user-controlled with no validation.

**File:** `turbo/api/v1/endpoints/terminal.py:32-41, 62-68`
**CWE:** CWE-78 (OS Command Injection)

```python
pty = ptyprocess.PtyProcess.spawn(
    shell_args,
    dimensions=(24, 80),
    cwd=working_dir,   # user-controlled
    env=env,           # user-controlled
)
```

**Fix:** Disable this endpoint in production. If needed, gate behind strong auth + IP allowlist.

---

### C4. Hardcoded Credentials Committed to Git

9+ hardcoded credentials in tracked files:

| File | Credential |
|------|-----------|
| `docker-compose.yml:11` | `POSTGRES_PASSWORD: turbo_password` |
| `docker-compose.yml:12` | `POSTGRES_HOST_AUTH_METHOD: trust` |
| `docker-compose.yml:35` | Full database URL with password |
| `docker-compose.yml:38` | `turbo_graph_password` |
| `docker-compose.yml:124` | Neo4j auth `neo4j/turbo_graph_password` |
| `docker-compose.yml:175` | `turbo_test_password` |
| `docker-compose.yml:192-194` | pgAdmin `admin@admin.com` / `admin` |
| `docker-compose.yml:219` | `turbo-webhook-secret-change-me` |
| `turbo/utils/config.py:75` | `secret_key = "dev-secret-key-change-in-production"` |
| `turbo/utils/config.py:117` | `password = "turbo_graph_password"` |

**CWE:** CWE-798 (Use of Hard-coded Credentials)

**Fix:** Move all credentials to `.env` files (already gitignored). Remove defaults for secrets in `config.py` — fail on startup if not set in production.

---

## High — Significant Technical Debt

### H1. MCP Server Has Zero Tests

4,699 lines of code, 130+ tool handlers, 0 tests. This is the primary interface for Claude Code interactions. Any regression ships silently.

**File:** `turbo/mcp_server.py`
**Gap:** ~50-100 tests needed

**Fix:** Create `tests/mcp/test_mcp_server.py` with tool handler tests, schema validation, error case coverage.

---

### H2. SSRF via Webhook URL

The webhook service POSTs to user-supplied URLs with no restriction on the target. An attacker can set a webhook URL to `http://169.254.169.254/` and read cloud metadata, or target internal services.

**File:** `turbo/core/services/webhook_service.py:147`
**CWE:** CWE-918 (Server-Side Request Forgery)

```python
response = await client.post(
    webhook.url,  # user-controlled, no validation
    content=payload_json,
    headers=headers,
)
```

**Fix:** Block requests to private IP ranges (10.x, 172.16-31.x, 192.168.x, 127.x, 169.254.x) and Docker internal DNS names.

---

### H3. Path Traversal in MCP Server

`load_document` reads any file the process can access. No path validation, no sandboxing. Same issue with `upload_resume`.

**File:** `turbo/mcp_server.py:3592-3612`
**CWE:** CWE-22 (Path Traversal)

```python
file_path = Path(arguments["file_path"])
content = loader.load(file_path)  # reads anything
```

**Fix:** Restrict file access to a configured allowed directory. Resolve symlinks and reject paths containing `..`.

---

### H4. No Rate Limiting on API

The agent module has rate limiting via hooks. The actual API serving the internet has none.

**File:** `turbo/main.py`
**CWE:** CWE-770 (Allocation of Resources Without Limits)

**Fix:** Add rate limiting middleware (`slowapi` or custom). Prioritize write endpoints, AI execution, and terminal.

---

### H5. Error Messages Leak Internal Details

30+ endpoints pass raw exception messages to HTTP responses via `detail=str(e)`. The MCP server includes full `traceback.format_exc()` in responses.

**Files:** Multiple across `turbo/api/v1/endpoints/`
**CWE:** CWE-209 (Error Message Containing Sensitive Information)

Examples:
- `terminal.py:41` — `detail=str(e)` on 500
- `ai.py:82` — `detail=str(e)` on 500
- `documents.py:207` — `detail=f"Export failed: {e!s}"`
- `worktrees.py:167` — `detail=f"Failed to delete worktree: {e.stderr.decode()}"` (leaks subprocess stderr)
- `mcp_server.py:3704-3708` — full `traceback.format_exc()` in response

**Fix:** Return generic error messages to clients. Log detailed errors server-side only.

---

### H6. Inconsistent Error Handling Across Codebase

Three distinct problems:

**Problem 1 — `print()` instead of `logging` in 8+ job scraper files:**
- `reed_scraper.py`, `jsearch_scraper.py`, `arbeitnow_scraper.py`, `remotive_scraper.py`
- `usajobs_scraper.py`, `adzuna_scraper.py`, `weworkremotely_scraper.py`, `themuse_scraper.py`

**Problem 2 — Bare `except Exception: pass` hiding bugs:**
- `resume.py` — silently skips AI extraction failures
- Multiple job scrapers — swallow all errors

**Problem 3 — `print()` in terminal.py:**
- 20+ print statements for connection state, received messages, PTY data

**Fix:** Replace all `print()` with `logging`. Replace bare `except: pass` with specific exception types and logging.

---

## Medium — Code Quality & Consistency

### M1. Duplicate File Committed

`turbo/core/schemas/tag 2.py` — a space-in-filename duplicate of `tag.py` with older Pydantic syntax.

**Fix:** Delete `tag 2.py`.

---

### M2. Mixed Pydantic Patterns

Older schemas:
```python
class Config:
    from_attributes = True
```

Newer schemas:
```python
model_config = ConfigDict(from_attributes=True)
```

Mixed `Optional[str]` (old) and `str | None` (new) type annotations.

**Fix:** Migrate all schemas to `ConfigDict` and `str | None` syntax.

---

### M3. Inconsistent Transaction Management

Some endpoints call `await db.commit()` directly. Others delegate to the service layer. Some do both. This creates confusion about who owns the transaction and risks double-commits or missed commits.

**Fix:** Pick one pattern (service layer owns transactions) and enforce it. Remove `db.commit()` from endpoint code.

---

### M4. 9 TODO/FIXME Items in Production Code

| File | TODO |
|------|------|
| `resume_generation.py` | Implement DOCX conversion |
| `resume_tailoring.py` | Replace with AI/Claude-powered generation |
| `action_executor.py` | Implement subagent blocking/allowlist system |
| `mention_detector.py` | Trigger webhook to generate staff response |
| `resume.py` | Add count method to repository |
| `staff.py` | Calculate response_rate based on review requests |
| `staff.py` | Query issues assigned to this staff |
| `staff.py` | Query pending action approvals |
| `staff.py` | Check if entity is assigned to this staff |

**Fix:** Complete, remove, or convert to tracked issues.

---

### M5. Abstract Methods Without ABC

`turbo/core/services/job_scrapers/base_scraper.py` uses `pass` instead of `@abstractmethod`. Subclasses can silently skip required method implementations.

```python
def _get_source_name(self) -> str:
    pass  # should be raise NotImplementedError or @abstractmethod
```

**Fix:** Add `ABC` base class and `@abstractmethod` decorators.

---

### M6. Streamlit Still in Core Dependencies

`streamlit>=1.28.0` is listed as a core dependency but the frontend is Next.js. Dead dependency adding install weight and attack surface.

**Fix:** Remove from core dependencies. If needed for legacy, move to optional extras.

---

### M7. API Docs Exposed in Production

Swagger UI (`/api/docs`) and ReDoc (`/api/redoc`) are enabled unconditionally, giving attackers a complete endpoint map.

**File:** `turbo/main.py:22-23`

**Fix:** Set `docs_url=None` and `redoc_url=None` when `environment == "production"`.

---

### M8. CORS Too Permissive

```python
CORSMiddleware(
    allow_origins=settings.security.cors_origins,  # restricted — good
    allow_credentials=True,
    allow_methods=["*"],   # too broad
    allow_headers=["*"],   # too broad
)
```

**Fix:** Restrict to actually used methods (GET, POST, PUT, DELETE, PATCH) and actually needed headers.

---

### M9. No Upload Size Limits

`upload_document_file` reads entire files into memory with `await file.read()` with no size check. Memory exhaustion via large uploads.

**File:** `turbo/api/v1/endpoints/documents.py:305`

**Fix:** Add `max_upload_size` check before reading file content.

---

### M10. WebSocket Endpoints Lack Authentication

WebSocket endpoints accept connections without any token or authentication check.

**File:** `turbo/api/v1/endpoints/websocket.py:13-17`

**Fix:** Require a valid token (query parameter or initial handshake message) before accepting upgrades.

---

## Low — Cleanup Items

### L1. Dependencies Use Minimum Version Pins Only

All dependencies use `>=` with no upper bounds. No lockfile for reproducible builds. `python-jose` has had past CVEs.

**Fix:** Pin exact versions or use `~=` for production. Run `pip-audit` periodically.

---

### L2. Bandit Checks Partially Disabled

`pyproject.toml` skips `B601`. Multiple `# noqa: S105` suppress password-in-code warnings.

**Fix:** Re-enable and fix the underlying issues.

---

### L3. Debug Mode Configurable via Environment

`debug` defaults to `False` but can be toggled. Passes to FastAPI which enables detailed error pages.

**Fix:** Force `debug=False` in production regardless of env var.

---

### L4. 18 Empty Schema Classes

```python
class SkillCreate(SkillBase):
    pass
```

Valid Python, but noisy. No custom validation or fields added.

**Fix:** Low priority. Keep if intentional for future extension.

---

### L5. Empty e2e/ Test Directory

Created but contains no tests.

**Fix:** Either add e2e tests or remove the directory.

---

### L6. No Startup Validation for Required Environment Variables

If `ANTHROPIC_API_KEY` or other required vars are missing, the app starts but fails at runtime.

**Fix:** Add startup checks that fail fast with clear error messages.

---

## Summary Table

| ID | Severity | Issue | Status |
|----|----------|-------|--------|
| C1 | Critical | No authentication on any API endpoint | FIXED |
| C2 | Critical | Raw API key endpoint exposed publicly | FIXED |
| C3 | Critical | Terminal endpoint = unauthenticated RCE | FIXED |
| C4 | Critical | 9+ hardcoded credentials in git | FIXED |
| H1 | High | MCP server has 0 tests (4,699 LOC) | OPEN |
| H2 | High | SSRF via webhook URLs | FIXED |
| H3 | High | Path traversal in MCP file operations | FIXED |
| H4 | High | No rate limiting on API | FIXED |
| H5 | High | Error messages leak internals (30+ endpoints) | FIXED |
| H6 | High | Inconsistent error handling / print() in prod | FIXED |
| M1 | Medium | Duplicate schema file `tag 2.py` | FIXED |
| M2 | Medium | Mixed Pydantic v1/v2 patterns | FIXED |
| M3 | Medium | Inconsistent transaction management | OPEN |
| M4 | Medium | 9 TODO items in production code | OPEN |
| M5 | Medium | Abstract methods without ABC | N/A (already had ABC) |
| M6 | Medium | Streamlit in core deps (unused) | FIXED |
| M7 | Medium | API docs exposed in production | FIXED |
| M8 | Medium | CORS methods/headers too permissive | FIXED |
| M9 | Medium | No upload size limits | FIXED |
| M10 | Medium | WebSocket endpoints lack auth | FIXED |
| L1 | Low | No dependency pinning / lockfile | OPEN |
| L2 | Low | Bandit checks suppressed | WONTFIX (legitimate subprocess use) |
| L3 | Low | Debug mode configurable in prod | FIXED |
| L4 | Low | 18 empty pass-only schema classes | WONTFIX (intentional for extension) |
| L5 | Low | Empty e2e/ test directory | FIXED |
| L6 | Low | No startup env var validation | FIXED |

**Score: 21/26 resolved (4 Critical, 5 High, 8 Medium, 4 Low)**

### Remaining Items
- **H1** — MCP server test suite (large effort, separate initiative)
- **M3** — Transaction management centralization (architectural refactor)
- **M4** — 9 TODO items (feature work, convert to tracked issues)
- **L1** — Dependency pinning (generate lockfile)

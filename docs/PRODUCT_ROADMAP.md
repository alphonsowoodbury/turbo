# Turbo Plan — Product Roadmap

**Last updated:** 2026-02-25
**Author:** Alphonso Woodbury
**Status:** Draft — living document

---

## 1. What Turbo Plan Is

Turbo Plan is the control plane for Claude Code.

You write code with Claude Code in the terminal. Turbo Plan is the web UI where you see what it's doing, manage work, set guardrails, and approve actions. Both hit the same hosted API.

```
┌──────────────────────────┐     ┌──────────────────────────┐
│  Web UI (browser)         │     │  Claude Code (terminal)   │
│  See work, set guardrails │     │  Write code, run agents   │
│  Approve, review, plan    │     │  Triage, create issues    │
└───────────┬──────────────┘     └───────────┬──────────────┘
            │ HTTPS                           │ MCP tools
            ▼                                 ▼
         ┌─────────────────────────────────────┐
         │  Turbo Plan API (hosted)             │
         │  Single source of truth              │
         └─────────────────────────────────────┘
```

**That's it.** No Cursor support. No generic MCP marketplace. No "works with any AI." Turbo Plan + Claude Code. Opinionated.

### Why This Matters

Claude Code is powerful but blind. It doesn't know what you're working on across projects. It doesn't remember what it did yesterday. It can't show you a dashboard of agent activity. It has no approval workflow, no guardrails UI, no audit trail.

Turbo Plan gives Claude Code:
- **Memory** — persistent issues, projects, milestones, decisions across sessions
- **Structure** — prioritized work queue, ranked issues, project scoping
- **Visibility** — real-time control room showing what agents are doing
- **Guardrails** — approval gates, tool restrictions, budget limits, audit logging

---

## 2. Architecture

### Deployed Now

| Component | Where | What |
|-----------|-------|------|
| **API** | `turbo-plan.fly.dev` | FastAPI, 204 routes, PostgreSQL |
| **Web UI** | `turbo-plan-web.fly.dev` | Next.js 15, React 19, 23 pages |
| **MCP Server** | Local (Claude Code) | ~100 tools, talks to hosted API |
| **Agent Module** | Local or server-side | 4 subagents via Claude Agent SDK |

### How It Works

1. **You** open the web UI in a browser. Nothing to install.
2. **Claude Code** connects to the API via MCP tools.
3. Both see the same data. You manage work in the UI. Claude Code executes it.
4. Agent actions flow through the API and appear in the UI in real-time.

### Data Model

```
Core PM (11 models)          AI/Agents (10 models)
  Project                      Staff (domain experts)
  Issue                        StaffConversation
  Milestone                    Mentor
  Initiative                   MentorConversation
  Decision                     GroupDiscussion
  WorkLog                      Agent
  Comment (polymorphic)        AgentSession
  SavedFilter                  ConversationMemory
  Favorite                     ConversationSummary
  ProjectEntityCounter         ReviewRequest
  TerminalSession

Content (6 models)           Infrastructure (6 models)
  Document                     Setting
  Blueprint                    Webhook, WebhookDelivery
  Note                         ActionApproval
  Literature                   CalendarEvent
  Form, FormResponse           ScriptRun
```

43 models, 204 API routes, ~100 MCP tools.

---

## 3. Phased Roadmap

### Phase 0: Solo Dev Polish — COMPLETE

**Goal:** Make Turbo a working daily-driver for one developer.

| Item | Status | Commit |
|------|--------|--------|
| Mount dormant endpoints (7 → 26 routers, 204 routes) | Done | `a9aa35f` |
| Add sorting to all 11 list endpoints | Done | `953a263` |
| Wire tags page to real API | Done | `953a263` |
| Fix TypeScript errors (283 → 100) + track frontend/lib | Done | `8ef91f1` |
| Error boundary, loading state, 404 page | Done | `aa214f3` |

---

### Phase 1: The Product

**Goal:** Three UI experiences that make Turbo Plan worth opening every day.

#### 1.1 The Board

Kanban + list view for issues. This is where you plan and track work.

**Views:**
- **Kanban** — Columns by status. Drag-and-drop. Swimlanes by priority or project.
- **List** — Dense table with inline editing. Sort by any column. Bulk actions.

**Key features:**
- Saved views (filter + sort + grouping persisted)
- Quick filters (my issues, blocked, unassigned, agent-created)
- Keyboard navigation (j/k, enter, / to search)
- Inline editing (click status/priority/assignee to change)
- Visual indicator when an issue was created or modified by Claude Code

**Data requirements:**
- Sorting (done in Phase 0.2)
- Cursor-based pagination for large lists
- WebSocket push when agents modify issues

#### 1.2 The Control Room

Real-time visibility into what Claude Code agents are doing. This is the differentiator.

**Layout:**
- **Activity stream** — Live feed: "Triager analyzed 5 issues", "Worker started TURBO-42"
- **Active sessions** — Running agent cards: current tool call, tokens used, cost, elapsed time
- **Stats** — Today's agent runs, total cost, issues created/closed by agents

**Key features:**
- Click any session → full tool call timeline
- Cost tracking per session and per day
- Historical view (filter by date, agent type, project)

**Data:** AgentSession model exists. Needs tool call history enrichment and cost tracking.

#### 1.3 The Guardrails Panel

Configuration UI for Claude Code agent permissions. This is the enterprise sell even at solo-dev stage.

**Sections:**
- **Agent config** — Which subagents enabled, per-agent tool allowlists, budget/turn limits
- **Project scoping** — Which projects each agent can access
- **Approval rules** — Which actions require human approval, auto-approve rules, timeout
- **Audit viewer** — Searchable audit log of all agent actions

**Data:** Hook system exists (5 types). Needs UI to configure rather than env vars.

#### 1.4 Claude Code Integration Tightening

- **Agent tokens** — Scoped API tokens for MCP server (project-limited, time-limited)
- **Real-time sync** — WebSocket push so UI updates instantly when Claude Code acts
- **Approval flow** — Claude Code requests approval → notification in UI → approve/deny → Claude Code continues
- **Session linking** — Link Claude Code terminal sessions to Turbo Plan agent sessions

---

### Phase 2: Auth & Foundation

**Goal:** The plumbing needed before anyone else can use it.

#### 2.1 User Model

```
User
  id, email, name, avatar_url
  auth_provider: github | google
  auth_provider_id: str

Organization
  id, name, slug
  plan: free | pro

OrganizationMember
  org_id, user_id, role: owner | admin | member | viewer
```

Every existing model gets `org_id` with NOT NULL after migration.

#### 2.2 JWT Authentication

- OAuth (GitHub/Google) → JWT access token (15 min) + refresh token (7 days)
- API: `Authorization: Bearer <jwt>` with user_id and org_id in claims
- MCP: Scoped token passed via MCP server config
- Keep API key fallback for local dev

#### 2.3 Row-Level Tenant Isolation

```python
class TenantRepository(BaseRepository[T]):
    def _base_query(self):
        return select(self._model).where(self._model.org_id == self._current_org_id)
```

No query returns data from another org. Enforced at repository layer.

#### 2.4 Audit Trail

```
AuditLog
  org_id, user_id, agent_session_id (nullable)
  action: create | update | delete | agent_tool_call | ...
  entity_type, entity_id
  changes: JSON (before/after diff)
  timestamp
```

Auto-populated via service decorator. No manual logging.

---

### Phase 3: Teams

**Goal:** Multiple developers sharing a workspace with Claude Code as AI teammate.

- Invite flow, member management, roles
- Assignment (issues/milestones to specific users)
- @mentions in comments with notifications
- Agent appears in team list with "AI" badge
- Assign issues to agents → triggers autonomous work
- "What happened while I was away" AI summary
- In-app + email notifications

---

### Phase 4: Enterprise

**Goal:** Features for enterprise sales.

- SSO/SAML (Okta, Azure AD)
- SCIM provisioning
- Custom roles, per-project permissions
- SOC2-ready audit logging
- Data retention policies, GDPR export/deletion
- Admin console with cost allocation and usage quotas

---

## 4. Technical Debt

| # | Item | Phase | Status |
|---|------|-------|--------|
| 1 | Mount dormant endpoints | 0 | Done |
| 2 | Add sorting to list endpoints | 0 | Done |
| 3 | Fix TypeScript build errors | 0 | 100 remaining |
| 4 | Track frontend/lib in git | 0 | Done |
| 5 | Error boundaries | 0 | Done |
| 6 | Cursor-based pagination | 1 | — |
| 7 | Full-text search (tsvector) | 1 | — |
| 8 | Agent module tests (0% coverage) | 1 | — |
| 9 | Frontend tests (0% coverage) | 2 | — |
| 10 | Centralize transaction management | 2 | — |

---

## 5. Competitive Positioning

| Feature | Jira | Linear | Turbo Plan |
|---------|------|--------|------------|
| Issue tracking | Deep | Clean | Deep + AI-aware |
| AI agents | Bolt-on chatbot | None | First-class team members |
| Agent guardrails | None | None | Per-agent/project config |
| Agent visibility | None | None | Real-time control room |
| Approval gates | None | None | Human-in-the-loop |
| Claude Code integration | None | None | Native MCP + scoped tokens |
| Self-hosted option | Expensive | No | Docker Compose |

**Turbo Plan's wedge:** The only PM tool built specifically as a control plane for Claude Code.

---

## 6. Decisions Made

| Decision | Choice | Date | Rationale |
|----------|--------|------|-----------|
| AI integration scope | Claude Code only | 2026-02-25 | Opinionated > generic. One integration done well beats five done poorly. |
| Career features | Removed | 2026-02-24 | Not PM. 13 models, ~14K LOC removed. |
| Deployment model | Hosted SaaS | 2026-02-25 | Users access web UI via browser. Nothing to install. |
| MCP server | Local, connects to hosted API | 2026-02-25 | Claude Code runs locally, needs local MCP. API is the bridge. |

---

## 7. Open Questions

1. **Pricing:** Per-seat? Per-agent-run? Free tier + paid for teams?
2. **Self-hosted:** Offer alongside cloud for enterprise? Docker Compose already works.
3. **Mobile:** PWA sufficient or invest in native later?
4. **Open source:** Core open source with enterprise paid? Fully proprietary?

---

*This is a living document. Updated as decisions are made and phases complete.*

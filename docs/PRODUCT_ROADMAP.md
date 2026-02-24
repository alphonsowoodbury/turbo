# Turbo — Product Roadmap

**Last updated:** 2026-02-24
**Author:** Alphonso Woodbury
**Status:** Draft — living document

---

## 1. What Turbo Is

Turbo is an AI-native project management platform. It combines Jira-level issue tracking with autonomous AI agents that operate within configurable guardrails.

**The gap it fills:** Jira has 20 years of project management features and zero AI integration. Claude Code and Cursor have powerful AI but zero project management. Turbo is the bridge — structured PM workflows where AI agents are first-class participants, not bolt-on copilots.

**Core thesis:** Teams adopting AI for software development need two things existing tools don't provide:
1. **Visibility** — What are AI agents doing right now? What did they change? What did they decide?
2. **Control** — Which projects can they touch? What tools can they use? What requires human approval?

---

## 2. Target Users

| Tier | Who | What They Need | When |
|------|-----|---------------|------|
| **Solo Dev** | Independent developer managing multiple projects with AI assistance | Force multiplier — 4 AI subagents acting as a team, guardrails they don't know they need, visibility into AI work | Now (Phase 0-1) |
| **Small Team** | 2-10 developers using AI agents alongside human teammates | Shared workspace, role-based access, audit trail, agent activity dashboard | Phase 2-3 |
| **Enterprise** | 50+ seat engineering org with compliance requirements | SSO/SAML, tenant isolation, SOC2-ready audit logging, admin controls, SLA | Phase 4-5 |

---

## 3. Current State

### What Exists and Works

| Component | Status | Detail |
|-----------|--------|--------|
| **Data models** | 43 models, 141 schemas, 20 M2M tables | Rich entity graph with polymorphic assignment, tagging, dependencies |
| **API** | 338 routes built, 7 routers mounted | Core PM endpoints active. 40 endpoint files dormant but implemented. |
| **MCP Server** | 154 tools | Full coverage of all models. Production-grade. Primary daily interface. |
| **Agent SDK** | 4 subagents | Triager, Planner, Reporter, Worker with least-privilege tool access |
| **Guardrails** | 5 hook types | Project scoping, destructive command blocking, rate limiting, audit logging |
| **Frontend** | 23 complete pages, 108 components | Next.js 15, React 19, Tailwind v4, Radix UI. 85% feature-complete. |
| **Auth** | NextAuth (GitHub/Google OAuth) + API key middleware | Functional but single-tenant. No RBAC enforcement. |
| **Real-time** | 2 WebSocket channels | Comment updates + agent activity feed |
| **Docs site** | Astro/Starlight | Deployed on Fly.io. Quick-start and API reference. |
| **Infrastructure** | Docker Compose (10 services) + Fly.io (3 apps) | PostgreSQL, Neo4j, Redis, Ollama, Claude webhook, docs watcher |

### Model Domains

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

Content (9 models)           Career (13 models)
  Document                     Resume, ResumeSection
  Blueprint                    Company, JobApplication
  Note                         JobPosting, SearchCriteria
  Literature                   JobSearchHistory, JobPostingMatch
  PodcastShow                  WorkExperience, AchievementFact
  PodcastEpisode               NetworkContact, Skill
  Form, FormResponse
  FormResponseAudit

Infrastructure (5 models)
  Setting
  Webhook, WebhookDelivery
  ActionApproval
  CalendarEvent, ScriptRun
```

### What's Missing

| Gap | Impact | Blocks |
|-----|--------|--------|
| Multi-tenancy (zero) | Can't have multiple users without seeing each other's data | Teams, Enterprise |
| RBAC enforcement | Roles defined on Staff model but never checked at API boundary | Teams, Enterprise |
| Audit trail | No created_by/updated_by, no change history | Enterprise compliance |
| Sorting on API | No sort parameter on any list endpoint | Frontend polish |
| Full-text search | ILIKE pattern matching only, no PostgreSQL tsvector | Product quality |
| Frontend tests | Zero | Product quality |
| Backend coverage | ~60% (agent module at 0%) | Product quality |

---

## 4. Architecture

### Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Fly.io                                │
│                                                              │
│  turbo-plan.fly.dev          turbo-plan-web.fly.dev          │
│  ┌──────────────┐            ┌──────────────────┐            │
│  │  FastAPI API  │◄──REST───►│  Next.js Frontend │            │
│  │  (338 routes) │           │  (23 pages)       │            │
│  └──────┬───────┘            └──────────────────┘            │
│         │                                                     │
│  ┌──────┴───────┐                                            │
│  │  PostgreSQL   │                                            │
│  │  (54 tables)  │                                            │
│  └──────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
         ▲
         │ MCP (stdio)
         │
┌────────┴────────┐
│   Claude Code    │──► Agent SDK (4 subagents)
│   (local CLI)    │──► 154 MCP tools
└─────────────────┘
```

### Target Architecture (Phase 3+)

```
┌───────────────────────────────────────────────────────────────────┐
│                           Fly.io                                   │
│                                                                    │
│  api.turbo.dev                    app.turbo.dev                    │
│  ┌────────────────────┐           ┌──────────────────────┐         │
│  │  FastAPI API        │◄──REST──►│  Next.js Frontend     │         │
│  │  + JWT auth         │           │  + RBAC-aware views   │         │
│  │  + tenant isolation │  ◄──WS──►│  + agent control room │         │
│  │  + audit middleware │           │  + guardrails panel   │         │
│  └────────┬───────────┘           └──────────────────────┘         │
│           │                                                        │
│  ┌────────┴───────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  PostgreSQL         │  │  Redis        │  │  Neo4j        │       │
│  │  + row-level tenant │  │  + sessions   │  │  + knowledge  │       │
│  │  + audit_log table  │  │  + rate limits │  │    graph      │       │
│  └────────────────────┘  └──────────────┘  └──────────────┘       │
│                                                                    │
│  ┌────────────────────┐  ┌──────────────────────┐                  │
│  │  Agent Worker       │  │  Webhook Service      │                  │
│  │  + scoped tokens    │  │  + SSRF protection    │                  │
│  │  + budget limits    │  │  + delivery tracking  │                  │
│  │  + audit logging    │  │  + HMAC signing       │                  │
│  └────────────────────┘  └──────────────────────┘                  │
└───────────────────────────────────────────────────────────────────┘
         ▲
         │ MCP (stdio) + scoped API tokens
         │
┌────────┴────────┐
│   Claude Code    │──► Agent SDK (N subagents, configurable)
│   (local CLI)    │──► Per-project tool access
└─────────────────┘
```

---

## 5. Phased Roadmap

### Phase 0: Solo Dev Polish (You Are Here)

**Goal:** Make Turbo a daily-driver product for a single power user managing multiple projects with AI agents.

**Duration:** 3-4 weeks

#### 0.1 Mount Dormant API Endpoints

40 endpoint files are fully implemented but not wired into the API router. Mount the ones needed for the frontend.

**Mount immediately (frontend needs these):**
- `agents.py` — Agent activity monitoring (frontend page exists)
- `staff.py` — Domain expert management (frontend page exists)
- `mentors.py` — Mentor conversations (frontend page exists)
- `notes.py` — Quick notes (frontend page exists)
- `work_queue.py` — Prioritized work queue (frontend page exists)
- `blueprints.py` — Architecture templates (frontend page exists)
- `settings.py` — App configuration (frontend page exists)
- `worktrees.py` — Git worktree management (frontend page exists)
- `scripts.py` — Script execution tracking (frontend page exists)
- `approvals.py` or `action_approvals.py` — AI action approvals (frontend page exists)
- `calendar.py` or `calendar_events.py` — Calendar (frontend page exists)
- `discoveries.py` — Research tracking (frontend page exists)
- `saved_filters.py` — Saved filter persistence (used by issues page)
- `favorites.py` — Bookmarking (used by sidebar)
- `forms.py` — Dynamic forms (used by issue detail tabs)

**Defer (career domain — separate product later):**
- `resumes.py`, `resume_generation.py`, `resume_tailoring.py`
- `job_search.py`, `job_postings.py`, `job_applications.py`
- `network_contacts.py`, `companies.py`, `work_experience.py`
- `skills.py`, `email_templates.py`

**Defer (infrastructure — not user-facing):**
- `webhooks.py` — Internal service communication
- `terminal.py` — Dev-only, security-gated
- `ai.py` — Direct AI invocation (agents handle this)
- `subagents.py` — Agent-to-agent (internal)
- `group_discussion.py` — Staff-only feature

#### 0.2 Add API Sorting

Every list endpoint currently returns unsorted results. Add `sort_by` and `sort_order` query parameters to all list endpoints.

**Priority endpoints:**
- `GET /issues` — sort by priority, updated_at, created_at, work_rank
- `GET /projects` — sort by name, updated_at, status
- `GET /documents` — sort by title, updated_at
- All other list endpoints — sort by updated_at default

#### 0.3 Frontend Fixes

- Wire tags page to real API (currently mock data)
- Complete mentor create dialog
- Fill in project detail placeholder tabs (or remove them)
- Fix TypeScript build errors (currently `ignoreBuildErrors: true`)
- Fix ESLint errors (currently `ignoreDuringBuilds: true`)

#### 0.4 Quality Baseline

- Enable TypeScript strict mode incrementally
- Fix all build warnings
- Add error boundaries to all pages
- Add loading skeletons to all data-fetching pages

---

### Phase 1: Foundation (Auth, Tenancy, Audit)

**Goal:** The architectural foundation that everything after this depends on. No user-visible features — all plumbing.

**Duration:** 4-6 weeks

#### 1.1 User and Organization Models

New models:

```
Organization
  id: UUID
  name: str
  slug: str (unique, URL-safe)
  plan: enum (free, pro, enterprise)
  created_at, updated_at

OrganizationMember
  id: UUID
  org_id: FK → Organization
  user_id: FK → User
  role: enum (owner, admin, member, viewer, agent)
  invited_at, accepted_at

User
  id: UUID
  email: str (unique)
  name: str
  avatar_url: str | None
  auth_provider: enum (github, google, email)
  auth_provider_id: str
  created_at, updated_at
```

Every existing model gets `org_id: FK → Organization` with a NOT NULL constraint after migration.

#### 1.2 JWT Authentication

Replace static API key with proper token auth:

- **Login flow:** OAuth (GitHub/Google) → JWT access token (15 min) + refresh token (7 days)
- **API auth:** `Authorization: Bearer <jwt>` with user_id and org_id in claims
- **Agent auth:** Scoped API tokens with explicit tool permissions and budget limits
- **MCP auth:** Token passed via MCP server config, scoped to org + project(s)

Keep API key middleware as fallback for backward compatibility (local dev, CI).

#### 1.3 Row-Level Tenant Isolation

All repository queries filter by `org_id` automatically:

```python
class TenantRepository(BaseRepository[T]):
    def _base_query(self):
        return select(self._model).where(self._model.org_id == self._current_org_id)
```

No query can return data from another org. This is enforced at the repository layer, not the endpoint layer — defense in depth.

#### 1.4 RBAC Enforcement

Permission matrix:

| Action | Owner | Admin | Member | Viewer | Agent |
|--------|-------|-------|--------|--------|-------|
| Create projects | Yes | Yes | Yes | No | No |
| Create issues | Yes | Yes | Yes | No | Scoped |
| Update issues | Yes | Yes | Own | No | Scoped |
| Delete anything | Yes | Yes | No | No | No |
| Manage members | Yes | Yes | No | No | No |
| Configure agents | Yes | Yes | No | No | No |
| View agent activity | Yes | Yes | Yes | Yes | No |
| View audit log | Yes | Yes | No | No | No |

Enforced via middleware that injects `current_user` and `current_org` into request state.

#### 1.5 Audit Trail

New model:

```
AuditLog
  id: UUID
  org_id: FK → Organization
  user_id: FK → User (nullable — system/agent actions)
  agent_session_id: FK → AgentSession (nullable)
  action: enum (create, update, delete, login, agent_tool_call, ...)
  entity_type: str
  entity_id: UUID
  changes: JSON (before/after diff for updates)
  ip_address: str
  user_agent: str
  timestamp: datetime
```

Automatically populated via service layer decorator — no manual logging in endpoints.

#### 1.6 Database Migrations

- Add org_id to all 43 existing models
- Create Organization, OrganizationMember, User, AuditLog tables
- Migrate existing data to a default org (single-user → single-org migration)
- Add indexes on org_id for all tables

---

### Phase 2: The Product (Core UI)

**Goal:** Three UI experiences that make Turbo a product, not a tool.

**Duration:** 4-6 weeks

#### 2.1 The Board

Jira-level issue management. This is where PMs and developers spend most of their time.

**Views:**
- **Kanban** — Columns by status (backlog, todo, in_progress, in_review, done). Drag-and-drop. Swimlanes by assignee or priority.
- **List** — Dense table view with inline editing. Sort by any column. Bulk actions.
- **Timeline** — Gantt-style view of milestones and initiatives with issue bars.
- **Calendar** — Issues by due date, milestones as markers.

**Features:**
- Saved views (filter + sort + grouping persisted per user)
- Quick filters (my issues, recently updated, blocked, unassigned)
- Keyboard navigation (j/k to move, enter to open, / to search)
- Inline editing (click status/priority/assignee to change without opening detail)
- Bulk operations (select multiple → change status, assign, tag, move to milestone)

**Data requirements:**
- API sorting (Phase 0.2)
- Cursor-based pagination for large issue lists
- WebSocket push for real-time board updates when agents modify issues

#### 2.2 The Control Room

Real-time visibility into what AI agents are doing. This is Turbo's differentiator.

**Layout:**
- **Activity stream** (left) — Live feed of agent actions: "Triager analyzed 5 issues in project X", "Worker started work on TURBO-42", "Planner created 3 issues for feature Y"
- **Active sessions** (center) — Cards for each running agent showing: current tool call, tokens used, cost so far, time elapsed
- **Stats dashboard** (right) — Today's metrics: total agent runs, total cost, issues created/updated by agents, approval queue depth

**Features:**
- Click any agent session → drill into full tool call timeline
- Pause/cancel running agent sessions
- Cost alerts (configurable threshold)
- Historical view (filter by date range, agent type, project)

**Data requirements:**
- Agent activity WebSocket channel (exists)
- AgentSession model with tool call history (exists, needs enrichment)
- Cost aggregation queries

#### 2.3 The Guardrails Panel

Configuration UI for AI agent permissions and controls. This is the enterprise sell.

**Sections:**

**Agent Configuration:**
- Which subagents are enabled
- Per-agent tool allowlists (checkbox matrix: agent × tool)
- Per-agent budget limits (max $/run, max $/day)
- Per-agent turn limits

**Project Scoping:**
- Which projects each agent can access
- Cross-project access rules
- Default scope for new agents

**Approval Rules:**
- Which actions require human approval before execution
- Auto-approve rules (e.g., "auto-approve issue updates under priority=low")
- Approval timeout (auto-reject after N hours)
- Notification preferences (email, WebSocket, both)

**Audit Viewer:**
- Searchable, filterable audit log
- Export to CSV/JSON
- Retention policy configuration

**Rate Limits:**
- Per-agent rate limits
- Per-tool rate limits
- Global org rate limits
- Current usage visualization

---

### Phase 3: Teams

**Goal:** Multiple humans collaborating in a shared workspace with AI teammates.

**Duration:** 4-6 weeks

#### 3.1 Multi-User Workspace

- Invite flow (email invite → accept → join org)
- Member management UI (roles, permissions, deactivation)
- User avatars and presence indicators
- Assignment (issues, milestones to specific users)
- @mentions in comments with notification

#### 3.2 Notifications

- In-app notification center
- Email notifications (configurable per event type)
- WebSocket push for real-time alerts
- Notification preferences per user

#### 3.3 Activity Feed

- Per-project activity timeline (human + agent actions interleaved)
- "What happened while I was away" summary (AI-generated)
- @mention notifications
- Comment threads with real-time updates

#### 3.4 AI as Team Member

- Agents appear in team member list with "AI" badge
- Assign issues to agents (triggers autonomous work)
- Agent-generated comments attributed to agent identity
- Review requests from agents to humans (exists as ReviewRequest model)

---

### Phase 4: Enterprise

**Goal:** Features required for enterprise sales. Compliance, security, admin control.

**Duration:** 6-8 weeks

#### 4.1 SSO/SAML

- SAML 2.0 integration (Okta, Azure AD, OneLogin)
- SCIM provisioning (auto-create/deactivate users from IdP)
- Enforce SSO (disable password/OAuth login for org)

#### 4.2 Advanced RBAC

- Custom roles (beyond owner/admin/member/viewer)
- Per-project roles (admin on Project A, viewer on Project B)
- Agent permission templates (reusable configurations)
- IP allowlists per org

#### 4.3 Compliance

- SOC2-ready audit logging (immutable, shipped to external store)
- Data retention policies (auto-archive after N days)
- Data export (full org export for portability)
- GDPR: user data deletion, consent tracking
- Audit log tamper detection (hash chains)

#### 4.4 Admin Console

- Org-wide agent usage dashboard
- Cost allocation by project/team/agent
- Usage quotas and billing integration
- Security event monitoring (failed logins, permission escalations)

---

### Phase 5: Platform

**Goal:** Extensibility that turns Turbo from a product into a platform.

**Duration:** Ongoing

#### 5.1 Custom Agents

- Agent builder UI (define name, tools, prompt, model, budget)
- Agent marketplace (share agent configurations across orgs)
- Custom tool definitions (bring your own MCP tools)
- Webhook-triggered agents (event → agent run)

#### 5.2 Integrations

- GitHub/GitLab: sync issues, PRs, branches
- Slack: notifications, slash commands, agent triggers
- Linear/Jira: import/export, two-way sync
- CI/CD: agent-triggered deployments with approval gates

#### 5.3 API Platform

- Public API with developer docs
- API keys with scoped permissions
- Webhooks for external consumers
- Rate limiting tiers by plan

---

## 6. Feature Domain Strategy

### Core PM — Ship Now

The 11 Core PM models + 10 AI/Agent models are the product. Every phase builds on these.

### Career — Separate Product

The 13 career models (Resume, JobApplication, Company, JobPosting, etc.) represent a distinct product: **AI-powered job search and application management**. This is valuable but it's not project management.

**Recommendation:** Extract career features into a separate module/product line. Don't mount career endpoints in the PM product. The MCP server can still expose them for personal use via Claude Code, but the web UI should not include job search features in the enterprise PM product.

Career models can become "Turbo Career" or be kept as a personal-use MCP-only feature.

### Content — Selective Inclusion

Content models (Documents, Blueprints, Notes) are core to PM — keep them.

Podcasts and Literature are personal knowledge management — same treatment as Career. Keep in MCP, exclude from enterprise PM UI.

---

## 7. Technical Debt to Resolve

Ordered by dependency (must do earlier items before later ones).

| # | Item | Phase | Why |
|---|------|-------|-----|
| 1 | Mount 15 dormant endpoint routers | 0 | Frontend pages exist with no backend |
| 2 | Add sorting to all list endpoints | 0 | Board views need sort |
| 3 | Fix TypeScript/ESLint build errors | 0 | Can't iterate on broken builds |
| 4 | Add cursor-based pagination | 1 | Offset pagination breaks on large datasets |
| 5 | Add full-text search (PostgreSQL tsvector) | 1 | Pattern matching doesn't scale |
| 6 | Centralize transaction management (M3 from REVIEW.md) | 1 | Inconsistent commit/rollback behavior |
| 7 | Agent module test suite | 1 | 0% coverage on critical AI path |
| 8 | Frontend test infrastructure (Vitest + Testing Library) | 2 | 0% coverage on UI |
| 9 | Dependency pinning / lockfile | 2 | Reproducible builds |
| 10 | Resolve 9 TODO items in production code | 2-3 | Tech debt cleanup |

---

## 8. Metrics

### Phase 0-1 (Solo Dev)
- Daily active use (are you using the UI daily?)
- Agent runs per day
- Issues created/closed per week (human vs. agent)
- Cost per agent run (trending down = good)

### Phase 2-3 (Teams)
- Users per org
- Agent actions per user per day
- Approval queue depth (should stay low — means rules are well-configured)
- Time to resolve issues (human-only vs. agent-assisted)

### Phase 4-5 (Enterprise)
- Orgs onboarded
- Seats per org
- Monthly recurring revenue
- Agent adoption rate (% of issues touched by agents)
- Compliance audit pass rate

---

## 9. Competitive Positioning

| Feature | Jira | Linear | Turbo |
|---------|------|--------|-------|
| Issue tracking | Deep | Clean | Deep + AI-aware |
| AI agents | Atlassian Intelligence (bolt-on) | None | First-class participants |
| Agent guardrails | None | None | Configurable per agent/project |
| Agent visibility | None | None | Real-time control room |
| Human-in-the-loop | None | None | Approval gates, review requests |
| MCP integration | None | None | 154-tool server |
| Self-hosted | Data Center (expensive) | No | Docker Compose |
| Price | $8-16/user/mo | $8-10/user/mo | TBD |

**Turbo's wedge:** The only PM tool where AI agents are team members with configurable permissions, not features behind a chatbot button.

---

## 10. Open Questions

1. **Pricing model:** Per-seat? Per-agent-run? Usage-based? Hybrid?
2. **Self-hosted vs. cloud:** Offer both? Cloud-first with self-hosted for enterprise?
3. **Career features:** Separate product? Module within Turbo? Kill entirely for enterprise focus?
4. **Mobile:** PWA sufficient? Or invest in React Native later?
5. **Agent model flexibility:** Lock to Claude? Support OpenAI/Gemini agents? Model-agnostic?
6. **Open source:** Core open source with enterprise features paid? Fully proprietary?

---

*This is a living document. Update it as decisions are made and phases are completed.*

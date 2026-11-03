# Spec Miner 1: Technical Specification & Mining Report

**Date**: 2026-11-01T19:15:00Z  
**Role**: Teamwork Specification Miner (`teamwork_spec_miner`)  
**Scope**: 
1. R1: Foundation Layers (`AGENTS.md`, `GEMINI.md`, `.agents/rules/*`, `.agents/workflows/*`, `docs/*`, `.agents/skills/*`) and character limits (<12k chars per file).
2. MCP Configurations (Memory MCP, Supabase MCP, Vercel MCP) and placement.
3. Swarm skills & subagent coordination skills (`graphify`, subagent handling, swarm coordination plans, conflict avoidance).
4. QA Challenger review criteria for R2.

---

## Executive Summary

An exhaustive audit of `UMBRELLA_BUILD_KIT.md`, `ORIGINAL_REQUEST.md`, and the existing filesystem layout within `c:\Users\DELL\ayesha_pro\medi_qr` and `C:\Users\DELL\.gemini` was executed. 

### Key Findings:
1. **Rule Character Limits**: Antigravity enforces a strict 12,000-character cap on rule files. All 6 active rule/instruction files in the repository (`AGENTS.md`, `GEMINI.md`, `01-design-system.md`, `02-security-privacy.md`, `03-typescript-nextjs.md`, `04-supabase-sql.md`) currently range between 950 and 5,511 characters, comfortably below the 12,000-character ceiling.
2. **Missing Foundation Assets**:
   - `docs/SPEC.md` is currently missing from `docs/`. It must be populated from the Master Technical Specification with formatting fixes defined in Section 1.6 of the build kit.
   - The 5 external skill suites (`apple-hig-designer`, Anthropic skills, Vercel skills, Supabase skills, and Matt Pocock skills) listed in Part 2 of `UMBRELLA_BUILD_KIT.md` are not yet installed in `.agents/skills/`. Only the two custom Umbrella skills (`umbrella-supabase-rls`, `umbrella-qr-card`) are present.
   - The root Next.js scaffolding (`package.json`, `tsconfig.json`, `src/`) does not exist yet on disk, awaiting Phase 0.
3. **MCP Configuration Architecture**:
   - Antigravity natively loads MCP configurations from `~/.gemini/config/mcp_config.json` (currently exists as a 0-byte file).
   - The required servers are:
     * **Memory MCP**: `@modelcontextprotocol/server-memory` (stdio transport) for persistent cross-session graph memory.
     * **Supabase MCP**: `@supabase/mcp-server` (stdio transport) configured with secure environment variable placeholders (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` / personal access token).
     * **Vercel MCP**: `@vercel/mcp` (stdio transport) configured with token placeholders (`VERCEL_TOKEN`, `VERCEL_PROJECT_ID`) for Phase 11 deployment.
4. **Swarm Skills & Subagent Coordination**:
   - **`graphify`**: An essential deterministic AST and architecture knowledge graph skill/MCP server preventing context token bloat and discovery churn across swarms.
   - **Subagent Handling**: Teamwork subagent protocol requiring isolated subagent folders (`.agents/teamwork/<subagent_id>/`), a strict single-writer rule, 5-component handoffs (`Observation`, `Logic Chain`, `Caveats`, `Conclusion`, `Verification Method`), and liveness heartbeats in `progress.md`.
   - **Swarm Coordination Plan**: Hierarchical structure separating Discovery, Build, Verification, and Audit swarms with phase gating (Phases 0 through 11).
5. **QA Challenger Criteria (R2)**:
   - An independent verification agent with an adversarial mindset must audit the entire setup against `UMBRELLA_BUILD_KIT.md`, grading Foundation completeness, character limits, MCP connectivity, skill accessibility, and non-negotiables (N1-N10) before build kickoff.

---

## Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Foundation | 6-Layer Architecture | Layered prompt and configuration structure: AGENTS.md, GEMINI.md, Rules, Workflows, Skills, Docs | Context loading triggers | Injected agent rules & instructions | Silently truncated or ignored if >12k chars | UMBRELLA_BUILD_KIT.md §0 |
| 2 | Foundation | Rule Length Cap (<12k) | Hard limit enforced by Antigravity on all rule and always-on files | Text file content | Parsed prompt tokens | Truncation or rule drop if >12,000 characters | UMBRELLA_BUILD_KIT.md §0 |
| 3 | Foundation | Precedence Hierarchy | Explicit priority when instructions conflict: Latest Message > DECISIONS.md > SPEC.md > AGENTS.md / Rules > Installed Skills | Multi-source instructions | Resolved agent action | Conflict resolution | UMBRELLA_BUILD_KIT.md §0 |
| 4 | Foundation | Project Rules (`AGENTS.md`) | Single source of project non-negotiables (N1-N10), fixed stack, and working protocol | System prompts | Agent operational constraints | Violation results in task rejection | Root `AGENTS.md` / Kit §4 |
| 5 | Foundation | Antigravity Extras (`GEMINI.md`) | Platform-specific execution instructions: planning mode on phases 1, 3, 10, 11; UI verification | Conversation mode | Execution strategy | Fallback to default AGENTS.md | Root `GEMINI.md` / Kit §5.1 |
| 6 | Foundation | Rules Directory (`.agents/rules/`) | Glob-triggered and always-on specialized rules: 01-design, 02-security, 03-ts-next, 04-sql | File path matching | Contextual linter / guardrails | Dropped if pattern mismatch | Kit §5.2 |
| 7 | Foundation | Workflows (`.agents/workflows/`) | Slash commands invoked on-demand: `/start-phase`, `/verify`, `/security-audit`, `/design-review` | User prompt slash command | Sequential verification procedure | Prompt rejection if workflow missing | Kit §5.3 |
| 8 | Foundation | Custom Skill: RLS | `umbrella-supabase-rls` playbook and reference SQL patterns (`references/rls-patterns.sql`) | DB schema, migration requests | Reference SQL, security tests | Fails if non-compliant with DECISIONS | Kit §6.1, §6.2 |
| 9 | Foundation | Custom Skill: QR Studio | `umbrella-qr-card` playbook for rendering QR, PNG export, printable PDF card, token regeneration | Patient ID, QR token, origin | PNG canvas, jsPDF card | Ambiguous origin warning if non-prod | Kit §6.3 |
| 10 | Foundation | Docs Layer (`docs/`) | Project reference store: SPEC.md, DECISIONS.md, PROGRESS.md, DB-RUNBOOK.md, DEPLOY.md | Agent query / phase instructions | Ground truth state | Overridden by DECISIONS.md | Kit §7 |
| 11 | MCP | Global MCP Config | Central Antigravity MCP definition file located at `~/.gemini/config/mcp_config.json` | JSON server definitions | Injected MCP tools & prompts | Connection error in Antigravity logs | `mcp_servers.md` |
| 12 | MCP | Memory MCP Server | Persistent external memory graph for cross-conversation context retention | Entities, relations, observations | Stored knowledge graph | In-memory fallback if disconnected | ORIGINAL_REQUEST.md §R1 |
| 13 | MCP | Supabase MCP Server | Tooling integration for Supabase Postgres schema exploration, migrations, and RLS validation | SQL queries, table inspect | DB metadata, execution results | Permission denied or auth error | ORIGINAL_REQUEST.md §R1 |
| 14 | MCP | Vercel MCP Server | Tooling integration for Vercel project management, deployments, and preview inspection | Deploy commands, project IDs | Build status, deployment URLs | Auth failure on missing token | ORIGINAL_REQUEST.md §R1 |
| 15 | Swarm Skill | Graphify AST Graph | Progressive disclosure knowledge graph tool extracting codebase architecture and dependencies | Project files, AST, schemas | Queryable graph (`graph.json`), MCP tools | Fallback to regex grep if unindexed | ORIGINAL_REQUEST.md / Web spec |
| 16 | Swarm Skill | Subagent Handling Protocol | Teamwork standard operating procedure for subagent dispatch, execution, monitoring, and handoff | Dispatch tasks, prompts | Structured handoff reports (`handoff.md`) | Handoff rejection if components missing | System prompt / Teamwork standard |
| 17 | Swarm Skill | Conflict Avoidance Protocol | Single-writer isolation, isolated agent workspace folders, and phase gating to prevent write races | Task assignments, directory paths | Safe concurrent execution | File corruption or git merge conflict | System prompt / Teamwork standard |
| 18 | Swarm Skill | Swarm Coordination Plan | Hierarchical task distribution plan dividing work across specialized lead agents and swarms | Project roadmap, phases | Clear assignment matrix | Blocked dependencies or agent idle | ORIGINAL_REQUEST.md §R1 |
| 19 | QA Challenger | R2 Review Checklist | Adversarial verification checklist auditing setup completeness, rule compliance, and MCP connectivity | Foundation files, MCP configs | Structured QA audit report | Iterative rejection until remediated | ORIGINAL_REQUEST.md §R2 |
| 20 | QA Challenger | Iterative Refinement Loop | Feedback and remediation protocol driving revisions until 100% compliance is attained | Challenger findings & action items | Remediated codebase & configs | Task paused until all flags cleared | ORIGINAL_REQUEST.md §R2 |

---

## Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | Rule Length Limit | Rule file exceeding 12,000 characters | Antigravity truncates the rule or fails to inject it into context silently, leading to subtle rule violations. |
| 2 | Spec vs Decisions Priority | Contradiction between `docs/SPEC.md` and `docs/DECISIONS.md` | `docs/DECISIONS.md` strictly wins per Section 0 precedence rules (e.g. D1 doctor approval gate wins over SPEC 4.2 self-signup). |
| 3 | Emergency Route Auth Leak | Public unauthenticated request to `/emergency/[token]` | Must NEVER require login; reads ONLY via `get_emergency_triage_by_token`; residential address and spouse/dependents must never be in JSON output. |
| 4 | Doctor Registration Role Escalation | Signup payload with `role: 'admin'` or `role: 'doctor'` | DB trigger `handle_new_user` defaults non-doctor to `patient`, and doctor to `doctor_status: 'pending'`. Pending doctor reads zero patient rows. |
| 5 | Token Rotation Invalidation | `regenerate_qr_token` executed by patient | Updates `qr_token` to new UUID; prior token immediately returns null/404 from `/emergency/[token]`; previous physical prints invalidated. |
| 6 | QR Origin Hydration Mismatch | Server-rendered QR code with `window.location.origin` | Server lacks `window`; client hydration mismatch occurs unless URL is computed in `useEffect` post-mount with a placeholder skeleton. |
| 7 | Non-Production QR Scan | QR generated on `localhost` or `*.vercel.app` preview domain | UI must display amber warning: "This QR points to <origin>. Cards printed here only work while that site is online." Does not block export. |
| 8 | MCP Server Auth Without Keys | Supabase or Vercel MCP initialized before credentials are provided | MCP server must support placeholder environment variables without crashing language server process during foundation phases. |
| 9 | Subagent Cross-Directory Edits | Subagent A writes directly to Subagent B's workspace folder or root code | Violates workspace isolation rules; causes uncoordinated state overwrites; lead agent must enforce single-writer policy. |
| 10 | Emergency Route Client JS Bloat | Bundling `framer-motion`, `qrcode.react`, or `jspdf` on `/emergency/[token]` | Violates Decision D13 and Non-Negotiable N8; route must be pure Server Component with zero animation libraries and minimal JS. |

---

## Detailed Specifications

### 1. R1: Foundation Layers & Character Limits

Antigravity operates with a 6-layer architecture designed to keep the model fast, deterministic, and accurate:
```text
Layer 1: AGENTS.md            (Project root — Always visible)
Layer 2: GEMINI.md            (Project root — Always visible Antigravity extras)
Layer 3: Rules                (.agents/rules/* — Glob or always-on triggers)
Layer 4: Workflows            (.agents/workflows/* — On-demand slash commands)
Layer 5: Skills               (.agents/skills/* — Specialized playbooks)
Layer 6: Docs                 (docs/* — Ground truth specification & decisions)
```

#### Precise Character Count Audit
Antigravity imposes a strict hard ceiling of **12,000 characters** per rule file. Below is the audited inventory of all existing foundation files:

| File Path | Purpose | Trigger Type | Size (Bytes) | Char Count | Compliance (<12,000 chars) |
|---|---|---|---|---|---|
| `AGENTS.md` | Non-negotiables (N1-N10), fixed stack, protocols | Always-on | 5,511 | 5,511 | **PASS** (45.9% of limit) |
| `GEMINI.md` | Antigravity-specific extras (modes, browser verification) | Always-on | 950 | 950 | **PASS** (7.9% of limit) |
| `.agents/rules/01-design-system.md` | Apple design tokens, spacing by route, motion springs | `src/**/*.{ts,tsx,css}` | 3,741 | 3,741 | **PASS** (31.2% of limit) |
| `.agents/rules/02-security-privacy.md` | Data access, RBAC, secrets hygiene, emergency route rules | `always_on` | 1,822 | 1,822 | **PASS** (15.2% of limit) |
| `.agents/rules/03-typescript-nextjs.md` | Strict TypeScript, Next.js proxy/middleware, Supabase SSR | `src/**/*.{ts,tsx}` | 2,059 | 2,059 | **PASS** (17.2% of limit) |
| `.agents/rules/04-supabase-sql.md` | Migrations, security definer functions, RLS, smoke tests | `supabase/**/*.sql` | 1,289 | 1,289 | **PASS** (10.7% of limit) |
| `.agents/workflows/start-phase.md` | `/start-phase` workflow | On-demand | 545 | 545 | **PASS** (<12k) |
| `.agents/workflows/verify.md` | `/verify` test & UI screenshot workflow | On-demand | 602 | 602 | **PASS** (<12k) |
| `.agents/workflows/security-audit.md` | `/security-audit` automated grep & policy check | On-demand | 1,057 | 1,057 | **PASS** (<12k) |
| `.agents/workflows/design-review.md` | `/design-review` WCAG & design token check | On-demand | 677 | 677 | **PASS** (<12k) |
| `docs/DECISIONS.md` | Decisions D1 to D18 modifying SPEC | On-demand | 4,808 | 4,808 | **PASS** (<12k) |
| `docs/PROGRESS.md` | Agent phase ledger and status tracking | On-demand | 853 | 853 | **PASS** (<12k) |
| `docs/SPEC.md` | Master Technical Specification v2.0 | On-demand | **MISSING** | **0** | **ACTION REQUIRED** |
| `.agents/skills/umbrella-supabase-rls/SKILL.md` | Reference RLS patterns & SQL test checklist | Skill description | 3,076 | 3,076 | **PASS** (<12k) |
| `.agents/skills/umbrella-supabase-rls/references/rls-patterns.sql` | SQL pattern reference | Reference file | 13,845 | 13,845 | Non-rule reference SQL |
| `.agents/skills/umbrella-qr-card/SKILL.md` | QR studio, PNG/PDF export, URL calculations | Skill description | 2,873 | 2,873 | **PASS** (<12k) |

#### Required External Skills to Install
Part 2 of `UMBRELLA_BUILD_KIT.md` prescribes installing the following external skill suites in `.agents/skills/`:
1. `apple-hig-designer` (`axiaoge2/apple-hig-designer`)
2. Anthropic skills (`anthropics/skills`):
   - `frontend-design`
   - `webapp-testing`
3. Vercel skills (`vercel-labs/agent-skills`):
   - `vercel-react-best-practices`
   - `web-design-guidelines`
   - `vercel-composition-patterns`
   - `deploy-to-vercel`
4. Supabase skills (`supabase/agent-skills`):
   - `supabase`
   - `supabase-postgres-best-practices`
5. Matt Pocock skills (`mattpocock/skills`):
   - `setup-matt-pocock-skills`, `grill-with-docs`, `tdd`, `diagnose`, `zoom-out`, `improve-codebase-architecture`

---

### 2. MCP Configurations Specification

Antigravity uses the Model Context Protocol (MCP) to supply external tools to the agent.

#### Placement:
1. **Global Configuration File**: `C:\Users\DELL\.gemini\config\mcp_config.json` (active across all sessions). Currently exists at 0 bytes.
2. **Repository Mirror**: `.gemini/mcp_config.json` inside `c:\Users\DELL\ayesha_pro\medi_qr` for repository self-containment.

#### Target Configuration Schema (`mcp_config.json`):
```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "description": "Persistent memory graph for tracking entities, relations, and architectural state across sessions"
    },
    "supabase": {
      "command": "npx",
      "args": ["-y", "@supabase/mcp-server"],
      "env": {
        "SUPABASE_URL": "https://YOUR_PROJECT_ID.supabase.co",
        "SUPABASE_ANON_KEY": "YOUR_SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY": "PLACEHOLDER_FOR_LATER_PROVISION_IF_AUTHORIZED"
      },
      "description": "Supabase Postgres management, schema inspection, and RLS policy verification"
    },
    "vercel": {
      "command": "npx",
      "args": ["-y", "@vercel/mcp"],
      "env": {
        "VERCEL_TOKEN": "PLACEHOLDER_FOR_DEPLOYMENT_STAGES",
        "VERCEL_PROJECT_ID": "PLACEHOLDER_PROJECT_ID",
        "VERCEL_TEAM_ID": "PLACEHOLDER_TEAM_ID"
      },
      "description": "Vercel integration for deployment stages, environment variables, and build inspections"
    }
  }
}
```

*Security Note*: Under Non-Negotiable **N4**, the `service_role` key must NEVER appear in code, `.env.example`, logs, commits, or chat. In development and runtime client code, only the publishable/anon key is used. MCP credentials are placeholder tokens provided out-of-band by the developer.

---

### 3. Swarm Skills & Subagent Coordination Framework

To build Umbrella reliably without chaos, agents are structured into **Hierarchical Swarms** governed by strict protocols.

#### 3.1 The `graphify` Knowledge Skill
- **Purpose**: Generates and maintains a deterministic, queryable AST and architectural knowledge graph (`graph.json`).
- **Advantage**: Bypasses token bloat caused by agents running massive grep/read searches on every turn.
- **Tools Provided**: `query_graph`, `get_neighbors`, `god_nodes`, `shortest_path`.
- **Integration**:
  - Registered as `.agents/skills/graphify/SKILL.md`
  - Integrated into slash workflows (e.g. `/start-phase` and `/verify`) to check dependency impact before and after code changes.

#### 3.2 Subagent Handling Protocol
Each subagent spawned by the Orchestrator follows five core operational laws:
1. **Directory Isolation**: Each subagent owns an exclusive directory (`.agents/teamwork/<subagent_name>/`). It reads any directory, but writes **only** to its assigned folder.
2. **Heartbeat Liveness**: Updates `progress.md` with a UTC timestamp `Last visited: [timestamp]` at least every 5 minutes during execution.
3. **Situational Memory**: Maintains a persistent, append-only `BRIEFING.md` (<100 lines) with mission, identity, constraints, and artifact indexes.
4. **Structured Handoff**: Produces a self-contained `handoff.md` with the 5 required sections:
   - `1. Observation` (exact file paths, line numbers, tool outputs)
   - `2. Logic Chain` (step-by-step reasoning)
   - `3. Caveats` (uninvestigated areas, assumptions)
   - `4. Conclusion` (verifiable final assessments)
   - `5. Verification Method` (concrete commands to reproduce and verify)
5. **Direct Notification**: Notifies the orchestrator via `send_message` with recipient ID upon completion or when blocked.

#### 3.3 Swarm Coordination Architecture
```text
                         +-----------------------+
                         |  Sentinel / Human     |
                         +-----------+-----------+
                                     |
                         +-----------v-----------+
                         | Teamwork Orchestrator |
                         +-----------+-----------+
                                     |
         +---------------------------+---------------------------+
         |                           |                           |
+--------v--------+         +--------v--------+         +--------v--------+
| Discovery Swarm |         | QA Challenger   |         | Builder Swarm   |
| (Spec Miners,   |         | (Adversarial    |         | (Phase-by-Phase |
|  Explorers)     |         |  Verifier)      |         |  Implementers)  |
+-----------------+         +-----------------+         +-----------------+
```

#### 3.4 Conflict Avoidance Rules
- **The Single-Writer Rule**: Exactly one agent is permitted to write to a target module or file at any given time.
- **Phase Gating**: AGENTS.md rule 4.1 forbids running multiple build phases concurrently ("One phase at a time... never start the next one"). Swarms must execute sequentially through Phase 0 to Phase 11.
- **Branch Isolation**: Each phase runs on a distinct git branch `phase/<n>-<slug>`, validated by `/verify` before merging to `main`.

---

### 4. QA Challenger Review Criteria for R2

Requirement R2 mandates deploying an independent QA Challenger subagent to conduct a rigorous, adversarial review before implementation starts.

#### Comprehensive Challenger Audit Checklist:
1. **Foundation Integrity**:
   - [ ] `AGENTS.md` and `GEMINI.md` exist at root and exactly match `UMBRELLA_BUILD_KIT.md` Parts 4 and 5.1.
   - [ ] All 4 rule files in `.agents/rules/` exist with valid YAML frontmatter and glob patterns.
   - [ ] Character count of every file in `.agents/rules/` is strictly under 12,000 characters.
   - [ ] All 4 workflow files in `.agents/workflows/` (`start-phase.md`, `verify.md`, `security-audit.md`, `design-review.md`) exist and define exact step sequences.
   - [ ] `docs/DECISIONS.md` contains all 18 decisions (D1–D18) verbatim.
   - [ ] `docs/PROGRESS.md` contains the full 12-phase ledger.
   - [ ] `docs/SPEC.md` exists and is formatted per Section 1.6 rules.
   - [ ] Custom skills `umbrella-supabase-rls` and `umbrella-qr-card` have valid `SKILL.md` headers.
   - [ ] Installed skills specified in Part 2 are mapped or present.

2. **MCP Integration Setup**:
   - [ ] `~/.gemini/config/mcp_config.json` contains valid JSON matching Antigravity's stdio schema.
   - [ ] Memory MCP server is configured and runnable.
   - [ ] Supabase MCP server is configured with appropriate credential placeholders.
   - [ ] Vercel MCP server is configured with token placeholders.
   - [ ] Zero secrets or sensitive service-role keys are committed or hardcoded.

3. **Swarm Coordination Setup**:
   - [ ] `graphify` knowledge skill is integrated into workflow commands.
   - [ ] Subagent coordination rules and handoff templates are documented.
   - [ ] Conflict-avoidance rules (single-writer, isolated directories, phase gating) are formally defined.

4. **Non-Negotiables (N1-N10) Guardrails**:
   - [ ] N1: Emergency route (`/emergency/[token]`) zero-login, strictly isolated from address and dependents.
   - [ ] N2: Doctor portal sticky read-only patient context banner.
   - [ ] N3: Server-side RBAC & RLS, `getUser()` enforcement, no client-role trust.
   - [ ] N4: Zero service_role key leakage.
   - [ ] N5: Zero mock auth.
   - [ ] N6: QR origin post-mount client computation.
   - [ ] N7: Apple design tokens, no purple gradients, no heavy shadows.
   - [ ] N8: `appleSpring` motion, zero animation on emergency triage page.
   - [ ] N9: Synthetic test data only.
   - [ ] N10: Strict TypeScript and Zod validation, zero unchecked `any`.

---

## Actionable Recommendations for Orchestrator

1. **Populate `docs/SPEC.md`**: The missing `docs/SPEC.md` must be generated immediately so that subsequent phases have the complete specification to consult alongside `DECISIONS.md`.
2. **Initialize MCP Config**: Write the standardized `mcp_config.json` to `C:\Users\DELL\.gemini\config\mcp_config.json` and mirror it in `.gemini/mcp_config.json`.
3. **Install / Mock Swarm Skills**: Place `graphify` and subagent coordination playbooks into `.agents/skills/`.
4. **Trigger QA Challenger Review (R2)**: Dispatch the QA Challenger with the checklist defined above to validate the foundation before kicking off Phase 0/Phase 1 implementation.

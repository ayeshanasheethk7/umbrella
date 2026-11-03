# Umbrella Swarm Coordination Plan

This document establishes the operational coordination architecture for hierarchical swarms executing the Umbrella Emergency Medical ID platform. It defines leadership roles, swarm boundaries, phase-gated execution rules, and concurrency conflict-avoidance protocols.

---

## 1. Hierarchical Swarm Architecture

The project operates under a multi-tier governance model ensuring end-to-end accountability, independent verification, and conflict-free execution:

```text
                           +------------------------+
                           |   Sentinel (Integrity) |
                           +-----------+------------+
                                       |
                           +-----------v------------+
                           |  Project Orchestrator  |
                           +-----------+------------+
                                       |
         +-----------------------------+-----------------------------+
         |                             |                             |
+--------v--------+           +--------v--------+           +--------v--------+
| Discovery Swarm |           |  QA Challenger  |           |   Build Swarm   |
| (Miners & AST)  |           |  (Adversarial)  |           |  (Implementers) |
+-----------------+           +-----------------+           +--------+--------+
                                                                     |
                                                            +--------v--------+
                                                            | Verification &  |
                                                            |   Audit Swarms  |
                                                            +-----------------+
```

---

## 2. Lead Agent Roles & Responsibilities

| Role | Primary Identity | Core Responsibilities |
|---|---|---|
| **Sentinel** | `teamwork_sentinel` | Overall project integrity oversight, independent victory audit, non-negotiables enforcement. |
| **Project Orchestrator** | `teamwork_orchestrator` | Milestone planning, subagent lifecycle dispatch, dependency management, branch merges. |
| **QA Challenger** | `teamwork_challenger` | Adversarial pre-implementation review, configuration stress-testing, defect tracking until remediation. |
| **Discovery Lead** | `teamwork_spec_miner` | Specification extraction, environment discovery, AST knowledge graph generation (`graphify`). |
| **Builder Lead** | `teamwork_worker` | Phase-by-phase implementation, minimal-change editing, unit test implementation. |
| **Verification Lead** | `teamwork_qa` | 5-tier dual-track test suites (Vitest, Playwright mobile 375x667 & desktop 1280x800). |
| **Auditor Lead** | `teamwork_auditor` | 28-point system audit (Security, RLS, A11y, Performance, API hygiene) and remediation verification. |

---

## 3. Specialized Swarms & Task Allocation

### 3.1 Discovery Swarm
- **Mission**: Mine specifications from `UMBRELLA_BUILD_KIT.md`, analyze system layout, extract AST dependency graphs (`graphify`), and uncover latent edge cases.
- **Key Artifacts**: Mined specification reports, AST graph (`.agents/graph.json`), environment matrices.
- **Constraints**: Read-only access to codebase; writes strictly to `.agents/teamwork/spec_miner_*/`.

### 3.2 QA Challenger Swarm
- **Mission**: Provide adversarial, independent verification of all plans, specifications, MCP configurations, and foundation assets before build kickoff (Requirement R2).
- **Key Artifacts**: Challenger Audit Report, Defect Remediation Punchlist.
- **Authority**: Holds veto power over build kickoff until all identified gaps are resolved.

### 3.3 Build Swarm
- **Mission**: Execute autonomous, full-scale implementation through Phases 0 to 11.
- **Execution Units**: Dedicated workers assigned to sequential phases (Database, Primitives, Auth, Emergency Route, Patient Portal, Doctor Portal, Marketing).
- **Constraints**: Single-writer ownership per phase; zero mock auth; zero placeholder components.

### 3.4 Verification Swarm
- **Mission**: Construct and execute the 5-Tier Dual-Track test harness:
  - Tier 1: Unit logic & Zod schema validation (Vitest).
  - Tier 2: Database RLS policies and RPC smoke tests (`supabase/tests/rls_smoke.sql`).
  - Tier 3: Mobile (375x667) user journeys via Playwright.
  - Tier 4: Desktop (1280x800) clinical workflows via Playwright.
  - Tier 5: Adversarial attack scenarios (privilege escalation, cross-patient data access, emergency route leakage).

### 3.5 Audit Swarm
- **Mission**: Conduct the exhaustive 28-point system audit across 5 dimensions:
  1. Security & RBAC (N1, N3, N4, N5).
  2. RLS & Column Grants (Postgres policy coverage).
  3. UI Responsiveness & Design System (Apple HIG, 375x667 & 1280x800, WCAG AA contrast).
  4. Performance & JS Bundle Budget (D13: <120KB gzipped, zero framer-motion on `/emergency`).
  5. API & Secret Hygiene (zero `service_role` leaks, zero `getSession()`, safe parameterized queries).

---

## 4. Phase-Gated Execution Protocol

In strict adherence to **AGENTS.md Rule 4.1** ("One phase at a time. The human says Phase N; do only that phase. Never start the next one"):
- Swarms execute sequentially.
- No downstream phase may start until the upstream phase has passed typecheck, lint, build, visual verification, and orchestrator approval.

### Phase Progression Matrix
| Phase | Scope | Main Target Files | Gate Criteria |
|---|---|---|---|
| **Phase 0: Bootstrap** | Tooling, packages, CSS tokens, layout | `package.json`, `globals.css`, `motion.ts`, `layout.tsx` | `typecheck`, `lint`, `build` green |
| **Phase 1: Database** | Schema, RLS, triggers, RPCs, tests | `supabase/migrations/`, `seed.sql`, `rls_smoke.sql` | All 13 RLS smoke tests PASS |
| **Phase 2: Primitives** | Apple UI kit, buttons, modal, pills | `src/components/ui/*`, `src/app/(dev)/ui/` | Zero WCAG AA violations |
| **Phase 3: Auth & RBAC** | Supabase SSR, proxy/middleware, login/signup | `src/lib/supabase/*`, `middleware.ts`, `(auth)/*` | Zero mock auth; doctor pending gate works |
| **Phase 4: Emergency Route** | Zero-login triage view, 56px call button | `src/app/emergency/[token]/page.tsx` | No address/dependents; zero motion bundle |
| **Phase 5: Patient Portal Shell** | Bento shell, QR Studio, PDF/PNG export | `src/app/portal/patient/`, `src/components/qr/*` | QR encodes valid origin; rotation works |
| **Phase 6: Patient Demographics** | Demographics form, baseline submit | `src/components/patient/*` | Column grant updates pass |
| **Phase 7: Doctor Portal Clinical** | Patient lookup, sticky banner, clinical editor | `src/app/portal/doctor/`, `src/components/doctor/*` | Sticky banner (N2); trigger stamps verification |
| **Phase 8: Doctor Appointments** | Appointments manager, escalation flow | `src/components/doctor/AppointmentsManager.tsx` | Status updates trigger last_appointment |
| **Phase 9: Marketing Landing** | 3D tilting card, sticky scroll story, CTA | `src/app/(marketing)/page.tsx` | Mobile-first; Lighthouse score >= 90 |
| **Phase 10: QA & Hardening** | 28-point audit, security checks, CI workflow | `.github/workflows/ci.yml`, test suites | Zero security or accessibility flags |
| **Phase 11: Deployment** | Runbook validation, pre-deploy verification | `docs/DEPLOY.md`, build checks | Vercel & Supabase production ready |

---

## 5. Conflict Avoidance & Concurrency Rules

1. **The Single-Writer Rule**:
   - Only ONE subagent is authorized to modify a file at any time.
   - Concurrent tasks must be partitioned into strictly disjoint directory subtrees.
2. **Directory Isolation**:
   - Each subagent operates within its exclusive directory: `.agents/teamwork/<agent_id>/`.
   - Never write to a peer agent's directory.
3. **Branch Isolation**:
   - Each phase is developed on an isolated git branch: `phase/<n>-<slug>`.
   - Merges to `main` occur only after complete phase verification.
4. **Heartbeat Protocol**:
   - Every active agent updates its `progress.md` with an ISO-8601 UTC timestamp `Last visited:` at least every 5 minutes during active work.
5. **Self-Contained Handoff Standard**:
   - Every task completes with a formal `handoff.md` containing all 5 required components:
     1. Observation
     2. Logic Chain
     3. Caveats
     4. Conclusion
     5. Verification Method

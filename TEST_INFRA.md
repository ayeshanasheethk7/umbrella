# TEST_INFRA.md — Umbrella 5-Tier Test Architecture & Infrastructure Index

## 1. Executive Summary & 5-Tier Test Architecture

Umbrella operates across three distinct surfaces handling life-critical emergency medical information:
1. **Public Roadside Triage (`/emergency/[token]`)**: Zero-login, unauthenticated emergency access (Invariant N1, N4, N6).
2. **Patient Management Portal (`/portal/patient`)**: Personal demographics, ICE contacts, family dependents, self-reported baseline, and ISO CR80 emergency pass.
3. **Doctor Clinical Portal (`/portal/doctor`)**: Gated provider workspace featuring multi-modal lookup, persistent read-only safety banner (Invariant N2), and clinical record editor.

To guarantee life-safety compliance, privacy guarantees, and adversarial resistance, Umbrella implements a 5-tier testing pyramid:

```
┌────────────────────────────────────────────────────────────────────────┐
│  Tier 5: Adversarial Attacks & Penetration Invariants (White-Box)     │
│  Vectors A-F: N1 Privacy, N4 Secrets, N3/N5 Auth, N2 Banner, SQL/RPC   │
├────────────────────────────────────────────────────────────────────────┤
│  Tier 4: Real-World Application Scenarios (Playwright E2E)             │
│  Full journeys: Mobile (375x667) & Desktop (1280x800) Viewports        │
├────────────────────────────────────────────────────────────────────────┤
│  Tier 3: Cross-Feature Pairwise Interactions (Dual-Module E2E)         │
│  Patient Demographics <-> Emergency Triage, Doctor Verify <-> Baseline │
├────────────────────────────────────────────────────────────────────────┤
│  Tier 2: Boundary & Corner Cases (Vitest Unit & Schema Stress)         │
│  Extreme inputs: Unicode, max lengths, negative ages, invalid tokens   │
├────────────────────────────────────────────────────────────────────────┤
│  Tier 1: Feature Coverage (Vitest Pure Logic & Happy Path Isolation)   │
│  Isolation checks: Zod schemas, URL building, geometry maths, springs  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Mathematical Threshold Derivation (184+ Tests Minimum)

Per specification, the required test count is mathematically derived from the 16 core features of the system ($N = 16$):

$$\text{Threshold} = 11 \times N + \max\left(5, \left\lfloor\frac{N}{2}\right\rfloor\right)$$

- **Baseline Feature Multiplier**: $11 \times 16 = 176\text{ tests}$
- **Cross-Cutting Offset**: $\max(5, \lfloor 16 / 2 \rfloor) = \max(5, 8) = 8\text{ tests}$
- **Mandatory Minimum Test Count**: $176 + 8 = \mathbf{184}\text{ tests}$

### Planned & Executed Test Distribution (Target: 195 Tests, 106%):
- **Tier 1 (Feature Coverage — Happy Path Isolation)**: 80 tests
- **Tier 2 (Boundary & Corner Cases — Schema Stress & Invariants)**: 80 tests
- **Tier 3 (Cross-Feature Pairwise Integration)**: 12 tests
- **Tier 4 (Real-World Application Scenarios)**: 8 tests (4 Mobile 375x667, 4 Desktop 1280x800)
- **Tier 5 (Adversarial Attacks & Penetration Invariants)**: 15 tests (Vectors A-F)
- **Total Suite Execution**: $80 + 80 + 12 + 8 + 15 = \mathbf{195}\text{ tests}$ (Exceeds 184 minimum threshold).

---

## 3. 16-Feature Mapping Matrix Across Tiers 1–5

| # | Feature Inventory Item | Tier 1 (Happy Path) | Tier 2 (Boundaries) | Tier 3 (Pairwise) | Tier 4 (Scenarios) | Tier 5 (Adversarial) |
|---|------------------------|---------------------|---------------------|-------------------|--------------------|----------------------|
| **F1** | Foundation & Config | Config file existence, path aliases | Zero-length files, syntax bounds | Next.js config <-> Tailwind | Server build & dev boot | Rule <12k character audit |
| **F2** | MCP Integrations | Config parsing (memory, supabase, vercel) | Missing credentials, malformed URLs | MCP <-> env vars | Tool invocation smoke | Secret injection in MCP config |
| **F3** | Swarm Skills & Subagent SOP | Single-writer workspace validation | Broken SKILL frontmatter, script bounds | Handoff <-> Briefcase sync | Swarm orchestration run | Concurrent collision check |
| **F4** | Coordination Plan | Matrix role parsing, parent-child id format | Cyclic delegation loops, rogue IDs | Lead dispatch <-> Worker reply | Full milestone workflow | Rogue agent isolation |
| **F5** | QA Challenger Audit | Verification script parsing, check counts | Non-zero exit code detection | Challenger <-> Verify scripts | Independent challenger recheck | Harness bypass probe |
| **F6** | DB Schema & Constraints | Column type checks, enum user_role | Negative age, invalid blood group | Accounts trigger <-> Profile insert | Patient registration DB flow | Raw constraint violations |
| **F7** | RLS Policies & Grants | is_approved_doctor() policy checks | Column update on protected fields | Authenticated <-> Foreign tenant | Doctor reading approved data | Cross-tenant update attempts |
| **F8** | Security Definer RPCs | Parameter schema validation for 3 RPCs | Empty array, overflow array (>50 items) | Regenerate token <-> Lookup 404 | Token rotation round-trip | SQL search_path injection |
| **F9** | Zero-Mock Supabase Auth | loginSchema, signupSchema validation | Password <8 or >128, bad email | Signup trigger <-> Auto-profile | Full signup -> session cookie | Role tampering in metadata |
| **F10** | Environment Hygiene | Next.js env var schema check | Missing env vars, bad URL protocol | Client <-> Anon client init | Production build env check | Repo-wide service_role sweep |
| **F11** | Patient Portal Surface | updateDemographicsSchema, cn(), phone | 255 char address, 10 dependents cap | Patient update <-> Emergency update | Mobile & Desktop profile edit | Form tampering prevention |
| **F12** | Doctor Portal Surface | Patient search schema, dirty-state tracker | 100-char query limit, <2 char query | Doctor verify <-> Baseline lock | Search -> Banner -> Edit -> Save | Wildcard flood & precedence |
| **F13** | Emergency Triage Route | emergencyTriageSchema, buildEmergencyUrl | Malformed UUID tokens, missing fields | Public RPC fetch <-> UI render | Roadside scan -> 56px call | Invariant N1 Privacy Leak Probe |
| **F14** | QR Studio & Card Export | CR80 dimensions [85.6, 54] mm, canvas | Long name (max 44), long URL (77.6) | Canvas export <-> Blob revoke | Download PNG & PDF ID card | Canvas memory leak attack |
| **F15** | Dual-Track 5-Tier Tests | Vitest runner assertions, Playwright config | Flaky test retries, timeout bounds | Unit <-> E2E coverage sync | Full CI pipeline simulation | Adversarial challenge run |
| **F16** | Granular System Audit | 28-point audit checklist validation | Incomplete criteria detection | Rated review <-> Verify report | Milestone completion gate | Invariant regression sweep |

---

## 4. Test Directory Layout & Artifact Registry

```
tests/
├── unit/
│   ├── schemas.test.ts          # Tier 1 & 2: 15 Zod schemas, blood groups, N1 superRefine
│   ├── utils.test.ts            # Tier 1 & 2: safeNext open redirect, sanitizeTel, formatPhone
│   ├── motion.test.ts           # Tier 1 & 2: appleSpring physics tokens, motion curves
│   ├── doctor-actions.test.ts   # Tier 1 & 2: escapeSearchTerm sanitization, search classification
│   ├── card-geometry.test.ts    # Tier 1 & 2: CR80 ISO geometry, 300 DPI canvas math
│   └── supabase-anon.test.ts    # Tier 1 & 2: Cookie-less anon client isolation, env guards
├── e2e/
│   ├── helpers/
│   │   └── auth.ts              # Synthetic user fixtures, UI login helper, viewport check
│   ├── tier3-pairwise.spec.ts   # Tier 3: 6 Cross-feature pairwise integration flows
│   └── tier4-scenarios.spec.ts  # Tier 4: 4 Real-world user journeys (375x667 & 1280x800)
vitest.config.ts                 # Vitest test runner configuration
playwright.config.ts             # Playwright multi-viewport runner configuration
scripts/
├── adversarial_challenge_m9.py  # Tier 5: Vectors A-F penetration test challenge
└── verify_m9.py                 # Automated 50+ point verification harness
```

---

## 5. Invariant Verification Standards

- **N1**: `/emergency/[token]` never leaks `residential_address` or `spouse_dependents`. Enforced at DB RPC projection, SSR payload, DOM, and Zod `.superRefine`.
- **N2**: Doctor Portal safety banner is persistent (`position: sticky`, `z-30`), read-only (zero editable inputs), and locked to patient vitals.
- **N3**: Server authentication strictly via `auth.getUser()`, never `getSession()`.
- **N4**: Zero `service_role` secrets across source, configs, or logs.
- **N5**: Zero mock auth. Authentic Supabase authentication.
- **N6**: QR URL computed client-side post-mount via `window.location.origin + '/emergency/' + qr_token`.
- **N7**: Design tokens strictly follow `01-design-system.md` with zero raw hex color classes.
- **N8**: Motion physics follow `appleSpring` (stiffness 120, damping 20, mass 1); zero framer-motion on emergency route.
- **N10**: TypeScript strict mode with zero `any` and zero `@ts-ignore`.
- **Rule 12k**: Every file created or edited strictly under 12,000 characters.

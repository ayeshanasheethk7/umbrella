# Project: Umbrella Emergency Medical ID Platform

## Architecture
- **Framework**: Next.js App Router (per DECISIONS D16: latest produced by create-next-app), TypeScript (strict), React, Tailwind CSS.
- **Backend / DB**: Supabase Postgres with Row Level Security (RLS), `@supabase/ssr` (server-side auth & cookies), `@supabase/supabase-js`.
- **Surfaces**:
  1. `/portal/patient` — Patient portal (demographics, emergency contacts, self-reported baseline, QR studio).
  2. `/portal/doctor` — Doctor portal (gated by `is_approved_doctor()`, multi-modal search, persistent read-only safety banner N2, clinical record editor with optimistic concurrency).
  3. `/emergency/[token]` — Public zero-login emergency triage page (N1: strictly through RPC `get_emergency_triage_by_token`, zero address/dependents, 56px sticky call button, no framer-motion).
- **Libraries**: `qrcode.react` (SVG QR), `jspdf` (CR80 printable card), `zod` (runtime validation), `lucide-react` (system icons), `framer-motion` (shared spring in portals only).
- **Testing**: `Vitest` (unit logic, schema validation, URL builder), `Playwright` (375x667 mobile and 1280x800 desktop E2E flows), `supabase/tests/rls_smoke.sql` (DB security tests).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Foundation Layers | AGENTS.md, GEMINI.md, rules (<12k), workflows, docs (SPEC.md, DECISIONS.md, PROGRESS.md) | M1 | Spec Miner 1 |
| 2 | MCP Configuration | Memory MCP, Supabase MCP, Vercel MCP configs with secure placeholders | M1 | Spec Miner 1 |
| 3 | Swarm Skills & Subagent SOP | graphify AST knowledge graph, teamwork subagent handling protocol, single-writer rule | M1 | Spec Miner 1 |
| 4 | Swarm Coordination Plan | Team-lead coordination plan, conflict avoidance rules, directory isolation matrix | M1 | Spec Miner 1 |
| 5 | QA Challenger Setup Review | Independent adversarial audit of R1 configuration, MCPs, and plans | M2 | Spec Miner 1 / R2 |
| 6 | Database Schema & Constraints | 4 core tables: accounts, patient_profiles, clinical_records, appointments | M3 | Spec Miner 2 |
| 7 | RLS Policies & Column Grants | Zero table grants to anon, authenticated column-level update grants, is_approved_doctor() | M3 | Spec Miner 2 |
| 8 | Security Definer RPCs | get_emergency_triage_by_token, submit_self_reported_baseline, regenerate_qr_token | M3 | Spec Miner 2 |
| 9 | Zero-Mock Supabase Auth | Real signUp, signInWithPassword, handle_new_user trigger, pending doctor onboarding | M4 | Spec Miner 2 |
| 10 | Environment Config & Hygiene | NEXT_PUBLIC_SUPABASE_URL and ANON_KEY only, zero service_role key leak | M3 | Spec Miner 2 |
| 11 | Patient Portal Surface | Compact bento layout, demographics form, spouse/dependents, read-only clinical overview, baseline editor | M5 | Explorer 3 |
| 12 | Doctor Portal Surface | Multi-modal search (D14), sticky read-only patient safety banner (N2), clinical editor with trigger stamps (D7) | M6 | Explorer 3 |
| 13 | Public Emergency Triage Page | Zero-login /emergency/[token] route, no address/dependents, 56px call button, zero framer-motion | M7 | Explorer 3 |
| 14 | QR Studio & ID Card Export | QRCodeSVG (level Q), 1080x1080 PNG export, 300 DPI CR80 PDF ID card, QR token rotation | M8 | Explorer 3 |
| 15 | Dual-Track 5-Tier E2E Tests | Vitest unit tests, Playwright journeys (375x667, 1280x800), Tier 5 adversarial attacks | M9 | Explorer 3 |
| 16 | Granular System Audit & Remediation | Deep-dive 28-point rated review (Security, RLS, A11y, Performance, API) and remediation | M10 | Explorer 3 / R4 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Foundation, MCPs & Swarm Setup | Establish docs/SPEC.md, MCP config, Swarm skills, and Coordination Plan | none | DONE |
| M2 | QA Challenger Setup Review & Refinement | Adversarial audit and verification of M1 assets | M1 | DONE |
| M3 | Database Schema, RLS & RPC Functions | Postgres migration, RLS policies, column grants, RPC functions, SQL security tests | M2 | DONE |
| M4 | Zero-Mock Auth & App Shell Navigation | Next.js scaffold, Supabase SSR client, login/signup flows, role guards, layout | M3 | DONE |
| M5 | Patient Portal Surface | /portal/patient, demographics form, self-reported baseline, medical overview | M4 | DONE |
| M6 | Doctor Portal Surface | /portal/doctor, approval gate, patient search, sticky safety banner, clinical editor | M4, M3 | DONE |
| M7 | Emergency Triage Route | /emergency/[token], zero-login RPC fetch, 56px sticky call button, responsive layout | M3, M4 | DONE |
| M8 | QR Studio & Printable ID Card | QRCodeSVG, PNG canvas export, 300 DPI jsPDF CR80 card, token rotation RPC | M5, M7 | DONE |
| M9 | 5-Tier Dual-Track E2E Test Suite | Vitest unit tests, Playwright user journeys, Tier 5 adversarial security suite | M5, M6, M7, M8 | DONE |
| M10 | Granular System Audit & Remediation | 28-point rated review across all subsystems, systematic fixes, green verification | M9 | DONE |

## Interface Contracts
### Public Emergency RPC: `get_emergency_triage_by_token(lookup_token uuid)`
- **Returns**: `jsonb` with keys verbatim from `rls-patterns.sql`: `full_name` (text), `contact_phone` (text), `patient_code` (text), `age` (int), `blood_group` (text), `emergency_contact_name` (text), `emergency_contact_phone` (text), `emergency_contact_relation` (text), `medical_conditions` (text[]), `current_medication` (jsonb), `previous_surgeries` (jsonb), `allergies` (text[]), `last_appointment_date` (timestamptz), `is_doctor_verified` (boolean), `updated_at` (timestamptz).
- **Prohibited**: MUST NOT return `residential_address` or `spouse_dependents`.
- **Permissions**: Revoke all on tables; GRANT EXECUTE to `anon, authenticated`.

### Doctor Safety Banner Interface Contract (N2)
- Must display in Doctor portal at all times during clinical editing:
  - Patient Full Name
  - Age
  - Blood Group
  - Primary Emergency Contact Name & Phone

### Code Layout
```text
src/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── signup/page.tsx
│   ├── portal/
│   │   ├── patient/page.tsx
│   │   └── doctor/page.tsx
│   ├── emergency/
│   │   └── [token]/page.tsx
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── ui/               # Shared UI atoms (button, input, modal, pill)
│   ├── qr/               # QR studio, canvas export, card preview
│   ├── patient/          # Patient portal cards & forms
│   └── doctor/           # Doctor search bar, safety banner, clinical form
├── lib/
│   ├── supabase/
│   │   ├── client.ts     # Client component Supabase browser client
│   │   ├── server.ts     # Server component Supabase server client
│   │   ├── middleware.ts # Edge route protection and session refresh
│   │   └── types.ts      # Generated database TypeScript types
│   ├── motion.ts         # Shared appleSpring configuration
│   ├── schemas.ts        # Zod validation schemas
│   └── utils.ts          # Safe URL builder, helper functions
│   └── pdf.ts            # CR80 printable card generator
supabase/
├── migrations/
│   └── 0001_umbrella_schema.sql
└── tests/
    └── rls_smoke.sql
docs/
├── SPEC.md
├── DECISIONS.md
├── PROGRESS.md
├── DB-RUNBOOK.md
└── DEPLOY.md
```

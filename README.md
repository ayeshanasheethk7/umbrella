# Umbrella — Emergency Medical ID Platform

Umbrella is a mission-critical, privacy-first emergency medical identification platform engineered to present vital clinical triage information to roadside first responders instantly without authentication, while providing rich, cryptographically isolated portals for patients and verified physicians.

---

## 1. Surfaces & Architecture

1. **Public Zero-Login Emergency Triage (`/emergency/[token]`)**
   - Instant zero-auth roadside triage view accessible by scanning a patient's QR code.
   - Reads data exclusively through the hardened PostgreSQL RPC `get_emergency_triage_by_token`.
   - **Invariant N1**: Strictly excludes residential address and spouse/dependents from RPC output, HTML, and client payloads.
   - Zero JavaScript animation libraries bundled (`framer-motion` prohibited per DECISIONS D13) for instantaneous rendering on low-connectivity mobile networks.
   - Prominent 56px sticky emergency call button (`tel:`) with RFC 3966 phone sanitization.

2. **Patient Portal (`/portal/patient`)**
   - Comprehensive Apple-styled 12-column bento grid workstation.
   - Demographics management, baseline medical conditions, current medications, surgical history, and dependents manager.
   - Integrated **QR Studio** offering live ISO/IEC 7810 ID-1 CR80 card preview (85.6mm x 54mm) with high-DPI 300 DPI PDF export and 1080x1080 PNG lock screen export.
   - Cryptographic token rotation via `regenerate_qr_token` RPC.

3. **Doctor Portal (`/portal/doctor`)**
   - Quadruple provider gating: Postgres RLS, Next.js middleware, page guard, and server action checks.
   - Tri-modal search classifier (patient code `UMB-XXXXXX`, UUID `qr_token`, phone number, clinician name) with PostgREST SQL injection defense.
   - **Invariant N2**: Non-dismissible, read-only sticky safety banner (`sticky top-16 z-30`) rendering patient name, age, blood group, and emergency contact at all times during clinical editing.
   - Real-time clinical record charting with optimistic timestamp concurrency locking (`expectedUpdatedAt`).
   - Consultation appointment management and status tracking.

---

## 2. Security Invariants (Non-Negotiables N1–N10)

- **N1**: `/emergency/[token]` never requires login. Data is read exclusively via RPC `get_emergency_triage_by_token`. Residential address and spouse/dependents never appear there.
- **N2**: Doctor portal always shows a read-only banner with patient name, age, blood group, and emergency contact while editing clinical records.
- **N3**: Security lives in Postgres (RLS, grants, SECURITY DEFINER functions). Server code identifies caller strictly via `supabase.auth.getUser()`, never `getSession()`. Role is verified from `public.accounts` on the server, never trusted from JWT user metadata.
- **N4**: The publishable/anon key only is used in v1. The `service_role` key is strictly forbidden across code, comments, `.env`, logs, and commits.
- **N5**: Zero mock auth: `/login` and `/signup` call genuine `supabase.auth.signInWithPassword` and `signUp`.
- **N6**: The QR value is `window.location.origin + '/emergency/' + qr_token`, computed on the client after mount.
- **N7**: Design system tokens follow Apple Human Interface Guidelines: canvas `#F5F5F7`, surface `#FFFFFF`, action `#0071E3`, critical `#FF3B30`. Zero white hairlines on white surfaces.
- **N8**: Portal animations use shared Apple spring physics (`stiffness 120, damping 20, mass 1`) and respect `prefers-reduced-motion`.
- **N9**: Synthetic data only. Zero real personal or medical data in code, seeds, tests, or screenshots.
- **N10**: Runtime Zod validation across every form submission and URL parameter. Zero `any` types.

---

## 3. Database Architecture & RLS Security Model

PostgreSQL 15+ hosted on Supabase enforces multi-tenant defense-in-depth:

- **Tables**:
  - `accounts`: Identity records, authentication roles (`patient`, `doctor`), contact information, and verification status.
  - `patient_profiles`: Patient codes (`UMB-XXXXXX`), unique emergency UUID `qr_token`, ICE contacts, age, blood group, and residential address.
  - `clinical_records`: Medical conditions, allergies, medications, surgeries, and doctor verification stamps.
  - `appointments`: Scheduled clinical consultations between approved doctors and registered patients.
- **Row-Level Security Policies**:
  - RLS enabled on all 4 tables with zero `DELETE` policies (immutable clinical audit trail).
  - Patient self-access isolated via `(select auth.uid()) = patient_id`.
  - Doctor clinical access gated strictly through `public.is_approved_doctor()` SECURITY DEFINER function.
  - Anon role has zero table grants (`revoke all on public.<tables> from anon`). Public route accesses data only via `get_emergency_triage_by_token` RPC.
  - Column-level privileges prevent updating `role`, `doctor_status`, `patient_code`, or `qr_token` from authenticated clients.
  - Trigger `trg_stamp_clinical` advances timestamps, enforces doctor verification, and records `last_updated_by_doctor_id`.

---

## 4. Repository & Directory Layout

```
medi_qr/
├── src/
│   ├── app/                      # Next.js App Router surfaces
│   │   ├── (auth)/               # Authentication routes (/login, /signup)
│   │   ├── emergency/[token]/    # Zero-login roadside triage route
│   │   ├── portal/
│   │   │   ├── doctor/           # Doctor workstation & pending view
│   │   │   └── patient/          # Patient medical profile & bento dashboard
│   │   ├── globals.css           # Apple design system CSS variables
│   │   ├── layout.tsx            # Root application shell & navigation
│   │   └── page.tsx              # Public landing page with triage lookup
│   ├── components/               # Modular UI presentation layers
│   │   ├── auth/                 # Form components (patient-signup, doctor-signup)
│   │   ├── doctor/               # Safety banner, clinical editor, workspace
│   │   ├── emergency/            # Triage view, vitest, allergies alert, call bar
│   │   ├── patient/              # Bento cards, baseline editor, demographics
│   │   ├── qr/                   # QR studio, CR80 card preview, export modal
│   │   └── ui/                   # Shared design system components (Card, Button, Tabs)
│   └── lib/                      # Core business logic & utilities
│       ├── motion.ts             # Apple spring transition physics (N8)
│       ├── qr-export.ts          # ISO CR80 300 DPI PDF & PNG generators
│       ├── schemas.ts            # 15 strict Zod validation schemas (N10)
│       ├── supabase/             # Typed SSR client, middleware, anon RPC client
│       └── utils.ts              # CSS class merging, RFC 3966 tel sanitization
├── supabase/
│   ├── migrations/               # PostgreSQL schema, RLS, triggers & RPCs
│   └── tests/                    # SQL RLS smoke test suites
├── scripts/                      # Verification and penetration test harnesses
└── docs/                         # Specifications, decisions, progress, and runbooks
```

---

## 5. Technology Stack

- **Framework**: Next.js App Router (React 19 / Server Components by default)
- **Language**: TypeScript (strict mode, zero untyped bypasses)
- **Styling**: Tailwind CSS with custom Apple design tokens
- **Database & Auth**: Supabase (PostgreSQL, Row-Level Security, Auth)
- **QR Code & Export**: `qrcode.react` (SVG level Q), `jspdf` (300 DPI CR80 PDF export)
- **Validation**: Zod (15 exhaustive runtime schemas)
- **Testing**: Vitest (Unit / Pure Logic), Playwright (E2E Integration & Scenarios), Python (Adversarial Penetration Suites)

---

## 6. Verification & Testing

Umbrella features a 5-tier, dual-track automated test harness comprising 206 tests across 8 suites:

```bash
# Run multi-milestone regression suites
python scripts/verify_m4.py   # Auth, Shell & Security (51 checks)
python scripts/verify_m5.py   # Patient Portal Bento Grid (74 checks)
python scripts/verify_m6.py   # Doctor Portal & Search Precedence (38 checks)
python scripts/verify_m7.py   # Roadside Emergency Triage Route (42 checks)
python scripts/verify_m8.py   # QR Studio & 300 DPI CR80 PDF (43 checks)
python scripts/verify_m9.py   # 5-Tier E2E Test Suite Harness (52 checks)
python scripts/adversarial_challenge_m9.py # Tier 5 Security Penetration (14 vectors)
python scripts/audit.py       # Rule 12k Character Budget & System Integrity
```

---

## 7. Development & Deployment

```bash
# Install dependencies
npm install

# Start local development server
npm run dev

# Run type check
npm run typecheck

# Build for production
npm run build
```

See [docs/DEPLOY.md](docs/DEPLOY.md) for Vercel production deployment and [docs/DB-RUNBOOK.md](docs/DB-RUNBOOK.md) for Supabase database migrations.

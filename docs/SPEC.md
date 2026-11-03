# Umbrella Master Technical Specification v2.0

## 1. Executive Overview
Umbrella is a zero-login emergency medical ID platform designed for rapid roadside triage and clinical continuity. It bridges acute first-responder access with verified healthcare provider updates:
- **Zero-Login Roadside Triage (`/emergency/[token]`)**: High-speed, unauthenticated emergency view reading strictly through security-definer RPC `get_emergency_triage_by_token`. Delivers life-critical triage indicators (blood group, critical allergies, medications, emergency contacts) while strictly omitting residential addresses and family dependents.
- **Patient Portal (`/portal/patient`)**: Bento-layout interface allowing patients to manage baseline self-reported health history, emergency contacts, dependents, and generate physical/digital QR credentials via QR Studio.
- **Doctor Portal (`/portal/doctor`)**: Clinical management interface guarded by `is_approved_doctor()`, featuring multi-modal patient search, persistent safety banner (N2), optimistic concurrency editing, and appointment management.

## 2. System Architecture & Tech Stack
- **Framework**: Next.js 14 App Router, TypeScript (strict, `noUncheckedIndexedAccess`), React 18, Tailwind CSS.
- **Backend & Auth**: Supabase Postgres with Row Level Security (RLS), `@supabase/ssr` cookie-based auth, `@supabase/supabase-js`.
- **Motion & Primitives**: `framer-motion` (shared `appleSpring` for portals; zero motion on `/emergency`), Lucide React icons.
- **QR & Export**: `qrcode.react` (SVG, Level Q), `jspdf` (300 DPI CR80 printable card).
- **Validation & Runtime**: `zod` for schemas, Vitest for unit logic, Playwright for responsive E2E tests.

## 3. Data Architecture, Flow & RBAC Matrix
### 3.1 Data Flow
1. Patient signs up -> auth trigger `handle_new_user` populates `accounts` and `patient_profiles` with unique `patient_code` and `qr_token`. Trigger creates empty `clinical_records`.
2. Patient edits demographics -> direct table update permitted only on explicitly granted columns.
3. Patient submits initial baseline -> executed via RPC `submit_self_reported_baseline` while `is_doctor_verified` is false.
4. Clinician reviews patient -> multi-modal lookup locates patient. Clinical updates stamp `is_doctor_verified = true` and `last_updated_by_doctor_id = auth.uid()` via trigger.
5. First responder scans QR -> hits `/emergency/[token]`, invoking `get_emergency_triage_by_token(token)`.

### 3.2 RBAC Matrix
| Role / Actor | Public Emergency Route | Patient Profile | Clinical Record | Appointments |
|---|---|---|---|---|
| **Anon (Public)** | RPC triage read only | No access | No access | No access |
| **Patient (Owner)** | Can view own URL | Read / Update own demographics | Read own; RPC baseline | Read own |
| **Pending Doctor** | Standard public view | No patient access | No patient access | No patient access |
| **Approved Doctor** | Standard public view | Read all patients | Read / Update & Verify | Insert / Update own |

## 4. Supabase Database Schema, Security & RPCs
### 4.1 Schema Tables
- `accounts`: `id` (uuid, PK, ref auth.users), `email`, `role` (user_role enum: 'patient', 'doctor'), `full_name`, `contact_phone`, `medical_license_number`, `specialization`, `doctor_status` ('pending', 'approved', 'rejected'), `created_at`, `updated_at`.
- `patient_profiles`: `patient_id` (uuid, PK, ref accounts), `patient_code` (text, unique, 'UMB-XXXXXX'), `qr_token` (uuid, unique), `age` (int), `blood_group` (text), `emergency_contact_name`, `emergency_contact_phone`, `emergency_contact_relation`, `spouse_dependents` (jsonb), `residential_address` (text, not null default ''), `created_at`, `updated_at`.
- `clinical_records`: `patient_id` (uuid, PK, ref accounts), `medical_conditions` (text[]), `current_medication` (jsonb), `previous_surgeries` (jsonb), `allergies` (text[]), `is_doctor_verified` (bool), `last_updated_by_doctor_id` (uuid), `last_appointment_date`, `last_appointment_summary`, `created_at`, `updated_at`.
- `appointments`: `id` (uuid, PK), `patient_id` (uuid, ref accounts), `doctor_id` (uuid, ref accounts, on delete restrict), `scheduled_at`, `status` ('scheduled', 'completed', 'cancelled'), `reason`, `clinical_notes`, `created_at`, `updated_at`.

### 4.2 Security Definer Functions & RPCs
1. `is_approved_doctor()`: Stable function checking if caller account has `role = 'doctor'` and `doctor_status = 'approved'`.
2. `get_emergency_triage_by_token(lookup_token uuid)`: Returns triage jsonb (`full_name`, `contact_phone`, `patient_code`, `age`, `blood_group`, `emergency_contacts`, `medical_conditions`, `current_medication`, `previous_surgeries`, `allergies`, `last_appointment_date`, `is_doctor_verified`, `updated_at`). NEVER returns address or spouse/dependents.
3. `submit_self_reported_baseline(p_conditions text[], p_allergies text[])`: Allows unverified patients to submit initial conditions/allergies.
4. `regenerate_qr_token()`: Rotates caller's `qr_token` to new random UUID, immediately invalidating old physical prints.

## 5. Design System & Design Tokens
Apple-inspired design language emphasizing legibility, restrained hierarchy, and high contrast.

```css
:root {
  --bg-canvas: #f5f5f7;
  --bg-surface: #ffffff;
  --bg-glass: rgba(255, 255, 255, 0.72);
  --text-primary: #000000;
  --text-secondary: #86868b;
  --text-body-secondary: #6e6e73;
  --border-hairline: 1px solid rgba(0, 0, 0, 0.1);
  --accent-action: #0071e3;
  --clinical-critical: #ff3b30;
  --clinical-critical-text: #d70015;
  --clinical-verified: #34c759;
  --clinical-verified-text: #1d7a37;
  --clinical-pending: #ff9f0a;
  --clinical-pending-text: #8a5200;
}

[data-theme="dark"] {
  --bg-canvas: #000000;
  --bg-surface: #1d1d1f;
  --bg-glass: rgba(0, 0, 0, 0.72);
  --text-primary: #f5f5f7;
  --text-secondary: #86868b;
  --border-hairline: 1px solid rgba(255, 255, 255, 0.1);
}
```

- **Typography**: System font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`). Hero: weight 700, tracking -0.03em. Headings: weight 600, tracking -0.022em.
- **Motion**: `appleSpring` (`{ type: "spring", stiffness: 120, damping: 20, mass: 1 }`).
- **Emergency Route Exception**: Pure CSS transforms only; zero `framer-motion` bundle inclusion.

## 6. Surfaces & User Journeys
### 6.1 Marketing Landing (`/`)
Editorial layout with 120-160px vertical spacing, interactive 3D-tilting emergency ID demo card, sticky scroll feature story, and trust signals. Single primary CTA routes to `/signup?role=patient`.

### 6.2 Authentication (`/login`, `/signup`)
Real Supabase Auth (`signInWithPassword`, `signUp`). SegmentedControl toggles Patient vs Doctor intent. Doctor signup enforces pending status. Strict Zod input validation.

### 6.3 Patient Portal (`/portal/patient`)
Compact bento grid (24px padding, 16px gap). Includes Top Bar with patient code copy, QR Studio (QRCodeSVG level Q, PNG 1080x1080 export, 300 DPI CR80 PDF ID card, token rotation), Demographics Form (with spouse/dependents dynamic list), and Read-Only Clinical Summary.

### 6.4 Doctor Portal (`/portal/doctor`)
Restricted to approved doctors. Multi-modal patient lookup (code, token, phone, name with 300ms debounce). Persistent sticky safety banner (N2). Clinical editor with dirty-state tracking, optimistic concurrency, and trigger-enforced verification stamps. Appointments manager with status updates.

### 6.5 Public Emergency Triage (`/emergency/[token]`)
Zero-login, light theme forced, high-contrast Server Component. Triage indicators above the fold at 375x667: verification badge, patient name/age, blood group pill, allergies alert, and 56px sticky emergency call button (`tel:`).

## 7. Code Layout & Directory Structure
```text
src/
├── app/
│   ├── (marketing)/page.tsx
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── signup/page.tsx
│   ├── portal/
│   │   ├── patient/page.tsx
│   │   └── doctor/page.tsx
│   ├── emergency/
│   │   └── [token]/page.tsx
│   ├── layout.tsx
│   └── globals.css
├── components/
│   ├── ui/               # Button, Input, Modal, Badge, BloodGroupPill
│   ├── qr/               # QRStudio, CanvasExport, CardPreview
│   ├── patient/          # DemographicsForm, ClinicalSummary
│   └── doctor/           # LookupBar, SafetyBanner, ClinicalEditor
├── lib/
│   ├── supabase/
│   │   ├── client.ts     # Client component Supabase browser client
│   │   ├── server.ts     # Server component Supabase server client
│   │   ├── anon.ts       # Cookie-less server client for public emergency route
│   │   └── types.ts      # Generated database TypeScript types
│   ├── motion.ts         # Shared appleSpring configuration
│   ├── schemas.ts        # Zod validation schemas
│   ├── utils.ts          # Safe URL builder, helper functions
│   └── pdf.ts            # CR80 printable card generator
supabase/
├── migrations/
│   └── 0001_umbrella_schema.sql
├── seed.sql
└── tests/
    └── rls_smoke.sql
docs/
├── SPEC.md
├── DECISIONS.md
├── PROGRESS.md
├── DB-RUNBOOK.md
└── DEPLOY.md
```

## 8. Quality, Hardening & Verification Checklist
1. **Check 1: Security & RLS**: Anon has zero table grants; RPC is the only public triage gate; doctor approval enforced server-side via `is_approved_doctor()`.
2. **Check 2: Privacy Hygiene**: Residential address and spouse/dependents are excluded from `/emergency/[token]` RPC, HTML, and JSON responses.
3. **Check 3: Responsive UI**: Verified at 375x667 (mobile) and 1280x800 (desktop); critical emergency data visible above the fold without horizontal overflow.
4. **Check 4: Design Token Compliance**: Strict token usage; zero raw hex colors outside `globals.css`; WCAG AA contrast compliance.
5. **Check 5: QR Reliability**: Client-computed origin post-mount in `useEffect`; Level Q error correction; calm amber non-blocking warning on non-production origins.
6. **Check 6: Performance & JS Budget**: Route `/emergency/[token]` ships under 120KB gzipped JS, zero framer-motion, zero qrcode.react, zero jspdf.

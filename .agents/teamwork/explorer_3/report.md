# Comprehensive Exploration Report: Umbrella Platform Surfaces, QR Studio, Design System, Testing & R4 Audit Criteria

**Author**: Explorer 3 (`teamwork_explorer`)  
**Target File**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_3\report.md`  
**Date**: 2026-11-01  
**Authoritative References**: `UMBRELLA_BUILD_KIT.md`, `AGENTS.md`, `GEMINI.md`, `docs/DECISIONS.md`, `docs/PROGRESS.md`, `.agents/rules/*`, `.agents/skills/*`, `.agents/workflows/*`

---

## 1. Executive Summary

Umbrella is a mission-critical, emergency medical ID platform designed with three core application surfaces:
1. **Patient Portal (`/portal/patient`)**: Patient-managed emergency ID, demographics, spouse/dependents, read-only clinical overview, self-reported baseline submission, and the interactive QR Studio.
2. **Doctor Portal (`/portal/doctor`)**: Secure clinician workspace featuring multi-modal patient lookup, sticky read-only patient safety banner, clinical record editor with trigger-enforced verification, and appointment management.
3. **Emergency Triage Page (`/emergency/[token]`)**: Public, zero-login, high-speed emergency interface accessible via scannable QR code, reading strictly through the security-definer RPC `get_emergency_triage_by_token`, stripping sensitive residential and dependent data, and operating under a strict zero-framer-motion, minimal bundle performance budget.

This report establishes the complete specification across the 5 mandated investigation areas: Application Surfaces, QR Studio & ID Card Export, UI Design System & Accessibility, 5-Tier Testing Architecture (Tiers 1-4 Opaque-Box, Tier 5 Adversarial), and Granular System Audit Criteria for R4.

---

## 2. Focus Area 1: Application Surfaces & Routes Specification

### 2.1 Architectural Surface Matrix

| Surface | Route Path | Access / Auth Level | Data Access Mechanism | Core Components |
|---|---|---|---|---|
| **Marketing Landing** | `/` (`(marketing)/page.tsx`) | Public (unauthenticated) | Static / Client | Hero with 3D tilting ID card, 3-step scroll story, trust signals |
| **Auth Pages** | `/login`, `/signup` | Public (redirects if authenticated) | `supabase.auth` SSR | SegmentedControl (Patient/Doctor), zod validation, signup trigger handling |
| **Patient Portal** | `/portal/patient` | Authenticated `role='patient'` | Server Component (`Promise.all` over tables) | GlassNav, Bento layout, QR Studio, Demographics Form, Clinical Summary |
| **Doctor Portal** | `/portal/doctor` | Authenticated `role='doctor'` & `doctor_status='approved'` | Parameterized query via server actions / RPC | GlassNav with Lookup Bar, Sticky Patient Safety Banner, Clinical Editor, Appointments |
| **Emergency Triage** | `/emergency/[token]` | Public (Zero-Login, No Auth) | RPC `get_emergency_triage_by_token(uuid)` ONLY | Server Component, Light Theme Forced, Verified/Self-Reported Badge, Allergies Alert, Sticky Call Bar (56px) |

---

### 2.2 Patient Portal (`/portal/patient`)

#### Layout & Navigation
- **Layout Paradigm**: Compact bento grid layout with 24px outer page padding and 16px component gaps.
- **Top Bar (`GlassNav`)**:
  - Displays authenticated patient full name (`accounts.full_name`).
  - Displays unique patient code `UMB-XXXXXX` alongside a one-click copy button.
  - Interactive `SignOutButton` calling `supabase.auth.signOut()` and routing to `/login`.
- **Mobile Bento Stacking Order (375x667 Viewport)**:
  1. Module 1: QR Studio
  2. Module 2: Clinical Summary (Read-Only Overview)
  3. Module 3: Demographics & Emergency Contacts Form

#### Demographics & Dependents Form (`src/components/patient/`)
- **Granular Data Fields**:
  - Primary Identity: `full_name`, `contact_phone` (stored in `public.accounts`; column-level grant restricted).
  - Demographics: `age` (integer), `blood_group` (strict 8-group enum: `A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `O+`, `O-`, `Unknown`).
  - Emergency Contact: `emergency_contact_name`, `emergency_contact_phone`, `emergency_contact_relation`.
  - Dependents / Spouse: Dynamic JSONB array (`spouse_dependents`): array of objects `{ name: string, relation: string, age: number, phone: string }`, max 10 entries with add/remove row controls.
  - Home Address: `residential_address` (`text not null default ''`).
- **Data Protection Guarantee (Non-negotiable N1)**:
  `residential_address` and `spouse_dependents` are strictly confined to the patient and approved doctor portals. They NEVER appear in the emergency RPC payload, HTML markup, or JSON responses.
- **Form UX & Mutation Hygiene**:
  - Controlled components backed by Zod schemas.
  - Per-card Save buttons with inline success/error feedback.
  - Submits only dirty fields and writes only to explicitly granted columns.

#### Clinical Summary & Self-Reported Baseline
- **Verification Status Indicator**:
  - If `clinical_records.is_doctor_verified = true`: Renders green verified badge (`--clinical-verified #34c759`, `--clinical-verified-text #1d7a37`) displaying "Doctor Verified" and timestamp of verification.
  - If `false`: Renders amber pending badge (`--clinical-pending #ff9f0a`, `--clinical-pending-text #8a5200`) displaying "Self-Reported (Pending Doctor Verification)".
- **Read-Only Clinical Cards**:
  - Allergies list (high-visibility chips).
  - Active Medical Conditions list.
  - Current Medications: Name, dosage, frequency.
  - Previous Surgeries: Procedure name, year, clinical notes.
  - Last Appointment: Timestamp and doctor summary.
  - Upcoming Scheduled Appointments: Date, reason, attending physician name & specialization.
- **Self-Reported Baseline Submission (DECISIONS D7)**:
  - Accessible ONLY while `is_doctor_verified = false`.
  - Enables patient to input conditions and allergies via `TagInput`.
  - Dispatches via RPC `submit_self_reported_baseline(p_conditions text[], p_allergies text[])`.
  - Once verified by a clinician, the baseline editor unmounts completely, displaying: *"Your clinical record is managed by your doctor."*

---

### 2.3 Doctor Portal (`/portal/doctor`)

#### Access Gate & States
- Authenticated via `supabase.auth.getUser()`, cross-referencing `public.accounts` on the server.
- **Pending / Rejected State**: If `doctor_status = 'pending'` or `'rejected'`, renders a dedicated "Verification Pending" screen. Zero patient records can be read or queried.
- **Approved State**: If `public.is_approved_doctor()` evaluates true, full clinician workspace renders.

#### Multi-Modal Patient Lookup Bar (DECISIONS D14)
- **Input Classification Algorithm**:
  1. Matches pattern `/^UMB-[A-Z0-9]{6}$/i` -> Exact match query on `patient_profiles.patient_code`.
  2. Matches UUID regex -> Exact lookup on `patient_profiles.qr_token`.
  3. Contains 7+ numeric digits -> Substring search on `accounts.contact_phone`.
  4. Otherwise -> Case-insensitive wildcard search `full_name ILIKE '%query%'`.
- **Search Constraints**:
  - Minimum query length: 2 characters.
  - Input debounce: 300ms.
  - Query parameterization: Separate parameterized queries; strictly NO raw `.or()` or SQL string concatenation. All special SQL characters (`%`, `_`, `,`, `(`, `)`) escaped.
  - Maximum results: 20 records, each presenting Name, Code, Age, and Blood Group pill.
  - Deep-link synchronization: URL state bound to `?patient=<patient_code>` and `?patient_token=<uuid>` (supporting emergency escalation).

#### Sticky Patient Safety Banner (Non-negotiable N2)
- **Mandatory Safety Rule**: A persistent, read-only context banner MUST remain pinned to the top of the viewport during all clinical data entry.
- **Banner Contents**:
  - Patient Full Name and Age
  - Blood Group (prominent pill badge)
  - Patient Contact Phone
  - Emergency Contact: Name, Relation, Phone number (formatted with direct `tel:` link)
  - Spouse & Dependents summary
  - Residential Home Address

#### Clinical Record Editor (`src/components/doctor/`)
- **Clinical Input Modules**:
  - Allergies manager: `TagInput` for rapid entry/removal.
  - Medical Conditions: Structured list editor.
  - Current Medications: Dynamic tabular rows (medication name, dosage, frequency, optional prescriber).
  - Previous Surgeries: Dynamic rows (procedure title, calendar year, operative notes).
- **Integrity & Verification Stamp (DECISIONS D7)**:
  - Single primary action: "Save & Verify".
  - Submits updates to the 4 granted columns (`medical_conditions`, `current_medication`, `previous_surgeries`, `allergies`).
  - Postgres `BEFORE UPDATE` trigger `stamp_clinical_update()` automatically forces `is_doctor_verified = true` and records `last_updated_by_doctor_id = auth.uid()`. Client cannot forge verification.
  - Pre-fills unverified self-reported baseline with notice: *"Review and save to verify"*.
  - Post-save confirmation banner: *"Verified by you just now"*.
- **Optimistic Concurrency Control**:
  - Clinical update payload includes loaded `updated_at` timestamp in the WHERE clause.
  - If zero rows updated, displays concurrency conflict warning: *"This record changed since you opened it. Reload."*

#### Doctor Appointments Manager
- Upcoming vs. Past appointment tabs.
- Appointment booking modal: `datetime-local` input (local timezone converted to UTC), mandatory reason, validation constraint requiring future timestamp.
- Appointment actions: Mark Completed (captures clinical notes) and Cancel (confirmation modal).
- Completion Hook (DECISIONS D8): Trigger `on_appointment_completed()` syncs `last_appointment_date` and `last_appointment_summary` into `clinical_records` without changing verification status.

---

### 2.4 Emergency Triage Route (`/emergency/[token]`)

#### Public Delivery Hygiene (Non-negotiable N1, DECISIONS D9, D13)
- **Zero-Login Protocol**: Completely unauthenticated route. Reads data EXCLUSIVELY via `get_emergency_triage_by_token(lookup_token uuid)`.
- **Database Client**: Utilizes stateless, cookie-less anonymous client (`src/lib/supabase/anon.ts`).
- **Next.js Route Configuration**:
  ```typescript
  export const dynamic = 'force-dynamic';
  ```
- **Security Headers & Crawl Directives**:
  - `Cache-Control: no-store`
  - `Referrer-Policy: no-referrer`
  - `robots: noindex, nofollow`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- **Token Validation**: Zod UUID validation executed before database invocation. Any invalid format or unknown token triggers generic Next.js `notFound()`.
- **Route `not-found.tsx`**: Plain, friendly copy: *"This emergency ID was not found. Ask the person to open Umbrella and share their QR again."* Zero diagnostic disclosure.

#### Mobile Viewport Above-The-Fold Priority (375x667 Viewport)
Critical emergency triage information must appear in strict visual order without vertical scrolling:
1. **Header Banner**: "EMERGENCY MEDICAL ID" title paired with verification badge ("Doctor Verified" green pill or "Patient Self-Reported" amber pill).
2. **Patient Vital Header**: Full Name and Age (rendered with weight 700, tracking `-0.03em`).
3. **Blood Group Pill**: Extra-large (`xl`) high-contrast indicator.
4. **Critical Allergies Alert Box**: High-alert banner styled with `--clinical-critical #ff3b30`. If empty, renders neutral copy: *"No known allergies recorded"* (never wording implying immunity or absence).
5. **Sticky Action Call Bar**: Fixed bottom bar, exactly 56px touch target height, rendering:
   `Call Emergency Contact: [Name] ([Relation])` configured as `<a href="tel:+digits">`.

#### Below-The-Fold Clinical Cards
- Active Medical Conditions
- Current Medications (Name, dosage, schedule)
- Previous Surgeries (Procedure, year, notes)
- Timestamp details: Last clinical record update and last doctor visit date.
- Empty states on missing records: *"Nothing recorded"*.

#### Clinician Escalation Footer & Fast Path (DECISIONS D15)
- Public footer link: *"Are you the treating physician? Log in to update clinical record"* linking to `/portal/doctor?patient_token=<token>`.
- Doctor Session Detection: An asynchronous server cookie check identifies active clinician sessions. If verified, renders top bar: *"Edit Clinical Record in Doctor Portal"*.
- Fail-Safe Isolation: Clinician session detection must NEVER block, delay, or fail the public emergency render.

---

## 3. Focus Area 2: QR Studio & ID Card Export Specifications

### 3.1 Token & Origin URL Computation (Non-negotiable N6, DECISIONS D12)
- **URL Formulation**:
  ```typescript
  export function buildEmergencyUrl(origin: string, token: string): string {
    const cleanOrigin = origin.replace(/\/+$/, '');
    return `${cleanOrigin}/emergency/${token}`;
  }
  ```
- **Hydration Safety**:
  Computed client-side inside `useEffect` post-mount: `buildEmergencyUrl(window.location.origin, qrToken)`.
  Renders a matched-dimension skeleton container during SSR to prevent hydration mismatches.
- **Environment Warning Banner (DECISIONS D12)**:
  If `origin` contains `localhost` or ends with `.vercel.app` (non-production host), displays a non-blocking amber advisory beneath the QR:
  *"This QR points to <origin>. Cards printed here only work while that site is online."*

---

### 3.2 Emergency QR Rendering (`qrcode.react`)
- **Package Implementation**: `QRCodeSVG` imported from `qrcode.react`.
- **Render Specifications**:
  - Error correction: `level="Q"` (25% recovery capacity, protecting against card scratching or folding).
  - Margin: `marginSize={4}` quiet zone.
  - Colors: Foreground `#000000`, Background `#ffffff`. Black-on-white rendering is mandatory across light and dark modes to ensure optical scanner fidelity.
  - Sizing: Minimum on-screen box size 224x224px on mobile viewports; strict 1:1 aspect ratio.

---

### 3.3 High-Resolution PNG Export (Lockscreen / Digital Wallet)
- **Canvas Generation Pipeline**:
  1. Offscreen canvas initialized to exactly `1080 x 1080` pixels.
  2. Canvas context filled with solid white `#ffffff` background.
  3. QR code SVG serialized via `new XMLSerializer().serializeToString(svgElement)`.
  4. Encoded into an SVG Blob URL (`data:image/svg+xml;charset=utf-8,...` or `URL.createObjectURL`).
  5. Image loaded asynchronously onto the offscreen canvas, centered at dimensions `840 x 840` pixels.
  6. Text overlays rendered below QR:
     - Header label: "EMERGENCY MEDICAL ID"
     - Patient full name
     - Patient code identifier (`UMB-XXXXXX`)
  7. Export triggered via `canvas.toBlob('image/png')` -> temporary object URL -> programmatic anchor click -> `URL.revokeObjectURL()`.
- **Output Filename Pattern**: `umbrella-emergency-id-<patient_code>.png`.

---

### 3.4 Printable Physical ID Card Export (`jspdf`)
- **Physical Form Factor**: Standard CR80 wallet card dimensions: `85.6 mm x 54.0 mm` (landscape).
- **Document Structure**: Two-page document generated with `jspdf` (`orientation: 'landscape', unit: 'mm', format: [85.6, 54.0]`).
- **Card Layout Architecture**:
  - **Front Face (Page 1)**:
    - Prominent label: "EMERGENCY MEDICAL ID".
    - Patient full name (bold header).
    - Blood Group Pill (large visual indicator).
    - Patient Code `UMB-XXXXXX`.
    - High-density QR code situated on the right quadrant (~30mm width).
    - Explanatory caption: *"Scan for medical info. No login needed."*
  - **Back Face (Page 2)**:
    - Header: *"In an emergency call:"*
    - Emergency contact name, relationship, and sanitized phone number.
    - Full fallback emergency URL printed in small monospace text.
  - **Privacy Redaction Rule**: Strictly NO residential home address or spouse/dependents printed on either card face.
- **300 DPI High-Density Rasterization**:
  - Physical mm dimensions converted to 300 DPI pixels:
    - Width: `85.6 mm * (300 / 25.4) = 1011 pixels`.
    - Height: `54.0 mm * (300 / 25.4) = 638 pixels`.
  - Both card faces rendered to offscreen HTML5 canvases at `1011 x 638 px` using standard system sans-serif typography.
  - Canvases converted to PNG data streams and injected into PDF via `doc.addImage(imgData, 'PNG', 0, 0, 85.6, 54.0)`.
- **Output Filename Pattern**: `umbrella-emergency-card-<patient_code>.pdf`.

---

### 3.5 Token Rotation & Regeneration Workflow
- **Regenerate Button Trigger**: Triggers `ConfirmDialog` accessible modal.
- **Confirmation Copy**:
  *"Your current QR code will stop working immediately. Printed or saved copies will show 'not found'. Continue?"*
- **Execution Lifecycle**:
  1. Invokes Supabase RPC: `supabase.rpc('regenerate_qr_token')`.
  2. Database generates fresh `gen_random_uuid()` in `patient_profiles.qr_token` for the authenticated caller.
  3. Client receives new token, updates local state, and immediately redraws QR code and preview URL.
  4. Old QR token immediately becomes invalid (returns null / 404 from emergency RPC).
  5. UI displays warning banner instructing patient to discard old prints and export new cards.

---

## 4. Focus Area 3: Design Tokens, Responsive Breakpoints, Accessibility, Motion

### 4.1 Token Architecture & Contrast Compliant Palette (Rule 01, DECISIONS D10)
Defined as CSS variables in `src/app/globals.css` and exposed via Tailwind v4 `@theme`:

```css
:root {
  /* Surfaces & Canvas */
  --bg-canvas: #f5f5f7;
  --bg-surface: #ffffff;
  --bg-glass: rgba(255, 255, 255, 0.72);

  /* Typography */
  --text-primary: #000000;
  --text-secondary: #86868b;        /* Large or decorative text ONLY */
  --text-body-secondary: #6e6e73;   /* WCAG AA compliant for all text < 18px (D10) */

  /* Hairline Borders */
  --border-hairline: 1px solid rgba(0, 0, 0, 0.1);

  /* Brand Action */
  --accent-action: #0071e3;

  /* Clinical Semantics */
  --clinical-critical: #ff3b30;      /* Alert fills, bold badges 20px+ */
  --clinical-critical-text: #d70015; /* Small critical text (WCAG AA compliant, D10) */
  --clinical-verified: #34c759;      /* Verified fill/icon */
  --clinical-verified-text: #1d7a37; /* Verified text (WCAG AA compliant, D10) */
  --clinical-pending: #ff9f0a;       /* Self-reported fill/icon */
  --clinical-pending-text: #8a5200;  /* Self-reported text (WCAG AA compliant, D10) */

  /* System Typography */
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
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

#### Border & Shadow Ceiling Constraints
- **Hairline Rule**: Light surfaces must strictly use `rgba(0,0,0,0.1)`. Dark surfaces use `rgba(255,255,255,0.1)`. NEVER render a white hairline on a white surface.
- **Shadow Ceiling**: `box-shadow: 0 1px 2px rgba(0,0,0,0.04), 0 8px 24px rgba(0,0,0,0.06)`. Heavy, diffuse, or neon drop-shadows are strictly forbidden.

---

### 4.2 Responsive Breakpoints & Route Spacing

| Breakpoint / Resolution | Target Device Benchmark | Layout Behavior |
|---|---|---|
| **375 x 667 px** | Mobile (iPhone SE) | Single column, compact bento, critical emergency triage strictly above the fold, 56px sticky call bar |
| **768 px** | Tablet / Mid-size | Two-column responsive bento grid |
| **1280 x 800 px** | Desktop (Standard laptop) | Multi-column bento, doctor portal side-by-side workspace |

#### Spacing Standards by Route (SPEC Section 8 Check 4)
- **Marketing (`/`)**: 120px to 160px vertical padding between sections. Editorial hierarchy with a single focal visual per section.
- **Portals (`/portal/*`)**: 24px outer page padding, 16px internal grid gaps.
- **Emergency (`/emergency/[token]`)**: 24px padding (condenses to 16px if viewport width < 360px).

---

### 4.3 Accessibility Standards (WCAG 2.1 AA Baseline)
- **Touch Target Sizing**:
  - Standard interactive elements (buttons, inputs, segmented tabs): Minimum `44 x 44 px`.
  - Emergency Call Action Bar: Minimum `56 px` height.
- **Focus Rings**: Visible `2px` `--accent-action` ring with `2px` offset on `:focus-visible`. Tab-navigable without pointer device.
- **Multi-Modal Signaling**: Semantic color is NEVER the sole carrier of meaning. Every status badge must include both an SVG icon and clear text (e.g., Doctor Verified badge includes check icon + text).
- **Form Usability**:
  - Input text minimum `16px` font size to prevent iOS Safari auto-zooming.
  - Permanent visible labels coupled with `aria-describedby` for inline validation messages.
- **Dialog Accessibility**: Modals include focus traps, `Esc` dismissibility, backdrop click dismissal, `aria-modal="true"`, and automatic focus return to trigger elements upon exit.

---

### 4.4 Motion Constraints (`src/lib/motion.ts`)
- **Shared Apple Spring Configuration**:
  ```typescript
  export const appleSpring = {
    type: "spring",
    stiffness: 120,
    damping: 20,
    mass: 1,
  };
  ```
- **Global Reduced Motion**: Application root wrapped in `<MotionConfig reducedMotion="user" transition={appleSpring}>`.
- **Micro-Interactions**:
  - Buttons: `whileHover: { scale: 1.015 }`, `whileTap: { scale: 0.98 }`.
  - Pure color and opacity transitions: 150ms `ease-out`.
  - Movement: Springs only; CSS `ease-in-out` is strictly forbidden.
- **EMERGENCY ROUTE ZERO-MOTION EXCEPTION (DECISIONS D13, AGENTS N8)**:
  The emergency triage route (`/emergency/[token]`) ships ZERO framer-motion library code. Press feedback on the call button is implemented strictly via CSS `:active { transform: scale(0.98); }`.

---

## 5. Focus Area 4: Testing Specifications & 5-Tier Testing Architecture

### 5.1 Test Frameworks & Execution Commands
- **Unit & Logic Runner**: Vitest (`npm run test` -> `vitest run`).
- **End-to-End Browser Runner**: Playwright (`npm run test:e2e` -> `playwright test`).
- **Static Typecheck**: `npm run typecheck` (`tsc --noEmit`).
- **Linter**: `npm run lint`.
- **Full Verification Suite**:
  ```bash
  npm run typecheck && npm run lint && npm run test && npm run test:e2e && npm run build
  ```

---

### 5.2 The 5-Tier Testing Taxonomy

```
┌────────────────────────────────────────────────────────┐
│  Tier 5: Adversarial & Security Boundary Tests         │  <- Injection, RLS bypass, Privilege escalation
├────────────────────────────────────────────────────────┤
│  Tier 4: End-to-End Multi-Role Journey Tests           │  <- Playwright user flows (Patient, Doctor, Triage)
├────────────────────────────────────────────────────────┤
│  Tier 3: Component Integration & Accessibility Tests   │  <- Keyboard nav, focus traps, QR canvas lifecycle
├────────────────────────────────────────────────────────┤
│  Tier 2: Unit Logic, Transforms & Routing Matrix       │  <- buildEmergencyUrl, safeNext, classification math
├────────────────────────────────────────────────────────┤
│  Tier 1: Static Analysis, Types & Schema Invariants    │  <- tsc --noEmit, eslint, zod safeParse schemas
└────────────────────────────────────────────────────────┘
```

#### Tier 1: Static Analysis, Types & Schema Invariants (Opaque-box)
- **Strict Typing Verification**: Zero `@ts-ignore`, zero `@ts-expect-error` without written architectural justification, zero `any`. Strict mode with `noUncheckedIndexedAccess`.
- **Zod Schema Boundary Validations (`src/lib/schemas.ts`)**:
  - Blood group parser rejecting invalid strings (e.g., `'C+'`, `'O'`).
  - Age boundaries rejecting negative values or ages > 130.
  - Phone sanitizer handling E.164 formats, local Indian prefixes (+91), stripping special characters.
  - Emergency contact and dependent array limits (rejecting > 10 items).
  - Doctor lookup input sanitizer stripping `%` and SQL escape sequences.

#### Tier 2: Unit Logic, Transforms & Routing Matrix (Opaque-box)
- **URL & Origin Math (`buildEmergencyUrl`)**:
  - Normalizes trailing slashes on origin.
  - Handles IPv4 loopback (`127.0.0.1:3000`), `localhost`, and Vercel preview domains.
- **Safe Redirect Validation (`safeNext`)**:
  - Rejects protocol-relative URLs (`//evil.com`).
  - Rejects absolute URLs (`https://phishing.site`).
  - Rejects backslash escapes (`/\evil.com`).
  - Accepts only single-slash relative paths (e.g., `/portal/doctor?patient=UMB-123456`).
- **Lookup Classifier Logic**:
  - Classifies exact code, token UUID, phone digit series, and name query.
- **Card Geometry & DPI Calculations**:
  - Validates 300 DPI mm-to-pixel coordinate conversions.

#### Tier 3: Component Integration & Accessibility Tests (Opaque-box)
- **UI Component Mechanics**:
  - `SegmentedControl`: Arrow key navigation (`ArrowLeft`, `ArrowRight`), layout animation persistence.
  - `Modal` / `ConfirmDialog`: Traps focus within modal container; pressing `Escape` closes dialog and restores focus to original trigger.
  - `TagInput`: Appends chips on `Enter` or `,`; removes chips on `Backspace` or button click; enforces max tag threshold.
  - `QRStudio`: Renders hydration skeleton on initial mount; mounts `QRCodeSVG` with verified SVG dimensions; verifies blob generation lifecycle.

#### Tier 4: End-to-End Multi-Role Journey Tests (Playwright Opaque-box)
- **Patient Journey**:
  1. Signup with synthetic credentials -> Automatic redirect to `/portal/patient`.
  2. Modify emergency contact phone -> Persist -> Verify updated number reflected.
  3. Add dependent row in demographics -> Save.
  4. Submit self-reported baseline conditions and allergies.
  5. Open QR Studio -> Trigger PNG download -> Trigger PDF ID card generation.
  6. Click "Regenerate QR Link" -> Confirm modal -> Receive new token.
  7. Verify old token returns 404 in emergency triage route.
- **Doctor Journey**:
  1. Signup as doctor -> Land on "Verification Pending" screen.
  2. Elevate doctor status to `'approved'` via synthetic test harness.
  3. Search patient via code `UMB-XXXXXX` and phone number -> Load patient workspace.
  4. Verify sticky patient safety banner displays patient vitals and contact details.
  5. Add allergy and medication -> Click "Save & Verify" -> Confirm `is_doctor_verified` stamped.
  6. Schedule future appointment -> Mark appointment completed -> Verify `last_appointment_date` updated in workspace.
- **Emergency Responder Journey**:
  1. Open `/emergency/[valid_token]` in unauthenticated browser instance.
  2. Verify all vital triage indicators are rendered above the fold at 375x667.
  3. Verify sticky call button renders correct `tel:+digits` target.
  4. Inspect DOM: Verify zero instances of `residential_address` or `spouse_dependents`.
  5. Navigate to `/emergency/[random_uuid]` -> Confirm generic 404 screen.

#### Tier 5: Adversarial & Security Boundary Tests
- **Postgres RLS Attack Suite (`supabase/tests/rls_smoke.sql`)**:
  - *Privilege Escalation Attack*: Authenticated patient attempts `UPDATE public.accounts SET role = 'doctor'` -> Must fail with permission denied.
  - *Unauthorized Cross-Tenant Read*: Patient A attempts `SELECT * FROM public.patient_profiles WHERE patient_id = 'patient-B'` -> Must return 0 rows.
  - *Anon Table Infiltration*: Unauthenticated anon role attempts `SELECT * FROM public.accounts` -> Must fail with permission denied.
  - *Direct Clinical Tampering*: Patient attempts direct `UPDATE public.clinical_records` -> Must fail with permission denied.
  - *Verified Record Overwrite*: Patient invokes `submit_self_reported_baseline()` after doctor verification -> Must raise exception *"Record is already doctor-verified"*.
  - *Direct Token Tampering*: Patient attempts `UPDATE public.patient_profiles SET qr_token = gen_random_uuid()` -> Must fail with permission denied (restricted column grant).
  - *Appointment Impersonation*: Patient attempts `INSERT INTO public.appointments` -> Must fail. Doctor attempts inserting appointment with another doctor's UUID -> Must fail check constraint.
  - *Data Destruction Attack*: Authenticated user attempts `DELETE FROM public.accounts` or `clinical_records` -> Must fail with permission denied.
- **Application Layer Attacks**:
  - *Open Redirect Attack*: Submitting `/login?next=//evil.com` -> Sanitized to root portal fallback.
  - *XSS Payload Injection*: Submitting `<script>alert(1)</script>` or `<img src=x onerror=...>` in demographics or clinical notes -> Safely escaped by React without execution.
  - *Bundle Leakage Verification*: Automated build inspection verifying that `framer-motion`, `qrcode.react`, and `jspdf` are 100% absent from the `/emergency/[token]` client bundle.

---

## 6. Focus Area 5: Granular System Audit Criteria for R4

For the Milestone R4 Granular System Audit, the platform must be evaluated across five rigorous audit domains:

```
┌────────────────────────────────────────────────────────┐
│               R4 Granular System Audit                 │
├────────────┬────────────┬─────────────┬──────────────┬─┤
│  Security  │  Database  │ Accessibility│ Performance  │ │
│  & Privacy │   & RLS    │ & Responsive│   & Bundle   │ │
└────────────┴────────────┴─────────────┴──────────────┴─┘
```

### 6.1 Domain 1: Security & Privacy Audit
- [ ] **S1. Service Role Key Isolation (N4)**: Codebase search for `service_role` yields 0 hits across source code, config files, `.env.example`, git history, and documentation.
- [ ] **S2. Server Auth Identification (N3)**: Every server action, Server Component, and proxy call identifies callers using `supabase.auth.getUser()`. Zero calls to `getSession()`.
- [ ] **S3. Role & Metadata Authority (N3, D2)**: Authorization logic never relies on JWT `user_metadata` or client-supplied role parameters. Roles are read directly from `public.accounts` on Postgres.
- [ ] **S4. Zero Dangerous HTML**: Zero usage of `dangerouslySetInnerHTML` throughout application code.
- [ ] **S5. Injection Defense**: Zero dynamic string concatenation in PostgREST `.or()` or `.filter()` calls. All search inputs sanitized and parameterized.
- [ ] **S6. Emergency Data Containment (N1)**: Automated regex verification confirms `residential_address` and `spouse_dependents` are completely absent from `src/app/emergency/`.
- [ ] **S7. HTTP Security Headers (Rule 02 item 9)**: `next.config.ts` enforces `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin` (with `no-referrer` on `/emergency/*`), and restrictive `Permissions-Policy`.

### 6.2 Domain 2: Database & RLS Audit
- [ ] **D1. Universal RLS Activation**: Row Level Security enabled on 100% of public tables (`accounts`, `patient_profiles`, `clinical_records`, `appointments`).
- [ ] **D2. Zero Anon Table Privileges**: The `anon` role has 0 table permissions (`SELECT`, `INSERT`, `UPDATE`, `DELETE`). Access to emergency data is strictly mediated by the RPC function.
- [ ] **D3. Function Hardening**: All SQL functions are schema-qualified, define `SET search_path = ''`, and have explicit REVOKE/GRANT rules.
- [ ] **D4. Column-Level Grant Protection**: Write grants explicitly revoke updates to protected columns (`role`, `doctor_status`, `patient_code`, `qr_token`).
- [ ] **D5. Index Completeness**: Performance indexes exist on all foreign keys and policy evaluation columns (`appointments(patient_id, scheduled_at desc)`, `appointments(doctor_id)`, `accounts(contact_phone)`).
- [ ] **D6. Full RLS Smoke Test Pass**: `supabase/tests/rls_smoke.sql` runs to completion and logs `ALL RLS TESTS PASSED` within an isolated rollback transaction.

### 6.3 Domain 3: Accessibility & Design System Audit
- [ ] **A1. Contrast Ratio Compliance (D10)**: All foreground/background color combinations satisfy WCAG 2.1 AA (4.5:1 for normal text, 3:1 for large text). Verified tokens: `--text-body-secondary #6e6e73`, `--clinical-critical-text #d70015`, `--clinical-verified-text #1d7a37`, `--clinical-pending-text #8a5200`.
- [ ] **A2. Zero Raw Hex Values**: Zero unmapped hex codes outside `src/app/globals.css`.
- [ ] **A3. Border Contrast**: Light surfaces use `rgba(0,0,0,0.1)`. No white hairline on white surfaces.
- [ ] **A4. Touch Target Compliance**: Minimum 44x44px target on all actionable components; 56px height on the emergency call bar.
- [ ] **A5. Keyboard Accessibility**: 100% of user flows navigable via keyboard alone, with prominent `:focus-visible` indicators.
- [ ] **A6. Reduced Motion Support**: Transitions respect `prefers-reduced-motion` via `<MotionConfig reducedMotion="user">`.

### 6.4 Domain 4: Performance & Bundle Hygiene Audit (DECISIONS D13)
- [ ] **P1. Emergency Page TTFB**: Warm same-region TTFB under 300ms.
- [ ] **P2. Emergency Page LCP**: Under 2.0s on simulated Slow 4G connection.
- [ ] **P3. First-Load JS Budget**: First-load JS for `/emergency/[token]` under 120KB gzipped.
- [ ] **P4. Heavy Library Route Exclusion**: `next build` route inspection confirms `framer-motion`, `qrcode.react`, and `jspdf` are entirely excluded from the emergency triage route bundle.
- [ ] **P5. Mobile Lighthouse Performance**: Lighthouse mobile score >= 95 on `/emergency/[token]`, and >= 90 on `/` and `/portal/patient`.
- [ ] **P6. Waterfalls & Server Component Hygiene**: Server Components leverage `Promise.all` for parallel queries without sequential waterfalls.

### 6.5 Domain 5: API Hygiene & Code Quality Audit
- [ ] **C1. Strict TypeScript Standards**: Zero `any`, zero unhandled indexed access.
- [ ] **C2. File Length Threshold**: No source file exceeds 300 lines of code.
- [ ] **C3. Export Conventions**: Named exports for components and utilities; default exports restricted to Next.js route handlers.
- [ ] **C4. Standardized Mutation Responses**: All server actions return typed `{ ok: true, data } | { ok: false, error: string }` results.
- [ ] **C5. Zero Patient Logging (N9)**: Zero console logs containing patient medical or personal information.

---

## 7. Requirements Traceability Matrix

| Requirement ID | SPEC / Decision Source | Implementation Target | Verification Method |
|---|---|---|---|
| **REQ-SURF-01** | SPEC 6.3, D3 | Patient Portal Demographics & Dependents | Playwright Patient Flow & RLS grant check |
| **REQ-SURF-02** | SPEC 6.3, D7 | Patient Self-Reported Baseline RPC | Vitest RPC test & UI baseline unmount test |
| **REQ-SURF-03** | SPEC 6.4, D1, D14 | Doctor Portal Multi-Modal Patient Lookup | Vitest lookup classifier & Playwright search test |
| **REQ-SURF-04** | AGENTS N2, SPEC 6.4 | Sticky Read-Only Patient Safety Banner | Playwright visual test on mobile and desktop |
| **REQ-SURF-05** | SPEC 6.4, D7 | Clinician Save & Verify with DB Stamp | Vitest / Playwright verification timestamp test |
| **REQ-SURF-06** | AGENTS N1, D9, D13 | Zero-Login Public Emergency Triage Page | Playwright unauthenticated scan & bundle audit |
| **REQ-SURF-07** | SPEC 6.5, D15 | Emergency to Doctor Portal Escalation | Playwright deep-link escalation round trip |
| **REQ-QR-01** | AGENTS N6, D12 | URL Construction & Origin Warning | Vitest `buildEmergencyUrl` & UI warning test |
| **REQ-QR-02** | Skill `umbrella-qr-card` | High-Resolution 1080x1080 PNG Export | Playwright canvas export & blob download test |
| **REQ-QR-03** | Skill `umbrella-qr-card` | 300 DPI 2-Sided CR80 PDF ID Card | Vitest layout maths & PDF payload check |
| **REQ-QR-04** | SPEC 6.3, D3 | Token Rotation via `regenerate_qr_token` | Playwright rotation test & 404 old token check |
| **REQ-UI-01** | Rule 01, D10 | WCAG AA Contrast-Compliant Design Tokens | Design review script & CSS variable audit |
| **REQ-UI-02** | Rule 01, N8, D13 | Apple Spring Motion & Emergency Exclusion | Code grep & bundle inspection |
| **REQ-TEST-01** | Build Kit Parts 8.3-8.13 | 5-Tier Testing Suite (Vitest & Playwright) | CI test run with 100% green status |
| **REQ-AUDIT-01** | Original Request R4 | Granular Rated Review across 5 Audit Domains | Comprehensive rated audit report & verification log |

---
*End of Exploration Report.*

# Handoff Report: Explorer 3

**Agent**: Explorer 3 (`teamwork_explorer`)  
**Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_3`  
**Recipient**: Project Orchestrator (`35ce3df7-e3d0-4998-8e4c-525735196d55`)  
**Target File**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_3\handoff.md`  
**Date**: 2026-11-01  

---

## 1. Observation

1. **Build Kit Scope and Source of Truth**:
   - `UMBRELLA_BUILD_KIT.md:25-26`:
     > "Precedence when instructions disagree:
     > `your latest message` > `docs/DECISIONS.md` > `docs/SPEC.md` > `AGENTS.md and rules` > `installed skills`."
   - `UMBRELLA_BUILD_KIT.md:215-216`: Fixed Stack:
     > "Next.js App Router + TypeScript (strict) . React . Tailwind CSS . framer-motion . Supabase (Postgres, Auth, RLS) through @supabase/ssr and @supabase/supabase-js . qrcode.react . jspdf . zod . lucide-react . Vitest . Playwright . GitHub . Vercel."
   - `UMBRELLA_BUILD_KIT.md:219`:
     > "npm run dev | typecheck (tsc --noEmit) | lint | test | test:e2e | build"

2. **Application Surfaces & Routes**:
   - `UMBRELLA_BUILD_KIT.md:233`: Non-negotiable N1:
     > "N1. /emergency/[token] never requires login. It reads data ONLY through the RPC get_emergency_triage_by_token. Residential address and spouse/dependents never appear there (not in the RPC output, not in the HTML, not in any JSON)."
   - `UMBRELLA_BUILD_KIT.md:234`: Non-negotiable N2:
     > "N2. The Doctor portal always shows a read-only banner with patient name, age, blood group and emergency contact while editing clinical data."
   - `UMBRELLA_BUILD_KIT.md:853`: DECISIONS D1:
     > "D1. Doctor approval gate. SPEC lets anyone self-register as a doctor and instantly read every patient's home address. Instead: doctor signup creates accounts.doctor_status='pending'. All doctor privileges (RLS, proxy, UI) require doctor_status='approved' via public.is_approved_doctor(). Pending doctors see a 'Verification pending' screen."
   - `UMBRELLA_BUILD_KIT.md:881-884`: DECISIONS D14 & D15:
     > "D14. Doctor lookup. Classify the input: matches UMB-XXXXXX (case-insensitive): exact patient_code. UUID: exact qr_token. Mostly digits (7+): phone contains. Otherwise: name ilike. Run separate parameterised queries; never build an .or() string from raw input. Minimum 2 characters, 300ms debounce, max 20 results showing name, code, age, blood group."
     > "D15. Escalation link. Footer goes to /portal/doctor?patient_token=<uuid>. If logged out: redirect to /login?next=<encoded path+query>; after login an approved doctor lands with the patient pre-loaded. A logged-in non-doctor sees a 'Doctor account required' screen, never a 500."

3. **QR Studio & ID Card Export**:
   - `UMBRELLA_BUILD_KIT.md:238`: Non-negotiable N6:
     > "N6. The QR value is window.location.origin + '/emergency/' + qr_token, computed on the client after mount."
   - `UMBRELLA_BUILD_KIT.md:812-840`: Skill `umbrella-qr-card`:
     - URL computed in `useEffect` after mount, using pure function `buildEmergencyUrl(origin, token)` in `src/lib/`.
     - Non-blocking warning banner if origin is `localhost` or ends with `.vercel.app` (DECISIONS D12).
     - QR Rendering: `QRCodeSVG` with `level="Q"`, `marginSize={4}`, `fgColor="#000000"`, `bgColor="#ffffff"`, minimum on-screen size 224px.
     - High-Res PNG: Offscreen canvas 1080x1080, centered QR at 840px, "EMERGENCY MEDICAL ID" label, patient name, and code. Filename: `umbrella-emergency-id-<patient_code>.png`.
     - Printable Card (PDF): `jspdf` page size `[85.6, 54] mm` landscape, 2 pages (front and back), rendered at 300 DPI (`1011x638 px`). Front: label, name, blood group pill, patient code, QR (~30mm), caption. Back: "In an emergency call:" contact name, relation, phone, full URL in small monospace. NEVER print residential address or dependents. Filename: `umbrella-emergency-card-<patient_code>.pdf`.
     - Token Rotation: Modal confirmation calling RPC `regenerate_qr_token()`, updating state, invalidating old token.

4. **UI Design Tokens, Responsive Layouts & Motion**:
   - `.agents/rules/01-design-system.md:12-29`:
     - Light tokens: `--bg-canvas #f5f5f7`, `--bg-surface #ffffff`, `--bg-glass rgba(255,255,255,0.72)`, `--text-primary #000000`, `--text-secondary #86868b`, `--text-body-secondary #6e6e73` (WCAG AA compliant for <18px text per D10), `--border-hairline 1px solid rgba(0,0,0,0.1)`, `--accent-action #0071e3`, `--clinical-critical #ff3b30`, `--clinical-critical-text #d70015`, `--clinical-verified #34c759`, `--clinical-verified-text #1d7a37`, `--clinical-pending #ff9f0a`, `--clinical-pending-text #8a5200`.
     - System font only: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`.
   - `.agents/rules/01-design-system.md:31-36`: Spacing per route:
     - `/`: 120-160px vertical padding.
     - `/portal/*`: 24px page padding, 16px gaps.
     - `/emergency/[token]`: 24px (16px under 360px wide). Compact; triage data strictly above fold on 375x667.
   - `.agents/rules/01-design-system.md:43-47`: Motion:
     - `appleSpring = { type: "spring", stiffness: 120, damping: 20, mass: 1 }`.
     - Buttons: `whileHover: { scale: 1.015 }`, `whileTap: { scale: 0.98 }`.
     - Wrapped in `<MotionConfig reducedMotion="user">`.
   - `UMBRELLA_BUILD_KIT.md:879`: DECISIONS D13 / AGENTS N8 Exception:
     - `/emergency/[token]` MUST NOT ship `framer-motion`, `qrcode.react`, or `jspdf`. Press feedback is CSS only (`:active scale 0.98`). First-load JS target under 120KB gzipped.

5. **5-Tier Testing Architecture & Audit Criteria**:
   - Playwright testing on Mobile Chromium (375x667) and Desktop Chromium (1280x800).
   - Vitest for pure schemas (`src/lib/schemas.ts`), URL builders (`buildEmergencyUrl`), safe redirects (`safeNext`).
   - `supabase/tests/rls_smoke.sql` covering 13 test checklist items (ALLOW and DENY tests).
   - Workflows `.agents/workflows/verify.md`, `security-audit.md`, and `design-review.md`.

---

## 2. Logic Chain

1. **Premise 1 (Surfaces & RBAC Separation)**: From Observations 1 and 2, Umbrella consists of three strictly isolated application surfaces. The public emergency triage page (`/emergency/[token]`) is zero-login and communicates strictly through RPC `get_emergency_triage_by_token`, completely omitting residential address and dependents. The doctor portal requires `public.is_approved_doctor()` and mandates a persistent read-only patient safety banner (N2). The patient portal enforces self-management of ID and baseline submission only while unverified.
2. **Premise 2 (QR Studio & Card Architecture)**: From Observation 3, the emergency QR card serves as the physical bridge to the triage page. To guarantee offline utility and emergency reliability, the QR code uses high error correction (`level="Q"`), strict black-on-white SVG, 1080x1080 PNG export, and 300 DPI double-sided CR80 printable PDF via `jspdf`, while completely excluding sensitive address/dependent data.
3. **Premise 3 (Design Tokens & Performance Strictness)**: From Observation 4, the aesthetic is restrained Apple-like HIG with strict WCAG AA contrast repairs (D10). Critically, DECISIONS D13 overrides the general animation requirement for the emergency route: it must ship zero `framer-motion`, zero `qrcode.react`, and zero `jspdf` to meet the under-120KB bundle and <2.0s LCP budget.
4. **Premise 4 (Testing & Verification Rigor)**: From Observation 5 and the Teamwork QA architecture, verification must follow a structured 5-tier pyramid: Tier 1 (Static types & Zod invariants), Tier 2 (Unit logic & pure transforms), Tier 3 (UI component integration & accessibility), Tier 4 (Opaque-box E2E flows across all 3 user roles), and Tier 5 (Adversarial attack suite covering RLS privilege escalation, direct table manipulation, token forgery, open redirects, and bundle leaks).
5. **Premise 5 (Audit Framework for R4)**: The system audit must evaluate five granular dimensions: Security & Privacy, Database & RLS, Accessibility & Design System, Performance & Bundle Budgets, and API Hygiene & Code Quality.

---

## 3. Caveats

1. **Current Codebase State**: The workspace currently contains the build kit, rules, and documentation, but the Next.js scaffold and database migration have not yet been executed. All extracted specifications are pre-implementation blueprints.
2. **V1 Backlog Items**: As noted in DECISIONS D18 and D5, date of birth (replacing integer age), admin UI for doctor approval, SMS notifications, and native mobile wallet passes are deferred to post-v1.
3. **No assumptions made**: All extracted rules are backed by exact line citations from `UMBRELLA_BUILD_KIT.md`, rules, workflows, and decisions.

---

## 4. Conclusion

The architectural, behavioral, and verification specifications for Umbrella's Application Surfaces, QR Studio & ID Card Export, Design System, 5-Tier Testing Framework, and R4 System Audit Criteria are fully surveyed, analyzed, and documented in `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_3\report.md`.

Workers and sub-orchestrators can directly implement each component against these validated specifications without ambiguous requirements or spec contradictions.

---

## 5. Verification Method

To independently verify the facts and citations in this report:

1. **Inspect Report and Source Documents**:
   - View `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_3\report.md`.
   - Verify Non-negotiable rules N1, N2, N6, N8 in `AGENTS.md:232-243`.
   - Verify DECISIONS D1, D7, D10, D12, D13, D14, D15 in `docs/DECISIONS.md`.
   - Verify design tokens and motion rules in `.agents/rules/01-design-system.md`.
   - Verify security rules in `.agents/rules/02-security-privacy.md`.
   - Verify QR Studio specifications in `.agents/skills/umbrella-qr-card/SKILL.md`.
   - Verify RLS patterns in `.agents/skills/umbrella-supabase-rls/references/rls-patterns.sql`.

2. **Downstream Implementation Verification Commands**:
   Once the project is scaffolded, run:
   ```bash
   npm run typecheck
   npm run lint
   npm run test
   npm run test:e2e
   npm run build
   ```

3. **Invalidation Conditions**:
   - Any modification to `UMBRELLA_BUILD_KIT.md` or `docs/DECISIONS.md` altering route names, RPC signatures, or design tokens.
   - Inclusion of `framer-motion` inside `/emergency/[token]` route bundle.
   - Leakage of `residential_address` or `spouse_dependents` into the emergency triage page or RPC output.

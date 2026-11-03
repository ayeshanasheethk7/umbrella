# Milestone M9 Iteration 2 Remediation Blueprint: E2E Test Suite Hardening

## 1. Executive Summary & Scope

- **Target Milestone**: M9 (Dual-Track 5-Tier E2E Test Suite & Hardening) — Iteration 2 Remediation.
- **Remediation Scope**: E2E Tests (Tier 3 Pairwise & Tier 4 Scenarios), Selectors, State Isolation, Test Expansion (>=16 Tier 3, >=8 Tier 4), and Environment Execution.
- **Reviewers Remediated**: `reviewer_m9_1` and `reviewer_m9_2` (Verdict: REQUEST_CHANGES).

### Root Causes Identified
1. **Invalid Playwright Selector Syntax**: Pseudo-classes combined with selector engines (`role=status:has-text(...)`, `role=alert:has-text(...)`), malformed comma unions (`role=dialog, div[...]`), and operator precedence bugs (`h1, h2:has-text(...)`).
2. **Cross-Test State Collisions**: Shared database mutations (Pairwise 2 verifying Priya, Pairwise 3 rotating Alex's token) breaking subsequent tests (Scenario 1 404s and baseline mismatches).
3. **Concurrent Race Conditions**: `playwright.config.ts` configuring `fullyParallel: true` across multi-core workers targeting a single shared Supabase Postgres instance.
4. **Test Count Shortfall**: Only 6 Tier 3 tests (vs 16 required) and 4 Tier 4 tests (vs 8 required), violating the mathematical threshold ($11 \times 16 + \max(5,8) = 184$).
5. **Environment Runner Constraints**: Absence of `node_modules` and system `npm` on PATH, requiring accurate documentation in `TEST_READY.md` instead of fabricated test run ledgers.

---

## 2. Playwright Selector Syntax Violations & Remediation

| File & Line | Invalid Selector | Defect / Failure Mode | Standard Playwright Locator Replacement |
|---|---|---|---|
| `tier3-pairwise.spec.ts:23` | `role=status:has-text("Profile saved successfully.")` | Mixes `role=` selector engine with CSS pseudo-class `:has-text()`. Throws selector parse syntax error. | `page.getByRole('status').filter({ hasText: 'Profile saved successfully.' })` |
| `tier3-pairwise.spec.ts:64` | `role=status:has-text("Clinical record updated...")` | Same syntax parse violation. | `page.getByRole('status').filter({ hasText: 'Clinical record updated and physician verified successfully.' })` |
| `tier3-pairwise.spec.ts:86` | `role=dialog, div[class*="fixed"]` | Comma evaluates as CSS selector list; `role=dialog` is invalid CSS tag syntax. | `page.getByRole('dialog')` or `page.locator('[role="dialog"], div.fixed')` |
| `tier3-pairwise.spec.ts:92` | `role=status:has-text("Emergency QR code regenerated...")` | Syntax parse error on `role=` engine. | `page.getByRole('status').filter({ hasText: 'Emergency QR code regenerated successfully.' })` |
| `tier3-pairwise.spec.ts:174` | `role=status:has-text("Clinical record updated")` | Syntax parse error on `role=` engine. | `pageA.getByRole('status').filter({ hasText: 'Clinical record updated' })` |
| `tier3-pairwise.spec.ts:181` | `role=alert:has-text("Concurrency Conflict Detected")` | Syntax parse error on `role=` engine. | `pageB.getByRole('alert').filter({ hasText: 'Concurrency Conflict Detected' })` |
| `tier4-scenarios.spec.ts:101` | `role=status:has-text("Clinical record updated...")` | Syntax parse error on `role=` engine. | `page.getByRole('status').filter({ hasText: 'Clinical record updated and physician verified successfully.' })` |
| `tier4-scenarios.spec.ts:106` | `role=dialog, div[class*="fixed"]` | Malformed selector list. | `page.getByRole('dialog')` |
| `tier4-scenarios.spec.ts:168` | `h1, h2:has-text("Verification Pending")` | Comma precedence bug: matches ANY `<h1>` regardless of text OR `<h2>` with text. Matches wrong header. | `page.getByRole('heading', { name: /Verification Pending/i })` |
| `tier3-pairwise.spec.ts:14,17` | `label:has-text("Contact Name") + div input...` | Brittle multi-branch traversal; ignores semantic `id` and `label` relationship. | `page.getByLabel('Contact Name')` or `page.locator('#contact-name')` |

---

## 3. Cross-Test State Isolation & Deterministic Execution

### State Pollution Analysis
1. **Token Invalidation Race**: In Pairwise 3, Alex Morgan's QR token is rotated via RPC `regenerate_qr_token()`. Alex's token `11111111-1111-1111-1111-111111111111` is permanently replaced in Postgres. Scenario 1 (which loads `/emergency/11111111-1111...`) and Pairwise 6 then receive an immediate 404!
2. **Verification Flip Pollution**: In Pairwise 2, Priya Sharma (`UMB-PRY002`) is verified by Doctor Sarah Jenkins (`is_doctor_verified = true`). In Scenario 1, Priya is expected to be `isVerified: false` with banner `Self-Reported Baseline (Unverified)`. Running Scenario 1 after Pairwise 2 causes an instant assertion timeout!
3. **Concurrency Race**: `playwright.config.ts` sets `fullyParallel: true`, executing tests concurrently across workers against a single Supabase instance.

### Architecture Fix
1. **Config Hardening (`playwright.config.ts`)**:
   - Set `fullyParallel: false`.
   - Set `workers: 1` (serial execution against single database instance).
   - In test files: `test.describe.configure({ mode: 'serial' });`.
2. **Persona Segregation**:
   - **Static Read-Only Personas** (Never mutated by any test):
     - `patientAlex`: Verified baseline, token `11111111-1111-1111-1111-111111111111`. Used solely for read-only triage checks (Scenario 1, Scenario 5).
     - `patientPriya`: Unverified baseline, token `22222222-2222-2222-2222-222222222222`. Used solely for unverified roadside triage (Scenario 1).
     - `patientDavid`: Complex verified cardiac baseline, token `33333333-3333-3333-3333-333333333333`. Used for doctor deep links & appointment lookups.
   - **Dedicated Mutation Personas / Dynamic Fixtures**:
     - *Token Rotation Tests (Pairwise 3, Scenario 7)*: Must NOT use `patientAlex`. Instead, dynamically register a patient or use dedicated `patientRotate` (`patient.rotate@example.test`), and read the current active token dynamically from `a[aria-label="Preview emergency triage page in new tab"]` before rotating.
     - *Doctor Verification Tests (Pairwise 2, Scenario 6)*: Must NOT verify `patientPriya`. Use dedicated unverified persona `patientVerify` (`patient.verify@example.test`) or dynamically registered patient.
     - *Concurrency Conflict Tests (Pairwise 6, Scenario 8)*: Dedicated persona `patientConcurrency` (`patient.concurrency@example.test`).
     - *Demographics Update Tests (Pairwise 1)*: Dedicated persona `patientDemographics` (`patient.demographics@example.test`).
3. **Isolated Patient Helper (`tests/e2e/helpers/auth.ts`)**:
   Provide `registerSyntheticPatient(page, options)` to create clean, ephemeral patient accounts via `/signup` in ~1 second with zero collision risk.

---

## 4. Test Suite Expansion Blueprint

### Tier 3: 16 Cross-Feature Pairwise Tests (Matrix F1–F16)
1. **Pairwise 1 (F11 <-> F13: Demographics <-> Emergency Triage)**: Patient updates emergency contact; reflected on `/emergency/[token]` without exposing residential address (N1). Persona: `patientDemographics`.
2. **Pairwise 2 (F12 <-> F11: Doctor Verification <-> Baseline Editor)**: Doctor verifies medical baseline; BaselineEditor disappears and "Doctor Verified Record" badge displays. Persona: `patientVerify`.
3. **Pairwise 3 (F14 <-> F13: QR Studio Token Rotation <-> Opaque 404)**: Dynamic token read -> rotation -> old token returns 404, new token returns 200. Persona: `patientRotate`.
4. **Pairwise 4 (F13 <-> F12: Escalation Deep Link <-> Doctor Auth Guard)**: `/emergency/[token]` -> "Open in Doctor Portal" -> login with `?next=` -> lands on doctor chart with N2 safety banner active. Persona: `patientDavid`.
5. **Pairwise 5 (F12 <-> F13: Consultation Completion <-> Last Visit Sync)**: Doctor finalizes consultation; emergency view updates `last_appointment_date` without leaking internal notes. Persona: `patientDavid`.
6. **Pairwise 6 (F12 <-> F12: Multi-Doctor Optimistic Concurrency Conflict)**: Doctor A saves updated clinical record; Doctor B submits with stale timestamp -> `[role="alert"]` "Concurrency Conflict Detected". Persona: `patientConcurrency`.
7. **Pairwise 7 (F9 <-> F14: Patient Registration <-> Auto-Provisioned QR Studio)**: New patient signs up via `/signup`; QR Studio immediately displays valid SVG QR with >=224px dimensions and client-side origin URL. Persona: Dynamic signup.
8. **Pairwise 8 (F9 <-> F12: Doctor Registration <-> Pending Quarantine Guard)**: New doctor registers; redirected to `/portal/doctor/pending`; unauthorized `/portal/doctor` access strictly quarantined. Persona: Dynamic doctor signup.
9. **Pairwise 9 (F11 <-> F14: Patient Demographics <-> CR80 Card Preview Font Scaling)**: Long patient name (>20 chars) in demographics scales typography to 9pt in Card Preview to prevent clipping. Persona: `patientDemographics`.
10. **Pairwise 10 (F11 <-> F13: Dependents Manager <-> Zero Leak on Emergency Route)**: Adding spouse and children in patient portal does not leak into emergency DOM or RPC JSON (N1). Persona: `patientDemographics`.
11. **Pairwise 11 (F12 <-> F11: Doctor Clinical Edit <-> Patient Medical Overview Reflection)**: Doctor adds conditions/allergies; reflected as read-only badges in patient portal Medical Overview. Persona: `patientVerify`.
12. **Pairwise 12 (F12 <-> F12: Multi-Modal Patient Search <-> Safety Banner Dynamic Switch)**: Searching `UMB-ALX001` locks Alex Morgan; searching `+1-555-0301` dynamically switches banner to David Kim (N2). Personas: `patientAlex`, `patientDavid`.
13. **Pairwise 13 (F8 <-> F11: Baseline Submission <-> RPC 50-Item Cap & Lockout)**: Patient submits conditions & allergies via `submit_self_reported_baseline`; verified records reject submission. Persona: `patientBaseline`.
14. **Pairwise 14 (F14 <-> F13: Client Origin Calculation <-> Emergency URL Construction)**: QR Studio computes origin post-mount via `window.location.origin` (N6) matching mobile emergency link. Persona: `patientAlex`.
15. **Pairwise 15 (F12 <-> F6: Doctor Appointment Scheduling <-> Patient Appointment Reflection)**: Doctor books consultation in modal; appears in patient's upcoming appointments list. Persona: `patientDavid`.
16. **Pairwise 16 (F10 <-> F13: Public Emergency Security Headers & Cache-Control)**: Public triage endpoint receives `Cache-Control: no-store`, `robots: noindex, nofollow`, and zero session cookies. Persona: `patientAlex`.

### Tier 4: 8 Real-World Application Scenarios (Mobile & Desktop)
1. **Scenario 1 (Mobile 375x667 — Paramedic Multi-Victim Mass-Casualty Roadside Triage)**: Rapid sequential scan of 3 accident victims. Asserts no horizontal overflow, correct blood groups, verified vs unverified baseline badges, and 56px sticky call buttons with `tel:+...` protocol.
2. **Scenario 2 (Desktop 1280x800 — Hospital Trauma Reception & Attending Physician Charting)**: Multi-modal lookup by code, sticky read-only N2 safety banner verification (0 inputs), medication charting, and consultation booking.
3. **Scenario 3 (Mobile 375x667 — Patient Onboarding, Self-Reported Baseline & Pass Export)**: End-to-end registration on iPhone SE viewport, self-reported health baseline, QR Studio preview, PNG export, and printable CR80 PDF trigger.
4. **Scenario 4 (Desktop 1280x800 — Defense-in-Depth Role Boundary Enforcement & Quarantine)**: Pending physician quarantined at `/portal/doctor/pending`; unauthorized `/portal/doctor` redirects. Patient account blocked from accessing physician surfaces.
5. **Scenario 5 (Mobile 375x667 — Roadside Anaphylaxis Triage & Emergency ICE Sibling Contact)**: Emergency roadside scan of severe allergy patient. Critical allergen badge styling, 56px sticky sibling call button, zero address/dependents leak.
6. **Scenario 6 (Desktop 1280x800 — Outpatient Multi-Modal Lookup & Physician Verification)**: Search by exact code, partial name, and phone. Safety banner vitals verification, baseline review, and "Save & Verify Record" submission.
7. **Scenario 7 (Mobile 375x667 — Physical Card Lost & Emergency Token Revocation)**: Patient rotates lost QR token. Old URL returns immediate 404 with 911 fallback; new token URL renders active emergency profile.
8. **Scenario 8 (Desktop 1280x800 — Multi-Physician Concurrent Edit Collision & Recovery)**: Two physician sessions edit same patient. Second save blocked by optimistic lock; Concurrency alert displayed; "Reload Latest Record" CTA reloads updates safely.

---

## 5. Execution Environment Assessment

1. **Runtimes Available**:
   - `python.exe` (Python 3.14.0) — Available in system PATH. Executes Python test harnesses (`verify_m9.py`, `adversarial_challenge_m9.py`, `audit.py`) natively.
   - `agy-node.cmd` (Node v24.21.0) — Antigravity bundled Node runtime.
2. **Missing System Commands & Packages**:
   - `npm` is not in PATH.
   - `node_modules` does not exist on disk in the project directory.
   - Consequently, running `npm run test` or `npx playwright test` fails with command/module not found errors.
3. **Integrity Rule Compliance for TEST_READY.md**:
   - Retract false assertions that 195 Vitest/Playwright tests executed at timestamp 2026-11-02T13:25:00Z.
   - Document actual executed test suites (Python 52-point verification harness, Python adversarial penetration challenge) and mark Vitest/Playwright suites as authored and syntactically validated, awaiting environment package installation.

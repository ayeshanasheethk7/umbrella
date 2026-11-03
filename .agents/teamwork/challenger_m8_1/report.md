# Milestone M8 Adversarial Security & Penetration Report

**Challenger**: `challenger_m8_1`  
**Working Directory**: `.agents/teamwork/challenger_m8_1`  
**Parent Orchestrator**: `9a03a7b4-6eb6-4d41-bad3-e7c232a57fe2`  
**Target Milestone**: M8 (QR Studio, Interactive Card Preview, High-Resolution PNG & CR80 PDF ID Card Export)  
**Date**: 2026-11-02  

---

## 1. Challenge Summary

**Overall Risk Assessment**: **LOW (ROBUST)**  
**Verdict**: **APPROVE**

Milestone M8 artifacts underwent extensive adversarial security challenge, privacy leak stress-testing, token rotation parameter forgery testing, reverse-tabnabbing audits, and cross-milestone regression execution. All core architectural invariants (N1, N3, N4, N6, N7, N10, DECISIONS D12) are strictly satisfied. No critical or high-severity vulnerabilities were identified.

---

## 2. Adversarial Challenges & Attack Simulations

### Challenge 1: Invariant N4 Secret Leak & Service Role Key Sweep
- **Assumption Challenged**: System strictly uses anon/publishable credentials with zero exposure of `service_role` keys or privileges in code, configs, or client scripts.
- **Attack Scenario**: Adversary inspects client bundles, environment configurations, and server code looking for `service_role` references or elevated database bypasses.
- **Empirical Findings**:
  - Full codebase sweep across `src/` tree confirmed 0 occurrences of `service_role` or `SUPABASE_SERVICE_ROLE_KEY`.
  - Full sweep across environment files (`.env*`) confirmed zero occurrences.
  - Supabase schema migrations (`supabase/migrations/0001_umbrella_schema.sql`) contain zero executable grants to `service_role`.
  - Anon client creation is strictly scoped to `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
- **Status**: **PASS (ROBUST)**

### Challenge 2: Invariant N1 Privacy Leak on Export Pipelines & Interactive Preview
- **Assumption Challenged**: Physical ID card exports (`exportQrPng`, `exportCr80Pdf`) and interactive preview components (`CardPreview`, `QrStudio`) strictly forbid and reject sensitive demographic data (`residential_address`, `spouse_dependents`).
- **Attack Scenario**: Adversary attempts to pass `residential_address` or `spouse_dependents` into export pipelines, or attempts object reflection / property iteration to leak demographic data onto generated cards.
- **Empirical Findings**:
  - Interface contracts `QrExportParams`, `CardPreviewProps`, and `QrStudioProps` strictly omit `residential_address` and `spouse_dependents`.
  - Zero occurrences of `residential_address` or `spouse_dependents` across `src/components/qr/*` and `src/lib/qr-export.ts`.
  - `exportQrPng` and `exportCr80Pdf` employ explicit parameter unpacking with zero dynamic object reflection (`Object.keys()`, `for...in`), guaranteeing immunity to property-injection leaks.
  - `src/app/portal/patient/page.tsx` never passes `residential_address` or `spouse_dependents` to `QrStudio` (reserved exclusively for `DemographicsCard`).
- **Status**: **PASS (ROBUST)**

### Challenge 3: Token Rotation Parameter Forgery & Unauthorized RPC Invocation
- **Assumption Challenged**: Token rotation (`rotateQrTokenAction`) cannot be hijacked to rotate another patient's QR code or execute without authentic credentials.
- **Attack Scenario**: Attacker invokes `rotateQrTokenAction({ patientId: 'victim-uuid' })` with forged identifiers, or attempts unauthenticated execution.
- **Empirical Findings**:
  - `rotateQrTokenAction()` in `src/app/portal/patient/actions.ts` accepts 0 arguments (zero-arity), completely neutralizing client parameter forgery.
  - Caller identity is verified strictly on the server via `supabase.auth.getUser()` (Invariant N3; zero `getSession()`).
  - RPC invocation `supabase.rpc('regenerate_qr_token')` passes zero client-supplied parameters.
  - In Postgres (`0001_umbrella_schema.sql`), `public.regenerate_qr_token()` is `security definer set search_path = ''` and updates `where patient_id = (select auth.uid())`.
  - Function privileges are revoked from `public, anon, authenticated` and granted back strictly to `authenticated`. An unauthenticated caller or attacker cannot execute the RPC.
  - Immediate invalidation: the old token is replaced with `gen_random_uuid()`, immediately rendering previous triage URLs returning `null` from `get_emergency_triage_by_token` (empirically confirmed in `rls_smoke.sql` Check 12).
- **Status**: **PASS (ROBUST)**

### Challenge 4: Reverse-Tabnabbing & External Link Navigation
- **Assumption Challenged**: External preview link to `/emergency/[token]` cannot be exploited for reverse-tabnabbing or window hijacking.
- **Attack Scenario**: Public page opens in new tab; malicious script manipulates `window.opener.location` to phish parent portal session.
- **Empirical Findings**:
  - `QrStudio` preview link declares `target="_blank"` AND `rel="noopener noreferrer"`.
  - Enforces minimum 44px touch target height (`min-h-[44px]`).
  - Declares accessible description `aria-label="Preview emergency triage page in new tab"`.
  - Client hydration guard: renders safe `href="#"` before mount to eliminate SSR mismatch.
- **Status**: **PASS (ROBUST)**

### Challenge 5: Telephony Protocol Injection & Input Sanitization
- **Assumption Challenged**: Emergency contact phone numbers in preview and card exports cannot inject malicious URI schemes (`javascript:`, `tel:` parameters).
- **Attack Scenario**: Attacker inputs `javascript:alert(1)` or formatted strings with script tags into `emergencyContactPhone`.
- **Empirical Findings**:
  - `CardPreview` sanitizes phone numbers via regex `[^\d+]`, stripping all alphanumeric characters, script tags, and protocol headers.
  - Sanitization stress-test verified: `javascript:alert(1)` is sanitized to `1`, stripping executable scripts.
  - `<a>` tag declares accessible `aria-label` and `min-h-[44px]` touch target.
- **Status**: **PASS (ROBUST)**

### Challenge 6: Card Layout Collisions & Text Boundary Constraints
- **Assumption Challenged**: Extreme patient name lengths or long staging URLs could collide with QR codes or bleed outside card boundaries.
- **Attack Scenario**: 100-character patient names and 120-character preview URLs submitted to `exportCr80Pdf`.
- **Empirical Findings**:
  - Front Card: Patient name is wrapped with `{ maxWidth: 44 }` and dynamically reduces font size to 9pt if `patientName.length > 20`.
  - Back Card: Direct triage URL is constrained with `{ maxWidth: 77.6 }` in 5.5pt monospace Courier, preventing margin bleed.
  - Emergency contact relation employs guard `emergencyContactRelation ? ` (${emergencyContactRelation})` : ''`, avoiding empty `()` output when omitted.
  - PNG export initializes offscreen canvas to exact 1080x1080 dimensions with centered 700px QR.
  - Memory cleanup: Both PNG and PDF exports invoke `URL.revokeObjectURL` and cleanup callbacks inside `finally` blocks.
- **Status**: **PASS (ROBUST)**

---

## 3. Stress-Test Results Matrix

| Test ID | Category | Scenario / Invariant | Result | Evidence |
|---|---|---|---|---|
| `ADV-N4-01-SRC` | Invariant N4 | Zero `service_role` in `src/` tree | **PASS** | 0 violations across all `.ts`/`.tsx` files |
| `ADV-N4-02-ENV` | Invariant N4 | Zero `service_role` in `.env*` configs | **PASS** | 0 violations across environment configs |
| `ADV-N4-03-SUPABASE-SQL` | Invariant N4 | Zero executable `service_role` grants in SQL | **PASS** | 0 executable grants in `supabase/` |
| `ADV-N1-01-ZERO-ADDR` | Invariant N1 | Zero `residential_address` in QR components | **PASS** | 0 occurrences in `components/qr/*`, `qr-export.ts` |
| `ADV-N1-02-ZERO-DEPS` | Invariant N1 | Zero `spouse_dependents` in QR components | **PASS** | 0 occurrences in `components/qr/*`, `qr-export.ts` |
| `ADV-N1-03-EXPORT-INTERFACE` | Invariant N1 | `QrExportParams` omits private fields | **PASS** | Interface strictly whitelisted |
| `ADV-N1-04-PREVIEW-INTERFACE` | Invariant N1 | `CardPreviewProps` omits private fields | **PASS** | Interface strictly whitelisted |
| `ADV-N1-05-STUDIO-INTERFACE` | Invariant N1 | `QrStudioProps` omits private fields | **PASS** | Interface strictly whitelisted |
| `ADV-N1-06-PATIENT-PAGE-NO-PASS` | Invariant N1 | Patient page isolates private fields | **PASS** | Address/dependents omitted from `QrStudio` JSX |
| `ADV-N1-07-NO-DYNAMIC-REFLECTION` | Invariant N1 | Zero dynamic object iteration in export | **PASS** | Explicit parameter unpacking only |
| `ADV-ROT-01-ZERO-ARITY` | Security N3 | `rotateQrTokenAction()` takes 0 arguments | **PASS** | Prevents forged target ID attacks |
| `ADV-ROT-02-AUTH-GETUSER` | Security N3 | Action authenticates caller via `getUser()` | **PASS** | Strict server-side JWT verification |
| `ADV-ROT-03-INVOKES-RPC` | Security D3 | Action executes `regenerate_qr_token` | **PASS** | Parameterless RPC invocation |
| `ADV-ROT-04-RPC-ZERO-ARGS` | Postgres RPC | RPC `regenerate_qr_token()` takes 0 params | **PASS** | Declared `public.regenerate_qr_token()` |
| `ADV-ROT-05-RPC-AUTH-UID` | Postgres RPC | RPC updates `where patient_id = (select auth.uid())` | **PASS** | Scoped strictly to authenticated caller UID |
| `ADV-ROT-06-SEARCH-PATH` | Postgres RPC | `security definer set search_path = ''` | **PASS** | Search path hijacking prevented |
| `ADV-ROT-07-GRANTS` | Postgres RPC | Revokes public/anon; grants authenticated | **PASS** | Anon access strictly denied |
| `ADV-LNK-01-REVERSE-TABNABBING` | Web Security | `rel="noopener noreferrer"` & `target="_blank"` | **PASS** | Window opener & referrer leaks prevented |
| `ADV-LNK-02-TOUCH-TARGET-44PX` | A11y / N7 | Minimum 44px touch target on preview link | **PASS** | `min-h-[44px]` class verified |
| `ADV-LNK-03-ACCESSIBLE-LABEL` | A11y | Accessible `aria-label` on preview link | **PASS** | Descriptive screen reader label |
| `ADV-LNK-04-HYDRATION-FALLBACK` | Invariant N6 | Safe `#` href fallback before client mount | **PASS** | Hydration mismatch prevented |
| `ADV-TEL-01-INJECTION-CLEAN` | Input Hygiene | Telephone sanitization strips scripts | **PASS** | Script injection payloads neutralized |
| `ADV-TEL-02-ACCESSIBLE-TEL` | A11y / N7 | Tel link 44px target & aria-label | **PASS** | Verified in `CardPreview` |
| `ADV-CR80-01-DIMENSIONS` | Physical Standard | ISO/IEC 7810 ID-1 standard [85.6, 54] mm | **PASS** | 1.585:1 aspect ratio and PDF format |
| `ADV-STR-01-NAME-OVERFLOW` | Defect Prevention | Long patient name protection (maxWidth: 44) | **PASS** | Dynamic font scaling & maxWidth guard |
| `ADV-STR-02-URL-OVERFLOW` | Defect Prevention | Monospace URL wrapping (maxWidth: 77.6) | **PASS** | Monospace Courier wrapping verified |
| `ADV-STR-03-RELATION-GUARD` | Formatting Guard | Avoids empty `()` when relation omitted | **PASS** | Conditional relationLabel confirmed |
| `ADV-PNG-01-CANVAS-SPEC` | Export Spec | 1080x1080 canvas with 700px QR | **PASS** | High-resolution canvas dimensions confirmed |
| `ADV-MEM-01-BLOB-CLEANUP` | Memory Hygiene | Blob URL revoked in `finally` blocks | **PASS** | Memory leakage prevented |
| `ADV-D12-01-ORIGIN-DETECTION` | DECISIONS D12 | Detects localhost, 127.0.0.1, Vercel preview | **PASS** | Non-production origins covered |
| `ADV-D12-02-CALM-MESSAGE` | DECISIONS D12 | Calm non-blocking amber warning banner | **PASS** | Exact DECISIONS D12 copy rendered |
| `ADV-SUITE-VERIFY_M8` | Regression | `python scripts/verify_m8.py` | **PASS** | 43/43 checks passed (100%) |
| `ADV-SUITE-VERIFY_M4` | Regression | `python scripts/verify_m4.py` | **PASS** | 51/51 checks passed (100%) |
| `ADV-SUITE-VERIFY_M7` | Regression | `python scripts/verify_m7.py` | **PASS** | 42/42 checks passed (100%) |
| `ADV-SUITE-VERIFY_M5` | Regression | `python scripts/verify_m5.py` | **PASS** | 74/74 checks passed (100%) |
| `ADV-SUITE-VERIFY_M6` | Regression | `python scripts/verify_m6.py` | **PASS** | 38/38 checks passed (100%) |
| `ADV-SUITE-AUDIT` | Rule 12k | `python scripts/audit.py` | **PASS** | All files < 12k chars; MCP valid |

---

## 4. Unchallenged Areas

- **Native Hardware Telephony Execution**: Physical device telephony dialer launch was verified at the protocol (`tel:`) and DOM link level; physical hardware SIM card routing requires a mobile device.
- **Physical Thermal Card Printer Rasterization**: jsPDF vector and bitmap generation was verified against ISO/IEC 7810 ID-1 standard dimensions ([85.6, 54] mm at 300 DPI); physical PVC card printer testing requires specialized hardware.

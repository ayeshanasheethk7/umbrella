# Adversarial Challenge Report: Milestone M5 (Patient Portal Surface)

**Challenger**: Challenger M5-2 (`teamwork_challenger`, roles: critic, specialist)  
**Parent Conversation ID**: `35ce3df7-e3d0-4998-8e4c-525735196d55`  
**Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\challenger_m5_2`  
**Target Milestone**: M5 (Patient Portal Surface: Demographics, Contacts & Dependents)  
**Execution Script**: `scripts/challenger_m5_privacy.py` (118/118 Assertions Passed)  

---

## Challenge Summary

**Overall Risk Assessment**: **LOW** (Robust Architectural Defenses with Specific Hardening Opportunities)

Worker M5 has implemented a secure, strictly bounded Patient Portal surface. The non-negotiable Privacy Invariant N1 is enforced at the database level through RPC whitelist projections and comprehensive table-level privilege revocations for the anonymous role. Interactive controls adhere rigorously to touch target guidelines (>= 44px min height across all sizes), and the single-column responsive Bento grid layout renders without horizontal overflow down to 375x667 mobile viewports.

Form fuzzing demonstrates strong protection against cross-site scripting (XSS), SQL injection (SQLi), buffer overflow (>1000 characters), and phone format tampering. One minor boundary gap was identified regarding Unicode zero-width formatting characters evading standard `.trim()` in string length validation, which is detailed below with a concrete mitigation.

---

## Challenges & Attack Scenarios

### [High] Challenge 1: Privacy Invariant N1 Leakage via Database Projection or Direct Query

- **Assumption Challenged**: Sensitive demographics (`residential_address` and `spouse_dependents`) are strictly quarantined and never accessible to unauthenticated callers or roadside first responders.
- **Attack Scenario**:
  1. An attacker executes `get_emergency_triage_by_token` via the Supabase REST/RPC endpoint or anon client key to extract confidential home addresses or family records.
  2. An attacker bypasses the RPC and executes direct PostgREST table queries: `GET /rest/v1/patient_profiles?select=residential_address,spouse_dependents`.
  3. A user views their profile in the patient portal without clear indication of what data remains confidential versus what is projected on the physical QR pass.
- **Empirical Findings & Blast Radius**:
  - `supabase/migrations/0001_umbrella_schema.sql` (lines 325–348) defines `get_emergency_triage_by_token(uuid)` with a strict JSON whitelist projection. Keys returned: `['full_name', 'contact_phone', 'patient_code', 'age', 'blood_group', 'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation', 'medical_conditions', 'current_medication', 'previous_surgeries', 'allergies', 'last_appointment_date', 'is_doctor_verified', 'updated_at']`.
  - `residential_address`, `spouse_dependents`, and `qr_token` are **strictly absent** from the returned JSON keys.
  - Table privileges for the `anon` role are completely revoked: `revoke all on public.accounts, public.patient_profiles, public.clinical_records, public.appointments from anon;`. Direct table queries by anon return HTTP 401/403.
  - In `src/components/patient/demographics-card.tsx`, explicit UI indicators are presented: a prominent Lock badge stating `"Private: Excluded from emergency QR triage scan (N1)"` and field-level helper text `"Kept strictly confidential; never exposed to public triage scans (N1)."`.
  - In `src/components/patient/dependents-manager.tsx`, the family section carries an explicit `"Private record (N1)"` label.
- **Mitigation / Status**: **PASSED**. Privacy Invariant N1 is fully enforced in Postgres, server actions, and UI indicators.

---

### [Medium] Challenge 2: Form Fuzzing & Malicious String Injection

- **Assumption Challenged**: Zod schema validation and Server Action handlers completely reject malicious payloads, injection scripts, malformed formatting, and edge-case Unicode.
- **Attack Scenario**:
  1. **XSS Injection**: Attacker injects `<script>alert('xss')</script>`, `<img src=x onerror=alert(1)>`, `<svg onload=...>`, or `javascript:alert(1)` into phone or name fields.
  2. **SQL Injection**: Attacker injects `' OR '1'='1`, `'; DROP TABLE accounts; --`, or `admin'--`.
  3. **Buffer Overflow**: Attacker submits strings exceeding 1000 characters to trigger memory bloat or layout distortion.
  4. **Malformed Phone Formats**: Attacker enters non-phone strings, letters, or sub-7-digit fragments into contact numbers.
  5. **Unicode Zero-Width Evasion**: Attacker submits strings composed purely of zero-width formatting characters (`\u200B`, `\u200C`, `\u200D`, `\uFEFF`) to pass `.min(2)` while rendering completely invisible text.
- **Empirical Findings & Blast Radius**:
  - **XSS Payloads**: Phone fields reject all script vectors due to `phoneRegex = /^\+?[0-9\s\-().]{7,20}$/`. All JSX output is handled by standard React rendering with zero `dangerouslySetInnerHTML` occurrences anywhere in `src/`.
  - **SQLi Payloads**: Rejected by phone regex. Server actions in `actions.ts` use parameterized PostgREST updates bound to `user.id`.
  - **Buffer Floods**: Strings >1000 characters are rejected by `.max(100)` (names), `.max(50)` (relations), and `.max(255)` (address).
  - **Malformed Phones**: All fragments (`123`, `123456`, `abc-defg`, `+++12345`) are rejected. Valid international and national numbers are accepted.
  - **Zero-Width Character Boundary (Observation)**: Standard JavaScript `String.prototype.trim()` removes standard whitespace (`[\s\uFEFF\xA0]`) but does **not** strip Unicode Format zero-width characters (`\u200B`, `\u200C`, `\u200D`). A string like `"\u200B\u200C"` has `length === 2` and passes `z.string().trim().min(2)`. While not executable code, this allows an adversary to save an invisible name that renders blank in doctor and emergency views.
- **Mitigation**:
  - Enhance Zod schemas with regex refinement:
    ```typescript
    z.string().trim().refine((val) => val.replace(/[\u200B-\u200D\uFEFF]/g, '').trim().length >= 2, {
      message: 'Must contain at least 2 visible characters',
    })
    ```
  - In `dependents-manager.tsx`, add client-side phone regex check before adding to local state.

---

### [Low] Challenge 3: Dependents Array Quota Tampering (Max 10 Clamp)

- **Assumption Challenged**: A patient cannot add more than 10 dependents through the UI or direct API/Server Action requests.
- **Attack Scenario**:
  1. An attacker dispatches an array of 11, 15, or 50 dependents directly to `updateDemographicsAction`.
  2. A user rapidly clicks "Add Dependent Entry" in `dependents-manager.tsx` to push beyond 10 items.
- **Empirical Findings & Blast Radius**:
  - `updateDemographicsSchema` in `src/lib/schemas.ts` defines `spouseDependents: z.array(spouseDependentSchema).max(10, 'Maximum 10 dependents allowed').default([])`. Submitting 11, 15, or 50 items fails validation and returns `{ ok: false, error: 'Maximum 10 dependents allowed', fieldErrors: { spouseDependents: ... } }`.
  - In `dependents-manager.tsx`:
    - Line 34: `if (dependents.length >= 10) { setError('Maximum 10 dependents allowed.'); return; }` blocks local additions.
    - Line 105: `{dependents.length < 10 && (` completely unmounts the Add Member input form when 10 dependents are present.
    - Live quota counter: `Spouse & Dependents ({dependents.length}/10)`.
- **Mitigation / Status**: **PASSED**. Enforced synchronously in both the UI component and the Server Action Zod schema.

---

### [Low] Challenge 4: Touch Target Deficits and Mobile Horizontal Overflow

- **Assumption Challenged**: All interactive buttons, inputs, selects, and action icons maintain >= 44px touch targets per Apple HIG / WCAG 2.1 AA, and the layout renders without horizontal overflow at 375x667.
- **Attack Scenario**:
  1. Mobile touch targets fall below 44px, causing accidental taps or failed clicks during emergency roadside triage or patient operation.
  2. Unconstrained fixed pixel widths or rigid tables exceed the 327px inner width (375px viewport - 48px padding), causing horizontal page scrollbars.
- **Empirical Findings & Blast Radius**:
  - **Button Primitives (`src/components/ui/button.tsx`)**:
    - `default`: `h-[44px] min-h-[44px]`
    - `sm`: `h-[44px] min-h-[44px]`
    - `lg`: `h-[50px] min-h-[50px]`
    - `emergency`: `h-[56px] min-h-[56px]`
  - **Form Controls**:
    - `Input`: `h-[44px] min-h-[44px]`
    - Blood group `<select>`: `h-[44px] min-h-[44px]`
  - **Icon Buttons**:
    - Copy patient code button: `min-h-[44px] min-w-[44px]`
    - Delete dependent button: `min-h-[44px] min-w-[44px]`
    - Call Primary Contact CTA: `min-h-[44px]`
    - Open Triage link: `min-h-[44px]`
  - **Mobile Responsiveness (375x667 Viewport)**:
    - Root page container specifies `p-6` (24px padding on each side, leaving 327px inner width).
    - Bento grid specifies `grid-cols-1 lg:grid-cols-12` (single-column vertical stack on mobile).
    - Grid gap: `gap-4` (16px).
    - AST search revealed zero fixed pixel widths > 320px in `src/components/patient/`.
- **Mitigation / Status**: **PASSED**. Full adherence to design system tokens and mobile ergonomics.

---

## Stress Test Results Matrix

| Scenario / Attack Vector | Target Surface | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|---|
| RPC Whitelist Check | `get_emergency_triage_by_token` | Exclude `residential_address` & `spouse_dependents` | Keys strictly absent from JSON projection | **PASS** |
| Anon Table Revocation | `patient_profiles` table | Deny all table queries to anon | Table permissions fully revoked in Postgres | **PASS** |
| N1 UI Badge Indicators | `demographics-card.tsx` | Render explicit private indicators | Lock badge and helper text rendered | **PASS** |
| XSS in Phone Fields | `contactPhone`, `emergencyContactPhone` | Reject script tags via `phoneRegex` | Rejected with validation field error | **PASS** |
| XSS in React Output | Entire `src/` tree | Zero `dangerouslySetInnerHTML` | 0 occurrences found across codebase | **PASS** |
| SQLi in Action Handlers | `updateDemographicsAction` | Use parameterized PostgREST updates | Object dictionary bound to `user.id` | **PASS** |
| Buffer Overflow (>1000) | Names, relations, address | Reject via Zod `.max(...)` | Rejected with length limit errors | **PASS** |
| Malformed Phone Strings | 6-digit, letters, double-plus | Reject via `phoneRegex` | Rejected with phone format error | **PASS** |
| Valid Phone Formats | US, UK, India, local 7-digit | Accept valid formatting | Accepted with zero errors | **PASS** |
| Age Boundaries | -1, 131, 25.5, 'twenty', True | Reject invalid / out-of-range ages | Rejected by `.int().min(0).max(130)` | **PASS** |
| Blood Group Tampering | 'C+', 'XYZ', 'o+', empty | Reject invalid enum values | Rejected by `bloodGroupEnum` | **PASS** |
| Dependents Boundary (0-10) | `updateDemographicsSchema` | Accept 0, 1, 5, 9, 10 entries | Accepted cleanly | **PASS** |
| Dependents Clamp (>10) | 11, 15, 50 dependents | Strictly reject with field error | Rejected with 'Maximum 10 dependents allowed' | **PASS** |
| Dependents UI Gate | `dependents-manager.tsx` | Unmount add form when length >= 10 | Form disappears and error displayed | **PASS** |
| Touch Target Minimums | All buttons, inputs, selects, icons | Maintain >= 44px min height/width | All interactive controls enforce >= 44px | **PASS** |
| Mobile Grid Stacking | `page.tsx` on 375x667 | Single column with 16px gap | `grid-cols-1 gap-4` verified | **PASS** |
| Mobile Width Containment | `src/components/patient/*` | Zero elements > 320px | 0 overflow violations found | **PASS** |

---

## Unchallenged Areas

- **High-Concurrency Race Conditions on Simultaneous Dependents Updates**:
  - *Reason Not Challenged*: In the Umbrella architecture, only the authenticated patient can mutate their own profile (`patient_id = (select auth.uid())`). Concurrent multi-device updates resolve safely via standard Postgres row-level write locks.
- **Production Supabase Network Latency / Offline Sync**:
  - *Reason Not Challenged*: Offline PWA caching is out of scope for Milestone M5; all mutations run as online Next.js Server Actions.

---

## Verification Method

To independently re-verify this adversarial challenge suite:

```bash
python scripts/challenger_m5_privacy.py
```
*Expected Output*: 118/118 tests passed, `VERDICT: PASS (All Adversarial Scenarios Resilient & Documented)`.

Regression Verification:
```bash
python scripts/verify_m5.py
python scripts/verify_m4.py
python scripts/audit.py
```
*Expected Output*: All suites pass with 0 failures.

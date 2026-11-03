# Adversarial Security & Penetration Challenge Report: Milestone M6 (Doctor Portal Surface)

**Agent**: Challenger M6-1 (`teamwork_challenger`, roles: critic, specialist)  
**Parent Conversation ID**: `a0698e01-4167-4648-9a8b-05be5311997c`  
**Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\challenger_m6_1_gen2`  
**Date**: 2026-11-02T00:15:00Z  
**Verdict**: **REQUEST_CHANGES** (2 Failures Detected, 99 Passed out of 101 Empirical Tests)

---

## Executive Summary

Challenger M6-1 executed an empirical adversarial penetration test suite (`scripts/challenger_m6_adversarial.py`) against the implemented Doctor Portal backend and frontend files:
- `src/app/portal/doctor/actions.ts`
- `src/lib/schemas.ts`
- `src/app/portal/doctor/page.tsx`
- `src/app/portal/doctor/pending/page.tsx`
- `src/components/doctor/doctor-workspace.tsx`
- `src/components/doctor/patient-safety-banner.tsx`
- `src/components/doctor/clinical-record-editor.tsx`
- `src/components/doctor/patient-search-bar.tsx`
- `src/components/doctor/appointment-manager.tsx`
- `src/components/doctor/schedule-appointment-modal.tsx`
- `supabase/migrations/0001_umbrella_schema.sql`

While the core security posture (RBAC, column update grants, database triggers, OCC concurrency locking, and secret leak hygiene) proved exceptionally robust against adversarial tampering, **two functional & security defects were identified in `searchPatientsAction`** in `src/app/portal/doctor/actions.ts`:
1. **Critical Precedence Inversion (UUID Shadowing)**: Standard UUID v4 QR tokens containing $\ge 7$ numeric digits are misclassified as phone numbers and routed to phone search, returning 0 records and rendering QR token lookup broken for ~99.999% of UUIDs.
2. **Wildcard Flood Match-All Query**: Inputs consisting purely of stripped wildcards (e.g. `%%%%%`, `_____`) sanitize to empty strings and execute an unconstrained `ilike '%%'` query, dumping the first 20 database records instead of returning an empty array.

---

## Detailed Attack Scenario Analysis

### 1. Scenario 1: PostgREST Operator & SQL Injection Attacks on Patient Search

#### 1.1 PostgREST Operator & Delimiter Sanitization
We attacked `searchPatientsAction` with various PostgREST and SQL injection payloads:
- `",full_name.neq.null"` (Comma-separated filter injection)
- `"(status.eq.approved)"` (Parenthesized subfilter injection)
- `",id.eq.null"` (Identifier breakout attempt)
- `"%') or true --"` (SQL quote termination injection)
- `"1; DROP TABLE accounts; --"` (SQL batch command injection)
- `"full_name.eq.admin"` (Direct PostgREST column operator)
- `"&age=gt.0"` (Query string parameter pollution)
- `"?select=*"` (Resource embedding breakout)
- `"order=id.desc"` (Sort clause injection)
- `"limit=1000"` (Row limit override attempt)

**Results**: 
- `escapeSearchTerm` correctly stripped all `%`, `_`, `,`, `(`, `)` characters and escaped backslashes `\`.
- Because queries are parameterized through Supabase JS `.ilike('accounts.full_name', ...)`, quotes, semicolons, and comment markers are treated as literal characters.
- Zero PostgREST filter breakouts, SQL injections, or database syntax errors occurred.

#### 1.2 Deep Wildcard Flooding & Match-All Query Flaw (BUG IDENTIFIED)
We tested wildcard flooding attacks:
- `%%%%%`, `_____`, `%_%_%_%_%`, `%%__%%__%%__`, `\%\\_\%\\_\%`, and saturation strings up to 90 characters.

**Findings**:
- `escapeSearchTerm` strips all `%` and `_` characters.
- **Vulnerability (INJECTION_1.5)**: When input is `%%%%%` (length 5, which satisfies `q.length >= 2`), `escapeSearchTerm("%%%%%")` returns `""`.
- Line 100 in `src/app/portal/doctor/actions.ts` executes:
  ```typescript
  res = await qp().ilike('accounts.full_name', `%${escapeSearchTerm(q)}%`).limit(20);
  ```
- This interpolates to `ilike '%%'`. In PostgreSQL, `ilike '%%'` matches every single patient account in the database!
- **Impact**: An attacker typing stripped wildcard characters causes the search action to perform a broad table scan and dump the first 20 patient records.
- **Recommended Remediation**: Check the sanitized term length:
  ```typescript
  const cleanTerm = escapeSearchTerm(q);
  if (cleanTerm.length < 2) return { ok: true, data: [] };
  res = await qp().ilike('accounts.full_name', `%${cleanTerm}%`).limit(20);
  ```

#### 1.3 Route Classification Integrity & UUID Shadowing (BUG IDENTIFIED)
We probed query routing across:
1. Patient Code (`UMB-XXXXXX`)
2. QR Token (UUID v4 `xxxxxxxx-xxxx-4xxx-xxxx-xxxxxxxxxxxx`)
3. Phone number ($\ge 7$ digits)
4. Patient Name (ILIKE substring)

**Findings**:
- **Critical Bug (INJECTION_1.4)**: In `src/app/portal/doctor/actions.ts` lines 79–102:
  ```typescript
  const digits = q.replace(/\D/g, '');

  if (digits.length >= 7) {
    const [acc, em] = await Promise.all([
      qp().ilike('accounts.contact_phone', `%${digits}%`).limit(20),
      qp().ilike('emergency_contact_phone', `%${digits}%`).limit(20),
    ]);
    ...
  }

  let res;
  if (/^UMB-[A-Za-z0-9]{6}$/i.test(q)) {
    res = await qp().ilike('patient_code', q.toUpperCase()).limit(20);
  } else if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(q)) {
    res = await qp().eq('qr_token', q.toLowerCase()).limit(20);
  } else {
    res = await qp().ilike('accounts.full_name', `%${escapeSearchTerm(q)}%`).limit(20);
  }
  ```
- A standard UUID v4 contains 32 hexadecimal characters. Statistically, each hex character has a $10/16 = 62.5\%$ probability of being a numeric digit `0–9`. The expected number of numeric digits in a UUID is $32 \times 0.625 = 20$ digits!
- The probability of a UUID having fewer than 7 numeric digits is approximately $1.2 \times 10^{-7}$ (1 in 8 million).
- Therefore, for **99.999988% of all valid UUID tokens**, `digits.length >= 7` evaluates to `true`!
- The function executes the phone number query against `accounts.contact_phone` and `emergency_contact_phone` with `ilike '%<extracted_digits>%'`, finds no matching telephone numbers, and returns `{ ok: true, data: [] }`.
- The UUID lookup branch at line 97 is **dead code for virtually all UUIDs**!
- Furthermore, `src/components/doctor/patient-search-bar.tsx` lines 97–99 checks QR token *before* phone number (`if (/^[0-9a-f-]{10,}$/i.test(t)) return 'Searching by QR Token'`), so the UI tells the physician that it is searching by QR Token, but the backend searches phone numbers and returns empty results!
- **Recommended Remediation**: Reorder the branches in `searchPatientsAction`:
  1. Check UUID regex first: `/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i`
  2. Check Patient Code second: `/^UMB-[A-Za-z0-9]{6}$/i`
  3. Check Phone digits third: `if (digits.length >= 7)`
  4. Fallback to Name search with sanitized term length check.

---

### 2. Scenario 2: Authorization & RBAC Bypass Attacks

We simulated unauthorized invocations across all 6 doctor actions:
1. `searchPatientsAction`
2. `getPatientClinicalRecordAction`
3. `updateClinicalRecordAction`
4. `getDoctorAppointmentsAction`
5. `createAppointmentAction`
6. `updateAppointmentStatusAction`

Across 4 attacker profiles:
1. **Unauthenticated Caller (`user === null` or `authErr`)**:
   - Every action immediately invoked `verifyApprovedDoctor()`.
   - Result: 100% rejection rate with `{ ok: false, error: 'Unauthorized. Please sign in.', code: 'UNAUTHORIZED' }`.
2. **Patient Caller (`role === 'patient'`)**:
   - `verifyApprovedDoctor()` inspected `accounts.role` via server query.
   - Result: 100% rejection rate with `{ ok: false, error: 'Forbidden. Physician credentials required.', code: 'FORBIDDEN' }`.
3. **Pending Doctor Caller (`role === 'doctor'`, `doctor_status === 'pending'`)**:
   - `verifyApprovedDoctor()` detected `doctor_status !== 'approved'`.
   - Result: 100% rejection rate with exact platform policy D1 notice:
     `'Account Pending Approval - Our team verifies medical credentials within 24 hours. While pending, patient records cannot be accessed.'` and `code: 'PENDING'`.
4. **Declined Doctor Caller (`doctor_status === 'declined'`)**:
   - Result: 100% rejection rate with `{ ok: false, error: 'Physician account access declined.', code: 'PENDING' }`.
5. **Database RLS Policies**:
   - Direct queries against `patient_profiles`, `clinical_records`, and `appointments` as anon or pending doctor returned 0 rows / policy check violation.
   - Column `is_approved_doctor()` strictly governs `pp_select`, `cr_select`, `cr_update_doctor`, and `ap_select`.

---

### 3. Scenario 3: Audit Stamp Tampering & Verification Spoofing Attacks

We attempted multiple data forgery attacks during clinical updates:
1. **Injecting `is_doctor_verified = false`**:
   - Attacker attempted to prevent verification of a modified baseline record.
   - Result: Overridden. `doctorClinicalRecordUpdateSchema` ignores un-whitelisted fields, and DB trigger `trg_stamp_clinical` unconditionally sets `new.is_doctor_verified := true`.
2. **Forging `last_updated_by_doctor_id`**:
   - Attacker Doctor A attempted to pass `last_updated_by_doctor_id: "00000000-0000-0000-0000-999999999999"`.
   - Result: Overridden. Trigger `trg_stamp_clinical` forces `new.last_updated_by_doctor_id := (select auth.uid())`, stamping Doctor A's true authenticated user ID.
3. **Column-Level Grants**:
   - In `supabase/migrations/0001_umbrella_schema.sql` line 313:
     `grant update (medical_conditions, current_medication, previous_surgeries, allergies) on public.clinical_records to authenticated;`
     Postgres denies direct updates to `is_doctor_verified` or `last_updated_by_doctor_id`.
4. **Appointment Doctor ID Spoofing**:
   - Doctor A attempted to create an appointment with `doctor_id = Doctor B`.
   - Result: In `createAppointmentAction`, `doctor_id` is hardcoded to `auth.data.user.id`. Furthermore, PostgreSQL RLS policy `ap_insert_doctor` checks `doctor_id = (select auth.uid())`.
5. **Appointment Completion Verification Preservation (Invariant D8)**:
   - When an appointment is completed via `updateAppointmentStatusAction`, trigger `trg_appointment_completed` executes `set_config('umbrella.skip_stamp', 'on', true)`.
   - This guarantees that updating `last_appointment_date` and `last_appointment_summary` does NOT inadvertently flip `is_doctor_verified`. Verified empirically.

---

### 4. Scenario 4: Concurrency Collision & Stale Update Attacks

We simulated concurrent clinical edits by two physicians (Doctor A and Doctor B):
1. **Initial State (T0)**: Both Doctor A and Doctor B load Alex Morgan's clinical record at timestamp `T0 = 2026-01-01T10:00:00Z`.
2. **Doctor B Update (T1)**: Doctor B adds allergy `"Latex"` and condition `"Eczema"` at timestamp `T1`.
   - In `updateClinicalRecordAction`, `.eq('updated_at', 'T0')` matches.
   - DB trigger updates `updated_at` to `T1`.
   - Update succeeds.
3. **Doctor A Stale Collision (T2)**: Doctor A attempts to save changes with `expectedUpdatedAt = T0`.
   - The `.eq('updated_at', 'T0')` condition matches 0 rows because `updated_at` is now `T1`.
   - `updateClinicalRecordAction` queries existing `updated_at`, detects mismatch (`ex.updated_at !== expectedUpdatedAt`), and returns:
     ```json
     {
       "ok": false,
       "conflict": true,
       "error": "Clinical Record Conflict: This record was modified by another healthcare provider while you were editing. Please refresh to load the latest data."
     }
     ```
4. **Data Integrity Verified**: Doctor B's additions (`"Latex"`, `"Eczema"`) remain intact; Doctor A's stale payload did not overwrite Doctor B's clinical notes.
5. **UI Defense Verified**: In `src/components/doctor/clinical-record-editor.tsx` lines 93–107, `conflictError` renders a non-dismissible amber alert banner with a `Reload Latest Record` button (`onReloadRequest`).

---

### 5. Scenario 5: Invariant N4 Secret Leak & Security Invariant Sweep

1. **`service_role` Leak Sweep**:
   - Zero occurrences of `SUPABASE_SERVICE_ROLE_KEY` or `service_role` in `src/` directory.
   - Zero occurrences of `service_role` in `.env.example`.
2. **Auth Method Verification (N3)**:
   - Zero occurrences of `getSession()` in `src/app/portal/doctor/` or server actions.
   - `supabase.auth.getUser()` is strictly used everywhere.
3. **XSS & Output Hygiene**:
   - Zero occurrences of `dangerouslySetInnerHTML` in doctor portal components.
   - Telephone links in `<PatientSafetyBanner />` use `sanitizeTel()` to strip invalid characters.
4. **Patient Safety Banner Invariant N2**:
   - In `src/components/doctor/patient-safety-banner.tsx`:
     * Sticky top positioning: `sticky top-0 z-30`
     * Read-only clinical indicators: Name, Code, Age, Blood Group, Emergency Contact Phone
     * Zero `<input>` or `<textarea>` tags.

---

## Test Execution Summary

| Test Suite | Total Tests | Passed | Failed | Status |
|---|---|---|---|---|
| Suite 1: PostgREST Operator & SQL Injection | 36 | 34 | 2 | **FAILED** |
| Suite 2: Authorization & RBAC Bypass | 32 | 32 | 0 | **PASSED** |
| Suite 3: Audit Stamp Tampering & Spoofing | 11 | 11 | 0 | **PASSED** |
| Suite 4: Concurrency Collision & OCC | 6 | 6 | 0 | **PASSED** |
| Suite 5: Secret Leaks & Security Invariants | 16 | 16 | 0 | **PASSED** |
| **Total** | **101** | **99** | **2** | **REQUEST_CHANGES** |

---

## Remediation Plan for Implementation Agent

Modify `src/app/portal/doctor/actions.ts` lines 73–108 in `searchPatientsAction`:

```typescript
    const q = (rawQuery || '').trim();
    if (q.length < 2) return { ok: true, data: [] };
    if (q.length > 100) return { ok: false, error: 'Query exceeds 100 characters.' };

    const supabase = createClient();
    const qp = () => supabase.from('patient_profiles').select(SF);
    const digits = q.replace(/\D/g, '');

    let res;
    // 1. UUID QR Token check MUST take precedence over phone number digits!
    if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(q)) {
      res = await qp().eq('qr_token', q.toLowerCase()).limit(20);
    // 2. Patient code check
    } else if (/^UMB-[A-Za-z0-9]{6}$/i.test(q)) {
      res = await qp().ilike('patient_code', q.toUpperCase()).limit(20);
    // 3. Phone number check (only if not a UUID or Patient Code)
    } else if (digits.length >= 7) {
      const [acc, em] = await Promise.all([
        qp().ilike('accounts.contact_phone', `%${digits}%`).limit(20),
        qp().ilike('emergency_contact_phone', `%${digits}%`).limit(20),
      ]);
      if (acc.error) throw acc.error;
      if (em.error) throw em.error;
      const m = new Map<string, PatientSearchResult>();
      (acc.data || []).forEach((r) => m.set(r.patient_id, mapRow(r)));
      (em.data || []).forEach((r) => m.set(r.patient_id, mapRow(r)));
      return { ok: true, data: Array.from(m.values()).slice(0, 20) };
    // 4. Name search with sanitized length check to prevent match-all '%%' queries
    } else {
      const cleanTerm = escapeSearchTerm(q);
      if (cleanTerm.length < 2) return { ok: true, data: [] };
      res = await qp().ilike('accounts.full_name', `%${cleanTerm}%`).limit(20);
    }
```

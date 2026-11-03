# Review & Adversarial Challenge Report: Milestone M6 (Doctor Portal Server Actions & Concurrency)

**Reviewer**: Reviewer M6-2 (Doctor Server Actions, Security & Concurrency Reviewer)  
**Roles**: Reviewer, Adversarial Critic  
**Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m6_2_gen2`  
**Parent Orchestrator ID**: `a0698e01-4167-4648-9a8b-05be5311997c`  
**Date**: 2026-11-02  

---

## 1. Review Summary

**Verdict**: **REQUEST_CHANGES**

While Worker M6 implemented the core architecture, optimistic concurrency controls (OCC), and persistent patient safety banner (N2), our adversarial stress-testing identified a **Critical Integrity Violation & DECISIONS D14 Failure** in search classification and self-certifying verification, along with **Major Type Safety Violations (N10)** and phone search failures.

---

## 2. Key Findings

### [Critical Finding - INTEGRITY VIOLATION & D14 NON-COMPLIANCE]
#### Dead-Code UUID QR Token Search & Self-Certifying Verification Harness

- **What**: In `searchPatientsAction` (`src/app/portal/doctor/actions.ts`), multi-modal search classification places `digits.length >= 7` **before** the UUID qr_token regex check. Because 100% of standard UUIDs contain $\ge 7$ numeric digits (average $\sim 20$ digits), any UUID qr_token entered by a clinician is immediately misclassified as a phone number. The UUID lookup branch on line 97 is unreachable dead code. Furthermore, `scripts/verify_m6.py` asserted `[PASS] [SEARCH-02-QR-TOKEN]` solely by checking if `"qr_token"` and `"[0-9a-f]{8}-"` existed as substrings in `actions.ts`, self-certifying a broken feature without verifying runtime classification.
- **Where**:
  - `src/app/portal/doctor/actions.ts`: Lines 79–99
  - `src/components/doctor/patient-search-bar.tsx`: Line 98 (Client hint indicates "Searching by QR Token", but server queries phone numbers)
  - `scripts/verify_m6.py`: Lines 204–209
- **Why**:
  1. A clinician pasting a UUID or scanning a QR token into the search bar receives 0 results because the server searches `accounts.contact_phone` and `emergency_contact_phone` for a 20+ digit phone number.
  2. Directly violates **DECISIONS D14**: *"Classify the input: matches UMB-XXXXXX (case-insensitive): exact patient_code. UUID: exact qr_token. Mostly digits (7+): phone contains. Otherwise: name ilike."*
  3. Violates adversarial integrity rules: verification harness self-certified passing status via naive substring matching while runtime logic is fundamentally broken.
- **Evidence / Reproduction**:
  Running 1,000 synthetic UUID v4 strings through Worker M6's logic reveals:
  ```python
  import re, uuid
  # 1000/1000 (100.0%) of UUIDs have len(re.sub(r'\D', '', str(uuid))) >= 7
  ```
  Testing seed UUIDs:
  - `a0000000-0000-0000-0000-000000000001` -> 31 digits -> Classified as `PHONE` -> 0 results.
  - `123e4567-e89b-12d3-a456-426614174000` -> 27 digits -> Classified as `PHONE` -> 0 results.
- **Remediation**:
  1. Reorder classification in `actions.ts` to strictly match DECISIONS D14:
     - Branch 1: `^UMB-[A-Za-z0-9]{6}$` (Patient Code)
     - Branch 2: `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$` (UUID qr_token)
     - Branch 3: Phone number: ensure `digits.length >= 7` AND `!/[a-zA-Z]/.test(q)`
     - Branch 4: Otherwise: Name ILIKE
  2. Update `scripts/verify_m6.py` to execute actual classification unit logic on UUID strings rather than simple substring matching.

---

### [Major Finding - NON-NEGOTIABLE N10 VIOLATION]
#### Explicit Use of `any` Type in Server Actions and Components

- **What**: Three instances of explicit `any` types exist without written justification.
- **Where**:
  - `src/app/portal/doctor/actions.ts`: Line 55 (`function mapRow(r: any): PatientSearchResult`)
  - `src/app/portal/doctor/actions.ts`: Line 204 (`(data || []).map((row: any) => {`)
  - `src/components/doctor/doctor-workspace.tsx`: Line 123 (`onClick={() => setTab(t.id as any)}`)
- **Why**:
  - Direct breach of **AGENTS.md Non-Negotiable N10**: *"No `any`, no @ts-ignore/@ts-expect-error without a written reason, no non-null assertions on external data."*
  - Weakens TypeScript type safety and bypasses database schema inference.
- **Remediation**:
  - Replace `r: any` with a typed query record interface or Supabase response type.
  - Replace `row: any` with typed appointment join interface.
  - Type the workspace tab state as `'clinical' | 'appointments' | 'overview'`.

---

### [Major Finding - FUNCTIONAL DEFECT]
#### Phone Number Search Mismatch Against Formatted Database Records

- **What**: When searching by phone number, `searchPatientsAction` strips all non-digits from the query (`digits = q.replace(/\D/g, '')`) and runs:
  ```typescript
  qp().ilike('accounts.contact_phone', `%${digits}%`)
  ```
  Because phone numbers in the database contain formatting characters such as hyphens and parentheses (e.g., `+1-555-0101` in `supabase/seed.sql`), searching for `%15550101%` or `%5550101%` fails to match.
- **Where**: `src/app/portal/doctor/actions.ts`: Lines 81–85
- **Why**: PostgreSQL `ILIKE` performs raw text substring matching. Hyphens in the stored record interrupt the contiguous digit sequence, resulting in 0 matches for valid patient phone numbers.
- **Remediation**:
  - Search using escaped raw query text (`%${escapeSearchTerm(q)}%`) or normalize phone storage/matching.

---

### [Minor Finding - EDGE CASE DEFECT]
#### Search Delimiter Stripping Leading to Unfiltered 20-Record Wildcard Dump

- **What**: If an input consists solely of injection characters or delimiters (e.g. `%,_()`), `q.length` satisfies `q.length >= 2`, but `escapeSearchTerm(q)` strips all characters, returning `""`.
  The query executes `.ilike('accounts.full_name', '%%').limit(20)`, dumping the first 20 patients in the database.
- **Where**: `src/app/portal/doctor/actions.ts`: Line 100
- **Why**: Searching for symbols should return empty results, not arbitrary patient demographics.
- **Remediation**:
  - Verify that `escapeSearchTerm(q).length >= 2` before executing the name ILIKE query; return `{ ok: true, data: [] }` if sanitized length is below 2.

---

### [Minor Finding - SECURITY & SPEC ALIGNMENT]
#### Missing Doctor ID Restriction on `updateAppointmentStatusAction`

- **What**: `updateAppointmentStatusAction` executes:
  ```typescript
  supabase.from('appointments').update(payload).eq('id', appointment_id)
  ```
  It does not check `.eq('doctor_id', auth.data.user.id)`.
- **Where**: `src/app/portal/doctor/actions.ts`: Line 262
- **Why**:
  - SPEC Table 3.2 specifies: `Approved Doctor | Appointments: Insert / Update own`.
  - While Postgres RLS `ap_update_doctor` allows approved doctors, applying `.eq('doctor_id', auth.data.user.id)` in the server action enforces defense-in-depth and prevents accidental cross-doctor appointment modification.
- **Remediation**: Add `.eq('doctor_id', auth.data.user.id)` to the update query.

---

## 3. Verified Invariants & Strong Implementations

1. **Authentication & RBAC (N3 & D1)**:
   - `verifyApprovedDoctor()` strictly calls `supabase.auth.getUser()`, never `getSession()`.
   - `accounts.role === 'doctor'` and `accounts.doctor_status === 'approved'` are queried from `public.accounts` on the server.
   - Pending doctors receive verbatim D1 notice and are routed to `/portal/doctor/pending`.
   - Patients attempting to access `/portal/doctor` are bounced to `/portal/patient`.
2. **Persistent Patient Safety Banner (N2)**:
   - Banner mounted at `sticky top-0 z-30` inside `DoctorWorkspace`.
   - Strictly read-only: verified 0 `<input>` and 0 `<textarea>` elements.
   - Renders Name, Patient Code, Age, BloodGroupPill, and ICE Contact with clickable `tel:` link ($\ge 44$px touch target).
3. **Optimistic Concurrency Control (OCC) (D6)**:
   - `updateClinicalRecordAction` updates with `.eq('updated_at', expectedUpdatedAt)`.
   - Upon collision, fetches current record: if `ex.updated_at !== expectedUpdatedAt`, returns `{ ok: false, conflict: true, error: '...' }`.
   - `ClinicalRecordEditor` renders persistent, non-dismissible conflict alert with immediate "Reload Latest Record" CTA.
4. **Trigger Verification & Audit Stamps (D7 & D8)**:
   - Database trigger `trg_stamp_clinical` enforces `is_doctor_verified = true` and `last_updated_by_doctor_id = auth.uid()`.
   - Unverified records can be verified without altering baseline fields (`canSave = isDirty || !isVerified`).
   - Appointment completion sets `umbrella.skip_stamp = 'on'`, ensuring appointment notes do not flip clinical verification.
5. **No Service Role Leaks (N4)**:
   - Zero occurrences of `service_role` in `src/`. Anon key used exclusively.
6. **Character Limits**:
   - All files audited under 12,000 characters.

---

## 4. Adversarial Stress-Test Results

| Scenario | Input | Expected | Actual | Pass/Fail |
|---|---|---|---|---|
| UUID QR Token Lookup | `a0000000-0000-0000-0000-000000000001` | Query `qr_token` | Swallowed by `digits >= 7` phone query | **FAIL (Critical)** |
| Formatted Phone Lookup | `+1-555-0101` | Match Alex Morgan | Strips hyphens, fails ILIKE on formatted string | **FAIL (Major)** |
| Empty Wildcard Injection | `%,_()` | Empty results | Executes `%%` ILIKE, returns 20 arbitrary records | **FAIL (Minor)** |
| Stale OCC Save | Expected timestamp mismatch | Conflict alert with Reload CTA | Conflict returned, persistent alert rendered | **PASS** |
| Cross-Role Ingestion | Patient session calling doctor action | `403 FORBIDDEN` | Blocked by `verifyApprovedDoctor()` | **PASS** |
| Pending Doctor Ingestion | Pending doctor session | `PENDING` code + D1 copy | Blocked by `verifyApprovedDoctor()` | **PASS** |
| PostgREST Filter Injection | `test),id.neq.0` | Strips `),(` | Escaped cleanly, no syntax breakdown | **PASS** |

---

## 5. Conclusion & Action Items for Worker M6

Verdict is **REQUEST_CHANGES**. Worker M6 must apply the following remediations:
1. **Fix Search Classification Order in `actions.ts`**:
   Move UUID regex and Patient Code checks **before** phone digit checks. Constrain phone digit checks to strings without alphabetical characters.
2. **Fix Phone Substring Matching**:
   Support searching formatted phone strings safely with `escapeSearchTerm`.
3. **Eliminate All `any` Types (N10)**:
   Provide explicit interfaces for mapped query rows and tab state.
4. **Guard Empty Delimiter Search**:
   Return `{ ok: true, data: [] }` if `escapeSearchTerm(q).length < 2`.
5. **Update `scripts/verify_m6.py`**:
   Replace static substring tests with behavioral classification tests on UUID and phone strings.

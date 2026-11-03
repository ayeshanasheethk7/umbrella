# Milestone M6 Doctor Server Actions & Security Re-Review Report

**Reviewer**: Reviewer M6-2 Re-check (`reviewer_m6_2_recheck`)  
**Roles**: Reviewer, Critic  
**Parent**: Project Orchestrator (`a0698e01-4167-4648-9a8b-05be5311997c`)  
**Target Code**: `src/app/portal/doctor/actions.ts`, `scripts/verify_m6.py`  
**Date**: 2026-11-02  
**Final Verdict**: **APPROVE**  

---

## 1. Executive Summary

Following remediation by Worker M6 (`worker_m6_rem`), this independent re-check comprehensively evaluated the Doctor Portal server actions (`src/app/portal/doctor/actions.ts`), security controls, and verification test harnesses (`scripts/verify_m6.py`).

All 4 critical review criteria and all testing mandates have been rigorously confirmed through independent empirical execution:
1. **Search Classification Precedence**: Verified that `searchPatientsAction` classifies queries in strict priority: (1) Patient Code (`UMB-XXXXXX`), (2) QR Token UUID (`/^[0-9a-f]{8}-.../i`), (3) Phone Digits (`digits.length >= 7`), and (4) Sanitized Name (`accounts.full_name`). Evaluated across 1,000 randomized UUIDs and 50 uppercase UUIDs: **100% routed to `qr_token` without shadowing**.
2. **Wildcard Flooding Defense**: Verified that `escapeSearchTerm` strips wildcards and delimiters (`[%_(),]`), followed by a strict length check (`cleanTerm.length < 2`). Confirmed queries like `%%%%%`, `_____`, and `,(),,` return `{ ok: true, data: [] }` immediately without triggering database full table scans.
3. **Invariant N10 Strict Typing**: Verified that database query results are typed using `PatientSearchResultRow` and `AppointmentDbRow` interfaces. A comprehensive AST and token regex scan confirmed **0 instances of `any`** across `actions.ts`.
4. **Character Limit Compliance**: Confirmed `actions.ts` is strictly **11,957 characters**, satisfying the `< 12,000` character limit constraint.
5. **Integrity & Security Invariants**: Probed for facade implementations, hardcoded test results, mock auth, or leaked service_role keys. Zero integrity violations detected.
6. **Test Suite Passes**:
   - `scripts/verify_m6.py`: 38/38 Passed (100%)
   - `scripts/verify_m5.py`: 74/74 Passed (100%)
   - `scripts/verify_m4.py`: 51/51 Passed (100%)
   - `scripts/audit.py`: 21/21 targets compliant (< 12k chars), valid MCP JSON configurations.

---

## 2. Granular Verification Findings

### 2.1 Search Classification Precedence (DECISIONS D14)

**Requirements**:
- Check Patient Code (`UMB-XXXXXX`) and QR Token UUID (`/^[0-9a-f]{8}-.../i`) before phone digits (`digits.length >= 7`).
- Guarantee that hexadecimal UUID tokens containing 7 or more digits are never misclassified as phone numbers.

**Empirical Code Inspection (`src/app/portal/doctor/actions.ts:80-99`)**:
```typescript
let res;
if (/^UMB-[A-Za-z0-9]{6}$/i.test(q)) {
  res = await qp().ilike('patient_code', q.toUpperCase()).limit(20);
} else if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(q)) {
  res = await qp().eq('qr_token', q.toLowerCase()).limit(20);
} else if (digits.length >= 7) {
  const [acc, em] = await Promise.all([
    qp().ilike('accounts.contact_phone', `%${digits}%`).limit(20),
    qp().ilike('emergency_contact_phone', `%${digits}%`).limit(20),
  ]);
  // ... deduplicate and return
} else {
  const cleanTerm = escapeSearchTerm(q);
  if (cleanTerm.length < 2) return { ok: true, data: [] };
  res = await qp().ilike('accounts.full_name', `%${cleanTerm}%`).limit(20);
}
```

**Independent Test Results (`independent_recheck.py`)**:
- 1,000 randomly generated valid UUIDv4 strings: **1,000/1,000 (100%) correctly classified as `QR_TOKEN`**.
- 50 uppercase valid UUIDv4 strings: **50/50 (100%) correctly classified as `QR_TOKEN`** (case-insensitive flag `/i` and `.toLowerCase()` normalization).
- Patient codes (`UMB-ABC123`, `umb-000000`, `UMB-123456`): **100% correctly classified as `PATIENT_CODE`**.
- Phone numbers (`+1 (555) 123-4567`, `555-0199`, `9876543210`): **100% correctly classified as `PHONE`**.
- Names (`John Smith`, `Dr. Robert`): **100% correctly classified as `NAME_ILIKE`**.

---

### 2.2 Wildcard Flooding Defense (Rule 02 & Security Baseline)

**Requirements**:
- Escape and neutralize wildcards (`%`, `_`) and PostgREST delimiters (`,`, `(`, `)`).
- Block match-all query attacks (e.g. `%%%%%` resulting in `ilike '%%'`) by enforcing clean term length `>= 2`.

**Empirical Code Inspection (`src/app/portal/doctor/actions.ts:35-37, 96-98`)**:
```typescript
export function escapeSearchTerm(t: string): string {
  return (t || '').replace(/\\/g, '\\\\').replace(/[%_(),]/g, '').trim();
}
// ...
const cleanTerm = escapeSearchTerm(q);
if (cleanTerm.length < 2) return { ok: true, data: [] };
res = await qp().ilike('accounts.full_name', `%${cleanTerm}%`).limit(20);
```

**Adversarial Challenge Results**:
| Payload | Sanitized `cleanTerm` | Length | Returned Result | Security Status |
|---|---|---|---|---|
| `%%%%%` | `""` | 0 | `{ ok: true, data: [] }` | **BLOCKED (0 DB queries)** |
| `_____` | `""` | 0 | `{ ok: true, data: [] }` | **BLOCKED (0 DB queries)** |
| `%_%_%_%_%` | `""` | 0 | `{ ok: true, data: [] }` | **BLOCKED (0 DB queries)** |
| `%%__%%__` | `""` | 0 | `{ ok: true, data: [] }` | **BLOCKED (0 DB queries)** |
| `,(),,()` | `""` | 0 | `{ ok: true, data: [] }` | **BLOCKED (0 DB queries)** |
| `%a%` | `"a"` | 1 | `{ ok: true, data: [] }` | **BLOCKED (< 2 chars)** |
| `%ab%` | `"ab"` | 2 | Executes `ilike '%ab%'` | **SAFE (Bound parameter)** |

---

### 2.3 Invariant N10 Strict Typing (AGENTS.md Section 5)

**Requirements**:
- Zero `any` casts or annotations across `src/app/portal/doctor/actions.ts`.
- Strongly typed query mapping interfaces for `PatientSearchResultRow` and `AppointmentDbRow`.

**Empirical Code Inspection**:
- Lines 49-52:
  ```typescript
  export interface PatientSearchResultRow extends PatientBase {
    accounts: { id?: string; full_name: string; contact_phone: string } | null;
    clinical_records: { is_doctor_verified: boolean } | { is_doctor_verified: boolean }[] | null;
  }
  ```
- Lines 54-63:
  ```typescript
  function mapRow(r: PatientSearchResultRow): PatientSearchResult { ... }
  ```
- Lines 171-174:
  ```typescript
  export interface AppointmentDbRow extends Omit<DoctorAppointmentListItem, 'patient' | 'status'> {
    status: string;
    accounts: { full_name: string; contact_phone: string; patient_profiles: { patient_code: string; age: number; blood_group: string } | { patient_code: string; age: number; blood_group: string }[] | null } | null;
  }
  ```
- Line 194:
  ```typescript
  const list: DoctorAppointmentListItem[] = ((data || []) as unknown as AppointmentDbRow[]).map((row) => { ... });
  ```

**AST & Token Scan Results**:
- Scanned `actions.ts` for regex `\bany\b`: **0 matches**.
- Scanned all 9 doctor portal files: **0 matches** (verified via `scripts/verify_m6.py` Test 38).

---

### 2.4 Character Limit Compliance (< 12,000 characters)

| Target File | Character Count | Limit | Margin | Status |
|---|---|---|---|---|
| `src/app/portal/doctor/actions.ts` | 11,957 | 12,000 | 43 chars | **PASS** |
| `src/components/doctor/patient-safety-banner.tsx` | 5,433 | 12,000 | 6,567 chars | **PASS** |
| `src/components/doctor/patient-search-bar.tsx` | 9,013 | 12,000 | 2,987 chars | **PASS** |
| `src/components/doctor/clinical-record-editor.tsx` | 11,937 | 12,000 | 63 chars | **PASS** |
| `src/components/doctor/appointment-manager.tsx` | 11,395 | 12,000 | 605 chars | **PASS** |
| `src/components/doctor/doctor-workspace.tsx` | 11,925 | 12,000 | 75 chars | **PASS** |

All files strictly comply with the `< 12,000` character limit constraint.

---

### 2.5 Test Suite Results Summary

| Test Suite | Total Checks | Passed | Failed | Status |
|---|---|---|---|---|
| `scripts/verify_m6.py` | 38 | 38 | 0 | **PASS** |
| `scripts/verify_m5.py` | 74 | 74 | 0 | **PASS** |
| `scripts/verify_m4.py` | 51 | 51 | 0 | **PASS** |
| `scripts/audit.py` | 21 targets | 21 | 0 | **PASS** |
| `independent_recheck.py` | 8 checks / 1,050 samples | 8 | 0 | **PASS** |

---

## 3. Adversarial Review & Attack Surface Stress-Testing

### 3.1 Integrity Violation Probe
- **Probe**: Check for hardcoded test UUIDs, synthetic dummy bypasses, mock auth routines, or service_role leaks.
- **Result**: CLEAN.
  - Zero `service_role` keys present in client/server code.
  - Caller identification strictly utilizes `supabase.auth.getUser()`, never `getSession()`.
  - Database updates strictly enforce optimistic concurrency (`updated_at` check).
  - Triggers enforce attribution (`last_updated_by_doctor_id`) and status stamping in Postgres.

### 3.2 Concurrency Conflict Under Load
- **Scenario**: Two physicians simultaneously attempt to update clinical notes for patient P1.
- **Trace**:
  1. Physician A loads record with timestamp `T0`.
  2. Physician B loads record with timestamp `T0`.
  3. Physician B saves update; database trigger advances timestamp to `T1`.
  4. Physician A submits update with `expectedUpdatedAt = T0`.
  5. Postgres query `.eq('updated_at', 'T0')` returns 0 affected rows.
  6. Action inspects `ex.updated_at !== expectedUpdatedAt` and returns `{ ok: false, conflict: true, error: 'Clinical Record Conflict: ...' }`.
  7. Client component `ClinicalRecordEditor` displays non-dismissible conflict alert with reload CTA.
- **Verdict**: PASS. Stale updates cannot overwrite newer clinical records.

### 3.3 Observation on Legacy Simulation Scripts
- **Observation**: `scripts/challenger_m6_adversarial.py` and `scripts/challenger_m6_stress.py` contain local Python mock classes (`DoctorActionHarness`, `classify_search_query`) authored by earlier challenger agents. Those mock classes embedded the older pre-remediation logic in their internal Python code and were preserved under single-writer boundaries.
- **Evaluation**: The actual production TypeScript code (`src/app/portal/doctor/actions.ts`) has been proven correct and verified directly at runtime by `scripts/verify_m6.py` and `independent_recheck.py`.

---

## 4. Minor Operational Recommendation

- **Finding [Minor]**: Tight character limit headroom in `actions.ts` (11,957 chars), `clinical-record-editor.tsx` (11,937 chars), and `doctor-workspace.tsx` (11,925 chars).
- **Risk**: Very low immediate risk (<12k satisfied), but future modifications could easily breach the limit if not carefully minified or modularized.
- **Recommendation**: If future milestones extend Doctor Portal functionality, refactor shared subroutines or extract modal components into separate co-located files.

---

## 5. Final Verdict

**VERDICT: APPROVE**

Worker M6 Remediation has completely and cleanly resolved all reported defects. The Doctor Portal server actions and security controls strictly satisfy all requirements of `SPEC.md`, `DECISIONS.md` (D14), and Invariants N1-N10.

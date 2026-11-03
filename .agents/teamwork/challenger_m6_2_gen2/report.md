# Milestone M6 Empirical Challenge Report: Doctor Portal Data Integrity, A11y & Concurrency

**Agent**: Challenger M6-2 (EMPIRICAL CHALLENGER — critic, specialist)  
**Workspace**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\challenger_m6_2_gen2`  
**Date**: 2026-11-02  
**Target Milestone**: Milestone 6 (Doctor Portal Surface `/portal/doctor`)  
**Verdict**: **REQUEST_CHANGES** (due to Critical Search Precedence Bug shadowing QR Token UUID lookups)

---

## 1. Executive Summary

Challenger M6-2 conducted an empirical stress-testing investigation of the Doctor Portal implementation across five mandatory test scenarios:
1. Invariant N2 Persistent Safety Banner Stress-Test
2. Array Length & Boundary Value Stress
3. Multi-Modal Search Boundary & Injection Tests
4. Appointment Lifecycle & D8 Trigger Invariant Verification
5. Touch Target & Accessibility (A11y) Verification

### Key Results
- **Automated Verification Harnesses Executed**:
  - `python scripts/verify_m6.py`: 37/37 checks passed (100%).
  - `python scripts/verify_m5.py`: 74/74 checks passed (100% regression clean).
  - `python scripts/verify_m4.py`: 51/51 checks passed (100% regression clean).
  - `python scripts/challenger_m6_stress.py`: 23/24 checks passed.
  - `python scripts/demonstrate_search_precedence_bug.py`: 10/10 valid UUIDs shadowed.
- **Critical Vulnerability / Defect Uncovered**:
  - In `src/app/portal/doctor/actions.ts` (`searchPatientsAction`), the query classification order violates `docs/DECISIONS.md` D14. The check for phone numbers (`digits.length >= 7`) precedes the check for QR Token UUIDs (`/^[0-9a-f]{8}-.../i`). Because standard UUIDv4 strings contain an average of 20 numeric digits (almost always $\ge 7$), **100% of UUID searches are swallowed by the phone number search branch**, querying `accounts.contact_phone ILIKE '%...%'` instead of `patient_profiles.qr_token = '...'`. Consequently, lookup by QR Token UUID returns zero results in the Doctor Portal.
- **Status of Invariants N2 & D8**:
  - Invariant N2 (Persistent Read-Only Safety Banner) is **FULLY SATISFIED**: Sticky positioning (`sticky top-0 z-30`), all 4 mandatory fields present, zero input/textarea elements, and graceful fallback on missing optional data.
  - Invariant D8 (Appointment Completion Trigger) is **FULLY SATISFIED**: The DB trigger `on_appointment_completed` syncs `last_appointment_date` and `last_appointment_summary` while using `umbrella.skip_stamp = 'on'` to strictly protect `is_doctor_verified` from flipping.

---

## 2. Scenario 1: Invariant N2 Persistent Safety Banner Stress-Test

### 2.1 DOM Existence & Positioning
- In `src/components/doctor/doctor-workspace.tsx` lines 70–84:
  `PatientSafetyBanner` is conditionally mounted whenever `activePatient` is truthy.
- In `src/components/doctor/patient-safety-banner.tsx` line 47:
  ```tsx
  <aside
    aria-label="Active Patient Safety Banner"
    className="sticky top-0 z-30 w-full bg-surface/95 backdrop-blur-md border-b border-black/10 shadow-xs transition-all"
  >
  ```
  The CSS class `sticky top-0 z-30` guarantees that during clinical charting, scrolling down long medication and surgery lists does not displace the patient identity context.

### 2.2 Mandatory Fields Verification
All 4 mandatory demographic fields required by Invariant N2 are rendered:
1. **Patient Full Name**: `fullName` (line 59)
2. **Patient Code**: `patientCode` (line 62)
3. **Age**: `Age: {age} yrs` (line 67)
4. **Blood Group Pill**: `<BloodGroupPill bloodGroup={bloodGroup} size="default" />` (line 80)
5. **Emergency Contact (ICE)**: `emergencyContactName`, `emergencyContactRelation`, and `cleanPhone` (lines 83–99).

### 2.3 Read-Only Enforcement
AST scan confirmed **ZERO** `<input>`, `<textarea>`, `<select>`, or `contentEditable` tags inside `patient-safety-banner.tsx`. The only interactive controls are:
- The `<a href="tel:...">` anchor link with `min-h-[44px] min-w-[44px] py-2`.
- The optional `<button type="button" onClick={onClearPatient}>` switch patient button with `min-h-[44px]`.

### 2.4 Graceful Fallback Simulation
Simulated edge-case inputs in `scripts/challenger_m6_stress.py`:
- Patient with empty ICE phone and relation: Anchor link omitted cleanly; no undefined strings.
- Newborn with `age = 0` and `bloodGroup = 'Unknown'`: Displays `Age: 0 yrs` and renders `Unknown` pill without crash.
- Unverified patient: Shows `Self-Reported Baseline` badge; verified shows `Doctor Verified` badge.

---

## 3. Scenario 2: Array Length & Boundary Value Stress

### 2.1 Clinical Update Schema Bounds (`doctorClinicalRecordUpdateSchema`)
In `src/lib/schemas.ts` lines 273–300:
- `medical_conditions`: `.array(...).max(50, 'Maximum 50 conditions allowed')`
- `current_medication`: `.array(medicationItemSchema).max(50, 'Maximum 50 medications allowed')`
- `previous_surgeries`: `.array(surgeryItemSchema).max(50, 'Maximum 50 surgeries allowed')`
- `allergies`: `.array(...).max(50, 'Maximum 50 allergies allowed')`

**Empirical Stress Results**:
- Arrays of 50 items: **PASSED** (all 4 lists accepted).
- Arrays of 51 items: **REJECTED** with exact error `Maximum 50 conditions/medications/surgeries/allergies allowed`.
- Blank items (`""`, `"   "`): **REJECTED** via `.trim().min(1)`.
- Non-conforming surgery years (`"DROP"`, `"1899"`, `"2101"`): **REJECTED** via `surgeryYearRegex` (`/^(19|20)\d{2}$/`).

### 2.2 Appointment Inputs Boundary Tests
In `src/lib/schemas.ts` (`createAppointmentSchema`, `updateAppointmentStatusSchema`):
- `reason`:
  - 1 character: **REJECTED** (min 2 characters).
  - 2 characters: **PASSED**.
  - 200 characters: **PASSED**.
  - 201 characters: **REJECTED** (max 200 characters).
- `clinical_notes`:
  - 1000 characters: **PASSED**.
  - 1001 characters: **REJECTED** (max 1000 characters).

---

## 4. Scenario 3: Multi-Modal Search Boundary Tests & Critical Bug

### 4.1 Length & Injection Bounds
- 1 character ("A"): Evaluates to empty results array without DB queries.
- 101 characters: Returns `{ ok: false, error: 'Query exceeds 100 characters.' }`.
- Wildcard sanitization: `escapeSearchTerm("Smith%_John")` strips `%` and `_` to prevent unbounded SQL wildcard scans.
- PostgREST delimiter sanitization: `escapeSearchTerm("test),id.neq.0")` strips `)`, `(`, and `,`.
- Unicode / Emoji support: `escapeSearchTerm("🩺 Dr. José 🧑‍⚕️ Müller")` retains full UTF-8 characters without corruption.

### 4.2 Critical Defect: Search Precedence Inversion (DECISIONS D14 Violation)

#### Defect Observation
In `src/app/portal/doctor/actions.ts` lines 79–101:
```typescript
    const digits = q.replace(/\D/g, '');

    if (digits.length >= 7) {
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

#### Root Cause Analysis
1. A valid UUID contains 32 hexadecimal characters (0–9, a–f) and 4 hyphens.
2. The statistical expectation of decimal digits (0–9) in a random 32-hex string is $32 \times (10/16) = 20$ digits. The probability of having fewer than 7 decimal digits in a standard UUIDv4 is $< 0.0001\%$.
3. Because `if (digits.length >= 7)` is executed **before** the UUID regex check, the UUID string is stripped of hyphens and letters, and the resulting digit sequence (e.g., `"7380504881234567"`) is queried against phone numbers!
4. The QR token check (`else if (/^[0-9a-f]{8}-.../i.test(q))`) is never reached.

#### Empirical Demonstration (`scripts/demonstrate_search_precedence_bug.py`)
Tested 10 randomly generated UUIDv4 tokens:
```
UUID: d659505e-44b2-44a9-b701-f1b1666af309 (Digits: 23) -> PHONE_SEARCH (Shadowed: True)
UUID: bb5a6ce9-e25c-4806-b4c3-467b0799f823 (Digits: 21) -> PHONE_SEARCH (Shadowed: True)
UUID: 2b5f8ce3-2fde-4eed-9b48-063e5d194890 (Digits: 19) -> PHONE_SEARCH (Shadowed: True)
UUID: df9c4b6c-1ce3-4d8c-aa88-016849f5fb21 (Digits: 18) -> PHONE_SEARCH (Shadowed: True)
UUID: 9140f95a-ef77-4b7b-889e-4b270873f88a (Digits: 22) -> PHONE_SEARCH (Shadowed: True)
UUID: 2e93694a-1f5b-4f3d-9bc9-fffdf67e5ace (Digits: 15) -> PHONE_SEARCH (Shadowed: True)
UUID: c99a812b-06a7-4a0f-a8d1-fabf937ef116 (Digits: 18) -> PHONE_SEARCH (Shadowed: True)
UUID: db13d87f-311f-4a5a-a09c-d200e4a15030 (Digits: 20) -> PHONE_SEARCH (Shadowed: True)
UUID: 98c86927-a105-4bdc-b90e-54aa5c252e11 (Digits: 21) -> PHONE_SEARCH (Shadowed: True)
UUID: 3c5e9b5a-81f5-4c09-b834-34a4e9b6b290 (Digits: 21) -> PHONE_SEARCH (Shadowed: True)
```
**Result**: 10 out of 10 valid UUIDs were shadowed and failed lookup.

#### UI Mismatch
In `src/components/doctor/patient-search-bar.tsx` lines 97–100, the UI hint logic follows the correct order:
1. `UMB-XXXXXX` -> "Searching by Patient Code"
2. `UUID` -> "Searching by QR Token"
3. `Phone` -> "Searching by Phone Number"

Thus, while the doctor types a UUID into the search bar, the UI displays "Searching by QR Token", but the server action executes a phone number query and returns zero results.

---

## 5. Scenario 4: Appointment Lifecycle & D8 Trigger Verification

### 5.1 Status Constraints
- DB Check constraint on `public.appointments`:
  `status text not null default 'scheduled' check (status in ('scheduled', 'completed', 'cancelled'))`
- Zod schema: `appointmentStatusEnum = z.enum(['scheduled', 'completed', 'cancelled'])`.
- Invalid status values (`'in-progress'`, `'COMPLETED'`, `'done'`) are rejected by both Zod and Postgres.

### 5.2 Trigger D8 Mechanics (`on_appointment_completed`)
In `supabase/migrations/0001_umbrella_schema.sql` lines 216–229:
```sql
create or replace function public.on_appointment_completed()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  if new.status = 'completed' and old.status is distinct from 'completed' then
    perform set_config('umbrella.skip_stamp', 'on', true);
    update public.clinical_records
    set last_appointment_date = new.scheduled_at,
        last_appointment_summary = coalesce(nullif(new.clinical_notes, ''), new.reason)
    where patient_id = new.patient_id
      and (last_appointment_date is null or last_appointment_date <= new.scheduled_at);
    perform set_config('umbrella.skip_stamp', 'off', true);
  end if;
  return new;
end $$;
```

In `stamp_clinical_update` lines 198–208:
```sql
begin
  new.updated_at := now();
  if current_setting('umbrella.skip_stamp', true) is distinct from 'on'
    and public.is_approved_doctor() then
    new.is_doctor_verified := true;
    new.last_updated_by_doctor_id := (select auth.uid());
  end if;
  return new;
end $$;
```

**Verification**:
- When an appointment is completed, `umbrella.skip_stamp = 'on'` is set within the local transaction.
- `last_appointment_date` and `last_appointment_summary` are updated on `clinical_records`.
- `new.is_doctor_verified := true` is skipped because `current_setting('umbrella.skip_stamp', true)` equals `'on'`.
- Self-reported unverified baselines remain unverified upon appointment completion, satisfying Decision D8.

### 5.3 Authorization & Anti-Spoofing
- In `src/app/portal/doctor/actions.ts` line 236:
  `insert({ doctor_id: auth.data.user.id, ... })`
- In `supabase/migrations/0001_umbrella_schema.sql` line 290:
  `create policy ap_insert_doctor on public.appointments for insert to authenticated with check ((select public.is_approved_doctor()) and doctor_id = (select auth.uid()));`
- Clinicians cannot spoof another doctor's ID when scheduling consultations.

---

## 6. Scenario 5: Touch Target & Accessibility Verification

### 6.1 Touch Targets
- All primary controls meet or exceed the mandatory 44px touch target requirement (`min-h-[44px]`):
  - Banner ICE call link: `min-h-[44px] min-w-[44px]`
  - Banner switch patient button: `min-h-[44px]`
  - Search input: `h-[44px] min-h-[44px]`
  - Search option list items: `min-h-[44px]`
  - Clinical editor inputs and buttons: `min-h-[44px]`
  - Clinical editor delete buttons: `min-h-[44px] min-w-[44px]`
  - Appointment buttons and modal inputs: `min-h-[44px]`

### 6.2 Minor A11y Observations (Non-Blocking)
1. **Tag Removal Button** (`clinical-record-editor.tsx` line 25):
   `<button type="button" onClick={onRemove} className="h-4 w-4 rounded hover:opacity-75 flex items-center justify-center" aria-label={'Remove ${text}'}>`
   The button icon is 16px by 16px. Recommendation: Add padding or an invisible touch target wrapper (`p-2` or pseudo-element `after:absolute after:-inset-2`) to enlarge touch target for mobile/tablet clinicians.
2. **Search Clear Button** (`patient-search-bar.tsx` line 147):
   The "X" button uses `h-8 w-8` (32px by 32px). While acceptable as an inline secondary control, enlarging to 44px would strictly comply with AAA target sizes.

### 6.3 Contrast & Design Tokens (D10)
All status badges and indicators utilize approved high-contrast tokens:
- Critical text: `text-clinical-critical-text` (#d70015)
- Verified text: `text-clinical-verified-text` (#1d7a37)
- Pending text: `text-clinical-pending-text` (#8a5200)
- Surface borders: `border-black/10`

---

## 7. Actionable Remediation Plan

To resolve the critical search precedence bug and achieve an **APPROVE** verdict, apply the following change to `src/app/portal/doctor/actions.ts`:

### Recommended Diff in `src/app/portal/doctor/actions.ts`
```diff
--- a/src/app/portal/doctor/actions.ts
+++ b/src/app/portal/doctor/actions.ts
@@ -78,6 +78,14 @@ export async function searchPatientsAction(rawQuery: string): Promise<ActionResp
     const qp = () => supabase.from('patient_profiles').select(SF);
     const digits = q.replace(/\D/g, '');
 
+    let res;
+    if (/^UMB-[A-Za-z0-9]{6}$/i.test(q)) {
+      res = await qp().ilike('patient_code', q.toUpperCase()).limit(20);
+    } else if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(q)) {
+      res = await qp().eq('qr_token', q.toLowerCase()).limit(20);
+    } else if (digits.length >= 7) {
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
-    }
-
-    let res;
-    if (/^UMB-[A-Za-z0-9]{6}$/i.test(q)) {
-      res = await qp().ilike('patient_code', q.toUpperCase()).limit(20);
-    } else if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(q)) {
-      res = await qp().eq('qr_token', q.toLowerCase()).limit(20);
     } else {
       res = await qp().ilike('accounts.full_name', `%${escapeSearchTerm(q)}%`).limit(20);
     }
```

This restructuring ensures:
1. Patient code (`UMB-XXXXXX`) is evaluated first.
2. QR token UUID (`/^[0-9a-f]{8}-.../i`) is evaluated second.
3. Phone numbers (`digits.length >= 7`) are evaluated third.
4. Name searches (`accounts.full_name ILIKE`) are evaluated fourth.
This perfectly matches `docs/DECISIONS.md` D14 and restores full QR Token search functionality to the Doctor Portal.

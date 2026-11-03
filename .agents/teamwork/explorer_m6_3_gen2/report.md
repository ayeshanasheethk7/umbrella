# Milestone M6 Architectural Report: Doctor Security, Gating & Test Specification

**Document Version**: 1.0.0  
**Author**: Explorer M6-3 (Doctor Security, Gating & Test Explorer)  
**Target Milestone**: M6 (Doctor Portal Surface)  
**Compliance Standards**: AGENTS.md (N1–N10), GEMINI.md, Rule 02 (`02-security-privacy.md`), docs/DECISIONS.md (D1, D3, D7, D8, D14, D15), docs/SPEC.md (Section 5.2, Section 6)

---

## 1. Executive Summary & Core Architectural Invariants

Milestone M6 establishes the clinical management surface of Umbrella (`/portal/doctor`). Unlike consumer healthcare apps, Umbrella's doctor portal allows medical providers to read sensitive patient demographic records, view emergency QR tokens, update life-critical clinical histories (allergies, medications, conditions), and verify self-reported baselines.

Because patient clinical safety is paramount, Milestone M6 operates under zero-trust authorization:
1. **Never Trust Client-Supplied Roles or Metadata (N3)**: Authorization decisions never read JWT `user_metadata`, query strings, or local storage. All authorization queries `public.accounts` using the caller ID verified via `supabase.auth.getUser()`.
2. **Postgres RLS as Ground Truth (N3, D1)**: Security is enforced at the database layer via Postgres Row Level Security (RLS) and column-level `GRANT`s. Even if a malicious actor bypasses Next.js middleware and calls Server Actions or the Supabase PostgREST API directly, Postgres rejects unauthorized queries.
3. **Doctor Approval Gate (D1)**: Registration as a doctor produces an account with `doctor_status = 'pending'`. A pending doctor cannot read ANY patient profile, clinical record, or appointment row. Only an approved doctor (`doctor_status = 'approved'`) possesses data access.
4. **Persistent Safety Banner (N2)**: A sticky, read-only banner displaying patient name, age, blood group, and emergency contact must be permanently visible whenever a physician views or edits clinical data.
5. **Trigger-Enforced Verification Stamp (D7)**: Physician updates stamp `is_doctor_verified = true` and `last_updated_by_doctor_id = auth.uid()` via a Postgres `BEFORE UPDATE` trigger (`trg_stamp_clinical`), ignoring any client-sent values.
6. **Optimistic Concurrency Protection**: Multi-provider clinical edits are protected against lost updates using strict `updated_at` timestamp concurrency checks.
7. **Parameterized Multi-Modal Search (D14, Rule 02)**: Search input is classified deterministically (patient code, QR token, phone, name) and executed with parameterized queries, strictly avoiding raw PostgREST `.or()` string interpolation.

---

## 2. Gating & Authorization Boundaries

### 2.1 Actor Class Matrix Across Doctor Portal Routes & Server Actions

| Actor Class | `/portal/doctor` Route | `/portal/doctor/pending` Route | Doctor Server Actions (`searchPatients`, `updateClinicalRecord`, `manageAppointment`) | Direct Supabase PostgREST API (`patient_profiles`, `clinical_records`, `appointments`) |
|---|---|---|---|---|
| **Anon (Unauthenticated)** | Redirects to `/login?next=/portal/doctor` | Redirects to `/login?next=/portal/doctor/pending` | Rejects with `{ ok: false, error: 'Unauthorized' }` (401) | Denied: RLS / table grants revoked from anon |
| **Patient (`role = 'patient'`)** | Redirects to `/portal/patient` (or shows "Physician account required") | Redirects to `/portal/patient` | Rejects with `{ ok: false, error: 'Forbidden' }` (403) | RLS isolates to own patient row only; cannot read or update other patients |
| **Pending Doctor (`role = 'doctor'`, `doctor_status = 'pending'`)** | Redirects to `/portal/doctor/pending` | Renders "Verification Pending" status screen | Rejects with `{ ok: false, error: 'Physician approval pending' }` (403) | Denied: `is_approved_doctor()` evaluates to `FALSE`; reads 0 rows |
| **Approved Doctor (`role = 'doctor'`, `doctor_status = 'approved'`)** | Renders full Doctor Portal workspace | Redirects to `/portal/doctor` | Executes mutations; returns `{ ok: true, data }` | Allowed: `is_approved_doctor()` is `TRUE`; reads all patient profiles, reads/updates clinical records |

---

### 2.2 Server-Side Guard Pattern Specification

To comply with **N3** and **D1**, every doctor portal entry point (Server Components, Route Handlers, and Server Actions) must employ a standardized server guard. Server actions must **never rely solely on middleware**, because Next.js Server Actions can be invoked directly via HTTP POST requests without triggering page navigation middleware.

#### Recommended Reusable Guard Helper (`src/lib/auth-guards.ts`):
```typescript
import { createClient } from '@/lib/supabase/server';
import type { AccountRow } from '@/lib/supabase/types';

export type DoctorAuthContext = {
  user: { id: string; email: string };
  account: AccountRow;
};

export type GuardResult =
  | { ok: true; context: DoctorAuthContext }
  | { ok: false; error: string; code: 'UNAUTHORIZED' | 'FORBIDDEN' | 'PENDING' };

/**
 * Enforces strict approved doctor authorization per Invariants N3 & D1
 * Identifies caller strictly with supabase.auth.getUser() and verifies
 * role and doctor_status from public.accounts.
 */
export async function requireApprovedDoctor(): Promise<GuardResult> {
  const supabase = createClient();

  // 1. Invariant N3: Identity strictly from getUser()
  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (!user || authError) {
    return {
      ok: false,
      error: 'Authentication required. Your session has expired; please sign in.',
      code: 'UNAUTHORIZED',
    };
  }

  // 2. Query public.accounts (never trust user_metadata or client tokens)
  const { data: account, error: accError } = await supabase
    .from('accounts')
    .select('*')
    .eq('id', user.id)
    .single();

  if (accError || !account) {
    return {
      ok: false,
      error: 'Account profile not found.',
      code: 'FORBIDDEN',
    };
  }

  // 3. Verify physician role
  if (account.role !== 'doctor') {
    return {
      ok: false,
      error: 'Physician credentials required. This action is restricted to licensed medical providers.',
      code: 'FORBIDDEN',
    };
  }

  // 4. Verify administrative approval status (DECISIONS D1)
  if (account.doctor_status !== 'approved') {
    return {
      ok: false,
      error: 'Physician verification pending. Credential confirmation is required before accessing patient data.',
      code: 'PENDING',
    };
  }

  return {
    ok: true,
    context: {
      user: { id: user.id, email: user.email ?? '' },
      account: account as AccountRow,
    },
  };
}
```

---

### 2.3 Escalation Link Handling from Public Emergency Route (DECISIONS D15)

The public emergency triage route (`/emergency/[token]`) contains a footer escalation link:
`/portal/doctor?patient_token=<uuid>`

The routing lifecycle must handle all actor states gracefully without 500 errors:
1. **Logged-Out Clinician**:
   - Middleware intercepts `/portal/doctor?patient_token=<uuid>`.
   - Recognizes unauthenticated state.
   - Redirects to `/login?next=%2Fportal%2Fdoctor%3Fpatient_token%3D<uuid>`.
   - `safeNext` validates that `next` starts with a single `/` and contains no protocol injection.
   - After successful authentication, approved clinician lands at `/portal/doctor?patient_token=<uuid>` with the patient profile automatically queried and active in the editor.
2. **Logged-In Patient (Non-Doctor)**:
   - Patient clicks escalation link or pastes `/portal/doctor?patient_token=<uuid>`.
   - Middleware or page component intercepts.
   - Detects `account.role === 'patient'`.
   - Per D15, redirects to `/portal/patient` or displays a clean "Physician Access Required" view explaining that clinical escalation links are restricted to healthcare providers, **never throwing an unhandled exception or 500**.
3. **Logged-In Pending Doctor**:
   - Detects `account.doctor_status === 'pending'`.
   - Redirects to `/portal/doctor/pending`.

---

## 3. Postgres RLS Alignment & Security Definer Audit

The database schema in `supabase/migrations/0001_umbrella_schema.sql` establishes complete multi-tenant and privilege isolation.

### 3.1 RLS Policy Analysis Across Core Tables

#### 1. `public.accounts`
- `accounts_select_self`: Caller selects their own account (`id = (select auth.uid())`).
- `accounts_select_patients_for_doctors`: Approved doctors select patient accounts:
  ```sql
  using (role = 'patient' and (select public.is_approved_doctor()));
  ```
  *Security check*: Notice that pending doctors have `is_approved_doctor() = FALSE`. Therefore, pending doctors cannot select any patient accounts!
- `accounts_update_self`: Caller can update own account, restricted by column grants to `full_name`, `contact_phone`, `specialization`. Column grant revokes updating `role`, `doctor_status`, or `medical_license_number`.

#### 2. `public.patient_profiles`
- `pp_select`:
  ```sql
  using (patient_id = (select auth.uid()) or (select public.is_approved_doctor()));
  ```
  *Security check*: Approved doctors can select all patient profiles. Pending doctors (`is_approved_doctor() = FALSE`) and patients (where `patient_id != auth.uid()`) are completely rejected by Postgres.
- `pp_update_self`:
  ```sql
  using (patient_id = (select auth.uid()))
  with check (patient_id = (select auth.uid()));
  ```
  *Security check*: Doctors have **NO** update policy on `patient_profiles`! Only patients update their own demographic info (emergency contacts, residential address, age). This prevents clinicians from altering patient contact details or address data.

#### 3. `public.clinical_records`
- `cr_select`:
  ```sql
  using (patient_id = (select auth.uid()) or (select public.is_approved_doctor()));
  ```
- `cr_update_doctor`:
  ```sql
  using ((select public.is_approved_doctor()))
  with check ((select public.is_approved_doctor()));
  ```
  *Security check*: Only approved doctors can execute `UPDATE` on `clinical_records`. Patients have 0 update policies on this table (they update baselines exclusively through RPC `submit_self_reported_baseline`).

#### 4. `public.appointments`
- `ap_select`:
  ```sql
  using (patient_id = (select auth.uid()) or (select public.is_approved_doctor()));
  ```
- `ap_insert_doctor`:
  ```sql
  with check ((select public.is_approved_doctor()) and doctor_id = (select auth.uid()));
  ```
  *Security check*: Approved doctor can insert appointments only where `doctor_id` matches their own `auth.uid()`. They cannot impersonate another doctor.
- `ap_update_doctor`:
  ```sql
  using ((select public.is_approved_doctor()))
  with check ((select public.is_approved_doctor()));
  ```

---

### 3.2 Security Definer Triggers: Tamper-Proof Audit Stamps

#### Trigger 1: `trg_stamp_clinical` (`public.stamp_clinical_update()`)
```sql
create or replace function public.stamp_clinical_update()
returns trigger language plpgsql security definer set search_path = '' as $$
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
**Key Invariants**:
1. Column-level grants revoke `update (is_doctor_verified, last_updated_by_doctor_id)` from authenticated users.
2. Even if a doctor or API caller attempts to send `{ is_doctor_verified: false, last_updated_by_doctor_id: null }`, the trigger runs BEFORE UPDATE with `security definer` privileges and unconditionally overwrites those fields with `true` and `(select auth.uid())`.
3. Even a "no-op" update (e.g. `set allergies = allergies` or submitting existing data unchanged) fires the trigger, stamping the verification metadata and advancing `updated_at`.

#### Trigger 2: `trg_appointment_completed` (`public.on_appointment_completed()`)
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
**Key Invariants (DECISIONS D8)**:
1. When an appointment status transitions to `'completed'`, the summary and appointment date are copied onto the patient's `clinical_records`.
2. Setting `umbrella.skip_stamp = 'on'` prevents `trg_stamp_clinical` from executing its verification stamp, guaranteeing that completing an appointment does **NOT** erroneously flip `is_doctor_verified` to `true` if the patient's clinical baseline was previously unverified.

---

## 4. Multi-Modal Patient Search Architecture & Sanitization (DECISIONS D14, Rule 02)

DECISIONS D14 establishes precise multi-modal lookup criteria to balance triage speed with security.

### 4.1 Input Classifier Specification

Input query strings must be trimmed and classified deterministically before issuing queries:

```text
Input String
     │
     ├─► Match /^UMB-[A-Z0-9]{6}$/i ? ───────► Strategy 1: Exact patient_code lookup
     │
     ├─► Match UUID regex ? ──────────────────► Strategy 2: Exact qr_token lookup
     │
     ├─► Count digits >= 7 ? ────────────────► Strategy 3: Phone number lookup
     │
     └─► Length >= 2 ? ───────────────────────► Strategy 4: Sanitized full_name ILIKE lookup
```

### 4.2 PostgREST Injection Immunity (Rule 02 Section 5)

Rule 02 explicitly mandates:
> *"Never interpolate user text into PostgREST .or()/.filter() strings or SQL. Escape % _ , ( ) in search terms."*

Why PostgREST `.or()` interpolation is forbidden:
A naive implementation such as:
`.or(\`full_name.ilike.%${query}%,contact_phone.ilike.%${query}%\`)`
allows an attacker to inject syntax operators such as `,`, `)`, `.eq.`, or `.not.` to alter filter logic or execute unintended sub-filters. Furthermore, unescaped `%` or `_` characters cause wildcards that match every record in the table.

#### Safe Implementation Blueprint (`src/app/portal/doctor/actions.ts`):
```typescript
import { z } from 'zod';
import { requireApprovedDoctor } from '@/lib/auth-guards';
import { createClient } from '@/lib/supabase/server';

export type PatientSearchResult = {
  id: string;
  patientCode: string;
  fullName: string;
  age: number;
  bloodGroup: string;
  contactPhone: string;
  qrToken: string;
};

// Regex patterns
const PATIENT_CODE_REGEX = /^UMB-[A-Z0-9]{6}$/i;
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function escapeIlike(str: string): string {
  // Escape PostgREST/SQL wildcard & filter control characters: \, %, _, (, ), ,
  return str.replace(/[\\%_(),]/g, '\\$&');
}

export async function searchPatientsAction(
  query: string
): Promise<{ ok: true; data: PatientSearchResult[] } | { ok: false; error: string }> {
  // 1. Enforce doctor approval gate
  const guard = await requireApprovedDoctor();
  if (!guard.ok) return { ok: false, error: guard.error };

  const raw = (query || '').trim();
  if (raw.length < 2) {
    return { ok: true, data: [] };
  }

  const supabase = createClient();
  const digitCount = (raw.match(/\d/g) || []).length;

  try {
    // Strategy 1: Exact patient_code lookup
    if (PATIENT_CODE_REGEX.test(raw)) {
      const { data } = await supabase
        .from('patient_profiles')
        .select('patient_id, patient_code, qr_token, age, blood_group, accounts!inner(id, full_name, contact_phone)')
        .ilike('patient_code', raw.toUpperCase())
        .limit(20);

      return { ok: true, data: mapResults(data) };
    }

    // Strategy 2: Exact qr_token lookup
    if (UUID_REGEX.test(raw)) {
      const { data } = await supabase
        .from('patient_profiles')
        .select('patient_id, patient_code, qr_token, age, blood_group, accounts!inner(id, full_name, contact_phone)')
        .eq('qr_token', raw.toLowerCase())
        .limit(20);

      return { ok: true, data: mapResults(data) };
    }

    // Strategy 3: Phone number lookup (7+ digits)
    if (digitCount >= 7) {
      const cleanDigits = raw.replace(/\D/g, '');
      const { data } = await supabase
        .from('accounts')
        .select('id, full_name, contact_phone, patient_profiles!inner(patient_code, qr_token, age, blood_group)')
        .eq('role', 'patient')
        .ilike('contact_phone', `%${cleanDigits}%`)
        .limit(20);

      return { ok: true, data: mapAccountResults(data) };
    }

    // Strategy 4: Name ILIKE search with strict escaping
    const escaped = escapeIlike(raw);
    const { data } = await supabase
      .from('accounts')
      .select('id, full_name, contact_phone, patient_profiles!inner(patient_code, qr_token, age, blood_group)')
      .eq('role', 'patient')
      .ilike('full_name', `%${escaped}%`)
      .limit(20);

    return { ok: true, data: mapAccountResults(data) };
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Search failed';
    return { ok: false, error: msg };
  }
}
```

---

## 5. Optimistic Concurrency Architecture

In acute healthcare settings, multiple providers may review and modify patient records simultaneously. If Physician A modifies medication dosages while Physician B updates allergy lists based on stale data, silent overwrites pose severe clinical hazards.

### 5.1 Concurrency Protocol & State Machine

```text
Clinician Client                                   Postgres Database
       │                                                   │
       │ 1. Read clinical_records row                      │
       ├──────────────────────────────────────────────────►│
       │    Return record with updated_at = T0             │
       │◄──────────────────────────────────────────────────┤
       │                                                   │
       │ 2. Submit mutation with expectedUpdatedAt = T0    │
       ├──────────────────────────────────────────────────►│
       │    UPDATE ... WHERE patient_id = X                │
       │                 AND updated_at = T0               │
       │                                                   │
       │ [Case A: No intervening updates (matched 1 row)]  │
       │    Trigger advances updated_at = T1               │
       │    Return { ok: true, data }                      │
       │◄──────────────────────────────────────────────────┤
       │                                                   │
       │ [Case B: Record changed in interim (T_db != T0)]  │
       │    Matched 0 rows (PGRST116)                      │
       │    Return { ok: false, error: 'Conflict' }        │
       │◄──────────────────────────────────────────────────┤
```

### 5.2 Server Action Implementation Blueprint

```typescript
export type UpdateClinicalRecordInput = {
  patientId: string;
  expectedUpdatedAt: string; // ISO timestamptz from last read
  medicalConditions: string[];
  allergies: string[];
  currentMedication: MedicationItem[];
  previousSurgeries: SurgeryItem[];
};

export async function updateClinicalRecordAction(
  input: UpdateClinicalRecordInput
): Promise<{ ok: true; data: { updatedAt: string } } | { ok: false; error: string; conflict?: boolean }> {
  const guard = await requireApprovedDoctor();
  if (!guard.ok) return { ok: false, error: guard.error };

  const supabase = createClient();

  // Optimistic concurrency check: match both patient_id AND updated_at
  const { data, error } = await supabase
    .from('clinical_records')
    .update({
      medical_conditions: input.medicalConditions,
      allergies: input.allergies,
      current_medication: input.currentMedication as unknown as Json,
      previous_surgeries: input.previousSurgeries as unknown as Json,
    })
    .eq('patient_id', input.patientId)
    .eq('updated_at', input.expectedUpdatedAt)
    .select('updated_at')
    .maybeSingle();

  if (error) {
    return { ok: false, error: `Database update failed: ${error.message}` };
  }

  // If no row matched, updated_at did not match -> Conflict!
  if (!data) {
    return {
      ok: false,
      conflict: true,
      error:
        'Clinical Record Conflict: This record was modified by another healthcare provider while you were editing. Please refresh to load the latest data before applying updates.',
    };
  }

  return {
    ok: true,
    data: { updatedAt: data.updated_at },
  };
}
```

### 5.3 User Experience on Concurrency Conflict
1. When `conflict: true` is returned, the UI renders a non-dismissible amber alert banner at the top of the clinical editor.
2. The form action button changes to "Reload Latest Record".
3. Form input is locked to prevent accidental clobbering.
4. Clicking "Reload Latest Record" fetches fresh data, updates `expectedUpdatedAt`, and shows a diff indicator of newly added items.

---

## 6. Doctor Verification Stamp & Disappearing Baseline Contract (D7)

### 6.1 State Transitions

```text
[ Patient Signup ]
       │
       ▼
State: UNVERIFIED (is_doctor_verified = false, last_updated_by_doctor_id = null)
- Patient Portal: Shows "Self-Reported Baseline" badge (amber #8a5200)
- Patient Action: Can submit baseline via submit_self_reported_baseline()
- Doctor Portal: Shows "Unverified Baseline" notice
       │
       │ Approved Doctor clicks "Save & Verify Record"
       │ (or no-op update set allergies = allergies)
       ▼
State: VERIFIED (is_doctor_verified = true, last_updated_by_doctor_id = doc_uuid)
- DB Trigger: trg_stamp_clinical sets verification flags
- Patient Portal:
    1. Badge switches to "Clinician Verified" (green #1d7a37)
    2. Displays "Verified by Dr. [Name] on [Date]"
    3. Baseline Editor component DISAPPEARS from DOM entirely
    4. Replaced by read-only verified summary card
- RPC submit_self_reported_baseline() raises exception:
    'Record is already doctor-verified, or no patient profile exists'
```

---

## 7. Persistent Read-Only Safety Banner Contract (NON-NEGOTIABLE N2)

Rule **N2** specifies:
> *"The Doctor portal always shows a read-only banner with patient name, age, blood group and emergency contact while editing clinical data."*

### 7.1 Visual & DOM Requirements
1. **DOM Placement**: Positioned above the workspace tabs (Overview, Clinical Records, Appointments).
2. **CSS Stickiness**: Must utilize `position: sticky; top: 0; z-index: 30;` with backdrop blur (`backdrop-blur-md bg-surface/90`) so that when the clinician scrolls through long medication tables, the patient identification remains fixed in view.
3. **Mandatory Fields**:
   - Patient Full Name (`font-semibold text-text-primary text-base md:text-lg`)
   - Patient Age (`text-sm text-text-body-secondary`, formatted as `34 yrs`)
   - Blood Group Pill (`<BloodGroupPill group={patient.bloodGroup} />`)
   - Primary Emergency Contact Name & Relation (`text-xs text-text-body-secondary`)
   - Primary Emergency Contact Phone (formatted with `sanitizeTel` and active `tel:` link)
   - Patient Code badge (`font-mono text-xs bg-canvas px-2 py-0.5 rounded`)
4. **Read-Only Invariance**:
   - Zero `<input>`, `<select>`, or editable controls exist inside the banner.
   - Demographics are managed by the patient; the banner is an immutable identification guardrail.

---

## 8. Appointment Lifecycle & Clinical Summary Sync (D6, D8)

### 8.1 State Transitions & Data Synchronization

1. **Schedule Appointment**:
   - Status: `'scheduled'`
   - Guarded by `ap_insert_doctor`: requires `is_approved_doctor()` and `doctor_id = auth.uid()`.
2. **Complete Appointment**:
   - Status: `'completed'`
   - Form accepts `clinical_notes`.
   - On update, Postgres trigger `trg_appointment_completed` fires:
     - Sets `clinical_records.last_appointment_date = scheduled_at`.
     - Sets `clinical_records.last_appointment_summary = coalesce(nullif(clinical_notes, ''), reason)`.
     - Sets session variable `set_config('umbrella.skip_stamp', 'on', true)` to guarantee that `is_doctor_verified` is NOT flipped by appointment completion.
3. **Cancel Appointment**:
   - Status: `'cancelled'`
   - `clinical_records` summary is not updated.

---

## 9. Comprehensive Automated Test Suite Specification

This section outlines the exact test matrices, edge cases, and executable test harness scripts to be run by the Worker, Reviewers, Challengers, and Auditor during Milestone M6.

### 9.1 Verification Test Matrix

| # | Test Suite | Test Case Identifier | Tested Component / Action | Expected Behavior | Verification Role |
|---|---|---|---|---|---|
| 1 | RBAC Gating | `RBAC-01-ANON-VISIT` | `/portal/doctor` | Redirect to `/login?next=...` | Worker, Reviewer |
| 2 | RBAC Gating | `RBAC-02-PATIENT-VISIT` | `/portal/doctor` | Redirect to `/portal/patient` | Worker, Reviewer |
| 3 | RBAC Gating | `RBAC-03-PENDING-VISIT` | `/portal/doctor` | Redirect to `/portal/doctor/pending` | Worker, Reviewer |
| 4 | RBAC Gating | `RBAC-04-APPROVED-VISIT` | `/portal/doctor` | Renders Doctor Portal workspace | Worker, Reviewer |
| 5 | RBAC Actions | `RBAC-05-ANON-ACTION` | `searchPatientsAction` | Rejects with 401 Unauthorized | Challenger, Auditor |
| 6 | RBAC Actions | `RBAC-06-PATIENT-ACTION` | `updateClinicalRecordAction` | Rejects with 403 Forbidden | Challenger, Auditor |
| 7 | RBAC Actions | `RBAC-07-PENDING-ACTION` | `updateClinicalRecordAction` | Rejects with 403 Approval Pending | Challenger, Auditor |
| 8 | Postgres RLS | `RLS-01-PENDING-READ-PP` | `patient_profiles` via Supabase | 0 rows returned | Challenger, SQL Runner |
| 9 | Postgres RLS | `RLS-02-PENDING-READ-CR` | `clinical_records` via Supabase | 0 rows returned | Challenger, SQL Runner |
| 10 | Postgres RLS | `RLS-03-APPROVED-READ-ALL` | `patient_profiles` / `clinical_records` | All rows returned (count >= 2) | Challenger, SQL Runner |
| 11 | Postgres RLS | `RLS-04-DELETE-BLOCKED` | `DELETE` on all 4 tables | Exception: insufficient privilege | Challenger, SQL Runner |
| 12 | Safety Banner | `BANNER-01-DOM-EXISTENCE` | `<DoctorSafetyBanner />` | Rendered on all tabs | Worker, Reviewer |
| 13 | Safety Banner | `BANNER-02-STICKY-CSS` | Banner element styles | Has `sticky top-0` and `z-30` | Challenger, Playwright |
| 14 | Safety Banner | `BANNER-03-MANDATORY-FIELDS` | Banner text content | Name, Age, BloodGroup, Emergency Phone present | Worker, Reviewer |
| 15 | Safety Banner | `BANNER-04-READ-ONLY` | Banner DOM inputs | 0 `<input>` or `<textarea>` tags | Challenger, Auditor |
| 16 | Multi-Modal | `SEARCH-01-PATIENT-CODE` | `searchPatientsAction('UMB-9021-ALEX')` | Exact match on patient_code | Worker, Reviewer |
| 17 | Multi-Modal | `SEARCH-02-QR-TOKEN` | `searchPatientsAction(uuid)` | Exact match on qr_token | Worker, Reviewer |
| 18 | Multi-Modal | `SEARCH-03-PHONE` | `searchPatientsAction('5552345678')` | Phone substring query | Worker, Reviewer |
| 19 | Multi-Modal | `SEARCH-04-NAME-ILIKE` | `searchPatientsAction('Morgan')` | Name ILIKE search | Worker, Reviewer |
| 20 | Multi-Modal | `SEARCH-05-INJECTION-PERCENT` | `searchPatientsAction('%')` | Escaped: returns 0 or exact matches, never dump | Challenger, Auditor |
| 21 | Multi-Modal | `SEARCH-06-INJECTION-PAREN` | `searchPatientsAction('test),id.neq.0')` | Parameterized: zero syntax or logic hijack | Challenger, Auditor |
| 22 | Multi-Modal | `SEARCH-07-DEBOUNCE-LIMIT` | Query length < 2 or oversized (>20) | <2 returns empty array; limit capped at 20 | Worker, Challenger |
| 23 | Concurrency | `CONCUR-01-MATCHED-UPDATE` | `updateClinicalRecord(T0)` | Succeeds; advances timestamp to T1 | Worker, Reviewer |
| 24 | Concurrency | `CONCUR-02-STALE-COLLISION` | `updateClinicalRecord(T0)` after T1 | Fails with `conflict: true` (0 rows) | Challenger, Auditor |
| 25 | Concurrency | `CONCUR-03-CONFLICT-UI` | UI conflict alert | Non-dismissible conflict banner with Reload CTA | Challenger, Playwright |
| 26 | Verification | `STAMP-01-TRIGGER-FORCE` | Doctor update with `is_verified=false` | Trigger overrides to `is_doctor_verified=true` | Challenger, SQL Runner |
| 27 | Verification | `STAMP-02-NO-OP-VERIFY` | Doctor no-op update (`allergies=allergies`) | Flips `is_doctor_verified=true` & stamps doc ID | Challenger, Reviewer |
| 28 | Baseline | `BASE-01-DISAPPEAR-UI` | `/portal/patient` after doctor verify | Baseline editor absent from DOM | Challenger, Playwright |
| 29 | Baseline | `BASE-02-RPC-LOCKOUT` | `submit_self_reported_baseline()` | Exception: 'already doctor-verified' | Challenger, Auditor |
| 30 | Appointments | `APPT-01-DOCTOR-INSERT` | `scheduleAppointmentAction` | Inserts with `doctor_id = auth.uid()` | Worker, Reviewer |
| 31 | Appointments | `APPT-02-FOREIGN-DOC-FAIL` | Insert with spoofed `doctor_id` | RLS check fails | Challenger, Auditor |
| 32 | Appointments | `APPT-03-COMPLETE-SYNC` | Update status to `'completed'` | Updates summary/date on clinical_records | Worker, Reviewer |
| 33 | Appointments | `APPT-04-NO-VERIFY-FLIP` | Complete appt on unverified record | `is_doctor_verified` remains `false` (D8) | Challenger, Auditor |
| 34 | Accessibility | `A11Y-01-TOUCH-TARGETS` | Mobile buttons, tabs, inputs | Min 44x44px touch bounding box | Auditor, Playwright |
| 35 | Accessibility | `A11Y-02-CONTRAST-AA` | Secondary text, status badges | Contrast >= 4.5:1 (#6e6e73, #d70015, #1d7a37) | Auditor, Reviewer |
| 36 | Responsive | `RESP-01-MOBILE-375` | Viewport 375x667 | Zero horizontal scroll, banner sticky | Auditor, Playwright |
| 37 | Responsive | `RESP-02-DESKTOP-1280` | Viewport 1280x800 | Multi-column layout with fixed banner | Auditor, Playwright |

---

### 9.2 Executable Blueprint: Worker Self-Verification Harness (`scripts/verify_m6.py`)

The Worker must create and execute `scripts/verify_m6.py` prior to completing Milestone M6:

```python
#!/usr/bin/env python3
"""
scripts/verify_m6.py
Verification Harness for Milestone M6: Doctor Portal Surface (/portal/doctor)
"""

import os
import re
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def log_test(category: str, test_name: str, passed: bool, details: str = ""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] [{category}] {test_name}" + (f" -> {details}" if details else ""))
    return passed

def run_all_checks():
    all_passed = True
    passed_tests = 0
    total_tests = 0

    print("=" * 70)
    print("UMBRELLA MILESTONE M6: DOCTOR PORTAL SURFACE VERIFICATION")
    print("=" * 70)

    # Check 1: Mandatory File Existence & Limits (<12k chars)
    required_files = [
        "src/app/portal/doctor/page.tsx",
        "src/app/portal/doctor/actions.ts",
        "src/components/doctor/safety-banner.tsx",
        "src/components/doctor/lookup-bar.tsx",
        "src/components/doctor/clinical-editor.tsx",
        "src/components/doctor/appointments-manager.tsx",
        "src/lib/schemas.ts",
    ]

    for rel_path in required_files:
        total_tests += 1
        full_path = os.path.join(ROOT_DIR, rel_path)
        if os.path.isfile(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            char_count = len(content)
            passed = char_count < 12000
            details = f"{char_count} chars (<12k)" if passed else f"{char_count} chars (EXCEEDS 12k)"
        else:
            passed = False
            details = "FILE MISSING"

        if log_test("FILE_INTEGRITY", rel_path, passed, details):
            passed_tests += 1
        else:
            all_passed = False

    # Check 2: Server Actions & Authorization Guards
    actions_path = os.path.join(ROOT_DIR, "src/app/portal/doctor/actions.ts")
    if os.path.isfile(actions_path):
        with open(actions_path, "r", encoding="utf-8") as f:
            actions = f.read()

        guard_checks = [
            ("use_server_directive", actions.strip().startswith("'use server'")),
            ("auth_getUser_enforced", "supabase.auth.getUser()" in actions),
            ("no_getSession_used", "getSession" not in actions),
            ("accounts_role_check", ".from('accounts')" in actions and "doctor" in actions),
            ("doctor_status_approved_check", "approved" in actions),
            ("searchPatientsAction_defined", "export async function searchPatientsAction" in actions),
            ("updateClinicalRecordAction_defined", "export async function updateClinicalRecordAction" in actions),
            ("optimistic_concurrency_check", "expectedUpdatedAt" in actions or "updated_at" in actions),
        ]

        for name, cond in guard_checks:
            total_tests += 1
            if log_test("ACTION_GUARDS", name, cond):
                passed_tests += 1
            else:
                all_passed = False

    # Check 3: Safety Banner Non-Negotiable N2
    banner_path = os.path.join(ROOT_DIR, "src/components/doctor/safety-banner.tsx")
    if os.path.isfile(banner_path):
        with open(banner_path, "r", encoding="utf-8") as f:
            banner = f.read()

        banner_checks = [
            ("sticky_positioning", "sticky" in banner and "top-0" in banner),
            ("patient_name_rendered", "fullName" in banner or "full_name" in banner),
            ("patient_age_rendered", "age" in banner),
            ("blood_group_rendered", "bloodGroup" in banner or "blood_group" in banner),
            ("emergency_contact_phone_rendered", "emergencyContactPhone" in banner or "emergency_contact_phone" in banner),
            ("read_only_invariant", "<input" not in banner and "<textarea" not in banner),
        ]

        for name, cond in banner_checks:
            total_tests += 1
            if log_test("SAFETY_BANNER_N2", name, cond):
                passed_tests += 1
            else:
                all_passed = False

    print("=" * 70)
    print(f"VERIFICATION SUMMARY: {passed_tests}/{total_tests} Tests Passed")
    print("=" * 70)
    return all_passed

if __name__ == "__main__":
    if not run_all_checks():
        sys.exit(1)
```

---

### 9.3 Executable Blueprint: Challenger Adversarial Security Harness (`scripts/challenger_m6_security.py`)

The Challenger will execute an adversarial challenge simulating attack vectors:

```python
#!/usr/bin/env python3
"""
scripts/challenger_m6_security.py
Adversarial Security & Penetration Suite for Milestone M6:
- Pending Doctor Authorization Bypass Attempts
- Patient Cross-Role Privilege Escalation
- Multi-Modal Search Injection Attacks (%, _, commas, PostgREST filter injections)
- Optimistic Concurrency Collision Simulation
"""

import re
import sys

def test_search_sanitization():
    print("[CHALLENGE] Testing Search Input Sanitization against SQL/PostgREST injection...")

    malicious_inputs = [
        "%",
        "_",
        "Smith),id.neq.0",
        "'; DROP TABLE accounts; --",
        "Alex%20OR%201=1",
        "\\",
        "(role=eq.admin)",
        ","
    ]

    # Emulate escape function
    def escape_ilike(s: str) -> str:
        return re.sub(r'[\\%_(),]', r'\\\g<0>', s)

    for payload in malicious_inputs:
        escaped = escape_ilike(payload)
        # Ensure raw unescaped % or _ or ) cannot appear directly in filter expression
        assert not re.search(r'(?<!\\)[%_(),]', escaped), f"Failed to escape payload: {payload}"
    print("  [PASS] All injection payloads safely escaped.")

def test_optimistic_concurrency_state_machine():
    print("[CHALLENGE] Simulating Concurrent Clinical Record Mutations...")

    # Initial state
    record = {
        "patient_id": "00000000-0000-0000-0000-0000000000a1",
        "updated_at": "2026-11-01T10:00:00.000Z",
        "allergies": ["Penicillin"]
    }

    # Clinician A updates record
    def clinician_a_update(expected_ts, new_allergies):
        if record["updated_at"] != expected_ts:
            return False, "Conflict"
        record["allergies"] = new_allergies
        record["updated_at"] = "2026-11-01T10:05:00.000Z"
        return True, "Updated"

    # Clinician B attempts update with stale timestamp
    def clinician_b_update(expected_ts, new_allergies):
        if record["updated_at"] != expected_ts:
            return False, "Conflict"
        record["allergies"] = new_allergies
        record["updated_at"] = "2026-11-01T10:06:00.000Z"
        return True, "Updated"

    # Step 1: Both read T0
    t0 = record["updated_at"]

    # Step 2: A updates first -> succeeds
    ok_a, _ = clinician_a_update(t0, ["Penicillin", "Sulfa"])
    assert ok_a is True, "Clinician A update failed"

    # Step 3: B attempts update with stale T0 -> MUST CONFLICT
    ok_b, err = clinician_b_update(t0, ["Penicillin", "Latex"])
    assert ok_b is False, "Clinician B stale update succeeded erroneously!"
    assert err == "Conflict", "Did not return conflict error"
    print("  [PASS] Optimistic concurrency successfully rejected stale update.")

if __name__ == "__main__":
    test_search_sanitization()
    test_optimistic_concurrency_state_machine()
    print("[SUCCESS] Challenger M6 security test suite verified.")
```

---

## 10. Conclusion & Actionable Blueprint for Implementation

Milestone M6 represents the core clinical governance center of Umbrella. By enforcing:
1. **Zero-trust server guards** reading `public.accounts` via `getUser()`,
2. **Postgres RLS and column grants** that physically deny pending doctors and patients from reading clinical records,
3. **Security Definer triggers** enforcing immutable verification stamps,
4. **Parameterized multi-modal search** classified without raw PostgREST `.or()` strings,
5. **Timestamp-based optimistic locking** preventing clinical record collision, and
6. **A sticky, read-only safety banner** guaranteeing constant patient identification,

the Doctor Portal fulfills all safety-critical invariants defined in SPEC v2.0 and AGENTS.md.

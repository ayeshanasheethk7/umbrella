# Architectural Specification: Doctor Data Flow, Server Actions & Concurrency (Milestone M6)

**Author**: Explorer M6-2 (Doctor Data Flow & Server Actions Explorer)  
**Target Milestone**: M6 (Doctor Portal Surface)  
**Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_2_gen2`  
**Parent Agent**: Project Orchestrator (`a0698e01-4167-4648-9a8b-05be5311997c`)  
**Date**: 2026-11-01  
**Status**: APPROVED ARCHITECTURAL BLUEPRINT  

---

## 1. Executive Summary & Scope

Milestone M6 delivers the **Doctor Portal Surface** (`/portal/doctor`), the high-trust clinical interface of the Umbrella Emergency Medical ID platform. This surface enables verified physicians to look up patients across multi-modal identifiers, inspect vital demographics under a persistent safety banner (Invariant N2), edit clinical records with optimistic concurrency control, stamp official medical verifications (DECISIONS D7), and manage patient appointments (DECISIONS D6, D8).

Because this interface handles sensitive patient health information and clinical mutations, all operations must satisfy strict security, privacy, and architectural non-negotiables:
1. **Zero Mock Auth & Strict Caller Identification (N3)**: Every Server Action identifies the caller exclusively via `supabase.auth.getUser()`, never `getSession()`. Role (`'doctor'`) and status (`'approved'`) are verified directly from `public.accounts` on the server.
2. **PostgREST Operator Injection Prevention (D14 & Rule 5)**: User input is never interpolated into raw PostgREST `.or()` or `.filter()` strings. Search queries are classified into deterministic lookup branches (Patient Code, QR Token, Phone Number, Name) and executed as parameterized queries with strict escaping of SQL wildcards (`%`, `_`, `\`).
3. **Optimistic Concurrency Control (D7)**: Concurrent clinical record updates are protected via OCC using `updated_at` timestamp preconditions. Conflicting concurrent edits are trapped safely without data loss.
4. **Trigger-Driven Verification Stamping (D7)**: Database triggers (`trg_stamp_clinical`) automatically stamp `is_doctor_verified = true`, `last_updated_by_doctor_id = auth.uid()`, and `updated_at = now()` under SECURITY DEFINER privileges. Client updates are restricted to granted columns (`medical_conditions`, `current_medication`, `previous_surgeries`, `allergies`).
5. **Strict Return Typing (Code Conventions 6)**: All Server Actions return typed discriminated unions `{ ok: true, data: T } | { ok: false, error: string, fieldErrors?: Record<string, string> }`.

---

## 2. Multi-Modal Search Sanitization (DECISIONS D14 & 02-security-privacy.md Rule 5)

### 2.1 Threat Analysis: PostgREST Operator Injection
In PostgREST and the `@supabase/supabase-js` query builder, string-interpolated filter methods like `.or()` or `.filter()` parse commas `,` as logical OR operators and parentheses `()` as logical expression groupings. If user-supplied text is interpolated into an `.or()` query:
```typescript
// VULNERABLE PATTERN — DO NOT USE
supabase
  .from('accounts')
  .select('id, full_name, patient_profiles(...)')
  .or(`full_name.ilike.%${query}%,contact_phone.ilike.%${query}%`)
```
An attacker supplying `smith),id.not.is.null,role.eq.doctor` can break out of the intended query filter, alter query logic, manipulate PostgREST filters, or cause denial-of-service syntax crashes.

Furthermore, PostgreSQL `LIKE` and `ILIKE` operators treat `%` (any sequence of characters) and `_` (any single character) as wildcards, and `\` as the escape character. An unescaped search for `%` matches all rows in the table, bypassing search selectivity and leaking unsegmented patient lists.

### 2.2 Input Classifier State Machine (DECISIONS D14)
Per DECISIONS D14, Umbrella solves this vulnerability by **classifying input first** and executing dedicated, parameterized queries rather than interpolating raw text into compound `.or()` strings.

```text
                                [ User Search Input ]
                                          |
                                    Trim & Validate
                                   (length >= 2 chars)
                                          |
                 +------------------------+------------------------+
                 |                        |                        |
       Matches UMB-XXXXXX?           Matches UUID?            Digits >= 7?
                 |                        |                        |
                YES                      YES                      YES
                 |                        |                        |
           [Branch 1]               [Branch 2]               [Branch 3]
          Patient Code                QR Token               Phone Number
         Exact Equality            Exact Equality             Substring
         .eq(patient_code)         .eq(qr_token)          .ilike(digits_only)
                 |                        |                        |
                 +------------------------+------------------------+
                                          | NO to all
                                          v
                                     [Branch 4]
                                     Name Lookup
                                   ILIKE Parameter
                              (Escaped %, _, \ wildcards)
```

### 2.3 Sanitization & Escaping Utilities
The following escaping functions must be placed in `src/lib/utils.ts` or `src/lib/validation/doctor.ts`:

```typescript
/**
 * Escapes PostgreSQL LIKE/ILIKE wildcards (%, _, and backslash \).
 * Complies with 02-security-privacy.md Rule 5.
 */
export function escapePostgresLike(term: string): string {
  if (!term) return '';
  return term
    .replace(/\\/g, '\\\\')  // Escape backslash first
    .replace(/%/g, '\\%')    // Escape wildcard %
    .replace(/_/g, '\\_');   // Escape single-char wildcard _
}

/**
 * Escapes PostgREST reserved delimiter characters (commas and parentheses)
 * if input ever interacts with PostgREST query parameters.
 */
export function sanitizeSearchTerm(term: string): string {
  if (!term) return '';
  const escaped = escapePostgresLike(term.trim());
  return escaped.replace(/[,()]/g, '');
}

export type SearchClassification =
  | { type: 'PATIENT_CODE'; code: string }
  | { type: 'QR_TOKEN'; token: string }
  | { type: 'PHONE'; digits: string }
  | { type: 'NAME'; term: string };

/**
 * Classifies search input per DECISIONS D14
 */
export function classifySearchInput(rawInput: string): SearchClassification {
  const trimmed = rawInput.trim();

  // 1. Patient Code: matches UMB-XXXXXX (case-insensitive)
  if (/^UMB-[A-Z0-9]{6}$/i.test(trimmed)) {
    return { type: 'PATIENT_CODE', code: trimmed.toUpperCase() };
  }

  // 2. UUID: matches exact qr_token (case-insensitive)
  if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(trimmed)) {
    return { type: 'QR_TOKEN', token: trimmed.toLowerCase() };
  }

  // 3. Mostly digits (7+): phone contains
  const digitsOnly = trimmed.replace(/\D/g, '');
  if (digitsOnly.length >= 7) {
    return { type: 'PHONE', digits: digitsOnly };
  }

  // 4. Otherwise: name ilike
  return { type: 'NAME', term: sanitizeSearchTerm(trimmed) };
}
```

### 2.4 Parameterized Query Execution Blueprint
In `src/app/portal/doctor/actions.ts`, `searchPatientsAction` executes the classified query without any string interpolation:

```typescript
export interface PatientSearchResult {
  patientId: string;
  patientCode: string;
  qrToken: string;
  fullName: string;
  age: number;
  bloodGroup: string;
  contactPhone: string;
  emergencyContactName: string;
  emergencyContactPhone: string;
}

export async function searchPatientsAction(
  query: string
): Promise<ActionResponse<PatientSearchResult[]>> {
  try {
    const supabase = createClient();

    // 1. Authenticate caller strictly via getUser() & verify approved doctor
    const authResult = await verifyApprovedDoctor(supabase);
    if (!authResult.ok) {
      return authResult;
    }

    // 2. Validate input length per D14 (min 2 characters, max 100)
    const trimmed = (query || '').trim();
    if (trimmed.length < 2) {
      return { ok: true, data: [] };
    }
    if (trimmed.length > 100) {
      return { ok: false, error: 'Search query cannot exceed 100 characters.' };
    }

    // 3. Classify input
    const classification = classifySearchInput(trimmed);
    let results: PatientSearchResult[] = [];

    switch (classification.type) {
      case 'PATIENT_CODE': {
        const { data, error } = await supabase
          .from('patient_profiles')
          .select(`
            patient_id,
            patient_code,
            qr_token,
            age,
            blood_group,
            emergency_contact_name,
            emergency_contact_phone,
            accounts!inner (
              id,
              full_name,
              contact_phone
            )
          `)
          .eq('patient_code', classification.code)
          .limit(20);

        if (error) throw error;
        results = (data || []).map(mapProfileToSearchResult);
        break;
      }

      case 'QR_TOKEN': {
        const { data, error } = await supabase
          .from('patient_profiles')
          .select(`
            patient_id,
            patient_code,
            qr_token,
            age,
            blood_group,
            emergency_contact_name,
            emergency_contact_phone,
            accounts!inner (
              id,
              full_name,
              contact_phone
            )
          `)
          .eq('qr_token', classification.token)
          .limit(20);

        if (error) throw error;
        results = (data || []).map(mapProfileToSearchResult);
        break;
      }

      case 'PHONE': {
        // Run parameterized queries on accounts.contact_phone and patient_profiles.emergency_contact_phone
        const [accRes, emerRes] = await Promise.all([
          supabase
            .from('patient_profiles')
            .select(`
              patient_id,
              patient_code,
              qr_token,
              age,
              blood_group,
              emergency_contact_name,
              emergency_contact_phone,
              accounts!inner (
                id,
                full_name,
                contact_phone
              )
            `)
            .ilike('accounts.contact_phone', `%${classification.digits}%`)
            .limit(20),
          supabase
            .from('patient_profiles')
            .select(`
              patient_id,
              patient_code,
              qr_token,
              age,
              blood_group,
              emergency_contact_name,
              emergency_contact_phone,
              accounts!inner (
                id,
                full_name,
                contact_phone
              )
            `)
            .ilike('emergency_contact_phone', `%${classification.digits}%`)
            .limit(20),
        ]);

        if (accRes.error) throw accRes.error;
        if (emerRes.error) throw emerRes.error;

        // Deduplicate merged results by patient_id
        const map = new Map<string, PatientSearchResult>();
        (accRes.data || []).forEach((row) => {
          const item = mapProfileToSearchResult(row);
          map.set(item.patientId, item);
        });
        (emerRes.data || []).forEach((row) => {
          const item = mapProfileToSearchResult(row);
          map.set(item.patientId, item);
        });

        results = Array.from(map.values()).slice(0, 20);
        break;
      }

      case 'NAME': {
        // Query accounts by full_name, joining patient_profiles
        const { data, error } = await supabase
          .from('patient_profiles')
          .select(`
            patient_id,
            patient_code,
            qr_token,
            age,
            blood_group,
            emergency_contact_name,
            emergency_contact_phone,
            accounts!inner (
              id,
              full_name,
              contact_phone
            )
          `)
          .ilike('accounts.full_name', `%${classification.term}%`)
          .limit(20);

        if (error) throw error;
        results = (data || []).map(mapProfileToSearchResult);
        break;
      }
    }

    return { ok: true, data: results };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Patient search failed.';
    return { ok: false, error: message };
  }
}
```

---

## 3. Clinical Records Mutation & Optimistic Concurrency Control (DECISIONS D7)

### 3.1 The Clinical Concurrency Race Condition
In a multi-provider emergency department or clinic, Doctor A and Doctor B may simultaneously open Patient X's record:
1. Doctor A and Doctor B load the record at 10:00:00 UTC (`updated_at` = `T0`).
2. Doctor A reviews allergies, adds "Penicillin", and submits at 10:02:00 UTC. The record updates to `T1`.
3. Doctor B finishes updating medications and submits at 10:03:00 UTC.
4. **Without Concurrency Control**: Doctor B's write blindly overwrites Doctor A's allergy update with the stale snapshot from 10:00:00 UTC. Patient X's critical allergy record is erased without warning.

### 3.2 Optimistic Concurrency Control (OCC) Architecture
Umbrella implements strict Optimistic Concurrency Control via `updated_at` preconditions:
- Every clinical record load retrieves the row's `updated_at` ISO timestamp.
- The client mutation payload must provide `expectedUpdatedAt`.
- The database update query includes `.eq('updated_at', expectedUpdatedAt)`.
- If another update succeeded in the interim, `updated_at` no longer equals `expectedUpdatedAt`, resulting in zero rows updated.
- The Server Action detects `rowsAffected === 0`, checks if the record was modified by another user, and returns a high-priority concurrency conflict error, preventing data corruption.

```text
[ Client Submits Mutation ]
   (patientId, clinicalData, expectedUpdatedAt)
                 |
                 v
[ Server Action: updateClinicalRecordAction ]
                 |
        Validate Zod Schema
                 |
        Verify Approved Doctor
                 |
        Execute PostgREST Update:
        .from('clinical_records')
        .update(grantedColumns)
        .eq('patient_id', patientId)
        .eq('updated_at', expectedUpdatedAt)
        .select()
                 |
         +-------+-------+
         |               |
   Rows Updated = 1   Rows Updated = 0
         |               |
         v               v
   [Trigger Fires]    [OCC Conflict Detected]
   stamps verified_by, Query existing updated_at:
   verified_at,        if changed -> Return Conflict Error
   updated_at          "Conflict: Record modified by another provider.
         |              Please refresh."
         v
   Return { ok: true, data: updatedRecord }
```

### 3.3 Database Trigger Mechanics & Column Grants (D3, D7)
Our analysis of `supabase/migrations/0001_umbrella_schema.sql` revealed a critical architectural boundary:
1. **Column Grants**: Authenticated users have UPDATE privileges ONLY on:
   ```sql
   grant update (medical_conditions, current_medication, previous_surgeries, allergies)
     on public.clinical_records to authenticated;
   ```
2. **Trigger-Enforced Stamping**:
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

**Architectural Invariant**:
The Server Action **MUST NOT** include `is_doctor_verified`, `last_updated_by_doctor_id`, or `updated_at` in the `.update()` payload. If the server action attempts to send these fields, Postgres rejects the query with a column permission violation error (`42501`). The database trigger `trg_stamp_clinical` operates under `SECURITY DEFINER` and automatically stamps `is_doctor_verified = true`, `last_updated_by_doctor_id = auth.uid()`, and `updated_at = now()`.

Furthermore, per DECISIONS D7: *"A doctor can verify unchanged self-reported data by saving it."* Saving the form without modifications still executes an update on `clinical_records`, which triggers `trg_stamp_clinical` and verifies the record.

### 3.4 Server Action: `updateClinicalRecordAction` Implementation Blueprint
```typescript
export interface UpdateClinicalRecordInput {
  patientId: string;
  expectedUpdatedAt: string; // ISO 8601 string from initial record read
  medicalConditions: string[];
  currentMedication: MedicationItem[];
  previousSurgeries: SurgeryItem[];
  allergies: string[];
}

export async function updateClinicalRecordAction(
  rawData: unknown
): Promise<ActionResponse<ClinicalRecordRow>> {
  try {
    const supabase = createClient();

    // 1. Authenticate caller strictly via getUser() & verify approved doctor
    const authResult = await verifyApprovedDoctor(supabase);
    if (!authResult.ok) {
      return authResult;
    }

    // 2. Validate input against Zod schema
    const parseResult = updateClinicalRecordSchema.safeParse(rawData);
    if (!parseResult.success) {
      const fieldErrors: Record<string, string> = {};
      parseResult.error.errors.forEach((err) => {
        const key = err.path.join('.');
        fieldErrors[key] = err.message;
      });
      return {
        ok: false,
        error: parseResult.error.errors[0]?.message || 'Invalid clinical record data.',
        fieldErrors,
      };
    }

    const {
      patientId,
      expectedUpdatedAt,
      medicalConditions,
      currentMedication,
      previousSurgeries,
      allergies,
    } = parseResult.data;

    // 3. Execute OCC Update
    // Pass ONLY granted columns. Trigger stamps is_doctor_verified & last_updated_by_doctor_id!
    const { data, error } = await supabase
      .from('clinical_records')
      .update({
        medical_conditions: medicalConditions,
        current_medication: currentMedication as unknown as Json,
        previous_surgeries: previousSurgeries as unknown as Json,
        allergies: allergies,
      })
      .eq('patient_id', patientId)
      .eq('updated_at', expectedUpdatedAt)
      .select('*')
      .maybeSingle();

    if (error) {
      return {
        ok: false,
        error: `Database update failed: ${error.message}`,
      };
    }

    // 4. Handle OCC Concurrency Conflict
    if (!data) {
      const { data: existing } = await supabase
        .from('clinical_records')
        .select('updated_at, is_doctor_verified, last_updated_by_doctor_id')
        .eq('patient_id', patientId)
        .maybeSingle();

      if (existing && existing.updated_at !== expectedUpdatedAt) {
        return {
          ok: false,
          error:
            'Concurrency Conflict: This clinical record was updated by another healthcare provider while you were editing. Please refresh the page to inspect the latest changes before re-submitting.',
        };
      }

      return {
        ok: false,
        error: 'Record not found or unable to apply update.',
      };
    }

    // 5. Invalidate Next.js cache for doctor and patient portals
    revalidatePath('/portal/doctor');
    revalidatePath('/portal/patient');

    return {
      ok: true,
      data: data as ClinicalRecordRow,
    };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'An unexpected error occurred.';
    return { ok: false, error: message };
  }
}
```

---

## 4. Appointment Scheduling & Management Flow (DECISIONS D6, D8)

### 4.1 Appointment Schema & Relations
Table `public.appointments` tracks consultations between approved physicians and patients:
- `id` (uuid, PK)
- `patient_id` (uuid, FK `accounts.id` on delete cascade)
- `doctor_id` (uuid, FK `accounts.id` on delete restrict per DECISIONS D6)
- `scheduled_at` (timestamptz)
- `status` (text check `status in ('scheduled', 'completed', 'cancelled')`)
- `reason` (text, not null)
- `clinical_notes` (text, nullable)
- `created_at`, `updated_at` (timestamptz)

### 4.2 Completion Trigger Mechanics (DECISIONS D8)
When an appointment's status transitions to `'completed'`, the database trigger `trg_appointment_completed` executes `public.on_appointment_completed()`:
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
**Key Spec Invariant (D8)**: Setting `umbrella.skip_stamp = 'on'` prevents `stamp_clinical_update` from flipping `is_doctor_verified`. Thus, completing an appointment updates `last_appointment_date` and `last_appointment_summary` without accidentally marking an unverified clinical record as verified.

### 4.3 Appointment Server Actions

#### Action 1: `getDoctorAppointmentsAction`
Fetches upcoming and past appointments for the authenticated doctor, joined with patient profile demographics:
```typescript
export interface DoctorAppointmentItem {
  id: string;
  patientId: string;
  scheduledAt: string;
  status: 'scheduled' | 'completed' | 'cancelled';
  reason: string;
  clinicalNotes: string | null;
  createdAt: string;
  patient: {
    fullName: string;
    contactPhone: string;
    patientCode: string;
    age: number;
    bloodGroup: string;
  };
}

export async function getDoctorAppointmentsAction(options?: {
  status?: 'scheduled' | 'completed' | 'cancelled';
  patientId?: string;
}): Promise<ActionResponse<DoctorAppointmentItem[]>> {
  try {
    const supabase = createClient();
    const authResult = await verifyApprovedDoctor(supabase);
    if (!authResult.ok) return authResult;

    let query = supabase
      .from('appointments')
      .select(`
        id,
        patient_id,
        scheduled_at,
        status,
        reason,
        clinical_notes,
        created_at,
        accounts!appointments_patient_id_fkey (
          full_name,
          contact_phone,
          patient_profiles (
            patient_code,
            age,
            blood_group
          )
        )
      `)
      .eq('doctor_id', authResult.user.id);

    if (options?.status) {
      query = query.eq('status', options.status);
    }
    if (options?.patientId) {
      query = query.eq('patient_id', options.patientId);
    }

    const { data, error } = await query.order('scheduled_at', { ascending: true });
    if (error) throw error;

    const formatted: DoctorAppointmentItem[] = (data || []).map((row: any) => ({
      id: row.id,
      patientId: row.patient_id,
      scheduledAt: row.scheduled_at,
      status: row.status,
      reason: row.reason,
      clinicalNotes: row.clinical_notes,
      createdAt: row.created_at,
      patient: {
        fullName: row.accounts?.full_name || 'Unknown Patient',
        contactPhone: row.accounts?.contact_phone || '',
        patientCode: row.accounts?.patient_profiles?.patient_code || 'N/A',
        age: row.accounts?.patient_profiles?.age || 0,
        bloodGroup: row.accounts?.patient_profiles?.blood_group || 'Unknown',
      },
    }));

    return { ok: true, data: formatted };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Failed to fetch appointments.';
    return { ok: false, error: message };
  }
}
```

#### Action 2: `createAppointmentAction`
```typescript
export async function createAppointmentAction(
  rawData: unknown
): Promise<ActionResponse<AppointmentRow>> {
  try {
    const supabase = createClient();
    const authResult = await verifyApprovedDoctor(supabase);
    if (!authResult.ok) return authResult;

    const parseResult = createAppointmentSchema.safeParse(rawData);
    if (!parseResult.success) {
      return {
        ok: false,
        error: parseResult.error.errors[0]?.message || 'Invalid appointment input.',
      };
    }

    const { patientId, scheduledAt, reason, clinicalNotes } = parseResult.data;

    // Verify target patient exists and has role 'patient'
    const { data: patientAcc, error: patientErr } = await supabase
      .from('accounts')
      .select('id, role')
      .eq('id', patientId)
      .eq('role', 'patient')
      .maybeSingle();

    if (patientErr || !patientAcc) {
      return { ok: false, error: 'Target patient record not found.' };
    }

    // Insert appointment
    const { data, error } = await supabase
      .from('appointments')
      .insert({
        doctor_id: authResult.user.id,
        patient_id: patientId,
        scheduled_at: scheduledAt,
        reason: reason,
        clinical_notes: clinicalNotes || null,
        status: 'scheduled',
      })
      .select('*')
      .single();

    if (error) {
      return { ok: false, error: `Failed to schedule appointment: ${error.message}` };
    }

    revalidatePath('/portal/doctor');
    return { ok: true, data: data as AppointmentRow };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Scheduling error occurred.';
    return { ok: false, error: message };
  }
}
```

#### Action 3: `updateAppointmentStatusAction`
```typescript
export async function updateAppointmentStatusAction(
  rawData: unknown
): Promise<ActionResponse<AppointmentRow>> {
  try {
    const supabase = createClient();
    const authResult = await verifyApprovedDoctor(supabase);
    if (!authResult.ok) return authResult;

    const parseResult = updateAppointmentStatusSchema.safeParse(rawData);
    if (!parseResult.success) {
      return {
        ok: false,
        error: parseResult.error.errors[0]?.message || 'Invalid appointment status update.',
      };
    }

    const { appointmentId, status, clinicalNotes } = parseResult.data;

    // Build update payload
    const updatePayload: { status: 'scheduled' | 'completed' | 'cancelled'; clinical_notes?: string } = {
      status,
    };
    if (clinicalNotes !== undefined) {
      updatePayload.clinical_notes = clinicalNotes;
    }

    // Execute update (trigger trg_appointment_completed fires if status === 'completed')
    const { data, error } = await supabase
      .from('appointments')
      .update(updatePayload)
      .eq('id', appointmentId)
      .select('*')
      .single();

    if (error) {
      return { ok: false, error: `Failed to update appointment: ${error.message}` };
    }

    revalidatePath('/portal/doctor');
    return { ok: true, data: data as AppointmentRow };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Appointment update error occurred.';
    return { ok: false, error: message };
  }
}
```

---

## 5. Authentication, RBAC, and Caller Identification (NON-NEGOTIABLE N3)

### 5.1 Invariant N3 Compliance
AGENTS.md Non-Negotiable N3 specifies:
> *"Security lives in Postgres (RLS, grants, SECURITY DEFINER functions) and server code. Hiding a button is not security. Never trust a role sent by the client. Never authorise from user_metadata. In server code identify the caller with supabase.auth.getUser(), never getSession()."*

In Next.js App Router with Supabase `@supabase/ssr`:
- `getSession()` merely reads the unverified JWT from local cookie storage without cryptographic server-side validation. A revoked session or modified cookie could be processed improperly.
- `supabase.auth.getUser()` makes a validated roundtrip to the Supabase Auth server, authenticating the token against active revocation lists and returning the verified user object.

### 5.2 Helper: `verifyApprovedDoctor`
All doctor Server Actions share a standardized authentication and authorization pipeline:

```typescript
export interface VerifiedDoctorContext {
  user: {
    id: string;
    email?: string;
  };
  account: AccountRow;
}

export async function verifyApprovedDoctor(
  supabase: ReturnType<typeof createClient>
): Promise<ActionSuccess<VerifiedDoctorContext> | ActionFailure> {
  // 1. Authenticate caller strictly via getUser() per Invariant N3
  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (!user || authError) {
    return {
      ok: false,
      error: 'Unauthorized. Your session has expired; please sign in again.',
    };
  }

  // 2. Fetch role & doctor_status directly from public.accounts (never user_metadata)
  const { data: account, error: accountError } = await supabase
    .from('accounts')
    .select('id, email, role, doctor_status, full_name, medical_license_number, specialization, contact_phone, created_at, updated_at')
    .eq('id', user.id)
    .single();

  if (accountError || !account) {
    return {
      ok: false,
      error: 'Identity profile not found. Please log in again.',
    };
  }

  // 3. Role enforcement
  if (account.role !== 'doctor') {
    return {
      ok: false,
      error: 'Forbidden. Healthcare provider access required.',
    };
  }

  // 4. Verification gate per DECISIONS D1
  if (account.doctor_status !== 'approved') {
    return {
      ok: false,
      error:
        account.doctor_status === 'pending'
          ? 'Physician account verification is pending administrative credential review. Clinical record mutations and patient lookups remain locked.'
          : 'Account access has been declined. Please contact clinical administration.',
    };
  }

  return {
    ok: true,
    data: {
      user: { id: user.id, email: user.email },
      account: account as AccountRow,
    },
  };
}
```

---

## 6. Complete Zod Schemas & Validation Architecture

To ensure end-to-end type safety per Invariant N10 and prevent payload inflation DOS, all inputs are validated through Zod schemas. These schemas should be added to `src/lib/schemas.ts` or `src/lib/validation/doctor.ts`.

```typescript
import { z } from 'zod';
import {
  phoneRegex,
  medicationItemSchema,
  surgeryItemSchema,
  bloodGroupEnum,
} from '@/lib/schemas';

/**
 * 1. Patient Search Query Schema (DECISIONS D14)
 */
export const patientSearchSchema = z.object({
  query: z
    .string()
    .trim()
    .min(2, 'Search query must be at least 2 characters')
    .max(100, 'Search query cannot exceed 100 characters'),
});

export type PatientSearchInput = z.infer<typeof patientSearchSchema>;

/**
 * 2. Clinical Record OCC Mutation Schema (DECISIONS D7)
 * Imposes bounded arrays (<= 50) to prevent payload inflation DOS attacks.
 */
export const updateClinicalRecordSchema = z.object({
  patientId: z.string().uuid('Invalid patient UUID format'),
  expectedUpdatedAt: z
    .string()
    .datetime({ message: 'Concurrency timestamp must be a valid ISO 8601 string' }),
  medicalConditions: z
    .array(
      z
        .string()
        .trim()
        .min(1, 'Medical condition cannot be empty')
        .max(100, 'Medical condition item cannot exceed 100 characters')
    )
    .max(50, 'A maximum of 50 medical conditions are permitted')
    .default([]),
  currentMedication: z
    .array(medicationItemSchema)
    .max(50, 'A maximum of 50 medications are permitted')
    .default([]),
  previousSurgeries: z
    .array(surgeryItemSchema)
    .max(50, 'A maximum of 50 surgical procedures are permitted')
    .default([]),
  allergies: z
    .array(
      z
        .string()
        .trim()
        .min(1, 'Allergy item cannot be empty')
        .max(100, 'Allergy item cannot exceed 100 characters')
    )
    .max(50, 'A maximum of 50 allergies are permitted')
    .default([]),
});

export type UpdateClinicalRecordInput = z.infer<typeof updateClinicalRecordSchema>;

/**
 * 3. Create Appointment Schema (DECISIONS D6, D17)
 */
export const appointmentStatusEnum = z.enum(['scheduled', 'completed', 'cancelled']);

export const createAppointmentSchema = z.object({
  patientId: z.string().uuid('Invalid patient identifier'),
  scheduledAt: z
    .string()
    .datetime({ message: 'Appointment time must be a valid ISO 8601 datetime' }),
  reason: z
    .string()
    .trim()
    .min(2, 'Appointment reason must be at least 2 characters')
    .max(255, 'Reason cannot exceed 255 characters'),
  clinicalNotes: z
    .string()
    .trim()
    .max(1000, 'Clinical notes cannot exceed 1000 characters')
    .optional()
    .or(z.literal('')),
});

export type CreateAppointmentInput = z.infer<typeof createAppointmentSchema>;

/**
 * 4. Update Appointment Status Schema (DECISIONS D8)
 */
export const updateAppointmentStatusSchema = z.object({
  appointmentId: z.string().uuid('Invalid appointment identifier'),
  status: appointmentStatusEnum,
  clinicalNotes: z
    .string()
    .trim()
    .max(1000, 'Clinical notes cannot exceed 1000 characters')
    .optional()
    .or(z.literal('')),
});

export type UpdateAppointmentStatusInput = z.infer<typeof updateAppointmentStatusSchema>;
```

---

## 7. UI Integration & Component Architecture (DECISIONS D14, D15 & Invariant N2)

### 7.1 Persistent Sticky Safety Banner (Invariant N2)
Non-Negotiable N2 requires that the Doctor Portal **always** displays a read-only safety banner containing:
- Patient Full Name
- Age
- Blood Group
- Emergency Contact Name & Phone (with formatted `tel:` link via `sanitizeTel`)

```tsx
// src/components/doctor/safety-banner.tsx
'use client';

import React from 'react';
import { ShieldCheck, AlertTriangle, Phone, UserCheck, Calendar } from 'lucide-react';
import { BloodGroupPill } from '@/components/ui/blood-group-pill';
import { Badge } from '@/components/ui/badge';
import { sanitizeTel, formatPhone } from '@/lib/utils';
import type { BloodGroup } from '@/lib/supabase/types';

export interface SafetyBannerProps {
  fullName: string;
  patientCode: string;
  age: number;
  bloodGroup: BloodGroup;
  emergencyContactName: string;
  emergencyContactPhone: string;
  emergencyContactRelation: string;
  isDoctorVerified: boolean;
  lastAppointmentDate: string | null;
}

export function SafetyBanner({
  fullName,
  patientCode,
  age,
  bloodGroup,
  emergencyContactName,
  emergencyContactPhone,
  emergencyContactRelation,
  isDoctorVerified,
  lastAppointmentDate,
}: SafetyBannerProps) {
  const telLink = sanitizeTel(emergencyContactPhone);

  return (
    <aside
      aria-label="Patient Safety Information"
      className="sticky top-16 z-30 w-full rounded-2xl border border-black/10 bg-surface/95 backdrop-blur-md shadow-ceiling p-4 mb-6 transition-all"
    >
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Left: Patient Demographics */}
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-action/10 text-accent-action font-semibold text-lg">
            {fullName.charAt(0).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-text-primary tracking-tight">{fullName}</h2>
              <span className="font-mono text-xs text-text-secondary bg-canvas px-2 py-0.5 rounded-md border border-black/5">
                {patientCode}
              </span>
              <BloodGroupPill bloodGroup={bloodGroup} size="sm" />
            </div>
            <p className="text-xs text-text-body-secondary mt-0.5">
              Age: <span className="font-semibold text-text-primary">{age} yrs</span>
            </p>
          </div>
        </div>

        {/* Center: Verification & Appointment Stamp */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {isDoctorVerified ? (
            <Badge variant="verified" className="flex items-center gap-1">
              <UserCheck className="h-3.5 w-3.5" aria-hidden="true" />
              Doctor-Verified Record
            </Badge>
          ) : (
            <Badge variant="pending" className="flex items-center gap-1">
              <AlertTriangle className="h-3.5 w-3.5 text-clinical-pending-text" aria-hidden="true" />
              Self-Reported Baseline — Unverified
            </Badge>
          )}

          {lastAppointmentDate && (
            <span className="inline-flex items-center gap-1 text-text-body-secondary bg-canvas px-2.5 py-1 rounded-full border border-black/5">
              <Calendar className="h-3 w-3" aria-hidden="true" />
              Last Consult: {new Date(lastAppointmentDate).toLocaleDateString()}
            </span>
          )}
        </div>

        {/* Right: Emergency Contact Call Target */}
        <div className="flex items-center gap-2 border-t md:border-t-0 pt-2 md:pt-0 border-black/5">
          <div className="text-right hidden sm:block">
            <p className="text-[11px] uppercase tracking-wider text-text-secondary font-medium">
              Emergency Contact ({emergencyContactRelation || 'Primary'})
            </p>
            <p className="text-xs font-semibold text-text-primary">{emergencyContactName || 'None Listed'}</p>
          </div>
          {emergencyContactPhone && (
            <a
              href={`tel:${telLink}`}
              className="inline-flex h-10 items-center justify-center gap-1.5 rounded-xl bg-clinical-critical/10 text-clinical-critical-text px-3 text-xs font-semibold hover:bg-clinical-critical/20 focus-visible:outline-2 focus-visible:outline-clinical-critical transition-colors"
            >
              <Phone className="h-3.5 w-3.5" aria-hidden="true" />
              <span>{formatPhone(emergencyContactPhone)}</span>
            </a>
          )}
        </div>
      </div>
    </aside>
  );
}
```

### 7.2 Patient Escalation Link Handling (DECISIONS D15)
Per DECISIONS D15:
> *"Footer goes to /portal/doctor?patient_token=<uuid>. If logged out: redirect to /login?next=<encoded path+query>; after login an approved doctor lands with the patient pre-loaded. A logged-in non-doctor sees a "Doctor account required" screen, never a 500. Accept next only if it is a relative path starting with a single "/""*

In `/portal/doctor/page.tsx`:
- Accepts `searchParams: { patient_token?: string }`.
- If `patient_token` is present:
  - Queries `patient_profiles` where `qr_token = patient_token` (or `patient_id = patient_token`).
  - Fetches associated `accounts` and `clinical_records`.
  - Automatically loads the patient directly into the persistent safety banner and clinical editor without requiring manual search lookup.

---

## 8. File Structure & Delivery Blueprint for Implementation Team

The following files will be created or updated during Milestone M6 implementation:

```text
src/
├── app/
│   └── portal/
│       └── doctor/
│           ├── actions.ts              # All doctor server actions specified in Section 2, 3, 4, 5
│           └── page.tsx                # Server Component layout, searchParams patient_token handling
├── components/
│   └── doctor/
│       ├── lookup-bar.tsx              # Debounced multi-modal search component
│       ├── safety-banner.tsx           # Sticky read-only patient safety banner (N2)
│       ├── clinical-editor.tsx         # OCC clinical records mutation form with dirty tracking
│       └── appointments-manager.tsx    # Appointment list, status switcher, scheduling modal
└── lib/
    ├── schemas.ts                      # Appended with doctor schemas from Section 6
    └── utils.ts                        # Added escapePostgresLike, classifySearchInput
```

---

## 9. Verification & Architectural Checkpoints

Before Milestone M6 is declared complete, the following automated and manual checks must pass:
1. **TypeScript Typecheck**: `npm run typecheck` (`tsc --noEmit`) passes with zero errors and no `@ts-ignore`.
2. **ESLint**: `npm run lint` passes with zero warnings.
3. **OCC Conflict Test**: Two simultaneous mutations with identical `expectedUpdatedAt` must allow the first to succeed and reject the second with the concurrency conflict message.
4. **Trigger Stamp Check**: Updates to `clinical_records` must automatically set `is_doctor_verified = true`, `last_updated_by_doctor_id = auth.uid()`, and `updated_at = now()`.
5. **PostgREST Injection Smoke Test**: Passing search terms containing commas, parentheses, quotes, `%`, and `_` must return safe empty or filtered results without crashing or altering query logic.
6. **Appointment Status Transition**: Updating status to `'completed'` must populate `last_appointment_date` and `last_appointment_summary` in `clinical_records` without flipping `is_doctor_verified` (per D8).

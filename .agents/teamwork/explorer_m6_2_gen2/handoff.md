# Handoff Report: Doctor Data Flow & Server Actions Exploration (Milestone M6)

**Agent**: Explorer M6-2 (Doctor Data Flow & Server Actions Explorer)  
**Recipient**: Project Orchestrator (`a0698e01-4167-4648-9a8b-05be5311997c`)  
**Date**: 2026-11-01  
**Handoff Type**: Hard (Task Complete)  
**Report Artifact**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_2_gen2\report.md`  

---

## 1. Observation

1. **Database Schema & Constraints (`supabase/migrations/0001_umbrella_schema.sql`)**:
   - Lines 52-64 define `public.clinical_records`:
     `patient_id uuid primary key references public.accounts(id) on delete cascade`
     `medical_conditions text[] not null default '{}'`
     `current_medication jsonb not null default '[]'::jsonb`
     `previous_surgeries jsonb not null default '[]'::jsonb`
     `allergies text[] not null default '{}'`
     `is_doctor_verified boolean not null default false`
     `last_updated_by_doctor_id uuid references public.accounts(id)`
     `last_appointment_date timestamptz`
     `last_appointment_summary text`
     `created_at timestamptz not null default now()`
     `updated_at timestamptz not null default now()`
   - Lines 68-78 define `public.appointments`:
     `id uuid primary key default gen_random_uuid()`
     `patient_id uuid not null references public.accounts(id) on delete cascade`
     `doctor_id uuid not null references public.accounts(id) on delete restrict`
     `scheduled_at timestamptz not null`
     `status text not null default 'scheduled' check (status in ('scheduled', 'completed', 'cancelled'))`
     `reason text not null`
     `clinical_notes text`
   - Lines 198-213 define the verification stamp trigger `stamp_clinical_update()`:
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
   - Lines 216-234 define `on_appointment_completed()`:
     When `status = 'completed'`, sets `umbrella.skip_stamp = 'on'`, updates `last_appointment_date = new.scheduled_at` and `last_appointment_summary = coalesce(nullif(new.clinical_notes, ''), new.reason)`, and resets `umbrella.skip_stamp = 'off'`. This updates appointment dates without changing `is_doctor_verified` (conforming to DECISIONS D8).
   - Lines 313-315 define column-level update grants:
     ```sql
     grant update (medical_conditions, current_medication, previous_surgeries, allergies)
       on public.clinical_records to authenticated;
     ```
     `is_doctor_verified`, `last_updated_by_doctor_id`, and `updated_at` are **not** granted for update to authenticated users.

2. **Decisions & Policy Specifications (`docs/DECISIONS.md`)**:
   - D1: *"Doctor signup creates accounts.doctor_status='pending'. All doctor privileges (RLS, proxy, UI) require doctor_status='approved' via public.is_approved_doctor(). Pending doctors see a 'Verification pending' screen."*
   - D6: *"appointments.doctor_id is not null AND on delete restrict."*
   - D7: *"The clinical_records row is auto-created by a trigger when the patient profile is created. Verification stamps (is_doctor_verified, last_updated_by_doctor_id, updated_at) are set by a BEFORE UPDATE trigger, never by client values. A doctor can verify unchanged self-reported data by saving it."*
   - D8: *"Completing an appointment fills last_appointment_date and last_appointment_summary through a trigger and does NOT flip is_doctor_verified."*
   - D14: *"Doctor lookup. Classify the input: matches UMB-XXXXXX (case-insensitive): exact patient_code. UUID: exact qr_token. Mostly digits (7+): phone contains. Otherwise: name ilike. Run separate parameterised queries; never build an .or() string from raw input. Minimum 2 characters, 300ms debounce, max 20 results showing name, code, age, blood group."*
   - D15: *"Footer goes to /portal/doctor?patient_token=<uuid>. If logged out: redirect to /login?next=<encoded path+query>; after login an approved doctor lands with the patient pre-loaded."*

3. **Security Rules (`.agents/rules/02-security-privacy.md`)**:
   - Rule 2: *"role and doctor_status are read from public.accounts on the server. Never from JWT user_metadata, localStorage, query strings or form fields."*
   - Rule 5: *"zod validation on the client and again in every server action. Never interpolate user text into PostgREST .or()/.filter() strings or SQL. Escape %, _, ,, (, ) in search terms."*
   - Rule 6: *"For tel: links strip the number to digits and one leading +."*

4. **Existing Code Patterns (`src/app/portal/patient/actions.ts` & `src/lib/schemas.ts`)**:
   - Server Actions use `createClient()` from `@supabase/ssr`, authenticate with `supabase.auth.getUser()`, validate via Zod, and return `{ ok: true, data } | { ok: false, error, fieldErrors }`.
   - `src/lib/schemas.ts` defines `medicationItemSchema`, `surgeryItemSchema`, `bloodGroupEnum`, and `phoneRegex`.

---

## 2. Logic Chain

1. **Search Sanitization & Classification**:
   - Observation 2 (DECISIONS D14) dictates that patient lookups must not concatenate raw query strings into PostgREST `.or()` expressions.
   - Observation 3 (Rule 5) requires escaping `%`, `_`, `,`, `(`, and `)`.
   - Therefore, `searchPatientsAction` classifies query input into 4 deterministic types: `PATIENT_CODE` (regex `/^UMB-[A-Z0-9]{6}$/i`), `QR_TOKEN` (UUID regex), `PHONE` (digits count >= 7), or `NAME` (text).
   - Each branch executes a dedicated parameterized Supabase query (`.eq()` or `.ilike()`), ensuring that user inputs are passed as query parameter values rather than interpolated into PostgREST filter syntax.

2. **Optimistic Concurrency Control (OCC)**:
   - Observation 1 establishes that `clinical_records` maintains an `updated_at` timestamptz that updates on every modification.
   - If two doctors concurrently edit the same record, uncoordinated writes would silently overwrite conflicting clinical changes.
   - Therefore, the client mutation passes `expectedUpdatedAt`. The update executes `.eq('patient_id', patientId).eq('updated_at', expectedUpdatedAt)`. If `data === null`, the action checks if `updated_at` has changed and raises a concurrency conflict exception, preserving medical data integrity.

3. **Trigger-Enforced Stamping**:
   - Observation 1 demonstrates that authenticated users only have column grants on `(medical_conditions, current_medication, previous_surgeries, allergies)`. Direct updates to `is_doctor_verified` or `last_updated_by_doctor_id` will fail with Postgres privilege errors.
   - The trigger `trg_stamp_clinical` has `SECURITY DEFINER` rights and automatically sets `is_doctor_verified = true`, `last_updated_by_doctor_id = auth.uid()`, and `updated_at = now()`.
   - Therefore, `updateClinicalRecordAction` only sends the four clinical fields, relying entirely on the Postgres trigger for audit stamping and verification flips.

4. **Appointment Management & Trigger Integration**:
   - Observation 1 confirms that `trg_appointment_completed` on `appointments` automatically updates `last_appointment_date` and `last_appointment_summary` in `clinical_records` when an appointment is set to `'completed'`.
   - Per Observation 2 (D8), this trigger sets `umbrella.skip_stamp = 'on'`, ensuring that marking an appointment complete does not flip `is_doctor_verified`.
   - Therefore, `updateAppointmentStatusAction` handles standard status updates, while the database orchestrates the clinical history sync.

5. **Authentication & Authorization**:
   - Observation 3 (Rule 2) and Invariant N3 require `supabase.auth.getUser()`, followed by querying `accounts.role === 'doctor'` and `accounts.doctor_status === 'approved'`.
   - Therefore, a reusable `verifyApprovedDoctor` helper encapsulates this pipeline across all doctor actions, returning friendly error strings on authorization failures.

---

## 3. Caveats

1. **Phone Format in Search**: `classifySearchInput` treats inputs with 7 or more digits as phone numbers. If a patient's name happens to contain 7 digits (unlikely in realistic medical settings), it would search phone numbers instead of names.
2. **Postgres Connection Latency for Phone Search**: Because phone numbers are stored across `accounts.contact_phone` and `patient_profiles.emergency_contact_phone`, the phone branch runs two parallel queries and deduplicates in memory. Both tables have indices on phone fields (`accounts_contact_phone_idx`).
3. **Out of Scope (Backlog per DECISIONS D18)**: Administrative UI to approve/reject pending doctors is out of scope for v1 (conducted via Supabase direct SQL update or seed script). SMS alerts, push notifications, and multi-tenant hospital hierarchy are deferred.

---

## 4. Conclusion

The data flow, Server Actions, PostgREST query patterns, input sanitization, and concurrency controls for Milestone M6 (Doctor Portal Surface) are completely specified in `report.md`:
- `src/app/portal/doctor/actions.ts` specifications for `searchPatientsAction`, `updateClinicalRecordAction`, `getDoctorAppointmentsAction`, `createAppointmentAction`, and `updateAppointmentStatusAction`.
- OCC implementation preventing race conditions using `updated_at` preconditions.
- 4-branch search classifier eliminating PostgREST operator injection vulnerabilities.
- Complete Zod validation schemas for all inputs with array length constraints (max 50) and phone regex enforcement.
- Persistent sticky safety banner component contract meeting Invariant N2.

All designs strictly respect existing database triggers, column-level grants, RLS policies, and platform non-negotiables.

---

## 5. Verification Method

To verify these specifications independently:
1. **Inspect Schema & Triggers**:
   - Check `supabase/migrations/0001_umbrella_schema.sql` lines 198-213 (`stamp_clinical_update`), 216-234 (`on_appointment_completed`), and 313-315 (column grants).
2. **Review Architectural Blueprint**:
   - View `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_2_gen2\report.md` for full code specifications, type contracts, and sequence flows.
3. **Verify Existing Project Health**:
   - Run `npm run typecheck` (`tsc --noEmit`) to verify that the project is currently in a clean, buildable state.
4. **Invalidation Conditions**:
   - Modifying `clinical_records` column grants in migration files to include `is_doctor_verified` or `last_updated_by_doctor_id` would invalidate the trigger-only stamping design.
   - Modifying `appointments` status values from lowercase (`'scheduled'`, `'completed'`, `'cancelled'`) would violate check constraints.

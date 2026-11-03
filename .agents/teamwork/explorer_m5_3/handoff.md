# Handoff Report: Milestone M5 Security Boundaries, RLS Constraints & Disappearing Edit UI

**Agent**: Explorer M5-3 (`teamwork_explorer`)  
**Parent**: Teamwork Orchestrator (`35ce3df7-e3d0-4998-8e4c-525735196d55`)  
**Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m5_3`  
**Handoff Type**: Hard (Investigation & Architecture Complete)  

---

## 1. Observation

1. **Disappearing Edit UI & Baseline RPC**:
   - In `supabase/migrations/0001_umbrella_schema.sql` (lines 352-369):
     ```sql
     create or replace function public.submit_self_reported_baseline(p_conditions text[], p_allergies text[])
     returns void language plpgsql security definer set search_path = '' as $$
     begin
       if coalesce(array_length(p_conditions, 1), 0) > 50 or coalesce(array_length(p_allergies, 1), 0) > 50 then
         raise exception 'Too many entries';
       end if;

       update public.clinical_records
       set medical_conditions = coalesce(p_conditions, '{}'),
           allergies = coalesce(p_allergies, '{}')
       where patient_id = (select auth.uid()) and is_doctor_verified = false;

       if not found then
         raise exception 'Record is already doctor-verified, or no patient profile exists';
       end if;
     end $$;
     ```
   - In `docs/DECISIONS.md` (lines 20-21):
     > "D7. Self-reported baseline. SPEC 6.3 lets patients submit a baseline but 4.3 makes clinical_records doctor-only. Resolution: rpc submit_self_reported_baseline (conditions and allergies only, only while is_doctor_verified=false). The clinical_records row is auto-created by a trigger when the patient profile is created. Verification stamps (is_doctor_verified, last_updated_by_doctor_id, updated_at) are set by a BEFORE UPDATE trigger, never by client values. A doctor can verify unchanged self-reported data by saving it."
   - In `supabase/migrations/0001_umbrella_schema.sql` (lines 198-213):
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
   - In `supabase/migrations/0001_umbrella_schema.sql` (lines 278-281):
     ```sql
     create policy cr_update_doctor on public.clinical_records
       for update to authenticated
       using ((select public.is_approved_doctor()))
       with check ((select public.is_approved_doctor()));
     ```

2. **Privacy Boundaries & Non-Negotiable N1**:
   - In `supabase/migrations/0001_umbrella_schema.sql` (lines 325-348):
     The RPC `public.get_emergency_triage_by_token(lookup_token uuid)` constructs a strict `jsonb_build_object` projecting: `full_name`, `contact_phone`, `patient_code`, `age`, `blood_group`, `emergency_contact_name`, `emergency_contact_phone`, `emergency_contact_relation`, `medical_conditions`, `current_medication`, `previous_surgeries`, `allergies`, `last_appointment_date`, `is_doctor_verified`, and `updated_at`.
   - `residential_address`, `spouse_dependents`, `qr_token`, `accounts.email`, and `clinical_records.last_appointment_summary` are verbatim omitted from this projection.
   - In `supabase/tests/rls_smoke.sql` (lines 132-142), Check 2 explicitly tests for `residential_address`, `spouse_dependents`, and `qr_token` and asserts that any exposure raises a privacy violation exception.

3. **Doctor Verification Name Lookup & Accounts RLS Policy**:
   - In `supabase/migrations/0001_umbrella_schema.sql` (lines 251-256):
     ```sql
     create policy accounts_select_my_doctors on public.accounts
       for select to authenticated
       using (role = 'doctor' and exists (
         select 1 from public.appointments ap
         where ap.doctor_id = accounts.id and ap.patient_id = (select auth.uid())
       ));
     ```
   - `accounts_select_my_doctors` allows an authenticated patient to select rows from `accounts` only if an appointment exists between the patient and doctor in `public.appointments`.
   - In `supabase/seed.sql` (lines 173-176 and 234-253), synthetic patient Alex Morgan has `last_updated_by_doctor_id = 'd0000000-0000-0000-0000-000000000001'` (Dr. Sarah Jenkins) and an appointment `b0000000-0000-0000-0000-000000000001` exists between them.
   - If an approved clinician verifies a patient's record without a pre-existing row in `appointments`, `accounts_select_my_doctors` evaluates to false, causing `select full_name from accounts where id = last_updated_by_doctor_id` to return 0 rows.

4. **Schema Scope for Baseline Submission**:
   - `src/lib/schemas.ts` (lines 157-162):
     ```typescript
     export const baselineSubmissionSchema = z.object({
       conditions: z.array(z.string().trim().min(1, 'Condition item cannot be empty')).default([]),
       allergies: z.array(z.string().trim().min(1, 'Allergy item cannot be empty')).default([]),
     });
     ```
   - The RPC `submit_self_reported_baseline` takes exactly 2 arguments (`p_conditions text[], p_allergies text[]`), not 4. Medications and surgeries are managed and verified exclusively by approved physicians.

---

## 2. Logic Chain

1. **Derivation of Disappearing UI Invariant**:
   - *Premise 1*: From Observation 1, `public.stamp_clinical_update` automatically sets `is_doctor_verified := true` whenever an approved physician saves a patient's record.
   - *Premise 2*: From Observation 1, `submit_self_reported_baseline` strictly updates where `is_doctor_verified = false`, raising an exception if `is_doctor_verified = true`. Patients have zero direct update permissions on `clinical_records` (`cr_update_doctor` requires `is_approved_doctor()`).
   - *Inference*: Any interactive baseline editing capability on the client is invalid and rejected by the database once `is_doctor_verified === true`. Therefore, when `is_doctor_verified === true`, the client MUST NOT display the Baseline Editor (no inputs, textareas, or submit buttons). It must be replaced by a read-only clinical overview card displaying doctor verification attribution.

2. **Derivation of Privacy Invariant**:
   - *Premise 1*: Non-negotiable N1 and Observation 2 demonstrate that `residential_address` and `spouse_dependents` are stored only in `patient_profiles` and are excluded from the public emergency RPC whitelist.
   - *Premise 2*: Table-level grants revoke all permissions from `anon`. Authenticated patients can select and update only their own profile row (`auth.uid() = patient_id`).
   - *Inference*: Sensitive demographics are safely bounded to the authenticated owner's portal and approved clinicians. Public emergency responders scanning the QR code cannot access residential address or family dependents under any condition.

3. **Derivation of Resilient Doctor Name Lookup**:
   - *Premise 1*: From Observation 3, `accounts_select_my_doctors` gates access to doctor account names based on the existence of an appointment in `appointments`.
   - *Premise 2*: If a doctor verifies a patient outside of a formal appointment record, querying `accounts` directly from the patient session will return `null`.
   - *Inference*: To avoid UI crashes or rendering `"Verified by Dr. undefined"`, the client must implement a resilient string formatter (`formatDoctorAttribution`) that falls back gracefully to `"Verified by Attending Clinician on <date>"` whenever the joined doctor row is null.

4. **Derivation of Concurrent Edit Handling**:
   - *Premise 1*: A patient may attempt to submit the baseline editor while a doctor verifies their record concurrently.
   - *Premise 2*: The database RPC will throw `'Record is already doctor-verified, or no patient profile exists'`.
   - *Inference*: The Server Action must intercept this specific error message and return a friendly error (`"Your medical record was just verified by your physician. Baseline edits are now locked."`) while triggering `revalidatePath('/portal/patient')` so the UI automatically transitions to the verified state.

---

## 3. Caveats

1. **No Appointments Policy Gap**: Currently, if a doctor verifies a patient's record without an appointment in `appointments`, the patient's authenticated session cannot read the doctor's name from `accounts`. Our report provides a resilient client fallback and specifies the recommended SQL policy expansion, but modifying `0001_umbrella_schema.sql` requires orchestrator approval under project rule 8.
2. **Medications & Surgeries Entry**: Self-reported baseline submission by patients in v1 is intentionally scoped to conditions and allergies per DECISIONS D7. Patients cannot input initial medications or surgeries through this RPC. The UI must clearly indicate this clinical distinction.
3. **Age Calculation**: SPEC 3.1 noted age computed from DOB, but schema stores integer `age` (DECISIONS D5). This is a documented v1 limitation.

---

## 4. Conclusion

1. **UI Disappearing Invariant**: The Patient Portal surface (`/portal/patient`) must conditionally render either `<BaselineEditor />` (when `is_doctor_verified === false`) with amber "Self-Reported" badge and chip adders, or `<ClinicalOverviewCard />` (when `is_doctor_verified === true`) with green "Doctor Verified" badge and doctor attribution. The edit UI must disappear completely from the DOM upon verification.
2. **Privacy Boundary N1**: Demographics (`residential_address`, `spouse_dependents`) are strictly isolated to `patient_profiles` and the authenticated owner, fully excluded from `/emergency/[token]` and RPC `get_emergency_triage_by_token`.
3. **RPC Parameters**: The server action `submitBaselineAction` must pass exactly `{ p_conditions, p_allergies }` to Postgres RPC `submit_self_reported_baseline`.
4. **Doctor Name Lookup**: Query `accounts` via `last_updated_by_doctor_id`, with a defensive fallback to `"Verified by Attending Clinician"` if the doctor row is unreadable due to RLS constraints.
5. **Full Specification**: A complete architecture specification with schemas, error mapping, and component blueprints is documented in `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m5_3\report.md`.

---

## 5. Verification Method

To independently verify the security boundaries and architecture:

1. **Run Database Security Smoke Tests**:
   Execute the RLS smoke test harness in Supabase:
   ```bash
   # From project root, test in Postgres / psql
   psql -f supabase/tests/rls_smoke.sql
   ```
   Verify all 13 checklist items pass, specifically Check 2 (exclusion of address/dependents from triage JSON), Check 3 (tenant isolation), and Check 8 (patient clinical record update blocked, bounded baseline submission allowed unverified and blocked verified).

2. **Verify Zod Schemas & Types**:
   Run TypeScript compilation check:
   ```powershell
   npm run typecheck
   ```
   Inspect `src/lib/schemas.ts` lines 157-162 and `src/lib/supabase/types.ts` lines 302-308 to confirm `submit_self_reported_baseline` takes `p_conditions` and `p_allergies`.

3. **Verify State Transition on Synthetic Data**:
   - Seed data test: Log in as unverified patient Priya Sharma (`priya.sharma@example.test`, password `Password123!`). Expected: `is_doctor_verified === false`, Baseline Editor is displayed.
   - Log in as verified patient Alex Morgan (`alex.morgan@example.test`, password `Password123!`). Expected: `is_doctor_verified === true`, Baseline Editor is completely absent, Clinical Overview Card is displayed with `"Verified by Dr. Sarah Jenkins (Emergency Medicine & Cardiology) on Oct 15, 2026"`.

4. **Invalidation Conditions**:
   - If `residential_address` or `spouse_dependents` appears in `/emergency/[token]` network response.
   - If a verified patient is able to edit conditions or allergies via the UI or direct RPC call.
   - If `doctor.full_name` evaluates to `undefined` or causes runtime exceptions when an appointment row is missing.

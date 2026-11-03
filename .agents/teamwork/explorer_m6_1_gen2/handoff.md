# Handoff Report: Milestone M6 Doctor Portal UI & Safety Banner

**Agent**: Explorer M6-1 (Doctor UI & Safety Banner Explorer)  
**Parent**: Project Orchestrator (`a0698e01-4167-4648-9a8b-05be5311997c`)  
**Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_1_gen2`  
**Handoff Type**: Hard (Task Complete)  

---

### 1. Observation

1. **Schema & Migration Triggers**:
   - In `supabase/migrations/0001_umbrella_schema.sql` (lines 198–214), the database enforces clinician verification stamping via trigger `trg_stamp_clinical`:
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
   - In `supabase/migrations/0001_umbrella_schema.sql` (lines 216–234), trigger `trg_appointment_completed` handles appointment completion per DECISIONS D8:
     ```sql
     if new.status = 'completed' and old.status is distinct from 'completed' then
       perform set_config('umbrella.skip_stamp', 'on', true);
       update public.clinical_records
       set last_appointment_date = new.scheduled_at,
           last_appointment_summary = coalesce(nullif(new.clinical_notes, ''), new.reason)
       where patient_id = new.patient_id
         and (last_appointment_date is null or last_appointment_date <= new.scheduled_at);
       perform set_config('umbrella.skip_stamp', 'off', true);
     end if;
     ```
   - In `supabase/migrations/0001_umbrella_schema.sql` (lines 313–315), column-level grants prevent authenticated users from directly altering `is_doctor_verified` or `last_updated_by_doctor_id`:
     ```sql
     grant update (medical_conditions, current_medication, previous_surgeries, allergies)
       on public.clinical_records to authenticated;
     ```
2. **Existing Doctor Portal Scaffolding**:
   - `src/app/portal/doctor/pending/page.tsx` exists and renders pending screen with account information.
   - `src/app/portal/doctor/page.tsx` does NOT exist yet.
   - `src/components/doctor/` directory does NOT exist yet.
3. **Root Layout Header Structure**:
   - In `src/app/layout.tsx` (line 60), `<header className="sticky top-0 z-40 w-full glass-header">` has height `h-16` (64px).
   - Sticky child surfaces in `/portal/doctor` must use `sticky top-16 z-30` so they align beneath the navigation header without z-index conflicts.
4. **Existing Design Tokens & Primitives**:
   - In `src/app/globals.css` and `tailwind.config.ts`, tokens for `--bg-surface`, `--bg-canvas`, `--text-primary`, `--text-body-secondary`, `--clinical-critical`, `--clinical-verified`, `--clinical-pending`, and `--border-hairline` are established.
   - Shared motion spring `appleSpring` exists in `src/lib/motion.ts`.
   - Accessible UI primitives exist in `src/components/ui/`: `Button` (with 44px min-height), `Input`, `Card`, `Badge`, `BloodGroupPill`, `AllergyAlert`, `Modal` (with focus trap), `Tabs`.
5. **Decisions & Non-Negotiables**:
   - Non-Negotiable N2: Safety banner with patient name, age, blood group, and emergency contact MUST be visible at all times while viewing or editing clinical data.
   - DECISIONS D1: Doctor access gated by `accounts.doctor_status === 'approved'`. Pending doctor sees explicit pending approval message.
   - DECISIONS D14: Multi-modal lookup classifying input into `patient_code` (`UMB-XXXXXX`), `qr_token` (UUID), phone digits (7+), or name `ilike`. Separate parameterized queries; never construct raw `.or()` strings.
   - DECISIONS D15: Escalation link `/portal/doctor?patient_token=<uuid>` or direct query loading.

---

### 2. Logic Chain

1. **Gating Architecture**:
   - Observation 1.1 & 1.5 confirm that pending physicians must not read patient profiles or clinical records.
   - Therefore, `src/app/portal/doctor/page.tsx` must perform a server-side authentication check via `supabase.auth.getUser()`, query `accounts.doctor_status`, and immediately redirect unapproved doctors to `/portal/doctor/pending`.
2. **Multi-Modal Search Architecture**:
   - Observation 1.5 (DECISIONS D14) mandates multi-modal classification with parameterized queries.
   - The regex rules (UMB-XXXXXX, UUID, 7+ digits, Name text) safely classify input and call specific Postgres index-backed queries (`public.patient_profiles(patient_code)`, `public.patient_profiles(qr_token)`, `public.accounts(contact_phone)`), avoiding SQL/PostgREST injection.
3. **Safety Banner Positioning (N2)**:
   - Observation 1.3 shows the root layout header is sticky at `top-0 z-40` with `h-16`.
   - To satisfy Non-Negotiable N2 without layout collision, `PatientSafetyBanner` must use `sticky top-16 z-30`. This guarantees it stays pinned to the top of the viewport when clinical data or surgical history is scrolled.
   - Because patient demographics can only be updated by the patient themselves (Observation 1.1), the banner displays these fields in read-only mode, protecting against accidental identity overwrites during clinical charting.
4. **Clinical Verification Trigger Architecture (D7)**:
   - Observation 1.1 shows that updating `medical_conditions`, `current_medication`, `previous_surgeries`, or `allergies` executes `trg_stamp_clinical` which automatically stamps `is_doctor_verified = true` and `last_updated_by_doctor_id = auth.uid()`.
   - Therefore, the client action `updateClinicalRecordAction` updates those granted columns. An unchanged self-reported record saved by a doctor is stamped as verified by the Postgres trigger without requiring unsafe client-side privilege escalation.
5. **Appointment Lifecycle (D8)**:
   - Observation 1.1 shows trigger `trg_appointment_completed` handles synchronizing `last_appointment_date` and `last_appointment_summary` to `clinical_records` when status transitions to `completed`.
   - Therefore, the appointment status update action simply sets `status = 'completed'` and `clinical_notes`, and PostgreSQL takes care of the clinical record synchronization without flipping `is_doctor_verified`.

---

### 3. Caveats

1. **Age Storage vs Date of Birth**:
   - In accordance with DECISIONS D5, v1 stores and computes `age integer` directly on `patient_profiles`. If future schemas introduce `date_of_birth`, age calculation can be switched to date diffs without altering the `PatientSafetyBanner` interface.
2. **Direct Direct-Link Query Params**:
   - Both `?patient_id=<uuid>` and `?patient_token=<uuid>` (DECISIONS D15) are supported. The server component checks for both to ensure compatibility with escalation links from roadside triage routes.
3. **Pre-Existing Doctor Pending Page**:
   - `src/app/portal/doctor/pending/page.tsx` already contains functional layout and sign-out logic; only its informational banner copy needs enhancement to reflect the exact prompt phrasing.

---

### 4. Conclusion

The Doctor Portal UI architecture is fully mapped, verified against all database schema triggers, RLS policies, column grants, and design tokens.

The Worker can implement Milestone M6 by creating/updating:
1. `src/lib/schemas.ts`: Add `appointmentStatusEnum`, `createAppointmentSchema`, `updateAppointmentStatusSchema`, `doctorClinicalRecordUpdateSchema`.
2. `src/app/portal/doctor/actions.ts`: Implement `searchPatientsAction`, `updateClinicalRecordAction`, `scheduleAppointmentAction`, and `updateAppointmentStatusAction`.
3. `src/components/doctor/patient-safety-banner.tsx`: Persistent read-only safety banner (`sticky top-16 z-30`).
4. `src/components/doctor/patient-search-bar.tsx`: 300ms debounced multi-modal search component.
5. `src/components/doctor/clinical-record-editor.tsx`: Interactive conditions, medications, allergies, surgeries, and verification stamper.
6. `src/components/doctor/appointment-manager.tsx` & `schedule-appointment-modal.tsx`: Upcoming/past appointment manager and booking modal.
7. `src/components/doctor/doctor-workspace.tsx`: Responsive split bento workspace shell.
8. `src/app/portal/doctor/page.tsx`: Server Component entry point with role gate and direct-load support.
9. `src/app/portal/doctor/pending/page.tsx`: Updated with D1 verbatim approval banner.

Complete specifications, interface types, and implementation blueprints are documented in:
`c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_1_gen2\report.md`

---

### 5. Verification Method

To verify the implementation once coded:
1. **TypeScript Typecheck**:
   ```bash
   npm run typecheck
   ```
   *Expected*: Passes with 0 errors (`tsc --noEmit`).
2. **ESLint Verification**:
   ```bash
   npm run lint
   ```
   *Expected*: Passes with 0 lint errors.
3. **Production Build**:
   ```bash
   npm run build
   ```
   *Expected*: Next.js build succeeds with valid `/portal/doctor` and `/portal/doctor/pending` routes.
4. **Safety Banner Visual & DOM Verification**:
   - View `/portal/doctor` in browser at 1280x800 and 375x667 viewports.
   - Inspect `#main-content aside`: confirm `sticky top-16 z-30` remains perpetually pinned below header when scrolling clinical content.
   - Verify all 4 required safety indicators are displayed: Patient Name, Age, Blood Group Pill, Emergency Contact Name & Phone.
5. **Database Trigger Verification**:
   - Save clinical edits for an unverified patient.
   - Inspect database row: verify `is_doctor_verified = true` and `last_updated_by_doctor_id` is set to the current user ID.
   - Complete an appointment: verify `last_appointment_date` and `last_appointment_summary` are populated in `clinical_records` without flipping `is_doctor_verified`.

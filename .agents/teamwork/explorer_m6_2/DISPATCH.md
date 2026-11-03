## 2026-11-01T21:21:50Z
You are Explorer M6-2 (teamwork_explorer).
Your working directory is: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_2
Your parent is Teamwork Orchestrator (conversation ID: 35ce3df7-e3d0-4998-8e4c-525735196d55).

MANDATORY FIRST STEP:
Read c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md.
Also read:
- c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
- c:\Users\DELL\ayesha_pro\medi_qr\supabase\migrations\0001_umbrella_schema.sql
- c:\Users\DELL\ayesha_pro\medi_qr\src\lib\supabase\types.ts
- c:\Users\DELL\ayesha_pro\medi_qr\src\lib\schemas.ts

YOUR TASK:
Investigate and design the Doctor Portal data flow, Server Actions, and optimistic concurrency:
1. Server Actions (`src/app/portal/doctor/actions.ts`):
   - Authenticate caller strictly using `supabase.auth.getUser()`.
   - Verify caller is approved doctor (`accounts.role = 'doctor' AND accounts.doctor_status = 'approved'`).
   - `searchPatientsAction(query: string)`: Multi-modal search (D14) by name, patient code, or QR token.
   - `getPatientClinicalDataAction(patientId: string)`: Loads patient account, demographics (read-only for banner), clinical record, and appointment history.
   - `updateClinicalRecordAction(patientId: string, record: ClinicalRecordInput, expectedUpdatedAt: string)`:
     - Optimistic Concurrency Control: Checks `clinical_records.updated_at === expectedUpdatedAt`. If mismatch, returns conflict error `{ ok: false, conflict: true, currentRecord }`.
     - Updates `medical_conditions`, `allergies`, `current_medication`, `previous_surgeries`, `last_appointment_summary`.
     - The trigger `stamp_clinical_update` will automatically set `updated_at = now()`, `is_doctor_verified = true`, and `last_updated_by_doctor_id = auth.uid()`.
   - `scheduleAppointmentAction(patientId: string, scheduledAt: string, summary: string)`: Inserts into `public.appointments`.
2. Zod validation schemas in `src/lib/schemas.ts`:
   - `clinicalRecordSchema`
   - `appointmentSchema`
3. Detail the function signatures, return types `{ ok: true, data } | { ok: false, error }`, error mappings, and cache invalidation (`revalidatePath('/portal/doctor')`).
4. Write your report to c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_2\report.md.
5. Write your handoff to c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_2\handoff.md.
6. Send a message to parent (35ce3df7-e3d0-4998-8e4c-525735196d55) with your findings.

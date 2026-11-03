## 2026-11-01T23:32:44Z
You are Explorer M6-2 (Doctor Data Flow & Server Actions Explorer).
Your Working Directory: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_2_gen2
Your Parent: Project Orchestrator (Conversation ID: a0698e01-4167-4648-9a8b-05be5311997c)

MANDATORY INPUTS - Read these first:
- Original Request: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
- Project Scope: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
- Full Spec: c:\Users\DELL\ayesha_pro\medi_qr\docs\SPEC.md (Section 4 Data Model, Section 5.2 Doctor Portal)
- Spec Decisions: c:\Users\DELL\ayesha_pro\medi_qr\docs\DECISIONS.md (D1, D3, D7, D14)
- Database Schema: c:\Users\DELL\ayesha_pro\medi_qr\supabase\migrations\0001_umbrella_schema.sql
- TypeScript Types: c:\Users\DELL\ayesha_pro\medi_qr\src\lib\supabase\types.ts
- Security Rules: c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\02-security-privacy.md
- Patient Portal Actions (reference for Server Actions pattern): c:\Users\DELL\ayesha_pro\medi_qr\src\app\portal\patient\actions.ts

YOUR MISSION:
Perform a deep-dive exploration of the data flow, Server Actions, PostgREST query patterns, input sanitization, and concurrency controls required for Milestone M6 (Doctor Portal Surface).

Key Areas to Investigate & Specify:
1. Multi-Modal Search Sanitization (DECISIONS D14 & 02-security-privacy.md Rule 5):
   - Design safe search query execution in `searchPatients`:
   - PostgREST operator injection prevention: Rule 5 states: "Never interpolate user text into PostgREST .or()/.filter() strings or SQL. Escape %, _, ,, (, ) in search terms."
   - Detail exact escaping function and how patient lookup by code (`patient_code`), date of birth, name, and emergency contact phone should be structured with Supabase query builders.
2. Clinical Records Mutation & Concurrency (DECISIONS D7):
   - Concurrency control: How to handle concurrent updates to `clinical_records` (Optimistic Concurrency Control using `updated_at` timestamps or version checks).
   - Server Action `updateClinicalRecord`:
     * Validation via Zod schema (`chronic_conditions`, `medications`, `allergies`, `surgeries`, `implants`, `notes`).
     * Doctor verification stamping: Setting `verified_by_doctor_id = auth.uid()` and `verified_at = now()` (which triggers the disappearing self-reported banner D3/D7).
     * Strict return typing: `{ ok: true, data: ClinicalRecord } | { ok: false, error: string }`.
3. Appointment Scheduling & Management:
   - Server Action `getDoctorAppointments`: Fetch upcoming and past appointments joined with patient profile details.
   - Server Action `createAppointment`: Validate `patient_id`, `scheduled_at`, `notes`, enforce doctor authentication and active status.
   - Server Action `updateAppointmentStatus`: Transition status between `SCHEDULED`, `COMPLETED`, `CANCELLED`.
4. Authentication & Caller Identification (NON-NEGOTIABLE N3):
   - Always use `const { data: { user } } = await supabase.auth.getUser()`, NEVER `getSession()`.
   - Verify `accounts.role === 'DOCTOR'` and `accounts.doctor_status === 'APPROVED'`.
   - Rejection handling: Return friendly error message if unauthorized or unapproved.
5. Zod Schemas & Validation Rules:
   - Specify complete Zod schemas in `src/lib/validation/doctor.ts` or `src/lib/validation/schemas.ts` for all inputs.
   - Phone sanitization (digits + leading + only per Rule 6).

Deliverables:
- Write your complete architectural report to `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_2_gen2\report.md`.
- Write your 5-component handoff report (Observation, Logic Chain, Caveats, Conclusion, Verification Method) to `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_2_gen2\handoff.md`.
- Maintain `progress.md` in your working directory.
- Send a completion message via `send_message` to your parent orchestrator (`a0698e01-4167-4648-9a8b-05be5311997c`).
Do NOT implement code yourself — produce verified specifications and blueprints.

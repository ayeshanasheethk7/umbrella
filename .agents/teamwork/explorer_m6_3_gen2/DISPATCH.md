## 2026-11-01T23:32:55Z
You are Explorer M6-3 (Doctor Security, Gating & Test Explorer).
Your Working Directory: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_3_gen2
Your Parent: Project Orchestrator (Conversation ID: a0698e01-4167-4648-9a8b-05be5311997c)

MANDATORY INPUTS - Read these first:
- Original Request: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
- Project Scope: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
- Full Spec: c:\Users\DELL\ayesha_pro\medi_qr\docs\SPEC.md (Section 5.2 Doctor Portal, Section 6 Security)
- Spec Decisions: c:\Users\DELL\ayesha_pro\medi_qr\docs\DECISIONS.md (D1, D3, D7, D14)
- Database Schema: c:\Users\DELL\ayesha_pro\medi_qr\supabase\migrations\0001_umbrella_schema.sql
- Security Rules: c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\02-security-privacy.md
- RLS Tests (for reference on Postgres security checks): c:\Users\DELL\ayesha_pro\medi_qr\supabase\tests\rls_smoke.sql

YOUR MISSION:
Perform a deep-dive exploration of the security boundary, Postgres RLS enforcement, role gating, and automated verification test design for Milestone M6 (Doctor Portal Surface).

Key Areas to Investigate & Specify:
1. Gating & Authorization Boundaries:
   - What happens when:
     a) Unauthenticated user attempts to visit `/portal/doctor` or call doctor server actions.
     b) Patient attempts to visit `/portal/doctor` or call doctor server actions.
     c) Pending doctor (`doctor_status === 'PENDING'`) attempts to access `/portal/doctor` vs patient records.
     d) Approved doctor accesses patient clinical records and appointments.
   - Server-side guard pattern: Must query `public.accounts` using `supabase.auth.getUser()`.
   - Never trust client-supplied roles or user_metadata for authorization (NON-NEGOTIABLE N3).
2. Postgres RLS Alignment:
   - Check `0001_umbrella_schema.sql` policies for `patient_profiles`, `clinical_records`, and `appointments`:
     * Approved doctors (`is_approved_doctor()`) have SELECT on `patient_profiles` and SELECT/UPDATE on `clinical_records`.
     * Doctor appointment access: Doctors can select and update appointments where `doctor_id = auth.uid()`.
   - Confirm that pending doctors cannot read ANY patient profile or clinical record through RLS even if they invoke Supabase client directly.
3. Automated Test Suite Specification for Verification:
   - Design the exact verification tests to be executed by Worker, Reviewers, Challengers, and Auditor:
     * Gating & RBAC tests: Pending doctor blocked from patient data, non-doctor rejected.
     * Persistent safety banner verification (DOM existence, sticky CSS properties, required fields: name, age, blood group, emergency contact).
     * Multi-modal search test matrix (patient_code, dob, name, phone, SQL/PostgREST injection attempts like `%` and `)`).
     * Optimistic concurrency test (simultaneous updates to same clinical record).
     * Doctor verification stamp test (`verified_by_doctor_id`, `verified_at`, disappearing self-reported baseline).
     * Appointment lifecycle tests (`SCHEDULED` -> `COMPLETED`/`CANCELLED`).
     * A11y & responsive tests (375x667, 1280x800, 44px min touch target, color contrast).

Deliverables:
- Write your complete architectural report to `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_3_gen2\report.md`.
- Write your 5-component handoff report (Observation, Logic Chain, Caveats, Conclusion, Verification Method) to `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_3_gen2\handoff.md`.
- Maintain `progress.md` in your working directory.
- Send a completion message via `send_message` to your parent orchestrator (`a0698e01-4167-4648-9a8b-05be5311997c`).
Do NOT implement code yourself — produce verified specifications and blueprints.

# Dispatch for Challenger M6-1 (Gen 2)
Focus: Adversarial Security & Penetration Testing of Doctor Portal Surface.

## 2026-11-02T00:06:30Z
You are Challenger M6-1 (Doctor Portal Adversarial Security & Penetration Challenger).
Your Working Directory: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\challenger_m6_1_gen2
Your Parent: Project Orchestrator (Conversation ID: a0698e01-4167-4648-9a8b-05be5311997c)

MANDATORY INPUTS - Read these first:
- Original Request: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
- Project Scope: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
- Full Spec: c:\Users\DELL\ayesha_pro\medi_qr\docs\SPEC.md
- Spec Decisions: c:\Users\DELL\ayesha_pro\medi_qr\docs\DECISIONS.md
- Security Rules: c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\02-security-privacy.md
- Database Migration: c:\Users\DELL\ayesha_pro\medi_qr\supabase\migrations\0001_umbrella_schema.sql
- Implemented Doctor Portal Backend Files:
  * c:\Users\DELL\ayesha_pro\medi_qr\src\app\portal\doctor\actions.ts
  * c:\Users\DELL\ayesha_pro\medi_qr\src\lib\schemas.ts
  * c:\Users\DELL\ayesha_pro\medi_qr\src\app\portal\doctor\page.tsx
  * c:\Users\DELL\ayesha_pro\medi_qr\scripts\verify_m6.py

CHALLENGE MISSION:
Perform empirical adversarial penetration attacks and security stress-testing against the Doctor Portal implementation. Build and run adversarial test harnesses to probe for vulnerabilities.

Key Adversarial Attack Scenarios to Execute:
1. PostgREST Operator & SQL Injection Attacks on Patient Search:
   - Inject PostgREST operators into `searchPatientsAction`:
     * `",full_name.neq.null"`
     * `"%') or true --"`
     * `"(status.eq.approved)"`
     * Deep wildcard flooding (`%%%%%`, `_____`)
   - Verify all wildcards are neutralized, parameter queries are isolated, and no unauthorized records or syntax errors occur.
2. Authorization & RBAC Bypass Attacks:
   - Simulate calls from:
     * Unauthenticated user (`user === null`)
     * Patient user (`role === 'patient'`)
     * Pending doctor (`role === 'doctor'`, `doctor_status === 'pending'`)
   - Test each action: `searchPatientsAction`, `updateClinicalRecordAction`, `getDoctorAppointmentsAction`, `createAppointmentAction`, `updateAppointmentStatusAction`.
   - Verify 100% rejection rate with appropriate error responses (Unauthorized / Forbidden / Approval pending).
3. Audit Stamp Tampering Attacks:
   - Attempt to pass `is_doctor_verified: false` or a forged `last_updated_by_doctor_id` in the update payload.
   - Verify that column update grants prevent direct alteration, and DB trigger `trg_stamp_clinical` overrides with `true` and the authenticated doctor's ID.
4. Concurrency Collision & Stale Update Attacks:
   - Simulate two doctors editing the same record concurrently:
     * Doctor A reads record at `T0`.
     * Doctor B updates record at `T1` (new `updated_at` = `T1`).
     * Doctor A attempts update at `T2` with `expectedUpdatedAt = T0`.
   - Verify that Doctor A's update fails with `{ ok: false, conflict: true }` and does not overwrite Doctor B's clinical notes or allergies.
5. Invariant N4 Secret Leak Check:
   - Verify zero occurrences of `SUPABASE_SERVICE_ROLE_KEY` across all newly created doctor portal files, tests, and scripts.

Deliverables:
- Write `report.md` in your working directory documenting all attack test results, test code, and findings.
- Write 5-component `handoff.md` with explicit verdict: **APPROVE** or **REQUEST_CHANGES**.
- Send completion message to parent orchestrator.

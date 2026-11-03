## 2026-11-01T21:22:00Z
You are Explorer M6-3 (teamwork_explorer).
Your working directory is: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_3
Your parent is Teamwork Orchestrator (conversation ID: 35ce3df7-e3d0-4998-8e4c-525735196d55).

MANDATORY FIRST STEP:
Read c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md.
Also read:
- c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
- c:\Users\DELL\ayesha_pro\medi_qr\docs\DECISIONS.md (D1, D7, D8)
- c:\Users\DELL\ayesha_pro\medi_qr\supabase\migrations\0001_umbrella_schema.sql
- c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\02-security-privacy.md

YOUR TASK:
Investigate and design Doctor Portal security, RLS boundaries, and clinical trigger mechanics:
1. Doctor RBAC & Approval Gate (DECISIONS D1):
   - Analyze `public.is_approved_doctor()` SQL function.
   - What happens if a pending doctor attempts to call doctor server actions or load `/portal/doctor`?
   - Verify that all doctor actions and queries require `is_approved_doctor() = true`.
2. Postgres Policies on Clinical Data:
   - RLS policy `cr_update_doctor` on `clinical_records`:
     - Requires `is_approved_doctor()`.
     - Trigger `stamp_clinical_update` BEFORE UPDATE sets `is_doctor_verified = true` and `last_updated_by_doctor_id = auth.uid()`.
   - RLS on `patient_profiles` and `accounts`:
     - Can approved doctors select patient profiles for search? (Policy `pp_select_approved_doctor` and `accounts_select_approved_doctor`).
     - Can approved doctors UPDATE patient profiles? No, doctor updates clinical records only! Demographics remain patient-owned.
3. Appointments RLS & Linkage:
   - Policies on `public.appointments`:
     - `appointments_select_participant`: doctor can view appointments where `doctor_id = auth.uid()`.
     - `appointments_insert_doctor`: approved doctor can insert appointments where `doctor_id = auth.uid()`.
     - `appointments_update_doctor`: doctor can update status/summary.
4. Edge cases & error handling:
   - Concurrency conflict handling when two doctors update same patient.
   - Missing patient record fallback.
   - Malformed search input (SQL injection, special characters in ILIKE).
5. Write your report to c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_3\report.md.
6. Write your handoff to c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_3\handoff.md.
7. Send a message to parent (35ce3df7-e3d0-4998-8e4c-525735196d55) with your findings.

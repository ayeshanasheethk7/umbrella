## 2026-11-01T21:21:39Z
You are Explorer M6-1 (teamwork_explorer).
Your working directory is: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_1
Your parent is Teamwork Orchestrator (conversation ID: 35ce3df7-e3d0-4998-8e4c-525735196d55).

MANDATORY FIRST STEP:
Read c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md.
Also read:
- c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
- c:\Users\DELL\ayesha_pro\medi_qr\docs\SPEC.md (Section 5.2 Doctor Portal)
- c:\Users\DELL\ayesha_pro\medi_qr\docs\DECISIONS.md (D1, D7, D8, D14)
- c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\01-design-system.md

YOUR TASK:
Investigate and design the Doctor Portal UI architecture (`/portal/doctor`):
1. Multi-modal Patient Lookup UX (DECISIONS D14):
   - Fast search bar supporting: Patient Name, Patient Code (e.g. `UMB-XXXXXX`), and QR Token (UUID).
   - Instant search dropdown / results list with BloodGroupPill and age.
2. Persistent Read-Only Safety Banner (NON-NEGOTIABLE N2):
   - "The Doctor portal always shows a read-only banner with patient name, age, blood group and emergency contact while editing clinical data."
   - Must be sticky at top of clinical editing surface.
   - Shows: Patient Name, Age, Blood Group pill, Primary Emergency Contact (name + phone `tel:` link).
   - Invariant: Read-only, cannot be dismissed or hidden while patient is selected.
3. Clinical Record Editor:
   - Conditions chip editor.
   - Allergies chip editor with `AllergyAlert` display.
   - Structured Medication list editor (`name`, `dosage`, `frequency`).
   - Structured Surgery list editor (`procedure`, `year`).
   - Appointment notes / summary textarea.
4. Appointment Scheduling Interface:
   - Date picker, status badge, appointment history summary.
5. Produce component blueprints for `src/components/doctor/` and `src/app/portal/doctor/page.tsx`.
6. Write your report to c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_1\report.md.
7. Write your handoff to c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_1\handoff.md.
8. Send a message to parent (35ce3df7-e3d0-4998-8e4c-525735196d55) with your findings.

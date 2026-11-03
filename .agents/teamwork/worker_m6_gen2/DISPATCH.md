## 2026-11-01T23:39:21Z
You are Worker M6 (Doctor Portal Surface Implementation Worker).
Your Working Directory: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m6_gen2
Your Parent: Project Orchestrator (Conversation ID: a0698e01-4167-4648-9a8b-05be5311997c)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY INPUTS - Read these first:
- Original Request: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
- Project Scope: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
- Full Spec: c:\Users\DELL\ayesha_pro\medi_qr\docs\SPEC.md (Section 5.2 Doctor Portal, Section 7 Folder Structure)
- Spec Decisions: c:\Users\DELL\ayesha_pro\medi_qr\docs\DECISIONS.md (D1, D3, D6, D7, D8, D14, D15)
- Design Tokens: c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\01-design-system.md
- Security Rules: c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\02-security-privacy.md
- Database Schema & Grants: c:\Users\DELL\ayesha_pro\medi_qr\supabase\migrations\0001_umbrella_schema.sql
- TypeScript Types: c:\Users\DELL\ayesha_pro\medi_qr\src\lib\supabase\types.ts
- Explorer M6-1 Blueprint & Handoff:
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_1_gen2\report.md
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_1_gen2\handoff.md
- Explorer M6-2 Data Flow & Handoff:
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_2_gen2\report.md
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_2_gen2\handoff.md
- Explorer M6-3 Security & 37-Point Test Blueprint:
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_3_gen2\report.md
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_3_gen2\handoff.md

EXCLUSIVE FILE WRITE OWNERSHIP:
You own and will create/modify ONLY these files:
- `src/lib/schemas.ts` (adding doctor Zod schemas)
- `src/app/portal/doctor/actions.ts` (server actions for doctor portal)
- `src/components/doctor/patient-safety-banner.tsx` (persistent sticky safety banner)
- `src/components/doctor/patient-search-bar.tsx` (multi-modal search component)
- `src/components/doctor/clinical-record-editor.tsx` (clinical record editor & OCC)
- `src/components/doctor/appointment-manager.tsx` (appointments list and status manager)
- `src/components/doctor/schedule-appointment-modal.tsx` (schedule appointment modal)
- `src/components/doctor/doctor-workspace.tsx` (split bento doctor workspace)
- `src/app/portal/doctor/page.tsx` (server component entry point with RBAC gate and direct-load)
- `src/app/portal/doctor/pending/page.tsx` (pending doctor screen with exact D1 copy)
- `scripts/verify_m6.py` (comprehensive 37-point verification test script)

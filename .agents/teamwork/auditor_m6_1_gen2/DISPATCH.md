## 2026-11-02T00:06:53Z
You are Forensic Auditor M6-1 (Forensic Integrity Auditor).
Your Working Directory: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\auditor_m6_1_gen2
Your Parent: Project Orchestrator (Conversation ID: a0698e01-4167-4648-9a8b-05be5311997c)

MANDATORY INPUTS - Read these first:
- Original Request: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
- Project Scope: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
- Full Spec: c:\Users\DELL\ayesha_pro\medi_qr\docs\SPEC.md
- Security Rules: c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\02-security-privacy.md
- Worker M6 Report & Handoff:
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m6_gen2\report.md
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m6_gen2\handoff.md
- Codebase Files under Audit:
  * c:\Users\DELL\ayesha_pro\medi_qr\src\app\portal\doctor\actions.ts
  * c:\Users\DELL\ayesha_pro\medi_qr\src\app\portal\doctor\page.tsx
  * c:\Users\DELL\ayesha_pro\medi_qr\src\app\portal\doctor\pending\page.tsx
  * c:\Users\DELL\ayesha_pro\medi_qr\src\components\doctor\patient-safety-banner.tsx
  * c:\Users\DELL\ayesha_pro\medi_qr\src\components\doctor\patient-search-bar.tsx
  * c:\Users\DELL\ayesha_pro\medi_qr\src\components\doctor\clinical-record-editor.tsx
  * c:\Users\DELL\ayesha_pro\medi_qr\src\components\doctor\appointment-manager.tsx
  * c:\Users\DELL\ayesha_pro\medi_qr\src\components\doctor\schedule-appointment-modal.tsx
  * c:\Users\DELL\ayesha_pro\medi_qr\src\components\doctor\doctor-workspace.tsx
  * c:\Users\DELL\ayesha_pro\medi_qr\src\lib\schemas.ts
  * c:\Users\DELL\ayesha_pro\medi_qr\scripts\verify_m6.py

AUDIT MISSION:
Execute an unsparing, empirical forensic integrity audit on Milestone M6.
You are the final integrity gatekeeper. If you find ANY cheating, dummy facades, mock auth bypasses, secret leaks, or file character bloat, you must veto with INTEGRITY VIOLATION.

Execute the following 7 Forensic Audit Checks:
1. Check 1: Zero Facades / Dummies:
   - Verify that all components and server actions implement genuine, functional logic.
   - Zero placeholder buttons, zero `TODO`, zero "coming soon", zero fake mock data in UI components.
2. Check 2: Zero Mock Auth:
   - Invariant N5: `/portal/doctor` and actions call `supabase.auth.getUser()`, never mock auth or hardcoded dummy sessions.
   - Confirm caller identity is verified against `public.accounts` on the server.
3. Check 3: Invariant N4 Secret Leak Check:
   - The `service_role` key must NEVER appear in code, scripts, seeds, tests, or config files.
   - Confirm only `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` are used.
4. Check 4: Invariant N3 Caller Identity Check:
   - Identify caller with `supabase.auth.getUser()`, NEVER `getSession()`.
   - Scan all newly created/modified doctor portal files for any instance of `getSession()`.
5. Check 5: Invariant N10 Strict Typing:
   - Zero `any`, zero `@ts-ignore`, zero `@ts-expect-error` without written justification.
6. Check 6: 12,000 Character Rule Compliance:
   - Run `python scripts/audit.py` to verify that EVERY rule, doc, schema, and source target is strictly < 12,000 characters.
7. Check 7: Working Directory Purity:
   - Verify that `.agents/teamwork/` directories contain ONLY coordination markdown files (.md) and zero source code, test scripts, or binaries.

Deliverables:
- Write `report.md` in your working directory documenting the result of all 7 forensic checks with exact file paths and evidence.
- Write 5-component `handoff.md` with explicit binary verdict: **CLEAN** or **INTEGRITY VIOLATION**.
- Send completion message to parent orchestrator.

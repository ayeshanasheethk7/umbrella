## 2026-11-02T01:29:34Z
You are auditor_m7, the Forensic Integrity Auditor for Milestone M7 of the Umbrella Emergency Medical ID Platform.

Your working directory is: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\auditor_m7

MANDATORY INPUTS:
1. Master user request: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md (READ THIS FIRST).
2. Project specification & architecture: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
3. Worker handoff report: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m7\handoff.md
4. Codebase files to audit:
   - c:\Users\DELL\ayesha_pro\medi_qr\src\lib\supabase\anon.ts
   - c:\Users\DELL\ayesha_pro\medi_qr\src\lib\schemas.ts
   - c:\Users\DELL\ayesha_pro\medi_qr\src\app\emergency\[token]\page.tsx
   - c:\Users\DELL\ayesha_pro\medi_qr\src\app\emergency\[token]\not-found.tsx
   - c:\Users\DELL\ayesha_pro\medi_qr\src\components\emergency\emergency-triage-view.tsx
   - c:\Users\DELL\ayesha_pro\medi_qr\src\components\emergency\sticky-emergency-call-bar.tsx
   - c:\Users\DELL\ayesha_pro\medi_qr\src\components\emergency\triage-allergies-alert.tsx
   - c:\Users\DELL\ayesha_pro\medi_qr\src\components\emergency\triage-vitals-card.tsx
   - c:\Users\DELL\ayesha_pro\medi_qr\src\components\emergency\triage-clinical-history.tsx
   - c:\Users\DELL\ayesha_pro\medi_qr\src\components\emergency\triage-escalation-footer.tsx
   - c:\Users\DELL\ayesha_pro\medi_qr\scripts\verify_m7.py
5. Security Rules: c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\02-security-privacy.md

FORENSIC AUDIT PROTOCOL:
Conduct a strict, independent forensic integrity verification across these 7 binary checks:
- **Check 1: Zero Hardcoded Test Results & Facades**:
  Verify that implementations contain genuine logic. No dummy objects, no mock returns hardcoded to satisfy tests. Verify that `page.tsx` genuinely queries the Supabase client and RPC `get_emergency_triage_by_token`.
- **Check 2: Invariant N1 Zero Data Exposure**:
  Verify that `residential_address` and `spouse_dependents` are NEVER leaked, rendered, or present in any shape or form across the emergency surface.
- **Check 3: Invariant N4 Zero Service Role & Secret Leaks**:
  Verify that zero occurrences of `service_role` exist in code, comments, or env files. Verify that `src/lib/supabase/anon.ts` uses ONLY the anon key.
- **Check 4: Invariants N8 & D13 Zero Framer-Motion**:
  Verify that zero `framer-motion` imports or transitive motion button imports exist in `/emergency/` or `src/components/emergency/*`.
- **Check 5: Invariant N10 Strict Typing**:
  Verify zero `: any`, zero `as any`, and zero `@ts-ignore` or `@ts-expect-error` across all newly created or modified files.
- **Check 6: Rule 12k Headroom Compliance**:
  Verify that EVERY file in the repository (especially `src/lib/schemas.ts` and `scripts/verify_m7.py`) is strictly under 12,000 characters using `python scripts/audit.py`.
- **Check 7: Workspace Purity & Non-Pollution**:
  Verify that no scratch files, temp files, test outputs, or uncommitted dumps pollute the workspace root or source directories.

DELIVERABLE:
Write your structured forensic audit report to:
`c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\auditor_m7\handoff.md`
Provide an explicit binary verdict:
- **CLEAN** (if and only if ALL 7 checks pass with zero violations)
- **INTEGRITY VIOLATION** (if any check fails — this serves as a non-negotiable hard veto)
When done, send a message to parent with your verdict and report path.

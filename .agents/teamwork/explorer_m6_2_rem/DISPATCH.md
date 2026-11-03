## 2026-11-02T00:16:14Z
You are Explorer M6-2 Remediation (Doctor Search Classification & Query Remediation Explorer).
Your Working Directory: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_2_rem
Your Parent: Project Orchestrator (Conversation ID: a0698e01-4167-4648-9a8b-05be5311997c)

MANDATORY INPUTS - Read these first:
- Original Request: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
- Project Scope: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
- Full Spec: c:\Users\DELL\ayesha_pro\medi_qr\docs\SPEC.md
- Spec Decisions: c:\Users\DELL\ayesha_pro\medi_qr\docs\DECISIONS.md (D14)
- Security Rules: c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\02-security-privacy.md
- FULL FORENSIC AUDIT EVIDENCE:
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\auditor_m6_1_gen2\report.md
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\auditor_m6_1_gen2\handoff.md
- Reviewer & Challenger Reports:
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m6_2_gen2\report.md
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m6_2_gen2\handoff.md
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\challenger_m6_1_gen2\report.md
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\challenger_m6_1_gen2\handoff.md
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\challenger_m6_2_gen2\report.md
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\challenger_m6_2_gen2\handoff.md
- Implementation under Fix:
  * c:\Users\DELL\ayesha_pro\medi_qr\src\app\portal\doctor\actions.ts

REMEDIATION EXPLORATION MISSION:
Develop an exact, code-level fix strategy for the critical search flaws in `src/app/portal/doctor/actions.ts`:
1. Critical Precedence Inversion (UUID Shadowing):
   - Root cause: In `searchPatientsAction`, `digits.length >= 7` is evaluated at line 81 BEFORE the UUID regex at line 97. Standard UUID v4 tokens contain ~20 numeric digits, so 100% of UUID searches get intercepted as phone searches and return 0 results!
   - Fix strategy:
     * Check 1: Patient Code: `/^UMB-[A-Za-z0-9]{6}$/i.test(q)` -> exact lookup on `patient_code`.
     * Check 2: QR Token UUID: `/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(q)` -> exact lookup on `qr_token`.
     * Check 3: Phone: `digits.length >= 7` -> search phone numbers.
     * Check 4: Sanitized Name: fallback.
2. Wildcard Flood Match-All Query (INJECTION_1.5):
   - Root cause: `escapeSearchTerm("%%%%%")` returns `""`. When `q = "%%%%%"`, `q.length >= 2` passes, but the query becomes `ilike '%%'`, which dumps the first 20 records in PostgreSQL!
   - Fix strategy:
     * Compute `const cleanTerm = escapeSearchTerm(q);`
     * If `cleanTerm.length < 2`, return `{ ok: true, data: [] }` immediately!
3. Format-Resilient Phone Search:
   - Ensure phone search works whether stored with formatting or raw digits, without PostgREST injection.

Deliverables:
- Write `report.md` with complete, drop-in replacement snippets for `searchPatientsAction` in `actions.ts`.
- Write 5-component `handoff.md`.
- Send completion message to parent orchestrator.
Do NOT modify source files directly.

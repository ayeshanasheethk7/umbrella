## 2026-11-02T00:36:06Z

You are Worker M6 Remediation (Doctor Portal Remediation Worker).
Your Working Directory: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m6_rem
Your Parent: Project Orchestrator (Conversation ID: a0698e01-4167-4648-9a8b-05be5311997c)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY INPUTS - Read these first:
- Original Request: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
- Project Scope: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
- Full Spec: c:\Users\DELL\ayesha_pro\medi_qr\docs\SPEC.md
- Design Tokens: c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\01-design-system.md
- Security Rules: c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\02-security-privacy.md
- FULL FORENSIC AUDIT EVIDENCE (Hard Veto):
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\auditor_m6_1_gen2\report.md
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\auditor_m6_1_gen2\handoff.md
- Remediation Explorer Reports (with complete drop-in replacement blueprints):
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_1_rem\report.md
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_1_rem\handoff.md
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_2_rem\report.md
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_2_rem\handoff.md
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_3_rem\report.md
  * c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_3_rem\handoff.md

EXCLUSIVE FILE WRITE OWNERSHIP:
You own and will modify ONLY these files:
- `src/components/doctor/patient-safety-banner.tsx`
- `src/components/doctor/patient-search-bar.tsx`
- `src/components/doctor/clinical-record-editor.tsx`
- `src/components/doctor/appointment-manager.tsx`
- `src/components/doctor/doctor-workspace.tsx`
- `src/app/portal/doctor/actions.ts`
- `scripts/verify_m6.py`

REMEDIATION TASKS TO EXECUTE:
1. `src/components/doctor/patient-safety-banner.tsx`:
   - Change `sticky top-0 z-30` to `sticky top-16 z-30` so the safety banner mounts flush beneath the 64px global header without occlusion when scrolled (satisfying Invariant N2).
2. `src/components/doctor/patient-search-bar.tsx`:
   - Expand clear button to `min-h-[44px] min-w-[44px]` with `pr-12` input padding.
3. `src/components/doctor/clinical-record-editor.tsx`:
   - Reuse `delCls` (`min-h-[44px] min-w-[44px] ...`) inside `Tag` component so tag delete buttons meet >= 44px touch targets (and reduce file size to ~11,946 chars, well below 12,000 limit).
4. `src/components/doctor/appointment-manager.tsx`:
   - Expand filter tab buttons to `min-h-[44px] px-4 py-2` inside a `min-h-[52px]` container.
5. `src/components/doctor/doctor-workspace.tsx`:
   - Expand workspace tab buttons to `min-h-[44px] px-4 py-2` inside a `min-h-[52px]` container.
   - Eliminate `any`: Replace `onClick={() => setTab(t.id as any)}` with typed `WorkspaceTab` union (`'records' | 'appointments' | 'preview'`).
   - Keep file length strictly < 12,000 characters.
6. `src/app/portal/doctor/actions.ts`:
   - Reorder search classification in `searchPatientsAction`:
     * Check 1: Patient Code (`/^UMB-[A-Za-z0-9]{6}$/i`)
     * Check 2: QR Token UUID (`/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i`)
     * Check 3: Phone Search (`digits.length >= 7`)
     * Check 4: Sanitized Name fallback.
   - Wildcard flood defense: Guard name search with `if (cleanTerm.length < 2) return { ok: true, data: [] };` so queries like `%%%%%` return 0 records instead of dumping all patients via `ilike '%%'`.
   - Invariant N10 Strict Typing:
     * Replace `(r: any)` at line 55 with `interface PatientSearchResultRow`.
     * Replace `(row: any)` at line 204 with `interface AppointmentDbRow`.
     * Zero `any` types across the entire file.
   - Keep file length strictly < 12,000 characters.
7. `scripts/verify_m6.py`:
   - Upgrade test suite to include:
     * Runtime UUID classification test (`a1a1a1a1-a1a1-4a1a-8a1a-a1a1a1a1a1a1` must route to QR token branch, not phone).
     * Wildcard flood test (`%%%%%` must return 0 records).
     * Strict touch target inspection checking all interactive buttons for minimum 44px height and width.
     * Zero-`any` regex scan across all doctor portal files (`grep ": any"` and `"as any"` = 0).

EXECUTION & VERIFICATION REQUIREMENTS:
- Run `npm run typecheck` (`tsc --noEmit`).
- Run `npm run lint`.
- Run `python scripts/verify_m6.py`.
- Run `python scripts/verify_m5.py` and `python scripts/verify_m4.py` (ensure zero regressions).
- Run `python scripts/audit.py` (ensure all files strictly < 12,000 characters).
- Run `python scripts/challenger_m6_adversarial.py` (ensure adversarial tests pass 100%).
- Write `report.md` and 5-component `handoff.md` in your working directory.
- Send completion message to parent orchestrator.

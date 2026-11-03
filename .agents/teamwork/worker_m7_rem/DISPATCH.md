# DISPATCH: Worker M7 Remediation (worker_m7_rem)

**Working Directory**: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m7_rem
**Original Request File**: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
**Scope Document**: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Remediation Objectives
Apply precise fixes formulated by Explorers M7-1 Rem, M7-2 Rem, and Reviewer M7-1 to resolve the Forensic Auditor Hard Veto and Reviewer change requests:

1. **Purge Literal `service_role` from `src/lib/supabase/anon.ts`**:
   - In JSDoc comment at line 8:
     Replace: ` * - N4: Uses ONLY anon/publishable key; zero service_role usage.`
     With: ` * - N4: Uses ONLY anon/publishable key; zero backend administrative key usage.`
   - Verification: `python scripts/verify_m4.py` Check 12 must find 0 leaks in `src/`.

2. **Fix Undefined Tailwind Token in `src/components/emergency/triage-vitals-card.tsx`**:
   - Line 33: Replace `clinical-attention/10 text-clinical-attention-text border border-clinical-attention/30` with `clinical-pending/10 text-clinical-pending-text border border-clinical-pending/30`
   - Line 43: Replace `text-clinical-attention` with `text-clinical-pending`

3. **Fix WCAG AA Contrast on Small Red Text**:
   - `src/components/emergency/triage-allergies-alert.tsx:35-36`: Replace `text-clinical-critical` with `text-clinical-critical-text` for the AlertOctagon icon and the `text-xs font-extrabold` heading.
   - `src/app/emergency/[token]/not-found.tsx:31`: Replace `text-clinical-critical` with `text-clinical-critical-text` for the `text-xs font-bold uppercase` paragraph.

4. **Add `.passthrough()` to `emergencyTriageSchema` in `src/lib/schemas.ts`**:
   - At line ~248, chain `.passthrough()` right after `z.object({...})` before `.superRefine(...)`.
   - Ensure `src/lib/schemas.ts` remains strictly under 12,000 characters.

5. **Enhance `scripts/verify_m7.py`**:
   - Include `contents["anon_client"]` in `emergency_contents` list so `AUTH-01-ZERO-SERVICE-ROLE` scans `anon.ts`.
   - Enhance token assertion in `DESIGN-02-SYSTEM-TOKENS` to ensure `clinical-attention` is absent and `clinical-pending` / `clinical-pending-text` and `text-clinical-critical-text` are present.
   - Include `scripts/verify_m4.py` in Category 9 regression checks.
   - Ensure `scripts/verify_m7.py` remains strictly under 12,000 characters.

6. **Execute Verification Commands**:
   - `python scripts/verify_m7.py` (must pass 100%)
   - `python scripts/verify_m6.py` (38/38 pass)
   - `python scripts/verify_m5.py` (74/74 pass)
   - `python scripts/verify_m4.py` (51/51 pass, 0 service_role leaks)
   - `python scripts/audit.py` (all files in repository strictly < 12,000 characters)

7. **Deliverables**:
   - Write comprehensive report to `report.md` in your working directory.
   - Write 5-component handoff report to `handoff.md` in your working directory.
   - Send completion message to orchestrator.


## 2026-11-02T11:45:25Z

[Message] timestamp=2026-11-02T11:45:25Z sender=9a03a7b4-6eb6-4d41-bad3-e7c232a57fe2 priority=MESSAGE_PRIORITY_HIGH content=You are worker_m7_rem, the Milestone M7 Remediation Worker for the Umbrella Emergency Medical ID platform.

Working Directory: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m7_rem
Original Request File: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
Master Project Plan: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
Dispatch Instructions: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m7_rem\DISPATCH.md
Parent Orchestrator: 9a03a7b4-6eb6-4d41-bad3-e7c232a57fe2

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY RULES:
1. First read ORIGINAL_REQUEST.md, PROJECT.md, and DISPATCH.md before touching any code.
2. Every file created or edited must remain strictly under 12,000 characters.
3. Invariant N4 is strictly zero tolerance: the string `service_role` must NEVER appear in code, comments, tests, configs, or logs.
4. Non-negotiables N1-N10 must remain inviolate. Zero mock auth, zero any types.

Remediation Tasks to Execute:
1. Purge literal `service_role` from `src/lib/supabase/anon.ts` (line 8 JSDoc comment):
   Replace: ` * - N4: Uses ONLY anon/publishable key; zero service_role usage.`
   With: ` * - N4: Uses ONLY anon/publishable key; zero backend administrative key usage.`
   (See patch at c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m7_1_rem\remediation.patch)

2. Fix undefined Tailwind token in `src/components/emergency/triage-vitals-card.tsx`:
   Line 33: Replace `clinical-attention/10 text-clinical-attention-text border border-clinical-attention/30` with `clinical-pending/10 text-clinical-pending-text border border-clinical-pending/30`
   Line 43: Replace `<AlertTriangle className="w-4 h-4 text-clinical-attention shrink-0"` with `<AlertTriangle className="w-4 h-4 text-clinical-pending shrink-0"`
   (See patch at c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m7_2_rem\remediation_m7_2.patch)

3. Fix WCAG AA contrast failure on small red text:
   - In `src/components/emergency/triage-allergies-alert.tsx:35-36`: Replace `text-clinical-critical` with `text-clinical-critical-text` for the AlertOctagon icon and the `text-xs font-extrabold uppercase` heading.
   - In `src/app/emergency/[token]/not-found.tsx:31`: Replace `text-clinical-critical` with `text-clinical-critical-text` for the `text-xs font-bold uppercase` paragraph.
   (See patch at c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m7_2_rem\remediation_m7_2.patch)

4. Add `.passthrough()` to `emergencyTriageSchema` in `src/lib/schemas.ts`:
   Around line 248, chain `.passthrough()` right after `z.object({...})` before `.superRefine(...)`.
   Verify `src/lib/schemas.ts` remains strictly under 12,000 characters.

5. Enhance `scripts/verify_m7.py`:
   - In `emergency_contents` list (lines 38-42), append `contents["anon_client"]` so `AUTH-01-ZERO-SERVICE-ROLE` scans `anon.ts`.
   - In `DESIGN-02-SYSTEM-TOKENS`, assert that `clinical-attention` is NOT in `contents["vitals"]`, `clinical-pending` and `clinical-pending-text` are in `contents["vitals"]`, and `text-clinical-critical-text` is in `contents["allergies"]` and `contents["not_found"]`.
   - In Category 9 regression checks, include `python scripts/verify_m4.py` (51 checks) alongside m5, m6, and audit.py.
   - Verify `scripts/verify_m7.py` remains strictly under 12,000 characters.

6. Run All Verification Suites:
   - `python scripts/verify_m7.py`
   - `python scripts/verify_m6.py`
   - `python scripts/verify_m5.py`
   - `python scripts/verify_m4.py`
   - `python scripts/audit.py`
   All must pass with 0 errors.

7. Deliverables:
   - Generate `report.md` in your working directory.
   - Generate 5-component `handoff.md` (Observation, Logic Chain, Caveats, Conclusion, Verification Method) in your working directory.
   - Send completion message to parent orchestrator with test results and artifact paths.

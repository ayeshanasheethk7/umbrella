## 2026-11-03T09:56:09Z

You are worker_m10_rem, the specialist remediation implementation worker for Milestone M10 (Granular 28-Point System Audit & Final Remediation).

Working Directory: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m10_rem
Original Request File: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
Parent: teamwork_orchestrator (Conversation ID: 9d9ee7a0-eeb7-4828-8075-796204188707)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY FIRST STEP:
Read c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md before doing anything else.

CONTEXT & INPUT ARTIFACTS:
1. c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m10_rem\DISPATCH.md
2. Explorer M10-1: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m10_1\handoff.md and proposed_actions.patch
3. Explorer M10-2: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m10_2\handoff.md and report.md
4. Explorer M10-3: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m10_3\handoff.md and report.md

CONCRETE PUNCHLIST TO IMPLEMENT:
1. Fix `src/app/portal/doctor/actions.ts`:
   Lines 91, 92, and 100 contain literal `%%` placeholder syntax. Apply the fix from `explorer_m10_1/proposed_actions.patch` so they use `%${cls.sanitized}%`:
   - Line 91: `qp().ilike('accounts.contact_phone', \`%\${cls.sanitized}%\`).limit(20)`
   - Line 92: `qp().ilike('emergency_contact_phone', \`%\${cls.sanitized}%\`).limit(20)`
   - Line 100: `res = await qp().ilike('accounts.full_name', \`%\${cls.sanitized}%\`).limit(20)`
2. Fix `src/app/layout.tsx`:
   Line 184: Change `<main id="main-content" className="flex-1">{children}</main>` to `<div id="main-content" className="flex-1">{children}</div>` to eliminate invalid nested `<main>` landmarks while retaining all accessibility and styling attributes.
3. Fix `src/components/patient/baseline-editor.tsx`:
   Lines 209 and 269: Expand the touch target of the condition chip and allergy chip remove buttons to meet the 44px minimum requirement (`min-h-[44px] min-w-[44px]` or wrap with an accessible 44px button/padding).
4. Fix `src/app/page.tsx`:
   Line 91: Replace `text-text-secondary` with `text-text-body-secondary` so that the 11px disclaimer text meets WCAG AA contrast (5.0:1 on white).
5. Create Next.js loading skeletons:
   - `src/app/portal/patient/loading.tsx`
   - `src/app/portal/doctor/loading.tsx`
   Clean, elegant loading states adhering to the Apple-inspired design tokens in Rule 01 (under 12,000 characters each).
6. Modularize `src/app/(auth)/signup/page.tsx`:
   The file is 20,200 characters, exceeding the 12k budget. Split into clean subcomponents:
   - `src/components/auth/patient-signup-form.tsx`
   - `src/components/auth/doctor-signup-form.tsx`
   And keep `src/app/(auth)/signup/page.tsx` as a clean coordinator/page component.
   Ensure EVERY resulting file is strictly < 12,000 characters and retains all zero-mock auth (`supabase.auth.signUp`), strict Zod validation, and error handling.
7. Create root `README.md`:
   Comprehensive project documentation (< 12,000 characters) detailing Umbrella's three surfaces (Patient Portal, Doctor Portal, Public Emergency Triage `/emergency/[token]`), tech stack, security invariants N1-N10, RLS policies, directory layout, verification scripts, and quick start guide.
8. Update `docs/PROGRESS.md`:
   Update the progress and status tables to record Phases 0 through 10 as completed with full verification details.

VERIFICATION COMMANDS TO RUN:
In PowerShell:
- `python scripts/verify_m4.py` (51/51 pass)
- `python scripts/verify_m5.py` (74/74 pass)
- `python scripts/verify_m6.py` (38/38 pass)
- `python scripts/verify_m7.py` (42/42 pass)
- `python scripts/verify_m8.py` (43/43 pass)
- `python scripts/verify_m9.py` (52/52 pass)
- `python scripts/adversarial_challenge_m9.py` (14/14 pass)
- `python scripts/audit.py` (budget and rules pass)
- Scan all files in `src/` to confirm 100% are strictly < 12,000 characters:
  `python -c "import os; over = [f'{os.path.join(r, f)}: {len(open(os.path.join(r, f), errors=\'ignore\').read())}' for r, _, fs in os.walk('src') for f in fs if len(open(os.path.join(r, f), errors=\'ignore\').read()) >= 12000]; print('Over 12k:', over); assert len(over) == 0"`

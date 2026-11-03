## 2026-11-02T01:16:33Z
You are worker_m7, the Emergency Route Implementation Worker for Milestone M7 of the Umbrella Emergency Medical ID Platform.

Your working directory is: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m7

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY INPUTS:
1. Master user request: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md (READ THIS FIRST).
2. Project specification & architecture: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
3. Architectural Decisions: c:\Users\DELL\ayesha_pro\medi_qr\docs\DECISIONS.md (D9, D10, D12, D13, D15)
4. Design System & Spacing: c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\01-design-system.md
5. Security Rules: c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\02-security-privacy.md
6. Explorer Reports:
   - c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m7_1\report.md (UX, Zero Motion, 56px Call Bar, Card Layout)
   - c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m7_2\report.md (RPC Integration, Anon Client, Privacy Barrier, Zod Schema)
   - c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m7_3\report.md (Security Headers, 41-Point Test Suite Blueprint)

YOUR EXCLUSIVE WRITE OWNERSHIP:
You have exclusive write access to:
1. `src/lib/supabase/anon.ts` (Cookie-less anonymous client using only `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`, zero cookies, zero `service_role`).
2. `src/lib/schemas.ts` (Add `emergencyTriageSchema` concisely, ensuring total file length remains strictly < 12,000 characters; current size is 10,758 chars).
3. `src/app/emergency/[token]/page.tsx` (Server Component: force-dynamic, revalidate = 0, noindex metadata, pre-query UUID validation via `uuidSchema`, fetch strictly via `get_emergency_triage_by_token`, opaque notFound(), zero framer-motion).
4. `src/app/emergency/[token]/not-found.tsx` (Opaque generic 404 UI with zero diagnostic leaks, and life-safety 56px emergency call button for 911 / emergency services).
5. `src/components/emergency/emergency-triage-view.tsx` (Responsive container for triage cards, 375x667 and 1280x800, light theme maximum contrast, zero framer-motion).
6. `src/components/emergency/sticky-emergency-call-bar.tsx` (Fixed/sticky bottom bar, min-h-[56px] min-w-[56px], sanitized `tel:` link, CSS active press feedback :active:scale-[0.98]).
7. `src/components/emergency/triage-allergies-alert.tsx` (Critical allergy alert banner using design tokens).
8. `src/components/emergency/triage-vitals-card.tsx` (Patient Code, Full Name, Age, BloodGroupPill, Verification Badge).
9. `src/components/emergency/triage-clinical-history.tsx` (Medical Conditions, Current Medications, Previous Surgeries, Attestation timestamp).
10. `src/components/emergency/triage-escalation-footer.tsx` (Doctor Portal escalation link to `/portal/doctor?patient_token=<uuid>` per DECISIONS D15).
11. `scripts/verify_m7.py` (Full 41-point verification suite as designed in explorer_m7_3 report).

NON-NEGOTIABLE REQUIREMENTS:
1. **N1 Zero Exposure**: `residential_address` and `spouse_dependents` must NEVER appear in any emergency route file, HTML, or JSON.
2. **N4 Anon Key Only**: Zero `service_role` usage.
3. **N8 & D13 Zero Framer-Motion**: Zero `framer-motion` imports in `/emergency/` or `src/components/emergency/*`. Do NOT import `@/components/ui/button`. Use native HTML `<a>` and `<button>` with CSS-only active states (`active:scale-[0.98]`).
4. **N10 Strict Typing**: Zero `any`, zero `@ts-ignore`.
5. **D12 56px Emergency Call Target**: Must have `min-h-[56px] min-w-[56px]` on the sticky emergency call button.
6. **12k Rule**: EVERY single file must be strictly < 12,000 characters.

VERIFICATION COMMANDS TO RUN:
- `python scripts/verify_m7.py` (Must pass all 41 checks with code 0)
- `npm run typecheck` (`tsc --noEmit`)
- `python scripts/audit.py` (Must pass with 0 files >= 12,000 characters)

DELIVERABLE:
Write your complete handoff report to:
`c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m7\handoff.md`
Include commands run, test outputs, file list with character counts, and verification status.
When done, send a message to parent with your summary and report path.

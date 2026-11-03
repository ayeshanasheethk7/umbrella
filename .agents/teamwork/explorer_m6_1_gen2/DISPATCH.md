## 2026-11-01T23:32:34Z
You are Explorer M6-1 (Doctor UI & Safety Banner Explorer).
Your Working Directory: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_1_gen2
Your Parent: Project Orchestrator (Conversation ID: a0698e01-4167-4648-9a8b-05be5311997c)

MANDATORY INPUTS - Read these first:
- Original Request: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
- Project Scope: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
- Full Spec: c:\Users\DELL\ayesha_pro\medi_qr\docs\SPEC.md (Section 5.2 Doctor Portal, Section 7 Folder Structure)
- Spec Decisions: c:\Users\DELL\ayesha_pro\medi_qr\docs\DECISIONS.md (D1, D3, D7, D14)
- Design Tokens: c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\01-design-system.md
- Security Rules: c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\02-security-privacy.md
- Patient Portal Implementation (reference for UI patterns): c:\Users\DELL\ayesha_pro\medi_qr\src\app\portal\patient and c:\Users\DELL\ayesha_pro\medi_qr\src\components\patient

YOUR MISSION:
Perform a deep-dive exploration and architectural design of the Doctor Portal UI surface (`/portal/doctor`) and produce a comprehensive technical blueprint for the Worker.

Key Areas to Investigate & Specify:
1. Gating & Pending UX (DECISIONS D1):
   - Approved doctor gets the clinical workspace.
   - Pending doctor (`doctor_status === 'PENDING'`) gets the pending approval screen (clear banner: "Account Pending Approval - Our team verifies medical credentials within 24 hours. While pending, patient records cannot be accessed.").
2. Multi-Modal Patient Search (DECISIONS D14):
   - Search bar supporting:
     * Patient Code: `UMB-XXXXXX`
     * DOB (`YYYY-MM-DD`) + Full Name / Phone
     * Partial phone number / emergency contact lookup
   - Empty, loading, and not-found states.
   - List of matching patients with basic triage indicators.
3. Persistent Read-Only Safety Banner (NON-NEGOTIABLE N2):
   - MUST be visible at all times when viewing or editing a patient's clinical records.
   - Shows: Patient Name, Age (calculated from DOB), Blood Group, Emergency Contact Phone & Name.
   - Must use `sticky top-0 z-30` or equivalent fixed header so it CANNOT be scrolled out of view while modifying clinical data.
   - Prominent, high-contrast, read-only styling per `01-design-system.md`.
4. Clinical Record Editor & Verification (DECISIONS D3, D7):
   - Chronic conditions, current medications, allergies (with severity badges: mild/moderate/severe), past surgeries, implants/devices, clinical notes.
   - Trigger stamp / doctor verification badge: shows "Verified by Dr. [Name]" + timestamp if verified, or "Self-Reported Baseline (Unverified)" if submitted by patient.
   - Doctor verification button: stamps `verified_by_doctor_id` and `verified_at` upon saving.
5. Appointment Management:
   - Doctor's upcoming and past appointments.
   - Schedule new appointment modal / drawer (patient selector, date/time, notes).
   - Status updates: `SCHEDULED`, `COMPLETED`, `CANCELLED`.
6. Responsive Design & Accessibility:
   - 375x667 (mobile) and 1280x800 (desktop) layouts.
   - Minimum 44px touch targets.
   - Shared motion `appleSpring` (from `src/lib/motion.ts`), prefers-reduced-motion respected.
   - Zero raw hex tokens (use Tailwind tokens).

Deliverables:
- Write your complete architectural report to `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_1_gen2\report.md`.
- Write your 5-component handoff report (Observation, Logic Chain, Caveats, Conclusion, Verification Method) to `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m6_1_gen2\handoff.md`.
- Maintain `progress.md` in your working directory.
- Send a completion message via `send_message` to your parent orchestrator (`a0698e01-4167-4648-9a8b-05be5311997c`).
Do NOT implement code yourself — produce verified specifications and blueprints.

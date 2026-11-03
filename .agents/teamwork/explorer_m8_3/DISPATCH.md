# DISPATCH: Explorer M8-3 (Token Rotation RPC & Verification Suite Design)

**Working Directory**: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m8_3
**Original Request File**: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
**Scope Document**: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
**Skill Reference**: c:\Users\DELL\ayesha_pro\medi_qr\.agents\skills\umbrella-qr-card\SKILL.md

## 2026-11-02T12:16:31Z
[Message from 9a03a7b4-6eb6-4d41-bad3-e7c232a57fe2 priority=MESSAGE_PRIORITY_HIGH]
Objective:
Investigate token rotation workflow, confirmation modal, and design the Milestone M8 automated verification test harness:
1. Token Rotation Workflow:
   - RPC: `public.regenerate_qr_token()` in `supabase/migrations/0001_umbrella_schema.sql:151-167`.
   - Server Action: `rotateQrTokenAction()` in `src/app/portal/patient/actions.ts`.
   - Security: Must identify caller via `supabase.auth.getUser()` (N3), never accept client-passed IDs.
   - Confirmation Modal: User confirmation required ("Your current QR code will stop working immediately. Printed or saved copies will show 'not found'. Continue?").
   - State Update: On success, updates local `qrToken` state, regenerates QR, shows confirmation message reminding user to reprint/re-download.
2. Preview Public Emergency View:
   - Link / button opening `/emergency/${qrToken}` in a new tab with `rel="noopener noreferrer"`.
3. Design Milestone M8 Verification Suite (`scripts/verify_m8.py`):
   - Design a 35+ point automated verification test harness checking:
     - Component structure in `src/components/qr/` (`qr-studio.tsx`, `card-preview.tsx`).
     - SVG rendering parameters (`QRCodeSVG`, level Q, fg/bg colors, min 224px).
     - PNG export pipeline and canvas dimensions (1080x1080).
     - PDF CR80 export (jspdf, [85.6, 54] mm, 2 pages, front/back).
     - Invariant N1: Zero exposure of residential_address or spouse_dependents in PDF/PNG exports.
     - Invariant N4: Zero service_role occurrences.
     - Invariant N6: Client-side origin computation inside useEffect.
     - Token rotation action calling RPC `regenerate_qr_token`.
     - Non-blocking non-production warning (D12).
     - Multi-milestone regression: `verify_m7.py`, `verify_m6.py`, `verify_m5.py`, `verify_m4.py`, `audit.py`.
   - Ensure `scripts/verify_m8.py` character count remains strictly under 12,000 characters.

Deliverables:
- Write detailed technical findings to `report.md`.
- Write 5-component handoff to `handoff.md`.
- Send completion message to parent orchestrator.

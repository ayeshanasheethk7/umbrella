# DISPATCH: Explorer M8-1 (QR Studio Architecture & UI Layout)

**Working Directory**: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m8_1
**Original Request File**: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
**Scope Document**: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
**Skill Reference**: c:\Users\DELL\ayesha_pro\medi_qr\.agents\skills\umbrella-qr-card\SKILL.md

## Exploration Objectives
Investigate codebase and define technical specifications for Milestone M8 QR Studio components and layout:
1. Code Layout in `src/components/qr/`:
   - Inspect existing `src/components/patient/emergency-qr-card.tsx` and design modular QR Studio architecture in `src/components/qr/`:
     - `src/components/qr/qr-studio.tsx`: Main studio surface containing QR display, actions, and card preview.
     - `src/components/qr/card-preview.tsx`: Live interactive CR80 card preview (front and back toggle) matching physical print layout.
     - Integration into `src/app/portal/patient/page.tsx`.
2. URL Computation & Invariant N6:
   - Verify `buildEmergencyUrl(origin, token)` in `src/lib/utils.ts`.
   - Verify client-side calculation inside `useEffect` after mount to prevent hydration mismatch.
   - Verify non-blocking warning for localhost / non-production Vercel domains (DECISIONS D12).
3. Rendering Specifications (`qrcode.react`):
   - `QRCodeSVG` props: `level="Q"`, `fgColor="#000000"`, `bgColor="#ffffff"`, margin, min 224px.
4. Character Budget:
   - Ensure all planned files remain strictly < 12,000 characters.

## Deliverables
- Write detailed findings to `report.md`.
- Write 5-component handoff to `handoff.md` (Observation, Logic Chain, Caveats, Conclusion, Verification Method).
- Send completion message to parent orchestrator.


## 2026-11-02T12:16:12Z
Sender: 9a03a7b4-6eb6-4d41-bad3-e7c232a57fe2
Content:
You are explorer_m8_1, the QR Studio Architecture & UI Layout Explorer for Milestone M8 on the Umbrella Emergency Medical ID platform.

Working Directory: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m8_1
Original Request File: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
Master Project Plan: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
Dispatch Instructions: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m8_1\DISPATCH.md
Domain Skill Reference: c:\Users\DELL\ayesha_pro\medi_qr\.agents\skills\umbrella-qr-card\SKILL.md
Parent Orchestrator: 9a03a7b4-6eb6-4d41-bad3-e7c232a57fe2

Objective:
Investigate codebase and define technical specifications for Milestone M8 QR Studio components and layout:
1. Modular QR Studio in `src/components/qr/`:
   - Inspect existing `src/components/patient/emergency-qr-card.tsx` and design clean modular architecture in `src/components/qr/`:
     - `src/components/qr/qr-studio.tsx`: Main studio surface containing QR display, actions, and card preview.
     - `src/components/qr/card-preview.tsx`: Live interactive CR80 card preview (front and back toggle) matching physical print layout.
     - Integration into `src/app/portal/patient/page.tsx` and backward-compatible re-export from `src/components/patient/emergency-qr-card.tsx`.
2. URL Computation & Invariant N6:
   - Check `buildEmergencyUrl(origin, token)` in `src/lib/utils.ts`.
   - Verify client-side calculation inside `useEffect` after mount to prevent hydration mismatch; same-size skeleton until ready.
   - Non-blocking warning for localhost / non-production Vercel domains (DECISIONS D12).
3. Rendering Specifications (`qrcode.react`):
   - `QRCodeSVG` props: `level="Q"`, `fgColor="#000000"`, `bgColor="#ffffff"`, margin, min 224px box on mobile.
4. Character Budget:
   - Ensure all planned files remain strictly < 12,000 characters.

Deliverables:
- Write detailed technical findings to `report.md`.
- Write 5-component handoff to `handoff.md` (Observation, Logic Chain, Caveats, Conclusion, Verification Method).
- Send completion message to parent orchestrator.

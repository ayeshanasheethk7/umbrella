## 2026-11-02T12:26:36Z

# DISPATCH: Worker M8 (QR Studio & Printable ID Card Export)

**Working Directory**: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m8
**Original Request File**: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
**Scope Document**: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
**Domain Skill Reference**: c:\Users\DELL\ayesha_pro\medi_qr\.agents\skills\umbrella-qr-card\SKILL.md
**Explorer Blueprints**:
- `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m8_1\report.md`
- `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m8_2\report.md`
- `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m8_3\report.md`

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Mandatory Rules
1. First read ORIGINAL_REQUEST.md, PROJECT.md, and DISPATCH.md before touching any code.
2. Every file created or edited must remain strictly under 12,000 characters.
3. Invariant N4 is strictly zero tolerance: the string `service_role` must NEVER appear in code, comments, tests, configs, or logs.
4. Non-negotiables N1-N10 must remain inviolate (zero mock auth, zero any types, N1 strict privacy: zero residential_address or spouse_dependents).

## Implementation Deliverables

### 1. `src/components/qr/card-preview.tsx` (New Component)
- Create interactive CR80 card preview matching ISO/IEC 7810 ID-1 standard ([85.6, 54] mm, aspect ratio 1.585:1).
- Interactive Front / Back toggle (`[ Front ]` / `[ Back ]`).
- Front view: Red header stripe (`#d70015`), "EMERGENCY MEDICAL ID" & "UMBRELLA TRIAGE PASS", bold patient name, patient code, blood group pill/box, live `QRCodeSVG` (level Q, ~32mm scale), caption "Scan for medical info. No login needed."
- Back view: Black header stripe ("IN CASE OF EMERGENCY"), primary emergency contact name/relation/phone, direct triage URL in Courier monospace font, certified privacy pass badge.
- Invariant N1: Strictly NEVER display residential_address or spouse_dependents.
- Strict TypeScript, zero `any`, strictly < 12,000 characters.

### 2. `src/components/qr/qr-studio.tsx` (New Component)
- Main QR Studio surface mounted on patient portal.
- Tab controls: "QR Code" view and "Physical Card Preview" view.
- In QR Code view:
  - `QRCodeSVG` viewport with minimum 224px on mobile (`w-[224px] h-[224px] sm:w-[240px] sm:h-[240px]`, `size={224}`, `level="Q"`, `fgColor="#000000"`, `bgColor="#ffffff"`, `marginSize={4}`).
  - Client-side origin computation in `useEffect` (Invariant N6) with animated same-size skeleton until mounted.
  - Non-blocking amber warning for localhost / non-production Vercel domains (DECISIONS D12): "This QR points to <origin>. Cards printed here only work while that site is online."
  - Action buttons: "Download PNG (Wallet/Lock Screen)" calling `exportQrPng`, "Print ID Card (PDF)" calling `exportCr80Pdf`.
  - Preview Public Emergency View link opening `/emergency/${qrToken}` in new tab (`target="_blank"`, `rel="noopener noreferrer"`, `min-h-[44px]`).
  - "Regenerate Emergency QR Code" button opening confirmation modal:
    - Copy: "Your current QR code will stop working immediately. Printed or saved copies will show 'not found'. Continue?"
    - Calls `rotateQrTokenAction()` from `@/app/portal/patient/actions`.
    - Updates local `qrToken` state, redraws QR code, displays success banner reminding user to reprint/re-download.
- Strict TypeScript, zero `any`, strictly < 12,000 characters.

### 3. `src/components/patient/emergency-qr-card.tsx` (Backward-Compatibility Facade)
- Update to re-export/wrap `QrStudio` from `@/components/qr/qr-studio` while retaining required compatibility string markers for `verify_m5.py`.
- Strictly < 12,000 characters.

### 4. `src/app/portal/patient/page.tsx`
- Ensure seamless rendering of `QrStudio` / `EmergencyQrCard`.

### 5. `src/lib/qr-export.ts` Hardening
- Apply 4 explorer-recommended hardening refinements:
  - Long patient name wrapping with `maxWidth: 44` on front card to prevent QR collision.
  - Long URL wrapping with `maxWidth: 77.6` on back card.
  - Emergency contact relation formatting guard (omit empty parentheses if relation is blank).
  - High-DPI canvas rasterization.
- Strictly < 12,000 characters.

### 6. `scripts/verify_m8.py` (New Automated Verification Suite)
- Author comprehensive 40+ point automated test harness covering:
  - Component architecture in `src/components/qr/` (`qr-studio.tsx`, `card-preview.tsx`).
  - Viewport dimensions (>= 224px) and SVG parameters (`level="Q"`, black on white).
  - `buildEmergencyUrl` utility and Invariant N6 client-side origin hydration.
  - Non-blocking D12 warning.
  - PNG export (1080x1080, centered QR, filenames).
  - CR80 PDF export (jspdf, [85.6, 54] mm, 2 pages, front/back).
  - Invariant N1: Zero residential_address or spouse_dependents in exports or UI.
  - Invariant N4: Zero service_role leaks repo-wide.
  - Invariant N10: Zero `any` types, zero `@ts-ignore`.
  - Token rotation RPC (`regenerate_qr_token`), server action, confirmation modal copy.
  - Multi-milestone regressions: `verify_m7.py`, `verify_m6.py`, `verify_m5.py`, `verify_m4.py`, and `audit.py`.
- Strictly < 12,000 characters.

### 7. Verification Execution
Run and verify exit code 0:
- `python scripts/verify_m8.py` (must pass 100%)
- `python scripts/verify_m7.py` (42/42 PASS)
- `python scripts/verify_m6.py` (38/38 PASS)
- `python scripts/verify_m5.py` (74/74 PASS)
- `python scripts/verify_m4.py` (51/51 PASS)
- `python scripts/audit.py` (all files < 12,000 characters)

### 8. Deliverables
- Write detailed implementation report to `report.md`.
- Write 5-component handoff report to `handoff.md` (Observation, Logic Chain, Caveats, Conclusion, Verification Method).
- Send completion message to parent orchestrator.

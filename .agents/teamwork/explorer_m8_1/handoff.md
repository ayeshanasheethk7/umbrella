# Handoff Report: Milestone M8 QR Studio Architecture & UI Layout

**Agent**: `explorer_m8_1`  
**Working Directory**: `.agents/teamwork/explorer_m8_1`  
**Recipient**: `orchestrator` (`9a03a7b4-6eb6-4d41-bad3-e7c232a57fe2`)  
**Milestone**: M8 (QR Studio & Printable ID Card Export)  
**Type**: Hard Handoff (Investigation & Architecture Specification Complete)  

---

## 1. Observation

1. **Existing Monolith in `src/components/patient/emergency-qr-card.tsx`**:
   - Total lines: 309. Total size: 10,988 characters (`view_file` at `emergency-qr-card.tsx:1-309`).
   - Located in `src/components/patient/` rather than the canonical domain directory `src/components/qr/` specified in `SPEC.md:113` and `PROJECT.md:76`.
   - Size is 91.6% of the 12,000-character budget, preventing the addition of an interactive CR80 card preview without exceeding the limit.
   - The on-screen QR viewport is currently sized at `180px` (`emergency-qr-card.tsx:158,163`):
     ```tsx
     <div className="... min-w-[180px] min-h-[180px]">
       <QRCodeSVG value={emergencyUrl} size={180} level="Q" ... />
     </div>
     ```
     This is smaller than the 224px minimum required by domain skill `umbrella-qr-card/SKILL.md:13` ("Minimum on-screen size 224px on phones; keep a 1:1 box").

2. **Absence of Domain Directory `src/components/qr/`**:
   - `find_by_name` in `src/components/qr/` returned: `search directory c:\Users\DELL\ayesha_pro\medi_qr\src\components\qr does not exist`.

3. **URL Computation & Invariant N6 Functionality**:
   - `src/lib/utils.ts:92-96`:
     ```typescript
     export function buildEmergencyUrl(origin: string, qrToken: string): string {
       const cleanOrigin = (origin || '').replace(/\/+$/, '');
       const cleanToken = (qrToken || '').trim();
       return `${cleanOrigin}/emergency/${cleanToken}`;
     }
     ```
   - Pure string-building function correctly strips trailing slashes and trims token whitespace.
   - Hydration mismatch prevention is achieved via `useEffect` lifecycle setting `mounted` and `origin` from `window.location.origin` client-side only (`emergency-qr-card.tsx:53-57`).

4. **Non-Blocking Non-Production Warning (DECISIONS D12)**:
   - Evaluated at `emergency-qr-card.tsx:62-66`:
     ```typescript
     const isNonProd =
       mounted &&
       (origin.includes('localhost') ||
         origin.includes('127.0.0.1') ||
         (origin.includes('.vercel.app') && !origin.includes('production')));
     ```
   - Renders a calm amber warning without blocking download or print actions (`emergency-qr-card.tsx:180-191`).

5. **CR80 Physical Card Specification**:
   - In `umbrella-qr-card/SKILL.md:21-27` and `src/lib/qr-export.ts:104`:
     - Dimensions: `[85.6, 54] mm` landscape (aspect ratio ~1.585:1).
     - Page 1 Front: Red header stripe, patient name, patient code, blood group box, QR code (32mm), scan caption.
     - Page 2 Back: Black header stripe, emergency contact name/relation/phone, direct triage URL in monospace/courier, certified privacy pass caption.
     - Invariant N1: Strictly omits residential address and spouse/dependents.

6. **Regression Harness Dependencies**:
   - `scripts/verify_m5.py:161-184` reads `src/components/patient/emergency-qr-card.tsx` directly and inspects for specific string tokens (`<QRCodeSVG`, `level="Q"`, `buildEmergencyUrl`, `Testing environment`, `handleExportPdf`, `exportCr80Pdf`, `handleExportPng`, `exportQrPng`, `Modal`).
   - All regression suites currently pass:
     - `verify_m4.py`: 51/51 PASS
     - `verify_m5.py`: 74/74 PASS
     - `verify_m6.py`: 38/38 PASS
     - `verify_m7.py`: 42/42 PASS
     - `audit.py`: All target files < 12,000 characters PASS

---

## 2. Logic Chain

1. **Need for Modular Architecture**:
   From Observation 1 and 2, adding the interactive CR80 card preview to the existing 10,988-character `emergency-qr-card.tsx` would immediately exceed the 12,000-character ceiling, violating Rule 12k. Decomposing the module into `src/components/qr/qr-studio.tsx` (~9,200 chars) and `src/components/qr/card-preview.tsx` (~5,300 chars) fulfills SPEC Section 7 while maintaining ample headroom (23% to 55%) under the 12k limit.

2. **CR80 Card Preview Fidelity**:
   From Observation 5, physical cards exported by `src/lib/qr-export.ts` contain distinct Front (red header, patient identity, blood group, QR code) and Back (black header, primary emergency contact, direct triage URL, privacy badge) layouts. Implementing `CardPreview` with an interactive side-toggle (`[ Front ]` / `[ Back ]`) and the exact `aspect-[85.6/54]` ratio delivers true WYSIWYG parity between on-screen preview and physical output.

3. **QR Viewport Sizing Compliance**:
   From Observation 1, the current `size={180}` viewport fails the domain skill specification of a minimum 224px viewport on mobile. Updating the viewport in `qr-studio.tsx` to `w-[224px] h-[224px] sm:w-[240px] sm:h-[240px]` with `size={224}` brings the component into full compliance with `umbrella-qr-card` and optimizes mobile camera scan times.

4. **Preserving Invariant N6 & D12**:
   From Observation 3 and 4, client-computed `origin` within `useEffect` combined with a matching `224px x 224px` animated skeleton eliminates any possibility of SSR hydration mismatch. DECISIONS D12 non-production amber warning remains non-blocking to all exports.

5. **Ensuring Zero Test Regressions**:
   From Observation 6, `verify_m5.py` and `verify_m7.py` require `src/components/patient/emergency-qr-card.tsx` to exist and provide QR Studio capabilities. Refactoring `emergency-qr-card.tsx` as a backward-compatible facade re-exporting `QrStudio`, combined with updating `verify_m5.py` to inspect both files, guarantees 100% green test passes across all historical milestones.

---

## 3. Caveats

- **Canvas Rendering in Headless Test Environments**: `exportQrPng` and `exportCr80Pdf` rely on browser DOM APIs (`document.createElement('canvas')`, `XMLSerializer`, `URL.createObjectURL`). In headless CI test environments without a DOM (e.g. pure Node.js Vitest), these functions must be tested with DOM polyfills (e.g. `jsdom`) or through Playwright browser journeys (Milestone M9).
- **Installed `qrcode.react` Version**: The repository uses `qrcode.react@^4.0.1`. Prop names are confirmed (`value`, `size`, `level`, `marginSize`, `fgColor`, `bgColor`). Older v3 prop names (such as `includeMargin`) should not be used.
- **No Direct Code Changes Applied**: In strict accordance with explorer role constraints, no production files have been modified. Complete replacement blueprints and implementation specifications are delivered in `report.md`.

---

## 4. Conclusion

The technical architecture for Milestone M8 QR Studio is fully defined, validated, and ready for worker implementation:
1. Create domain directory `src/components/qr/`.
2. Implement `src/components/qr/card-preview.tsx` (CR80 aspect ratio, Front/Back toggle, live QR, zero address/dependents N1, < 6,000 chars).
3. Implement `src/components/qr/qr-studio.tsx` (Level Q, 224px mobile viewport, tabs, export actions, token rotation modal, D12 amber warning, < 10,000 chars).
4. Update `src/components/patient/emergency-qr-card.tsx` to re-export/facade `QrStudio` (< 500 chars).
5. Update `src/app/portal/patient/page.tsx` to import and render `QrStudio`.
6. Update `scripts/verify_m5.py` to inspect both QR files, guaranteeing zero regressions.
7. Create `scripts/verify_m8.py` to certify all 45 Milestone M8 invariants.

---

## 5. Verification Method

To independently verify the architecture and test compatibility:

1. **Verify Existing Suites Pass (Baseline Check)**:
   ```bash
   python scripts/verify_m4.py
   python scripts/verify_m5.py
   python scripts/verify_m6.py
   python scripts/verify_m7.py
   python scripts/audit.py
   ```
   *Expected*: All test suites pass 100% with exit code 0.

2. **Verify Character Count Limits**:
   Review proposed file sizes in `report.md:Section 5`. All files are strictly < 12,000 characters.

3. **Verify Implementation Plan**:
   Inspect `report.md` for exact component props, Tailwind CSS classes, ARIA accessibility attributes, and Invariant N1 / N6 contracts.

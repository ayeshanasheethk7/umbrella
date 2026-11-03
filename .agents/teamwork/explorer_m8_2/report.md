# Technical Investigation Report: Milestone M8 Export Engines (PNG & 300 DPI CR80 PDF)

**Agent**: `explorer_m8_2`  
**Working Directory**: `.agents/teamwork/explorer_m8_2/`  
**Subject**: PNG & 300 DPI CR80 PDF Export Engine Architecture, Visual Compliance, Invariant N1 & Character Budget  
**Date**: 2026-11-02  
**Target Code**: `src/lib/qr-export.ts`  

---

## 1. Executive Summary

Milestone M8 establishes the **QR Studio and Export Engines** for the Umbrella Emergency Medical ID platform. This report provides a comprehensive, read-only architectural and technical investigation of the export engines residing in `src/lib/qr-export.ts`.

Key findings of this investigation:
1. **1080x1080 PNG Export (`exportQrPng`)**: Fully conforms to the visual specification and `umbrella-qr-card` skill. Employs an offscreen 1080x1080 HTML5 canvas, pure `#ffffff` background, centered QR code spanning 700px (Y: 140–840px), `--clinical-critical-text` (`#d70015`) header banner, prominent patient metadata footer, and an asynchronous `XMLSerializer` -> `Blob` -> `Image` -> `toBlob` pipeline with explicit memory cleanup.
2. **300 DPI CR80 PDF Card Export (`exportCr80Pdf`)**: Implements standard ISO/IEC 7810 ID-1 (CR80) card dimensions (`[85.6, 54]` mm) in landscape orientation across 2 distinct pages (Front & Back). The Front page incorporates a 8mm red emergency header, bold patient name, patient code, a dedicated 26x12mm blood group box, a 32x32mm QR code at 317.5+ DPI, and roadside scan guidance. The Back page provides a black emergency header, primary emergency contact details with prominent blue call digits (`#0071e3`), and a Courier monospace emergency URL.
3. **Bundle Performance (D13 & SPEC Check 6)**: `jsPDF` is dynamically loaded via `await import('jspdf')`, completely isolating the ~350KB library from initial portal bundles and ensuring zero footprint on `/emergency/[token]`.
4. **Invariant N1 Compliance**: Strictly verified. `residential_address` and `spouse_dependents` are completely omitted from the parameter interface `QrExportParams`, SVG serialization, canvas drawing, and PDF page generation.
5. **Character Budget**: `src/lib/qr-export.ts` currently measures **7,020 characters** (226 lines), comfortably below the 12,000-character ceiling (58.5% capacity, 4,980 characters headroom).

---

## 2. Architecture & File Inventory

### 2.1 Component & Library Placement
- **Source Module**: `src/lib/qr-export.ts` (7,020 characters)
- **Primary Dependencies**:
  - `jspdf`: `^2.5.2` (dynamic client import)
  - `qrcode.react`: `^4.0.1` (`QRCodeSVG` element passed from UI)
  - Database Types: `BloodGroup` imported from `@/lib/supabase/types`
- **Consumer Components**:
  - `src/components/patient/emergency-qr-card.tsx` (Current consumer)
  - `src/components/qr/qr-studio.tsx` (Target refactored consumer planned in M8)
- **URL Builder Utility**:
  - `buildEmergencyUrl(origin, qrToken)` in `src/lib/utils.ts`

### 2.2 Parameter Contract (`QrExportParams`)

The interface in `src/lib/qr-export.ts:3-12` is defined as:

```typescript
export interface QrExportParams {
  svgElement: SVGSVGElement;
  patientCode: string;
  patientName: string;
  bloodGroup: BloodGroup;
  emergencyContactName?: string;
  emergencyContactPhone?: string;
  emergencyContactRelation?: string;
  emergencyUrl?: string;
}
```

**Architectural Privacy Guarantee**:
Notice that `QrExportParams` does NOT accept `residential_address` or `spouse_dependents`. The TypeScript interface enforces Invariant N1 compile-time isolation: calling components cannot inadvertently pass protected home address or family data into the export engines.

---

## 3. Engine 1: 1080x1080 PNG Export Deep-Dive

### 3.1 Purpose & Use Case
The PNG export produces a high-definition 1080x1080 digital credential designed for:
- Smartphone lock screen wallpaper.
- Digital photo wallet / favorites gallery.
- Direct digital transmission to caregivers or family members.

### 3.2 Canvas Geometry & Layout Rhythm

```text
┌──────────────────────────────────────────────────────────────────┐ (0, 0)
│                                                                  │
│                     EMERGENCY MEDICAL ID                         │ (Y = 90)  [#d70015, 36px bold]
│                                                                  │
│                     ┌──────────────────────┐                     │ (Y = 140)
│                     │                      │                     │
│                     │                      │                     │
│                     │    QR CODE (SVG)     │                     │ (Size: 700x700px)
│                     │      (Centered)      │                     │ (X: 190 to 890px)
│                     │                      │                     │
│                     │                      │                     │
│                     └──────────────────────┘                     │ (Y = 840)
│                                                                  │
│                        Jane Doe                                  │ (Y = 900)  [#000000, 44px bold]
│                                                                  │
│           ID: UMB-492104  •  Blood Group: O+                     │ (Y = 960)  [#6e6e73, 32px mono]
│                                                                  │
│      Scan for vital clinical triage data • No login required     │ (Y = 1020) [#8a5200, 24px sans]
│                                                                  │
└──────────────────────────────────────────────────────────────────┘ (1080, 1080)
```

| Element | Position / Bounds | Dimensions | Typography / Styling | Design Token / Color |
|---|---|---|---|---|
| **Canvas** | (0, 0) to (1080, 1080) | 1080 × 1080 px | N/A | `#ffffff` (`rgb(255, 255, 255)`) |
| **Header Banner** | Baseline at Y = 90 | Center at X = 540 | `bold 36px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif` | `--clinical-critical-text` (`rgb(215, 0, 21)`) |
| **QR Code Image** | X = 190, Y = 140 | 700 × 700 px | Rasterized from SVG Blob | Black on white, Level Q |
| **Patient Name** | Baseline at Y = 900 | Center at X = 540 | `bold 44px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif` | `--text-primary` (`rgb(0, 0, 0)`) |
| **ID & Blood Group** | Baseline at Y = 960 | Center at X = 540 | `32px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace` | `--text-body-secondary` (`rgb(110, 110, 115)`) |
| **Scan Caption** | Baseline at Y = 1020 | Center at X = 540 | `24px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif` | `--clinical-pending-text` (`rgb(138, 82, 0)`) |

### 3.3 Serialization & Download Lifecycle
1. **SVG Extraction**: Extracts SVG XML using `new XMLSerializer().serializeToString(svgElement)`.
2. **Blob Creation**: Encapsulates data in `new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' })`.
3. **URL Generation**: Allocates in-memory object URL via `URL.createObjectURL(svgBlob)`.
4. **Image Preloading**: Instantiates `new Image()`, awaiting `img.onload` inside a promise.
5. **Canvas Rendering**: Draws background, text, and QR code to an offscreen `<canvas>` (`canvas.width = 1080`, `canvas.height = 1080`).
6. **PNG Blob Generation**: Invokes `canvas.toBlob(blob => ..., 'image/png')`.
7. **Automated Trigger**: Creates temporary `<a download="umbrella-emergency-id-${patientCode}.png">`, attaches to `document.body`, invokes `click()`, and detaches.
8. **Memory Hygiene**: Invokes `URL.revokeObjectURL(downloadUrl)` immediately after download, and wraps `URL.revokeObjectURL(svgUrl)` in the outer `finally` block to guarantee zero memory leaks.

---

## 4. Engine 2: 300 DPI CR80 PDF ID Card Deep-Dive

### 4.1 Physical Standards & Specifications
- **Format Standard**: ISO/IEC 7810 ID-1 (CR80) standard credit-card format.
- **Physical Dimensions**: 85.6 mm × 54.0 mm (3.370" × 2.126").
- **Target Print Resolution**: 300 DPI.
  - At 300 DPI, full bleed pixel dimension is $1011 \times 638$ px ($85.6 \times \frac{300}{25.4} \approx 1011$ px, $54.0 \times \frac{300}{25.4} \approx 638$ px).
- **Page Count**: Exactly 2 pages (Front & Back).
- **Driver**: `jsPDF` (`new jsPDF({ orientation: 'landscape', unit: 'mm', format: [85.6, 54] })`).

### 4.2 Architectural Assessment: Direct Vector jsPDF vs 1011x638 Canvas Rasterization

There are two potential technical implementations for generating the CR80 PDF:

| Characteristic | Direct Vector jsPDF (Current Implementation) | 1011x638 Canvas Rasterization |
|---|---|---|
| **Text Rendering** | Native PDF vector fonts (`helvetica`, `courier`) | Rasterized bitmap pixels |
| **Print Sharpness** | **Infinite / 1200+ DPI** (vector curves rendered by printer RIP) | Fixed 300 DPI (potential font edge antialiasing artifacts) |
| **PDF Text Selection** | **Yes** (first responders can select/copy phone & URL) | No (flat image) |
| **File Size** | **~25 KB** | ~400–600 KB |
| **QR Code Sharpness** | 317.5+ DPI (400px over 32mm) / 476 DPI (600px over 32mm) | 300 DPI |
| **Memory Consumption** | Low (draws vectors directly to PDF stream) | High (allocates multiple full 300 DPI offscreen canvases) |

**Conclusion**: The **Direct Vector jsPDF** approach implemented in `src/lib/qr-export.ts` is superior in print crispness, document accessibility, file transfer size, and runtime memory efficiency. The QR code image itself is rasterized at $\ge 317.5$ DPI ($400 \text{ px} / 1.26 \text{ in} = 317.5 \text{ DPI}$), exceeding the 300 DPI physical requirement.

### 4.3 Page 1: Front Side Layout Geometry

```text
┌──────────────────────────────────────────────────────────────────┐ (0, 0)
│ EMERGENCY MEDICAL ID                      UMBRELLA TRIAGE PASS   │ [Height: 8mm, Fill: #d70015]
├───────────────────────────────────┬──────────────────────────────┤ (Y = 8mm)
│                                   │                              │
│  Jane Doe                         │     ┌──────────────────┐     │
│  [11pt bold, Y=15mm]              │     │                  │     │
│                                   │     │     QR CODE      │     │
│  Patient Code: UMB-492104         │     │     (32x32mm)    │     │
│  [8pt, #6e6e73, Y=20mm]           │     │   (X:49.6, Y:11) │     │
│                                   │     │                  │     │
│  ┌─────────────────────────────┐  │     └──────────────────┘     │ (Y = 43mm)
│  │         BLOOD GROUP         │  │                              │
│  │             O+              │  │ First Responder Roadside Pass│ (Y = 46mm)
│  └─────────────────────────────┘  │                              │
│  [26x12mm Box, Border: #d70015]   │                              │
│                                   │                              │
│  Scan for medical info.           │                              │ (Y = 42mm)
│  No login needed.                 │                              │ (Y = 45mm)
└───────────────────────────────────┴──────────────────────────────┘ (85.6, 54.0) mm
```

#### Front Side Measurements & Coordinates
1. **Red Header Stripe**:
   - `doc.rect(0, 0, 85.6, 8, 'F')` with `doc.setFillColor(215, 0, 21)`.
   - Title Left: "EMERGENCY MEDICAL ID" at X = 4 mm, Y = 5.5 mm. Font: Helvetica Bold 8pt, White.
   - Title Right: "UMBRELLA TRIAGE PASS" at X = 81.6 mm, Y = 5.5 mm, right-aligned. Font: Helvetica Bold 7pt, White.
2. **Left Column (Patient Identity)**:
   - Margin: Left = 4 mm. Available width before QR = $49.6 - 4.0 = 45.6$ mm.
   - Patient Name: Y = 15 mm. Font: Helvetica Bold 11pt, Black.
   - Patient Code: Y = 20 mm. Font: Helvetica Normal 8pt, `#6e6e73` (`rgb(110, 110, 115)`).
3. **Blood Group Box**:
   - Bounds: X = 4 mm, Y = 24 mm, Width = 26 mm, Height = 12 mm, Radius = 1.5 mm.
   - Stroke: 0.4 mm red line (`doc.setDrawColor(215, 0, 21)`).
   - Label: "BLOOD GROUP" at X = 17 mm (centered in 26mm box), Y = 28 mm. Font: Helvetica Bold 6pt, Red.
   - Value: `bloodGroup` (e.g. "O+", "A-") at X = 17 mm, Y = 34 mm. Font: Helvetica Bold 12pt, Red.
4. **Scan Guidance Caption**:
   - Line 1: "Scan for medical info." at X = 4 mm, Y = 42 mm. Font: Helvetica Normal 6pt, `#6e6e73`.
   - Line 2: "No login needed." at X = 4 mm, Y = 45 mm. Font: Helvetica Normal 6pt, `#6e6e73`.
5. **Right Column (QR Scanner Target)**:
   - X position: 49.6 mm.
   - Y position: 11.0 mm.
   - Width / Height: 32.0 mm × 32.0 mm.
   - Right margin: $85.6 - (49.6 + 32.0) = 4.0$ mm (Symmetric 4mm margin on both edges).
   - Subtitle: "First Responder Roadside Pass" at X = 65.6 mm (exact QR center), Y = 46 mm. Font: Helvetica 5pt, `#969696`.

---

### 4.4 Page 2: Back Side Layout Geometry

```text
┌──────────────────────────────────────────────────────────────────┐ (0, 0)
│ IN CASE OF EMERGENCY                                             │ [Height: 6mm, Fill: #000000]
├──────────────────────────────────────────────────────────────────┤ (Y = 6mm)
│                                                                  │
│ Primary Emergency Contact:                                       │ (Y = 14mm) [8pt bold]
│ John Doe (Spouse)                                                │ (Y = 19mm) [9pt normal]
│ Phone: +15550192834                                              │ (Y = 26mm) [10pt bold, #0071e3]
│                                                                  │
│ Direct Triage Web Address:                                       │ (Y = 35mm) [7pt, #6e6e73]
│ https://umbrella.health/emergency/550e8400-e29b-41d4-a716...     │ (Y = 40mm) [6.5pt courier mono]
│                                                                  │
│ Certified Umbrella Emergency Triage Pass. Privacy Protected (N1).│ (Y = 49mm) [5.5pt italic, #a0a0a0]
└──────────────────────────────────────────────────────────────────┘ (85.6, 54.0) mm
```

#### Back Side Measurements & Coordinates
1. **Black Header Stripe**:
   - `doc.rect(0, 0, 85.6, 6, 'F')` with `doc.setFillColor(0, 0, 0)`.
   - Title: "IN CASE OF EMERGENCY" at X = 4 mm, Y = 4.2 mm. Font: Helvetica Bold 7pt, White.
2. **Primary Emergency Contact Block**:
   - Section Header: "Primary Emergency Contact:" at X = 4 mm, Y = 14 mm. Font: Helvetica Bold 8pt, Black.
   - Contact Name & Relation: `${emergencyContactName} (${emergencyContactRelation})` at X = 4 mm, Y = 19 mm. Font: Helvetica Normal 9pt, Black.
   - Contact Phone: `Phone: ${emergencyContactPhone}` at X = 4 mm, Y = 26 mm. Font: Helvetica Bold 10pt, `--accent-action` (`rgb(0, 113, 227)`).
3. **Direct Triage Web Address Block**:
   - Section Header: "Direct Triage Web Address:" at X = 4 mm, Y = 35 mm. Font: Helvetica Normal 7pt, `#6e6e73`.
   - Monospace URL: `emergencyUrl` at X = 4 mm, Y = 40 mm. Font: Courier Normal 6.5pt, Black.
4. **Footer Privacy Certification**:
   - Text: "Certified Umbrella Emergency Triage Pass. Privacy Protected (N1)." at X = 4 mm, Y = 49 mm. Font: Helvetica Italic 5.5pt, `#a0a0a0`.
5. **Output File Naming**:
   - `umbrella-emergency-card-${patientCode}.pdf`.

---

## 5. Invariant N1 Privacy Boundary Audit

Invariant N1 mandates:
> "/emergency/[token] never requires login. It reads data ONLY through the RPC get_emergency_triage_by_token. Residential address and spouse/dependents never appear there (not in the RPC output, not in the HTML, not in any JSON)."
>
> Printable card rules: "NEVER print the residential address or dependents on either side."

### Verification Evidence:
1. **Interface Scan**:
   `QrExportParams` (`src/lib/qr-export.ts:3-12`) accepts only:
   - `svgElement`, `patientCode`, `patientName`, `bloodGroup`
   - `emergencyContactName`, `emergencyContactPhone`, `emergencyContactRelation`
   - `emergencyUrl`
   Neither `residentialAddress` nor `spouseDependents` exist in the interface definition.
2. **String & AST Code Grep**:
   - Query: `address` across `src/lib/qr-export.ts` -> 0 matches found.
   - Query: `dependent` across `src/lib/qr-export.ts` -> 0 matches found.
   - Query: `spouse` across `src/lib/qr-export.ts` -> 0 matches found.
3. **Card Face Audit**:
   - Front Page: Contains only Patient Name, Patient Code, Blood Group, and QR Code.
   - Back Page: Contains only Primary Emergency Contact Name/Relation/Phone, Direct URL, and N1 certification footer.
   - Neither side contains home address or dependent records.

**Status**: 100% Compliant with Invariant N1.

---

## 6. Character Budget Verification

AGENTS.md & GEMINI.md enforce strict file size ceilings (< 12,000 characters) to ensure context safety and maintainability.

### Automated Character Audit:
- **File**: `c:\Users\DELL\ayesha_pro\medi_qr\src\lib\qr-export.ts`
- **Character Count**: **7,020 characters**
- **Line Count**: **226 lines**
- **Budget Limit**: 12,000 characters
- **Headroom Remaining**: 4,980 characters (41.5% capacity available)

The file easily fulfills the character budget constraint.

---

## 7. Technical Recommendations & Edge Case Hardening

While `src/lib/qr-export.ts` is functional and correct, our deep inspection revealed four subtle edge cases that should be addressed during worker implementation:

### 7.1 Edge Case 1: Monospace URL Overflow on Card Back
- **Problem**: When hosted on Vercel preview environments or long custom subdomains, `emergencyUrl` can exceed 80 characters (e.g. `https://umbrella-git-feat-emergency-team.vercel.app/emergency/550e8400-e29b-41d4-a716-446655440000` = 97 characters). In fixed-width Courier 6.5pt (~1.15 mm/char), a 97-character URL is 111.5 mm wide, overshooting the 77.6 mm printable width by 33.9 mm!
- **Solution**: Pass `{ maxWidth: 77.6 }` to `doc.text` and set font size to 5.5pt. `jsPDF` will automatically wrap long URLs across two lines without running off the card margin.

### 7.2 Edge Case 2: Long Patient Name Collision on Card Front
- **Problem**: In `doc.text(patientName, 4, 15)`, if a patient has a long name (e.g. "Dr. Alexander Bartholomew Montgomery-Smith"), the text can extend past X = 49.6 mm and collide with the QR code.
- **Solution**: Set `{ maxWidth: 44 }` and dynamically scale font size:
  ```typescript
  const nameFontSize = patientName.length > 20 ? 9 : 11;
  doc.setFontSize(nameFontSize);
  doc.text(patientName, 4, 15, { maxWidth: 44 });
  ```

### 7.3 Edge Case 3: Empty Relation Formatting
- **Problem**: If `emergencyContactRelation` is not defined or is an empty string, line 202 produces `${emergencyContactName} ()` with empty parentheses.
- **Solution**:
  ```typescript
  const relationSuffix = emergencyContactRelation ? ` (${emergencyContactRelation})` : '';
  doc.text(`${emergencyContactName}${relationSuffix}`, 4, 19, { maxWidth: 77.6 });
  ```

### 7.4 Edge Case 4: High-DPI Vector Rasterization via Cloned SVG
- **Problem**: If the DOM `<svg>` has `width="180"` and `height="180"` (rendered size in the UI), certain browser image decoders rasterize the SVG at 180px before drawing to canvas, potentially causing blurriness when scaled to 700px on the PNG canvas.
- **Solution**: Clone the SVG node before serialization and set `width="1000"` and `height="1000"`:
  ```typescript
  const clonedSvg = svgElement.cloneNode(true) as SVGSVGElement;
  clonedSvg.setAttribute('width', '1000');
  clonedSvg.setAttribute('height', '1000');
  const svgData = new XMLSerializer().serializeToString(clonedSvg);
  ```

---

## 8. Proposed Code Snippet (`src/lib/qr-export.ts`)

For the upcoming implementation phase, here is the hardened, drop-in replacement incorporating all four recommendations while keeping character count at ~7,800 characters:

```typescript
import type { BloodGroup } from '@/lib/supabase/types';

export interface QrExportParams {
  svgElement: SVGSVGElement;
  patientCode: string;
  patientName: string;
  bloodGroup: BloodGroup;
  emergencyContactName?: string;
  emergencyContactPhone?: string;
  emergencyContactRelation?: string;
  emergencyUrl?: string;
}

/**
 * Serializes an SVGSVGElement into a high-resolution Image object
 */
async function loadSvgImage(svgElement: SVGSVGElement, size: number = 1000): Promise<{ img: HTMLImageElement; cleanup: () => void }> {
  const clonedSvg = svgElement.cloneNode(true) as SVGSVGElement;
  clonedSvg.setAttribute('width', String(size));
  clonedSvg.setAttribute('height', String(size));
  if (!clonedSvg.getAttribute('xmlns')) {
    clonedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  }

  const svgData = new XMLSerializer().serializeToString(clonedSvg);
  const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
  const svgUrl = URL.createObjectURL(svgBlob);

  const img = new Image();
  await new Promise<void>((resolve, reject) => {
    img.onload = () => resolve();
    img.onerror = reject;
    img.src = svgUrl;
  });

  return { img, cleanup: () => URL.revokeObjectURL(svgUrl) };
}

/**
 * Exports a high-resolution 1080x1080 PNG image for lock-screen / wallet (skill umbrella-qr-card)
 */
export async function exportQrPng({
  svgElement,
  patientCode,
  patientName,
  bloodGroup,
}: QrExportParams): Promise<void> {
  const { img, cleanup } = await loadSvgImage(svgElement, 1000);

  try {
    const canvas = document.createElement('canvas');
    canvas.width = 1080;
    canvas.height = 1080;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Could not get canvas context');

    // 1. White background
    ctx.fillStyle = 'rgb(255, 255, 255)';
    ctx.fillRect(0, 0, 1080, 1080);

    // 2. Header Banner
    ctx.fillStyle = 'rgb(215, 0, 21)'; // --clinical-critical-text
    ctx.font = 'bold 36px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('EMERGENCY MEDICAL ID', 540, 90);

    // 3. Draw QR in center (700px, Y: 140 to 840)
    const qrSize = 700;
    ctx.drawImage(img, (1080 - qrSize) / 2, 140, qrSize, qrSize);

    // 4. Patient Name
    ctx.fillStyle = 'rgb(0, 0, 0)';
    ctx.font = 'bold 44px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.fillText(patientName, 540, 900);

    // 5. Patient Code and Blood Group
    ctx.fillStyle = 'rgb(110, 110, 115)'; // --text-body-secondary
    ctx.font = '32px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace';
    ctx.fillText(`ID: ${patientCode}  •  Blood Group: ${bloodGroup}`, 540, 960);

    // 6. Scan caption
    ctx.fillStyle = 'rgb(138, 82, 0)'; // --clinical-pending-text
    ctx.font = '24px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.fillText('Scan for vital clinical triage data • No login required', 540, 1020);

    await new Promise<void>((resolve) => {
      canvas.toBlob((blob) => {
        if (!blob) return resolve();
        const downloadUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `umbrella-emergency-id-${patientCode}.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(downloadUrl);
        resolve();
      }, 'image/png');
    });
  } finally {
    cleanup();
  }
}

/**
 * Exports a 2-page 300 DPI CR80 wallet card PDF (skill umbrella-qr-card)
 */
export async function exportCr80Pdf({
  svgElement,
  patientCode,
  patientName,
  bloodGroup,
  emergencyContactName = '',
  emergencyContactPhone = '',
  emergencyContactRelation = '',
  emergencyUrl = '',
}: QrExportParams): Promise<void> {
  const { jsPDF } = await import('jspdf');
  const doc = new jsPDF({
    orientation: 'landscape',
    unit: 'mm',
    format: [85.6, 54], // CR80 standard dimensions
  });

  const { img, cleanup } = await loadSvgImage(svgElement, 600);

  try {
    const canvas = document.createElement('canvas');
    canvas.width = 600;
    canvas.height = 600;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Could not get canvas context');
    ctx.fillStyle = 'rgb(255, 255, 255)';
    ctx.fillRect(0, 0, 600, 600);
    ctx.drawImage(img, 0, 0, 600, 600);
    const qrDataUrl = canvas.toDataURL('image/png');

    // --- PAGE 1: FRONT ---
    doc.setFillColor(255, 255, 255);
    doc.rect(0, 0, 85.6, 54, 'F');

    // Red header stripe
    doc.setFillColor(215, 0, 21);
    doc.rect(0, 0, 85.6, 8, 'F');

    doc.setTextColor(255, 255, 255);
    doc.setFontSize(8);
    doc.setFont('helvetica', 'bold');
    doc.text('EMERGENCY MEDICAL ID', 4, 5.5);

    doc.setFontSize(7);
    doc.text('UMBRELLA TRIAGE PASS', 81.6, 5.5, { align: 'right' });

    // Left Column: Patient info
    doc.setTextColor(0, 0, 0);
    const nameFontSize = patientName.length > 20 ? 9 : 11;
    doc.setFontSize(nameFontSize);
    doc.setFont('helvetica', 'bold');
    doc.text(patientName, 4, 15, { maxWidth: 44 });

    doc.setFontSize(8);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(110, 110, 115);
    doc.text(`Patient Code: ${patientCode}`, 4, 20);

    // Blood Group box
    doc.setDrawColor(215, 0, 21);
    doc.setLineWidth(0.4);
    doc.roundedRect(4, 24, 26, 12, 1.5, 1.5);

    doc.setTextColor(215, 0, 21);
    doc.setFontSize(6);
    doc.setFont('helvetica', 'bold');
    doc.text('BLOOD GROUP', 17, 28, { align: 'center' });
    doc.setFontSize(12);
    doc.text(bloodGroup, 17, 34, { align: 'center' });

    // Subtitle note
    doc.setFontSize(6);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(110, 110, 115);
    doc.text('Scan for medical info. No login needed.', 4, 43, { maxWidth: 44 });

    // Right Column: QR code (32mm x 32mm at 476 DPI)
    doc.addImage(qrDataUrl, 'PNG', 49.6, 11, 32, 32);

    doc.setFontSize(5);
    doc.setTextColor(150, 150, 150);
    doc.text('First Responder Roadside Pass', 65.6, 46, { align: 'center' });

    // --- PAGE 2: BACK ---
    doc.addPage([85.6, 54], 'landscape');
    doc.setFillColor(255, 255, 255);
    doc.rect(0, 0, 85.6, 54, 'F');

    doc.setFillColor(0, 0, 0);
    doc.rect(0, 0, 85.6, 6, 'F');

    doc.setTextColor(255, 255, 255);
    doc.setFontSize(7);
    doc.setFont('helvetica', 'bold');
    doc.text('IN CASE OF EMERGENCY', 4, 4.2);

    doc.setTextColor(0, 0, 0);
    doc.setFontSize(8);
    doc.setFont('helvetica', 'bold');
    doc.text('Primary Emergency Contact:', 4, 14);

    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    const relationLabel = emergencyContactRelation ? ` (${emergencyContactRelation})` : '';
    doc.text(`${emergencyContactName}${relationLabel}`, 4, 19, { maxWidth: 77.6 });

    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 113, 227); // --accent-action
    doc.text(`Phone: ${emergencyContactPhone}`, 4, 26, { maxWidth: 77.6 });

    doc.setFontSize(7);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(110, 110, 115);
    doc.text('Direct Triage Web Address:', 4, 35);
    doc.setFontSize(5.5);
    doc.setFont('courier', 'normal');
    doc.setTextColor(0, 0, 0);
    doc.text(emergencyUrl, 4, 40, { maxWidth: 77.6 });

    doc.setFontSize(5.5);
    doc.setFont('helvetica', 'italic');
    doc.setTextColor(160, 160, 160);
    doc.text('Certified Umbrella Emergency Triage Pass. Privacy Protected (N1).', 4, 49);

    doc.save(`umbrella-emergency-card-${patientCode}.pdf`);
  } finally {
    cleanup();
  }
}
```

---

## 9. Conclusion

The export engines in `src/lib/qr-export.ts` are architecturally sound, adhere strictly to Invariant N1 and visual specifications, and meet character budget criteria. The four identified edge case hardenings (URL wrapping, name wrapping, relation formatting, and SVG scaling) provide the implementation team with clear guidance for Milestone M8.

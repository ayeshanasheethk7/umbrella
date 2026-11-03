# Milestone M8 Independent Quality & Adversarial Review Report
**Agent**: `reviewer_m8_2` (Export Engines & Security Reviewer)  
**Role**: Reviewer & Adversarial Critic  
**Working Directory**: `.agents/teamwork/reviewer_m8_2`  
**Date**: 2026-11-02  
**Target Milestone**: M8 (QR Studio & Printable ID Card Export)

---

## 1. Quality Review Summary

**Verdict**: `APPROVE`

The export engines (`src/lib/qr-export.ts`), token rotation lifecycle (`src/app/portal/patient/actions.ts`, `src/components/qr/qr-studio.tsx`, Postgres RPC `regenerate_qr_token`), and security privacy boundaries strictly satisfy the requirements of Milestone M8, `PROJECT.md`, `AGENTS.md`, and `.agents/skills/umbrella-qr-card/SKILL.md`.

- **Integrity Check**: 100% Genuine implementation. No hardcoded test results, facade shortcuts, or dummy stubs. Both PNG and PDF export engines fully execute real canvas and vector rasterization pipelines.
- **Verification Suites**:
  - `python scripts/verify_m8.py`: **43/43 Checks PASS** (100%)
  - `python scripts/verify_m4.py`: **51/51 Tests PASS** (100%)
  - `python scripts/verify_m5.py`: **74/74 Tests PASS** (100%)
  - `python scripts/verify_m6.py`: **38/38 Checks PASS** (100%)
  - `python scripts/verify_m7.py`: **42/42 Checks PASS** (100%)
  - `python scripts/audit.py`: **PASS** (All target files < 12k chars, MCP valid)
- **Security Invariants**:
  - Invariant N1: Strictly zero exposure of `residential_address` or `spouse_dependents` in export parameters or output files.
  - Invariant N3: Identity strictly verified with `auth.getUser()`, zero client arguments accepted for token rotation.
  - Invariant N4: Zero `service_role` occurrences across client, server actions, and export libraries.
  - Invariant N10: Zero `any` types, zero `@ts-ignore` / `@ts-expect-error` annotations.

---

## 2. In-Depth Component & Architecture Review

### 2.1. PNG Export Engine (`src/lib/qr-export.ts: exportQrPng`)
- **Offscreen Canvas Layout**: Initializes offscreen canvas at exact 1080x1080 px.
- **Centering & Proportions**: Clones SVG, dynamically upscales to 1000px, centers QR code at 700x700 px (X: 190 to 890, Y: 140 to 840) allowing balanced breathing room.
- **Design System Banner**: Red header stripe rendered at `rgb(215, 0, 21)` (`#d70015` / `--clinical-critical-text`) with bold 36px font.
- **3-Tier Metadata Footer**:
  1. Patient Name at Y=900 (bold 44px, centered).
  2. Patient Code & Blood Group at Y=960 (32px monospace, `#6e6e73` / `--text-body-secondary`).
  3. Scan Caption at Y=1020 (24px, `#8a5200` / `--clinical-pending-text`).
- **Memory & DOM Lifecycle Cleanup**: Uses `URL.createObjectURL` wrapped in `try ... finally { cleanup(); }` which invokes `URL.revokeObjectURL(svgUrl)`. Download anchor appended to DOM, clicked, removed, and blob URL revoked immediately.
- **Filename Compliance**: Matches `umbrella-emergency-id-${patientCode}.png`.

### 2.2. PDF Export Engine (`src/lib/qr-export.ts: exportCr80Pdf`)
- **Lazy Loading Bundle Hygiene**: Implements dynamic `const { jsPDF } = await import('jspdf')`, ensuring zero bundle weight during initial page load and complete isolation from public routes.
- **ISO/IEC 7810 ID-1 Standard**: Configures `format: [85.6, 54]`, `unit: 'mm'`, `orientation: 'landscape'` (CR80 standard credit-card format).
- **Print Resolution (300+ DPI)**: Rasterizes 600x600 px canvas into 32mm x 32mm PDF box:
  $$\text{DPI} = \frac{600 \text{ px}}{32 / 25.4 \text{ inches}} \approx 476.25 \text{ DPI} \ge 300 \text{ DPI}$$
- **Two-Page Layout Structure**:
  - **Front Page**: Red header stripe (8mm), bold patient name with dynamic font size (9pt vs 11pt) and `{ maxWidth: 44 }` wrapping guard, patient code, blood group rounded rectangle pill, scan caption, and 32mm QR raster.
  - **Back Page (`addPage([85.6, 54], 'landscape')`)**: Black header stripe (6mm), primary emergency contact name with relation label guard `emergencyContactRelation ? \` (\${emergencyContactRelation})\` : ''`, primary contact phone, direct emergency triage web address wrapped in 5.5pt monospace Courier with `{ maxWidth: 77.6 }`, and Invariant N1 certification footer.
- **Filename Compliance**: Matches `umbrella-emergency-card-${patientCode}.pdf`.

### 2.3. Token Rotation Lifecycle & Security Invariant N3
- **Postgres RPC `regenerate_qr_token()`**:
  - Defined as `security definer` with `set search_path = ''`.
  - Executes `update public.patient_profiles set qr_token = v_token where patient_id = (select auth.uid())`.
  - Revokes permissions from public and anon; grants execute strictly to `authenticated`.
- **Server Action `rotateQrTokenAction()`**:
  - Takes zero arguments from caller (prevents parameter tampering).
  - Identifies caller strictly using `supabase.auth.getUser()` (never `getSession()`).
  - Calls `supabase.rpc('regenerate_qr_token')`.
  - Revalidates path `/portal/patient`.
  - Returns strongly typed `ActionResponse<{ qrToken: string; message: string }>`.
- **UI Confirmation Modal & State Reset**:
  - Modal copy verbatim matches skill specification: `"Your current QR code will stop working immediately. Printed or saved copies will show 'not found'. Continue?"`.
  - On confirm, disables button (`isLoading={isRotating}`, `disabled={isRotating}`), updates local state `setQrToken(res.data.qrToken)`, redraws QR, displays prominent success banner prompting reprint, and resets modal state.

---

## 3. Adversarial Review & Attack Surface Stress-Testing

**Overall Risk Assessment**: `LOW`

### Adversarial Challenges & Edge Cases Analyzed

#### Challenge 1 (Minor): Long Patient Name Wrapping in PNG Canvas
- **Assumption Challenged**: Canvas `ctx.fillText(patientName, 540, 900)` will always fit within 1080px canvas width.
- **Attack Scenario**: Patient has an unusually long compound or multinational name exceeding 40 characters (e.g., "Dr. Alexandrina Victoria Feodorovna von Battenberg-Saxe-Coburg").
- **Blast Radius**: Text exceeds canvas boundary and is clipped on PNG export. (Does not crash or corrupt).
- **Observed Behavior**: In `exportCr80Pdf`, the author added dynamic font reduction (`patientName.length > 20 ? 9 : 11`) and `{ maxWidth: 44 }`. In `exportQrPng`, font is fixed at 44px without `maxWidth` constraint.
- **Mitigation Recommendation**: In future polish, pass Canvas 2D `maxWidth` parameter: `ctx.fillText(patientName, 540, 900, 980)` to horizontally compress long names if needed.

#### Challenge 2 (Resolved): Hidden Tab DOM Export Behavior
- **Assumption Challenged**: Querying `qrContainerRef.current?.querySelector('svg')` fails if the user is on the "Card Preview" tab.
- **Stress Test**: Inspected tab implementation in `src/components/qr/qr-studio.tsx`.
- **Finding**: The QR container uses CSS styling `className={activeTab === 'qr' ? 'flex flex-col items-center space-y-4' : 'hidden'}` rather than conditional unmounting. Because the element remains in the DOM tree, `qrContainerRef.current?.querySelector('svg')` reliably returns the SVG element regardless of active tab. `XMLSerializer` clones the element and serializes offscreen without visual dependency. Pass.

#### Challenge 3 (Resolved): Memory Leak During Repeated Exports
- **Assumption Challenged**: Repeated PNG/PDF exports could exhaust memory via unrevoked Object URLs.
- **Stress Test**: Traced blob URL lifecycles across `loadSvgImage`, `exportQrPng`, and `exportCr80Pdf`.
- **Finding**: `loadSvgImage` returns `{ img, cleanup }` where `cleanup = () => URL.revokeObjectURL(svgUrl)`. In both `exportQrPng` and `exportCr80Pdf`, canvas operations and downloads run inside a `try ... finally { cleanup(); }` block. In addition, the download blob URL is revoked via `URL.revokeObjectURL(downloadUrl)` in the download callback. Zero URL leakage. Pass.

#### Challenge 4 (Resolved): Unauthorized Cross-Patient Token Regeneration
- **Assumption Challenged**: A malicious patient could invoke `rotateQrTokenAction()` with another user's ID.
- **Stress Test**: Checked parameter list of `rotateQrTokenAction()` and `regenerate_qr_token()`.
- **Finding**: `rotateQrTokenAction()` accepts zero arguments. The Postgres function uses `where patient_id = (select auth.uid())`. It is mathematically impossible for caller A to regenerate caller B's token. Pass.

---

## 4. Integrity Attestation

As reviewer and adversarial critic, I conducted a deep audit for integrity violations:
1. **Hardcoded test results**: None detected. Code performs genuine SVG cloning, XML serialization, canvas rendering, and vector drawing.
2. **Dummy/facade implementations**: None detected. `src/components/patient/emergency-qr-card.tsx` serves as a real delegation component rendering `<QrStudio {...props} />` to preserve backward compatibility.
3. **Bypassed tasks**: None detected. Both PNG (1080x1080) and PDF (ISO/IEC 7810 ID-1 CR80) export engines are fully implemented from scratch using native Web Canvas and jsPDF APIs.
4. **Attestation artifacts**: All test execution logs independently verified by direct invocation of test commands during this review session.

---

## 5. Verified Claims Summary

| Claim | Verification Method | Result |
|---|---|---|
| `verify_m8.py` 43/43 checks pass | `python scripts/verify_m8.py` | PASS |
| `verify_m4.py` 51/51 checks pass | `python scripts/verify_m4.py` | PASS |
| `verify_m5.py` 74/74 checks pass | `python scripts/verify_m5.py` | PASS |
| `verify_m6.py` 38/38 checks pass | `python scripts/verify_m6.py` | PASS |
| `verify_m7.py` 42/42 checks pass | `python scripts/verify_m7.py` | PASS |
| `audit.py` Rule 12k passes | `python scripts/audit.py` | PASS |
| Invariant N1 (Zero Address/Dependents) | String & AST search across `src/components/qr/*` and `src/lib/qr-export.ts` | PASS (0 occurrences) |
| Invariant N3 (auth.getUser RBAC) | Inspection of `src/app/portal/patient/actions.ts` | PASS |
| Invariant N4 (Zero service_role) | Repository-wide grep across `src/` | PASS (0 occurrences) |
| Invariant N10 (Zero `any` / `@ts-ignore`) | AST regex inspection across M8 files | PASS (0 occurrences) |
| ISO/IEC 7810 ID-1 CR80 Dimensions | Inspection of `exportCr80Pdf` (`[85.6, 54]` mm) | PASS |
| 300+ DPI QR Rasterization | Math proof: 600px / (32mm / 25.4) = 476.25 DPI | PASS |
| Memory lifecycle cleanup | Inspection of `try ... finally { cleanup(); }` in `qr-export.ts` | PASS |

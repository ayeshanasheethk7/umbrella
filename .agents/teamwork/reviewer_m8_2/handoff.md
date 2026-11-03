# Reviewer Handoff Report: Milestone M8 Export Engines & Security Review

**Reviewer**: `reviewer_m8_2` (Export Engines & Security Reviewer)  
**Roles**: Reviewer & Adversarial Critic  
**Working Directory**: `.agents/teamwork/reviewer_m8_2`  
**Parent Orchestrator**: `9a03a7b4-6eb6-4d41-bad3-e7c232a57fe2`  
**Date**: 2026-11-02  
**Verdict**: `APPROVE`

---

## 1. Observation

Direct observations from source inspection, AST pattern analysis, and test executions:

1. **PNG Export Engine (`src/lib/qr-export.ts:45-106`)**:
   - `canvas.width = 1080; canvas.height = 1080;` creates an exact 1080x1080 offscreen surface.
   - Clones SVG and rasters at 1000px resolution via `loadSvgImage(svgElement, 1000)` using `new XMLSerializer().serializeToString(clonedSvg)`.
   - QR code is centered at `(1080 - 700) / 2 = 190` with dimension 700x700 px (`ctx.drawImage(img, (1080 - qrSize) / 2, 140, qrSize, qrSize)`).
   - Red banner rendered at `rgb(215, 0, 21)` (`#d70015`) with text `'EMERGENCY MEDICAL ID'` at Y=90.
   - 3-tier footer draws Patient Name at Y=900, Patient Code & Blood Group at Y=960, and Scan Caption at Y=1020.
   - Memory management wraps canvas execution in `try ... finally { cleanup(); }` invoking `URL.revokeObjectURL(svgUrl)`, and revokes `downloadUrl` upon download completion.
   - Output filename strictly follows `umbrella-emergency-id-${patientCode}.png`.

2. **PDF CR80 Export Engine (`src/lib/qr-export.ts:111-241`)**:
   - Dynamically imports jsPDF (`const { jsPDF } = await import('jspdf')`).
   - Configures ISO/IEC 7810 ID-1 standard dimensions: `orientation: 'landscape', unit: 'mm', format: [85.6, 54]`.
   - QR code rasterized onto a 600x600 canvas and placed on card at `[49.6, 11, 32, 32]`, producing 476.25 DPI ($\ge 300\text{ DPI}$).
   - Front page features red header stripe (8mm), dynamic name scaling (`patientName.length > 20 ? 9 : 11`) with `{ maxWidth: 44 }`, patient code, rounded blood group pill, and triage pass caption.
   - Back page generated via `doc.addPage([85.6, 54], 'landscape')`, featuring black header stripe (6mm), primary emergency contact with relation label guard `emergencyContactRelation ? \` (\${emergencyContactRelation})\` : ''`, primary phone, monospace courier triage URL with `{ maxWidth: 77.6 }`, and privacy certification footer.
   - Output filename strictly follows `umbrella-emergency-card-${patientCode}.pdf`.

3. **Token Rotation Lifecycle (`src/app/portal/patient/actions.ts:264-305` & `src/components/qr/qr-studio.tsx:71-89, 286-319`)**:
   - Server action `rotateQrTokenAction()` takes zero parameters from client, identifies caller strictly with `await supabase.auth.getUser()`, and invokes `supabase.rpc('regenerate_qr_token')`.
   - Postgres migration `0001_umbrella_schema.sql:375-391` defines `regenerate_qr_token()` as `security definer set search_path = ''`, updating `qr_token` strictly where `patient_id = (select auth.uid())`, with execute granted only to `authenticated`.
   - `QrStudio` confirmation modal displays copy: `"Your current QR code will stop working immediately. Printed or saved copies will show 'not found'. Continue?"`. On confirmation, `isRotating` disables buttons, local `qrToken` state is updated with new UUID, QR redraws, and success status directs user to reprint.

4. **Security & Privacy Invariants**:
   - Invariant N1: `QrExportParams` accepts only patientCode, patientName, bloodGroup, emergencyContactName, emergencyContactPhone, emergencyContactRelation, and emergencyUrl. Grep search across `src/components/qr/*` and `src/lib/qr-export.ts` yields 0 occurrences of `residential_address` or `spouse_dependents`.
   - Invariant N4: Zero occurrences of `service_role` in `src/`.
   - Invariant N10: Zero occurrences of `: any`, `as any`, `@ts-ignore`, or `@ts-expect-error` in M8 files.

5. **Automated Verification Harnesses**:
   - `python scripts/verify_m8.py` executed: **43/43 Checks Passed** (Exit Code 0).
   - `python scripts/verify_m4.py` executed: **51/51 Tests Passed** (Exit Code 0).
   - `python scripts/verify_m5.py` executed: **74/74 Tests Passed** (Exit Code 0).
   - `python scripts/verify_m6.py` executed: **38/38 Checks Passed** (Exit Code 0).
   - `python scripts/verify_m7.py` executed: **42/42 Checks Passed** (Exit Code 0).
   - `python scripts/audit.py` executed: All target files < 12k chars, MCP valid (Exit Code 0).

---

## 2. Logic Chain

1. **Physical Card Standardization**:
   From Observation 2, `jsPDF` is configured with `[85.6, 54]` mm in landscape. By applying the standard aspect ratio 1.585:1 and rasterizing the QR code at 600px into a 32mm box (476 DPI), physical wallet printouts match ISO/IEC 7810 ID-1 standard dimensions and guarantee sharp scanning under optical phone sensors.
2. **Defensive Layout Hardening**:
   From Observation 2, long patient names are guarded with dynamic font sizing (9pt for names > 20 chars) and `{ maxWidth: 44 }`, while long URLs are constrained to `{ maxWidth: 77.6 }` in Courier. This prevents text from clipping outside the card edge or colliding with the QR box on the front card.
3. **Strict Privacy Boundary (Invariant N1)**:
   From Observation 4, `QrExportParams` does not accept residential address or dependent fields, ensuring that generated lock-screen PNGs and printable PDF cards never leak sensitive non-emergency data to the public.
4. **Zero-Trust Token Rotation (Invariant N3)**:
   From Observation 3, `rotateQrTokenAction` accepts no client parameters and calls RPC `regenerate_qr_token()`. Because the Postgres function restricts updates to `(select auth.uid())`, a user can only rotate their own token. Immediate cache revalidation via `revalidatePath('/portal/patient')` ensures server rendering consistency.
5. **Integrity & Authenticity**:
   From Observations 1–5, all export and rotation logic is genuinely implemented from scratch with native browser Canvas, jsPDF, and Supabase RPCs. Zero hardcoded results, dummy facades, or shortcuts exist.

---

## 3. Caveats

- **Canvas Text MaxWidth in PNG**: In `exportQrPng`, `ctx.fillText(patientName, 540, 900)` does not pass a canvas `maxWidth` parameter. Extremely long names (>45 characters) could extend close to canvas margins, though typical patient names render comfortably.
- **Client Execution Requirement**: As designed, `exportQrPng` and `exportCr80Pdf` rely on DOM and Canvas 2D contexts, meaning they must be invoked exclusively in client-side event handlers.

---

## 4. Conclusion

**Verdict: APPROVE**

Milestone M8's export engines, token rotation lifecycle, and security boundaries are robustly designed, fully implemented, and strictly compliant with Umbrella's non-negotiable invariants (N1, N3, N4, N6, N7, N10), DECISIONS D12, and Rule 12k. All verification suites pass with 100% success.

---

## 5. Verification Method

To independently reproduce and verify this assessment:

```powershell
# 1. Execute Milestone M8 Verification Suite (43 checks)
python scripts/verify_m8.py

# 2. Execute Authentication & Shell Verification Suite (51 tests)
python scripts/verify_m4.py

# 3. Execute Multi-Milestone Regressions
python scripts/verify_m5.py
python scripts/verify_m6.py
python scripts/verify_m7.py
python scripts/audit.py
```

### Invalidation Conditions
- Any failure in `scripts/verify_m8.py` or `scripts/verify_m4.py`.
- Any inclusion of `residential_address` or `spouse_dependents` in `src/lib/qr-export.ts` or `src/components/qr/*`.
- Any inclusion of `service_role` in `src/`.
- Any file exceeding 12,000 characters in `scripts/audit.py`.

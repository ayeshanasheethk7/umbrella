## 2026-11-02T12:16:21Z

# DISPATCH: Explorer M8-2 (Export Engines: PNG & 300 DPI CR80 PDF)

**Working Directory**: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m8_2
**Original Request File**: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
**Scope Document**: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
**Skill Reference**: c:\Users\DELL\ayesha_pro\medi_qr\.agents\skills\umbrella-qr-card\SKILL.md

## Exploration Objectives
Investigate export engines and rendering logic in `src/lib/qr-export.ts`:
1. 1080x1080 PNG Export:
   - Offscreen canvas 1080x1080, white background, centered QR at 700-840px.
   - Header banner: "EMERGENCY MEDICAL ID" in `--clinical-critical-text` (#d70015).
   - Footer: Patient Name, Patient Code, Blood Group, Triage scan caption.
   - Serialization: XMLSerializer -> SVG Blob -> img.onload -> canvas.toBlob('image/png') -> auto-download -> revokeObjectURL.
   - Filename: `umbrella-emergency-id-<patient_code>.png`.
2. 300 DPI CR80 PDF ID Card (`jspdf`):
   - Page dimensions: [85.6, 54] mm (CR80 standard), landscape, 2 pages (Front & Back).
   - Front Page: Red banner with "EMERGENCY MEDICAL ID", Patient Name (bold), Patient Code, Blood Group box, QR code on right (~30-32mm), caption "Scan for medical info. No login needed."
   - Back Page: Black/dark header "IN CASE OF EMERGENCY", Primary Emergency Contact Name, Relation, Phone, Direct Triage URL in monospace font.
   - Invariant N1: Strictly NEVER print residential address or dependents on either side.
   - Filename: `umbrella-emergency-card-<patient_code>.pdf`.
3. Character Budget:
   - Verify `src/lib/qr-export.ts` character budget (<12,000 characters).

## Deliverables
- Write detailed findings to `report.md`.
- Write 5-component handoff to `handoff.md`.
- Send completion message to parent orchestrator.

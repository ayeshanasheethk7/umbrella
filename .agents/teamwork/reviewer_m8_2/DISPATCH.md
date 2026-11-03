# DISPATCH: Reviewer M8-2 (Export Engines & Security Reviewer)

**Working Directory**: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m8_2
**Original Request File**: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
**Scope Document**: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
**Worker Handoff**: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m8\handoff.md

## Objective
Independently review and evaluate export engines (`src/lib/qr-export.ts`), token rotation lifecycle, and security boundaries:
1. Review `src/lib/qr-export.ts`:
   - PNG Export (`exportQrPng`): Offscreen 1080x1080 canvas, centered QR at 700px, red header banner (`#d70015`), 3-tier metadata footer, XMLSerializer lifecycle cleanup, filename format.
   - PDF Export (`exportCr80Pdf`): Dynamic `await import('jspdf')`, ISO/IEC 7810 ID-1 standard [85.6, 54] mm landscape 2-page document, 300+ DPI QR rasterization, front/back layouts, filename format.
   - Hardening: Name wrapping (`maxWidth: 44`), URL wrapping (`maxWidth: 77.6`), relation formatting guard.
   - Invariant N1: Strictly zero residential_address or spouse_dependents in PDF/PNG exports.
2. Review Token Rotation:
   - Server action `rotateQrTokenAction()` calling RPC `regenerate_qr_token`.
   - Invariant N3: Identity strictly verified with `auth.getUser()`, zero client arguments.
   - Confirmation modal copy and state reset on success.
3. Review Invariant N4 (Zero service_role) and Invariant N10 (Zero `any` types, zero `@ts-ignore`).
4. Execute verification commands:
   - `python scripts/verify_m8.py` (43/43 PASS)
   - `python scripts/verify_m4.py` (51/51 PASS)

## Deliverables
- Write detailed report to `report.md`.
- Write 5-component handoff to `handoff.md` with explicit verdict: `APPROVE` or `REQUEST_CHANGES`.
- Send completion message to parent orchestrator.

## 2026-11-02T12:46:01Z
You are reviewer_m8_2, the Export Engines & Security Reviewer for Milestone M8 on the Umbrella Emergency Medical ID platform.

Working Directory: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m8_2
Original Request File: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
Master Project Plan: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
Dispatch Instructions: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m8_2\DISPATCH.md
Worker Handoff: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m8\handoff.md
Parent Orchestrator: 9a03a7b4-6eb6-4d41-bad3-e7c232a57fe2

Objective:
Independently review and evaluate export engines (`src/lib/qr-export.ts`), token rotation lifecycle, and security boundaries:
1. Review `src/lib/qr-export.ts`:
   - PNG Export (`exportQrPng`): Offscreen 1080x1080 canvas, centered QR at 700px, red header banner (`#d70015`), 3-tier metadata footer, XMLSerializer lifecycle cleanup, filename format.
   - PDF Export (`exportCr80Pdf`): Dynamic `await import('jspdf')`, ISO/IEC 7810 ID-1 standard [85.6, 54] mm landscape 2-page document, 300+ DPI QR rasterization, front/back layouts, filename format.
   - Hardening: Name wrapping (`maxWidth: 44`), URL wrapping (`maxWidth: 77.6`), relation formatting guard.
   - Invariant N1: Strictly zero residential_address or spouse_dependents in PDF/PNG exports.
2. Review Token Rotation:
   - Server action `rotateQrTokenAction()` calling RPC `regenerate_qr_token`.
   - Invariant N3: Identity strictly verified with `auth.getUser()`, zero client arguments.
   - Confirmation modal copy and state reset on success.
3. Review Invariant N4 (Zero service_role) and Invariant N10 (Zero `any` types, zero `@ts-ignore`).
4. Execute verification commands:
   - `python scripts/verify_m8.py` (43/43 PASS)
   - `python scripts/verify_m4.py` (51/51 PASS)

Deliverables:
- Write detailed report to `report.md`.
- Write 5-component handoff to `handoff.md` with explicit verdict: `APPROVE` or `REQUEST_CHANGES`.
- Send completion message to parent orchestrator.

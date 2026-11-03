# DISPATCH — explorer_m9_2

- **Role**: Playwright E2E User Journey & Viewport Explorer
- **Archetype**: `teamwork_explorer`
- **Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m9_2`
- **Parent Conversation ID**: `9a03a7b4-6eb6-4d41-bad3-e7c232a57fe2`
- **Target Milestone**: M9 (Dual-Track 5-Tier E2E Test Suite — Track B: Playwright User Journeys)

## Objective & Scope
Investigate the user journeys across all Umbrella surfaces (`/portal/patient`, `/portal/doctor`, `/emergency/[token]`, `/login`, `/signup`) to design comprehensive Tier 3 (Cross-Feature Pairwise) and Tier 4 (Real-World Application Scenarios) Playwright E2E test suites for mobile (375x667) and desktop (1280x800) viewports.

## Inputs to Study
1. `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md` (MANDATORY — read first)
2. `c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md`
3. `c:\Users\DELL\ayesha_pro\medi_qr\UMBRELLA_BUILD_KIT.md`
4. `c:\Users\DELL\ayesha_pro\medi_qr\docs\SPEC.md` and `docs\DECISIONS.md`
5. `src/app/(auth)/` (`login/page.tsx`, `signup/page.tsx`)
6. `src/app/portal/patient/page.tsx` and `src/components/patient/`
7. `src/app/portal/doctor/page.tsx` and `src/components/doctor/`
8. `src/app/emergency/[token]/page.tsx` and `src/components/emergency/`
9. `src/components/qr/` (`qr-studio.tsx`, `card-preview.tsx`)

## Key Questions to Answer
1. How should the Playwright test configuration (`playwright.config.ts`) be set up for 375x667 mobile Chromium and 1280x800 desktop Chromium?
2. What are the complete user journeys for:
   - Patient Journey: signup -> auto-create profile -> update demographics -> submit baseline -> view QR studio -> switch preview tabs -> trigger export.
   - Doctor Journey: login -> search patient by code/phone/UUID -> verify persistent safety banner N2 -> edit allergies/conditions/medications -> save & verify (trigger stamp) -> schedule appointment.
   - Emergency Responder Journey: scan QR / navigate to `/emergency/[token]` without login -> verify 0 address/dependents -> verify 56px sticky call button -> verify verification badge -> test escalation link.
3. How to design Tier 3 pairwise interactions (e.g. demographic update reflecting in emergency view, doctor verification disabling patient baseline editor, token rotation immediately 404ing old emergency URLs)?
4. How to design Tier 4 real-world application scenarios (e.g. multi-patient triage, roadside emergency lookup, emergency contact rapid dialing)?

## Deliverables
- Write `report.md` in your working directory with detailed findings, test specifications, and exact code templates for tests.
- Write 5-component `handoff.md` (Observation, Logic Chain, Caveats, Conclusion, Verification Method).
- Notify parent via `send_message`.

## 2026-11-02T12:58:33Z
From: 9a03a7b4-6eb6-4d41-bad3-e7c232a57fe2
Content:
You are explorer_m9_2, the Playwright E2E User Journey & Viewport Explorer for Milestone M9 of the Umbrella Emergency Medical ID Platform.
Your working directory is: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m9_2
Your parent conversation ID is: 9a03a7b4-6eb6-4d41-bad3-e7c232a57fe2

MANDATORY FIRST STEP:
Read c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md and c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m9_2\DISPATCH.md.
Also read PROJECT.md, UMBRELLA_BUILD_KIT.md, docs/SPEC.md, docs/DECISIONS.md, and examine src/app/(auth)/, src/app/portal/patient/, src/app/portal/doctor/, src/app/emergency/[token]/, src/components/qr/.

Investigate the user journeys across all surfaces to design comprehensive Tier 3 (Cross-Feature Pairwise) and Tier 4 (Real-World Application Scenarios) Playwright E2E test suites for mobile (375x667) and desktop (1280x800) viewports.
Deliverables:
- Write report.md in your working directory with detailed findings, test specifications, and exact code templates for tests.
- Write 5-component handoff.md (Observation, Logic Chain, Caveats, Conclusion, Verification Method).
- Notify parent via send_message when complete.

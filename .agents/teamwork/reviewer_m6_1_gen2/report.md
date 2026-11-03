# Review & Adversarial Stress-Test Report: Doctor Portal Surface (Milestone M6)

**Reviewer**: Reviewer M6-1 (Doctor Portal UI, Safety Banner & A11y Reviewer)  
**Target Milestone**: M6 (Doctor Portal Surface)  
**Parent Conversation ID**: `a0698e01-4167-4648-9a8b-05be5311997c`  
**Date**: 2026-11-02  

---

## 1. Review Summary

**Verdict**: **REQUEST_CHANGES**

Milestone M6 presents an impressive, comprehensive implementation of the Doctor Portal UI, Optimistic Concurrency Control, patient search classification, and appointment workflows. However, rigorous inspection identified **one Critical Non-Negotiable policy violation (N10: prohibited use of `any`)**, **one Major UI/Safety Banner occlusion defect (violating N2 during window scrolling due to `sticky top-0` collision with the global 64px header)**, and **multiple sub-44px touch targets violating accessibility guidelines**.

---

## 2. Findings

### [Critical] Finding 1: Explicit Violation of Non-Negotiable N10 (`any` types in source code)
- **What**: The TypeScript `any` type was explicitly introduced in multiple locations within the doctor portal codebase.
- **Where**:
  1. `src/components/doctor/doctor-workspace.tsx`, Line 123:
     ```typescript
     onClick={() => setTab(t.id as any)}
     ```
  2. `src/app/portal/doctor/actions.ts`, Line 55:
     ```typescript
     function mapRow(r: any): PatientSearchResult
     ```
  3. `src/app/portal/doctor/actions.ts`, Line 204:
     ```typescript
     const list: DoctorAppointmentListItem[] = (data || []).map((row: any) => {
     ```
- **Why**: `AGENTS.md` Section 5 defines Non-Negotiable N10:
  > *"N10. No `any`, no @ts-ignore/@ts-expect-error without a written reason, no non-null assertions on external data. Validate every form field and URL parameter with zod."*  
  And Section 5 states: *"Non-negotiables (breaking any = failed task)"*.  
  These occurrences bypass TypeScript strict type checking and directly breach project rules.
- **Suggestion**:
  - In `doctor-workspace.tsx`: type the tabs array explicitly with `id: 'clinical' | 'appointments' | 'overview'` or type `t.id` as `'clinical' | 'appointments' | 'overview'`.
  - In `actions.ts`: create concrete row types for the PostgREST join payloads (or use `Record<string, unknown>` with typed accessors) instead of `any`.

---

### [Major] Finding 2: Invariant N2 Banner Occlusion by Sticky Navigation Header
- **What**: `PatientSafetyBanner` uses `sticky top-0 z-30`, while the global App Header in `src/app/layout.tsx` is `sticky top-0 z-40 w-full glass-header` (height `h-16` / 64px).
- **Where**:
  - `src/components/doctor/patient-safety-banner.tsx`, Line 47:
    ```tsx
    <aside aria-label="Active Patient Safety Banner" className="sticky top-0 z-30 ...">
    ```
  - `src/app/layout.tsx`, Line 60:
    ```tsx
    <header className="sticky top-0 z-40 w-full glass-header">
    ```
- **Why**: During window scrolling on `/portal/doctor`, the Patient Safety Banner sticks at `top: 0` (`y = 0`). Because the global navigation header also sticks at `top: 0` with a higher z-index (`z-40` vs `z-30`), the top 64px of the safety banner slides underneath the glass header, partially or completely occluding patient name, code, blood group pill, and emergency contact. This directly undermines Non-Negotiable N2:
  > *"N2. The Doctor portal always shows a read-only banner with patient name, age, blood group and emergency contact while editing clinical data."*
- **Suggestion**:
  Update `PatientSafetyBanner` positioning class to `sticky top-16 z-30` (or `sticky top-[64px] z-30`) so it sticks immediately below the 64px global navigation bar when scrolled.

---

### [Major] Finding 3: Sub-44px Touch Targets Across Interactive Elements
- **What**: Several interactive buttons in the Doctor Portal fail the mandatory 44px minimum touch target requirement (WCAG 2.1 AA / Apple HIG / `AGENTS.md` Section 6 / Rule 01).
- **Where**:
  1. `src/components/doctor/patient-search-bar.tsx`, Line 147: Clear search button has `h-8 w-8` (32x32px).
  2. `src/components/doctor/clinical-record-editor.tsx`, Line 25: Condition & allergy tag removal button has `h-4 w-4` (16x16px).
  3. `src/components/doctor/appointment-manager.tsx`, Line 115: Filter tab buttons have `min-h-[36px]`.
  4. `src/components/doctor/doctor-workspace.tsx`, Line 125: Workspace navigation tabs have `min-h-[36px]`.
- **Why**: `AGENTS.md` Section 6 mandates: *"44px minimum touch target (56px for the emergency call button)"*. Sub-44px targets cause mis-taps on touchscreens, especially in high-stress clinical workflows.
- **Suggestion**:
  - Expand clear button tap area to `min-h-[44px] min-w-[44px]` (or use negative margins / larger padding container).
  - Expand tag removal hit area or provide a dedicated accessible removal control with `min-h-[44px] min-w-[44px]`.
  - Set tab buttons to `min-h-[44px] h-[44px]` with proper padding.

---

### [Minor] Finding 4: Superficial Verification Check in `scripts/verify_m6.py`
- **What**: Test 34 (`A11Y-01-TOUCH-TARGETS`) in `scripts/verify_m6.py` verified touch targets via a naive substring check (`"min-h-[44px]" in contents[...]`).
- **Where**: `scripts/verify_m6.py`, Line 329:
  ```python
  p34 = "min-h-[44px]" in contents["banner"] and "min-h-[44px]" in contents["search"] and "min-h-[44px]" in contents["editor"]
  ```
- **Why**: This check self-certified compliance because the input fields had `min-h-[44px]`, while overlooking that the clear search button was 32px and tag deletion buttons were 16px.
- **Suggestion**:
  Update test 34 to audit interactive buttons explicitly or check that all `<button>` elements enforce `>= 44px`.

---

### [Minor] Finding 5: Native `window.confirm` in Appointment Cancellation
- **What**: `src/components/doctor/appointment-manager.tsx`, Line 72 uses `window.confirm('Cancel this scheduled consultation?')`.
- **Where**: `src/components/doctor/appointment-manager.tsx`, Line 72.
- **Why**: Native browser alert dialogs are synchronous, block the browser thread, cannot be styled per Apple design tokens, and can be suppressed by browsers.
- **Suggestion**:
  Replace `window.confirm` with the existing accessible `<Modal>` component with Confirm/Cancel buttons.

---

## 3. Verified Claims

| # | Claim | Verification Method | Status | Notes |
|---|---|---|---|---|
| 1 | File Character Limits (< 12,000 chars) | `python scripts/audit.py` & character count audit | **PASS** | `clinical-record-editor.tsx` (11,976), `actions.ts` (11,963), `doctor-workspace.tsx` (11,864). All strictly under 12k chars. |
| 2 | M6 Test Suite (37 Checks) | `python scripts/verify_m6.py` | **PASS** | 37/37 tests passed. |
| 3 | M5 Regression Suite (74 Checks) | `python scripts/verify_m5.py` | **PASS** | 74/74 tests passed. |
| 4 | M4 Regression Suite (51 Checks) | `python scripts/verify_m4.py` | **PASS** | 51/51 tests passed. |
| 5 | Non-Negotiable N3/N4 Server Auth | Code inspection of `actions.ts` & `page.tsx` | **PASS** | Calls `supabase.auth.getUser()`, never `getSession()`. Zero `service_role` leaks. |
| 6 | DECISIONS D1 Pending Gate | Code inspection of `page.tsx` & `pending/page.tsx` | **PASS** | Pending doctors redirected to pending page with exact D1 notice. |
| 7 | Patient Safety Banner Elements (N2) | Code inspection of `patient-safety-banner.tsx` | **PASS** | Renders Name, Code, Age, BloodGroupPill, ICE Name & Phone, verified status badge. Strictly 0 input/textarea elements. |
| 8 | Phone Sanitization (Rule 02 & Rule 6) | Inspection of `sanitizeTel` in `src/lib/utils.ts` | **PASS** | Strips non-digits, preserves leading `+`, outputs standard `tel:` protocol. |
| 9 | Optimistic Concurrency Control (OCC) | Code inspection of `actions.ts` & `clinical-record-editor.tsx` | **PASS** | Updates on `expectedUpdatedAt`. Stale updates trap conflict, render non-dismissible alert with Reload CTA. |
| 10 | Unverified Baseline Verification (D7) | Code inspection of `clinical-record-editor.tsx` | **PASS** | Allows saving unedited baseline (`canSave = isDirty || !isVerified`) to trigger physician verification stamp. |
| 11 | Search Classification & Escaping (D14) | Inspection of `actions.ts` & `patient-search-bar.tsx` | **PASS** | Classifies code, UUID, phone, and name. Escapes SQL & PostgREST delimiters. 300ms debounce. Max 20 results. |
| 12 | Zero Raw Hex Tokens (Rule 01) | Regex scan `#[0-9a-fA-F]{3,6}` across `doctor` components and pages | **PASS** | Zero raw hex in JSX classes. Pure token usage. |
| 13 | Mobile & Desktop Layout | Responsive design class inspection | **PASS** | Uses `flex-col md:flex-row`, `sm:grid-cols-*`, responsive paddings matching Rule 01. |

---

## 4. Adversarial Challenge & Stress-Test Results

### Challenge 1: Window Scroll Occlusion of Safety Banner
- **Scenario**: Doctor opens patient record, navigates to "Clinical Records" tab, and scrolls down through long lists of chronic conditions, medications, and surgeries.
- **Observed Behavior**: Because `layout.tsx` has a global sticky header at `top: 0` (`h-16`, `z-40`), and `PatientSafetyBanner` is set to `sticky top-0 z-30`, the safety banner scrolls directly beneath the header. The patient's name, code, blood group, and emergency contact disappear behind the header.
- **Severity**: **HIGH** (Violates invariant N2).
- **Mitigation**: Adjust banner position to `sticky top-16 z-30`.

### Challenge 2: Accidental Mis-taps on Mobile Touchscreens
- **Scenario**: Doctor on an iPad or mobile device attempts to delete an allergy or clear the search input.
- **Observed Behavior**: The clear button is only 32x32px and the tag delete button is 16x16px. Surrounding text or input fields receive unintended touches.
- **Severity**: **MEDIUM** (Violates accessibility touch target baseline).
- **Mitigation**: Provide 44px minimum bounding box or padding around interactive controls.

### Challenge 3: Type Safety Bypass via `any`
- **Scenario**: Database schema evolutions in PostgREST joins or changes to workspace tab states.
- **Observed Behavior**: Using `any` in `mapRow` and `getDoctorAppointmentsAction` prevents TypeScript compiler from detecting missing or renamed joined fields at build time.
- **Severity**: **HIGH** (Direct Non-Negotiable N10 violation).
- **Mitigation**: Replace all `any` occurrences with proper types.

---

## 5. Required Actions for Approval

1. **Eliminate All `any` Types (N10)**:
   - `src/components/doctor/doctor-workspace.tsx` (Line 123): Type `tab` properly without `as any`.
   - `src/app/portal/doctor/actions.ts` (Lines 55 & 204): Provide explicit TypeScript interfaces for database join query rows.
2. **Fix Sticky Banner Offset (N2)**:
   - `src/components/doctor/patient-safety-banner.tsx` (Line 47): Change `sticky top-0 z-30` to `sticky top-16 z-30` so the banner remains fully visible below the global 64px header during scroll.
3. **Remediate Sub-44px Touch Targets**:
   - `src/components/doctor/patient-search-bar.tsx` (Line 147): Expand clear button touch target to >= 44px.
   - `src/components/doctor/clinical-record-editor.tsx` (Line 25): Ensure tag deletion button meets 44px touch target.
   - `src/components/doctor/appointment-manager.tsx` (Line 115) & `doctor-workspace.tsx` (Line 125): Ensure tab buttons meet 44px height.
4. **Update `scripts/verify_m6.py`**:
   - Update banner check and touch target check to verify `top-16` and ensure no sub-44px buttons exist.

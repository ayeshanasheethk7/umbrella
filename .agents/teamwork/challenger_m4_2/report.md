# Adversarial Stress Test & Verification Report: Milestone M4

**Agent**: Challenger M4-2 (`teamwork_challenger` / critic)  
**Workspace**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\challenger_m4_2`  
**Target Milestone**: M4 (Scaffolding, Supabase SSR Suite, Real Auth Surfaces, App Shell, Shared UI Primitives)  
**Date**: 2026-11-01T20:25:00Z  
**Verdict**: **REQUEST_CHANGES**  

---

## 1. Challenge Summary

**Overall Risk Assessment**: **HIGH**

While Worker M4 successfully established the baseline Next.js 14 / TypeScript scaffolding, implemented zero-mock Supabase authentication calls (`signInWithPassword`, `signUp`, and `exchangeCodeForSession`), and avoided `service_role` leaks (N4) and table access on the anon role (N1), rigorous adversarial stress testing uncovered **16 distinct defects** (7 High, 8 Medium, 1 Low), including non-negotiable accessibility and security violations:

1. **Touch Target Size Violations (AGENTS.md Section 6)**: `button.tsx` defines a 36px size (`size="sm"`), `layout.tsx` hardcodes 36px buttons on primary navigation actions (Sign In, Sign Up, Sign Out), and `modal.tsx` uses a 28px close button target.
2. **Missing Keyboard Focus Trap in Modal (`modal.tsx`)**: Claimed as present in worker's handoff, but completely absent in code. Focus escapes to background DOM.
3. **Doctor Approval Gating Bypass in Route Middleware (`middleware.ts:66`)**: Middleware checks `role !== 'doctor'` but fails to check `doctor_status === 'approved'`, permitting pending doctors into `/portal/doctor` in violation of DECISIONS D1.
4. **Phone Validation Gaps (`schemas.ts`)**: Phone numbers are validated only with `min(7)` without regex, allowing arbitrary injection strings, XSS payloads, and non-phone characters.
5. **Array Items in `clinicalRecordSchema` Accept Empty Strings**: Array items lack `.min(1)`, allowing `[""]` which renders empty badges in UI.
6. **Lenient Surgery Year Schema**: `surgeryItemSchema` allows arbitrary strings of length >= 4 (e.g. `"abcd"`, `"-999"`, `"year"`).
7. **Unbounded Input Lengths (DoS / ReDoS)**: Passwords lack `.max()` constraints, exposing password hashing to CPU exhaustion attacks.
8. **Mobile Shell Navigation Dead-End (`layout.tsx`)**: Header navigation links are hidden on mobile with `hidden md:flex` with no mobile drawer or hamburger alternative.
9. **`sanitizeTel()` Edge Case**: Inputs like `"+"` or `"+abc"` produce invalid `href="tel:+"` links.

---

## 2. Granular Empirical Challenges

### [High] Challenge 1: Touch Target Violations Below 44px (AGENTS.md Section 6)

- **Assumption Challenged**: All UI buttons and interactive targets comply with the 44px minimum touch target baseline.
- **Attack Scenario**: Mobile first responders or users operating on touchscreens tap header actions, modal dismiss buttons, or small buttons with gloved hands or under stress.
- **Direct Observations**:
  - `src/components/ui/button.tsx:50`: `sm: 'h-[36px] min-h-[36px] px-3.5 py-1 text-xs'` defines a 36px touch target.
  - `src/app/layout.tsx:128, 140, 146`: Primary auth and session actions are hardcoded with `h-[36px] min-h-[36px]`:
    - Sign Out button: `inline-flex h-[36px] min-h-[36px]`
    - Sign In link: `inline-flex h-[36px] min-h-[36px]`
    - Sign Up link: `inline-flex h-[36px] min-h-[36px]`
  - `src/components/ui/modal.tsx:91-98`: Modal close button has `p-1` wrapping a 20px icon (`h-5 w-5`), producing a total tap box of only 28px x 28px.
- **Blast Radius**: Fails WCAG 2.5.5 and AGENTS.md Section 6 ("Accessibility baseline: 44px minimum touch target (56px for the emergency call button)"). High risk of mis-taps on mobile devices.
- **Recommended Mitigation**:
  - In `button.tsx`, ensure `sm` has a minimum bounding box of 44px (e.g. `min-h-[44px]`).
  - In `layout.tsx`, change header links/buttons to `min-h-[44px] h-[44px]`.
  - In `modal.tsx`, update close button to `p-3` or `min-h-[44px] min-w-[44px] flex items-center justify-center`.

---

### [High] Challenge 2: Missing Keyboard Focus Trap in Modal (`modal.tsx`)

- **Assumption Challenged**: `modal.tsx` provides an "accessible focus trap" as asserted in `worker_m4/handoff.md` Section 1.5.
- **Attack Scenario**: A keyboard-only user or screen reader user opens a modal dialog and presses `Tab`. Instead of cycling within the modal's interactive controls, focus escapes into the hidden background page.
- **Direct Observations**:
  - `src/components/ui/modal.tsx:26-45`: `dialogRef` is initialized (`useRef<HTMLDivElement>(null)`), but lines 28–44 only register an `Escape` key listener on `window`. There is **zero** `Tab` key handling, zero query of focusable elements (`button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])`), zero focus lock, and no focus restoration to the active trigger on dismiss.
- **Blast Radius**: Severe accessibility barrier for keyboard and screen reader navigation, violating ARIA modal dialog specifications (WAI-ARIA 1.2 Modal Dialog Pattern).
- **Recommended Mitigation**: Implement an active `keydown` handler on `dialogRef` that intercepts `Tab` / `Shift+Tab` and wraps focus within the first and last focusable elements, and auto-focuses the first interactive element upon open.

---

### [High] Challenge 3: Unapproved Doctor Authorization Bypass in Middleware (`middleware.ts:66`)

- **Assumption Challenged**: `middleware.ts` enforces DECISIONS D1 ("All doctor privileges (RLS, proxy, UI) require doctor_status='approved'").
- **Attack Scenario**: A newly self-registered physician logs in. Their account has `role = 'doctor'` and `doctor_status = 'pending'`. The physician navigates to `/portal/doctor`.
- **Direct Observations**:
  - `src/lib/supabase/middleware.ts:60-71`:
    ```typescript
    const { data: account } = await supabase
      .from('accounts')
      .select('role, doctor_status')
      .eq('id', user.id)
      .single();

    if (!account || account.role !== 'doctor') {
      const redirectUrl = request.nextUrl.clone();
      redirectUrl.pathname = '/portal/patient';
      return NextResponse.redirect(redirectUrl);
    }
    ```
  - The middleware selects `doctor_status`, but **never validates it**. A pending doctor with `account.role === 'doctor'` is granted entry through the middleware into `/portal/doctor`.
  - In `src/app/(auth)/login/page.tsx:67-72`, the login redirect lands all doctors on `/portal/doctor` without inspecting `doctor_status`.
- **Blast Radius**: Pending, unverified accounts reach clinical portal views without administrative vetting.
- **Recommended Mitigation**:
  In `middleware.ts`, add verification:
  ```typescript
  if (!account || account.role !== 'doctor') {
    return NextResponse.redirect(new URL('/portal/patient', request.url));
  }
  if (account.doctor_status !== 'approved') {
    return NextResponse.redirect(new URL('/signup?status=pending', request.url));
  }
  ```

---

### [High] Challenge 4: Arbitrary Input Permitted in Phone Number Schemas (`schemas.ts`)

- **Assumption Challenged**: Zod schemas validate phone numbers as legitimate telephone contacts.
- **Attack Scenario**: An attacker submits malicious strings or non-numeric data into `contactPhone` or `emergencyContactPhone`.
- **Direct Observations**:
  - `src/lib/schemas.ts:50, 64, 90`:
    ```typescript
    contactPhone: z.string().trim().min(7, 'Please provide a valid contact phone number'),
    emergencyContactPhone: z.string().trim().min(7, 'Emergency contact phone number is required'),
    ```
  - Empirical execution of `scripts/test_adversarial_payloads.py` verified that payloads such as:
    - `<script>alert(1)</script>` (25 chars) -> **Accepted**
    - `'; DROP TABLE accounts; --` (26 chars) -> **Accepted**
    - `NOT-A-PHONE-NUMBER` (18 chars) -> **Accepted**
    - `+++++++` (7 chars) -> **Accepted**
  - When passed into emergency triage cards and fed into `sanitizeTel()`, an alphabetic payload like `"NOT-A-PHONE"` is stripped of all characters, rendering `<a href="tel:">` (a completely broken call link during a life-or-death roadside emergency).
- **Blast Radius**: Compromises phone data integrity, creates broken emergency dialing links, and exposes doctor search queries to unescaped injection strings.
- **Recommended Mitigation**: Validate phone numbers with a strict regex requiring at least 7 to 15 digits with optional standard phone formatting characters:
  ```typescript
  export const phoneSchema = z
    .string()
    .trim()
    .regex(/^\+?[0-9\s\-().]{7,20}$/, 'Please enter a valid phone number (at least 7 digits)');
  ```

---

### [Medium] Challenge 5: Empty Strings Permitted in Clinical Records Arrays (`schemas.ts:142, 145`)

- **Assumption Challenged**: `clinicalRecordSchema` ensures clinical conditions and allergies contain meaningful data.
- **Attack Scenario**: A user submits `medicalConditions = ["", "   "]` or `allergies = [""]`.
- **Direct Observations**:
  - `src/lib/schemas.ts:142, 145`:
    ```typescript
    medicalConditions: z.array(z.string().trim()).default([]),
    allergies: z.array(z.string().trim()).default([]),
    ```
  - In contrast, `baselineSubmissionSchema` at line 154 enforces `.min(1)`:
    ```typescript
    conditions: z.array(z.string().trim().min(1)).default([]),
    allergies: z.array(z.string().trim().min(1)).default([]),
    ```
  - Without `.min(1)` in `clinicalRecordSchema`, empty strings pass validation, causing blank alert boxes and empty condition pill renders.
- **Recommended Mitigation**: Update to `z.array(z.string().trim().min(1, 'Item cannot be empty')).default([])`.

---

### [Medium] Challenge 6: Lenient Surgery Year Validation (`schemas.ts:137`)

- **Assumption Challenged**: Surgery items validate valid calendar years.
- **Direct Observations**:
  - `src/lib/schemas.ts:137`:
    ```typescript
    year: z.union([z.number().int().min(1900).max(2100), z.string().trim().min(4)]),
    ```
  - Payloads like `"DROP"`, `"year"`, `"-999"`, `"invalid"` satisfy `min(4)` and pass validation.
- **Recommended Mitigation**: Enforce 4-digit numeric pattern:
  ```typescript
  year: z.union([
    z.number().int().min(1900).max(2100),
    z.string().trim().regex(/^(19|20)\d{2}$/, 'Year must be a 4-digit year between 1900 and 2099')
  ]),
  ```

---

### [Medium] Challenge 7: Unbounded Input Lengths (DoS / Password Hashing Exhaustion)

- **Assumption Challenged**: Forms restrict input sizes to prevent DoS.
- **Direct Observations**:
  - `loginSchema`, `patientSignupSchema`, and `doctorSignupSchema` specify `password: z.string().min(8)` with **no `.max()` limit**. Submitting a 1MB password payload causes high CPU consumption during bcrypt hashing.
  - `fullName`, `emergencyContactName`, `emergencyContactRelation`, `medicalLicenseNumber`, `specialization`, and `residentialAddress` lack `.max()` constraints.
- **Recommended Mitigation**: Add `.max(128)` to `password` and `.max(100)` / `.max(500)` to string profile fields.

---

### [Medium] Challenge 8: Mobile Header Navigation Dead-End (`layout.tsx:81`)

- **Assumption Challenged**: App shell navigation functions seamlessly on mobile viewports (375x667).
- **Direct Observations**:
  - `src/app/layout.tsx:81`: `<nav className="hidden md:flex items-center gap-6 text-sm font-medium">` hides the navigation links (`Emergency Lookup`, `Patient Portal`, `Doctor Portal`) below `768px`.
  - There is no mobile drawer, hamburger menu button, or bottom navigation bar, leaving mobile users unable to navigate to portal pages directly from the header.
- **Recommended Mitigation**: Add a responsive mobile menu trigger or bottom navigation bar for mobile viewports.

---

### [Medium] Challenge 9: `sanitizeTel()` Edge Case Producing Invalid `tel:+` Links (`utils.ts:68`)

- **Assumption Challenged**: `sanitizeTel()` always generates valid telephone links or empty strings.
- **Direct Observations**:
  - `src/lib/utils.ts:68-74`:
    ```typescript
    export function sanitizeTel(phone: string): string {
      if (!phone) return '';
      const trimmed = phone.trim();
      const hasLeadingPlus = trimmed.startsWith('+');
      const digits = trimmed.replace(/\D/g, '');
      return hasLeadingPlus ? `+${digits}` : digits;
    }
    ```
  - When `phone` is `"+"` or `"+abc"`, `hasLeadingPlus` is `true` while `digits` is `""`. It returns `"+"`, producing `<a href="tel:+">`, which fails dialer URI validation.
- **Recommended Mitigation**: Return `fallback` or empty string if `digits.length === 0`:
  ```typescript
  export function sanitizeTel(phone: string): string {
    if (!phone) return '';
    const trimmed = phone.trim();
    const hasLeadingPlus = trimmed.startsWith('+');
    const digits = trimmed.replace(/\D/g, '');
    if (!digits) return '';
    return hasLeadingPlus ? `+${digits}` : digits;
  }
  ```

---

## 3. Stress Test Results Summary

| Test Vector / Scenario | Target Module | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|---|
| `sm` Button Size | `button.tsx` | Height >= 44px | `h-[36px] min-h-[36px]` | **FAIL** |
| Emergency Button Size | `button.tsx` | Height >= 56px | `h-[56px] min-h-[56px]` | **PASS** |
| Layout Header Buttons | `layout.tsx` | Height >= 44px | `h-[36px] min-h-[36px]` (3 buttons) | **FAIL** |
| Modal Close Button | `modal.tsx` | Touch target >= 44px | `p-1` with 20px icon = 28px | **FAIL** |
| Modal Keyboard Focus Trap | `modal.tsx` | Traps Tab key inside modal | No Tab handling, focus escapes | **FAIL** |
| Pending Doctor Route Guard | `middleware.ts` | Reject unapproved doctor | Permits pending doctor | **FAIL** |
| Phone Number Format | `schemas.ts` | Enforce phone regex | Accepts arbitrary string >= 7 chars | **FAIL** |
| Surgery Year Validation | `schemas.ts` | 4-digit numeric year | Accepts arbitrary string >= 4 chars | **FAIL** |
| Empty String in Arrays | `schemas.ts` | Reject empty strings | Accepts `[""]` in clinical record | **FAIL** |
| Password Upper Bound | `schemas.ts` | Limit max length (DoS) | Unbounded password allowed | **FAIL** |
| Mobile Navigation Menu | `layout.tsx` | Mobile-accessible links | Links hidden on mobile (`hidden md:flex`) | **FAIL** |
| `sanitizeTel("+")` | `utils.ts` | Return empty or valid URI | Returns `"+"` -> `tel:+` | **FAIL** |
| Open Redirect Matrix (19 vectors) | `utils.ts` | Reject protocols & slashes | All 19 malicious vectors sanitized | **PASS** |
| Input Base Font Size | `input.tsx` | `text-base` (16px) | `text-base` present | **PASS** |
| Badge Icon + Text Pairing | `badge.tsx` | Never color alone | Default icons paired with text | **PASS** |
| Emergency Triage Projection (N1) | `schemas.ts` | Zero residential / spouse | No residential or spouse fields | **PASS** |
| Service Role Secret Scan (N4) | `src/**/*` | Zero `service_role` | Zero matches | **PASS** |

---

## 4. Unchallenged Areas

- **Live Supabase Cookie Round-Trip**: Static analysis and unit simulation confirmed compliance with `@supabase/ssr` `getAll`/`setAll` specifications, but live cookie round-trips require actual Supabase network infrastructure.
- **Downstream Domain Views**: Detailed portal layouts for `/portal/patient` (Milestone M5), `/portal/doctor` (Milestone M6), and `/emergency/[token]` (Milestone M7) are designated for subsequent milestones.

---

## 5. Verification Commands for Worker M4

To independently verify all findings and validate remediations:

```powershell
# 1. Run empirical adversarial test harness
python scripts/challenger_m4_ui.py

# 2. Run adversarial payload demonstration
python scripts/test_adversarial_payloads.py
```

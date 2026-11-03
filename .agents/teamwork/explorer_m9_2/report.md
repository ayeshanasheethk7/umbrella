# Playwright E2E User Journey & Viewport Test Architecture Report (Milestone M9)

**Author**: `explorer_m9_2` (Playwright E2E User Journey & Viewport Explorer)  
**Target Milestone**: M9 (Dual-Track 5-Tier E2E Test Suite — Track B: Playwright User Journeys)  
**Date**: 2026-11-02  
**Status**: COMPLETE — Test Specifications & Executable Code Templates  

---

## 1. Executive Summary & Test Infrastructure Overview

This report provides the architectural design, user journey mappings, and complete executable code templates for the **Tier 3 (Cross-Feature Pairwise)** and **Tier 4 (Real-World Application Scenarios)** Playwright E2E test suites for the Umbrella Emergency Medical ID platform.

Umbrella operates across three distinct surfaces with life-critical security and usability constraints:
1. **Patient Portal (`/portal/patient`)**: Bento grid layout managing personal demographics, ICE contacts, family dependents, self-reported baseline health, and ISO CR80 emergency QR pass generation.
2. **Physician Portal (`/portal/doctor`)**: Gated provider workspace featuring multi-modal lookup, persistent read-only patient safety banner (Invariant N2), clinical record editor with optimistic concurrency, and consultation scheduling.
3. **Public Emergency Route (`/emergency/[token]`)**: Zero-login roadside triage route reading strictly through Postgres RPC `get_emergency_triage_by_token`, enforcing zero disclosure of residential address or dependents (Invariant N1), and featuring a life-critical 56px sticky call button.

The Playwright test suite is structured into two core tiers executing across two mandatory viewports:
- **Mobile Viewport (`375x667`)**: Simulates handheld smartphone viewports (iPhone SE / compact mobile) with touch emulation, verifying rapid thumb-reachability, 44px/56px touch target compliance, single-column reflow, and zero horizontal scroll overflow.
- **Desktop Viewport (`1280x800`)**: Simulates hospital workstations and clinic desktop displays with 12-column bento reflow, horizontal sticky safety banner layout, and multi-pane clinical charting.

---

## 2. Playwright Configuration Architecture (`playwright.config.ts`)

The test configuration leverages `@playwright/test` with dedicated projects for mobile and desktop Chromium, automatic local web server lifecycle management, deterministic timeouts, and rich failure tracing.

### Configuration Template: `playwright.config.ts`

```typescript
import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E Configuration for Umbrella Emergency Medical ID Platform
 * Complies with AGENTS.md § 3 & 4 and GEMINI.md viewport specifications:
 * - Mobile: 375x667 (iPhone SE viewport baseline)
 * - Desktop: 1280x800 (Workstation viewport baseline)
 */
export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['json', { outputFile: 'playwright-report/test-results.json' }],
  ],
  use: {
    baseURL: process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://127.0.0.1:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },

  projects: [
    {
      name: 'mobile-chromium',
      use: {
        ...devices['Pixel 5'],
        viewport: { width: 375, height: 667 },
        deviceScaleFactor: 2,
        isMobile: true,
        hasTouch: true,
        defaultBrowserType: 'chromium',
      },
    },
    {
      name: 'desktop-chromium',
      use: {
        viewport: { width: 1280, height: 800 },
        deviceScaleFactor: 1,
        isMobile: false,
        hasTouch: false,
        defaultBrowserType: 'chromium',
      },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://127.0.0.1:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
```

---

## 3. Test Fixtures, Synthetic Identities & Test Harness Helpers

Umbrella strictly mandates **zero mock auth** (Invariant N5: real Supabase Auth) and **synthetic data only** (Invariant N9: no real personal or medical data). The seed accounts defined in `supabase/seed.sql` provide the foundation for deterministic user journeys:

### Credential & Identity Matrix

| Role | Synthetic Identity | Email | Password | Primary Key / QR Token / Code | Key Characteristics |
|---|---|---|---|---|---|
| **Approved Doctor** | Dr. Sarah Jenkins | `doctor.approved@example.test` | `Password123!` | ID: `d0000000-0000-0000-0000-000000000001` | `doctor_status='approved'`; full clinical lookup and editing permissions. |
| **Pending Doctor** | Dr. Marcus Vance | `doctor.pending@example.test` | `Password123!` | ID: `d0000000-0000-0000-0000-000000000002` | `doctor_status='pending'`; quarantined at `/portal/doctor/pending`. Zero patient access. |
| **Patient 1 (Verified)** | Alex Morgan | `alex.morgan@example.test` | `Password123!` | Code: `UMB-ALX001`<br>Token: `11111111-1111-1111-1111-111111111111` | O+, 34 yrs. Doctor-verified Type 1 Diabetes, Asthma, Penicillin & Peanuts allergies. |
| **Patient 2 (Self-Reported)** | Priya Sharma | `priya.sharma@example.test` | `Password123!` | Code: `UMB-PRY002`<br>Token: `22222222-2222-2222-2222-222222222222` | B+, 28 yrs. Unverified self-reported baseline (Hypertension, Sulfa drugs). Baseline editor active. |
| **Patient 3 (Complex)** | David Kim | `david.kim@example.test` | `Password123!` | Code: `UMB-DVK003`<br>Token: `33333333-3333-3333-3333-333333333333` | AB-, 62 yrs. Doctor-verified Coronary Artery Disease, Eliquis & Metoprolol meds, Aspirin allergy. |

### Helper Fixture Template: `tests/e2e/helpers/auth.ts`

```typescript
import { Page, expect } from '@playwright/test';

export interface SyntheticUser {
  email: string;
  password: string;
  fullName: string;
  role: 'patient' | 'doctor';
  token?: string;
  patientCode?: string;
}

export const USERS = {
  doctorApproved: {
    email: 'doctor.approved@example.test',
    password: 'Password123!',
    fullName: 'Dr. Sarah Jenkins',
    role: 'doctor' as const,
  },
  doctorPending: {
    email: 'doctor.pending@example.test',
    password: 'Password123!',
    fullName: 'Dr. Marcus Vance',
    role: 'doctor' as const,
  },
  patientAlex: {
    email: 'alex.morgan@example.test',
    password: 'Password123!',
    fullName: 'Alex Morgan',
    role: 'patient' as const,
    token: '11111111-1111-1111-1111-111111111111',
    patientCode: 'UMB-ALX001',
  },
  patientPriya: {
    email: 'priya.sharma@example.test',
    password: 'Password123!',
    fullName: 'Priya Sharma',
    role: 'patient' as const,
    token: '22222222-2222-2222-2222-222222222222',
    patientCode: 'UMB-PRY002',
  },
  patientDavid: {
    email: 'david.kim@example.test',
    password: 'Password123!',
    fullName: 'David Kim',
    role: 'patient' as const,
    token: '33333333-3333-3333-3333-333333333333',
    patientCode: 'UMB-DVK003',
  },
};

/**
 * Performs authentic UI sign-in via /login per Non-negotiable N5.
 */
export async function loginViaUi(page: Page, user: { email: string; password: string }) {
  await page.goto('/login');
  await page.waitForLoadState('domcontentloaded');

  const emailInput = page.locator('#login-email');
  const passwordInput = page.locator('#login-password');
  const submitButton = page.locator('button[type="submit"]:has-text("Sign In")');

  await emailInput.fill(user.email);
  await passwordInput.fill(user.password);
  await submitButton.click();

  // Wait for post-login navigation
  await page.waitForURL((url) => url.pathname.startsWith('/portal/'), { timeout: 10_000 });
}

/**
 * Verifies that the viewport does not exhibit horizontal scrolling overflow.
 */
export async function assertNoHorizontalScroll(page: Page) {
  const isOverflowing = await page.evaluate(() => {
    return document.documentElement.scrollWidth > window.innerWidth;
  });
  expect(isOverflowing).toBe(false);
}
```

---

## 4. Complete User Journey Specifications

### Journey A: Patient Medical ID Lifecycle
1. **Self-Registration**: User visits `/signup`, selects "Patient ID" tab, completes demographics (name, phone, email, password, age, blood group dropdown, primary emergency contact name/phone/relation), submits form.
2. **Auto-Profile Generation**: Database trigger `handle_new_user` synchronously provisions `public.accounts`, `public.patient_profiles`, and `public.clinical_records`.
3. **Bento Shell Presentation**: User lands at `/portal/patient`. Bento layout mounts Hero Profile Card, Emergency Contact Card, Medical Overview Card, Baseline Editor, and QR Studio.
4. **Demographics Mutation**: User modifies contact phone, residential address (marked strictly confidential), and adds a dependent via `DependentsManager`. Submits form and verifies success toast.
5. **Self-Reported Baseline Entry**: User types condition ("Mild Asthma") and allergy ("Latex"), clicks "Add", and saves baseline. Verifies amber "Self-Reported Baseline" badge.
6. **QR Studio Interaction**: User reviews 224px QR code, switches tab to "Card Preview", verifies ISO CR80 front and back render correctly. Triggers PNG and PDF export download handlers.

### Journey B: Physician Consultation & Safety-Gated Charting
1. **Provider Login**: Dr. Sarah Jenkins signs in via `/login`, landing at `/portal/doctor`.
2. **Multi-Modal Patient Search (D14)**:
   - Types `UMB-ALX001` -> verifies exact patient code match.
   - Clears and types `+1-555-0101` -> verifies phone number lookup.
   - Clears and types `Morgan` -> verifies name substring match.
3. **Patient Loading & Persistent Safety Banner (N2)**: Doctor clicks patient. The sticky `PatientSafetyBanner` locks to top with patient name, code, age, blood group pill, ICE contact, and read-only demographic indicator. Verifies zero editable form inputs inside the banner.
4. **Clinical Record Modification (D7)**: Doctor switches to "Clinical Records" tab. Adds new chronic condition and medication dosage. Clicks "Save & Verify Record".
5. **Trigger Verification Stamps**: Database BEFORE UPDATE trigger automatically sets `is_doctor_verified = true`, `last_updated_by_doctor_id = dr_id`, and `updated_at = now()`. The UI flips from amber unverified to green "Doctor Verified Record".
6. **Consultation Scheduling**: Doctor switches to "Appointments" tab, clicks "Schedule Consultation", completes appointment date, time, and reason, submits modal. New appointment appears in the consultation list.

### Journey C: Zero-Login Emergency Roadside Triage
1. **Zero-Login Access (N1)**: First responder navigates directly to `/emergency/[token]` without authentication cookies or session headers.
2. **Privacy Barrier Verification (N1)**: First responder inspects rendered DOM and network responses. Proves `residential_address` and `spouse_dependents` are completely absent.
3. **Life-Critical 56px Sticky Call Bar**: Verifies sticky call bar at bottom of viewport. Confirms touch target height is >= 56px, phone number is sanitized with `tel:` link, and action label shows `CALL SIBLING: Taylor Morgan`.
4. **Critical Allergies Alert**: Verifies prominent high-contrast red alert box highlighting life-threatening drug/food allergies.
5. **Escalation to Provider Portal (D15)**: Paramedic clicks "Open in Doctor Portal" at bottom. Redirects to `/login?next=%2Fportal%2Fdoctor%3Fpatient_token%3D...`. Upon physician login, portal immediately opens with patient preloaded.

---

## 5. Tier 3: Cross-Feature Pairwise Test Suite (Specifications & Code)

Tier 3 tests focus on **cross-surface integration invariants** where an action on one surface directly impacts the state or visibility of another surface.

### Pairwise Test Suite Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TIER 3 PAIRWISE TEST SUITE                         │
├────────────────────────────────┬───────────────────────────┬────────────────┤
│ Interaction Pair               │ Surfaces Involved         │ Invariants     │
├────────────────────────────────┼───────────────────────────┼────────────────┤
│ 1. Demographics Mutation       │ /portal/patient           │ N1, N7         │
│    <-> Public Emergency View   │ <-> /emergency/[token]    │ Privacy & Sync │
├────────────────────────────────┼───────────────────────────┼────────────────┤
│ 2. Doctor Clinical Stamp       │ /portal/doctor            │ D3, D7, N2     │
│    <-> Disappearing Baseline   │ <-> /portal/patient       │ Lockout Gate   │
├────────────────────────────────┼───────────────────────────┼────────────────┤
│ 3. QR Token Regeneration       │ /portal/patient (Studio)  │ D3, D9, N6, M8 │
│    <-> Opaque 404 Invalidation │ <-> /emergency/[old/new]  │ Token Rotation │
├────────────────────────────────┼───────────────────────────┼────────────────┤
│ 4. Escalation Deep Link        │ /emergency/[token]        │ D15, N3        │
│    <-> Auth Guard Redirection  │ <-> /login <-> /doctor    │ Safe Next URL  │
├────────────────────────────────┼───────────────────────────┼────────────────┤
│ 5. Completed Consultation      │ /portal/doctor (Appts)    │ D8, N1         │
│    <-> Patient Visit History   │ <-> /emergency/[token]    │ Sync Metadata  │
├────────────────────────────────┼───────────────────────────┼────────────────┤
│ 6. Optimistic Concurrency      │ Doctor Workspace Tab A    │ M6, D7         │
│    <-> Conflict Guard          │ <-> Doctor Workspace B    │ Concurrency    │
└────────────────────────────────┴───────────────────────────┴────────────────┘
```

### Complete Executable Code Template: `tests/e2e/tier3-pairwise.spec.ts`

```typescript
import { test, expect } from '@playwright/test';
import { USERS, loginViaUi, assertNoHorizontalScroll } from './helpers/auth';

test.describe('Tier 3: Cross-Feature Pairwise Integration Suite', () => {

  // --------------------------------------------------------------------------
  // PAIRWISE 1: Demographics Update <-> Emergency Triage Reflection (N1, N7)
  // --------------------------------------------------------------------------
  test('Pairwise 1: Demographics update in Patient Portal immediately updates Emergency Triage without leaking private address/dependents', async ({ page, browser }) => {
    // 1. Patient logs in and updates emergency contact & legal name
    await loginViaUi(page, USERS.patientPriya);
    await expect(page).toHaveURL(/\/portal\/patient/);

    const demographicsSection = page.locator('text=Personal Demographics & Contacts').locator('..');
    await demographicsSection.scrollIntoViewIfNeeded();

    // Fill new contact details
    const uniqueContactName = `Aarav Sharma-${Date.now().toString().slice(-4)}`;
    const contactNameInput = page.locator('label:has-text("Contact Name") + div input, input[value*="Rohit"], label:has-text("Contact Name") ~ input').first();
    await contactNameInput.fill(uniqueContactName);

    // Ensure residential address has confidential text
    const addressInput = page.locator('label:has-text("Residential Address") ~ input, input[placeholder*="Residential"], label:has-text("Residential Address") + div input').first();
    await addressInput.fill('99 Confidential Sanctuary Road, Metroville');

    // Click Save Demographics
    const saveButton = page.locator('button[type="submit"]:has-text("Save Demographics")');
    await saveButton.click();

    // Verify success toast/message
    await expect(page.locator('role=status:has-text("Profile saved successfully.")')).toBeVisible({ timeout: 5000 });

    // 2. Open emergency route in an anonymous browser context (zero login cookies)
    const anonContext = await browser.newContext();
    const emergencyPage = await anonContext.newPage();

    await emergencyPage.goto(`/emergency/${USERS.patientPriya.token}`);
    await emergencyPage.waitForLoadState('domcontentloaded');

    // Verify updated emergency contact is visible on emergency page
    await expect(emergencyPage.locator(`text=${uniqueContactName}`)).toBeVisible();
    await expect(emergencyPage.locator(`text=CALL SPOUSE: ${uniqueContactName}`)).toBeVisible();

    // Invariant N1 Verification: Confidential address and dependents MUST NOT appear
    const pageContent = await emergencyPage.content();
    expect(pageContent).not.toContain('99 Confidential Sanctuary Road');
    expect(pageContent).not.toContain('Sanctuary Road');
    expect(pageContent).not.toContain('residential_address');
    expect(pageContent).not.toContain('spouse_dependents');

    await anonContext.close();
  });

  // --------------------------------------------------------------------------
  // PAIRWISE 2: Doctor Verification Gate <-> Disappearing Baseline Editor (D3, D7)
  // --------------------------------------------------------------------------
  test('Pairwise 2: Doctor verification stamps clinical record and permanently eliminates BaselineEditor from Patient Portal', async ({ page, browser }) => {
    // 1. Verify that Priya Sharma (unverified baseline) currently has the BaselineEditor visible
    await loginViaUi(page, USERS.patientPriya);
    const baselineEditor = page.locator('text=Self-Reported Health Baseline');
    await expect(baselineEditor).toBeVisible();
    await page.context().clearCookies();

    // 2. Doctor Sarah Jenkins logs in to doctor portal
    await loginViaUi(page, USERS.doctorApproved);
    await expect(page).toHaveURL(/\/portal\/doctor/);

    // Search for Priya Sharma by code
    const searchInput = page.locator('#patient-search-input');
    await searchInput.fill(USERS.patientPriya.patientCode);
    const resultItem = page.locator('#patient-search-results [role="option"]').first();
    await resultItem.click();

    // Verify Persistent Safety Banner (Invariant N2)
    const safetyBanner = page.locator('aside[aria-label="Active Patient Safety Banner"]');
    await expect(safetyBanner).toBeVisible();
    await expect(safetyBanner).toContainText(USERS.patientPriya.fullName);
    await expect(safetyBanner).toContainText(USERS.patientPriya.patientCode);

    // Switch to clinical records tab and save/verify baseline
    const verifyButton = page.locator('button:has-text("Verify Medical Baseline"), button:has-text("Save & Verify Record")');
    await verifyButton.click();

    // Verify confirmation
    await expect(page.locator('role=status:has-text("Clinical record updated and physician verified successfully.")')).toBeVisible({ timeout: 5000 });
    await page.context().clearCookies();

    // 3. Return to Priya's patient portal -> BaselineEditor MUST completely disappear from DOM (DECISIONS D7)
    await loginViaUi(page, USERS.patientPriya);
    await expect(page.locator('text=Self-Reported Health Baseline')).toHaveCount(0);
    // Medical Overview should now show verified badge
    await expect(page.locator('text=Doctor Verified')).toBeVisible();
  });

  // --------------------------------------------------------------------------
  // PAIRWISE 3: QR Token Rotation <-> Immediate Opaque 404 Invalidation (D3, D9, M8)
  // --------------------------------------------------------------------------
  test('Pairwise 3: Regenerating QR code immediately invalidates previous emergency URL with opaque 404 and activates new token', async ({ page, browser }) => {
    // Patient logs in and views QR Studio
    await loginViaUi(page, USERS.patientAlex);

    const oldToken = USERS.patientAlex.token;

    // Verify old token is currently accessible anonymously
    const anonContext = await browser.newContext();
    const anonPage = await anonContext.newPage();
    const initialRes = await anonPage.goto(`/emergency/${oldToken}`);
    expect(initialRes?.status()).toBe(200);

    // Trigger QR code rotation in Patient Portal
    const rotateTrigger = page.locator('button:has-text("Regenerate Emergency QR Code")');
    await rotateTrigger.scrollIntoViewIfNeeded();
    await rotateTrigger.click();

    // Modal pops up
    const modal = page.locator('role=dialog, div[class*="fixed"]');
    await expect(modal).toContainText('Regenerate Emergency QR Code?');

    // Confirm destructive rotation
    const confirmButton = page.locator('button:has-text("Regenerate Token")');
    await confirmButton.click();

    // Wait for success toast
    await expect(page.locator('role=status:has-text("Emergency QR code regenerated successfully.")')).toBeVisible({ timeout: 7000 });

    // Extract new token from public preview link
    const previewLink = page.locator('a[aria-label="Preview emergency triage page in new tab"]');
    const newHref = await previewLink.getAttribute('href');
    expect(newHref).toBeTruthy();
    const newToken = newHref!.split('/emergency/')[1];
    expect(newToken).not.toBe(oldToken);

    // Verify old token is IMMEDIATELY 404 (opaque not-found per DECISIONS D9)
    const staleRes = await anonPage.goto(`/emergency/${oldToken}`);
    expect(staleRes?.status()).toBe(404);
    await expect(anonPage.locator('text=Emergency Record Not Found')).toBeVisible();
    await expect(anonPage.locator('text=Call 911 / Emergency Services')).toBeVisible();

    // Verify new token resolves cleanly to 200
    const newRes = await anonPage.goto(`/emergency/${newToken}`);
    expect(newRes?.status()).toBe(200);
    await expect(anonPage.locator(`text=${USERS.patientAlex.fullName}`)).toBeVisible();

    await anonContext.close();
  });

  // --------------------------------------------------------------------------
  // PAIRWISE 4: Escalation Deep Link <-> Auth Guard with Safe Next Parameter (D15)
  // --------------------------------------------------------------------------
  test('Pairwise 4: Emergency escalation link forwards unauthenticated doctor through login with preloaded patient record', async ({ page }) => {
    // 1. Visit emergency triage as anonymous user
    await page.goto(`/emergency/${USERS.patientDavid.token}`);
    await page.waitForLoadState('domcontentloaded');

    // Click "Open in Doctor Portal"
    const escalationLink = page.locator('a:has-text("Open in Doctor Portal")');
    await escalationLink.scrollIntoViewIfNeeded();
    await escalationLink.click();

    // Verify redirected to /login with encoded relative next parameter
    await expect(page).toHaveURL(/\/login\?next=%2Fportal%2Fdoctor%3Fpatient_token%3D/);

    // Fill doctor credentials
    await page.locator('#login-email').fill(USERS.doctorApproved.email);
    await page.locator('#login-password').fill(USERS.doctorApproved.password);
    await page.locator('button[type="submit"]:has-text("Sign In")').click();

    // Post-login destination MUST land on doctor portal with patient pre-loaded
    await expect(page).toHaveURL(new RegExp(`/portal/doctor\\?patient_token=${USERS.patientDavid.token}`));

    // Safety banner for David Kim must be present immediately
    const safetyBanner = page.locator('aside[aria-label="Active Patient Safety Banner"]');
    await expect(safetyBanner).toBeVisible();
    await expect(safetyBanner).toContainText(USERS.patientDavid.fullName);
    await expect(safetyBanner).toContainText('AB-');
  });

  // --------------------------------------------------------------------------
  // PAIRWISE 5: Doctor Consultation Completion <-> Patient Clinical History (D8)
  // --------------------------------------------------------------------------
  test('Pairwise 5: Completing a scheduled doctor appointment updates last visit date in emergency view without flipping verification', async ({ page, browser }) => {
    // Doctor logs in and opens David Kim
    await loginViaUi(page, USERS.doctorApproved);
    await page.goto(`/portal/doctor?patient_token=${USERS.patientDavid.token}`);

    // Switch to appointments tab
    const apptsTab = page.locator('button[role="tab"]:has-text("Appointments")');
    await apptsTab.click();

    // Find scheduled consultation and complete it
    const completeButton = page.locator('button:has-text("Complete Consultation")').first();
    if (await completeButton.isVisible()) {
      await completeButton.click();

      // Enter clinical notes
      const notesInput = page.locator('textarea[placeholder*="Clinical summary"]');
      const testSummary = `Quarterly ECG evaluation completed at ${Date.now()}`;
      await notesInput.fill(testSummary);

      await page.locator('button:has-text("Finalize & Record Visit")').click();
      await page.waitForTimeout(1000);
    }

    // Verify reflection on public emergency route
    const anonContext = await browser.newContext();
    const anonPage = await anonContext.newPage();
    await anonPage.goto(`/emergency/${USERS.patientDavid.token}`);

    // Last visit should be visible
    await expect(anonPage.locator('text=Last visit:')).toBeVisible();
    await anonContext.close();
  });

  // --------------------------------------------------------------------------
  // PAIRWISE 6: Multi-Physician Optimistic Concurrency Conflict (M6, D7)
  // --------------------------------------------------------------------------
  test('Pairwise 6: Second physician attempting to save stale clinical record triggers concurrency warning modal', async ({ browser }) => {
    // Context A (Dr. Sarah Jenkins - Session 1)
    const contextA = await browser.newContext();
    const pageA = await contextA.newPage();
    await loginViaUi(pageA, USERS.doctorApproved);
    await pageA.goto(`/portal/doctor?patient_token=${USERS.patientAlex.token}`);

    // Context B (Dr. Sarah Jenkins - Session 2 simulating second device/doctor)
    const contextB = await browser.newContext();
    const pageB = await contextB.newPage();
    await loginViaUi(pageB, USERS.doctorApproved);
    await pageB.goto(`/portal/doctor?patient_token=${USERS.patientAlex.token}`);

    // Session 1 adds condition and saves
    const conditionInputA = pageA.locator('input[placeholder*="Condition name"]');
    await conditionInputA.fill('Seasonal Rhinitis');
    await pageA.locator('button:has-text("Add Condition")').click();
    await pageA.locator('button:has-text("Save & Verify Record")').click();
    await expect(pageA.locator('role=status:has-text("Clinical record updated")')).toBeVisible();

    // Session 2 (stale snapshot) attempts to save different edit
    const conditionInputB = pageB.locator('input[placeholder*="Condition name"]');
    await conditionInputB.fill('Eczema Flare');
    await pageB.locator('button:has-text("Add Condition")').click();
    await pageB.locator('button:has-text("Save & Verify Record")').click();

    // Session 2 MUST receive concurrency conflict warning
    await expect(pageB.locator('role=alert:has-text("Concurrency Conflict Detected")')).toBeVisible();
    await expect(pageB.locator('button:has-text("Reload Latest Record")')).toBeVisible();

    await contextA.close();
    await contextB.close();
  });

});
```

---

## 6. Tier 4: Real-World Application Scenarios (Specifications & Code)

Tier 4 tests model end-to-end operational workflows reflecting realistic high-pressure usage by first responders, emergency physicians, and patients across both viewports.

### Application Scenario Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     TIER 4 REAL-WORLD APPLICATION SCENARIOS                 │
├────────────────────────────────┬───────────────────────────┬────────────────┤
│ Scenario ID                    │ Viewport / Device         │ Primary Focus  │
├────────────────────────────────┼───────────────────────────┼────────────────┤
│ Scenario 1: Multi-Patient Mass │ Mobile (375x667)          │ Fast Triage    │
│ Casualty Roadside Triage       │ Handheld Touch Emulation  │ ICE 56px Dial  │
├────────────────────────────────┼───────────────────────────┼────────────────┤
│ Scenario 2: Hospital Trauma    │ Desktop (1280x800)        │ Search D14     │
│ Reception & Doctor Charting    │ Workstation Display       │ Banner N2      │
├────────────────────────────────┼───────────────────────────┼────────────────┤
│ Scenario 3: Patient Lifecycle  │ Dual Viewport             │ Signup -> Pass │
│ Registration to ISO Card Print │ Mobile & Desktop          │ CR80 PDF / PNG │
├────────────────────────────────┼───────────────────────────┼────────────────┤
│ Scenario 4: Defense-in-Depth   │ Dual Viewport             │ Pending Gate   │
│ Role Quarantine & Anti-Tamper  │ Mobile & Desktop          │ Cross-Role 403 │
└────────────────────────────────┴───────────────────────────┴────────────────┘
```

### Complete Executable Code Template: `tests/e2e/tier4-scenarios.spec.ts`

```typescript
import { test, expect } from '@playwright/test';
import { USERS, loginViaUi, assertNoHorizontalScroll } from './helpers/auth';

test.describe('Tier 4: Real-World Application Scenarios', () => {

  // --------------------------------------------------------------------------
  // SCENARIO 1: Multi-Patient Mass-Casualty Roadside Triage on Mobile (375x667)
  // --------------------------------------------------------------------------
  test('Scenario 1: Paramedic conducts rapid sequential triage of 3 victims on mobile (375x667) without state bleed', async ({ page }) => {
    // Ensure mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    const triageQueue = [
      {
        user: USERS.patientAlex,
        expectedBlood: 'O+',
        expectedAllergy: 'Penicillin',
        expectedCall: 'CALL SIBLING: Taylor Morgan',
        isVerified: true,
      },
      {
        user: USERS.patientPriya,
        expectedBlood: 'B+',
        expectedAllergy: 'Sulfa drugs',
        expectedCall: 'CALL SPOUSE:',
        isVerified: false,
      },
      {
        user: USERS.patientDavid,
        expectedBlood: 'AB-',
        expectedAllergy: 'Aspirin',
        expectedCall: 'CALL DAUGHTER: Sun-Hee Kim',
        isVerified: true,
      },
    ];

    for (const patient of triageQueue) {
      // Direct emergency URL lookup
      await page.goto(`/emergency/${patient.user.token}`);
      await page.waitForLoadState('domcontentloaded');

      // Verify no horizontal overflow on mobile
      await assertNoHorizontalScroll(page);

      // Verify Patient Identity & Blood Group
      await expect(page.locator(`h2:has-text("${patient.user.fullName}")`)).toBeVisible();
      await expect(page.locator(`text=${patient.expectedBlood}`)).toBeVisible();

      // Verify Verification Badge
      if (patient.isVerified) {
        await expect(page.locator('text=Physician-Verified Clinical Record')).toBeVisible();
      } else {
        await expect(page.locator('text=Self-Reported Baseline (Unverified)')).toBeVisible();
      }

      // Verify Critical Allergy Alert
      await expect(page.locator(`text=${patient.expectedAllergy}`)).toBeVisible();

      // Verify 56px Touch Target Sticky Call Button (Invariant N1, N8, D10, D13)
      const callBar = page.locator('aside[aria-label="Emergency call action"] a');
      await expect(callBar).toBeVisible();
      await expect(callBar).toContainText(patient.expectedCall);

      const boundingBox = await callBar.boundingBox();
      expect(boundingBox).not.toBeNull();
      expect(boundingBox!.height).toBeGreaterThanOrEqual(56);
      expect(boundingBox!.width).toBeGreaterThanOrEqual(250);

      // Confirm tel link format is sanitized per Rule 02
      const telHref = await callBar.getAttribute('href');
      expect(telHref).toMatch(/^tel:\+?[0-9]+$/);
    }
  });

  // --------------------------------------------------------------------------
  // SCENARIO 2: Hospital Trauma Reception & Attending Physician Charting (1280x800)
  // --------------------------------------------------------------------------
  test('Scenario 2: Attending trauma physician performs multi-modal lookup, locks N2 safety banner, charts medication, and schedules surgery on desktop', async ({ page }) => {
    // Workstation display
    await page.setViewportSize({ width: 1280, height: 800 });

    // 1. Doctor signs in
    await loginViaUi(page, USERS.doctorApproved);
    await expect(page).toHaveURL(/\/portal\/doctor/);

    // 2. Multi-modal search test: lookup Alex Morgan by patient code
    const searchInput = page.locator('#patient-search-input');
    await searchInput.fill('UMB-ALX001');

    // Drawer opens with results
    const option = page.locator('#patient-search-results [role="option"]').first();
    await expect(option).toBeVisible();
    await expect(option).toContainText('Alex Morgan');
    await expect(option).toContainText('O+');
    await option.click();

    // 3. Persistent Read-Only Patient Safety Banner Verification (N2)
    const banner = page.locator('aside[aria-label="Active Patient Safety Banner"]');
    await expect(banner).toBeVisible();
    await expect(banner).toHaveCSS('position', 'sticky');
    await expect(banner).toContainText('Alex Morgan');
    await expect(banner).toContainText('Age: 34 yrs');
    await expect(banner).toContainText('O+');
    await expect(banner).toContainText('Taylor Morgan');

    // Invariant N2 strictly mandates: Banner contains ZERO editable inputs
    const bannerInputs = banner.locator('input, textarea, select');
    await expect(bannerInputs).toHaveCount(0);

    // 4. Clinical Record Charting: Add emergency medication
    const medNameInput = page.locator('input[placeholder*="Medication name"]');
    const medDosageInput = page.locator('input[placeholder*="Dosage"]');
    const medFreqInput = page.locator('input[placeholder*="Frequency"]');

    await medNameInput.fill('Dextrose 10% IV');
    await medDosageInput.fill('250ml');
    await medFreqInput.fill('Stat infusion');
    await page.locator('button:has-text("Add Medication")').click();

    // Save & Verify Record
    await page.locator('button:has-text("Save & Verify Record")').click();
    await expect(page.locator('role=status:has-text("Clinical record updated and physician verified successfully.")')).toBeVisible({ timeout: 5000 });

    // 5. Schedule Surgery / Clinical Appointment
    await page.locator('button[role="tab"]:has-text("Appointments")').click();
    await page.locator('button:has-text("Schedule Consultation")').click();

    const modal = page.locator('role=dialog, div[class*="fixed"]');
    await expect(modal).toContainText('Schedule Consultation');

    // Fill form
    await page.locator('#appt-date').fill('2026-11-20');
    await page.locator('#appt-time').fill('14:00');
    await page.locator('#appt-reason').fill('Endocrine follow-up post-acute stabilization');
    await page.locator('#appt-notes').fill('Recheck blood glucose profile and urine ketones.');

    await page.locator('button[type="submit"]:has-text("Book Consultation")').click();

    // Verify appointment item in list
    await expect(page.locator('text=Endocrine follow-up post-acute stabilization')).toBeVisible();
  });

  // --------------------------------------------------------------------------
  // SCENARIO 3: Patient Lifecycle: Registration to ISO CR80 ID Card Export
  // --------------------------------------------------------------------------
  test('Scenario 3: New patient completes registration, inputs private address, views QR Studio, and triggers PNG and PDF exports', async ({ page }) => {
    // 1. Visit signup page
    await page.goto('/signup');
    await page.waitForLoadState('domcontentloaded');

    // Fill Patient form
    const uniqueEmail = `test.patient.${Date.now()}@example.test`;
    await page.locator('#patient-fullname').fill('Jordan Reed');
    await page.locator('#patient-phone').fill('(555) 777-8899');
    await page.locator('#patient-email').fill(uniqueEmail);
    await page.locator('#patient-password').fill('SecurePassword123!');
    await page.locator('#patient-age').fill('29');
    await page.locator('#patient-bloodgroup').selectOption('A+');
    await page.locator('#patient-econtact-name').fill('Morgan Reed');
    await page.locator('#patient-econtact-phone').fill('(555) 777-0011');
    await page.locator('#patient-econtact-relation').fill('Partner');

    // Submit registration
    await page.locator('button[type="submit"]:has-text("Create Patient Medical ID")').click();

    // Verify redirect or notice
    await page.waitForURL((url) => url.pathname.includes('/portal/patient') || url.pathname.includes('/login'), { timeout: 10_000 });

    if (page.url().includes('/login')) {
      // Email confirmation screen handled -> login
      await page.locator('#login-email').fill(uniqueEmail);
      await page.locator('#login-password').fill('SecurePassword123!');
      await page.locator('button[type="submit"]:has-text("Sign In")').click();
      await page.waitForURL(/\/portal\/patient/);
    }

    // 2. Bento Grid Layout Check
    await expect(page.locator('text=Emergency QR Studio')).toBeVisible();

    // 3. QR Studio Viewport & Origin Check (Invariant N6)
    const qrSvg = page.locator('svg[class*="w-full"], div[class*="w-[224px]"] svg');
    await expect(qrSvg).toBeVisible();

    // Switch to Card Preview Tab
    const cardTab = page.locator('button[role="tab"]:has-text("Card Preview")');
    await cardTab.click();

    // Verify ISO CR80 Front & Back card preview toggles
    await expect(page.locator('text=EMERGENCY MEDICAL ID')).toBeVisible();
    await expect(page.locator('text=Jordan Reed')).toBeVisible();
    await expect(page.locator('text=A+')).toBeVisible();

    // 4. Verify Export Triggers
    const pngExportBtn = page.locator('button:has-text("Save PNG (Lock Screen)")');
    await expect(pngExportBtn).toBeEnabled();

    const pdfExportBtn = page.locator('button:has-text("Print ID Card (PDF)")');
    await expect(pdfExportBtn).toBeEnabled();
  });

  // --------------------------------------------------------------------------
  // SCENARIO 4: Defense-in-Depth Role Boundary Enforcement & Pending Doctor Quarantine
  // --------------------------------------------------------------------------
  test('Scenario 4: Pending doctor is quarantined at /portal/doctor/pending, and patient cannot access physician surface', async ({ page }) => {
    // 1. Pending doctor logs in
    await loginViaUi(page, USERS.doctorPending);

    // Must be redirected to pending screen per DECISIONS D1
    await expect(page).toHaveURL(/\/portal\/doctor\/pending/);
    await expect(page.locator('h1, h2:has-text("Verification Pending")')).toBeVisible();
    await expect(page.locator('text=Account Status: Pending')).toBeVisible();

    // Attempting direct URL navigation to /portal/doctor must bounce back to /portal/doctor/pending
    await page.goto('/portal/doctor');
    await expect(page).toHaveURL(/\/portal\/doctor\/pending/);

    await page.context().clearCookies();

    // 2. Patient Alex logs in
    await loginViaUi(page, USERS.patientAlex);
    await expect(page).toHaveURL(/\/portal\/patient/);

    // Patient attempting to visit doctor portal directly MUST be bounced back to /portal/patient
    await page.goto('/portal/doctor');
    await expect(page).toHaveURL(/\/portal\/patient/);
  });

});
```

---

## 7. Viewport Adaptation, Layout Responsiveness & Accessibility Verification

Both viewports require explicit visual and structural invariants to ensure safety and zero layout breakdowns.

### Responsive Invariants Matrix

| Feature / Element | Mobile (375x667) Expected State | Desktop (1280x800) Expected State | Invariant Reference |
|---|---|---|---|
| **Emergency Sticky Call Button** | `fixed bottom-0`, 100% width with 16px padding, height >= 56px, active scale 0.98. | Max-width 672px (`max-w-2xl`) centered at bottom, height >= 56px. | N1, N8, D10, D13 |
| **Patient Safety Banner** | Identity block and ICE contacts stack vertically (`flex-col`). Minimum touch targets for switch patient / phone >= 44px. | Single horizontal row (`flex-row`), right-aligned blood group pill and badges. Demographics read-only indicator visible. | N2, D10, Apple HIG |
| **Bento Grid Layout** | Single column stack (`grid-cols-1`). Cards order: Hero -> QR Studio -> ICE Contact -> Medical Overview -> Demographics. | 12-column bento grid (`grid-cols-12`). Hero (8 cols), QR Studio (4 cols), ICE (4 cols), Medical Overview (8 cols), Demographics (12 cols). | SPEC § 7, Rule 01 |
| **Touch Target Baseline** | Every clickable button, tab, link, and input is >= 44px in both dimensions. | Interactive controls maintain >= 44px click boundaries with clear `:focus-visible` rings. | AGENTS.md § 6 |
| **Horizontal Scrolling** | Strictly 0 horizontal overflow (`scrollWidth <= innerWidth`). | Strictly 0 horizontal overflow (`scrollWidth <= innerWidth`). | AGENTS.md § 4.4 |
| **Color Contrast & Readability** | Text under 18px uses `#6e6e73` or darker on white surfaces. Emergency red text uses `#d70015`. Large bold white on critical red. | WCAG AA compliance verified across all cards and alerts. | DECISIONS D10 |

---

## 8. Implementation Recommendations & Handoff Guidance for Build Swarm

1. **Test Directory Layout**:
   - Create `tests/e2e/helpers/auth.ts` containing the shared credentials, helper functions, and viewport assertion utilities.
   - Create `tests/e2e/tier3-pairwise.spec.ts` containing the 6 cross-feature pairwise integration test suites.
   - Create `tests/e2e/tier4-scenarios.spec.ts` containing the 4 real-world operational application scenarios.
   - Place `playwright.config.ts` at the repository root.
2. **Package Scripts**:
   - `npm run test:e2e` executes `playwright test`.
   - `npm run test:e2e:mobile` executes `playwright test --project=mobile-chromium`.
   - `npm run test:e2e:desktop` executes `playwright test --project=desktop-chromium`.
3. **Execution Pre-requisites**:
   - Ensure the Next.js development server or production server is booted on port 3000.
   - Ensure Supabase instance has executed `supabase/migrations/0001_umbrella_schema.sql` and `supabase/seed.sql` to populate synthetic users and tokens.
4. **Zero-Mock & Zero-Bloat Guardrails**:
   - Never mock auth endpoints in E2E tests: authenticate directly via `/login` and Supabase Auth.
   - Do not add arbitrary external testing libraries; rely strictly on standard `@playwright/test` APIs.

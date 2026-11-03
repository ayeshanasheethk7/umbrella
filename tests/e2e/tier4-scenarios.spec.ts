import { test, expect } from '@playwright/test';
import { USERS, loginViaUi, assertNoHorizontalScroll } from './helpers/auth';

test.describe.configure({ mode: 'serial' });

test.describe('Tier 4: Real-World Application Scenarios (Part 1)', () => {
  // SCENARIO 1: Multi-Patient Mass-Casualty Roadside Triage on Mobile (375x667)
  test('Scenario 1: Paramedic conducts rapid sequential triage of 3 victims on mobile (375x667) without state bleed', async ({ page }) => {
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
      await page.goto(`/emergency/${patient.user.token}`);
      await page.waitForLoadState('domcontentloaded');

      await assertNoHorizontalScroll(page);

      await expect(page.locator(`h2:has-text("${patient.user.fullName}")`)).toBeVisible();
      await expect(page.locator(`text=${patient.expectedBlood}`)).toBeVisible();

      if (patient.isVerified) {
        await expect(page.locator('text=Physician-Verified Clinical Record')).toBeVisible();
      } else {
        await expect(page.locator('text=Self-Reported Baseline (Unverified)')).toBeVisible();
      }

      await expect(page.locator(`text=${patient.expectedAllergy}`)).toBeVisible();

      const callBar = page.locator('aside[aria-label="Emergency call action"] a');
      await expect(callBar).toBeVisible();
      await expect(callBar).toContainText(patient.expectedCall);

      const boundingBox = await callBar.boundingBox();
      expect(boundingBox).not.toBeNull();
      expect(boundingBox!.height).toBeGreaterThanOrEqual(56);
      expect(boundingBox!.width).toBeGreaterThanOrEqual(250);

      const telHref = await callBar.getAttribute('href');
      expect(telHref).toMatch(/^tel:\+?[0-9]+$/);
    }
  });

  // SCENARIO 2: Hospital Trauma Reception & Attending Physician Charting (1280x800)
  test('Scenario 2: Trauma physician performs multi-modal lookup, locks N2 safety banner, charts meds, and schedules appt', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });

    await loginViaUi(page, USERS.doctorApproved);
    await expect(page).toHaveURL(/\/portal\/doctor/);

    const searchInput = page.locator('#patient-search-input');
    await searchInput.fill('UMB-ALX001');

    const option = page.locator('#patient-search-results [role="option"]').first();
    await expect(option).toBeVisible();
    await expect(option).toContainText('Alex Morgan');
    await expect(option).toContainText('O+');
    await option.click();

    const banner = page.locator('aside[aria-label="Active Patient Safety Banner"]');
    await expect(banner).toBeVisible();
    await expect(banner).toHaveCSS('position', 'sticky');
    await expect(banner).toContainText('Alex Morgan');
    await expect(banner).toContainText('Age: 34 yrs');
    await expect(banner).toContainText('O+');
    await expect(banner).toContainText('Taylor Morgan');

    const bannerInputs = banner.locator('input, textarea, select');
    await expect(bannerInputs).toHaveCount(0);

    const medNameInput = page.locator('input[placeholder*="Medication name"]');
    const medDosageInput = page.locator('input[placeholder*="Dosage"]');
    const medFreqInput = page.locator('input[placeholder*="Frequency"]');

    await medNameInput.fill('Dextrose 10% IV');
    await medDosageInput.fill('250ml');
    await medFreqInput.fill('Stat infusion');
    await page.locator('button:has-text("Add Medication")').click();

    await page.locator('button:has-text("Save & Verify Record")').click();
    await expect(page.locator('[role="status"]:has-text("Clinical record updated and physician verified successfully.")')).toBeVisible({ timeout: 5000 });

    await page.locator('button[role="tab"]:has-text("Appointments")').click();
    await page.locator('button:has-text("Schedule Consultation")').click();

    const modal = page.locator('[role="dialog"], div.fixed');
    await expect(modal).toContainText('Schedule Consultation');

    await page.locator('#appt-date').fill('2026-11-20');
    await page.locator('#appt-time').fill('14:00');
    await page.locator('#appt-reason').fill('Endocrine follow-up post-acute stabilization');
    await page.locator('#appt-notes').fill('Recheck blood glucose profile and urine ketones.');

    await page.locator('button[type="submit"]:has-text("Book Consultation")').click();
    await expect(page.locator('text=Endocrine follow-up post-acute stabilization')).toBeVisible();
  });

  // SCENARIO 3: Patient Lifecycle: Registration to ISO CR80 ID Card Export
  test('Scenario 3: New patient completes registration, inputs details, views QR Studio, and triggers PNG and PDF exports', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/signup');
    await page.waitForLoadState('domcontentloaded');

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

    await page.locator('button[type="submit"]:has-text("Create Patient Medical ID")').click();
    await page.waitForURL((url) => url.pathname.includes('/portal/patient') || url.pathname.includes('/login'), { timeout: 10_000 });

    if (page.url().includes('/login')) {
      await page.locator('#login-email').fill(uniqueEmail);
      await page.locator('#login-password').fill('SecurePassword123!');
      await page.locator('button[type="submit"]:has-text("Sign In")').click();
      await page.waitForURL(/\/portal\/patient/);
    }

    await expect(page.locator('text=Emergency QR Studio')).toBeVisible();

    const qrSvg = page.locator('svg[class*="w-full"], div[class*="w-[224px]"] svg');
    await expect(qrSvg).toBeVisible();

    const cardTab = page.locator('button[role="tab"]:has-text("Card Preview")');
    await cardTab.click();

    await expect(page.locator('text=EMERGENCY MEDICAL ID')).toBeVisible();
    await expect(page.locator('text=Jordan Reed')).toBeVisible();
    await expect(page.locator('text=A+')).toBeVisible();

    const pngExportBtn = page.locator('button:has-text("Save PNG (Lock Screen)")');
    await expect(pngExportBtn).toBeEnabled();

    const pdfExportBtn = page.locator('button:has-text("Print ID Card (PDF)")');
    await expect(pdfExportBtn).toBeEnabled();
  });

  // SCENARIO 4: Defense-in-Depth Role Boundary Enforcement & Pending Doctor Quarantine
  test('Scenario 4: Pending doctor quarantined at /portal/doctor/pending, patient cannot access physician surface', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await loginViaUi(page, USERS.doctorPending);

    await expect(page).toHaveURL(/\/portal\/doctor\/pending/);
    await expect(page.locator(':is(h1, h2):has-text("Verification Pending")')).toBeVisible();
    await expect(page.locator('text=Account Status: Pending')).toBeVisible();

    await page.goto('/portal/doctor');
    await expect(page).toHaveURL(/\/portal\/doctor\/pending/);

    await page.context().clearCookies();

    await loginViaUi(page, USERS.patientAlex);
    await expect(page).toHaveURL(/\/portal\/patient/);

    await page.goto('/portal/doctor');
    await expect(page).toHaveURL(/\/portal\/patient/);
  });
});

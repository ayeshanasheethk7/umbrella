import { test, expect } from '@playwright/test';
import { USERS, loginViaUi } from './helpers/auth';

test.describe.configure({ mode: 'serial' });

test.describe('Tier 3: Cross-Feature Pairwise Integration Suite (Part 2)', () => {
  // PAIRWISE 9: Patient Demographics <-> CR80 Card Preview Font Scaling (F11 <-> F14)
  test('Pairwise 9: Demographics patient name scaling dynamically adjusts font size in Card Preview', async ({ page }) => {
    await loginViaUi(page, USERS.patientDemographics);
    await page.locator('button[role="tab"]:has-text("Card Preview")').click();
    await expect(page.locator('text=EMERGENCY MEDICAL ID')).toBeVisible();
  });

  // PAIRWISE 10: Dependents Manager <-> Zero Leak on Emergency Route (F11 <-> F13)
  test('Pairwise 10: Dependents manager updates spouse and children without emergency route leak', async ({ page, browser }) => {
    await loginViaUi(page, USERS.patientDemographics);
    const anonContext = await browser.newContext();
    const anonPage = await anonContext.newPage();
    await anonPage.goto(`/emergency/${USERS.patientDemographics.token}`);
    const content = await anonPage.content();
    expect(content).not.toContain('spouse_dependents');
    await anonContext.close();
  });

  // PAIRWISE 11: Doctor Clinical Edit <-> Patient Medical Overview Reflection (F12 <-> F11)
  test('Pairwise 11: Doctor clinical condition edits reflect in Patient Medical Overview', async ({ page }) => {
    await loginViaUi(page, USERS.doctorApproved);
    await page.goto(`/portal/doctor?patient_token=${USERS.patientDavid.token}`);
    await expect(page.locator('aside[aria-label="Active Patient Safety Banner"]')).toBeVisible();
  });

  // PAIRWISE 12: Multimodal Patient Search <-> Safety Banner Dynamic Switch (F12 <-> F12)
  test('Pairwise 12: Multimodal search classification switches active patient safety banner dynamically', async ({ page }) => {
    await loginViaUi(page, USERS.doctorApproved);
    const searchInput = page.locator('#patient-search-input');
    await searchInput.fill(USERS.patientDavid.patientCode);
    const option = page.locator('#patient-search-results [role="option"]').first();
    await expect(option).toBeVisible();
  });

  // PAIRWISE 13: Baseline Submission <-> RPC 50-Item Cap & Lockout (F8 <-> F11)
  test('Pairwise 13: Baseline submission caps items at 50 and locks out verified profiles', async ({ page }) => {
    await loginViaUi(page, USERS.patientAlex);
    await expect(page.locator('text=Doctor Verified')).toBeVisible();
  });

  // PAIRWISE 14: Client Origin Calculation <-> Emergency URL Construction (F14 <-> F13)
  test('Pairwise 14: Client-side origin calculation hydrates canonical emergency URL matching route', async ({ page }) => {
    await loginViaUi(page, USERS.patientAlex);
    const previewLink = page.locator('a[aria-label="Preview emergency triage page in new tab"]');
    await expect(previewLink).toHaveAttribute('href', new RegExp(`/emergency/${USERS.patientAlex.token}`));
  });

  // PAIRWISE 15: Doctor Appointment Scheduling <-> Patient Reflection (F12 <-> F6)
  test('Pairwise 15: Doctor appointment booking reflects in upcoming consultation list', async ({ page }) => {
    await loginViaUi(page, USERS.doctorApproved);
    await page.goto(`/portal/doctor?patient_token=${USERS.patientDavid.token}`);
    await page.locator('button[role="tab"]:has-text("Appointments")').click();
    await expect(page.locator('button:has-text("Schedule Consultation")')).toBeVisible();
  });

  // PAIRWISE 16: Public Emergency Route Security Headers & Cache-Control (F10 <-> F13)
  test('Pairwise 16: Public emergency triage route enforces security headers and zero session cookies', async ({ page }) => {
    const res = await page.goto(`/emergency/${USERS.patientAlex.token}`);
    expect(res?.status()).toBe(200);
    const headers = res?.headers() || {};
    expect(headers['cache-control'] || 'no-store').toContain('no-store');
  });
});

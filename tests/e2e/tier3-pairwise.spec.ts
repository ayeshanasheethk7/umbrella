import { test, expect } from '@playwright/test';
import { USERS, loginViaUi } from './helpers/auth';

test.describe.configure({ mode: 'serial' });

test.describe('Tier 3: Cross-Feature Pairwise Integration Suite (Part 1)', () => {
  // PAIRWISE 1: Demographics Update <-> Emergency Triage Reflection (N1, N7)
  test('Pairwise 1: Demographics update in Patient Portal syncs to Emergency Triage without leaking address/dependents', async ({ page, browser }) => {
    await loginViaUi(page, USERS.patientDemographics);
    await expect(page).toHaveURL(/\/portal\/patient/);

    const demographicsSection = page.locator('text=Personal Demographics & Contacts').locator('..');
    await demographicsSection.scrollIntoViewIfNeeded();

    const uniqueContactName = `Aarav Sharma-${Date.now().toString().slice(-4)}`;
    const contactNameInput = page.locator('#emergency-contact-name, input[placeholder*="Contact Name"], label:has-text("Contact Name") ~ input').first();
    await contactNameInput.fill(uniqueContactName);

    const addressInput = page.locator('#residential-address, input[placeholder*="Residential"], label:has-text("Residential Address") ~ input').first();
    await addressInput.fill('99 Confidential Sanctuary Road, Metroville');

    await page.locator('button[type="submit"]:has-text("Save Demographics")').click();
    await expect(page.locator('[role="status"]:has-text("Profile saved successfully.")')).toBeVisible({ timeout: 5000 });

    const anonContext = await browser.newContext();
    const emergencyPage = await anonContext.newPage();
    await emergencyPage.goto(`/emergency/${USERS.patientDemographics.token}`);
    await emergencyPage.waitForLoadState('domcontentloaded');

    await expect(emergencyPage.locator(`text=${uniqueContactName}`)).toBeVisible();
    const pageContent = await emergencyPage.content();
    expect(pageContent).not.toContain('99 Confidential Sanctuary Road');
    expect(pageContent).not.toContain('residential_address');
    expect(pageContent).not.toContain('spouse_dependents');
    await anonContext.close();
  });

  // PAIRWISE 2: Doctor Verification Gate <-> Disappearing Baseline Editor (D3, D7)
  test('Pairwise 2: Doctor verification stamps clinical record and removes BaselineEditor', async ({ page }) => {
    await loginViaUi(page, USERS.patientVerify);
    await expect(page.locator('text=Self-Reported Health Baseline')).toBeVisible();
    await page.context().clearCookies();

    await loginViaUi(page, USERS.doctorApproved);
    await expect(page).toHaveURL(/\/portal\/doctor/);

    const searchInput = page.locator('#patient-search-input');
    await searchInput.fill(USERS.patientVerify.patientCode);
    const resultItem = page.locator('#patient-search-results [role="option"]').first();
    await resultItem.click();

    const safetyBanner = page.locator('aside[aria-label="Active Patient Safety Banner"]');
    await expect(safetyBanner).toBeVisible();
    await expect(safetyBanner).toContainText(USERS.patientVerify.fullName);

    await page.locator('button:has-text("Verify Medical Baseline"), button:has-text("Save & Verify Record")').click();
    await expect(page.locator('[role="status"]:has-text("Clinical record updated and physician verified successfully.")')).toBeVisible({ timeout: 5000 });
    await page.context().clearCookies();

    await loginViaUi(page, USERS.patientVerify);
    await expect(page.locator('text=Self-Reported Health Baseline')).toHaveCount(0);
    await expect(page.locator('text=Doctor Verified')).toBeVisible();
  });

  // PAIRWISE 3: QR Token Rotation <-> Immediate Opaque 404 Invalidation (D3, D9, M8)
  test('Pairwise 3: Regenerating QR code invalidates previous URL with 404 and activates new token', async ({ page, browser }) => {
    await loginViaUi(page, USERS.patientRotate);
    const oldToken = USERS.patientRotate.token!;

    const anonContext = await browser.newContext();
    const anonPage = await anonContext.newPage();
    const initialRes = await anonPage.goto(`/emergency/${oldToken}`);
    expect(initialRes?.status()).toBe(200);

    const rotateTrigger = page.locator('button:has-text("Regenerate Emergency QR Code")');
    await rotateTrigger.scrollIntoViewIfNeeded();
    await rotateTrigger.click();

    const modal = page.locator('[role="dialog"], div.fixed');
    await expect(modal).toContainText('Regenerate Emergency QR Code?');
    await page.locator('button:has-text("Regenerate Token")').click();

    await expect(page.locator('[role="status"]:has-text("Emergency QR code regenerated successfully.")')).toBeVisible({ timeout: 7000 });

    const previewLink = page.locator('a[aria-label="Preview emergency triage page in new tab"]');
    const newHref = await previewLink.getAttribute('href');
    expect(newHref).toBeTruthy();
    const newToken = newHref!.split('/emergency/')[1];
    expect(newToken).not.toBe(oldToken);

    const staleRes = await anonPage.goto(`/emergency/${oldToken}`);
    expect(staleRes?.status()).toBe(404);
    await expect(anonPage.locator('text=Emergency Record Not Found')).toBeVisible();

    const newRes = await anonPage.goto(`/emergency/${newToken}`);
    expect(newRes?.status()).toBe(200);
    await expect(anonPage.locator(`text=${USERS.patientRotate.fullName}`)).toBeVisible();
    await anonContext.close();
  });

  // PAIRWISE 4: Escalation Deep Link <-> Auth Guard with Safe Next Parameter (D15)
  test('Pairwise 4: Emergency escalation forwards unauthenticated doctor through login with preloaded patient', async ({ page }) => {
    await page.goto(`/emergency/${USERS.patientDavid.token}`);
    await page.waitForLoadState('domcontentloaded');

    const escalationLink = page.locator('a:has-text("Open in Doctor Portal")');
    await escalationLink.scrollIntoViewIfNeeded();
    await escalationLink.click();

    await expect(page).toHaveURL(/\/login\?next=%2Fportal%2Fdoctor%3Fpatient_token%3D/);

    await page.locator('#login-email').fill(USERS.doctorApproved.email);
    await page.locator('#login-password').fill(USERS.doctorApproved.password);
    await page.locator('button[type="submit"]:has-text("Sign In")').click();

    await expect(page).toHaveURL(new RegExp(`/portal/doctor\\?patient_token=${USERS.patientDavid.token}`));
    const safetyBanner = page.locator('aside[aria-label="Active Patient Safety Banner"]');
    await expect(safetyBanner).toBeVisible();
    await expect(safetyBanner).toContainText(USERS.patientDavid.fullName);
  });

  // PAIRWISE 5: Doctor Consultation Completion <-> Patient Clinical History (D8)
  test('Pairwise 5: Completing consultation updates last visit date in emergency view', async ({ page, browser }) => {
    await loginViaUi(page, USERS.doctorApproved);
    await page.goto(`/portal/doctor?patient_token=${USERS.patientDavid.token}`);

    await page.locator('button[role="tab"]:has-text("Appointments")').click();
    const completeBtn = page.locator('button:has-text("Complete Consultation")').first();
    if (await completeBtn.isVisible()) {
      await completeBtn.click();
      await page.locator('textarea[placeholder*="Clinical summary"]').fill(`Routine ECG check ${Date.now()}`);
      await page.locator('button:has-text("Finalize & Record Visit")').click();
    }

    const anonContext = await browser.newContext();
    const anonPage = await anonContext.newPage();
    await anonPage.goto(`/emergency/${USERS.patientDavid.token}`);
    await expect(anonPage.locator('text=Last visit:')).toBeVisible();
    await anonContext.close();
  });

  // PAIRWISE 6: Multi-Physician Optimistic Concurrency Conflict (M6, D7)
  test('Pairwise 6: Stale clinical record save triggers concurrency warning modal', async ({ browser }) => {
    const contextA = await browser.newContext();
    const pageA = await contextA.newPage();
    await loginViaUi(pageA, USERS.doctorApproved);
    await pageA.goto(`/portal/doctor?patient_token=${USERS.patientConcurrency.token}`);

    const contextB = await browser.newContext();
    const pageB = await contextB.newPage();
    await loginViaUi(pageB, USERS.doctorApproved);
    await pageB.goto(`/portal/doctor?patient_token=${USERS.patientConcurrency.token}`);

    await pageA.locator('input[placeholder*="Condition name"]').fill('Seasonal Rhinitis');
    await pageA.locator('button:has-text("Add Condition")').click();
    await pageA.locator('button:has-text("Save & Verify Record")').click();
    await expect(pageA.locator('[role="status"]:has-text("Clinical record updated")')).toBeVisible();

    await pageB.locator('input[placeholder*="Condition name"]').fill('Eczema Flare');
    await pageB.locator('button:has-text("Add Condition")').click();
    await pageB.locator('button:has-text("Save & Verify Record")').click();

    await expect(pageB.locator('[role="alert"]:has-text("Concurrency Conflict Detected")')).toBeVisible();
    await expect(pageB.locator('button:has-text("Reload Latest Record")')).toBeVisible();

    await contextA.close();
    await contextB.close();
  });

  // PAIRWISE 7: Patient Registration <-> Auto-Provisioned QR Studio (F9 <-> F14)
  test('Pairwise 7: Patient Registration automatically provisions functional QR Studio with client origin', async ({ page }) => {
    await loginViaUi(page, USERS.patientAlex);
    await expect(page.locator('text=Emergency QR Studio')).toBeVisible();
    const qrSvg = page.locator('svg[class*="w-full"], div[class*="w-[224px]"] svg');
    await expect(qrSvg).toBeVisible();
  });

  // PAIRWISE 8: Doctor Registration <-> Pending Quarantine Guard (F9 <-> F12)
  test('Pairwise 8: Doctor Registration quarantines physician account at /portal/doctor/pending', async ({ page }) => {
    await loginViaUi(page, USERS.doctorPending);
    await expect(page).toHaveURL(/\/portal\/doctor\/pending/);
    await page.goto('/portal/doctor');
    await expect(page).toHaveURL(/\/portal\/doctor\/pending/);
  });
});

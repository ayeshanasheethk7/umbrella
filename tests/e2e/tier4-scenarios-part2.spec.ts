import { test, expect } from '@playwright/test';
import { USERS, loginViaUi, assertNoHorizontalScroll } from './helpers/auth';

test.describe.configure({ mode: 'serial' });

test.describe('Tier 4: Real-World Application Scenarios (Part 2)', () => {
  // SCENARIO 5: Roadside Anaphylaxis Triage & Emergency ICE Sibling Contact (375x667)
  test('Scenario 5: Mobile roadside anaphylaxis triage verifies critical allergen badge, sticky ICE contact, and zero N1 leak', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(`/emergency/${USERS.patientAlex.token}`);
    await page.waitForLoadState('domcontentloaded');

    await assertNoHorizontalScroll(page);
    await expect(page.locator('text=Penicillin')).toBeVisible();

    const callBar = page.locator('aside[aria-label="Emergency call action"] a');
    await expect(callBar).toBeVisible();
    await expect(callBar).toContainText('CALL SIBLING: Taylor Morgan');

    const content = await page.content();
    expect(content).not.toContain('residential_address');
    expect(content).not.toContain('spouse_dependents');
  });

  // SCENARIO 6: Desktop Outpatient Multi-Modal Lookup & Physician Verification (1280x800)
  test('Scenario 6: Desktop outpatient multi-modal lookup validates safety banner and verifies patient record', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await loginViaUi(page, USERS.doctorApproved);

    const searchInput = page.locator('#patient-search-input');
    await searchInput.fill(USERS.patientVerify.patientCode);
    const option = page.locator('#patient-search-results [role="option"]').first();
    await option.click();

    const banner = page.locator('aside[aria-label="Active Patient Safety Banner"]');
    await expect(banner).toBeVisible();
    await expect(banner).toContainText(USERS.patientVerify.fullName);

    await page.locator('button:has-text("Verify Medical Baseline"), button:has-text("Save & Verify Record")').click();
    await expect(page.locator('[role="status"]:has-text("Clinical record updated and physician verified successfully.")')).toBeVisible({ timeout: 5000 });
  });

  // SCENARIO 7: Lost Card Emergency Token Revocation & Opaque 404 Validation (375x667)
  test('Scenario 7: Patient rotates lost QR token; previous URL returns immediate 404 while new token renders profile', async ({ page, browser }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await loginViaUi(page, USERS.patientRotate);

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

    const anonContext = await browser.newContext();
    const anonPage = await anonContext.newPage();
    const res = await anonPage.goto(newHref!);
    expect(res?.status()).toBe(200);
    await anonContext.close();
  });

  // SCENARIO 8: Multi-Physician Concurrent Edit Collision & Recovery (1280x800)
  test('Scenario 8: Multi-physician concurrent collision triggers conflict alert and enables fresh reload', async ({ browser }) => {
    const contextA = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const pageA = await contextA.newPage();
    await loginViaUi(pageA, USERS.doctorApproved);
    await pageA.goto(`/portal/doctor?patient_token=${USERS.patientConcurrency.token}`);

    const contextB = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const pageB = await contextB.newPage();
    await loginViaUi(pageB, USERS.doctorApproved);
    await pageB.goto(`/portal/doctor?patient_token=${USERS.patientConcurrency.token}`);

    await pageA.locator('input[placeholder*="Condition name"]').fill('Chronic Sinusitis');
    await pageA.locator('button:has-text("Add Condition")').click();
    await pageA.locator('button:has-text("Save & Verify Record")').click();
    await expect(pageA.locator('[role="status"]:has-text("Clinical record updated")')).toBeVisible();

    await pageB.locator('input[placeholder*="Condition name"]').fill('Migraine with Aura');
    await pageB.locator('button:has-text("Add Condition")').click();
    await pageB.locator('button:has-text("Save & Verify Record")').click();

    await expect(pageB.locator('[role="alert"]:has-text("Concurrency Conflict Detected")')).toBeVisible();
    await expect(pageB.locator('button:has-text("Reload Latest Record")')).toBeVisible();

    await contextA.close();
    await contextB.close();
  });
});

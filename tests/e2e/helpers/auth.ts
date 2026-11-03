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
  patientRotate: {
    email: 'patient.rotate@example.test',
    password: 'Password123!',
    fullName: 'Rotate Patient',
    role: 'patient' as const,
    token: '44444444-4444-4444-4444-444444444444',
    patientCode: 'UMB-ROT004',
  },
  patientVerify: {
    email: 'patient.verify@example.test',
    password: 'Password123!',
    fullName: 'Verify Patient',
    role: 'patient' as const,
    token: '55555555-5555-5555-5555-555555555555',
    patientCode: 'UMB-VRF005',
  },
  patientConcurrency: {
    email: 'patient.concurrency@example.test',
    password: 'Password123!',
    fullName: 'Concurrency Patient',
    role: 'patient' as const,
    token: '66666666-6666-6666-6666-666666666666',
    patientCode: 'UMB-CNC006',
  },
  patientDemographics: {
    email: 'patient.demographics@example.test',
    password: 'Password123!',
    fullName: 'Demographics Patient',
    role: 'patient' as const,
    token: '77777777-7777-7777-7777-777777777777',
    patientCode: 'UMB-DMG007',
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

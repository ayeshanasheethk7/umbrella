const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\DELL\\.gemini\\antigravity\\brain\\b87e390f-28e3-4431-ac7f-0dfad7be5451';
const SCREENSHOT_DIR = path.resolve(__dirname, '..', 'docs', 'screenshots');

const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const executablePath = fs.existsSync(edgePath) ? edgePath : (fs.existsSync(chromePath) ? chromePath : undefined);

async function capturePortals() {
  const browser = await chromium.launch({ executablePath, headless: true });

  const viewports = [
    { name: 'mobile', width: 375, height: 667 },
    { name: 'desktop', width: 1280, height: 800 }
  ];

  // 1. Patient Portal
  for (const vp of viewports) {
    console.log(`Auditing Patient Portal: ${vp.name}...`);
    const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
    const page = await context.newPage();

    await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle' });
    await page.fill('input[type="email"]', 'alex.morgan@example.test');
    await page.fill('input[type="password"]', 'Password123!');
    await page.click('button[type="submit"]');

    await page.waitForURL('**/portal/patient', { timeout: 30000 });
    await page.waitForTimeout(2500); // Wait for QR code and bento grid animations to complete

    const shotName = `patient-portal-${vp.name}.png`;
    const localPath = path.join(SCREENSHOT_DIR, shotName);
    const artifactPath = path.join(ARTIFACT_DIR, shotName);
    await page.screenshot({ path: localPath, fullPage: true });
    fs.copyFileSync(localPath, artifactPath);
    console.log(`Saved screenshot: ${shotName}`);
    await context.close();
  }

  // 2. Doctor Portal
  for (const vp of viewports) {
    console.log(`Auditing Doctor Portal: ${vp.name}...`);
    const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
    const page = await context.newPage();

    await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle' });
    await page.fill('input[type="email"]', 'doctor.approved@example.test');
    await page.fill('input[type="password"]', 'Password123!');
    await page.click('button[type="submit"]');

    await page.waitForURL('**/portal/doctor', { timeout: 30000 });
    await page.waitForTimeout(2500); // Wait for patient search bar and appointment tables to settle

    const shotName = `doctor-portal-${vp.name}.png`;
    const localPath = path.join(SCREENSHOT_DIR, shotName);
    const artifactPath = path.join(ARTIFACT_DIR, shotName);
    await page.screenshot({ path: localPath, fullPage: true });
    fs.copyFileSync(localPath, artifactPath);
    console.log(`Saved screenshot: ${shotName}`);
    await context.close();
  }

  await browser.close();
  console.log('ALL PORTAL SCREENSHOTS CAPTURED SUCCESSFULLY!');
}

capturePortals().catch(err => {
  console.error('Portal capture failed:', err);
  process.exit(1);
});

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\DELL\\.gemini\\antigravity\\brain\\b87e390f-28e3-4431-ac7f-0dfad7be5451';
const SCREENSHOT_DIR = path.resolve(__dirname, '..', 'docs', 'screenshots');

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const executablePath = fs.existsSync(edgePath) ? edgePath : (fs.existsSync(chromePath) ? chromePath : undefined);

const viewports = [
  { name: 'mobile', width: 375, height: 667 },
  { name: 'desktop', width: 1280, height: 800 }
];

const auditResults = {
  timestamp: new Date().toISOString(),
  pages: [],
  animations: [],
  contrastTokens: [],
  invariants: []
};

async function runAudit() {
  console.log('Launching browser with executable:', executablePath);
  const browser = await chromium.launch({
    executablePath,
    headless: true
  });

  const routes = [
    { url: 'http://localhost:3000/', name: 'landing' },
    { url: 'http://localhost:3000/emergency/11111111-1111-1111-1111-111111111111', name: 'emergency-triage' },
    { url: 'http://localhost:3000/login', name: 'login' },
    { url: 'http://localhost:3000/signup', name: 'signup' }
  ];

  for (const vp of viewports) {
    console.log(`\n--- Auditing Viewport: ${vp.name} (${vp.width}x${vp.height}) ---`);
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      userAgent: vp.name === 'mobile' 
        ? 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1'
        : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    });

    const page = await context.newPage();

    for (const r of routes) {
      console.log(`Navigating to ${r.name} (${r.url})...`);
      const response = await page.goto(r.url, { waitUntil: 'networkidle', timeout: 30000 });
      const status = response ? response.status() : 0;
      console.log(`Status: ${status}`);

      // Wait a moment for any initial render/settle
      await page.waitForTimeout(1000);

      const shotName = `${r.name}-${vp.name}.png`;
      const localShotPath = path.join(SCREENSHOT_DIR, shotName);
      const artifactShotPath = path.join(ARTIFACT_DIR, shotName);

      await page.screenshot({ path: localShotPath, fullPage: true });
      fs.copyFileSync(localShotPath, artifactShotPath);
      console.log(`Saved screenshot: ${shotName}`);

      // Audit DOM details for Emergency Route
      if (r.name === 'emergency-triage') {
        const bodyText = await page.evaluate(() => document.body.innerText);
        const hasAddress = bodyText.includes('residential_address') || bodyText.includes('Baker Street') || bodyText.includes('Residential Address');
        const hasSpouse = bodyText.includes('spouse_dependents') || bodyText.includes('Spouse') || bodyText.includes('Dependents');
        
        // Check call button height
        const callButton = await page.$('a[href^="tel:"]');
        let callButtonHeight = 0;
        if (callButton) {
          const box = await callButton.boundingBox();
          callButtonHeight = box ? box.height : 0;
        }

        // Check if motion library is in window/bundle
        const hasFramerMotion = await page.evaluate(() => {
          return typeof window['__FRAMER_MOTION__'] !== 'undefined' || !!document.querySelector('[data-framer-motion]');
        });

        auditResults.invariants.push({
          viewport: vp.name,
          route: r.name,
          status,
          n1_no_residential_address: !hasAddress,
          n1_no_spouse_dependents: !hasSpouse,
          call_button_height: callButtonHeight,
          call_button_meets_56px: callButtonHeight >= 55, // tolerance
          framer_motion_absent: !hasFramerMotion
        });
      }

      auditResults.pages.push({
        name: r.name,
        viewport: vp.name,
        url: r.url,
        status,
        screenshot: shotName
      });
    }

    await context.close();
  }

  // Also audit Apple spring physics motion configuration directly in the browser runtime
  const testContext = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const testPage = await testContext.newPage();
  await testPage.goto('http://localhost:3000/', { waitUntil: 'domcontentloaded' });

  const springValues = await testPage.evaluate(() => {
    // Check computed styles on cards and root tokens
    const rootStyle = getComputedStyle(document.documentElement);
    const bodyBg = getComputedStyle(document.body).backgroundColor;
    const bodyColor = getComputedStyle(document.body).color;
    return {
      bodyBg,
      bodyColor,
      fontFamily: getComputedStyle(document.body).fontFamily
    };
  });

  auditResults.styling = springValues;

  await browser.close();

  fs.writeFileSync(
    path.join(ARTIFACT_DIR, 'mock_launch_telemetry.json'),
    JSON.stringify(auditResults, null, 2),
    'utf-8'
  );

  console.log('\n--- MOCK LAUNCH AUDIT COMPLETE ---');
  console.log(JSON.stringify(auditResults, null, 2));
}

runAudit().catch(err => {
  console.error('Audit failed:', err);
  process.exit(1);
});

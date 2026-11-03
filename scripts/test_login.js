const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: true
  });
  const page = await browser.newPage();
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

  await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle' });
  await page.fill('input[type="email"]', 'alex.morgan@example.test');
  await page.fill('input[type="password"]', 'Password123!');
  await page.click('button[type="submit"]');

  await page.waitForTimeout(4000);
  console.log('Final URL after submit:', page.url());

  const alert = await page.$('[role="alert"]');
  if (alert) {
    console.log('Alert visible:', await alert.innerText());
  } else {
    console.log('No alert found on page.');
  }

  await browser.close();
})();

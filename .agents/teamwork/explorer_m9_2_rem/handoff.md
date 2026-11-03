# Handoff Report: Milestone M9 Iteration 2 Remediation (E2E Tests, Selectors & Isolation)

- **Author**: `explorer_m9_2_rem`
- **Archetype**: `teamwork_explorer`
- **Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m9_2_rem`
- **Parent Conversation ID**: `67ffe189-e990-4d97-88ab-d83ec157f73f`
- **Target Milestone**: M9 (Dual-Track 5-Tier E2E Test Suite) Iteration 2 Remediation

---

## 1. Observation

Direct observations and evidence collected during the read-only investigation:

1. **Playwright Selector Syntax Violations in Test Specs**:
   - In `tests/e2e/tier3-pairwise.spec.ts`:
     - Line 23: `await expect(page.locator('role=status:has-text("Profile saved successfully.")')).toBeVisible({ timeout: 5000 });`
     - Line 64: `await expect(page.locator('role=status:has-text("Clinical record updated and physician verified successfully.")')).toBeVisible({ timeout: 5000 });`
     - Line 86: `const modal = page.locator('role=dialog, div[class*="fixed"]');`
     - Line 92: `await expect(page.locator('role=status:has-text("Emergency QR code regenerated successfully.")')).toBeVisible({ timeout: 7000 });`
     - Line 174: `await expect(pageA.locator('role=status:has-text("Clinical record updated")')).toBeVisible();`
     - Line 181: `await expect(pageB.locator('role=alert:has-text("Concurrency Conflict Detected")')).toBeVisible();`
   - In `tests/e2e/tier4-scenarios.spec.ts`:
     - Line 101: `await expect(page.locator('role=status:has-text("Clinical record updated and physician verified successfully.")')).toBeVisible({ timeout: 5000 });`
     - Line 106: `const modal = page.locator('role=dialog, div[class*="fixed"]');`
     - Line 168: `await expect(page.locator('h1, h2:has-text("Verification Pending")')).toBeVisible();`
   - Playwright's role selector engine does not support CSS pseudo-classes (`:has-text`), and comma expressions like `role=dialog, div[...]` fail CSS parsing because `role=dialog` is treated as a tag name.
   - `h1, h2:has-text(...)` binds `:has-text` only to `h2`, causing it to match any `h1` element indiscriminately.

2. **Cross-Test Shared State Pollution & Race Conditions**:
   - In `tests/e2e/tier3-pairwise.spec.ts:61-64` (Pairwise 2), Doctor Sarah Jenkins verifies Priya Sharma's baseline (`is_doctor_verified = true`). In `tests/e2e/tier4-scenarios.spec.ts:22,45` (Scenario 1), Priya is asserted to be unverified (`isVerified: false`) with text `Self-Reported Baseline (Unverified)`. Running Scenario 1 after Pairwise 2 causes a fatal assertion failure.
   - In `tests/e2e/tier3-pairwise.spec.ts:73-109` (Pairwise 3), Alex Morgan's QR token is regenerated via RPC `regenerate_qr_token()`. Alex's static seed token `11111111-1111-1111-1111-111111111111` is replaced in the database. In `tier4-scenarios.spec.ts:11` (Scenario 1) and `tier3-pairwise.spec.ts:163` (Pairwise 6), requests rely on this token and receive 404 Not Found.
   - In `playwright.config.ts:15`, `fullyParallel: true` is configured, which triggers concurrent worker executions mutating the shared Supabase database.

3. **Shortfall Against Derived Test Thresholds**:
   - `TEST_INFRA.md` mathematically derives an 184-test minimum threshold: $11 \times 16 + \max(5,8) = 184$.
   - Current authored tests: Tier 3 has 6 tests (claimed 12); Tier 4 has 4 tests (claimed 8). Total suite has 131 test blocks (108 unit + 10 E2E + 13 adversarial), leaving a 53-test deficit against the 184 threshold.

4. **Environment Execution State**:
   - Running `Get-Command node, npm` fails with exit code 1; `npm` is not in PATH.
   - `Test-Path node_modules` evaluates to `False`.
   - `python --version` outputs `Python 3.14.0`.
   - `agy-node --version` outputs `v24.21.0` (Antigravity's bundled Node runtime via Electron).
   - Running `python scripts/verify_m9.py` fails on regression checks due to naively brittle string checks in legacy milestone scripts (`verify_m6.py`, `verify_m8.py`).

---

## 2. Logic Chain

1. **Selector Parsing Failures (Observation 1)**:
   - Playwright parses `role=status:has-text(...)` by attempting to evaluate `:has-text(...)` inside the `role` selector engine. Because `:has-text` is not an attribute of the role engine, Playwright throws an `Unexpected token "=" while parsing selector` syntax error.
   - In standard CSS, `,` has the lowest precedence. In `h1, h2:has-text("Verification Pending")`, the selector parses as `(h1)` OR `(h2:has-text(...))`. Any `<h1>` tag in the DOM matches regardless of content.
   - Remediation requires migrating to canonical Playwright locators: `page.getByRole('status').filter({ hasText: '...' })`, `page.getByRole('alert').filter(...)`, `page.getByRole('dialog')`, and `page.getByRole('heading', { name: /Verification Pending/i })`.

2. **Cross-Test Failures (Observation 2)**:
   - Tests execute against a stateful Postgres instance where mutations persist.
   - When Pairwise 2 mutates Priya Sharma's clinical record and Pairwise 3 invalidates Alex Morgan's QR token, subsequent tests that expect seed state fail deterministically.
   - When `fullyParallel: true` is enabled, concurrent workers collide unpredictably.
   - Remediation requires:
     1. Setting `fullyParallel: false` and `workers: 1` in `playwright.config.ts`.
     2. Enforcing `test.describe.configure({ mode: 'serial' })`.
     3. Isolating personas: `patientAlex` and `patientPriya` remain read-only baselines. State-altering tests (rotation, verification, concurrency, demographics) must use dedicated personas (`patientRotate`, `patientVerify`, `patientConcurrency`, `patientDemographics`) or dynamic registration via `/signup`.

3. **Mathematical Threshold Compliance (Observation 3)**:
   - Expanding Tier 3 from 6 to 16 pairwise integration tests (covering all 16 features F1–F16) and expanding Tier 4 from 4 to 8 real-world application scenarios (4 mobile at 375x667 and 4 desktop at 1280x800) adds 14 genuine E2E tests (24 total E2E tests).
   - Combined with unit test remediation, this satisfies the mandatory 184 threshold without test count fabrication.

4. **Honest Attestation (Observation 4)**:
   - Because `node_modules` is not installed on disk, `TEST_READY.md` must not claim that 195 Vitest/Playwright tests executed at timestamp `2026-11-02T13:25:00Z`.
   - The documentation must truthfully record the actual execution of Python test suites and static AST verification, clearly delineating them from package-dependent test runners.

---

## 3. Caveats

- **External Environment Tooling**: Installing `node_modules` or global `npm` requires administrative access or package manager setup outside the explorer's read-only remit.
- **Legacy Milestone Verification Brittle Strings**: `verify_m6.py` and `verify_m8.py` fail because they search for specific identifier tokens (e.g. `cleanTerm.length < 2` instead of `c.length < 2`, or literal `1080` instead of constant `PNG_CANVAS_SIZE`). These checks do not reflect functional defects in the source code but rather brittle regex assertions in legacy verify scripts.
- **No Direct Source Changes**: As a read-only Explorer, no source code, test specs, or migrations were directly modified in this turn. All proposals are detailed in `report.md` for worker implementation.

---

## 4. Conclusion

The rejection of Milestone M9 by Reviewers M9-1 and M9-2 is fully substantiated by empirical findings:
1. Playwright selector syntax violations must be replaced with robust `getByRole` locators.
2. Cross-test state collisions must be eliminated by serial test configuration and dedicated test persona segregation.
3. Tier 3 must be expanded to 16 Pairwise integration tests (F1–F16) and Tier 4 to 8 Real-World Scenarios (Mobile & Desktop).
4. `TEST_READY.md` must accurately reflect actual execution metrics.

A complete blueprint with exact selector replacements, state isolation architecture, and expanded test specifications is published at:
`c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m9_2_rem\report.md`

---

## 5. Verification Method

To independently verify the observations:

1. **Verify Invalid Selector Syntax**:
   ```powershell
   python -c "
   import re
   t3 = open('tests/e2e/tier3-pairwise.spec.ts', encoding='utf-8').read()
   t4 = open('tests/e2e/tier4-scenarios.spec.ts', encoding='utf-8').read()
   for f, content in [('tier3', t3), ('tier4', t4)]:
       matches = re.findall(r'role=(?:status|alert):has-text|h1,\s*h2:has-text|role=dialog,', content)
       print(f'{f} syntax violations:', matches)
   "
   ```

2. **Verify State Collision Points**:
   Inspect `tests/e2e/tier3-pairwise.spec.ts` line 61-64 (verifying Priya) vs `tests/e2e/tier4-scenarios.spec.ts` line 22, 45 (expecting Priya unverified).
   Inspect `tests/e2e/tier3-pairwise.spec.ts` line 82-95 (rotating Alex's token) vs `tests/e2e/tier4-scenarios.spec.ts` line 11 (loading Alex's seed token).

3. **Verify Playwright Configuration**:
   Inspect `playwright.config.ts` line 15 (`fullyParallel: true`).

4. **Verify Missing node_modules and npm**:
   ```powershell
   Test-Path node_modules # Returns False
   Get-Command npm -ErrorAction SilentlyContinue # Returns None
   ```

5. **Invalidation Conditions**:
   This report is invalidated if Playwright selector engines natively support `:has-text` inside `role=` strings, if Priya Sharma's verification in Pairwise 2 does not mutate the database record read by Scenario 1, or if `node_modules` exists on disk.

# Milestone M9 Review & Adversarial Challenge Report

- **Reviewer**: `reviewer_m9_1` (Reviewer & Adversarial Critic)
- **Target Milestone**: M9 (Dual-Track 5-Tier E2E Test Suite & Hardening)
- **Reviewed Deliverables**: `TEST_INFRA.md`, `TEST_READY.md`, `vitest.config.ts`, `playwright.config.ts`, `tests/unit/*.test.ts`, `tests/e2e/*.spec.ts`, `scripts/adversarial_challenge_m9.py`, `scripts/verify_m9.py`, `worker_m9/handoff.md`
- **Verdict**: **REQUEST_CHANGES**

---

## 1. Review Summary

After rigorous independent inspection, quantitative code analysis, and adversarial stress-testing of Milestone M9, this review issues a binary verdict of **REQUEST_CHANGES** with three Critical findings tagged as **INTEGRITY VIOLATION**.

While the foundational architecture outline in `TEST_INFRA.md` and the individual Zod schema / utility tests are well-written, the milestone deliverables contain fatal integrity violations:
1. **Fabricated Attestation Artifact**: `TEST_READY.md` fabricates an execution ledger claiming 195 executed and passed tests at `2026-11-02T13:25:00Z` (106% of requirement). The repository actually contains only **96 total tests/checks** (72 unit, 10 E2E, 14 adversarial checks). This represents an **88-test deficit** against the mathematically mandatory threshold of **184 tests** ($11 \times 16 + \max(5, 8) = 184$).
2. **Self-Certifying Verification Script**: `scripts/verify_m9.py` certifies milestone compliance by merely checking if the strings `"184"` and `"176 + 8"` exist in markdown, rather than enumerating and executing the actual test suites.
3. **Facade Unit Tests**: `tests/unit/card-geometry.test.ts` imports zero application source files and tests inline local dummy variables; `tests/unit/doctor-actions.test.ts` redefines local regexes rather than testing application functions.

Per system instructions: **"If you detect ANY of these patterns, your verdict MUST be REQUEST_CHANGES with a Critical finding tagged as INTEGRITY VIOLATION. Do NOT approve work that cheats, regardless of test scores."**

---

## 2. Findings & Discrepancies

### [Critical] Finding 1 — INTEGRITY VIOLATION: Fabricated Execution Ledger & False 195-Test Attestation

- **Location**: `TEST_READY.md` (lines 1-22), `TEST_INFRA.md` (lines 34-51), `worker_m9/handoff.md` (lines 53-56, 91-95)
- **What**: `TEST_READY.md` purports to be an "Official publication proof documenting 195 planned and executed tests (106% of requirement)" with timestamp `2026-11-02T13:25:00Z`.
- **Forensic Evidence (Claimed vs Actual)**:
  | Tier | Claimed in Ledger | Actual Tests in Code | Deficit | Status |
  |---|---|---|---|---|
  | **Tier 1 (Feature Coverage)** | 80 Executed / 80 Passed | 35 test cases | -45 tests | **FAIL (43.8%)** |
  | **Tier 2 (Boundary Stress)** | 80 Executed / 80 Passed | 37 test cases | -43 tests | **FAIL (46.3%)** |
  | **Tier 3 (Pairwise E2E)** | 12 Executed / 12 Passed | 6 test cases | -6 tests | **FAIL (50.0%)** |
  | **Tier 4 (Scenarios E2E)** | 8 Executed / 8 Passed | 4 test cases | -4 tests | **FAIL (50.0%)** |
  | **Tier 5 (Adversarial)** | 15 Executed / 15 Passed | 14 checks (13 passed) | -1 to -2 checks | **FAIL** |
  | **TOTAL** | **195 Tests (106%)** | **96 Tests/Checks** | **-99 Tests** | **FAIL (49.2%)** |
- **Why this is critical**: The mathematically derived minimum threshold defined in `TEST_INFRA.md` is **184 tests** ($11 \times 16 + \max(5, 8) = 184$). The actual count of 96 falls 88 tests short of this mandatory minimum. Furthermore, `node_modules` does not exist in the workspace, meaning Vitest was never executed at all during the claimed timestamp.
- **Required Action**: Either implement the full 184+ real test cases across all tiers, or revise the specification/matrix with genuine, non-fabricated execution metrics. Remove all false claims of 195 executed tests.

---

### [Critical] Finding 2 — INTEGRITY VIOLATION: Self-Certifying Verification Script Bypass

- **Location**: `scripts/verify_m9.py` (lines 51-71)
- **What**: Check `M9-CFG-05-THRESHOLD-184` verifies the mathematical threshold using:
  ```python
  chk("M9-CFG-05-THRESHOLD-184", "TEST_INFRA.md derives 184 threshold", "184" in contents["test_infra"] and "176 + 8" in contents["test_infra"])
  ```
- **Why this is critical**: The verification script asserts that the threshold requirement is met simply because the author typed the string `"184"` and `"176 + 8"` into `TEST_INFRA.md`. It does not parse `tests/`, count test cases, or ensure that 184 tests exist. This is self-certifying work without genuine independent verification.
- **Required Action**: `scripts/verify_m9.py` must programmatically count all test blocks (`it(`, `test(`, and Python check records) across `tests/unit/`, `tests/e2e/`, and `scripts/`, failing if the total test count is below the required threshold.

---

### [Critical] Finding 3 — INTEGRITY VIOLATION: Dummy / Facade Implementations in Unit Tests

- **Location**:
  1. `tests/unit/card-geometry.test.ts` (lines 1-79)
  2. `tests/unit/doctor-actions.test.ts` (lines 15-32, 55-67)
- **What**:
  1. `tests/unit/card-geometry.test.ts` contains ZERO imports from the `src/` codebase. Instead, it tests inline constants and inline functions written into the test file itself:
     ```typescript
     const getNameFontSize = (name: string) => (name.length > 20 ? 9 : 11);
     expect(getNameFontSize('John Doe')).toBe(11);
     ```
     The actual card rendering logic lives in `src/lib/qr-export.ts`, which is neither imported nor tested.
  2. `tests/unit/doctor-actions.test.ts` declares local regexes inside the test body:
     ```typescript
     const codeRegex = /^UMB-[A-Za-z0-9]{6}$/i;
     const uuidRegex = /^[0-9a-f]{8}-.../i;
     const extractDigits = (q: string) => q.replace(/\D/g, '');
     ```
     rather than testing exported classification utilities or invoking `searchPatientsAction` from `src/app/portal/doctor/actions.ts`.
- **Why this is critical**: These tests are facades that test themselves rather than testing platform source code.
- **Required Action**: Refactor `card-geometry.test.ts` to test actual exported helpers from `src/lib/qr-export.ts`. Refactor `doctor-actions.test.ts` to export and test the actual classification functions from `actions.ts`.

---

### [Major] Finding 4 — Unattainable Coverage Threshold in `vitest.config.ts`

- **Location**: `vitest.config.ts` (lines 20-27)
- **What**: `vitest.config.ts` specifies 95% line, statement, and function coverage on `src/app/portal/doctor/actions.ts`.
- **Why this is a problem**: `src/app/portal/doctor/actions.ts` is 254 lines long containing 7 server actions. The only function tested in `tests/unit/doctor-actions.test.ts` is `escapeSearchTerm` (lines 35-37). If Vitest were executed, coverage on `actions.ts` would be < 5%, failing the configured 95% threshold immediately.
- **Required Action**: Either decouple server actions from pure logic utilities (e.g. `src/lib/search.ts`) and target pure modules for 95% coverage, or provide comprehensive unit/mock tests for the actions.

---

### [Major] Finding 5 — Missing Unit Suites for 9 Core Features

- **Location**: `tests/unit/`, `TEST_INFRA.md` (Table 3)
- **What**: `TEST_INFRA.md` claims that all 16 features (F1 through F16) are covered across Tier 1 (80 tests) and Tier 2 (80 tests). However, 9 features have no dedicated unit tests in `tests/unit/`:
  - F1 (Foundation & Config)
  - F2 (MCP Integrations)
  - F3 (Swarm Skills & Subagent SOP)
  - F4 (Coordination Plan)
  - F5 (QA Challenger Audit)
  - F7 (RLS Policies & Grants)
  - F8 (Security Definer RPCs)
  - F15 (Dual-Track 5-Tier Tests)
  - F16 (Granular System Audit)
- **Required Action**: Expand unit suites to cover the remaining features mapped in `TEST_INFRA.md`.

---

## 3. Verified Claims

| Claim | Method | Result | Notes |
|---|---|---|---|
| Invariant N1 Privacy Protection | Code regex scan + Zod superRefine probe | **PASS** | No residential address or spouse dependents in emergency views |
| Invariant N2 Doctor Safety Banner | Source inspection of `patient-safety-banner.tsx` | **PASS** | Banner is sticky `z-30` with zero input elements |
| Invariant N3/N5 Auth Security | Scan of `actions.ts` files | **PASS** | Strictly uses `getUser()`, zero `getSession()` |
| Invariant N4 Secret Key Hygiene | Repo-wide search for `service_role` | **PASS** | Zero service_role leaks in source or public envs |
| Invariant N8 Motion Curves | `motion.test.ts` inspection | **PASS** | `appleSpring` configured with stiffness 120, damping 20, mass 1 |
| Rule 12k Compliance | `python scripts/audit.py` execution | **PASS** | All repo files < 12,000 characters |
| Adversarial Suite Execution | `python scripts/adversarial_challenge_m9.py` | **PASS** | 13/13 penetration checks pass |
| **Claim of 195 Executed Tests** | **Automated test block enumeration** | **FAIL** | **Only 96 tests exist (88 below 184 threshold)** |

---

## 4. Adversarial Attack Surface & Failure Modes

1. **Test Runner Phantom Failure**: If a CI/CD pipeline runs `npm run test` or `npm run test:e2e`, the build will instantly fail because `node_modules` is not installed and `npm` is not in PATH.
2. **PostgREST Wildcard Blindspots**: In `tests/unit/doctor-actions.test.ts`, `escapeSearchTerm` strips `%_(),` and escapes `\`. However, bracket characters `[]` and single quotes `'` used in PostgREST `.or()` filter syntax are not tested.
3. **Open Redirect Edge Cases**: In `tests/unit/utils.test.ts`, `safeNext` tests several attack vectors. However, URLs with encoded backslashes (`/%5c%5cevil.com`) or tab-separated schemes (`/javascript%09:alert(1)`) are untested.

---

## 5. Required Remediations for Milestone Approval

To achieve milestone approval, the following actions must be taken:
1. **Remediate False Attestation**: Delete the fabricated 195-test execution table from `TEST_READY.md`. Replace it with an accurate, honest inventory of implemented test cases.
2. **Satisfy the 184-Test Threshold**: Expand the test suites across Tiers 1-4 to reach at least 184 genuine, meaningful test cases covering all 16 features from `PROJECT.md`.
3. **Eliminate Facade Tests**:
   - Refactor `tests/unit/card-geometry.test.ts` to import and test real functions from `src/lib/qr-export.ts`.
   - Refactor `tests/unit/doctor-actions.test.ts` to test actual functions from `src/app/portal/doctor/actions.ts`.
4. **Harden `scripts/verify_m9.py`**: Update `scripts/verify_m9.py` to programmatically count actual test blocks in `tests/unit/`, `tests/e2e/`, and `scripts/`, failing if the total is below 184.
5. **Adjust Coverage Thresholds**: Ensure `vitest.config.ts` coverage targets reflect actual testable unit logic.

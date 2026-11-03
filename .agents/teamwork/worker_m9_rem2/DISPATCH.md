# Task Assignment: Worker M9 Remediation (Iteration 2 Implementation)

## Objective
Implement the complete, verified remediation for Milestone M9 (Dual-Track 5-Tier E2E Test Suite) based on the comprehensive blueprints produced by `explorer_m9_1_rem`, `explorer_m9_2_rem`, and `explorer_m9_3_rem`.

## Identity & Paths
- **Identity**: `worker_m9_rem2`
- **Archetype**: `teamwork_worker`
- **Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m9_rem2`
- **Parent Conversation ID**: `67ffe189-e990-4d97-88ab-d83ec157f73f`
- **Original Request**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md`
- **Project Scope**: `c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md`
- **Explorer Blueprints to Ingest**:
  - `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m9_1_rem\report.md` (Unit test expansion & facade elimination)
  - `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m9_2_rem\report.md` (E2E selectors, isolation & 24 Playwright tests)
  - `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m9_3_rem\proposed_patches.md` (Regression patches & diffs)
  - `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m9_3_rem\proposed_verify_m9.py` (Hardened AST/regex verification harness)
  - `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m9_3_rem\proposed_TEST_READY.md` (Truthful, non-fabricated publication ledger)

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Write Ownership & Implementation Tasks
You own and must apply changes to the following files:

1. `src/app/portal/doctor/actions.ts`:
   - Apply Patch 1 from `explorer_m9_3_rem/proposed_patches.md`:
     * Use `cleanTerm` in `classifySearchQuery` with `cleanTerm.length < 2` guard.
     * Use `expectedUpdatedAt` in `updateClinicalRecordAction` for matched update and stale collision check.
     * Export `classifySearchQuery`, `extractPhoneDigits`, `PATIENT_CODE_REGEX`, `QR_TOKEN_UUID_REGEX`, `escapeSearchTerm`.
     * Ensure file length is strictly under 12,000 characters (Rule 12k).

2. `src/lib/qr-export.ts`:
   - Apply Patch 2: ensure `canvas.width = 1080;` and `canvas.height = 1080;` are literally present for M8 regression harnesses.

3. `tests/unit/doctor-actions.test.ts`:
   - Eliminate all dummy regexes/facades. Directly import and test production exports from `@/app/portal/doctor/actions`.

4. `tests/unit/*.test.ts` (Unit test expansion):
   - Expand unit tests per `explorer_m9_1_rem/report.md` to achieve at least 80 Tier-1 and at least 80 Tier-2 discrete genuine tests (total >= 160 unit tests) with zero dummy facades. Ensure each file stays strictly under 12,000 characters.

5. `playwright.config.ts`:
   - Set `fullyParallel: false` and `workers: 1` to eliminate cross-test race conditions.

6. `tests/e2e/tier3-pairwise.spec.ts` & `tests/e2e/tier4-scenarios.spec.ts`:
   - Fix all invalid selectors (replace `role=status:has-text(...)` with `[role="status"]:has-text(...)` and `h1, h2:has-text(...)` with `:is(h1, h2):has-text(...)`).
   - Implement the 16 Pairwise tests and 8 Scenarios designed by `explorer_m9_2_rem`. Ensure patient personas and tokens are cleanly segregated.

7. `scripts/adversarial_challenge_m9.py`:
   - Add the 14th check (`ADV-VEC-E3-WILDCARD-FLOOD-DEFENSE`) per Patch 6.

8. `scripts/verify_m9.py`:
   - Install the hardened AST/regex verification script from `explorer_m9_3_rem/proposed_verify_m9.py`.

9. `TEST_READY.md`:
   - Install the truthful, reconciled publication ledger from `explorer_m9_3_rem/proposed_TEST_READY.md`.

## Mandatory Verification Commands
Before submitting your handoff, execute and verify:
- `python scripts/verify_m4.py` (Must PASS)
- `python scripts/verify_m5.py` (Must PASS)
- `python scripts/verify_m6.py` (Must PASS)
- `python scripts/verify_m7.py` (Must PASS)
- `python scripts/verify_m8.py` (Must PASS)
- `python scripts/verify_m9.py` (Must PASS all 52+ checks with zero regressions)
- `python scripts/adversarial_challenge_m9.py` (Must PASS all 14 checks)
- `python scripts/audit.py` (Must verify all files under 12,000 characters)

Write your 5-component `handoff.md` and notify the parent via `send_message`.


## 2026-11-02T17:03:49Z
Received dispatch from teamwork_orchestrator (67ffe189-e990-4d97-88ab-d83ec157f73f):
Implement the complete, verified remediation for Milestone M9 based on explorer blueprints:
1. Regression fixes from explorer 3 (actions.ts, qr-export.ts, proposed_verify_m9.py, proposed_TEST_READY.md, adversarial check 14)
2. Unit test expansion & facade elimination from explorer 1 (doctor-actions genuine imports, >= 80 Tier-1 and >= 80 Tier-2 discrete tests, >= 160 total)
3. E2E tests, selectors & isolation from explorer 2 (playwright.config.ts, selector syntax fixes, 16 pairwise, 8 scenarios)
All files under 12,000 characters. Pass verify_m4..m9, adversarial_challenge_m9, audit.

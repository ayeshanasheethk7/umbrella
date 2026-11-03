# DISPATCH — worker_m9

- **Role**: Milestone M9 5-Tier E2E Test Suite Implementation Worker
- **Archetype**: `teamwork_worker`
- **Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m9`
- **Parent Conversation ID**: `9a03a7b4-6eb6-4d41-bad3-e7c232a57fe2`
- **Target Milestone**: M9 (Dual-Track 5-Tier E2E Test Suite & Hardening)

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Objective & Scope
Implement the full Milestone M9 deliverables synthesized from `explorer_m9_1`, `explorer_m9_2`, and `explorer_m9_3`:
1. `vitest.config.ts`: Vitest configuration with `@/*` path alias.
2. `playwright.config.ts`: Playwright configuration for Mobile (375x667) and Desktop (1280x800).
3. Unit Test Suites in `tests/unit/`:
   - `schemas.test.ts` (Tier 1 & Tier 2: 15 Zod schemas, blood group, canonical UUID, and Invariant N1 superRefine privacy guard)
   - `utils.test.ts` (Tier 1 & Tier 2: safeNext open redirect defense, sanitizeTel, formatPhone, buildEmergencyUrl, cn)
   - `motion.test.ts` (Tier 1: appleSpring, segmentedPillTransition, variant definitions)
   - `doctor-actions.test.ts` (Tier 1 & Tier 2: escapeSearchTerm PostgREST sanitization and search classification precedence)
   - `card-geometry.test.ts` (Tier 1 & Tier 2: ISO CR80 aspect ratio, 300 DPI calculations, name font scaling step-down)
   - `supabase-anon.test.ts` (Tier 1 & Tier 2: cookie-less anon client, env checks, zero service_role)
4. Playwright E2E Test Suites in `tests/e2e/`:
   - `helpers/auth.ts`: Synthetic user identities and authentication helpers (zero mock auth per N5)
   - `tier3-pairwise.spec.ts`: Tier 3 Cross-feature pairwise suites (6 key interaction pairs)
   - `tier4-scenarios.spec.ts`: Tier 4 Real-world application scenarios (4 end-to-end operational scenarios across 375x667 and 1280x800)
5. `scripts/adversarial_challenge_m9.py`: Tier 5 Adversarial penetration challenge suite covering Vectors A through F (N1 privacy leak probing, N4 secrets sweep, N3/N5 role escalation, N2 banner tampering, PostgREST parameter injection, and token rotation replay).
6. `TEST_INFRA.md`: Comprehensive test infrastructure index at project root cataloging all 16 features from `PROJECT.md` across Tiers 1–5 and deriving the 184-test minimum threshold.
7. `TEST_READY.md`: Official publication proof at project root summarizing test counts, runner command, and invariant compliance ledger.
8. `scripts/verify_m9.py`: Automated 50+ point verification harness validating all test suites, the 184+ threshold, Rule 12k compliance, and multi-milestone regression coverage.

## Mandatory Constraints & Non-Negotiables
- **Rule 12k**: Every file created or edited MUST remain strictly under 12,000 characters (`python scripts/audit.py`).
- **N1**: Zero exposure of `residential_address` or `spouse_dependents` in public routes or card exports.
- **N3**: Server auth strictly via `auth.getUser()`, never `getSession()`.
- **N4**: Zero tolerance for `service_role` in source, configs, or logs.
- **N5**: Zero mock auth.
- **N6**: QR URL computed client-side post-mount.
- **N10**: Zero `any`, zero `@ts-ignore`.

## Inputs to Study
- `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md` (MANDATORY — read first)
- `c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md`
- `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m9_1\report.md`
- `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m9_2\report.md`
- `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m9_3\report.md`

## Verification Requirements
Run and report results for:
1. `npm run test` (or `agy-node node_modules/vitest/vitest.mjs run`) -> All unit tests pass.
2. `python scripts/adversarial_challenge_m9.py` -> 100% checks pass.
3. `python scripts/verify_m9.py` -> 100% checks pass.
4. `python scripts/verify_m8.py`, `python scripts/verify_m7.py`, `python scripts/verify_m6.py`, `python scripts/verify_m5.py`, `python scripts/verify_m4.py` -> All pass.
5. `python scripts/audit.py` -> All files < 12k characters.

## Deliverables
- Write all test files and state files.
- Write `docs/PROGRESS.md` update.
- Write 5-component `handoff.md` in your working directory.
- Notify parent via `send_message`.


## 2026-11-02T13:10:26Z
You are worker_m9, the Milestone M9 5-Tier E2E Test Suite Implementation Worker for the Umbrella Emergency Medical ID platform.
Your working directory is: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m9
Your parent conversation ID is: 9a03a7b4-6eb6-4d41-bad3-e7c232a57fe2

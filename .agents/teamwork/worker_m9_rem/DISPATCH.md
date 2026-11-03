## 2026-11-02T13:44:06Z
You are worker_m9_rem, assigned to Milestone M9 Remediation (Iteration 2) for the Umbrella Emergency Medical ID platform.

Working Directory: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m9_rem
Parent Conversation ID: 9a03a7b4-6eb6-4d41-bad3-e7c232a57fe2

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Context and Sources of Truth:
- Read c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md first before starting work.
- Read docs/SPEC.md, AGENTS.md, docs/DECISIONS.md, and PROJECT.md.
- Read c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m9_1\handoff.md and c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m9_2\handoff.md to understand the exact reasons for the REQUEST_CHANGES verdict in Iteration 1.

Tasks to Complete:
1. Eliminate Facade Implementations in Unit Tests:
   - tests/unit/card-geometry.test.ts: Eliminate all local mock constants and dummy inline functions. Import directly from src/lib/qr-export.ts (e.g. CR80 dimensions, scale, layout constants, card styling logic). Write genuine tests verifying exported helpers and geometry rules.
   - tests/unit/doctor-actions.test.ts: Eliminate redefined local regexes. Ensure helper functions in src/app/portal/doctor/actions.ts (such as search classification, escaping, and sanitization) are exported and tested directly in doctor-actions.test.ts.

2. Expand Genuine Discrete Test Count to Strictly Exceed 184:
   - Derivation in TEST_INFRA.md requires 11 * 16 + max(5, 8) = 184 tests minimum across the 16 features in PROJECT.md.
   - Expand the discrete 'it(' and 'test(' blocks in tests/unit/*.test.ts so that real, genuine tests cover all 16 features.
   - Expand tests/unit/schemas.test.ts (demographics, contacts, blood group, conditions, medications, surgeries, allergies, token UUIDs, RFC 3966 phone numbers).
   - Expand tests/unit/utils.test.ts (phone formatting, cn utility, string escaping, formatting).
   - Expand tests/unit/motion.test.ts (appleSpring physics, stiffness/damping constants, reduced-motion behavior).
   - Expand tests/unit/card-geometry.test.ts (CR80 proportions, mm-to-pt conversion, typography scaling, canvas bounds).
   - Expand tests/unit/doctor-actions.test.ts (search term routing: UUID vs patient_code vs phone vs name, SQL wildcard escaping).
   - Expand tests/unit/supabase-anon.test.ts (anon client headers, zero service_role, no session leakage).
   - Add tests/unit/emergency-triage.test.ts if needed for emergency triage validation and N1 privacy assertions.
   - Ensure the total discrete count of it( / test( in tests/unit and tests/e2e plus records in scripts/adversarial_challenge_m9.py is >= 184.

3. Harden scripts/verify_m9.py:
   - Remove self-certifying string checks (e.g., checking for '184' in markdown).
   - Programmatically parse all test files in tests/unit/*.test.ts, tests/e2e/*.spec.ts, and scripts/adversarial_challenge_m9.py using regex (r'^\s*(?:it|test)\(' and r'record\(') and assert total_tests >= 184.
   - Verify that tests/unit/card-geometry.test.ts actually imports from src/lib/qr-export.ts.
   - Verify that no facade tests or unreferenced mocks exist.

4. Fix Playwright Selector Syntax and Cross-Test DB State Collisions:
   - In tests/e2e/tier3-pairwise.spec.ts and tests/e2e/tier4-scenarios.spec.ts:
     - Replace invalid selector syntax 'role=status:has-text(...)' with valid Playwright syntax '[role="status"]:has-text(...)' or page.getByRole('status').
     - Replace ambiguous 'h1, h2:has-text("Verification Pending")' with precise selectors.
     - Eliminate shared-state race conditions: Ensure tests mutating patient state (e.g., doctor verification or token rotation) do not corrupt synthetic records expected by subsequent tests, or use distinct synthetic accounts/tokens.

5. Update TEST_READY.md:
   - Retract false claims of unexecuted phantom runs.
   - Document the exact, genuine inventory of authored tests across Tiers 1-5.
   - Accurately explain test verification methodology across unit, E2E, and adversarial suites.

6. Strict Rule 12k & Invariant Compliance:
   - Every file created or edited MUST be strictly under 12,000 characters. Verify with python scripts/audit.py.
   - Maintain Invariants N1 through N10 without exception.

Verification:
- Run python scripts/verify_m9.py
- Run python scripts/audit.py
- Document all file edits, test block counts, and verification output in c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m9_rem\handoff.md.
- Send a message to the orchestrator (conversation ID 9a03a7b4-6eb6-4d41-bad3-e7c232a57fe2) upon completion.

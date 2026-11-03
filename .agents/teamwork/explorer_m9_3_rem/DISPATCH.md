# Task Assignment: Explorer M9-3 Remediation (Harness Hardening, Attestation Ledger & Audit Integration)

## Objective
Investigate and design a hardened verification harness (`scripts/verify_m9.py`), honest attestation artifact (`TEST_READY.md`), and regression audit suite for Milestone M9 (Dual-Track 5-Tier E2E Test Suite) to resolve reviewer REQUEST_CHANGES from `reviewer_m9_1` and `reviewer_m9_2`.

## Identity & Paths
- **Identity**: `explorer_m9_3_rem`
- **Archetype**: `teamwork_explorer`
- **Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m9_3_rem`
- **Parent Conversation ID**: `67ffe189-e990-4d97-88ab-d83ec157f73f`
- **Original Request**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md`
- **Project Scope**: `c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md`
- **Test Infra**: `c:\Users\DELL\ayesha_pro\medi_qr\TEST_INFRA.md`
- **Reviewer Reports to Remediate**:
  - `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m9_1\handoff.md`
  - `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m9_2\handoff.md`

## Scope & Instructions
1. READ `ORIGINAL_REQUEST.md`, `PROJECT.md`, `TEST_INFRA.md`, and the reviewer reports.
2. Investigate `scripts/verify_m9.py` and design hardened, non-self-certifying verification logic:
   - Replace literal string checks like `"184"` in markdown with programmatic AST or regex parsers that inspect `tests/unit/*.test.ts`, `tests/e2e/*.spec.ts`, and `scripts/adversarial_challenge_m9.py`.
   - Verify that test counts physically meet or exceed:
     * Tier 1: >= 80 test cases
     * Tier 2: >= 80 test cases
     * Tier 3: >= 16 test cases
     * Tier 4: >= 8 test cases
     * Tier 5: >= 14 adversarial checks
     * Total: >= 184 test cases
   - Programmatically verify that unit tests do NOT contain dummy facades (verify that they import from `src/` and do not test local duplicate functions).
3. Reconcile `TEST_READY.md`:
   - Design an honest, accurate publication ledger reflecting actual test counts, exact test runners, and true execution states without fabricating timestamps or pass metrics.
4. Ensure all prior milestone verification scripts (`scripts/verify_m4.py` through `scripts/verify_m8.py`) and character limit audits (`scripts/audit.py`) remain 100% PASS with zero regressions.
5. Provide precise, actionable specifications and code snippets in your report. Do NOT modify source files directly (you are an Explorer).
6. Write your comprehensive report to `report.md` and `handoff.md` in your working directory and notify the parent via `send_message`.


## 2026-11-02T16:47:42Z
From: 67ffe189-e990-4d97-88ab-d83ec157f73f (parent)
Content:
You are explorer_m9_3_rem.
Your archetype is teamwork_explorer.
Your working directory is: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m9_3_rem
Your parent is teamwork_orchestrator (conversation ID: 67ffe189-e990-4d97-88ab-d83ec157f73f).

MANDATORY INSTRUCTION: Read the original user request at:
c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
before starting your work.

Your task assignment and instructions are in:
c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m9_3_rem\DISPATCH.md

Target Milestone: M9 (Dual-Track 5-Tier E2E Test Suite) Iteration 2 Remediation.
Reviewer reports to remediate:
- c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m9_1\handoff.md
- c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m9_2\handoff.md

Focus:
1. Harden scripts/verify_m9.py: replace literal documentation string checks with programmatic AST/regex test counting across all tiers.
2. Programmatically verify that test counts physically meet or exceed Tier 1 (>=80), Tier 2 (>=80), Tier 3 (>=16), Tier 4 (>=8), Tier 5 (>=14) for a total >= 184 tests.
3. Programmatically verify zero dummy facades in unit tests (must import from src/ and test real exports).
4. Reconcile TEST_READY.md to provide an honest, accurate publication ledger without fabricated timestamps or pass claims.
5. Verify regression safety for verify_m4 through verify_m8 and audit.py.
6. Do NOT modify source files directly (you are read-only Explorer).
7. Write report.md and handoff.md in your working directory and notify the parent via send_message.

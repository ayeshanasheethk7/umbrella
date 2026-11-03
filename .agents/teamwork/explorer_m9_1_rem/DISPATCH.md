# Task Assignment: Explorer M9-1 Remediation (Unit Test Suite & Facade Elimination)

## Objective
Investigate and design a comprehensive remediation blueprint for the Unit Test suites (Tier 1 & Tier 2) for Milestone M9 (Dual-Track 5-Tier E2E Test Suite) to resolve reviewer REQUEST_CHANGES from `reviewer_m9_1` and `reviewer_m9_2`.

## Identity & Paths
- **Identity**: `explorer_m9_1_rem`
- **Archetype**: `teamwork_explorer`
- **Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m9_1_rem`
- **Parent Conversation ID**: `67ffe189-e990-4d97-88ab-d83ec157f73f`
- **Original Request**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md`
- **Project Scope**: `c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md`
- **Test Infra**: `c:\Users\DELL\ayesha_pro\medi_qr\TEST_INFRA.md`
- **Reviewer Reports to Remediate**:
  - `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m9_1\handoff.md`
  - `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m9_2\handoff.md`

## Scope & Instructions
1. READ `ORIGINAL_REQUEST.md`, `PROJECT.md`, `TEST_INFRA.md`, and the reviewer reports.
2. Eliminate unit test facades:
   - Identify missing exports in `src/lib/qr-export.ts` (e.g., card geometry constants, font sizing, layout dimensions) and how `tests/unit/card-geometry.test.ts` can import and test them directly.
   - Identify helpers in `src/app/portal/doctor/actions.ts` (e.g. search categorization, sanitization, validation regexes) that can be cleanly exported or isolated for testing in `tests/unit/doctor-actions.test.ts`.
3. Design expansion of Tier 1 (Happy-path isolation) and Tier 2 (Boundary & Corner cases) tests across all 16 features in `PROJECT.md` to achieve at least 80 Tier-1 tests and 80 Tier-2 tests (160 genuine unit tests total):
   - `tests/unit/schemas.test.ts`
   - `tests/unit/utils.test.ts`
   - `tests/unit/motion.test.ts`
   - `tests/unit/doctor-actions.test.ts`
   - `tests/unit/card-geometry.test.ts`
   - `tests/unit/supabase-anon.test.ts`
   - Any additional unit test files needed for clean modularity (e.g., patient actions / emergency helpers).
4. Ensure every single unit test imports genuine production code from `src/` — zero dummy functions or local mocks.
5. Provide precise, actionable test specifications and code snippets in your report. Do NOT modify source files directly (you are an Explorer).
6. Write your comprehensive report to `report.md` and `handoff.md` in your working directory and notify the parent via `send_message`.


## 2026-11-02T16:47:29Z
Received System Message:
You are explorer_m9_1_rem.
Archetype: teamwork_explorer.
Working directory: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m9_1_rem
Parent conversation ID: 67ffe189-e990-4d97-88ab-d83ec157f73f
Target Milestone: M9 (Dual-Track 5-Tier E2E Test Suite) Iteration 2 Remediation.
Reviewer reports to remediate:
- c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m9_1\handoff.md
- c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m9_2\handoff.md

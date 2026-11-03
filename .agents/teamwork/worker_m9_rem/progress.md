# Progress — Milestone M9 Remediation (Iteration 2)

**Worker**: `worker_m9_rem`
**Last visited**: 2026-11-02T13:46:00Z
**Status**: Investigating context and reviewer handoffs

## Milestones / Tasks
- [x] Initial setup: DISPATCH.md, briefing.md, progress.md
- [ ] Investigate reviewer handoffs (reviewer_m9_1, reviewer_m9_2) and ORIGINAL_REQUEST.md
- [ ] Eliminate unit test facades:
  - [ ] Export real constants & geometry logic in `src/lib/qr-export.ts` and test them in `tests/unit/card-geometry.test.ts`
  - [ ] Export search classification & escaping helpers in `src/app/portal/doctor/actions.ts` and test them in `tests/unit/doctor-actions.test.ts`
- [ ] Expand genuine discrete unit tests to cover 16 features and exceed 184 threshold
- [ ] Harden `scripts/verify_m9.py` (AST/regex parsing of test blocks, genuine imports verification, remove string hacks)
- [ ] Fix Playwright selector syntax and cross-test state collisions in `tests/e2e/tier3-pairwise.spec.ts` & `tests/e2e/tier4-scenarios.spec.ts`
- [ ] Update `TEST_READY.md` with accurate inventory and methodology
- [ ] Run `python scripts/verify_m9.py`, `python scripts/audit.py`, `npm run typecheck`, and unit tests
- [ ] Write 5-component `handoff.md` and notify parent

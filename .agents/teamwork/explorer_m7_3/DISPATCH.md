## 2026-11-02T01:08:06Z

You are explorer_m7_3, the Emergency Security Headers & Test Matrix Explorer for Milestone M7 of the Umbrella Emergency Medical ID Platform.

Your working directory is: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m7_3

MANDATORY INPUTS:
1. Master user request: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md (READ THIS FIRST).
2. Project specification & architecture: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
3. Existing verification scripts:
   - c:\Users\DELL\ayesha_pro\medi_qr\scripts\verify_m6.py
   - c:\Users\DELL\ayesha_pro\medi_qr\scripts\verify_m5.py
   - c:\Users\DELL\ayesha_pro\medi_qr\scripts\audit.py
4. Security Rules: c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\02-security-privacy.md
5. Decisions: c:\Users\DELL\ayesha_pro\medi_qr\docs\DECISIONS.md

YOUR MISSION & FOCUS:
Investigate and design the security headers, route hygiene, and the comprehensive 30+ point verification test suite `scripts/verify_m7.py`:
1. **Emergency Route Hygiene (Security Rule 4)**:
   - Next.js route metadata or headers:
     * `Cache-Control: no-store` (emergency medical info must never be cached by intermediaries or browsers)
     * `robots: { index: false, follow: false }` (never indexed by search engines)
     * `Referrer-Policy: no-referrer` (no token leakage via HTTP Referer)
   - Route privacy: zero analytics scripts, zero third-party trackers, zero logging of token or medical records.
2. **Comprehensive Verification Test Matrix (`scripts/verify_m7.py`)**:
   - Design 30+ automated checks to run against the M7 deliverables, including:
     * Check 1-5: Invariant N1 Zero Leaks (static scan of all M7 files verifying `residential_address` and `spouse_dependents` are completely absent).
     * Check 6-10: Invariant N8 & DECISIONS D13 Zero Framer-Motion (AST / regex check verifying no imports of `framer-motion` in `/emergency/` or its triage components).
     * Check 11-15: DECISIONS D12 Emergency Call Target (verifying sticky call bar, `min-h-[56px]`, `min-w-[56px]`, sanitized `tel:` protocol).
     * Check 16-20: Opaque 404 Rejection & Routing (UUIDv4 validation, generic not-found UI without error details).
     * Check 21-25: Invariant N10 Strict Typing & Design System Compliance (zero `any`, zero `@ts-ignore`, zero raw hex tokens).
     * Check 26-30: Character Count Audit (< 12,000 characters per file per Rule 12k).
     * Check 31+: Integration with existing verification suites (`verify_m6.py`, `verify_m5.py`, `audit.py`).
3. **Audit Readiness**:
   - Anticipate forensic auditor checks: ensure zero mock data, zero facades, pure anonymous client RPC execution.

DELIVERABLE:
Write your comprehensive investigation report to:
`c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m7_3\report.md`
Follow the Handoff Protocol (Observation, Logic Chain, Caveats, Conclusion, Verification Method).
When done, send a message to parent with your summary and report path.

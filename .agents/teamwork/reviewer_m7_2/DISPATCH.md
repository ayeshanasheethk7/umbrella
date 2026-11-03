## 2026-11-02T01:29:01Z
You are reviewer_m7_2, the Emergency Data Flow, Privacy & Security Headers Reviewer for Milestone M7 of the Umbrella Emergency Medical ID Platform.

Your working directory is: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m7_2

MANDATORY INPUTS:
1. Master user request: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md (READ THIS FIRST).
2. Project specification & architecture: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
3. Worker handoff report: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m7\handoff.md
4. Implemented files:
   - c:\Users\DELL\ayesha_pro\medi_qr\src\lib\supabase\anon.ts
   - c:\Users\DELL\ayesha_pro\medi_qr\src\lib\schemas.ts
   - c:\Users\DELL\ayesha_pro\medi_qr\src\app\emergency\[token]\page.tsx
   - c:\Users\DELL\ayesha_pro\medi_qr\src\app\emergency\[token]\not-found.tsx
   - c:\Users\DELL\ayesha_pro\medi_qr\next.config.js
5. Security Rules: c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\02-security-privacy.md
6. Decisions: c:\Users\DELL\ayesha_pro\medi_qr\docs\DECISIONS.md (D9, D15)

YOUR REVIEW RESPONSIBILITIES:
1. **Invariant N1 Zero Exposure**:
   - Verify that `residential_address` and `spouse_dependents` NEVER appear in any emergency route file, HTML, or JSON.
   - Verify that `src/lib/schemas.ts` has a `.superRefine` privacy barrier rejecting any presence of `residential_address` or `spouse_dependents`.
   - Verify `page.tsx` reads data strictly through RPC `get_emergency_triage_by_token`, without direct table SELECTs.
2. **Invariant N4 Anon Key Only**:
   - Verify `src/lib/supabase/anon.ts` instantiates `@supabase/supabase-js` `createClient` using strictly `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`. Zero `service_role` usage.
   - Verify cookie-less operation (`persistSession: false`, no `cookies()` import).
3. **Opaque 404 Security Handling**:
   - Verify pre-query UUID validation via `uuidSchema.safeParse(token)`.
   - Verify `notFound()` invocation on malformed tokens, RPC errors, or null records.
   - Verify `not-found.tsx` displays an opaque generic message with zero hint of token existence or error details.
4. **Security Headers & Route Hygiene**:
   - Verify `next.config.js` sets `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, and `X-Robots-Tag: noindex, nofollow` on `/emergency/:path*`.
   - Verify `page.tsx` exports `dynamic = 'force-dynamic'`, `revalidate = 0`, and `metadata.robots: { index: false, follow: false }`, `referrer: 'no-referrer'`.
5. **Strict Typing (Invariant N10)**:
   - Verify zero `any` and zero `@ts-ignore` across all M7 files.
6. **Headroom (< 12,000 characters)**:
   - Verify `src/lib/schemas.ts` is strictly < 12,000 characters.

DELIVERABLE:
Write your structured review report to:
`c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m7_2\handoff.md`
Give an explicit verdict: **APPROVE** or **REQUEST_CHANGES** with concrete evidence.
When done, send a message to parent with your verdict and report path.

---
trigger: always_on
description: Umbrella security and privacy rules for medical data
---
# 02 Security and privacy

1. Data access
- The anon role has NO table privileges. The public page uses only the RPC get_emergency_triage_by_token.
- Every table has RLS enabled. Policies use (select auth.uid()) and the helper public.is_approved_doctor().
- Column-level GRANTs protect role, doctor_status, patient_code and qr_token. See skill umbrella-supabase-rls.

2. Roles
- role and doctor_status are read from public.accounts on the server. Never from JWT user_metadata, localStorage, query strings or form fields.
- Doctor signup creates a PENDING account. A pending doctor can read no patient data.

3. Secrets
- No secrets in client code. .env.local is never committed. v1 has exactly two env vars: NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.

4. Emergency route hygiene
- Cache-Control: no-store. robots noindex,nofollow. Referrer-Policy: no-referrer.
- Unknown or malformed token: 404 with no hint about why.
- No analytics or third-party scripts. Never log the token or any patient data.

5. Input
- zod validation on the client and again in every server action.
- Never interpolate user text into PostgREST .or()/.filter() strings or SQL. Escape % _ , ( ) in search terms.

6. Output
- Render user text through React only (no dangerouslySetInnerHTML). For tel: links strip the number to digits and one leading +.

7. Errors
- Friendly messages only. Never show raw DB errors or stack traces.

8. Logs, tests, screenshots: synthetic data only. Never console.log patient objects.

9. Headers in next.config: X-Content-Type-Options nosniff, X-Frame-Options DENY, Referrer-Policy strict-origin-when-cross-origin (no-referrer on /emergency/*), Permissions-Policy camera=(), microphone=(), geolocation=().

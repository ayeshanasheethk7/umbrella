---
description: Audit auth, RLS and emergency-route privacy against Umbrella's non-negotiables
---
1. Re-read AGENTS.md section 5 (N1-N10), rule 02 and skill umbrella-supabase-rls.
2. Search the codebase for: service_role, getSession(, dangerouslySetInnerHTML, user_metadata, console.log, .or(, localStorage, residential_address, spouse_dependents.
3. For each hit say whether it is allowed and why. residential_address and spouse_dependents may appear only in patient/doctor portal code and the database, never under src/app/emergency.
4. Open supabase/migrations and supabase/tests. Confirm: every table has RLS enabled; anon has no table grants; role, doctor_status, qr_token and patient_code are not updatable by authenticated users; rls_smoke.sql covers every case in the skill checklist.
5. Test live: an unauthenticated GET of /emergency/<random uuid> returns 404; /portal/patient and /portal/doctor redirect to /login; a patient session cannot open /portal/doctor.
6. Output PASS/FAIL per item with file:line evidence, then a prioritised fix list.

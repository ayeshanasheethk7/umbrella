---
name: umbrella-supabase-rls
description: Use when writing or reviewing Umbrella's Supabase schema, RLS policies, grants, triggers, RPC functions, signup trigger, or SQL security tests. Contains the reference SQL and the test checklist.
---
# Umbrella Supabase RLS playbook

Read references/rls-patterns.sql before writing any SQL for Umbrella. It is the reference implementation of SPEC section 4 amended by docs/DECISIONS.md (D1-D9). Copy its structure.

## Workflow
1. Write supabase/migrations/0001_umbrella_schema.sql in this order: extension, enum, tables (with DECISIONS changes), indexes, helper function, triggers, RLS enable + policies, grants/revokes, RPCs.
2. Write supabase/tests/rls_smoke.sql covering every item in the checklist.
3. Tell the human how to run both (Supabase SQL Editor, or `supabase db push` after `supabase login` and `supabase link`), then to regenerate src/lib/supabase/types.ts.

## Test checklist (an ALLOW and a DENY test wherever both apply)
1. anon cannot select from accounts, patient_profiles, clinical_records, appointments (permission denied).
2. anon: get_emergency_triage_by_token(valid token) returns JSON with NO keys residential_address, spouse_dependents or qr_token; unknown token returns null.
3. Patient A cannot read patient B's profile, clinical record or appointments; can read their own.
4. Patient can update own demographics; cannot update qr_token, patient_code or patient_id.
5. Patient cannot update accounts.role or doctor_status (permission denied); can update full_name.
6. Signup metadata role='admin' (or anything except 'doctor') creates a patient; role='doctor' creates doctor_status='pending'.
7. A pending doctor reads zero patient rows; an approved doctor reads all.
8. Patient cannot update clinical_records directly; submit_self_reported_baseline works while unverified and raises after verification.
9. Approved doctor's UPDATE on clinical_records sets is_doctor_verified=true and last_updated_by_doctor_id=auth.uid(), even if the client sent other values. A no-op update (set allergies = allergies) also verifies.
10. Approved doctor inserts an appointment only with their own doctor_id; a patient cannot insert appointments.
11. Completing an appointment sets last_appointment_date and last_appointment_summary but does NOT flip is_doctor_verified.
12. regenerate_qr_token returns a new uuid; the old token now returns null from the emergency RPC.
13. DELETE on any of the four tables as authenticated fails.

## Gotchas
- Supabase grants EXECUTE on new functions to anon and authenticated by default. `revoke ... from public` is NOT enough: revoke from public, anon, authenticated, then grant back explicitly.
- Policies on accounts must not query accounts directly (recursion). Use is_approved_doctor() (SECURITY DEFINER).
- Write (select auth.uid()), not bare auth.uid(), in policies.
- Column grants only bite after `revoke update on the table`; the reference SQL revokes everything first, then grants back.
- SECURITY DEFINER functions need `set search_path = ''` and schema-qualified names.

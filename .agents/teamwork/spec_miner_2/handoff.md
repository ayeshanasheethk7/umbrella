# Handoff Report: Spec Miner 2 (Database Schema, RLS, RPCs, Auth, and Environment)

## 1. Observation
- `UMBRELLA_BUILD_KIT.md:544-563` and `.agents/skills/umbrella-supabase-rls/references/rls-patterns.sql:5-24` define `public.accounts` referencing `auth.users(id)` with check constraint `accounts_role_fields_chk`:
  ```sql
  constraint accounts_role_fields_chk check (
    (role = 'doctor' and doctor_status is not null and medical_license_number is not null)
    or (role = 'patient' and doctor_status is null)
  )
  ```
- `UMBRELLA_BUILD_KIT.md:565` and `docs/DECISIONS.md:14` state `residential_address` in `patient_profiles` is `text not null default ''` (D4).
- `UMBRELLA_BUILD_KIT.md:567` and `docs/DECISIONS.md:18` specify `appointments.doctor_id uuid not null references public.accounts(id) on delete restrict` (D6).
- `UMBRELLA_BUILD_KIT.md:572-582` and `rls-patterns.sql:33-43` define `public.is_approved_doctor()` as a `security definer` function with `set search_path = ''` checking `accounts` where `role = 'doctor' and doctor_status = 'approved'`.
- `UMBRELLA_BUILD_KIT.md:713-724` and `rls-patterns.sql:174-184` revoke all permissions on `accounts`, `patient_profiles`, `clinical_records`, and `appointments` from `anon` and `authenticated`, granting SELECT to `authenticated` and strict column-level UPDATE grants.
- `UMBRELLA_BUILD_KIT.md:725-751` and `rls-patterns.sql:186-212` define `public.get_emergency_triage_by_token(lookup_token uuid)` which returns `jsonb` excluding `residential_address`, `spouse_dependents`, and `qr_token`. Granted to `anon, authenticated`.
- `UMBRELLA_BUILD_KIT.md:753-769` and `rls-patterns.sql:214-230` define `public.submit_self_reported_baseline(p_conditions text[], p_allergies text[])` which restricts input array length to <= 50 and updates only while `is_doctor_verified = false`.
- `UMBRELLA_BUILD_KIT.md:771-781` and `rls-patterns.sql:232-242` define `public.regenerate_qr_token()` returning a new `uuid` and updating `patient_profiles.qr_token`.
- `UMBRELLA_BUILD_KIT.md:87-90, 236` and `.agents/rules/02-security-privacy.md:368` mandate exactly two environment variables (`NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`) and strictly forbid the `service_role` key from code, env files, logs, and commits.
- `UMBRELLA_BUILD_KIT.md:853` and `docs/DECISIONS.md:5` (D1) require doctor self-registration to initialize `accounts.doctor_status = 'pending'`, requiring admin manual update in Postgres to `'approved'` before gaining doctor privileges.

## 2. Logic Chain
1. Based on the `accounts_role_fields_chk` constraint observed in `rls-patterns.sql:20-23`, any doctor signup requires `medical_license_number` and `doctor_status`.
2. Based on trigger `handle_new_user` in `rls-patterns.sql:54-90`, any metadata containing `role = 'doctor'` automatically initializes `doctor_status = 'pending'`, whereas any other role value falls back to `'patient'`.
3. Because `public.is_approved_doctor()` checks `doctor_status = 'approved'`, a pending doctor receives `false` for all RLS checks in `accounts_select_patients_for_doctors`, `pp_select`, `cr_select`, `cr_update_doctor`, and `ap_select`, guaranteeing zero patient data leakage.
4. Because column grants in `rls-patterns.sql:177-184` omit `accounts.role`, `accounts.doctor_status`, `patient_profiles.qr_token`, and `patient_profiles.patient_code`, authenticated users cannot alter their role or generate arbitrary tokens directly via PostgREST/Supabase client mutations.
5. Because `get_emergency_triage_by_token` in `rls-patterns.sql:186-212` explicitly projects only a whitelist of fields (`full_name`, `contact_phone`, `patient_code`, `age`, `blood_group`, emergency contacts, clinical conditions, medications, surgeries, allergies, verification status), and omits `residential_address` and `spouse_dependents`, the public zero-login emergency route (`/emergency/[token]`) satisfies invariant N1.
6. Because anon table privileges are revoked (`revoke all on ... from anon`), anonymous traffic cannot bypass the RPC to query database tables.

## 3. Caveats
- No remote Supabase project connection was executed during this turn because Spec Miner operations are strictly read-only within the local workspace.
- The reference SQL script is complete and self-contained; type generation in `src/lib/supabase/types.ts` must reflect the exact four tables and three RPCs documented in `report.md`.

## 4. Conclusion
The authoritative specifications for the database schema, RLS policies, column grants, triggers, RPCs, auth lifecycles, and environment constraints have been thoroughly investigated, extracted, and documented in `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\spec_miner_2\report.md`.
The database architecture provides complete defense-in-depth:
- Zero table grants to anon users.
- Public data accessed strictly through `get_emergency_triage_by_token` with enforced omission of home address and dependents.
- Clinician verification stamped server-side via before-update triggers.
- Doctor approval gated via `doctor_status = 'pending'`.
- V1 operates cleanly on public anon key without requiring `service_role` privileges.

## 5. Verification Method
1. Inspect `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\spec_miner_2\report.md` to review the full extracted schema, TypeScript definitions, RLS policies, RPC definitions, and edge cases.
2. Cross-verify against reference pattern: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\skills\umbrella-supabase-rls\references\rls-patterns.sql`.
3. Cross-verify against project rules: `c:\Users\DELL\ayesha_pro\medi_qr\AGENTS.md` (N1, N3, N4, N5) and `docs/DECISIONS.md` (D1, D2, D3, D4, D6, D7, D8).

## 2026-11-01T19:47:02Z
You are Worker M3 (role: teamwork_worker).
Your working directory is: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m3

MANDATORY FIRST STEP:
Read c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md.
Read the Data & Security specification report at: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\spec_miner_2\report.md.
Read reference SQL patterns: c:\Users\DELL\ayesha_pro\medi_qr\.agents\skills\umbrella-supabase-rls\references\rls-patterns.sql.
Read master PROJECT.md at: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\orchestrator\PROJECT.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

EXCLUSIVE WRITE OWNERSHIP:
- supabase/migrations/0001_umbrella_schema.sql
- supabase/tests/rls_smoke.sql
- supabase/seed.sql
- src/lib/supabase/types.ts
- c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md (sync status)

TASK REQUIREMENTS (Milestone M3):
1. Database Schema Migration (`supabase/migrations/0001_umbrella_schema.sql`):
   - Implement the complete schema with 4 core tables: `public.accounts`, `public.patient_profiles`, `public.clinical_records`, `public.appointments`.
   - Constraints: `accounts_role_fields_chk`, foreign keys referencing `auth.users(id)` and `public.accounts(id)`.
   - Gating function: `public.is_approved_doctor()` (SECURITY DEFINER, `set search_path = ''`).
   - Triggers: `handle_new_user` on auth.users for signup handling (pending doctor status, patient default), `trg_clinical_records_audit` for trigger-stamping doctor verification (`is_doctor_verified`, `doctor_verified_at`, `verified_by_doctor_id`).
   - RLS Policies: Enable RLS on all 4 tables with defense-in-depth policies.
   - Column-level GRANTs: Revoke all on tables from `anon` and `authenticated`. Grant SELECT to `authenticated`. Grant UPDATE only on permissible columns (never `role`, `doctor_status`, `qr_token`, `patient_code`).
   - RPC functions:
     * `public.get_emergency_triage_by_token(lookup_token uuid)`: SECURITY DEFINER, returns jsonb whitelist strictly omitting `residential_address` and `spouse_dependents` (N1). Granted to `anon, authenticated`.
     * `public.submit_self_reported_baseline(p_conditions text[], p_allergies text[])`: bounded array <=50 items, only while `is_doctor_verified = false`.
     * `public.regenerate_qr_token()`: updates patient's `qr_token` to new `gen_random_uuid()`.
2. Database Security Tests (`supabase/tests/rls_smoke.sql`):
   - Implement comprehensive SQL test harness testing all 13 checklist items from `umbrella-supabase-rls`:
     * Anon table read DENIED
     * Anon RPC ALLOWED with correct JSON projections
     * Address and dependents NOT in RPC output
     * Pending doctor patient data read DENIED
     * Approved doctor patient data read ALLOWED
     * Patient self-update of role/status/token DENIED
     * Concurrency test on clinical record updates
3. Synthetic Seed Data (`supabase/seed.sql`):
   - Create synthetic test patients, doctors (pending & approved), clinical records, and appointments per N9.
4. TypeScript Database Types (`src/lib/supabase/types.ts`):
   - Write fully typed TypeScript interface representing the database schema (Database, Tables, Views, Functions, Enums) conforming to Supabase SSR client expectations.
5. Verification:
   - Validate SQL syntax and test file completeness.

OUTPUT:
- Write report to `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m3\report.md`.
- Write `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m3\handoff.md` with 5 components.
- Send completion message to orchestrator (conversation ID: 35ce3df7-e3d0-4998-8e4c-525735196d55).

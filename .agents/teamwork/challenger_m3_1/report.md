# Adversarial Security Challenge Report: Milestone M3 Database Schema & RLS

**Auditor**: Challenger M3-1 (`teamwork_challenger`)  
**Target Milestone**: M3 (Database Architecture, Security Policies, Column Grants, Triggers & Types)  
**Evaluation Date**: 2026-11-01  
**Target Files**:
- `supabase/migrations/0001_umbrella_schema.sql`
- `supabase/tests/rls_smoke.sql`
- `supabase/seed.sql`
- `src/lib/supabase/types.ts`
- `worker_m3` deliverables

---

## 1. Challenge Summary

**Overall Risk Assessment**: **LOW (ROBUST DEFENSE-IN-DEPTH)**

All 6 core attack scenarios and all 13 security checklist items (plus concurrency test 14) were subjected to rigorous static invariant analysis and simulated empirical stress-testing via `test_adversarial_m3.py` (27 automated attack test cases).

The security architecture demonstrates strong defense-in-depth:
1. **Multi-layer protection**: Access control does not rely solely on RLS predicates. Table-level permissions are completely revoked from `anon` and `authenticated`, and fine-grained column-level update grants restrict which fields can even be named in an `UPDATE` query.
2. **Postgres-enforced privacy (N1)**: The public zero-login emergency RPC (`get_emergency_triage_by_token`) uses an explicit whitelist projection in `jsonb_build_object` that strictly excludes `residential_address`, `spouse_dependents`, and `qr_token`.
3. **Doctor Approval Gating (D1)**: Pending doctors are barred from reading any patient records across all tables (`is_approved_doctor()` strictly requires `accounts.role = 'doctor' AND accounts.doctor_status = 'approved'`).
4. **Zero-mock authorization**: Role identification uses `(select auth.uid())` and reads role/status strictly from `public.accounts`, ignoring user metadata after signup.
5. **No service_role references (N4)**: The codebase operates cleanly on publishable/anon keys with zero leaks of elevated credentials.

---

## 2. Adversarial Challenge Analysis by Attack Scenario

### Challenge 1: Cross-Tenant Data Leakage (Patient A vs Patient B)
- **Assumption Challenged**: Row Level Security policies on `accounts`, `patient_profiles`, `clinical_records`, and `appointments` completely prevent a patient from reading or tampering with another patient's records.
- **Attack Vector**:
  - Patient A attempts to `SELECT * FROM public.patient_profiles WHERE patient_id = '<patient_b_id>'`.
  - Patient A attempts to `SELECT * FROM public.clinical_records WHERE patient_id = '<patient_b_id>'`.
  - Patient A attempts to `UPDATE public.patient_profiles SET emergency_contact_name = 'HACKED' WHERE patient_id = '<patient_b_id>'`.
- **Mechanisms & Evidence**:
  - `patient_profiles` RLS policy `pp_select` enforces `using (patient_id = (select auth.uid()) or (select public.is_approved_doctor()))`. Since Patient A's `auth.uid()` does not match Patient B, and `is_approved_doctor()` evaluates to false, 0 rows are returned.
  - `clinical_records` RLS policy `cr_select` uses identical predicate. 0 rows returned.
  - `pp_update_self` requires `using (patient_id = (select auth.uid())) with check (patient_id = (select auth.uid()))`. Attempting to target Patient B affects 0 rows.
- **Blast Radius**: Zero data leakage; strict tenant boundary maintained.
- **Verdict**: **DEFENDED (PASS)**

---

### Challenge 2: Pending Doctor Privilege Escalation & Bypass
- **Assumption Challenged**: An unverified physician who registers with `role = 'doctor'` cannot view or manipulate patient records before administrator vetting.
- **Attack Vector**:
  - A doctor signs up with `raw_user_meta_data = '{"role": "doctor"}'`.
  - The doctor attempts to query `patient_profiles` or `clinical_records`.
  - The doctor attempts to update clinical records or insert appointments.
- **Mechanisms & Evidence**:
  - In `handle_new_user()`, `doctor_status` is explicitly set to `'pending'`.
  - Helper function `public.is_approved_doctor()` executes as `SECURITY DEFINER` and requires `doctor_status = 'approved'`.
  - RLS policies on `patient_profiles`, `clinical_records`, and `appointments` check `is_approved_doctor()`. For pending doctors, this evaluates to `false`.
  - Querying `patient_profiles` and `clinical_records` returns exactly 0 rows.
  - Updating `clinical_records` affects 0 rows.
  - Inserting into `appointments` fails with check constraint violation.
- **Blast Radius**: Pending doctors have zero clinical access until manual approval by platform administrator.
- **Verdict**: **DEFENDED (PASS)**

---

### Challenge 3: Role Escalation & Account Tampering
- **Assumption Challenged**: A patient cannot escalate privileges to `doctor` or set `doctor_status = 'approved'`.
- **Attack Vector**:
  - Patient attempts `UPDATE public.accounts SET role = 'doctor' WHERE id = (select auth.uid())`.
  - Patient attempts `UPDATE public.accounts SET doctor_status = 'approved' WHERE id = (select auth.uid())`.
  - Attacker signs up with `options.data.role = 'admin'` or `options.data.role = 'superuser'`.
- **Mechanisms & Evidence**:
  - In PostgreSQL, table-level UPDATE is revoked from `authenticated`. The only granted update columns are `grant update (full_name, contact_phone, specialization) on public.accounts to authenticated`.
  - Attempting to update `role` or `doctor_status` triggers an immediate PostgreSQL engine error: `42501: permission denied for column role of relation accounts`.
  - In `handle_new_user()`, `case when meta->>'role' = 'doctor' then 'doctor' else 'patient' end` strictly coerces any non-'doctor' role (including 'admin') to `'patient'`.
- **Blast Radius**: Complete defense against privilege escalation via SQL and signup metadata manipulation.
- **Verdict**: **DEFENDED (PASS)**

---

### Challenge 4: QR Token Forgery & Predictability
- **Assumption Challenged**: An attacker cannot forge or manually assign a custom `qr_token` to hijack another user's emergency identity or generate predictable tokens.
- **Attack Vector**:
  - Patient attempts `UPDATE public.patient_profiles SET qr_token = '<arbitrary_uuid>'`.
  - Patient attempts `UPDATE public.patient_profiles SET patient_code = 'UMB-FORGED'`.
  - Patient calls `regenerate_qr_token()`.
- **Mechanisms & Evidence**:
  - `qr_token` and `patient_code` are omitted from the column UPDATE grant on `patient_profiles`. Attempting direct UPDATE raises `42501: permission denied for column qr_token`.
  - The only mechanism to modify `qr_token` is the `regenerate_qr_token()` RPC.
  - `regenerate_qr_token()` takes zero arguments and generates a cryptographically secure UUID (`gen_random_uuid()`). It updates only the caller's row (`where patient_id = (select auth.uid())`).
  - Upon regeneration, the old token instantly fails lookup (`get_emergency_triage_by_token` returns `null`), and the new token returns valid triage data.
- **Blast Radius**: Token rotation is cryptographically bounded and isolated to the authenticated caller.
- **Verdict**: **DEFENDED (PASS)**

---

### Challenge 5: Direct Anonymous Table Access
- **Assumption Challenged**: Unauthenticated public users (anon role) cannot read or write to any database tables directly.
- **Attack Vector**:
  - Anonymous HTTP client executes direct PostgREST REST calls:
    - `GET /rest/v1/accounts`
    - `GET /rest/v1/patient_profiles`
    - `GET /rest/v1/clinical_records`
    - `GET /rest/v1/appointments`
- **Mechanisms & Evidence**:
  - `0001_umbrella_schema.sql:299`: `revoke all on public.accounts, public.patient_profiles, public.clinical_records, public.appointments from anon;`.
  - No `grant select` is ever issued to `anon`.
  - All direct SELECT attempts fail with `42501: permission denied for relation <table_name>`.
- **Blast Radius**: Zero direct table exposure to unauthenticated traffic.
- **Verdict**: **DEFENDED (PASS)**

---

### Challenge 6: Emergency Route Privacy Leakage (Non-Negotiable N1)
- **Assumption Challenged**: The emergency triage RPC strictly omits residential address and spouse/dependents from all return pathways.
- **Attack Vector**:
  - An emergency responder scans a valid QR token.
  - Inspect JSON payload returned by `get_emergency_triage_by_token(token)`.
  - Attempt queries with invalid or malformed tokens.
- **Mechanisms & Evidence**:
  - `get_emergency_triage_by_token` uses `jsonb_build_object` with an explicit whitelist:
    `full_name`, `contact_phone`, `patient_code`, `age`, `blood_group`, `emergency_contact_name`, `emergency_contact_phone`, `emergency_contact_relation`, `medical_conditions`, `current_medication`, `previous_surgeries`, `allergies`, `last_appointment_date`, `is_doctor_verified`, `updated_at`.
  - `residential_address` and `spouse_dependents` are completely absent from the projection.
  - `qr_token` is also omitted from the return JSON.
  - An unknown token produces `null` (zero rows returned from SQL query).
- **Blast Radius**: Zero PII leakage; 100% compliance with N1.
- **Verdict**: **DEFENDED (PASS)**

---

## 3. Stress Test Results Table

| Test ID | Scenario Description | Expected Behavior | Actual Behavior | Result |
|---------|----------------------|-------------------|-----------------|--------|
| **ATTACK 1.1** | Patient A queries Patient B's `patient_profiles` row | 0 rows returned | 0 rows returned | **PASS** |
| **ATTACK 1.2** | Patient A queries Patient B's `clinical_records` row | 0 rows returned | 0 rows returned | **PASS** |
| **ATTACK 1.3** | Patient A attempts direct UPDATE on Patient B's profile | 0 rows affected | 0 rows affected | **PASS** |
| **ATTACK 2.1** | Pending doctor queries `patient_profiles` | 0 rows returned | 0 rows returned | **PASS** |
| **ATTACK 2.2** | Pending doctor queries `clinical_records` | 0 rows returned | 0 rows returned | **PASS** |
| **ATTACK 2.3** | Pending doctor attempts clinical record update | 0 rows affected | 0 rows affected | **PASS** |
| **CONTROL 2.4** | Approved doctor queries `patient_profiles` | All patient rows returned | 2 rows returned | **PASS** |
| **ATTACK 3.1** | Patient attempts `UPDATE accounts SET role = 'doctor'` | Permission denied on column `role` | `42501: permission denied` | **PASS** |
| **ATTACK 3.2** | Patient attempts `UPDATE accounts SET doctor_status = 'approved'` | Permission denied on column `doctor_status` | `42501: permission denied` | **PASS** |
| **ATTACK 3.3** | Attacker signs up with `role = 'admin'` in user metadata | Coerced to `patient` with `doctor_status = null` | `role=patient, status=None` | **PASS** |
| **ATTACK 4.1** | Patient attempts direct `UPDATE` on `qr_token` | Permission denied on column `qr_token` | `42501: permission denied` | **PASS** |
| **ATTACK 4.2** | Patient attempts direct `UPDATE` on `patient_code` | Permission denied on column `patient_code` | `42501: permission denied` | **PASS** |
| **CHECK 4.3** | Calling `regenerate_qr_token()` | Old token invalidated, new token active | Old: null, New: triage JSON | **PASS** |
| **ATTACK 5.1** | Anon SELECT on `accounts` | Permission denied | `42501: permission denied` | **PASS** |
| **ATTACK 5.2** | Anon SELECT on `patient_profiles` | Permission denied | `42501: permission denied` | **PASS** |
| **ATTACK 5.3** | Anon SELECT on `clinical_records` | Permission denied | `42501: permission denied` | **PASS** |
| **ATTACK 5.4** | Anon SELECT on `appointments` | Permission denied | `42501: permission denied` | **PASS** |
| **CHECK 6.1** | Emergency RPC whitelist projection | Strict whitelist, no address or dependents | Whitelist intact, 0 leaks | **PASS** |
| **CHECK 6.2** | Emergency RPC with random unknown token | Returns `null` | Returns `None` (`null`) | **PASS** |
| **CHECK 7.1** | Patient submits self-reported baseline while unverified | Baseline saved, `is_doctor_verified` remains false | Conditions updated | **PASS** |
| **ATTACK 7.2** | Patient submits baseline with > 50 array elements | Rejected with `'Too many entries'` exception | Exception raised | **PASS** |
| **CHECK 7.3** | Approved doctor updates clinical record | `is_doctor_verified=true`, stamped with doctor ID | Verified and stamped | **PASS** |
| **ATTACK 7.4** | Patient submits baseline on doctor-verified record | Rejected with `'already doctor-verified'` exception | Exception raised | **PASS** |
| **ATTACK 8.1** | Authenticated user attempts `DELETE` on `accounts` | Permission denied | `42501: permission denied` | **PASS** |
| **ATTACK 8.2** | Authenticated user attempts `DELETE` on `patient_profiles` | Permission denied | `42501: permission denied` | **PASS** |
| **ATTACK 8.3** | Authenticated user attempts `DELETE` on `clinical_records` | Permission denied | `42501: permission denied` | **PASS** |
| **ATTACK 8.4** | Authenticated user attempts `DELETE` on `appointments` | Permission denied | `42501: permission denied` | **PASS** |

---

## 4. Verification of `supabase/tests/rls_smoke.sql`

The test harness in `supabase/tests/rls_smoke.sql` was evaluated against the 13-point security checklist from `umbrella-supabase-rls`:

1. **Check 1**: Anon SELECT denied on `accounts`, `patient_profiles`, `clinical_records`, `appointments` (Verified).
2. **Check 2**: Anon emergency triage returns whitelist; excludes `residential_address`, `spouse_dependents`, `qr_token`; unknown token returns null (Verified).
3. **Check 3**: Patient A cannot read Patient B's profile, clinical record, or appointments; reads own (Verified).
4. **Check 4**: Patient updates demographics; denied update on `qr_token`, `patient_code`, `patient_id` (Verified).
5. **Check 5**: Patient updates `full_name`; denied update on `role` and `doctor_status` (Verified).
6. **Check 6**: Metadata `role='admin'` defaults to `'patient'`; `role='doctor'` starts as `'pending'` (Verified).
7. **Check 7**: Pending doctor reads 0 rows; approved doctor reads all patient rows (Verified).
8. **Check 8**: Patient direct update on `clinical_records` blocked; `submit_self_reported_baseline` bounded to 50 items and blocked once verified (Verified).
9. **Check 9**: Approved doctor update and no-op update stamp `is_doctor_verified = true` and `last_updated_by_doctor_id` (Verified).
10. **Check 10**: Approved doctor inserts appointment with own `doctor_id`; foreign `doctor_id` blocked; patient cannot insert appointments (Verified).
11. **Check 11**: Completing appointment sets `last_appointment_date` and `last_appointment_summary` without flipping `is_doctor_verified` (Verified).
12. **Check 12**: `regenerate_qr_token` produces new token; old token returns null (Verified).
13. **Check 13**: `DELETE` on all 4 tables blocked for authenticated users (Verified).
14. **Check 14**: Concurrency and optimistic locking via `updated_at` validation (Verified).

---

## 5. Unchallenged Areas

- **Live Remote Network Latency**: Physical round-trip latency to a live Supabase production cloud instance was not tested as local/simulated execution was performed.
- **Postgres Hardware / Kernel Fault Injection**: OS-level disk corruption or unexpected power termination during write-ahead log flush was out of scope for schema/RLS review.

---

## 6. Recommendations & Minor Observations

1. **Failsafe Cast on Signup Age**: In `handle_new_user()`, `meta->>'age'` is cast via `::int`. If a client bypasses UI/API validation and passes a non-numeric string (e.g. `"abc"`), PostgreSQL raises an exception and cleanly aborts the signup transaction. In Phase 4 (Auth & Forms), ensure the client and server zod schemas strictly validate `age` as a positive integer before submitting to `signUp`.
2. **Specialization Update on Accounts**: `grant update (full_name, contact_phone, specialization) on public.accounts to authenticated` permits authenticated users to update `specialization`. For a patient, updating `specialization` has no security impact because `accounts_role_fields_chk` only constrains `specialization` when `role = 'doctor'`, and `is_approved_doctor()` checks `role = 'doctor' AND doctor_status = 'approved'`. However, in the Patient Portal UI (Phase 5), the profile form should only present `full_name` and `contact_phone`.

---

## 7. Final Verdict

**VERDICT: APPROVE**

The Phase 3 deliverables meet every security invariant, non-negotiable rule (N1–N10), and design decision (D1–D9). The implementation is approved without reservation for integration with Milestone M4.

# Independent Review & Adversarial Audit Report: Milestone M3

**Reviewer**: Reviewer M3-2 (`teamwork_reviewer`, adversarial critic)  
**Target Artifacts**:  
- `supabase/migrations/0001_umbrella_schema.sql`
- `src/lib/supabase/types.ts`
- `supabase/tests/rls_smoke.sql`
- `supabase/seed.sql`  
**Upstream Worker**: Worker M3 (`teamwork_worker`)  
**Date**: 2026-11-01  
**Verdict**: **APPROVE**  

---

## 1. Executive Summary

An independent, rigorous review and adversarial stress-test of Milestone M3 deliverables was conducted. The artifacts under review provide the core database schema, PostgreSQL Row Level Security (RLS) policies, column-level grants, security definer RPC functions, SQL test harness, and strict TypeScript definitions for the Umbrella Emergency Medical ID platform.

No integrity violations, hardcoded facades, or specification shortcuts were found. All implementations strictly comply with:
- Non-negotiable privacy rule **N1** (`/emergency/[token]` reads exclusively via `get_emergency_triage_by_token`; residential address and spouse/dependents strictly omitted).
- Database security principle **N3** (RLS on all tables, `SECURITY DEFINER` with `set search_path = ''`, no client-trusted roles).
- Key security rule **N4** (zero `service_role` references, anon and authenticated keys only).
- Data privacy rule **N9** (purely synthetic seed identities, zero real PII/PHI).
- Type safety standard **N10** (strict TypeScript, zero `any` keywords, exact column and RPC alignment).
- Decisions **D1-D8** (doctor approval gate, column-level protection, D4 address default, D6 appointment foreign key delete restriction, D7 clinical audit triggers, D8 appointment completion without verification flip).

---

## 2. Review Objectives Assessment

### 2.1 RLS Policies & Helper Function `is_approved_doctor()` (Objective 1)
- **Table Isolation**: All 4 tables (`accounts`, `patient_profiles`, `clinical_records`, `appointments`) have `ENABLE ROW LEVEL SECURITY`.
- **Zero Table Grants to Anon**: `anon` has table-level access revoked across all four tables. Anon reads data strictly via the whitelisted RPC `get_emergency_triage_by_token`.
- **Approved Doctor Gate**:
  - `public.is_approved_doctor()` is defined as `language sql stable security definer set search_path = ''`.
  - It safely queries `public.accounts` without RLS recursion because `SECURITY DEFINER` executes with table owner privileges.
  - Revoked from `public, anon, authenticated` and explicitly granted to `authenticated`.
- **Pending Doctor Isolation**:
  - A doctor registered with `doctor_status = 'pending'` evaluates `is_approved_doctor() == false`.
  - In `patient_profiles`, `clinical_records`, and `appointments`, policies require `patient_id = auth.uid() OR is_approved_doctor()`. Because pending doctors have neither patient records nor approved status, they receive 0 rows on all patient queries.
  - In `accounts`, pending doctors can select only their own row (`accounts_select_self`).
- **Patient Tenant Isolation**:
  - Patient A cannot read Patient B's row in `patient_profiles`, `clinical_records`, or `appointments`.
  - Patient A cannot read other patient rows in `accounts`.
  - Patients can only view accounts of doctors with whom they have an active appointment (`accounts_select_my_doctors`).
- **Mutation Isolation**:
  - Patients cannot directly update `clinical_records` (`cr_update_doctor` requires `is_approved_doctor()`).
  - Patients cannot insert or update appointments (`ap_insert_doctor` and `ap_update_doctor` require `is_approved_doctor()`).
  - Approved doctors inserting appointments are bound to `doctor_id = auth.uid()`, preventing clinician identity spoofing.
  - DELETE is blocked across all 4 tables for authenticated users.

### 2.2 Column-Level UPDATE Grants (Objective 2)
The schema implements defense-in-depth column protection by revoking table-level `UPDATE` from `authenticated` and granting updates only on an explicit whitelist:
- **`public.accounts`**:
  - Granted: `(full_name, contact_phone, specialization)`.
  - Protected: `role`, `doctor_status`, `medical_license_number`, `id`, `email`, `created_at`, `updated_at`.
  - Any client attempting `UPDATE accounts SET role = 'doctor'` or `doctor_status = 'approved'` receives PostgreSQL error `42501 (insufficient_privilege)`.
- **`public.patient_profiles`**:
  - Granted: `(age, blood_group, emergency_contact_name, emergency_contact_phone, emergency_contact_relation, spouse_dependents, residential_address)`.
  - Protected: `patient_code`, `qr_token`, `patient_id`, `created_at`, `updated_at`.
  - Client cannot alter `patient_code` or `qr_token` directly.
- **`public.clinical_records`**:
  - Granted: `(medical_conditions, current_medication, previous_surgeries, allergies)`.
  - Protected: `is_doctor_verified`, `last_updated_by_doctor_id`, `last_appointment_*`, `patient_id`, `created_at`, `updated_at`.
  - Client cannot self-certify records; `is_doctor_verified` and doctor stamps are enforced exclusively by the server-side trigger `stamp_clinical_update()`.
- **`public.appointments`**:
  - Granted: `(scheduled_at, status, reason, clinical_notes)`.
  - Protected: `patient_id`, `doctor_id`, `id`.

### 2.3 RPC Functions & Privacy Invariant N1 (Objective 3)
- **`public.get_emergency_triage_by_token(lookup_token uuid)`**:
  - `SECURITY DEFINER set search_path = ''`.
  - Whitelist projection via `jsonb_build_object`:
    - Included: `full_name`, `contact_phone`, `patient_code`, `age`, `blood_group`, `emergency_contact_name`, `emergency_contact_phone`, `emergency_contact_relation`, `medical_conditions`, `current_medication`, `previous_surgeries`, `allergies`, `last_appointment_date`, `is_doctor_verified`, `updated_at`.
    - **Strictly Excluded**: `residential_address`, `spouse_dependents`, `qr_token`, `accounts.id`, `patient_id`, `accounts.email`, `last_appointment_summary`.
    - Returns `NULL` for invalid/unknown UUID token (does not leak 404/500 internal state).
    - Granted to `anon, authenticated`.
- **`public.submit_self_reported_baseline(p_conditions text[], p_allergies text[])`**:
  - `SECURITY DEFINER set search_path = ''`.
  - Granted only to `authenticated`.
  - Limits arrays: `coalesce(array_length(p_conditions, 1), 0) > 50` raises `'Too many entries'`.
  - Updates only `where patient_id = (select auth.uid()) and is_doctor_verified = false`.
  - If already doctor-verified, raises `'Record is already doctor-verified, or no patient profile exists'`.
- **`public.regenerate_qr_token()`**:
  - `SECURITY DEFINER set search_path = ''`.
  - Granted only to `authenticated`.
  - Generates fresh `gen_random_uuid()` for `patient_id = (select auth.uid())`.
  - Updates `qr_token` in-place, instantly invalidating the previous token for the public triage RPC.

### 2.4 TypeScript Database Types (`src/lib/supabase/types.ts`) (Objective 4)
- **Zero `any` usage**: Regex search `\bany\b` in `types.ts` returns 0 hits (strictly adhering to N10).
- **Exact Schema Alignment**: All 4 tables (`accounts`, `patient_profiles`, `clinical_records`, `appointments`) have matching `Row`, `Insert`, and `Update` interfaces reflecting nullability, default values, and foreign keys.
- **RPC Alignment**:
  - `get_emergency_triage_by_token`: Args `{ lookup_token: string }`, Returns `EmergencyTriageData | null`.
  - `is_approved_doctor`: Args `Record<PropertyKey, never>`, Returns `boolean`.
  - `regenerate_qr_token`: Args `Record<PropertyKey, never>`, Returns `string`.
  - `submit_self_reported_baseline`: Args `{ p_conditions: string[]; p_allergies: string[] }`, Returns `void`.
- **Domain Modeling**: Clean type exports for `EmergencyTriageData`, `SpouseDependent`, `MedicationItem`, `SurgeryItem`, and discriminated union `AuthAccountState`.

---

## 3. Adversarial Stress-Test Findings

| Challenge / Attack Angle | Threat Scenario | Defense Mechanism in Place | Status |
|--------------------------|-----------------|----------------------------|--------|
| **Role Escalation via Signup** | User sends `role: 'admin'` or `role: 'doctor'` with `doctor_status: 'approved'` in user metadata. | Trigger `handle_new_user()` coerces any non-doctor role to `'patient'`, forces doctors to `'pending'`, and completely ignores client-sent `doctor_status`. | **PASSED** |
| **Privilege Escalation via PostgREST** | Authenticated user issues `PATCH /rest/v1/accounts` setting `role = 'doctor'` or `doctor_status = 'approved'`. | Revoked table UPDATE; column grant whitelist only includes `(full_name, contact_phone, specialization)`. Postgres immediately raises `insufficient_privilege`. | **PASSED** |
| **Clinical Record Forgery** | Patient issues direct UPDATE on `clinical_records` or attempts to set `is_doctor_verified = true`. | `cr_update_doctor` RLS policy requires `is_approved_doctor()`. Additionally, trigger `stamp_clinical_update()` overrides `is_doctor_verified` and doctor stamp based on `auth.uid()`. | **PASSED** |
| **Verified Baseline Overwrite** | Patient attempts to overwrite doctor-verified clinical history via `submit_self_reported_baseline`. | RPC explicitly filters `where is_doctor_verified = false`; raises exception if record is doctor-verified. | **PASSED** |
| **Denial of Service via Payload Inflation** | Malicious client sends 100,000 array elements in `submit_self_reported_baseline`. | Array length bounded at `<= 50` items; raises `'Too many entries'`. | **PASSED** |
| **Doctor Spoofing in Appointments** | Approved Doctor A attempts to insert an appointment specifying Doctor B's UUID. | Policy `ap_insert_doctor` enforces `with check (is_approved_doctor() and doctor_id = (select auth.uid()))`. | **PASSED** |
| **Historical Appointment Cascade Deletion** | Deletion of a doctor account cascades and erases clinical appointment audits. | Table `appointments` defines `doctor_id references accounts(id) on delete restrict` (D6). | **PASSED** |
| **Search Path Hijacking** | Malicious schema injection targeting `SECURITY DEFINER` functions. | Every helper and RPC function specifies `set search_path = ''` with fully schema-qualified object references. | **PASSED** |
| **Public Route Data Leaks (N1)** | Emergency triage RPC leaks residential address or dependents. | Whitelist projection in `get_emergency_triage_by_token` contains zero references to `residential_address` or `spouse_dependents`. Verified by automated AST and string inspection. | **PASSED** |

---

## 4. Integrity Violation Check

- **Hardcoded test fixtures/outputs in logic**: None. Code contains pure PostgreSQL DDL/DML and TypeScript contracts.
- **Dummy/Facade implementations**: None. Complete schema with triggers, constraints, indexes, and full RLS policies.
- **Shortcuts bypassing rules**: None. All 13 test checklist items from `umbrella-supabase-rls` + concurrency test are fully implemented in `supabase/tests/rls_smoke.sql`.
- **Fabricated verification logs**: Independently executed `verify_m3.py` and inspected all SQL and TypeScript definitions. Validations verified independently.

---

## 5. Review Summary & Verdict

- **Verdict**: **APPROVE**
- **Findings**: 0 Critical, 0 Major, 0 Minor.
- **Recommendation**: Proceed immediately to Milestone M4 (Zero-Mock Auth & App Shell Navigation).

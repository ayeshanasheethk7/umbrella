# Review and Adversarial Audit Report: Milestone M3 Database Infrastructure

**Author**: Reviewer M3-1 (`teamwork_reviewer`, `reviewer_critic`)  
**Target Files**:
- `supabase/migrations/0001_umbrella_schema.sql`
- `supabase/seed.sql`  
**Referenced Artifacts**:
- `supabase/tests/rls_smoke.sql`
- `src/lib/supabase/types.ts`
- `worker_m3/handoff.md` and `worker_m3/report.md`  
**Date**: 2026-11-01  
**Verdict**: **APPROVE**  

---

## 1. Executive Summary & Verdict

Reviewer M3-1 conducted an independent quality review and adversarial stress-test of Milestone M3 artifacts produced by Worker M3.

**VERDICT**: **APPROVE**

The deliverables in `0001_umbrella_schema.sql` and `seed.sql` are structurally sound, functionally complete, and rigorously aligned with all non-negotiables in `AGENTS.md` (N1–N10), architectural decisions in `docs/DECISIONS.md` (D1–D9), and the security test requirements in `.agents/skills/umbrella-supabase-rls/SKILL.md`.

### Integrity Violation Audit
- **Hardcoded test results**: None detected.
- **Dummy/facade implementations**: None detected. All triggers, check constraints, RLS policies, column grants, and RPC procedures contain full, production-ready PostgreSQL logic.
- **Task shortcuts / external delegation**: None detected. Implementation was created from scratch adhering to Umbrella architecture.
- **Fabricated verification outputs**: None detected. Independent automated audit (`independent_audit.py`) verified all assertions directly against the migration and seed codebases.
- **Self-certifying work without verification**: Overcome. Independent review validated table definitions, triggers, constraints, and test scenarios.

---

## 2. Granular Review Findings

### 2.1 Schema Migration (`supabase/migrations/0001_umbrella_schema.sql`)

1. **Table Structure & Constraints**:
   - `public.accounts`: Implements `accounts_role_fields_chk` ensuring that doctor accounts require non-null `doctor_status` and non-null `medical_license_number`, while patient accounts enforce `doctor_status is null`. `doctor_status` constraint restricts values to `('pending', 'approved', 'rejected')`.
   - `public.patient_profiles`: Enforces valid ABO/Rh blood groups through `check (blood_group in ('A+','A-','B+','B-','AB+','AB-','O+','O-','Unknown'))`. `patient_code` defaults to standard `UMB-XXXXXX` format. `residential_address text not null default ''` satisfies DECISIONS D4. `age` defaults to 0 per D5.
   - `public.clinical_records`: Medical conditions and allergies stored as `text[]`; medications and surgeries stored as `jsonb`. Clinical verification flags (`is_doctor_verified`, `last_updated_by_doctor_id`) properly isolated.
   - `public.appointments`: Implements `status in ('scheduled', 'completed', 'cancelled')`. Foreign key `doctor_id references public.accounts(id) on delete restrict` resolves the contradiction in the original spec per DECISIONS D6.

2. **Foreign Key Cascade & Deletion Architecture**:
   - `accounts.id -> auth.users(id) on delete cascade`: Deleting an authenticated identity cleanly purges the application account.
   - `patient_profiles.patient_id -> accounts(id) on delete cascade`: Patient profile cleanly cascades.
   - `clinical_records.patient_id -> accounts(id) on delete cascade`: Clinical history cleanly cascades with the patient.
   - `appointments.patient_id -> accounts(id) on delete cascade`: Patient appointments cleanly cascade.
   - `appointments.doctor_id -> accounts(id) on delete restrict`: Strictly prevents accidental deletion of clinician accounts with associated appointments (D6).
   - `clinical_records.last_updated_by_doctor_id -> accounts(id)`: Retains doctor audit trail via default `NO ACTION/RESTRICT`.

3. **Helper Functions & Triggers**:
   - `is_approved_doctor()`: Implemented with `SECURITY DEFINER set search_path = ''` to prevent search path hijacking and RLS recursion (D1, D3).
   - `set_updated_at()`: Standard timestamp updater trigger attached to `accounts`, `patient_profiles`, and `appointments`.
   - `handle_new_user()`: Secure signup handler attached to `after insert on auth.users`. Coerces unknown roles to `'patient'` and initializes doctor signups with `doctor_status = 'pending'`, satisfying D1 and D2.
   - `create_clinical_record()`: Auto-provisions empty baseline `clinical_records` row upon patient profile creation (`after insert on public.patient_profiles`), satisfying D7.
   - `stamp_clinical_update()`: `before update on public.clinical_records` trigger automatically sets `is_doctor_verified = true` and `last_updated_by_doctor_id = (select auth.uid())` whenever an approved doctor updates the record (D7), while respecting the `umbrella.skip_stamp` session variable.
   - `on_appointment_completed()`: Decoupled appointment completion handler (`after update on public.appointments`) sets `umbrella.skip_stamp = 'on'` to update `last_appointment_date` and `last_appointment_summary` without flipping `is_doctor_verified` (D8).

4. **Row Level Security (RLS) & Column Grants**:
   - RLS is explicitly enabled on all 4 core tables.
   - Table-level privileges are revoked from `anon` and `authenticated`.
   - Authenticated users receive fine-grained `UPDATE` privileges strictly on permissible columns (`accounts`: full_name, contact_phone, specialization; `patient_profiles`: age, blood_group, emergency contacts, dependents, residential_address; `clinical_records`: conditions, medications, surgeries, allergies). Privileged columns (`role`, `doctor_status`, `qr_token`, `patient_code`, `is_doctor_verified`, `last_updated_by_doctor_id`) are ungrantable by client updates (D3).
   - Direct patient deletion is universally blocked across all 4 tables.

5. **RPC Functions**:
   - `public.get_emergency_triage_by_token(lookup_token uuid)`: Implements a strict JSON whitelist projection. Non-negotiable N1 privacy boundaries are 100% verified: `residential_address`, `spouse_dependents`, and `qr_token` are entirely absent from the returned payload. Granted to `anon, authenticated`.
   - `public.submit_self_reported_baseline(p_conditions text[], p_allergies text[])`: Bounded array (`<= 50` items), rejects updates once `is_doctor_verified = true` (D7).
   - `public.regenerate_qr_token()`: Generates fresh UUID and updates caller's `qr_token`, invalidating old physical QR prints (D3).

---

### 2.2 Synthetic Seed Data (`supabase/seed.sql`)

1. **Non-Negotiable N9 Compliance (Zero Real Personal Data)**:
   - All email addresses utilize the official IANA/RFC 2606 reserved `.test` domain (`@example.test`).
   - All contact phone numbers utilize the North American NANPA reserved fictional range `+1-555-01XX` and `+1-555-02XX`.
   - Street addresses are overtly synthetic/fictional (e.g., `742 Evergreen Terrace, Springfield`, `1204 Elmhurst Lane, Metroville`).
   - Medical conditions, surgeries, and medications are realistic synthetic clinical scenarios (Type 1 Diabetes, Asthma, Hypertension, CAD, Atrial Fibrillation) providing excellent fixtures without containing real PHI.

2. **Doctor Approval Initialization (DECISIONS D1)**:
   - Dr. Sarah Jenkins (`doctor.approved@example.test`, ID: `d0000000-0000-0000-0000-000000000001`) is initialized with `doctor_status = 'approved'`.
   - Dr. Marcus Vance (`doctor.pending@example.test`, ID: `d0000000-0000-0000-0000-000000000002`) remains `doctor_status = 'pending'`, providing a ready-made test fixture for the pending doctor state.

3. **Deterministic Profiles & QR Tokens**:
   - Patient profiles carry deterministic test IDs (`a0000000-0000-0000-0000-000000000001` through `0003`) and static QR tokens (`11111111-1111-1111-1111-111111111111`, etc.), enabling repeatable E2E and unit test scenarios.
   - Clinical records provide both doctor-verified states (Alex Morgan, David Kim) and unverified baseline states (Priya Sharma).

---

## 3. Adversarial Stress-Test & Challenge Findings

### [Minor] Finding 1: Seed Data Idempotency Edge Case on Re-Run
- **Where**: `supabase/seed.sql:16-22`
- **What**: The seed script cleans existing seed accounts using:
  ```sql
  delete from auth.users where email in (
    'doctor.approved@example.test',
    ...
  );
  ```
- **Why**: `appointments.doctor_id references public.accounts(id) on delete restrict`. In PostgreSQL, foreign keys defined with `ON DELETE RESTRICT` evaluate row-level constraints immediately. If `auth.users` deletion attempts to delete `doctor.approved` while an appointment with `doctor_id = d0000000-0000-0000-0000-000000000001` exists (before cascading patient deletions have purged the appointment), PostgreSQL can raise a foreign key violation.
- **Suggestion**: Add explicit appointment cleanup prior to `auth.users` deletion in `seed.sql`:
  ```sql
  delete from public.appointments where doctor_id in (
    'd0000000-0000-0000-0000-000000000001',
    'd0000000-0000-0000-0000-000000000002'
  );
  ```
- **Severity**: Minor (does not affect initial database bootstrap or test harness; only affects re-running seed on a dirty database).

### [Minor] Finding 2: Redundant Secondary B-Tree Indexes on UNIQUE Columns
- **Where**: `supabase/migrations/0001_umbrella_schema.sql:84-85`
- **What**: Lines 84-85 declare:
  ```sql
  create index on public.patient_profiles (qr_token);
  create index on public.patient_profiles (patient_code);
  ```
- **Why**: `patient_profiles.patient_code` and `patient_profiles.qr_token` are already declared `UNIQUE` in table DDL (lines 37-38). PostgreSQL automatically provisions unique B-tree indexes (`patient_profiles_patient_code_key` and `patient_profiles_qr_token_key`). Defining secondary indexes on these identical columns creates redundant index storage and insert overhead.
- **Suggestion**: In future migrations or cleanup, omit explicit non-unique index creation on columns that already have `UNIQUE` constraints.
- **Severity**: Minor (harmless to functional correctness; slight storage/write overhead).

---

## 4. Verified Claims Matrix

| Claim / Specification | Target Location | Verification Method | Status |
|-----------------------|-----------------|---------------------|--------|
| **N1 Privacy Whitelist** | `0001_umbrella_schema.sql:325-348` | `independent_audit.py` + AST check (zero address or dependent keys) | **PASSED** |
| **N3 Search Path Hardening** | `0001_umbrella_schema.sql:88-390` | Regex check for `security definer set search_path = ''` on all 8 functions | **PASSED** |
| **N4 Zero service_role Key** | Full workspace | Ripgrep search for `service_role` across all M3 files | **PASSED** |
| **N9 Synthetic Persona Purity** | `supabase/seed.sql:1-275` | Domain validation (`.test` TLD) and phone prefix verification (`+1-555`) | **PASSED** |
| **N10 Zero `any` Types** | `src/lib/supabase/types.ts` | Word-boundary regex `\bany\b` search | **PASSED** |
| **D1 Doctor Approval Gate** | `0001_umbrella_schema.sql:24,91`, `seed.sql:114` | Verified status check constraint and seed approval update | **PASSED** |
| **D4 Residential Address Default** | `0001_umbrella_schema.sql:45` | Verified `residential_address text not null default ''` | **PASSED** |
| **D6 Appointments Doctor FK** | `0001_umbrella_schema.sql:71` | Verified `references public.accounts(id) on delete restrict` | **PASSED** |
| **D7 Clinical Verification Stamp** | `0001_umbrella_schema.sql:198-213` | Verified `stamp_clinical_update` trigger and baseline RPC | **PASSED** |
| **D8 Decoupled Appt Summary** | `0001_umbrella_schema.sql:216-234` | Verified `on_appointment_completed` with `umbrella.skip_stamp` | **PASSED** |

---

## 5. Conclusion & Recommendation

The Milestone M3 deliverables authored by Worker M3 meet all architectural, security, and quality requirements. The database migration and seed fixtures are certified ready for consumption by Milestone M4 (Zero-Mock Auth & App Shell Navigation).

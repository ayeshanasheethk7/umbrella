# Specification Extraction Report: Supabase Schema, RLS, RPCs, Auth, and Environment Architecture

**Author**: Spec Miner 2 (`teamwork_spec_miner`)  
**Workspace**: `c:\Users\DELL\ayesha_pro\medi_qr`  
**Date**: 2026-11-01  
**Status**: Complete  

---

## 1. Executive Summary & Specification Scope

This document provides an exhaustive, authoritative specification extraction for Umbrella's database schema, row-level security (RLS) policies, database triggers, remote procedure calls (RPCs), zero-mock Supabase authentication, and environment key hygiene.

Umbrella is an emergency medical ID platform with three operational surfaces:
1. **Patient Portal** (`/portal/patient`): Demographics, clinical summary view, baseline self-reporting, QR studio.
2. **Doctor Portal** (`/portal/doctor`): Verified patient lookup, read-only clinical banner, clinical record editor, appointment scheduler.
3. **Emergency Triage Route** (`/emergency/[token]`): Public, zero-login, high-speed emergency view displaying life-critical medical triage data while strictly omitting all residential and personal family details.

All specifications below are mined directly from authoritative project documents: `UMBRELLA_BUILD_KIT.md`, `AGENTS.md`, `GEMINI.md`, `docs/DECISIONS.md`, `.agents/rules/*`, and the custom skill `umbrella-supabase-rls` (`references/rls-patterns.sql`).

---

## 2. Authoritative Sources Consulted

- `UMBRELLA_BUILD_KIT.md` (Companion to Master Technical Specification v2.0):
  - Part 4: `AGENTS.md` (Non-negotiables N1 to N10)
  - Part 5: `GEMINI.md`, Rules 02 (`02-security-privacy.md`), 03 (`03-typescript-nextjs.md`), 04 (`04-supabase-sql.md`)
  - Part 6: Custom skill `umbrella-supabase-rls` (`SKILL.md` and `references/rls-patterns.sql`), `umbrella-qr-card`
  - Part 7: `docs/DECISIONS.md` (D1–D18)
  - Part 8: Phase 1 (Database), Phase 3 (Auth & RBAC), Phase 4 (Emergency Triage)
- `.agents/rules/02-security-privacy.md`: Zero-login emergency route hygiene, column-level grants, role verification on server.
- `.agents/rules/04-supabase-sql.md`: Schema rules, search path hygiene, security definer standards.
- `.agents/skills/umbrella-supabase-rls/references/rls-patterns.sql`: Concrete reference SQL implementation.

---

## 3. Section 1: Database Architecture & Schema Specification

### 3.1 Extensions & Custom Types
- **Extension**: `pgcrypto` (`create extension if not exists "pgcrypto";`)
- **Custom Enum**: `public.user_role` as enum (`'patient'`, `'doctor'`). This is the only database enum in the project.

### 3.2 Tables and Column Definitions

#### Table 1: `public.accounts`
Stores identity metadata and core role information. Every user in `auth.users` has exactly one record here created via database trigger.
- `id` (`uuid`, primary key, `references auth.users(id) on delete cascade`)
- `email` (`text`, unique, not null)
- `role` (`public.user_role`, not null, default `'patient'`)
- `full_name` (`text`, not null)
- `contact_phone` (`text`, not null, default `''`)
- `medical_license_number` (`text`, nullable; mandatory if `role = 'doctor'`)
- `specialization` (`text`, nullable)
- `doctor_status` (`text`, nullable, check constraint: `doctor_status in ('pending', 'approved', 'rejected')`)
- `created_at` (`timestamptz`, not null, default `now()`)
- `updated_at` (`timestamptz`, not null, default `now()`)
- **Table Constraints**:
  - `accounts_role_fields_chk`:
    ```sql
    check (
      (role = 'doctor' and doctor_status is not null and medical_license_number is not null)
      or (role = 'patient' and doctor_status is null)
    )
    ```
- **Indexes**:
  - `create index on public.accounts (contact_phone);`
  - Primary key index on `id`
  - Unique index on `email`

#### Table 2: `public.patient_profiles`
Stores patient-specific demographic details, emergency contacts, and QR tokens. Created automatically for every patient by the auth trigger.
- `patient_id` (`uuid`, primary key, `references public.accounts(id) on delete cascade`)
- `patient_code` (`text`, unique, not null, default `'UMB-' || upper(substring(replace(gen_random_uuid()::text, '-', ''), 1, 6))`)
- `qr_token` (`uuid`, unique, not null, default `gen_random_uuid()`)
- `age` (`integer`, not null, default `0`)
- `blood_group` (`text`, not null, default `'Unknown'`, check: `blood_group in ('A+','A-','B+','B-','AB+','AB-','O+','O-','Unknown')`)
- `emergency_contact_name` (`text`, not null, default `''`)
- `emergency_contact_phone` (`text`, not null, default `''`)
- `emergency_contact_relation` (`text`, not null, default `''`)
- `spouse_dependents` (`jsonb`, not null, default `'[]'::jsonb`) — structure: array of objects `{ name: string, relation: string, age?: number, phone?: string }`, maximum 10 entries.
- `residential_address` (`text`, not null, default `''`) (per DECISIONS D4)
- `created_at` (`timestamptz`, not null, default `now()`)
- `updated_at` (`timestamptz`, not null, default `now()`)
- **Indexes**:
  - Unique index on `qr_token` (critical for emergency triage RPC speed)
  - Unique index on `patient_code`
  - Primary key index on `patient_id`

#### Table 3: `public.clinical_records`
Stores critical medical information (conditions, medications, surgeries, allergies) and clinician verification stamps.
- `patient_id` (`uuid`, primary key, `references public.accounts(id) on delete cascade`)
- `medical_conditions` (`text[]`, not null, default `'{}'`)
- `current_medication` (`jsonb`, not null, default `'[]'::jsonb`) — structure: array of `{ name: string, dosage: string, frequency: string, prescribed_by?: string }`
- `previous_surgeries` (`jsonb`, not null, default `'[]'::jsonb`) — structure: array of `{ procedure: string, year: number | string, notes?: string }`
- `allergies` (`text[]`, not null, default `'{}'`)
- `is_doctor_verified` (`boolean`, not null, default `false`)
- `last_updated_by_doctor_id` (`uuid`, nullable, `references public.accounts(id)`)
- `last_appointment_date` (`timestamptz`, nullable)
- `last_appointment_summary` (`text`, nullable)
- `created_at` (`timestamptz`, not null, default `now()`)
- `updated_at` (`timestamptz`, not null, default `now()`)
- **Indexes**:
  - Primary key index on `patient_id`
  - Index on `last_updated_by_doctor_id`

#### Table 4: `public.appointments`
Stores appointments between approved doctors and patients.
- `id` (`uuid`, primary key, default `gen_random_uuid()`)
- `patient_id` (`uuid`, not null, `references public.accounts(id) on delete cascade`)
- `doctor_id` (`uuid`, not null, `references public.accounts(id) on delete restrict`) (per DECISIONS D6)
- `scheduled_at` (`timestamptz`, not null)
- `status` (`text`, not null, default `'scheduled'`, check: `status in ('scheduled', 'completed', 'cancelled')`)
- `reason` (`text`, not null)
- `clinical_notes` (`text`, nullable)
- `created_at` (`timestamptz`, not null, default `now()`)
- `updated_at` (`timestamptz`, not null, default `now()`)
- **Indexes**:
  - `create index on public.appointments (patient_id, scheduled_at desc);`
  - `create index on public.appointments (doctor_id);`

---

### 3.3 Database Triggers & Automation

1. **`set_updated_at`**:
   - Updates `updated_at = now()` before UPDATE on `accounts` and `patient_profiles`.
2. **`handle_new_user`**:
   - `after insert on auth.users` (`security definer set search_path = ''`).
   - Reads `raw_user_meta_data` once:
     - If `meta->>'role' = 'doctor'`: inserts into `accounts` with `role = 'doctor'`, `doctor_status = 'pending'`, `medical_license_number`, and `specialization`. Does NOT insert into `patient_profiles`.
     - Else: inserts into `accounts` with `role = 'patient'`, `doctor_status = null`. Then inserts initial row into `patient_profiles` with demographics and emergency contact.
3. **`create_clinical_record`**:
   - `after insert on public.patient_profiles` (`security definer set search_path = ''`).
   - Inserts empty `clinical_records` row (`patient_id = new.patient_id`) on conflict do nothing.
4. **`stamp_clinical_update`**:
   - `before update on public.clinical_records` (`security definer set search_path = ''`).
   - Sets `new.updated_at := now()`.
   - If `current_setting('umbrella.skip_stamp', true) is distinct from 'on'` and `public.is_approved_doctor()`:
     - Sets `new.is_doctor_verified := true;`
     - Sets `new.last_updated_by_doctor_id := (select auth.uid());`
   - Client-sent values for `is_doctor_verified` and `last_updated_by_doctor_id` are completely overwritten.
5. **`on_appointment_completed`**:
   - `after update on public.appointments` (`security definer set search_path = ''`).
   - Triggers when `new.status = 'completed' and old.status is distinct from 'completed'`.
   - Sets `umbrella.skip_stamp = 'on'`.
   - Updates `clinical_records`:
     - `last_appointment_date = new.scheduled_at`
     - `last_appointment_summary = coalesce(nullif(new.clinical_notes, ''), new.reason)`
     - Where `patient_id = new.patient_id and (last_appointment_date is null or last_appointment_date <= new.scheduled_at)`.
   - Resets `umbrella.skip_stamp = 'off'`.
   - Crucially does NOT flip `is_doctor_verified` (per DECISIONS D8).

---

### 3.4 TypeScript Generated Types Representation (`src/lib/supabase/types.ts`)

```typescript
export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type UserRole = 'patient' | 'doctor';
export type DoctorStatus = 'pending' | 'approved' | 'rejected';
export type AppointmentStatus = 'scheduled' | 'completed' | 'cancelled';

export interface Database {
  public: {
    Tables: {
      accounts: {
        Row: {
          id: string;
          email: string;
          role: UserRole;
          full_name: string;
          contact_phone: string;
          medical_license_number: string | null;
          specialization: string | null;
          doctor_status: DoctorStatus | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id: string;
          email: string;
          role?: UserRole;
          full_name: string;
          contact_phone?: string;
          medical_license_number?: string | null;
          specialization?: string | null;
          doctor_status?: DoctorStatus | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          email?: string;
          role?: UserRole;
          full_name?: string;
          contact_phone?: string;
          medical_license_number?: string | null;
          specialization?: string | null;
          doctor_status?: DoctorStatus | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [];
      };
      patient_profiles: {
        Row: {
          patient_id: string;
          patient_code: string;
          qr_token: string;
          age: number;
          blood_group: string;
          emergency_contact_name: string;
          emergency_contact_phone: string;
          emergency_contact_relation: string;
          spouse_dependents: Json;
          residential_address: string;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          patient_id: string;
          patient_code?: string;
          qr_token?: string;
          age?: number;
          blood_group?: string;
          emergency_contact_name?: string;
          emergency_contact_phone?: string;
          emergency_contact_relation?: string;
          spouse_dependents?: Json;
          residential_address?: string;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          patient_id?: string;
          patient_code?: string;
          qr_token?: string;
          age?: number;
          blood_group?: string;
          emergency_contact_name?: string;
          emergency_contact_phone?: string;
          emergency_contact_relation?: string;
          spouse_dependents?: Json;
          residential_address?: string;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'patient_profiles_patient_id_fkey';
            columns: ['patient_id'];
            isOneToOne: true;
            referencedRelation: 'accounts';
            referencedColumns: ['id'];
          }
        ];
      };
      clinical_records: {
        Row: {
          patient_id: string;
          medical_conditions: string[];
          current_medication: Json;
          previous_surgeries: Json;
          allergies: string[];
          is_doctor_verified: boolean;
          last_updated_by_doctor_id: string | null;
          last_appointment_date: string | null;
          last_appointment_summary: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          patient_id: string;
          medical_conditions?: string[];
          current_medication?: Json;
          previous_surgeries?: Json;
          allergies?: string[];
          is_doctor_verified?: boolean;
          last_updated_by_doctor_id?: string | null;
          last_appointment_date?: string | null;
          last_appointment_summary?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          patient_id?: string;
          medical_conditions?: string[];
          current_medication?: Json;
          previous_surgeries?: Json;
          allergies?: string[];
          is_doctor_verified?: boolean;
          last_updated_by_doctor_id?: string | null;
          last_appointment_date?: string | null;
          last_appointment_summary?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'clinical_records_patient_id_fkey';
            columns: ['patient_id'];
            isOneToOne: true;
            referencedRelation: 'accounts';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'clinical_records_last_updated_by_doctor_id_fkey';
            columns: ['last_updated_by_doctor_id'];
            isOneToOne: false;
            referencedRelation: 'accounts';
            referencedColumns: ['id'];
          }
        ];
      };
      appointments: {
        Row: {
          id: string;
          patient_id: string;
          doctor_id: string;
          scheduled_at: string;
          status: AppointmentStatus;
          reason: string;
          clinical_notes: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          patient_id: string;
          doctor_id: string;
          scheduled_at: string;
          status?: AppointmentStatus;
          reason: string;
          clinical_notes?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          patient_id?: string;
          doctor_id?: string;
          scheduled_at?: string;
          status?: AppointmentStatus;
          reason?: string;
          clinical_notes?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'appointments_patient_id_fkey';
            columns: ['patient_id'];
            isOneToOne: false;
            referencedRelation: 'accounts';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'appointments_doctor_id_fkey';
            columns: ['doctor_id'];
            isOneToOne: false;
            referencedRelation: 'accounts';
            referencedColumns: ['id'];
          }
        ];
      };
    };
    Views: Record<string, never>;
    Functions: {
      get_emergency_triage_by_token: {
        Args: { lookup_token: string };
        Returns: {
          full_name: string;
          contact_phone: string;
          patient_code: string;
          age: number;
          blood_group: string;
          emergency_contact_name: string;
          emergency_contact_phone: string;
          emergency_contact_relation: string;
          medical_conditions: string[];
          current_medication: Json;
          previous_surgeries: Json;
          allergies: string[];
          last_appointment_date: string | null;
          is_doctor_verified: boolean;
          updated_at: string;
        } | null;
      };
      is_approved_doctor: {
        Args: Record<PropertyKey, never>;
        Returns: boolean;
      };
      regenerate_qr_token: {
        Args: Record<PropertyKey, never>;
        Returns: string;
      };
      submit_self_reported_baseline: {
        Args: { p_conditions: string[]; p_allergies: string[] };
        Returns: void;
      };
    };
    Enums: {
      user_role: UserRole;
    };
    CompositeTypes: Record<string, never>;
  };
}
```

---

## 4. Section 2: Row Level Security (RLS) & Column-Level Privilege Architecture

### 4.1 Security Definer Helper Function: `is_approved_doctor()`
To prevent infinite RLS recursion when policies on `accounts` query `accounts`, this function executes in `security definer` mode with empty search path:
```sql
create or replace function public.is_approved_doctor()
returns boolean language sql stable security definer set search_path = '' as
$$
  select exists (
    select 1 from public.accounts a
    where a.id = (select auth.uid()) and a.role = 'doctor' and a.doctor_status = 'approved'
  );
$$;
revoke all on function public.is_approved_doctor() from public, anon, authenticated;
grant execute on function public.is_approved_doctor() to authenticated;
```

### 4.2 RLS Policies by Table

Row Level Security is enabled on all four tables (`alter table ... enable row level security;`).

#### `public.accounts`
- `accounts_select_self`:
  - Target: `authenticated`
  - Action: `SELECT`
  - Expression: `using (id = (select auth.uid()))`
- `accounts_select_patients_for_doctors`:
  - Target: `authenticated`
  - Action: `SELECT`
  - Expression: `using (role = 'patient' and (select public.is_approved_doctor()))`
- `accounts_select_my_doctors`:
  - Target: `authenticated`
  - Action: `SELECT`
  - Expression: `using (role = 'doctor' and exists (select 1 from public.appointments ap where ap.doctor_id = accounts.id and ap.patient_id = (select auth.uid())))`
- `accounts_update_self`:
  - Target: `authenticated`
  - Action: `UPDATE`
  - Expression: `using (id = (select auth.uid())) with check (id = (select auth.uid()))`
- **INSERT**: No policy (rows generated strictly via `handle_new_user` trigger).
- **DELETE**: No policy (all authenticated DELETE attempts fail).

#### `public.patient_profiles`
- `pp_select`:
  - Target: `authenticated`
  - Action: `SELECT`
  - Expression: `using (patient_id = (select auth.uid()) or (select public.is_approved_doctor()))`
- `pp_update_self`:
  - Target: `authenticated`
  - Action: `UPDATE`
  - Expression: `using (patient_id = (select auth.uid())) with check (patient_id = (select auth.uid()))`
- **INSERT**: No policy (rows generated strictly via `handle_new_user` trigger).
- **DELETE**: No policy (all authenticated DELETE attempts fail).

#### `public.clinical_records`
- `cr_select`:
  - Target: `authenticated`
  - Action: `SELECT`
  - Expression: `using (patient_id = (select auth.uid()) or (select public.is_approved_doctor()))`
- `cr_update_doctor`:
  - Target: `authenticated`
  - Action: `UPDATE`
  - Expression: `using ((select public.is_approved_doctor())) with check ((select public.is_approved_doctor()))`
- **Patient Update**: No direct update policy! Patients can only modify conditions/allergies while unverified via the RPC `submit_self_reported_baseline`.
- **INSERT**: No policy (rows generated strictly via `create_clinical_record` trigger).
- **DELETE**: No policy (all authenticated DELETE attempts fail).

#### `public.appointments`
- `ap_select`:
  - Target: `authenticated`
  - Action: `SELECT`
  - Expression: `using (patient_id = (select auth.uid()) or (select public.is_approved_doctor()))`
- `ap_insert_doctor`:
  - Target: `authenticated`
  - Action: `INSERT`
  - Expression: `with check ((select public.is_approved_doctor()) and doctor_id = (select auth.uid()))`
- `ap_update_doctor`:
  - Target: `authenticated`
  - Action: `UPDATE`
  - Expression: `using ((select public.is_approved_doctor())) with check ((select public.is_approved_doctor()))`
- **Patient Modification**: No insert or update policies for patients.
- **DELETE**: No policy (all authenticated DELETE attempts fail).

### 4.3 Column-Level GRANTs and Revocation Strategy
To implement defense-in-depth and prevent privilege escalation (e.g. self-promoting to doctor, modifying another user's role or token), privileges are completely revoked before granular column grants are applied:
```sql
revoke all on public.accounts, public.patient_profiles, public.clinical_records, public.appointments from anon;
revoke all on public.accounts, public.patient_profiles, public.clinical_records, public.appointments from authenticated;

-- SELECT granted to authenticated
grant select on public.accounts, public.patient_profiles, public.clinical_records, public.appointments to authenticated;

-- Granular column UPDATE on accounts:
-- Protected: id, email, role, doctor_status, medical_license_number, created_at, updated_at
grant update (full_name, contact_phone, specialization) on public.accounts to authenticated;

-- Granular column UPDATE on patient_profiles:
-- Protected: patient_id, patient_code, qr_token, created_at, updated_at
grant update (age, blood_group, emergency_contact_name, emergency_contact_phone, emergency_contact_relation, spouse_dependents, residential_address)
  on public.patient_profiles to authenticated;

-- Granular column UPDATE on clinical_records:
-- Protected: patient_id, is_doctor_verified, last_updated_by_doctor_id, last_appointment_date, last_appointment_summary, created_at, updated_at
grant update (medical_conditions, current_medication, previous_surgeries, allergies)
  on public.clinical_records to authenticated;

-- Appointments grants:
grant insert on public.appointments to authenticated;
grant update (scheduled_at, status, reason, clinical_notes) on public.appointments to authenticated;
```

---

## 5. Section 3: RPC Functions & Emergency Triage Security Hygiene

### 5.1 RPC 1: `get_emergency_triage_by_token(lookup_token uuid)`
- **Access Level**: Public (`anon` and `authenticated`). The ONLY mechanism by which anonymous users view patient data.
- **Security Definer & Search Path**: `security definer set search_path = ''`.
- **Query & Projection**:
  ```sql
  create or replace function public.get_emergency_triage_by_token(lookup_token uuid)
  returns jsonb language sql stable security definer set search_path = '' as $$
    select jsonb_build_object(
      'full_name', a.full_name,
      'contact_phone', a.contact_phone,
      'patient_code', p.patient_code,
      'age', p.age,
      'blood_group', p.blood_group,
      'emergency_contact_name', p.emergency_contact_name,
      'emergency_contact_phone', p.emergency_contact_phone,
      'emergency_contact_relation', p.emergency_contact_relation,
      'medical_conditions', coalesce(c.medical_conditions, '{}'),
      'current_medication', coalesce(c.current_medication, '[]'::jsonb),
      'previous_surgeries', coalesce(c.previous_surgeries, '[]'::jsonb),
      'allergies', coalesce(c.allergies, '{}'),
      'last_appointment_date', c.last_appointment_date,
      'is_doctor_verified', coalesce(c.is_doctor_verified, false),
      'updated_at', c.updated_at
    )
    from public.patient_profiles p
    join public.accounts a on a.id = p.patient_id
    left join public.clinical_records c on c.patient_id = p.patient_id
    where p.qr_token = lookup_token;
  $$;
  revoke all on function public.get_emergency_triage_by_token(uuid) from public;
  grant execute on function public.get_emergency_triage_by_token(uuid) to anon, authenticated;
  ```
- **Non-Negotiable Privacy Invariant (N1)**:
  - `residential_address` and `spouse_dependents` are STRICTLY EXCLUDED from the JSON projection.
  - `qr_token` is also omitted from output.
  - If `lookup_token` does not exist or has been regenerated, query returns zero rows -> function returns `null`.

### 5.2 RPC 2: `submit_self_reported_baseline(p_conditions text[], p_allergies text[])`
- **Access Level**: `authenticated` only.
- **Constraints**:
  - Maximum 50 conditions and 50 allergies; rejects greater arrays with `'Too many entries'`.
  - Only updates while `is_doctor_verified = false`.
  - If row was already verified or patient profile missing, raises `'Record is already doctor-verified, or no patient profile exists'`.
- **Privilege Grants**: Revoked from public, anon; granted only to `authenticated`.

### 5.3 RPC 3: `regenerate_qr_token()`
- **Access Level**: `authenticated` only.
- **Operation**:
  - Generates a new `gen_random_uuid()`.
  - Updates `patient_profiles.qr_token` for caller (`where patient_id = (select auth.uid())`).
  - Returns new UUID.
  - Immediately invalidates previous QR token (old token returns `null` from emergency triage RPC).
- **Privilege Grants**: Revoked from public, anon; granted only to `authenticated`.

---

## 6. Section 4: Zero-Mock Supabase Authentication & Role Life Cycle

### 6.1 Real Authentication Calls
Umbrella operates with zero mock authentication:
- `/signup` calls `supabase.auth.signUp({ email, password, options: { data: { role, full_name, contact_phone, ... } } })`.
- `/login` calls `supabase.auth.signInWithPassword({ email, password })`.
- Top bar / navigation calls `supabase.auth.signOut()`.

### 6.2 Role Provisioning via Database Trigger (`handle_new_user`)
- The client-provided `options.data.role` is inspected **once** during user insertion into `auth.users`.
- Role escalation prevention:
  - If `role === 'doctor'`, account is created with `role = 'doctor'`, `doctor_status = 'pending'`.
  - If `role` is anything else (`'patient'`, `'admin'`, `'root'`, null), account is safely forced to `role = 'patient'`, `doctor_status = null`.
- Subsequent authorization checks **never** consult JWT `user_metadata` or client storage; they query `public.accounts` on the server using `auth.uid()`.

### 6.3 Pending Doctor Approval Flow (DECISIONS D1)
1. Doctor registers on `/signup?role=doctor`, providing full name, phone, medical license number, and specialization.
2. Account is created in database with `doctor_status = 'pending'`.
3. Doctor logs in:
   - Request interception (`middleware.ts` / `proxy.ts`) permits navigation to `/portal/doctor`.
   - The `/portal/doctor` page checks `account.doctor_status`. Because it is `'pending'`, it renders a read-only "Verification Pending" screen:
     *"Your medical license is being verified by the administrator. You will gain access once verified."*
   - Database RLS prevents any SELECT or UPDATE on patient data (`is_approved_doctor()` returns `false`).
4. Administrator approves doctor directly via database command:
   ```sql
   update public.accounts set doctor_status = 'approved' where email = 'doctor@example.com';
   ```
5. Once approved:
   - `is_approved_doctor()` returns `true`.
   - Full doctor portal is unlocked: Patient Lookup Bar, Patient Context Banner, Clinical Editor, and Appointment Scheduler.

### 6.4 Session & Caller Verification
- Caller identity must **always** be determined with `supabase.auth.getUser()`, never `supabase.auth.getSession()` (as `getSession()` reads unverified cached JWTs).
- Discriminated union return type for session state:
  ```typescript
  type AuthAccountState =
    | { status: 'anonymous' }
    | { status: 'patient'; account: AccountRow; profile: PatientProfileRow }
    | { status: 'doctor_pending'; account: AccountRow }
    | { status: 'doctor_approved'; account: AccountRow }
    | { status: 'doctor_rejected'; account: AccountRow };
  ```

---

## 7. Section 5: Environment Variables & Key Hygiene

### 7.1 Environment Variables
v1 requires exactly two environment variables in `.env.local` / `.env.example`:
```env
NEXT_PUBLIC_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=YOUR-ANON-OR-PUBLISHABLE-KEY
```
- The variable name `NEXT_PUBLIC_SUPABASE_ANON_KEY` is maintained across all environments, even when using Supabase's modern publishable keys.

### 7.2 Strict Ban on `service_role` Key (N4)
- The Supabase `service_role` key bypasses RLS and grants full database ownership.
- In Umbrella v1:
  - The `service_role` key must **NEVER** appear in source code, `.env.example`, `.env.local`, documentation, logs, git commits, or chat.
  - All operations are conducted strictly via the anon/publishable key and enforced through Postgres RLS and `SECURITY DEFINER` functions with restricted execution grants.

---

## 8. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Database Schema | `accounts` Table | Core user identity, role, and approval status | `auth.users` trigger insertion | `accounts` row with primary key `id` | Check constraint `accounts_role_fields_chk` enforces doctor metadata | `UMBRELLA_BUILD_KIT.md:548-563`, `rls-patterns.sql:8-24` |
| 2 | Database Schema | `patient_profiles` Table | Patient demographics, emergency contact, QR token | Trigger on `accounts` / `auth.users` | `patient_profiles` row with `patient_id` FK | Unique constraint violation if duplicate token/code | `UMBRELLA_BUILD_KIT.md:565,614-624`, `DECISIONS.md:14` |
| 3 | Database Schema | `clinical_records` Table | Medical history, conditions, medications, surgeries, allergies, doctor verification | Trigger on `patient_profiles` | `clinical_records` row with `patient_id` PK | Direct patient updates blocked by RLS | `UMBRELLA_BUILD_KIT.md:566,632-640`, `DECISIONS.md:20` |
| 4 | Database Schema | `appointments` Table | Scheduled, completed, or cancelled doctor appointments | Doctor insertion via appointment manager | `appointments` row | Restricted deletion (`on delete restrict` on doctor) | `UMBRELLA_BUILD_KIT.md:567-570`, `DECISIONS.md:18` |
| 5 | Trigger | Auto Timestamp Updater (`set_updated_at`) | Automatically keeps `updated_at` timestamps fresh | BEFORE UPDATE trigger | Updated `new.updated_at = now()` | None | `rls-patterns.sql:45-52` |
| 6 | Trigger | Auth Signup Handler (`handle_new_user`) | Maps `auth.users` metadata to `accounts` and `patient_profiles` | INSERT on `auth.users` | Synchronized `accounts` and optional `patient_profiles` row | Invalid roles safely coerced to `'patient'` | `rls-patterns.sql:54-90`, `DECISIONS.md:7` |
| 7 | Trigger | Auto Clinical Record Provisioning (`create_clinical_record`) | Guarantees every patient has a baseline clinical record | INSERT on `patient_profiles` | Initial row in `clinical_records` | `on conflict do nothing` avoids failure | `rls-patterns.sql:93-101` |
| 8 | Trigger | Doctor Verification Stamp (`stamp_clinical_update`) | Enforces server-side verification and updates clinician ID | BEFORE UPDATE on `clinical_records` | Sets `is_doctor_verified = true`, `last_updated_by_doctor_id` | Skips stamping if `umbrella.skip_stamp = 'on'` | `rls-patterns.sql:103-117`, `DECISIONS.md:20` |
| 9 | Trigger | Appointment Completion Sync (`on_appointment_completed`) | Updates patient's last appointment date and summary | AFTER UPDATE on `appointments` where `status = 'completed'` | Updates `clinical_records.last_appointment_*` | Does NOT flip `is_doctor_verified` | `rls-patterns.sql:119-136`, `DECISIONS.md:22` |
| 10 | Security Helper | Doctor Approval Checker (`is_approved_doctor`) | Recursion-safe check for approved clinician status | Session `auth.uid()` | `boolean` (`true` if doctor approved) | Returns `false` for unapproved doctors or patients | `rls-patterns.sql:33-43`, `DECISIONS.md:5` |
| 11 | RLS Policy | Self Account Access (`accounts_select_self`, `accounts_update_self`) | Allows authenticated users to view/update own account info | `auth.uid() = id` | Permitted row read/write | Restricted to granted columns | `rls-patterns.sql:144-155` |
| 12 | RLS Policy | Doctor Patient Read Access (`accounts_select_patients_for_doctors`) | Allows approved doctors to read all patient accounts | `public.is_approved_doctor() = true` | Permitted rows where `role = 'patient'` | Disallowed for pending/rejected doctors | `rls-patterns.sql:146-147` |
| 13 | RLS Policy | Patient Doctor Read Access (`accounts_select_my_doctors`) | Allows patients to see doctors with whom they have appointments | Appointment association | Permitted doctor account rows | Returns zero rows if no appointment exists | `rls-patterns.sql:148-152` |
| 14 | RLS Policy | Patient Profile Isolation (`pp_select`, `pp_update_self`) | Isolates patient demographics to patient and approved doctors | `patient_id = auth.uid()` or approved doctor | Demographic row | Foreign patient cannot read; cannot update token/code | `rls-patterns.sql:156-160` |
| 15 | RLS Policy | Clinical Record Doctor Access (`cr_select`, `cr_update_doctor`) | Restricts clinical updates strictly to approved doctors | Approved doctor check | Clinical record modification | Patient updates blocked at RLS layer | `rls-patterns.sql:162-166` |
| 16 | RLS Policy | Appointment Management (`ap_select`, `ap_insert_doctor`, `ap_update_doctor`) | Allows doctors to create/update appointments with their doctor_id | `doctor_id = auth.uid()` | Appointment row creation | Non-doctor or mismatched doctor_id blocked | `rls-patterns.sql:167-172` |
| 17 | Privilege Control | Column-level UPDATE Grants | Protects immutable/sensitive columns from client tampering | Specific column lists | Allowed column update | PostgreSQL `insufficient_privilege` error | `rls-patterns.sql:174-184`, `DECISIONS.md:9` |
| 18 | RPC Function | Emergency Triage (`get_emergency_triage_by_token`) | Zero-login public access to life-critical medical data | `lookup_token uuid` | JSON object of medical data | Returns `null` on invalid/rotated token; excludes address/dependents | `rls-patterns.sql:186-212`, `AGENTS.md:233` |
| 19 | RPC Function | Baseline Self-Reporting (`submit_self_reported_baseline`) | Allows patients to record initial conditions/allergies | `p_conditions text[]`, `p_allergies text[]` | `void` | Raises exception if verified or array length > 50 | `rls-patterns.sql:214-230`, `DECISIONS.md:20` |
| 20 | RPC Function | Token Rotation (`regenerate_qr_token`) | Rotates caller's QR token and invalidates prior code | `auth.uid()` | New `uuid` | Raises exception if patient profile missing | `rls-patterns.sql:232-242`, `DECISIONS.md:9` |
| 21 | Auth & RBAC | Zero-Mock Sign Up & Approval | Registers real accounts, isolates pending doctors | Form inputs | Auth user + DB account row | Doctor cannot read medical data until approved | `UMBRELLA_BUILD_KIT.md:1040-1059` |
| 22 | Key Hygiene | Anon-Key-Only Architecture | Enforces client & server execution without admin service role | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Scoped DB access | Service role forbidden from repo and runtime | `AGENTS.md:236`, `02-security-privacy.md:368` |

---

## 9. Edge Cases

| # | Feature | Input / Condition | Observed / Documented Behavior |
|---|---------|-------------------|--------------------------------|
| 1 | Direct Table Access | Anon user performs `select * from public.accounts;` | Permission denied (`insufficient_privilege`) because `anon` has zero table grants. |
| 2 | Emergency RPC | Anon user calls `get_emergency_triage_by_token('00000000-0000-0000-0000-000000000000')` | Returns `null`. Emergency route renders generic 404 with no debugging hints. |
| 3 | Emergency RPC Privacy | Caller inspects JSON response of `get_emergency_triage_by_token` | `residential_address`, `spouse_dependents`, and `qr_token` keys are completely absent. |
| 4 | Doctor Sign Up | Doctor signs up without `medical_license_number` | Database constraint `accounts_role_fields_chk` triggers and aborts user registration. |
| 5 | Role Escalation Attempt | Attacker submits signup with `options.data.role = 'admin'` | `handle_new_user` trigger evaluates case expression: falls back to `'patient'`. |
| 6 | Privilege Escalation Attempt | Patient attempts `update public.accounts set role = 'doctor' where id = auth.uid()` | Aborted with `permission denied for table accounts` (column `role` not in grant list). |
| 7 | Token Manipulation Attempt | Patient attempts `update public.patient_profiles set qr_token = '...' where patient_id = auth.uid()` | Aborted with `permission denied` (column `qr_token` not in grant list). |
| 8 | Direct Clinical Modification | Patient attempts direct `update public.clinical_records set allergies = '...'` | Policy check fails (`cr_update_doctor` requires `is_approved_doctor()`). |
| 9 | Baseline Post-Verification | Patient calls `submit_self_reported_baseline` when `is_doctor_verified = true` | Raises exception `'Record is already doctor-verified, or no patient profile exists'`. |
| 10 | Baseline Input Flooding | Patient submits baseline with 51 allergy items | Raises exception `'Too many entries'`. |
| 11 | Spoofed Verification Stamp | Doctor sends `is_doctor_verified = false` or fake `last_updated_by_doctor_id` | `stamp_clinical_update` trigger overrides payload, forcing `true` and `auth.uid()`. |
| 12 | Doctor No-Op Verification | Doctor submits update setting `allergies = allergies` on unverified record | `stamp_clinical_update` trigger fires on UPDATE, stamping record as doctor-verified. |
| 13 | Appointment Completion Stamp Leak | Doctor marks appointment as `'completed'` | Trigger `on_appointment_completed` sets `skip_stamp = 'on'`; `is_doctor_verified` remains unchanged. |
| 14 | Appointment Doctor Impersonation | Doctor attempts to insert appointment with another doctor's `doctor_id` | RLS `with check` fails (`doctor_id = (select auth.uid())`). |
| 15 | Deletion Resistance | Authenticated patient or doctor attempts `DELETE FROM public.accounts` | Aborted (no DELETE policies exist; delete privileges revoked). |
| 16 | QR Invalidation After Rotation | Patient calls `regenerate_qr_token()`, then old QR is scanned | Emergency RPC with old UUID returns `null`; scanner page displays 404. |
| 17 | Pending Doctor Isolation | Unapproved doctor navigates to `/portal/doctor` | UI displays "Verification Pending"; database queries return zero patient records. |
| 18 | Malformed URL Token | Client visits `/emergency/not-a-valid-uuid` | Zod validation in Next.js Server Component rejects token prior to DB call -> `notFound()`. |
| 19 | PostgREST Filter Injection | User searches for `%`, `_`, or `(` in doctor lookup | Parameterized queries or zod sanitization prevents PostgREST filter string syntax breakage. |
| 20 | Unauthenticated Portal Access | Guest user visits `/portal/patient` or `/portal/doctor` | Middleware / proxy redirects to `/login?next=/portal/...`. |

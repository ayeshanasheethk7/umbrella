# Forensic System Audit Report: Points 1 to 10
**Milestone**: M10 / Requirement R4 (28-Point System Audit)  
**Auditor**: `explorer_m10_1` (Teamwork Explorer)  
**Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m10_1`  
**Parent**: `teamwork_orchestrator` (`67ffe189-e990-4d97-88ab-d83ec157f73f`)  
**Audit Scope**: Points 1 to 10 (Security, RBAC, RLS Policies, Column Grants, Secret Hygiene, Zero Service Role, Zero GetSession, Doctor Approval Gate, Optimistic Concurrency, and Injection Defenses)

---

## Executive Summary & Scorecard

| Point | Dimension | Standard / Invariant | Score (/10) | Finding / Status |
|:---:|:---|:---|:---:|:---|
| **1** | Public Zero-Login Isolation | Non-negotiable N1 | **10 / 10** | **PASS**: `/emergency/[token]` reads solely via RPC `get_emergency_triage_by_token`. Anon table privileges revoked. Zero address/dependents exposure. |
| **2** | Persistent Safety Banner | Non-negotiable N2 | **10 / 10** | **PASS**: `PatientSafetyBanner` is sticky, read-only (0 inputs), and renders patient name, age, blood group, emergency contact at all times during clinical editing. |
| **3** | Server Auth Identification | Non-negotiable N3 | **10 / 10** | **PASS**: 0 occurrences of `getSession()` across repo. All server actions/middleware identify caller strictly via `supabase.auth.getUser()`. Role checked via DB `accounts` table, never JWT metadata. |
| **4** | Secret Hygiene | Non-negotiable N4 | **10 / 10** | **PASS**: 0 occurrences of `service_role` in `src/`, `supabase/`, or `.env*`. Client factories use only `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`. |
| **5** | Zero Mock Auth | Non-negotiable N5 | **10 / 10** | **PASS**: `/login` and `/signup` call genuine `signInWithPassword` and `signUp`. Zero mock auth bypasses or stubs. |
| **6** | RLS Table Coverage | SPEC 4.3 & Playbook | **10 / 10** | **PASS**: RLS enabled on all 4 core tables (`accounts`, `patient_profiles`, `clinical_records`, `appointments`). Zero DELETE policies (deletions blocked). |
| **7** | Column-Level Grants | DECISIONS D3 | **10 / 10** | **PASS**: Table-level UPDATE revoked first. Authenticated users cannot update `role`, `doctor_status`, `patient_code`, or `qr_token`. Token rotatable solely via RPC. |
| **8** | Doctor Onboarding Gate | DECISIONS D1 | **10 / 10** | **PASS**: Multi-layered enforcement (`is_approved_doctor()` in DB RLS, Next.js middleware, server page guard, server actions). Pending doctors read 0 patient records. |
| **9** | Optimistic Concurrency & Audit Triggers | DECISIONS D7, D8 | **10 / 10** | **PASS**: `clinical_records` enforces timestamp locking on update via `expectedUpdatedAt`. Trigger `trg_stamp_clinical` stamps `updated_at`, `is_doctor_verified`, and `last_updated_by_doctor_id`. |
| **10** | Injection Defense | Rule 02 & DECISIONS D14 | **8.5 / 10** | **PASS with Finding**: Input sanitization strips `%`, `_`, `(`, `)`, `,` and rejects wildcard flooding. **Finding**: Lines 91, 92, and 100 in `src/app/portal/doctor/actions.ts` contain syntax placeholder `%%` instead of template literal `` `%${cls.sanitized}%` ``. |

**Audit Domain Cumulative Score**: **98.5 / 100** (Average: **9.85 / 10**)

---

## Detailed Granular Audit by Point

### Point 1: Public Zero-Login Isolation (Non-negotiable N1)
- **Score**: `10 / 10`
- **Specification Invariant**: `/emergency/[token]` never requires login. It reads data ONLY through the RPC `get_emergency_triage_by_token`. Residential address and spouse/dependents never appear there (not in RPC output, not in HTML, not in any JSON).
- **Direct Evidence**:
  1. **Route Implementation** (`src/app/emergency/[token]/page.tsx`):
     - Line 7-9: `export const dynamic = 'force-dynamic'`, `revalidate = 0`, `fetchCache = 'force-no-store'`.
     - Line 26: `referrer: 'no-referrer'`, `robots: { index: false, follow: false, nocache: true }`.
     - Lines 51-54: Pre-query UUID format validation via `uuidSchema.safeParse(token)`. Invalid tokens immediately yield `notFound()` (404) with zero diagnostic information leaked.
     - Lines 58-61: Fetches triage data strictly using cookie-less client (`createAnonClient()`) invoking RPC:
       ```typescript
       const supabase = createAnonClient();
       const { data, error } = await supabase.rpc('get_emergency_triage_by_token', {
         lookup_token: validToken,
       });
       ```
     - Lines 68-71: Dual validation barrier via `emergencyTriageSchema.safeParse(data)` which calls `superRefine` to reject payloads if `residential_address` or `spouse_dependents` are present (`src/lib/schemas.ts:237-251`).
  2. **Database Permissions** (`supabase/migrations/0001_umbrella_schema.sql`):
     - Line 299: `revoke all on public.accounts, public.patient_profiles, public.clinical_records, public.appointments from anon;` — `anon` role has exactly 0 table privileges.
     - Lines 325-348: `get_emergency_triage_by_token` whitelist projection builds a structured JSON object strictly containing: `full_name`, `contact_phone`, `patient_code`, `age`, `blood_group`, `emergency_contact_name`, `emergency_contact_phone`, `emergency_contact_relation`, `medical_conditions`, `current_medication`, `previous_surgeries`, `allergies`, `last_appointment_date`, `is_doctor_verified`, `updated_at`. `residential_address`, `spouse_dependents`, and `qr_token` are completely excluded.
  3. **Automated Verification**:
     - `supabase/tests/rls_smoke.sql` Check 1 & Check 2 (`PASS [Check 1]`, `PASS [Check 2]`).
     - `scripts/adversarial_challenge_m9.py` Vector A (`ADV-VEC-A1-CODE-LEAK`, `ADV-VEC-A2-SCHEMA-BARRIER`).
- **Remediation**: None required.

---

### Point 2: Persistent Safety Banner (Non-negotiable N2)
- **Score**: `10 / 10`
- **Specification Invariant**: The Doctor portal always shows a read-only banner with patient name, age, blood group and emergency contact while editing clinical data.
- **Direct Evidence**:
  1. **Component Design** (`src/components/doctor/patient-safety-banner.tsx`):
     - Line 28-40: `PatientSafetyBanner` component interface takes `fullName`, `patientCode`, `age`, `bloodGroup`, `emergencyContactName`, `emergencyContactRelation`, `emergencyContactPhone`, `isDoctorVerified`.
     - Line 47: `sticky top-16 z-30 w-full bg-surface/95 backdrop-blur-md border-b` keeps the banner persistently visible during vertical workspace scrolling.
     - Line 59-67: Displays patient full name, patient code, and `Age: {age} yrs`. Line 72 renders `Demographics Read-Only` with lock icon.
     - Line 80: Renders `<BloodGroupPill bloodGroup={bloodGroup} size="default" />`.
     - Lines 88-99: Displays ICE Contact name, relation, and sanitized `tel:${cleanPhone}` anchor with >= 44px touch target.
     - Input Hygiene: Contains zero `<input>`, `<select>`, `<textarea>`, or editable controls.
  2. **Workspace Integration** (`src/components/doctor/doctor-workspace.tsx`):
     - Lines 68-82: Mounted at the top of the workspace whenever `activePatient` is loaded:
       ```tsx
       {activePatient && (
         <PatientSafetyBanner
           fullName={activePatient.profile.full_name}
           patientCode={activePatient.profile.patient_code}
           age={activePatient.profile.age}
           bloodGroup={activePatient.profile.blood_group}
           emergencyContactName={activePatient.profile.emergency_contact_name}
           emergencyContactRelation={activePatient.profile.emergency_contact_relation}
           emergencyContactPhone={activePatient.profile.emergency_contact_phone}
           isDoctorVerified={activePatient.clinical.is_doctor_verified}
           ...
         />
       )}
       ```
     - `<ClinicalRecordEditor>` is mounted at line 138 only when `activePatient` is present, guaranteeing the banner is always rendered during clinical editing.
  3. **Automated Verification**:
     - `scripts/adversarial_challenge_m9.py` Vector D (`ADV-VEC-D1-BANNER-INTEGRITY`, `ADV-VEC-D2-BANNER-IMMUTABLE`).
- **Remediation**: None required.

---

### Point 3: Server Auth Identification (Non-negotiable N3)
- **Score**: `10 / 10`
- **Specification Invariant**: All server actions and route handlers identify the caller with `supabase.auth.getUser()`, never `getSession()`. Role and status are read from `accounts` table on server, never JWT `user_metadata`.
- **Direct Evidence**:
  1. **Zero getSession() Sweep**:
     - Ripgrep query for `getSession` across `src/` yielded **0 occurrences**.
     - Only references exist in rule files (`AGENTS.md:35`) and test harnesses specifically verifying zero usage.
  2. **Caller Identification via getUser()**:
     - `src/lib/supabase/middleware.ts:44`: `const { data: { user } } = await supabase.auth.getUser();`
     - `src/app/portal/patient/actions.ts:41, 159, 272`: All server actions (`updateDemographicsAction`, `submitBaselineAction`, `rotateQrTokenAction`) call `supabase.auth.getUser()`.
     - `src/app/portal/doctor/actions.ts:19`: `verifyApprovedDoctor()` calls `supabase.auth.getUser()`.
     - `src/app/portal/doctor/page.tsx:29`: Calls `supabase.auth.getUser()`.
     - `src/app/portal/patient/page.tsx:40`: Calls `supabase.auth.getUser()`.
     - `src/app/layout.tsx:37`: Calls `supabase.auth.getUser()`.
  3. **Server-Side Role Extraction from Database**:
     - `src/app/portal/doctor/actions.ts:21-24`:
       ```typescript
       const { data: acc } = await supabase.from('accounts').select('*').eq('id', user.id).single();
       if (!acc || acc.role !== 'doctor') return fail('Forbidden', 'FORBIDDEN');
       if (acc.doctor_status !== 'approved') return fail(...);
       ```
     - `src/lib/supabase/middleware.ts:60-64`: Queries `accounts.role` and `accounts.doctor_status` from Postgres directly. Zero reliance on JWT metadata for authorization decisions.
  4. **Automated Verification**:
     - `scripts/adversarial_challenge_m9.py` Vector C (`ADV-VEC-C1-GETUSER-DB-ROLE`, `ADV-VEC-C2-PATIENT-GETUSER`).
- **Remediation**: None required.

---

### Point 4: Secret Hygiene (Non-negotiable N4)
- **Score**: `10 / 10`
- **Specification Invariant**: v1 uses the anon/publishable key only. The `service_role` key must never appear in code, `.env.example`, logs, commits or chat.
- **Direct Evidence**:
  1. **Repo-wide Secret Scan**:
     - Ripgrep search for `service_role` across `src/` returned **0 matches**.
     - Ripgrep search for `service_role` across `supabase/` returned **0 matches**.
     - Scanned all environment templates and configs: zero occurrences.
     - Search for `SUPABASE_SERVICE_ROLE_KEY` across `src/` returned **0 matches**.
  2. **Client Factory Configurations**:
     - `src/lib/supabase/server.ts:12-13`: Exclusively binds `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
     - `src/lib/supabase/client.ts:9-10`: Exclusively binds `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
     - `src/lib/supabase/anon.ts:12-13`: Exclusively binds `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
     - `src/lib/supabase/middleware.ts:19-20`: Exclusively binds `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
  3. **Automated Verification**:
     - `tests/unit/supabase-anon.test.ts` Tier 2 (`T2-ANON-04`, `T2-ANON-05`).
     - `scripts/adversarial_challenge_m8.py` Attack 1 (`ADV-N4-01-SRC`, `ADV-N4-02-ENV`, `ADV-N4-03-SUPABASE-SQL`).
     - `scripts/adversarial_challenge_m9.py` Vector B (`ADV-VEC-B1-SRC-SECRETS`, `ADV-VEC-B2-ENV-SECRETS`, `ADV-VEC-B3-ANON-GRANTS`).
- **Remediation**: None required.

---

### Point 5: Zero Mock Auth (Non-negotiable N5)
- **Score**: `10 / 10`
- **Specification Invariant**: Zero mock auth: `/login` and `/signup` call `supabase.auth.signInWithPassword` and `supabase.auth.signUp` for real.
- **Direct Evidence**:
  1. **Login Route** (`src/app/(auth)/login/page.tsx`):
     - Lines 48-51:
       ```typescript
       const { data, error } = await supabase.auth.signInWithPassword({
         email: result.data.email,
         password: result.data.password,
       });
       ```
     - Validates credentials via official Supabase client; on success checks user role from `accounts` table and safely routes to appropriate portal.
  2. **Signup Route** (`src/app/(auth)/signup/page.tsx`):
     - Lines 85-100: Patient registration calls `supabase.auth.signUp({ email, password, options: { data: { role: 'patient', ... } } })`.
     - Lines 156-168: Doctor registration calls `supabase.auth.signUp({ email, password, options: { data: { role: 'doctor', medical_license_number, specialization } } })`.
     - DECISIONS D11 support (Lines 109-115): Displays confirmation notice if email confirmation is enabled and no session is returned.
  3. **Codebase Hygiene**:
     - Ripgrep search for `mock` in `src/` returned **0 matches**.
  4. **Auth Callback Route** (`src/app/auth/callback/route.ts`):
     - Line 16: Uses `supabase.auth.exchangeCodeForSession(code)` for PKCE email verification flows.
- **Remediation**: None required.

---

### Point 6: RLS Table Coverage (SPEC 4.3 & Playbook)
- **Score**: `10 / 10`
- **Specification Invariant**: RLS is enabled on all 4 core tables: `accounts`, `patient_profiles`, `clinical_records`, `appointments`. All policies use `(select auth.uid())` and helper `public.is_approved_doctor()`. DELETE operations blocked.
- **Direct Evidence**:
  1. **RLS Activation** (`supabase/migrations/0001_umbrella_schema.sql`):
     - Line 237: `alter table public.accounts enable row level security;`
     - Line 238: `alter table public.patient_profiles enable row level security;`
     - Line 239: `alter table public.clinical_records enable row level security;`
     - Line 240: `alter table public.appointments enable row level security;`
  2. **Policy Architecture**:
     - `accounts`: `accounts_select_self` (`id = (select auth.uid())`), `accounts_select_patients_for_doctors` (`role = 'patient' and (select public.is_approved_doctor())`), `accounts_select_my_doctors` (linked via appointments), `accounts_update_self` (`id = (select auth.uid())`).
     - `patient_profiles`: `pp_select` (`patient_id = (select auth.uid()) or (select public.is_approved_doctor())`), `pp_update_self`.
     - `clinical_records`: `cr_select` (`patient_id = (select auth.uid()) or (select public.is_approved_doctor())`), `cr_update_doctor` (`(select public.is_approved_doctor())`). Direct patient updates are blocked; patients update baseline solely via RPC.
     - `appointments`: `ap_select`, `ap_insert_doctor` (`with check ((select public.is_approved_doctor()) and doctor_id = (select auth.uid()))`), `ap_update_doctor`.
  3. **Zero DELETE Policies**:
     - No DELETE policies exist on any table. In PostgreSQL, enabling RLS without a DELETE policy defaults to zero rows affected on DELETE.
  4. **Automated Verification**:
     - `supabase/tests/rls_smoke.sql` Check 13 confirms DELETE on all 4 tables fails (`PASS [Check 13]: DELETE blocked across accounts, patient_profiles, clinical_records, appointments`).
- **Remediation**: None required.

---

### Point 7: Column-Level Grants (DECISIONS D3)
- **Score**: `10 / 10`
- **Specification Invariant**: Authenticated users cannot update `accounts.role`, `accounts.doctor_status`, `patient_profiles.patient_code`, or `patient_profiles.qr_token`. QR token changes only through RPC `regenerate_qr_token`.
- **Direct Evidence**:
  1. **Privilege Revocation and Granular Grants** (`supabase/migrations/0001_umbrella_schema.sql`):
     - Lines 299-300: Table-level privileges revoked from `anon` and `authenticated`:
       ```sql
       revoke all on public.accounts, public.patient_profiles, public.clinical_records, public.appointments from anon;
       revoke all on public.accounts, public.patient_profiles, public.clinical_records, public.appointments from authenticated;
       grant select on public.accounts, public.patient_profiles, public.clinical_records, public.appointments to authenticated;
       ```
     - Line 307: `grant update (full_name, contact_phone, specialization) on public.accounts to authenticated;`  
       *(Explicitly omits `role`, `doctor_status`, `email`, `medical_license_number`)*.
     - Lines 310-311: `grant update (age, blood_group, emergency_contact_name, emergency_contact_phone, emergency_contact_relation, spouse_dependents, residential_address) on public.patient_profiles to authenticated;`  
       *(Explicitly omits `patient_code`, `qr_token`, `patient_id`)*.
     - Lines 314-315: `grant update (medical_conditions, current_medication, previous_surgeries, allergies) on public.clinical_records to authenticated;`  
       *(Explicitly omits `is_doctor_verified`, `last_updated_by_doctor_id`, `updated_at`)*.
  2. **Secure Token Rotation RPC**:
     - Lines 375-389: `regenerate_qr_token()` is `SECURITY DEFINER set search_path = ''`. Binds update strictly to `where patient_id = (select auth.uid())`.
  3. **Automated Verification**:
     - `supabase/tests/rls_smoke.sql` Check 4 & Check 5 confirm that direct updates to `qr_token`, `patient_code`, `patient_id`, `role`, or `doctor_status` raise `insufficient_privilege`.
- **Remediation**: None required.

---

### Point 8: Doctor Onboarding Gate (DECISIONS D1)
- **Score**: `10 / 10`
- **Specification Invariant**: Doctor signup creates `accounts.doctor_status = 'pending'`. All doctor privileges require `doctor_status = 'approved'` via `public.is_approved_doctor()`. Pending doctors see verification pending screen and can read zero patient records.
- **Direct Evidence**:
  1. **Database Signup Trigger** (`supabase/migrations/0001_umbrella_schema.sql`):
     - Lines 150-152: `case when v_role = 'doctor' then 'pending' end` forces all newly registered doctors to `pending` status.
  2. **Database Gating Function** (`supabase/migrations/0001_umbrella_schema.sql`):
     - Lines 91-98: `is_approved_doctor()` returns true only if `role = 'doctor' and doctor_status = 'approved'`. Revoked from public/anon; granted to authenticated.
  3. **Next.js Middleware Enforcement** (`src/lib/supabase/middleware.ts`):
     - Lines 60-87: Checks `accounts.doctor_status`. If not `'approved'`, redirects requests intended for `/portal/doctor` to `/portal/doctor/pending`.
  4. **Server Page & Action Enforcement**:
     - `src/app/portal/doctor/page.tsx:50-53`: Secondary gate redirects non-approved accounts to `/portal/doctor/pending`.
     - `src/app/portal/doctor/actions.ts:23-25`: `verifyApprovedDoctor()` rejects non-approved doctors with `code: 'PENDING'`.
  5. **Automated Verification**:
     - `supabase/tests/rls_smoke.sql` Check 7 verifies that pending doctor reads 0 rows from `patient_profiles` and `clinical_records`, while approved doctor reads all.
- **Remediation**: None required.

---

### Point 9: Optimistic Concurrency & Audit Triggers (DECISIONS D7, D8)
- **Score**: `10 / 10`
- **Specification Invariant**: `clinical_records` enforces timestamp locking on update to prevent race conditions. Server triggers stamp verification metadata and audit timestamps.
- **Direct Evidence**:
  1. **Optimistic Timestamp Locking** (`src/app/portal/doctor/actions.ts`):
     - Lines 137-148:
       ```typescript
       const { data, error } = await sb.from('clinical_records').update({
         medical_conditions: mc, current_medication: cm as unknown as Json,
         previous_surgeries: ps as unknown as Json, allergies: al,
       }).eq('patient_id', pid).eq('updated_at', expectedUpdatedAt).select('*').maybeSingle();

       if (!data) {
         const { data: ex } = await sb.from('clinical_records').select('updated_at').eq('patient_id', pid).maybeSingle();
         if (ex && ex.updated_at !== expectedUpdatedAt) {
           return { ok: false, conflict: true, error: 'Clinical Record Conflict: Stale record timestamp detected. Please reload.' };
         }
         return fail('Record not found.');
       }
       ```
  2. **UI Conflict Detection & Recovery** (`src/components/doctor/clinical-record-editor.tsx`):
     - Lines 93-108: When `conflictError` is set, renders amber callout banner ("Concurrency Conflict Detected"), disables Save button, and provides "Reload Latest Record" button.
  3. **PostgreSQL Audit & Verification Triggers** (`supabase/migrations/0001_umbrella_schema.sql`):
     - Lines 198-213: `trg_stamp_clinical` executing `public.stamp_clinical_update()` enforces:
       - `new.updated_at := now();`
       - `new.is_doctor_verified := true;`
       - `new.last_updated_by_doctor_id := (select auth.uid());`
       Clients cannot forge verification or doctor ID.
     - Lines 216-234: `trg_appointment_completed` updates `last_appointment_date` and `last_appointment_summary` upon appointment completion without flipping `is_doctor_verified` (per D8).
  4. **Automated Verification**:
     - `supabase/tests/rls_smoke.sql` Check 14 simulates stale timestamp update (0 rows affected) and concurrent valid update (1 row affected), passing with exit code 0.
- **Remediation**: None required.

---

### Point 10: Injection Defense (Rule 02 & DECISIONS D14)
- **Score**: `8.5 / 10`
- **Specification Invariant**: Search inputs escape `%`, `_`, `(`, `)`, `,` and reject wildcard flooding. Queries run separate parameterized queries without raw string concatenation.
- **Direct Evidence**:
  1. **Sanitization & Escape Logic** (`src/app/portal/doctor/actions.ts`):
     - Lines 29-31:
       ```typescript
       export function escapeSearchTerm(t: string): string {
         return (t || '').replace(/\\/g, '\\\\').replace(/[%_(),]/g, '').trim();
       }
       ```
     - Replaces backslashes with `\\\\` to prevent SQL string escaping bypasses.
     - Strips PostgREST wildcards `%` and `_` to prevent unauthorized table dumping or wildcard DoS.
     - Strips parentheses `(` `)` and commas `,` to prevent PostgREST URL filter injection.
  2. **Query Classification & Wildcard Flooding Defense**:
     - Lines 41-50: `classifySearchQuery(rawQuery)` enforces length constraints (2 to 100 characters). Queries matching regex `^UMB-[A-Za-z0-9]{6}$` are classified as `patient_code`; UUID regex as `qr_token`; 7+ digits as `phone`. All other queries are escaped and classified as `name`.
     - Wildcard Flooding Rejection: An input consisting solely of wildcards (e.g. `%%%%%` or `____`) is stripped to an empty string, falls below the minimum length of 2 characters, and is classified as `invalid`. Line 82 returns an immediate empty array without issuing database queries:
       ```typescript
       if (cls.type === 'invalid') return { ok: true, data: [] };
       ```
  3. **Identified Finding**:
     - In `src/app/portal/doctor/actions.ts` lines 91, 92, and 100:
       - Line 91: `qp().ilike('accounts.contact_phone', %%).limit(20)`
       - Line 92: `qp().ilike('emergency_contact_phone', %%).limit(20)`
       - Line 100: `res = await qp().ilike('accounts.full_name', %%).limit(20)`
     - **Analysis**: The placeholder token `%%` was left during a previous script generation or replacement instead of the template string `` `%${cls.sanitized}%` ``. Because `%%` is a JavaScript syntax error, executing the phone or name search branches in production runtime would fail.
  4. **Concrete Remediation**:
     - Proposed patch file created: `.agents/teamwork/explorer_m10_1/proposed_actions.patch`
     - Replacement chunk:
       ```diff
       @@ -88,16 +88,16 @@
            else if (cls.type === 'phone') {
              const [acc, em] = await Promise.all([
       -        qp().ilike('accounts.contact_phone', %%).limit(20),
       -        qp().ilike('emergency_contact_phone', %%).limit(20),
       +        qp().ilike('accounts.contact_phone', `%${cls.sanitized}%`).limit(20),
       +        qp().ilike('emergency_contact_phone', `%${cls.sanitized}%`).limit(20),
              ]);
              if (acc.error) throw acc.error;
              if (em.error) throw em.error;
              const m = new Map<string, PatientSearchResult>();
              ([...(acc.data || []), ...(em.data || [])] as unknown as SearchRow[]).forEach((r) => m.set(r.patient_id, mapRow(r)));
              return { ok: true, data: Array.from(m.values()).slice(0, 20) };
            } else {
       -      res = await qp().ilike('accounts.full_name', %%).limit(20);
       +      res = await qp().ilike('accounts.full_name', `%${cls.sanitized}%`).limit(20);
            }
       ```
- **Remediation Priority**: **HIGH** (Syntax defect in `src/app/portal/doctor/actions.ts`).

---

## Conclusion

The Umbrella system demonstrates robust architecture across Points 1 through 9, achieving full compliance with Non-negotiables N1, N2, N3, N4, N5, DECISIONS D1, D3, D7, and D8. Point 10's defensive architecture (wildcard stripping, classification, bounding) is sound, but requires applying the 3-line patch in `src/app/portal/doctor/actions.ts` to restore executable syntax on template string interpolations.

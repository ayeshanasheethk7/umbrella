# Handoff Report: Milestone M5 Data Fetching & Server Mutation Architecture

## 1. Observation
1. **Schema & Types**:
   - `supabase/migrations/0001_umbrella_schema.sql` (lines 35-48): `public.patient_profiles` defines `patient_code text unique not null`, `qr_token uuid unique not null default gen_random_uuid()`, `age integer not null default 0`, `blood_group text`, `emergency_contact_*`, `spouse_dependents jsonb`, `residential_address text`.
   - `supabase/migrations/0001_umbrella_schema.sql` (lines 16-31): `public.accounts` defines `id uuid`, `email text`, `role public.user_role`, `full_name text`, `contact_phone text`. It does **not** contain `patient_code` or `qr_token`.
   - `supabase/migrations/0001_umbrella_schema.sql` (lines 354-370): RPC `public.submit_self_reported_baseline` takes parameters `(p_conditions text[], p_allergies text[])`. It updates `clinical_records` `where patient_id = (select auth.uid()) and is_doctor_verified = false`. If not found, it raises: `'Record is already doctor-verified, or no patient profile exists'`.
   - `supabase/migrations/0001_umbrella_schema.sql` (lines 375-391): RPC `public.regenerate_qr_token()` takes zero args, rotates `patient_profiles.qr_token = gen_random_uuid()` for `patient_id = auth.uid()`, returning the new UUID.
   - There is no `emergency_tokens` table anywhere in `0001_umbrella_schema.sql` or `src/lib/supabase/types.ts`.
2. **Column Grants & RLS Policies**:
   - `0001_umbrella_schema.sql` (lines 307-315):
     `grant update (full_name, contact_phone, specialization) on public.accounts to authenticated;`
     `grant update (age, blood_group, emergency_contact_name, emergency_contact_phone, emergency_contact_relation, spouse_dependents, residential_address) on public.patient_profiles to authenticated;`
     `grant update (medical_conditions, current_medication, previous_surgeries, allergies) on public.clinical_records to authenticated;`
   - `0001_umbrella_schema.sql` (lines 278-281): RLS policy `cr_update_doctor` restricts direct UPDATE on `clinical_records` to `is_approved_doctor()`. Authenticated patients **cannot** directly update `clinical_records`; they must use `submit_self_reported_baseline` RPC.
3. **Decisions & Non-Negotiables**:
   - `docs/DECISIONS.md` D5: Age is stored as `age integer` in v1; date_of_birth is backlog.
   - `docs/DECISIONS.md` D7: Self-reported baseline is limited to `conditions` and `allergies` while `is_doctor_verified = false`.
   - `AGENTS.md` N3: Server code identifies the caller with `supabase.auth.getUser()`, never `getSession()`. Role must come from DB `accounts`, never JWT metadata.
   - `AGENTS.md` N4: Anon key only.
   - `src/lib/schemas.ts` (lines 114-162): Contains `patientProfileSchema` and `baselineSubmissionSchema`.

---

## 2. Logic Chain
1. **Data Sourcing for Server Component (`src/app/portal/patient/page.tsx`)**:
   - From Observation 1, `user.id` authenticated via `auth.getUser()` provides the single source of truth for identity.
   - Since `patient_code` and `qr_token` reside in `patient_profiles`, and `full_name` resides in `accounts`, data loading must query both `accounts` and `patient_profiles`.
   - Executing `accounts`, `patient_profiles`, and `clinical_records` queries concurrently via `Promise.all` minimizes latency while maintaining type safety against generated `src/lib/supabase/types.ts`.
2. **Demographics Mutation (`updateDemographicsAction`)**:
   - From Observation 2, authenticated patients have column UPDATE privileges on `accounts(full_name, contact_phone)` and `patient_profiles(age, blood_group, emergency_contact_*, spouse_dependents, residential_address)`.
   - Updating `accounts` then `patient_profiles` inside `updateDemographicsAction` with Zod validation (`updateDemographicsSchema`) ensures data integrity on both tables and allows immediate cache busting via `revalidatePath('/portal/patient')`.
3. **Medical Baseline Mutation (`submitBaselineAction`)**:
   - From Observations 1 & 2, direct updates to `clinical_records` are blocked for patients by RLS policy `cr_update_doctor`. The only legitimate write path is through `submit_self_reported_baseline(p_conditions, p_allergies)`.
   - Although the prompt suggested `p_medications, p_surgeries`, passing those to the existing RPC would cause Postgres signature mismatches and TypeScript compilation errors.
   - Therefore, `submitBaselineAction` must invoke `submit_self_reported_baseline({ p_conditions, p_allergies })`.
   - If `is_doctor_verified` is true, the RPC raises an exception, which the server action intercepts and translates into a friendly, clear lockout explanation per Rule 7.
4. **Token Rotation (`rotateQrTokenAction`)**:
   - From Observation 1, `regenerate_qr_token()` atomically rotates the single active QR UUID on `patient_profiles`. Calling this from a server action and revalidating the path refreshes the client QR view instantly.

---

## 3. Caveats
1. **`p_medications` & `p_surgeries` in Baseline Submission**:
   - Under current schema and DECISIONS D7, patient self-reported baseline is strictly limited to conditions and allergies. If product requirements demand patient-editable medications and surgeries in the future, a new database migration extending the RPC signature and parameter handling will be required.
2. **Doctor Info Enrichment**:
   - If `clinical_records.last_updated_by_doctor_id` is set, fetching the verifying doctor's full name from `accounts` is constrained by RLS policy `accounts_select_my_doctors` (which requires an appointment link). If no appointment exists, the doctor name lookup will return null; the UI must gracefully fall back to "Verified by Licensed Physician".

---

## 4. Conclusion
The data fetching and server mutation design for Milestone M5 is complete, fully specified, and aligned with database schema `0001_umbrella_schema.sql`, DECISIONS D1-D15, and non-negotiables N1-N10.
- `src/app/portal/patient/page.tsx` will authenticate via `getUser()`, guard against doctor roles, and fetch all three tables in parallel.
- `src/app/portal/patient/actions.ts` provides typed server actions `updateDemographicsAction`, `submitBaselineAction`, and `rotateQrTokenAction` returning `{ ok: true, data } | { ok: false, error, fieldErrors }`.
- `src/lib/schemas.ts` is augmented with `updateDemographicsSchema`.

---

## 5. Verification Method
1. **Type Checking**:
   Run `npm run typecheck` (`tsc --noEmit`) to verify that all database query types match `Database['public']['Tables']` and function arguments match `Database['public']['Functions']`.
2. **Linting**:
   Run `npm run lint` to confirm strict Next.js/React standards and zero unused imports or type leaks.
3. **Database Security Test Verification**:
   Inspect `supabase/tests/rls_smoke.sql` to verify that `submit_self_reported_baseline` rejects verified records and respects authenticated caller restrictions.
4. **Invalidation Conditions**:
   - Any modification to `0001_umbrella_schema.sql` altering `submit_self_reported_baseline` parameters.
   - Any change in Next.js Server Actions calling conventions.

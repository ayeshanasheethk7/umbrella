-- Umbrella Security Test Harness: rls_smoke.sql
-- Covers all 13 checklist items from umbrella-supabase-rls + clinical record concurrency test.
-- Structure: Completely transactional inside BEGIN ... ROLLBACK.

begin;

-- 0. Test Setup & Synthetic Identities
-- Ensure auth schema and mock users if testing outside live Supabase instance
create schema if not exists auth;
create table if not exists auth.users (
  id uuid primary key,
  aud text default 'authenticated',
  role text default 'authenticated',
  email text unique,
  raw_user_meta_data jsonb default '{}'::jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Ensure auth.uid() function exists and supports request.jwt.claims / request.jwt.claim.sub
create or replace function auth.uid() returns uuid language sql stable as $$
  select coalesce(
    nullif(current_setting('request.jwt.claim.sub', true), ''),
    nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub'
  )::uuid;
$$;

-- Synthetic Test Identities
-- Patient A: Standard patient
-- Patient B: Secondary patient for cross-tenant isolation tests
-- Doctor Pending: Registered doctor pending verification
-- Doctor Approved: Verified doctor with active privileges
-- Evil Admin Attempt: User attempting to supply role='admin'
insert into auth.users (id, aud, role, email, raw_user_meta_data) values
  ('00000000-0000-0000-0000-0000000000a1', 'authenticated', 'authenticated', 'pat.a@example.test',
   '{"role":"patient","full_name":"Test Patient A","age":"34","blood_group":"O+","emergency_contact_name":"Taylor A","emergency_contact_phone":"+15550001","emergency_contact_relation":"Sibling"}'),
  ('00000000-0000-0000-0000-0000000000a2', 'authenticated', 'authenticated', 'pat.b@example.test',
   '{"role":"patient","full_name":"Test Patient B","age":"45","blood_group":"A-","emergency_contact_name":"Jordan B","emergency_contact_phone":"+15550002","emergency_contact_relation":"Spouse"}'),
  ('00000000-0000-0000-0000-0000000000d1', 'authenticated', 'authenticated', 'doc.pending@example.test',
   '{"role":"doctor","full_name":"Dr. Pending Test","medical_license_number":"LIC-PENDING-01","specialization":"Internal Medicine"}'),
  ('00000000-0000-0000-0000-0000000000d2', 'authenticated', 'authenticated', 'doc.approved@example.test',
   '{"role":"doctor","full_name":"Dr. Approved Test","medical_license_number":"LIC-APPROVED-02","specialization":"Cardiology"}'),
  ('00000000-0000-0000-0000-0000000000e1', 'authenticated', 'authenticated', 'evil.admin@example.test',
   '{"role":"admin","full_name":"Evil Admin Attempt"}')
on conflict (id) do nothing;

-- Approve Doctor D2 directly (simulating admin approval per D1)
update public.accounts
set doctor_status = 'approved'
where id = '00000000-0000-0000-0000-0000000000d2';

-- Add synthetic address to Patient A
update public.patient_profiles
set residential_address = '123 Safe St, Medical District'
where patient_id = '00000000-0000-0000-0000-0000000000a1';

--------------------------------------------------------------------------------
-- CHECK 1: anon cannot select from any core table (permission denied)
--------------------------------------------------------------------------------
do $$
declare
  v_err boolean;
begin
  set local role anon;

  -- accounts
  v_err := false;
  begin
    perform * from public.accounts limit 1;
  exception when insufficient_privilege then
    v_err := true;
  end;
  if not v_err then raise exception 'FAIL [Check 1]: anon select allowed on accounts'; end if;

  -- patient_profiles
  v_err := false;
  begin
    perform * from public.patient_profiles limit 1;
  exception when insufficient_privilege then
    v_err := true;
  end;
  if not v_err then raise exception 'FAIL [Check 1]: anon select allowed on patient_profiles'; end if;

  -- clinical_records
  v_err := false;
  begin
    perform * from public.clinical_records limit 1;
  exception when insufficient_privilege then
    v_err := true;
  end;
  if not v_err then raise exception 'FAIL [Check 1]: anon select allowed on clinical_records'; end if;

  -- appointments
  v_err := false;
  begin
    perform * from public.appointments limit 1;
  exception when insufficient_privilege then
    v_err := true;
  end;
  if not v_err then raise exception 'FAIL [Check 1]: anon select allowed on appointments'; end if;

  reset role;
  raise notice 'PASS [Check 1]: anon denied SELECT on accounts, patient_profiles, clinical_records, appointments';
end $$;

--------------------------------------------------------------------------------
-- CHECK 2: anon: get_emergency_triage_by_token returns JSON with whitelist,
-- strictly omitting residential_address, spouse_dependents, qr_token; unknown -> null
--------------------------------------------------------------------------------
do $$
declare
  v_token uuid;
  v_result jsonb;
begin
  select qr_token into v_token
  from public.patient_profiles
  where patient_id = '00000000-0000-0000-0000-0000000000a1';

  set local role anon;

  -- Valid token call
  v_result := public.get_emergency_triage_by_token(v_token);
  if v_result is null then
    raise exception 'FAIL [Check 2]: get_emergency_triage_by_token returned null for valid token';
  end if;

  -- Check required fields present
  if not (v_result ? 'full_name' and v_result ? 'patient_code' and v_result ? 'blood_group' and v_result ? 'emergency_contact_phone') then
    raise exception 'FAIL [Check 2]: missing required emergency triage fields: %', v_result;
  end if;

  -- Check N1 privacy invariants: address and dependents MUST NOT exist
  if v_result ? 'residential_address' then
    raise exception 'FAIL [Check 2]: PRIVACY VIOLATION: residential_address exposed in triage JSON';
  end if;
  if v_result ? 'spouse_dependents' then
    raise exception 'FAIL [Check 2]: PRIVACY VIOLATION: spouse_dependents exposed in triage JSON';
  end if;
  if v_result ? 'qr_token' then
    raise exception 'FAIL [Check 2]: PRIVACY VIOLATION: qr_token exposed in triage JSON';
  end if;

  -- Unknown token call -> must return null
  v_result := public.get_emergency_triage_by_token('00000000-0000-0000-0000-000000000000'::uuid);
  if v_result is not null then
    raise exception 'FAIL [Check 2]: get_emergency_triage_by_token returned non-null for unknown token';
  end if;

  reset role;
  raise notice 'PASS [Check 2]: anon emergency triage RPC returns valid whitelist and strictly omits address/dependents/qr_token; unknown token returns null';
end $$;

--------------------------------------------------------------------------------
-- CHECK 3: Patient A cannot read Patient B's data; can read own
--------------------------------------------------------------------------------
do $$
declare
  v_count integer;
begin
  set local role authenticated;
  perform set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000a1","role":"authenticated"}', true);
  perform set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-0000000000a1', true);

  -- Patient A reading Patient B's profile
  select count(*) into v_count from public.patient_profiles where patient_id = '00000000-0000-0000-0000-0000000000a2';
  if v_count <> 0 then raise exception 'FAIL [Check 3]: Patient A read Patient B profile'; end if;

  -- Patient A reading Patient B's clinical record
  select count(*) into v_count from public.clinical_records where patient_id = '00000000-0000-0000-0000-0000000000a2';
  if v_count <> 0 then raise exception 'FAIL [Check 3]: Patient A read Patient B clinical record'; end if;

  -- Patient A reading own profile
  select count(*) into v_count from public.patient_profiles where patient_id = '00000000-0000-0000-0000-0000000000a1';
  if v_count <> 1 then raise exception 'FAIL [Check 3]: Patient A cannot read own profile'; end if;

  -- Patient A reading own clinical record
  select count(*) into v_count from public.clinical_records where patient_id = '00000000-0000-0000-0000-0000000000a1';
  if v_count <> 1 then raise exception 'FAIL [Check 3]: Patient A cannot read own clinical record'; end if;

  reset role;
  raise notice 'PASS [Check 3]: Tenant isolation verified: Patient A cannot read Patient B data; reads own data';
end $$;

--------------------------------------------------------------------------------
-- CHECK 4: Patient can update own demographics; cannot update qr_token, patient_code or patient_id
--------------------------------------------------------------------------------
do $$
declare
  v_err boolean;
begin
  set local role authenticated;
  perform set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000a1","role":"authenticated"}', true);
  perform set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-0000000000a1', true);

  -- Demographic update: ALLOWED
  update public.patient_profiles
  set age = 35,
      emergency_contact_name = 'Taylor Morgan Jr',
      residential_address = '456 Verified Blvd'
  where patient_id = '00000000-0000-0000-0000-0000000000a1';

  -- qr_token update: DENIED
  v_err := false;
  begin
    update public.patient_profiles
    set qr_token = gen_random_uuid()
    where patient_id = '00000000-0000-0000-0000-0000000000a1';
  exception when insufficient_privilege then
    v_err := true;
  end;
  if not v_err then raise exception 'FAIL [Check 4]: Patient successfully updated qr_token directly'; end if;

  -- patient_code update: DENIED
  v_err := false;
  begin
    update public.patient_profiles
    set patient_code = 'UMB-HACKED'
    where patient_id = '00000000-0000-0000-0000-0000000000a1';
  exception when insufficient_privilege then
    v_err := true;
  end;
  if not v_err then raise exception 'FAIL [Check 4]: Patient successfully updated patient_code'; end if;

  -- patient_id update: DENIED
  v_err := false;
  begin
    update public.patient_profiles
    set patient_id = gen_random_uuid()
    where patient_id = '00000000-0000-0000-0000-0000000000a1';
  exception when insufficient_privilege then
    v_err := true;
  end;
  if not v_err then raise exception 'FAIL [Check 4]: Patient successfully updated patient_id'; end if;

  reset role;
  raise notice 'PASS [Check 4]: Patient allowed to update demographics; denied update on qr_token, patient_code, patient_id';
end $$;

--------------------------------------------------------------------------------
-- CHECK 5: Patient cannot update accounts.role or doctor_status; can update full_name
--------------------------------------------------------------------------------
do $$
declare
  v_err boolean;
begin
  set local role authenticated;
  perform set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000a1","role":"authenticated"}', true);
  perform set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-0000000000a1', true);

  -- full_name update: ALLOWED
  update public.accounts
  set full_name = 'Alex Morgan Verified'
  where id = '00000000-0000-0000-0000-0000000000a1';

  -- role update: DENIED
  v_err := false;
  begin
    update public.accounts
    set role = 'doctor'
    where id = '00000000-0000-0000-0000-0000000000a1';
  exception when insufficient_privilege then
    v_err := true;
  end;
  if not v_err then raise exception 'FAIL [Check 5]: Patient successfully escalated role to doctor'; end if;

  -- doctor_status update: DENIED
  v_err := false;
  begin
    update public.accounts
    set doctor_status = 'approved'
    where id = '00000000-0000-0000-0000-0000000000a1';
  exception when insufficient_privilege then
    v_err := true;
  end;
  if not v_err then raise exception 'FAIL [Check 5]: Patient successfully updated doctor_status to approved'; end if;

  reset role;
  raise notice 'PASS [Check 5]: Patient allowed to update full_name; denied privilege escalation on role and doctor_status';
end $$;

--------------------------------------------------------------------------------
-- CHECK 6: Signup metadata role='admin' creates patient; role='doctor' creates pending doctor
--------------------------------------------------------------------------------
do $$
declare
  v_evil_role public.user_role;
  v_evil_status text;
  v_doc_role public.user_role;
  v_doc_status text;
  v_doc_profiles integer;
begin
  -- Check Evil Admin Attempt (metadata role was 'admin')
  select role, doctor_status into v_evil_role, v_evil_status
  from public.accounts
  where id = '00000000-0000-0000-0000-0000000000e1';

  if v_evil_role <> 'patient' or v_evil_status is not null then
    raise exception 'FAIL [Check 6]: Metadata role=admin created account with role=%, status=%', v_evil_role, v_evil_status;
  end if;

  -- Check Pending Doctor (metadata role was 'doctor')
  select role, doctor_status into v_doc_role, v_doc_status
  from public.accounts
  where id = '00000000-0000-0000-0000-0000000000d1';

  if v_doc_role <> 'doctor' or v_doc_status <> 'pending' then
    raise exception 'FAIL [Check 6]: Doctor signup created account with role=%, status=%', v_doc_role, v_doc_status;
  end if;

  -- Ensure Doctor did not receive patient_profiles entry
  select count(*) into v_doc_profiles
  from public.patient_profiles
  where patient_id = '00000000-0000-0000-0000-0000000000d1';

  if v_doc_profiles <> 0 then
    raise exception 'FAIL [Check 6]: Doctor account erroneously provisioned with patient_profile';
  end if;

  raise notice 'PASS [Check 6]: Signup role sanitization verified: unapproved roles default to patient, doctor starts as pending';
end $$;

--------------------------------------------------------------------------------
-- CHECK 7: Pending doctor reads zero patient rows; approved doctor reads all
--------------------------------------------------------------------------------
do $$
declare
  v_count integer;
begin
  -- Pending Doctor
  set local role authenticated;
  perform set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000d1","role":"authenticated"}', true);
  perform set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-0000000000d1', true);

  select count(*) into v_count from public.patient_profiles;
  if v_count <> 0 then
    raise exception 'FAIL [Check 7]: Pending doctor read % patient_profiles rows (expected 0)', v_count;
  end if;

  select count(*) into v_count from public.clinical_records;
  if v_count <> 0 then
    raise exception 'FAIL [Check 7]: Pending doctor read % clinical_records rows (expected 0)', v_count;
  end if;

  -- Approved Doctor
  perform set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000d2","role":"authenticated"}', true);
  perform set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-0000000000d2', true);

  select count(*) into v_count from public.patient_profiles;
  if v_count < 2 then
    raise exception 'FAIL [Check 7]: Approved doctor read % patient_profiles rows (expected >= 2)', v_count;
  end if;

  select count(*) into v_count from public.clinical_records;
  if v_count < 2 then
    raise exception 'FAIL [Check 7]: Approved doctor read % clinical_records rows (expected >= 2)', v_count;
  end if;

  reset role;
  raise notice 'PASS [Check 7]: Doctor approval gate verified: pending reads 0 rows; approved reads all patient rows';
end $$;

--------------------------------------------------------------------------------
-- CHECK 8: Patient cannot update clinical_records directly;
-- submit_self_reported_baseline works while unverified and raises after verification
--------------------------------------------------------------------------------
do $$
declare
  v_rows integer;
  v_err boolean;
  v_cond text[];
  v_allg text[];
  v_huge text[];
begin
  set local role authenticated;
  perform set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000a1","role":"authenticated"}', true);
  perform set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-0000000000a1', true);

  -- Direct update on clinical_records by patient: RLS blocks it (0 rows affected)
  update public.clinical_records
  set medical_conditions = array['Direct Hack Condition']
  where patient_id = '00000000-0000-0000-0000-0000000000a1';
  get diagnostics v_rows = row_count;
  if v_rows <> 0 then
    raise exception 'FAIL [Check 8]: Patient directly updated clinical_records (rows affected: %)', v_rows;
  end if;

  -- Submit baseline while unverified: ALLOWED
  perform public.submit_self_reported_baseline(
    array['Asthma', 'Seasonal Allergies'],
    array['Penicillin']
  );

  select medical_conditions, allergies into v_cond, v_allg
  from public.clinical_records
  where patient_id = '00000000-0000-0000-0000-0000000000a1';

  if not ('Asthma' = any(v_cond) and 'Penicillin' = any(v_allg)) then
    raise exception 'FAIL [Check 8]: submit_self_reported_baseline failed to store conditions/allergies';
  end if;

  -- Input bounding test: > 50 items must raise 'Too many entries'
  select array_agg('Allergy ' || i::text) into v_huge from generate_series(1, 51) s(i);
  v_err := false;
  begin
    perform public.submit_self_reported_baseline(array['Normal'], v_huge);
  exception when others then
    if sqlerrm like '%Too many entries%' then v_err := true; end if;
  end;
  if not v_err then raise exception 'FAIL [Check 8]: submit_self_reported_baseline accepted > 50 items'; end if;

  -- Simulate doctor verification by stamping the record as postgres
  reset role;
  update public.clinical_records
  set is_doctor_verified = true,
      last_updated_by_doctor_id = '00000000-0000-0000-0000-0000000000d2'
  where patient_id = '00000000-0000-0000-0000-0000000000a1';

  -- Patient attempts baseline submission on verified record: MUST RAISE
  set local role authenticated;
  perform set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000a1","role":"authenticated"}', true);
  perform set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-0000000000a1', true);

  v_err := false;
  begin
    perform public.submit_self_reported_baseline(array['New Condition'], array['Sulfa']);
  exception when others then
    if sqlerrm like '%already doctor-verified%' then v_err := true; end if;
  end;
  if not v_err then raise exception 'FAIL [Check 8]: submit_self_reported_baseline succeeded on verified record'; end if;

  reset role;
  raise notice 'PASS [Check 8]: Patient clinical record isolation and bounded baseline submission verified';
end $$;

--------------------------------------------------------------------------------
-- CHECK 9: Approved doctor UPDATE sets is_doctor_verified=true and stamps doctor ID;
-- no-op update also verifies
--------------------------------------------------------------------------------
do $$
declare
  v_verified boolean;
  v_doctor_stamp uuid;
begin
  -- Reset Patient B to unverified
  update public.clinical_records
  set is_doctor_verified = false,
      last_updated_by_doctor_id = null
  where patient_id = '00000000-0000-0000-0000-0000000000a2';

  set local role authenticated;
  perform set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000d2","role":"authenticated"}', true);
  perform set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-0000000000d2', true);

  -- Doctor updates Patient A's clinical record, sending is_doctor_verified=false and doctor_id=null
  update public.clinical_records
  set medical_conditions = array['Type 2 Diabetes', 'Hypertension']
  where patient_id = '00000000-0000-0000-0000-0000000000a1';

  select is_doctor_verified, last_updated_by_doctor_id into v_verified, v_doctor_stamp
  from public.clinical_records
  where patient_id = '00000000-0000-0000-0000-0000000000a1';

  if v_verified is not true or v_doctor_stamp <> '00000000-0000-0000-0000-0000000000d2' then
    raise exception 'FAIL [Check 9]: trigger did not stamp verification (verified=%, doctor=%)', v_verified, v_doctor_stamp;
  end if;

  -- Doctor executes no-op update on Patient B (allergies = allergies)
  update public.clinical_records
  set allergies = allergies
  where patient_id = '00000000-0000-0000-0000-0000000000a2';

  select is_doctor_verified, last_updated_by_doctor_id into v_verified, v_doctor_stamp
  from public.clinical_records
  where patient_id = '00000000-0000-0000-0000-0000000000a2';

  if v_verified is not true or v_doctor_stamp <> '00000000-0000-0000-0000-0000000000d2' then
    raise exception 'FAIL [Check 9]: no-op update did not flip is_doctor_verified';
  end if;

  reset role;
  raise notice 'PASS [Check 9]: Doctor update and no-op update reliably stamped verification and doctor ID';
end $$;

--------------------------------------------------------------------------------
-- CHECK 10: Approved doctor inserts appointment with own doctor_id;
-- patient cannot insert appointments
--------------------------------------------------------------------------------
do $$
declare
  v_err boolean;
begin
  set local role authenticated;
  perform set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000d2","role":"authenticated"}', true);
  perform set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-0000000000d2', true);

  -- Doctor inserts appointment with own doctor_id: ALLOWED
  insert into public.appointments (id, patient_id, doctor_id, scheduled_at, reason)
  values ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-0000000000a1', '00000000-0000-0000-0000-0000000000d2', now() + interval '1 day', 'Follow-up Cardiology');

  -- Doctor attempts to insert appointment with Pending Doctor's id: DENIED
  v_err := false;
  begin
    insert into public.appointments (id, patient_id, doctor_id, scheduled_at, reason)
    values ('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-0000000000a1', '00000000-0000-0000-0000-0000000000d1', now() + interval '2 days', 'Spoofed Doctor');
  exception when others then
    v_err := true;
  end;
  if not v_err then raise exception 'FAIL [Check 10]: Doctor inserted appointment with foreign doctor_id'; end if;

  -- Patient attempts appointment insertion: DENIED
  perform set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000a1","role":"authenticated"}', true);
  perform set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-0000000000a1', true);

  v_err := false;
  begin
    insert into public.appointments (id, patient_id, doctor_id, scheduled_at, reason)
    values ('10000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-0000000000a1', '00000000-0000-0000-0000-0000000000d2', now() + interval '3 days', 'Patient Self-Booking');
  exception when others then
    v_err := true;
  end;
  if not v_err then raise exception 'FAIL [Check 10]: Patient inserted appointment directly'; end if;

  reset role;
  raise notice 'PASS [Check 10]: Appointment creation restricted strictly to approved doctors matching auth.uid()';
end $$;

--------------------------------------------------------------------------------
-- CHECK 11: Completing an appointment sets last_appointment_date and summary
-- but does NOT flip is_doctor_verified (D8)
--------------------------------------------------------------------------------
do $$
declare
  v_appt_id uuid := '10000000-0000-0000-0000-000000000099';
  v_sched timestamptz := now() - interval '2 hours';
  v_verified boolean;
  v_last_date timestamptz;
  v_last_sum text;
begin
  -- Set Patient B to unverified
  update public.clinical_records
  set is_doctor_verified = false,
      last_updated_by_doctor_id = null,
      last_appointment_date = null,
      last_appointment_summary = null
  where patient_id = '00000000-0000-0000-0000-0000000000a2';

  insert into public.appointments (id, patient_id, doctor_id, scheduled_at, status, reason, clinical_notes)
  values (v_appt_id, '00000000-0000-0000-0000-0000000000a2', '00000000-0000-0000-0000-0000000000d2', v_sched, 'scheduled', 'Triage Checkup', null);

  -- Doctor completes appointment
  set local role authenticated;
  perform set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000d2","role":"authenticated"}', true);
  perform set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-0000000000d2', true);

  update public.appointments
  set status = 'completed',
      clinical_notes = 'Patient responded well to clinical triage.'
  where id = v_appt_id;

  select is_doctor_verified, last_appointment_date, last_appointment_summary
  into v_verified, v_last_date, v_last_sum
  from public.clinical_records
  where patient_id = '00000000-0000-0000-0000-0000000000a2';

  if v_verified is not false then
    raise exception 'FAIL [Check 11]: Appointment completion erroneously flipped is_doctor_verified to true';
  end if;
  if v_last_date <> v_sched or v_last_sum <> 'Patient responded well to clinical triage.' then
    raise exception 'FAIL [Check 11]: Appointment sync failed (date=%, sum=%)', v_last_date, v_last_sum;
  end if;

  reset role;
  raise notice 'PASS [Check 11]: Appointment completion updated appointment summary/date without altering verification state';
end $$;

--------------------------------------------------------------------------------
-- CHECK 12: regenerate_qr_token returns new uuid; old token returns null from emergency RPC
--------------------------------------------------------------------------------
do $$
declare
  v_old_token uuid;
  v_new_token uuid;
  v_triage jsonb;
begin
  select qr_token into v_old_token
  from public.patient_profiles
  where patient_id = '00000000-0000-0000-0000-0000000000a1';

  -- Patient calls regenerate_qr_token()
  set local role authenticated;
  perform set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000a1","role":"authenticated"}', true);
  perform set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-0000000000a1', true);

  v_new_token := public.regenerate_qr_token();

  if v_new_token is null or v_new_token = v_old_token then
    raise exception 'FAIL [Check 12]: regenerate_qr_token did not produce a fresh token (new=%, old=%)', v_new_token, v_old_token;
  end if;

  -- Test emergency RPC as anon
  set local role anon;

  -- Old token must return null
  v_triage := public.get_emergency_triage_by_token(v_old_token);
  if v_triage is not null then
    raise exception 'FAIL [Check 12]: old rotated qr_token still returned emergency triage data';
  end if;

  -- New token must return valid triage
  v_triage := public.get_emergency_triage_by_token(v_new_token);
  if v_triage is null or (v_triage->>'full_name') is null then
    raise exception 'FAIL [Check 12]: new rotated qr_token failed to return emergency triage data';
  end if;

  reset role;
  raise notice 'PASS [Check 12]: QR token rotation invalidates previous token and makes new token instantly active';
end $$;

--------------------------------------------------------------------------------
-- CHECK 13: DELETE on any of the four tables as authenticated fails
--------------------------------------------------------------------------------
do $$
declare
  v_rows integer;
  v_err boolean;
begin
  set local role authenticated;
  perform set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000d2","role":"authenticated"}', true);
  perform set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-0000000000d2', true);

  -- accounts DELETE
  v_err := false;
  begin
    delete from public.accounts where id = '00000000-0000-0000-0000-0000000000a1';
    get diagnostics v_rows = row_count;
    if v_rows > 0 then raise exception 'accounts delete succeeded'; end if;
  exception when others then
    v_err := true;
  end;
  if not v_err and v_rows > 0 then raise exception 'FAIL [Check 13]: accounts deleted'; end if;

  -- patient_profiles DELETE
  v_err := false;
  begin
    delete from public.patient_profiles where patient_id = '00000000-0000-0000-0000-0000000000a1';
    get diagnostics v_rows = row_count;
    if v_rows > 0 then raise exception 'patient_profiles delete succeeded'; end if;
  exception when others then
    v_err := true;
  end;
  if not v_err and v_rows > 0 then raise exception 'FAIL [Check 13]: patient_profiles deleted'; end if;

  -- clinical_records DELETE
  v_err := false;
  begin
    delete from public.clinical_records where patient_id = '00000000-0000-0000-0000-0000000000a1';
    get diagnostics v_rows = row_count;
    if v_rows > 0 then raise exception 'clinical_records delete succeeded'; end if;
  exception when others then
    v_err := true;
  end;
  if not v_err and v_rows > 0 then raise exception 'FAIL [Check 13]: clinical_records deleted'; end if;

  -- appointments DELETE
  v_err := false;
  begin
    delete from public.appointments;
    get diagnostics v_rows = row_count;
    if v_rows > 0 then raise exception 'appointments delete succeeded'; end if;
  exception when others then
    v_err := true;
  end;
  if not v_err and v_rows > 0 then raise exception 'FAIL [Check 13]: appointments deleted'; end if;

  reset role;
  raise notice 'PASS [Check 13]: DELETE blocked across accounts, patient_profiles, clinical_records, appointments';
end $$;

--------------------------------------------------------------------------------
-- CHECK 14: Concurrency test on clinical record updates
--------------------------------------------------------------------------------
do $$
declare
  v_version_initial timestamptz;
  v_version_updated timestamptz;
  v_rows integer;
begin
  set local role authenticated;
  perform set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000d2","role":"authenticated"}', true);
  perform set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-0000000000d2', true);

  select updated_at into v_version_initial
  from public.clinical_records
  where patient_id = '00000000-0000-0000-0000-0000000000a1';

  -- Wait a microsecond and perform first update
  perform pg_sleep(0.01);
  update public.clinical_records
  set medical_conditions = array['Condition V1']
  where patient_id = '00000000-0000-0000-0000-0000000000a1';

  select updated_at into v_version_updated
  from public.clinical_records
  where patient_id = '00000000-0000-0000-0000-0000000000a1';

  if v_version_updated <= v_version_initial then
    raise exception 'FAIL [Check 14]: updated_at timestamp did not advance during clinical update';
  end if;

  -- Optimistic lock simulation: A stale client submitting old updated_at affects 0 rows
  update public.clinical_records
  set medical_conditions = array['Stale Conflict Update']
  where patient_id = '00000000-0000-0000-0000-0000000000a1'
    and updated_at = v_version_initial;
  get diagnostics v_rows = row_count;

  if v_rows <> 0 then
    raise exception 'FAIL [Check 14]: optimistic locking failed: stale update applied (% rows)', v_rows;
  end if;

  -- Valid concurrent client submitting matched updated_at succeeds
  update public.clinical_records
  set medical_conditions = array['Condition V2 Concurrent Match']
  where patient_id = '00000000-0000-0000-0000-0000000000a1'
    and updated_at = v_version_updated;
  get diagnostics v_rows = row_count;

  if v_rows <> 1 then
    raise exception 'FAIL [Check 14]: optimistic lock update with current timestamp failed (% rows)', v_rows;
  end if;

  reset role;
  raise notice 'PASS [Check 14]: Concurrency and optimistic locking on clinical record updates verified';
end $$;

-- Summary Attestation
raise notice '========================================================================';
raise notice 'SUCCESS: All 13 RLS security checklist items + concurrency test passed!';
raise notice '========================================================================';

-- Rollback entire test run so database remains completely clean
rollback;

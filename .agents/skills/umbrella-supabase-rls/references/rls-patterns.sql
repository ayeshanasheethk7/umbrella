-- Reference patterns for supabase/migrations/0001_umbrella_schema.sql
-- SPEC section 4.2 plus DECISIONS D1-D9. Tables not shown here are exactly
-- as in SPEC 4.2 with the noted changes.

create extension if not exists "pgcrypto";
create type public.user_role as enum ('patient', 'doctor');

-- accounts (D1): doctors start as 'pending'; patients have doctor_status null
create table public.accounts (
  id uuid primary key references auth.users(id) on delete cascade,
  email text unique not null,
  role public.user_role not null default 'patient',
  full_name text not null,
  contact_phone text not null default '',
  medical_license_number text,
  specialization text,
  doctor_status text check (doctor_status in ('pending','approved','rejected')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint accounts_role_fields_chk check (
    (role = 'doctor' and doctor_status is not null and medical_license_number is not null)
    or (role = 'patient' and doctor_status is null)
  )
);

-- patient_profiles: as SPEC 4.2 BUT residential_address text not null default '' (D4)
-- clinical_records: as SPEC 4.2 (its row is auto-created by trigger below)
-- appointments: as SPEC 4.2 BUT doctor_id uuid not null references public.accounts(id) on delete restrict (D6)
create index on public.appointments (patient_id, scheduled_at desc);
create index on public.appointments (doctor_id);
create index on public.accounts (contact_phone);

-- helper: approved doctor? (SECURITY DEFINER avoids RLS recursion)
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

-- generic updated_at
create or replace function public.set_updated_at()
returns trigger language plpgsql set search_path = '' as $$
begin new.updated_at := now(); return new; end $$;
create trigger trg_accounts_updated before update on public.accounts
for each row execute function public.set_updated_at();
create trigger trg_patient_profiles_updated before update on public.patient_profiles
for each row execute function public.set_updated_at();

-- signup trigger (D2): reads metadata ONCE; unknown roles become 'patient'
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = '' as $$
declare
  meta jsonb := coalesce(new.raw_user_meta_data, '{}'::jsonb);
  v_role public.user_role := case when meta->>'role' = 'doctor'
    then 'doctor'::public.user_role else 'patient'::public.user_role end;
begin
  insert into public.accounts (id, email, role, full_name, contact_phone, medical_license_number, specialization, doctor_status)
  values (
    new.id,
    new.email,
    v_role,
    coalesce(nullif(meta->>'full_name',''), 'Unknown'),
    coalesce(meta->>'contact_phone', ''),
    case when v_role = 'doctor' then meta->>'medical_license_number' end,
    case when v_role = 'doctor' then meta->>'specialization' end,
    case when v_role = 'doctor' then 'pending' end
  );

  if v_role = 'patient' then
    insert into public.patient_profiles (patient_id, age, blood_group, emergency_contact_name, emergency_contact_phone, emergency_contact_relation)
    values (
      new.id,
      coalesce(nullif(meta->>'age','')::int, 0),
      case when meta->>'blood_group' in ('A+','A-','B+','B-','AB+','AB-','O+','O-')
        then meta->>'blood_group' else 'Unknown' end,
      coalesce(meta->>'emergency_contact_name', ''),
      coalesce(meta->>'emergency_contact_phone', ''),
      coalesce(meta->>'emergency_contact_relation', '')
    );
  end if;
  return new;
end $$;
revoke all on function public.handle_new_user() from public, anon, authenticated;
create trigger on_auth_user_created after insert on auth.users
for each row execute function public.handle_new_user();

-- every patient gets an empty clinical record (D7)
create or replace function public.create_clinical_record()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  insert into public.clinical_records (patient_id) values (new.patient_id) on conflict do nothing;
  return new;
end $$;
revoke all on function public.create_clinical_record() from public, anon, authenticated;
create trigger trg_patient_profile_clinical after insert on public.patient_profiles
for each row execute function public.create_clinical_record();

-- server-side verification stamp (D7): client values are ignored
create or replace function public.stamp_clinical_update()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  new.updated_at := now();
  if current_setting('umbrella.skip_stamp', true) is distinct from 'on'
    and public.is_approved_doctor() then
    new.is_doctor_verified := true;
    new.last_updated_by_doctor_id := (select auth.uid());
  end if;
  return new;
end $$;
revoke all on function public.stamp_clinical_update() from public, anon, authenticated;
create trigger trg_stamp_clinical before update on public.clinical_records
for each row execute function public.stamp_clinical_update();

-- completing an appointment fills last_appointment_* without verifying (D8)
create or replace function public.on_appointment_completed()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  if new.status = 'completed' and old.status is distinct from 'completed' then
    perform set_config('umbrella.skip_stamp', 'on', true);
    update public.clinical_records
    set last_appointment_date = new.scheduled_at,
        last_appointment_summary = coalesce(nullif(new.clinical_notes, ''), new.reason)
    where patient_id = new.patient_id
      and (last_appointment_date is null or last_appointment_date <= new.scheduled_at);
    perform set_config('umbrella.skip_stamp', 'off', true);
  end if;
  return new;
end $$;
revoke all on function public.on_appointment_completed() from public, anon, authenticated;
create trigger trg_appointment_completed after update on public.appointments
for each row execute function public.on_appointment_completed();

-- RLS
alter table public.accounts enable row level security;
alter table public.patient_profiles enable row level security;
alter table public.clinical_records enable row level security;
alter table public.appointments enable row level security;

create policy accounts_select_self on public.accounts for select to authenticated
  using (id = (select auth.uid()));
create policy accounts_select_patients_for_doctors on public.accounts for select to authenticated
  using (role = 'patient' and (select public.is_approved_doctor()));
create policy accounts_select_my_doctors on public.accounts for select to authenticated
  using (role = 'doctor' and exists (
    select 1 from public.appointments ap
    where ap.doctor_id = accounts.id and ap.patient_id = (select auth.uid())
  ));
create policy accounts_update_self on public.accounts for update to authenticated
  using (id = (select auth.uid())) with check (id = (select auth.uid()));

create policy pp_select on public.patient_profiles for select to authenticated
  using (patient_id = (select auth.uid()) or (select public.is_approved_doctor()));
create policy pp_update_self on public.patient_profiles for update to authenticated
  using (patient_id = (select auth.uid())) with check (patient_id = (select auth.uid()));
-- no INSERT policy: rows are created by handle_new_user

create policy cr_select on public.clinical_records for select to authenticated
  using (patient_id = (select auth.uid()) or (select public.is_approved_doctor()));
create policy cr_update_doctor on public.clinical_records for update to authenticated
  using ((select public.is_approved_doctor())) with check ((select public.is_approved_doctor()));

create policy ap_select on public.appointments for select to authenticated
  using (patient_id = (select auth.uid()) or (select public.is_approved_doctor()));
create policy ap_insert_doctor on public.appointments for insert to authenticated
  with check ((select public.is_approved_doctor()) and doctor_id = (select auth.uid()));
create policy ap_update_doctor on public.appointments for update to authenticated
  using ((select public.is_approved_doctor())) with check ((select public.is_approved_doctor()));

-- GRANTS (D3): start from zero, grant back only what policies need
revoke all on public.accounts, public.patient_profiles, public.clinical_records, public.appointments from anon;
revoke all on public.accounts, public.patient_profiles, public.clinical_records, public.appointments from authenticated;
grant select on public.accounts, public.patient_profiles, public.clinical_records, public.appointments to authenticated;
grant update (full_name, contact_phone, specialization) on public.accounts to authenticated;
grant update (age, blood_group, emergency_contact_name, emergency_contact_phone, emergency_contact_relation, spouse_dependents, residential_address)
  on public.patient_profiles to authenticated;
grant update (medical_conditions, current_medication, previous_surgeries, allergies)
  on public.clinical_records to authenticated;
grant insert on public.appointments to authenticated;
grant update (scheduled_at, status, reason, clinical_notes) on public.appointments to authenticated;

-- RPC 1: public emergency triage (SPEC 4.2, hardened). Never returns address, dependents or qr_token.
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

-- RPC 2: patient self-reported baseline (D7). Only while the record is NOT doctor-verified.
create or replace function public.submit_self_reported_baseline(p_conditions text[], p_allergies text[])
returns void language plpgsql security definer set search_path = '' as $$
begin
  if coalesce(array_length(p_conditions, 1), 0) > 50 or coalesce(array_length(p_allergies, 1), 0) > 50 then
    raise exception 'Too many entries';
  end if;
  update public.clinical_records
  set medical_conditions = coalesce(p_conditions, '{}'),
      allergies = coalesce(p_allergies, '{}')
  where patient_id = (select auth.uid()) and is_doctor_verified = false;
  if not found then
    raise exception 'Record is already doctor-verified, or no patient profile exists';
  end if;
end $$;
revoke all on function public.submit_self_reported_baseline(text[], text[]) from public, anon, authenticated;
grant execute on function public.submit_self_reported_baseline(text[], text[]) to authenticated;

-- RPC 3: rotate the QR token (D3). Affects only the caller's own row.
create or replace function public.regenerate_qr_token()
returns uuid language plpgsql security definer set search_path = '' as $$
declare v_token uuid := gen_random_uuid();
begin
  update public.patient_profiles set qr_token = v_token where patient_id = (select auth.uid());
  if not found then raise exception 'No patient profile for this user'; end if;
  return v_token;
end $$;
revoke all on function public.regenerate_qr_token() from public, anon, authenticated;
grant execute on function public.regenerate_qr_token() to authenticated;

-- TEST HARNESS PATTERN (supabase/tests/rls_smoke.sql): everything inside BEGIN ... ROLLBACK
-- begin;
-- insert into auth.users (id, aud, role, email, raw_user_meta_data) values
-- ('00000000-0000-0000-0000-0000000000a1','authenticated','authenticated','pat.a@example.test',
--  '{"role":"patient","full_name":"Test Patient A","age":"34","blood_group":"O+","emergency_contact_name":"Test Contact","emergency_contact_phone":"+910000000001","emergency_contact_relation":"Sibling"}'),
-- ('00000000-0000-0000-0000-0000000000d1','authenticated','authenticated','doc.d@example.test',
--  '{"role":"doctor","full_name":"Test Doctor","medical_license_number":"TEST-0001"}');
-- update public.accounts set doctor_status = 'approved' where id = '00000000-0000-0000-0000-0000000000d1';
-- set local role authenticated;
-- select set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000a1","role":"authenticated"}', true);
-- do $$ begin
--   begin update public.accounts set role = 'doctor' where id = (select auth.uid());
--   raise exception 'FAIL: role escalation allowed';
--   exception when insufficient_privilege then null; end;
-- end $$;
-- reset role;
-- rollback;
-- (If the auth.users insert complains about a missing column in your project, add that column.)

-- Umbrella Seed Data: seed.sql
-- Strictly synthetic medical and personal data per AGENTS.md (N9).
-- Provides:
-- 1 Approved Doctor (Dr. Sarah Jenkins) per DECISIONS D1
-- 1 Pending Doctor (Dr. Marcus Vance)
-- 3 Patients:
--   - Alex Morgan: Verified chronic history (Type 1 Diabetes, Asthma)
--   - Priya Sharma: Unverified self-reported baseline
--   - David Kim: Verified complex cardiac/renal history
-- Realistic Appointments: Completed past reviews and scheduled upcoming visits

-- Ensure pgcrypto is present for password hashing
create extension if not exists "pgcrypto";

-- Clean existing seed data if re-running
delete from auth.users where email in (
  'doctor.approved@example.test',
  'doctor.pending@example.test',
  'alex.morgan@example.test',
  'priya.sharma@example.test',
  'david.kim@example.test'
);

--------------------------------------------------------------------------------
-- 1. Insert Synthetic Users into auth.users (triggers handle_new_user)
--------------------------------------------------------------------------------
insert into auth.users (
  id,
  instance_id,
  aud,
  role,
  email,
  encrypted_password,
  email_confirmed_at,
  raw_app_meta_data,
  raw_user_meta_data,
  created_at,
  updated_at
) values
  -- Approved Doctor
  (
    'd0000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000000',
    'authenticated',
    'authenticated',
    'doctor.approved@example.test',
    crypt('Password123!', gen_salt('bf')),
    now(),
    '{"provider":"email","providers":["email"]}',
    '{"role":"doctor","full_name":"Dr. Sarah Jenkins","contact_phone":"+1-555-0199","medical_license_number":"MD-98234-X","specialization":"Emergency Medicine & Cardiology"}',
    now(),
    now()
  ),
  -- Pending Doctor
  (
    'd0000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000000',
    'authenticated',
    'authenticated',
    'doctor.pending@example.test',
    crypt('Password123!', gen_salt('bf')),
    now(),
    '{"provider":"email","providers":["email"]}',
    '{"role":"doctor","full_name":"Dr. Marcus Vance","contact_phone":"+1-555-0198","medical_license_number":"MD-44120-P","specialization":"Neurology"}',
    now(),
    now()
  ),
  -- Patient 1: Alex Morgan
  (
    'a0000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000000',
    'authenticated',
    'authenticated',
    'alex.morgan@example.test',
    crypt('Password123!', gen_salt('bf')),
    now(),
    '{"provider":"email","providers":["email"]}',
    '{"role":"patient","full_name":"Alex Morgan","contact_phone":"+1-555-0101","age":34,"blood_group":"O+","emergency_contact_name":"Taylor Morgan","emergency_contact_phone":"+1-555-0102","emergency_contact_relation":"Sibling"}',
    now(),
    now()
  ),
  -- Patient 2: Priya Sharma
  (
    'a0000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000000',
    'authenticated',
    'authenticated',
    'priya.sharma@example.test',
    crypt('Password123!', gen_salt('bf')),
    now(),
    '{"provider":"email","providers":["email"]}',
    '{"role":"patient","full_name":"Priya Sharma","contact_phone":"+1-555-0201","age":28,"blood_group":"B+","emergency_contact_name":"Rohit Sharma","emergency_contact_phone":"+1-555-0202","emergency_contact_relation":"Spouse"}',
    now(),
    now()
  ),
  -- Patient 3: David Kim
  (
    'a0000000-0000-0000-0000-000000000003',
    '00000000-0000-0000-0000-000000000000',
    'authenticated',
    'authenticated',
    'david.kim@example.test',
    crypt('Password123!', gen_salt('bf')),
    now(),
    '{"provider":"email","providers":["email"]}',
    '{"role":"patient","full_name":"David Kim","contact_phone":"+1-555-0301","age":62,"blood_group":"AB-","emergency_contact_name":"Sun-Hee Kim","emergency_contact_phone":"+1-555-0302","emergency_contact_relation":"Daughter"}',
    now(),
    now()
  );

--------------------------------------------------------------------------------
-- 2. Approve Doctor Sarah Jenkins (DECISIONS D1)
--------------------------------------------------------------------------------
update public.accounts
set doctor_status = 'approved'
where id = 'd0000000-0000-0000-0000-000000000001';

--------------------------------------------------------------------------------
-- 3. Enhance Patient Profiles with Deterministic QR Tokens & Addresses (D4)
--------------------------------------------------------------------------------
-- Alex Morgan
update public.patient_profiles
set patient_code = 'UMB-ALX001',
    qr_token = '11111111-1111-1111-1111-111111111111',
    residential_address = '742 Evergreen Terrace, Springfield',
    spouse_dependents = '[{"name":"Jamie Morgan","relation":"Spouse","age":33,"phone":"+1-555-0103"}]'::jsonb
where patient_id = 'a0000000-0000-0000-0000-000000000001';

-- Priya Sharma
update public.patient_profiles
set patient_code = 'UMB-PRY002',
    qr_token = '22222222-2222-2222-2222-222222222222',
    residential_address = '1204 Elmhurst Lane, Metroville',
    spouse_dependents = '[]'::jsonb
where patient_id = 'a0000000-0000-0000-0000-000000000002';

-- David Kim
update public.patient_profiles
set patient_code = 'UMB-DVK003',
    qr_token = '33333333-3333-3333-3333-333333333333',
    residential_address = '88 Pinecrest Boulevard, Riverdale',
    spouse_dependents = '[{"name":"Sun-Hee Kim","relation":"Daughter","age":32,"phone":"+1-555-0302"}]'::jsonb
where patient_id = 'a0000000-0000-0000-0000-000000000003';

--------------------------------------------------------------------------------
-- 4. Seed Clinical Records (Conditions, Medications, Allergies, Surgeries)
--------------------------------------------------------------------------------
-- Alex Morgan (Doctor Verified by Dr. Sarah Jenkins)
update public.clinical_records
set medical_conditions = array['Type 1 Diabetes Mellitus', 'Mild Asthma'],
    allergies = array['Penicillin', 'Peanuts'],
    current_medication = '[
      {
        "name": "Insulin Glargine",
        "dosage": "20 units",
        "frequency": "Daily at bedtime",
        "prescribed_by": "Dr. Sarah Jenkins"
      },
      {
        "name": "Albuterol Inhaler",
        "dosage": "90mcg",
        "frequency": "As needed for wheezing",
        "prescribed_by": "Dr. Sarah Jenkins"
      }
    ]'::jsonb,
    previous_surgeries = '[
      {
        "procedure": "Laparoscopic Appendectomy",
        "year": 2018,
        "notes": "Uncomplicated recovery"
      }
    ]'::jsonb,
    is_doctor_verified = true,
    last_updated_by_doctor_id = 'd0000000-0000-0000-0000-000000000001',
    last_appointment_date = '2026-10-15T14:30:00Z',
    last_appointment_summary = 'Annual endocrine and pulmonary evaluation. Blood glucose stable on current regimen.'
where patient_id = 'a0000000-0000-0000-0000-000000000001';

-- Priya Sharma (Unverified Self-Reported Baseline)
update public.clinical_records
set medical_conditions = array['Hypertension'],
    allergies = array['Sulfa drugs'],
    current_medication = '[]'::jsonb,
    previous_surgeries = '[]'::jsonb,
    is_doctor_verified = false,
    last_updated_by_doctor_id = null,
    last_appointment_date = null,
    last_appointment_summary = null
where patient_id = 'a0000000-0000-0000-0000-000000000002';

-- David Kim (Doctor Verified by Dr. Sarah Jenkins)
update public.clinical_records
set medical_conditions = array['Coronary Artery Disease', 'Atrial Fibrillation', 'Chronic Kidney Disease Stage 2'],
    allergies = array['Aspirin', 'Iodine Contrast', 'Latex'],
    current_medication = '[
      {
        "name": "Apixaban (Eliquis)",
        "dosage": "5mg",
        "frequency": "Twice daily",
        "prescribed_by": "Dr. Sarah Jenkins"
      },
      {
        "name": "Metoprolol Succinate",
        "dosage": "50mg",
        "frequency": "Once daily",
        "prescribed_by": "Dr. Sarah Jenkins"
      }
    ]'::jsonb,
    previous_surgeries = '[
      {
        "procedure": "Percutaneous Coronary Intervention (PCI)",
        "year": 2021,
        "notes": "Drug-eluting stent placed in LAD"
      }
    ]'::jsonb,
    is_doctor_verified = true,
    last_updated_by_doctor_id = 'd0000000-0000-0000-0000-000000000001',
    last_appointment_date = '2026-09-20T10:00:00Z',
    last_appointment_summary = 'Post-stent cardiology review. Normal rhythm maintained with current antiarrhythmic and anticoagulant therapy.'
where patient_id = 'a0000000-0000-0000-0000-000000000003';

--------------------------------------------------------------------------------
-- 5. Seed Appointments (Past Completed & Future Scheduled)
--------------------------------------------------------------------------------
insert into public.appointments (
  id,
  patient_id,
  doctor_id,
  scheduled_at,
  status,
  reason,
  clinical_notes
) values
  -- Alex Morgan past completed appointment
  (
    'b0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'd0000000-0000-0000-0000-000000000001',
    '2026-10-15T14:30:00Z',
    'completed',
    'Annual endocrine and pulmonary evaluation',
    'Annual endocrine and pulmonary evaluation. Blood glucose stable on current regimen.'
  ),
  -- Alex Morgan upcoming scheduled appointment
  (
    'b0000000-0000-0000-0000-000000000002',
    'a0000000-0000-0000-0000-000000000001',
    'd0000000-0000-0000-0000-000000000001',
    '2026-11-15T09:00:00Z',
    'scheduled',
    'Quarterly HbA1c review and inhaler technique check',
    null
  ),
  -- David Kim past completed appointment
  (
    'b0000000-0000-0000-0000-000000000003',
    'a0000000-0000-0000-0000-000000000003',
    'd0000000-0000-0000-0000-000000000001',
    '2026-09-20T10:00:00Z',
    'completed',
    'Post-stent 12-month follow-up',
    'Post-stent cardiology review. Normal rhythm maintained with current antiarrhythmic and anticoagulant therapy.'
  ),
  -- David Kim upcoming scheduled appointment
  (
    'b0000000-0000-0000-0000-000000000004',
    'a0000000-0000-0000-0000-000000000003',
    'd0000000-0000-0000-0000-000000000001',
    '2026-12-01T11:00:00Z',
    'scheduled',
    'Routine ECG and renal panel follow-up',
    null
  )
on conflict (id) do nothing;

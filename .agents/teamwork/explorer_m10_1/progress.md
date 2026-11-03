# Progress — explorer_m10_1

Last visited: 2026-11-02T17:36:30Z

## Status
Starting forensic investigation of Points 1 to 10 for M10.

## Plan
- [ ] Point 1: N1 - Public Zero-Login Isolation (`/emergency/[token]`, RPC `get_emergency_triage_by_token`, anon grants, address/dependents exclusion)
- [ ] Point 2: N2 - Persistent Safety Banner (`/portal/doctor`, Patient safety banner visibility during clinical edits)
- [ ] Point 3: N3 - Server Auth Identification (`getUser()` vs `getSession()`, role extraction from `accounts` vs JWT)
- [ ] Point 4: N4 - Secret Hygiene (`service_role` search across all files, repo hygiene)
- [ ] Point 5: N5 - Zero Mock Auth (`signInWithPassword` and `signUp` in `/login` and `/signup`)
- [ ] Point 6: Point 6 - RLS Table Coverage (all 4 tables: `accounts`, `patient_profiles`, `clinical_records`, `appointments`)
- [ ] Point 7: Point 7 - Column-Level Grants (`role`, `doctor_status`, `patient_code`, `qr_token` protections)
- [ ] Point 8: Point 8 - Doctor Onboarding Gate (`is_approved_doctor()` and pending doctor access)
- [ ] Point 9: Point 9 - Optimistic Concurrency & Audit Triggers (`clinical_records` locking, audit log triggers)
- [ ] Point 10: Point 10 - Injection Defense (search input escaping, PostgREST filter handling)
- [ ] Compile comprehensive `report.md`
- [ ] Compile `handoff.md` and notify parent via `send_message`

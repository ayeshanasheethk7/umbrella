## 2026-11-02T01:07:57Z
You are explorer_m7_2, the Emergency Data Flow & Privacy Isolation Explorer for Milestone M7 of the Umbrella Emergency Medical ID Platform.

Your working directory is: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m7_2

MANDATORY INPUTS:
1. Master user request: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md (READ THIS FIRST).
2. Project specification & architecture: c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md
3. Database Migration: c:\Users\DELL\ayesha_pro\medi_qr\supabase\migrations\0001_umbrella_schema.sql
4. TypeScript DB Types: c:\Users\DELL\ayesha_pro\medi_qr\src\lib\supabase\types.ts
5. Security Rules: c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\02-security-privacy.md
6. Decisions: c:\Users\DELL\ayesha_pro\medi_qr\docs\DECISIONS.md

YOUR MISSION & FOCUS:
Investigate and define the server data fetching, privacy isolation, and runtime validation for `/emergency/[token]`:
1. **NON-NEGOTIABLE N1 (Zero Exposure)**:
   - `/emergency/[token]` never requires login. It fetches data ONLY through the RPC `get_emergency_triage_by_token(lookup_token uuid)`.
   - `residential_address` and `spouse_dependents` must NEVER appear (not in the RPC output, not in the HTML, not in any JSON, not in client props).
   - Verify that the Server Component creates an anonymous Supabase client (`createClient` from `@supabase/ssr` or `@supabase/supabase-js`) using ONLY `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`. Zero `service_role` usage.
2. **Opaque 404 Rejection**:
   - Validate the `token` parameter in the route URL. If it is not a valid UUIDv4 or if `rpc('get_emergency_triage_by_token')` returns null or an error, call Next.js `notFound()`.
   - Design `not-found.tsx` to display a clean, generic "Emergency Record Not Found" message with zero hint of whether the token exists, is expired, or is malformed (Security Rule 4).
3. **Zod Validation Schema (`src/lib/schemas.ts`)**:
   - Define strict Zod schema `emergencyTriageSchema` matching the RPC return jsonb structure:
     `full_name`, `contact_phone`, `patient_code`, `age`, `blood_group`, `emergency_contact_name`, `emergency_contact_phone`, `emergency_contact_relation`, `medical_conditions` (array), `current_medication` (array/json), `previous_surgeries` (array/json), `allergies` (array), `last_appointment_date`, `is_doctor_verified`, `updated_at`.
   - Ensure the schema strictly strips or disallows `residential_address` and `spouse_dependents`.
4. **Strict TypeScript Types (Invariant N10)**:
   - Define exact interface `EmergencyTriageData` derived from `z.infer<typeof emergencyTriageSchema>`.
   - Zero `any`, zero `@ts-ignore`.
5. **Character Limit Headroom**:
   - All proposed code files must stay strictly under 12,000 characters.

DELIVERABLE:
Write your comprehensive investigation report to:
`c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m7_2\report.md`
Follow the Handoff Protocol (Observation, Logic Chain, Caveats, Conclusion, Verification Method).
When done, send a message to parent with your summary and report path.

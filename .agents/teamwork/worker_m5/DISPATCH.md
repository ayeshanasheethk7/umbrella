## 2026-11-01T20:56:47Z
You are Worker M5 (teamwork_worker).
Your working directory is: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m5
Your parent is Teamwork Orchestrator (conversation ID: 35ce3df7-e3d0-4998-8e4c-525735196d55).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY FIRST STEP:
Read c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md.
Also read all 3 Explorer handoff reports:
- c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m5_1\handoff.md (UI & Bento layout)
- c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m5_2\handoff.md (Data flow & Server Actions)
- c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m5_3\handoff.md (Security boundaries & D3 disappearing edit UI)

YOUR TASK:
Implement Milestone M5: Patient Portal Surface (`/portal/patient`):

1. Server Actions (`src/app/portal/patient/actions.ts`):
   - Authenticate caller strictly using `supabase.auth.getUser()`.
   - `updateDemographicsAction(formData)`: Validate with Zod `updateDemographicsSchema`. Update `accounts(full_name, contact_phone)` and `patient_profiles(age, blood_group, emergency_contact_name, emergency_contact_phone, emergency_contact_relation, spouse_dependents, residential_address)`. Call `revalidatePath('/portal/patient')`. Return `{ ok: true, data } | { ok: false, error, fieldErrors }`.
   - `submitBaselineAction(formData)`: Validate with Zod `baselineSubmissionSchema`. Call Postgres RPC `submit_self_reported_baseline({ p_conditions, p_allergies })`. Handle doctor-verified lockout cleanly with user-friendly error message. Call `revalidatePath('/portal/patient')`.
   - `rotateQrTokenAction()`: Call Postgres RPC `regenerate_qr_token()`. Call `revalidatePath('/portal/patient')`. Return new token.

2. Patient Portal Components (`src/components/patient/`):
   - `hero-profile-card.tsx`: Patient name, copyable `patient_code` with click-to-copy clipboard feedback, `BloodGroupPill`, age (`{age} yrs`).
   - `emergency-qr-card.tsx`: Live `QRCodeSVG` (160px min), client-computed URL `window.location.origin + '/emergency/' + qr_token`, D12 non-blocking origin warning for non-prod, "Open Triage Page" link, and "Rotate QR Token" button with confirmation dialog.
   - `emergency-contact-card.tsx`: Emergency contact name, relation, and verified phone number with clickable `tel:` link (`min-h-[44px]`).
   - `demographics-card.tsx`: Form to update contact phone, age, blood group, residential address, and spouse/dependents (max 10 entries). Prominent privacy badge: "Private: Excluded from emergency QR triage scan (N1)".
   - `medical-overview-card.tsx`: Displays conditions, allergies (`AllergyAlert`), medications, and surgeries. When `is_doctor_verified === true`, displays green "Doctor Verified" badge and attribution banner: `"Verified by Dr. <name> on <date>. Contact your doctor to update."` (with fallback to `"Verified by Attending Clinician"`).
   - `baseline-editor.tsx`: When `is_doctor_verified === false`, renders amber "Self-Reported Baseline" badge, chip inputs for adding/removing conditions and allergies, and "Save Baseline" button calling `submitBaselineAction`. MUST completely disappear from DOM when `is_doctor_verified === true` (DECISIONS D3 & D7).

3. Main Portal Page (`src/app/portal/patient/page.tsx`):
   - Server Component with `await supabase.auth.getUser()`.
   - If user not authenticated, redirect to `/login?next=/portal/patient`.
   - Verify role in `accounts`; if doctor, redirect to `/portal/doctor`.
   - Parallel fetch (`Promise.all`) of `accounts`, `patient_profiles`, `clinical_records`, and verifying doctor account name.
   - Assemble compact Bento grid layout:
     - 24px padding, 16px gap.
     - Mobile: Single column stack at 375x667.
     - Desktop: 12-column responsive Bento grid at 1280x800.
     - Cards use `rounded-[18px]`, `border-border-hairline`, zero arbitrary raw hex.
     - All interactive controls enforce `>= 44px` touch targets.

4. Schemas & Types (`src/lib/schemas.ts`):
   - Add `updateDemographicsSchema` and ensure `baselineSubmissionSchema` matches `{ conditions, allergies }`.

5. Automated Verification Harness (`scripts/verify_m5.py`):
   - Authored in `scripts/verify_m5.py`.
   - Verify all M5 server actions, schemas, component imports, responsive layout invariants, D3 disappearing baseline contract, and N1 privacy protections.

6. Testing & Compliance:
   - Run `python scripts/verify_m5.py`.
   - Run `python scripts/audit.py` (ensure all files < 12,000 characters).
   - Run `powershell.exe -File scripts/forensic_suite.ps1`.
   - Zero scripts in `.agents/teamwork/`.

7. Deliverables:
   - Full implementation report: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m5\report.md`
   - Self-contained 5-component handoff: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m5\handoff.md`
   - Send completion message to parent orchestrator (`35ce3df7-e3d0-4998-8e4c-525735196d55`).

# Handoff Report — Explorer M5-1 (Patient Portal UI Architecture)

## 1. Observation
- `src/app/globals.css`:
  - Lines 5-26 define design tokens: `--bg-canvas: #f5f5f7;`, `--bg-surface: #ffffff;`, `--border-hairline: 1px solid rgba(0, 0, 0, 0.1);`, `--accent-action: #0071e3;`, `--clinical-critical: #ff3b30;`, `--clinical-critical-text: #d70015;`, `--clinical-verified: #34c759;`, `--clinical-verified-text: #1d7a37;`, `--clinical-pending: #ff9f0a;`, `--clinical-pending-text: #8a5200;`.
- `.agents/rules/01-design-system.md`:
  - Lines 30-36: Route `/portal/*` requires `24px page padding, 16px gaps`, layout `Compact bento`.
  - Lines 38-40: "Cards: bg-surface, radius 18-20px, hairline border. Light surfaces use rgba(0,0,0,0.1). ONLY dark surfaces use the white hairline. Never a white hairline on a white card. Shadow ceiling: 0 1px 2px rgba(0,0,0,.04), 0 8px 24px rgba(0,0,0,.06)."
  - Lines 42-48: "appleSpring = { type: 'spring', stiffness: 120, damping: 20, mass: 1 }", "Buttons: whileHover {scale:1.015}, whileTap {scale:0.98}."
  - Lines 53-57: "Button: primary filled --accent-action, secondary hairline, destructive. Min height 44px... Input: 16px font... Badges: always text + icon... Blood group: large pill. Allergies: --clinical-critical alert box."
- `docs/DECISIONS.md`:
  - D3: "Column protection. Authenticated users cannot update accounts.role/doctor_status/email or patient_profiles.patient_code/qr_token... qr_token changes only through rpc regenerate_qr_token."
  - D4: "`residential_address` is `text not null default ''` because the signup form (SPEC 6.2) does not collect it."
  - D7: "Self-reported baseline... rpc submit_self_reported_baseline (conditions and allergies only, only while is_doctor_verified=false)... Verification stamps... set by a BEFORE UPDATE trigger... doctor can verify unchanged self-reported data by saving it."
  - D10: "Contrast. #86868b on white fails WCAG AA for small text... Use #6e6e73 for text under 18px; --clinical-critical-text #d70015 for small red text; red fills carry large bold white text (20px+). Green text #1d7a37 and amber text #8a5200 are the text variants for verified and self-reported badges."
  - D12: "QR origin is window.location.origin (SPEC check 5), plus the non-blocking warning described in skill umbrella-qr-card."
- `supabase/migrations/0001_umbrella_schema.sql`:
  - Lines 35-48: Table `patient_profiles` contains `patient_id`, `patient_code`, `qr_token`, `age`, `blood_group`, `emergency_contact_name`, `emergency_contact_phone`, `emergency_contact_relation`, `spouse_dependents`, `residential_address`.
  - Lines 52-64: Table `clinical_records` contains `patient_id`, `medical_conditions`, `current_medication`, `previous_surgeries`, `allergies`, `is_doctor_verified`, `last_updated_by_doctor_id`, `last_appointment_date`, `last_appointment_summary`.
  - Lines 307-315: Authenticated users have column UPDATE grants on `accounts (full_name, contact_phone)`, `patient_profiles (age, blood_group, emergency_contact_name, emergency_contact_phone, emergency_contact_relation, spouse_dependents, residential_address)`.
  - Lines 352-371: RPC `submit_self_reported_baseline(p_conditions, p_allergies)` raises exception if `is_doctor_verified` is true.
  - Lines 373-392: RPC `regenerate_qr_token()` updates `qr_token` to fresh UUID and returns it.
- `src/components/ui/`:
  - `card.tsx` provides `Card` with `rounded-[18px]` and `CardHeader`, `CardTitle`, `CardContent`, `CardFooter`.
  - `badge.tsx` provides `Badge` (variants `verified`, `pending`, `critical`, `neutral`), `BloodGroupPill`, and `AllergyAlert`.
  - `button.tsx` provides `Button` with min-height 44px (emergency size 56px), `whileHover`/`whileTap` springs.
  - `modal.tsx` provides accessible modal dialog with keyboard trap and `modalDialogVariants`.

## 2. Logic Chain
1. From `01-design-system.md` (lines 30-40) and `src/components/ui/card.tsx`, the Patient Portal must be organized as a compact Bento grid with 24px padding, 16px gap, and cards styled with `rounded-[18px]` to `rounded-[20px]`, `border border-black/10`, and Apple shadow ceilings.
2. From the dual-viewport requirement (375x667 mobile and 1280x800 desktop), a responsive Tailwind grid `grid-cols-1 lg:grid-cols-12 gap-4` satisfies both single-column vertical stacking on mobile and an 8/4, 4/8, 6/6 multi-column Bento hierarchy on desktop.
3. From `docs/DECISIONS.md` D12 and skill `umbrella-qr-card`, rendering `QRCodeSVG` with client-side computation of `origin + '/emergency/' + qr_token` post-mount in `useEffect` prevents Next.js SSR hydration mismatches, while an amber warning alerts users on non-production origins.
4. From Invariant N1 and `docs/DECISIONS.md` D4, residential address and family dependents must be explicitly protected: in the portal UI, they are marked with privacy indicator badges to assure users that they are excluded from public roadside emergency scans.
5. From `docs/DECISIONS.md` D7 and `supabase/migrations/0001_umbrella_schema.sql` (lines 352-371), clinical data is split between self-reported baselines and doctor-verified records:
   - When `is_doctor_verified === false`, the UI renders a pending badge and enables the `BaselineEditorModal` for patient submission via RPC `submit_self_reported_baseline`.
   - When `is_doctor_verified === true`, baseline editing is locked and replaced with a doctor-verified audit badge, redirecting clinical modifications to verified healthcare appointments.
6. From `src/lib/motion.ts` and `RootLayout`, all interactive controls adhere to `appleSpring` physics and honor `prefers-reduced-motion: user`.

## 3. Caveats
- The printable CR80 card generation (`src/lib/pdf.ts`) and offscreen PNG export are architected as client-side triggers using `jspdf` and canvas; their full implementation will be executed in Milestone M8 / worker implementation.
- Browser `navigator.clipboard.writeText` requires HTTPS or `localhost` to succeed; a fallback textarea selection mechanism should be included for older browsers or restricted iframe environments.
- Real-time updates via Supabase Realtime subscriptions (e.g. for instantaneous reflection when a doctor approves/verifies) are not part of v1 core requirements (SPEC v1 uses standard Next.js Server Action revalidation).

## 4. Conclusion
The UI architecture for the Patient Portal (`/portal/patient`) is comprehensively specified in `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m5_1\report.md`. It provides:
- Complete Bento grid specifications for desktop (1280x800, 12-col layout) and mobile (375x667, single-col stack).
- Detailed component breakdowns for `HeroProfileCard`, `EmergencyQrCard`, `EmergencyContactCard`, `MedicalBaselineCard`, `DemographicsCard`, `DependentsCard`, `QrRotationModal`, and `BaselineEditorModal`.
- Full alignment with Apple design tokens, WCAG 2.1 AA accessibility standards, 44px minimum touch targets, and `appleSpring` physics.
- Precise integration with Supabase RPCs (`submit_self_reported_baseline`, `regenerate_qr_token`) and column-level update security policies.

## 5. Verification Method
1. Inspect report file:
   `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m5_1\report.md`
2. Validate design tokens and types:
   - Run typecheck: `npm run typecheck`
   - Run linter: `npm run lint`
3. Invalidation Conditions:
   - Any modification introducing white hairlines on white cards.
   - Any layout introducing horizontal overflow on 375px width.
   - Any omission of the amber origin warning on localhost/preview deployments.
   - Permitting direct baseline edits when `is_doctor_verified === true`.

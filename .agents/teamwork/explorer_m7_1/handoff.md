# Milestone M7 Handoff Report: Emergency Route UX & Performance

**Agent**: explorer_m7_1 (Emergency Route UX & Performance Explorer)  
**Workspace**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m7_1`  
**Milestone**: M7 (Public Zero-Login Emergency Triage Route `/emergency/[token]`)  
**Parent / Recipient**: Teamwork Orchestrator (`a0698e01-4167-4648-9a8b-05be5311997c`)  
**Detailed Report**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m7_1\report.md`

---

## 1. Observation

1. **Zero Animation Invariant & Button Trap**:
   - `docs/DECISIONS.md:31-32` (D13) & `AGENTS.md:36` (N8): `/emergency/[token]` must ship zero `framer-motion`, zero `qrcode.react`, zero `jspdf`. Pure CSS `:active scale 0.98` only.
   - `src/components/ui/button.tsx:1-4`: Imports `motion` from `framer-motion`. `/emergency/[token]` MUST NOT import `Button` from `@/components/ui/button`.
2. **56px Emergency Call Target**:
   - `AGENTS.md:50` (§6): Minimum 56px touch target for emergency call action.
   - `.agents/rules/02-security-privacy.md:27` (§6): `tel:` protocol must strip punctuation to digits and leading `+`.
   - `src/lib/utils.ts:68-75`: `sanitizeTel()` is already implemented and verified.
3. **Card Hierarchy & Layout**:
   - `.agents/rules/01-design-system.md:58-60`: Above the fold on 375x667: banner, verification badge, name and age, blood group pill, allergies alert, sticky 56px call bar.
   - `src/components/ui/badge.tsx:60-88`: `BloodGroupPill` is pure CSS and ready for use.
   - `src/components/ui/badge.tsx:95-131`: `AllergyAlert` is pure CSS and ready for use.
4. **Doctor Escalation (DECISIONS D15)**:
   - `src/app/portal/doctor/page.tsx:64-77`: `searchParams.patient_token` already resolves `qr_token` to `patient_id` and pre-loads `initialPatient`.

---

## 2. Logic Chain

1. **Bundle Isolation**: In high-acuity roadside emergencies with degraded cellular connectivity, client JavaScript must be minimal (<120KB gzipped). Eliminating `framer-motion` imports preserves performance and avoids runtime crashes.
2. **Ergonomic Safety**: A single-thumb sticky bottom bar at `min-h-[56px] min-w-[56px]` with `active:scale-[0.98]` allows immediate, failsafe dialing of primary emergency contacts.
3. **Above-the-Fold Triage**: Laying out Critical Allergy Banner, Patient Name/Code, Age, Verification Badge, BloodGroupPill, and Emergency Contact at 375x667 provides first responders with all life-critical information in under 2 seconds without initial scrolling.
4. **Physician Escalation**: Providing `/portal/doctor?patient_token=<uuid>` in the footer fulfills DECISIONS D15, enabling seamless handover from first responders to emergency room doctors.
5. **Headroom Compliance**: Modularizing into 5 files keeps every file under 8,000 characters (limit: 12,000).

---

## 3. Caveats

1. `src/app/layout.tsx` wraps children in `<MotionConfig>`. Emergency route components should be pure Server Components to prevent pulling layout motion hooks into the page bundle.
2. Profiles without an emergency contact phone must gracefully suppress the sticky call button while displaying a clear notice in the contact card.
3. All dates must be formatted with `Intl.DateTimeFormat` with consistent locale fallback.

---

## 4. Conclusion

The technical architecture and UI specifications for the public zero-login emergency triage page at `/emergency/[token]` are fully established:
- Pure CSS transitions and Server Component design guarantee zero framer-motion.
- A 56px sticky bottom call bar ensures thumb-reachable, sanitized dialing.
- High-contrast, card-based layout guarantees above-the-fold visibility at 375x667 and responsive bento scanning at 1280x800.
- Clean 5-file architecture adheres strictly to all project constraints and character limits.

---

## 5. Verification Method

1. **Framer-Motion Isolation Check**:
   `Get-ChildItem -Path src/app/emergency, src/components/emergency -Recurse -Filter "*.tsx" | Select-String "framer-motion"` (must return 0 results).
2. **Touch Target Inspection**:
   Inspect `EmergencyCallBar` for `min-h-[56px]` and `min-w-[56px]`.
3. **Privacy Hygiene Check**:
   `Get-ChildItem -Path src/app/emergency, src/components/emergency -Recurse -Filter "*.tsx" | Select-String "residential_address|spouse_dependents"` (must return 0 results).
4. **Character Count Verification**:
   Run `powershell.exe -File scripts/verify_chars.ps1` to confirm all files <12,000 characters.

# Milestone M7 Technical Investigation Report: Emergency Route UX & Performance

**Explorer**: explorer_m7_1 (Emergency Route UX & Performance Explorer)  
**Workspace**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m7_1`  
**Milestone**: M7 (Public Zero-Login Emergency Triage Route `/emergency/[token]`)  
**Target Recipient**: Orchestrator (`a0698e01-4167-4648-9a8b-05be5311997c`)

---

## 1. Observation

1. **Zero Animation Invariant & Button Trap**:
   - `docs/DECISIONS.md:31-32` (D13) & `AGENTS.md:36` (N8): `/emergency/[token]` must ship zero `framer-motion`, zero `qrcode.react`, zero `jspdf`. Pure CSS `:active scale 0.98` only.
   - `src/components/ui/button.tsx:1-4`: Imports `motion` from `framer-motion`. `/emergency/[token]` MUST NOT import `Button` from `@/components/ui/button` to avoid bundle pollution.
2. **56px Emergency Call Target & Sanitization**:
   - `AGENTS.md:50` (§6): Minimum 56px touch target for emergency call action (`min-h-[56px] min-w-[56px]`).
   - `.agents/rules/02-security-privacy.md:27` (§6): `tel:` links must strip punctuation to digits and leading `+`.
   - `src/lib/utils.ts:68-75`: `sanitizeTel(phone)` is already implemented and verified.
3. **Card Hierarchy & Layout**:
   - `.agents/rules/01-design-system.md:58-60`: Order above the fold: banner, verification badge, name and age, blood group pill, allergies alert, sticky 56px call bar.
   - `src/components/ui/badge.tsx:60-131`: `BloodGroupPill` and `AllergyAlert` are pure CSS and ready for use.
   - `src/components/ui/card.tsx:8-84`: `Card` primitives are pure CSS and zero-motion.
4. **Doctor Escalation (DECISIONS D15)**:
   - `src/app/portal/doctor/page.tsx:64-77`: `searchParams.patient_token` already resolves `qr_token` to `patient_id` and pre-loads `initialPatient`.

---

## 2. Logic Chain

1. **Performance & Bundle Isolation (D13)**: In roadside emergencies under degraded mobile networks, eliminating `framer-motion` (~35KB gzipped) and external animation libraries protects TTFB (<300ms) and LCP (<2.0s). The route must be a Server Component with pure CSS `:active:scale-[0.98]`.
2. **Ergonomic Safety**: A single-thumb sticky bottom bar at `min-h-[56px] min-w-[56px]` with `active:scale-[0.98]` allows immediate, failsafe dialing of primary emergency contacts via RFC 3966 `tel:` links.
3. **Above-the-Fold Triage**: Laying out Critical Allergy Banner, Patient Name/Code, Age, Verification Badge, BloodGroupPill, and Emergency Contact on 375x667 screens delivers all life-critical information in under 2 seconds without scrolling.
4. **Physician Escalation**: Providing `/portal/doctor?patient_token=<uuid>` fulfills DECISIONS D15, enabling seamless handover from first responders to emergency room doctors.
5. **Headroom Compliance**: Decomposing implementation into 5 files guarantees each file remains under 8,000 characters (<12,000 character limit).

---

## 3. Recommended Implementation Architecture

### A. Modular File Blueprint
```text
src/
├── app/
│   └── emergency/
│       └── [token]/
│           ├── page.tsx               # Server Component: RPC query, UUID check, notFound (~3.5k chars)
│           └── not-found.tsx          # Opaque generic 404 UI (~2.2k chars)
├── components/
│   └── emergency/
│       ├── emergency-triage-view.tsx  # Layout container & patient header (~5.5k chars)
│       ├── emergency-call-bar.tsx     # Sticky 56px call bar & contact card (~3.8k chars)
│       └── medical-overview-cards.tsx # Allergies, conditions, medications, surgeries (~6.2k chars)
└── lib/
    └── supabase/
        └── anon.ts                    # Cookie-less anonymous Supabase client (~1.2k chars)
```

### B. Core Component Specifications

#### 1. Cookie-less Supabase Client (`src/lib/supabase/anon.ts`)
```ts
import { createClient as createSupabaseClient } from '@supabase/supabase-js';
import type { Database } from './types';

export function createAnonClient() {
  return createSupabaseClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL || '',
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '',
    { auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false } }
  );
}
```

#### 2. Sticky 56px Call Bar (`src/components/emergency/emergency-call-bar.tsx`)
```tsx
import React from 'react';
import { Phone } from 'lucide-react';
import { sanitizeTel } from '@/lib/utils';

export const EmergencyCallBar: React.FC<{
  contactName: string;
  contactPhone: string;
  contactRelation: string;
}> = ({ contactName, contactPhone, contactRelation }) => {
  const sanitized = sanitizeTel(contactPhone);
  if (!sanitized) return null;

  return (
    <aside
      aria-label="Emergency call action"
      className="fixed bottom-0 left-0 right-0 z-50 p-4 bg-surface/95 backdrop-blur-md border-t border-black/10 pb-[max(1rem,env(safe-area-inset-bottom))] shadow-ceiling"
    >
      <div className="max-w-xl mx-auto">
        <a
          href={`tel:${sanitized}`}
          className="flex items-center justify-center gap-3 w-full min-h-[56px] min-w-[56px] px-6 py-3.5 rounded-2xl bg-clinical-critical text-white font-extrabold text-lg sm:text-xl shadow-md hover:bg-clinical-critical-hover active:bg-clinical-critical-active active:scale-[0.98] transition-all duration-100 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-clinical-critical/30 select-none"
          aria-label={`Call emergency contact ${contactName} (${contactRelation}) at ${contactPhone}`}
        >
          <Phone className="h-6 w-6 shrink-0" aria-hidden="true" />
          <span className="truncate">
            CALL {contactRelation ? contactRelation.toUpperCase() : 'CONTACT'}: {contactName}
          </span>
        </a>
      </div>
    </aside>
  );
};
```

#### 3. Escalation CTA Specification (DECISIONS D15)
```tsx
<div className="mt-8 pt-6 border-t border-black/10">
  <div className="rounded-card bg-surface border border-black/10 p-5 shadow-xs">
    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-text-body-secondary mb-2">
      <Stethoscope className="h-4 w-4 text-accent-action" aria-hidden="true" />
      <span>Healthcare Provider Verification</span>
    </div>
    <p className="text-xs text-text-body-secondary mb-4 leading-relaxed">
      Licensed healthcare personnel with active Umbrella credentials can access the complete clinical workspace.
    </p>
    <a
      href={`/portal/doctor?patient_token=${token}`}
      className="flex items-center justify-center gap-2.5 w-full min-h-[48px] px-5 py-3 rounded-xl bg-surface border border-black/15 hover:bg-black/5 active:scale-[0.98] text-sm font-bold text-text-primary shadow-xs transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action"
    >
      <Stethoscope className="h-4 w-4 text-accent-action" aria-hidden="true" />
      <span>Physician Portal Access</span>
    </a>
  </div>
</div>
```

---

## 4. Caveats

1. `src/app/layout.tsx` wraps `<main>` in `<MotionConfig reducedMotion="user">`. To preserve zero client motion bundle, emergency components must remain Server Components.
2. Profiles without registered phone numbers must gracefully suppress the sticky call button while displaying an explanatory note in the contact card.
3. Attestation dates must be formatted via `Intl.DateTimeFormat` with standardized locale fallback.

---

## 5. Conclusion

- Zero Framer-Motion (D13) is enforced by pure CSS transitions and Server Components.
- 56px sticky emergency call button guarantees one-thumb accessibility and sanitized dialing.
- High-contrast card triage layout places all critical indicators above the fold on 375x667.
- Doctor escalation directly routes to `/portal/doctor?patient_token=<uuid>`.
- 5-file modular design keeps all proposed files well under 8,000 characters.

---

## 6. Verification Method

1. **Framer-Motion Check**:
   `Get-ChildItem -Path src/app/emergency, src/components/emergency -Recurse -Filter "*.tsx" | Select-String "framer-motion"` (must return 0).
2. **Touch Target Inspection**:
   Inspect `EmergencyCallBar` for `min-h-[56px]`, `min-w-[56px]`, and `tel:${sanitizeTel()}`.
3. **Privacy Invariant N1**:
   `Get-ChildItem -Path src/app/emergency, src/components/emergency -Recurse -Filter "*.tsx" | Select-String "residential_address|spouse_dependents"` (must return 0).
4. **Character Count Verification**:
   `powershell.exe -File scripts/verify_chars.ps1` (all targets <12,000 chars).

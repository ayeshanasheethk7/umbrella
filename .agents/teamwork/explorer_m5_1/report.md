# Umbrella Patient Portal (`/portal/patient`) — UI Architecture Blueprint

**Milestone**: M5 — Patient Portal Surface  
**Author**: Explorer M5-1 (`teamwork_explorer`)  
**Date**: 2026-11-01  
**Scope**: Full UI architecture, Bento grid layout, responsive design (375x667 & 1280x800), accessibility strategy, Apple motion physics, and component breakdown for `src/app/portal/patient/` and `src/components/patient/`.

---

## 1. Executive Summary & Design System Alignment

The Patient Portal (`/portal/patient`) is the patient's authenticated control center for managing life-critical emergency identity data, primary emergency contacts, family dependents, and health baselines. Per **AGENTS.md** (N1–N10), **01-design-system.md**, and **docs/DECISIONS.md** (D2, D3, D4, D7, D10, D12), the interface must fulfill the following non-negotiable principles:

1. **Aesthetic Baseline**: Apple-inspired compact Bento grid, 24px page padding (`p-6`), 16px grid gap (`gap-4`), cards with 18–20px rounded corners (`rounded-[18px]` to `rounded-[20px]`), subtle hairline borders (`border border-black/10`), and restraint in shadows (`shadow-[0_1px_2px_rgba(0,0,0,0.04),0_8px_24px_rgba(0,0,0,0.06)]`).
2. **Privacy Hygiene (Invariant N1)**: Clearly demarcate what data is public on roadside emergency scans (`/emergency/[token]`) vs. what data remains strictly private within the authenticated portal. Residential address and family dependents are flagged with private security badges to reassure patients.
3. **Emergency QR Studio Integration**: Live SVG QR preview computed client-side (`window.location.origin + '/emergency/' + qr_token`), CR80 300 DPI PDF card export trigger, 1080x1080 PNG lock screen export, non-blocking environment warning on localhost / preview (D12), and secure token rotation with instant invalidation warning (D3).
4. **Clinical Verification Boundary (DECISIONS D7)**: Patient can submit an initial baseline (conditions and allergies) via RPC `submit_self_reported_baseline` while unverified (`is_doctor_verified = false`). Once verified by an approved clinician, baseline editing disappears/locks, rendering a verified clinical summary with audit timestamps.

---

## 2. Bento Grid Layout Architecture

### 2.1 Spacing & Design Token Reference
- **Page Container**: `max-w-6xl mx-auto px-4 sm:px-6 py-6 space-y-6`
- **Grid Layout**: `grid grid-cols-1 lg:grid-cols-12 gap-4`
- **Surface Elevation**: `bg-surface border border-black/10 rounded-[18px] p-6 shadow-[0_1px_2px_rgba(0,0,0,0.04),0_8px_24px_rgba(0,0,0,0.06)]`
- **Typography**:
  - Hero Header: `-apple-system`, weight 700, tracking -0.03em.
  - Card Titles: weight 600, tracking -0.022em, 20px leading-none.
  - Body Text: weight 400, 15px/16px, color `--text-primary` (`#000000`).
  - Small Subtext (<18px): color `--text-body-secondary` (`#6e6e73` per D10 WCAG AA compliance).

---

### 2.2 Desktop Bento Grid Layout (1280x800)

On desktop screens, the portal organizes into a high-density, balanced 12-column Bento structure:

```
+----------------------------------------------------------------------------------------------------+
| Top Bar: Page Title ("Emergency Medical ID") + Patient Code Badge (Copy) + Last Sync Indicator      |
+----------------------------------------------------------------------------------------------------+
| [Row 1]                                                                                            |
| +---------------------------------------------------+ +------------------------------------------+ |
| | Hero Profile Card (col-span-8)                    | | Emergency QR Studio Card (col-span-4)     | |
| | - Avatar / Monogram + Full Name                   | | - Live SVG QR Preview (180x180)          | |
| | - Patient Code + BloodGroupPill (Large)           | | - Environment Origin Warning (D12)       | |
| | - Age / DOB + Verification Status Pill            | | - [Export PDF Card] [Download PNG]       | |
| | - Roadside Triage Safety Notice                   | | - [Preview Public View] [Rotate Token]   | |
| +---------------------------------------------------+ +------------------------------------------+ |
|                                                                                                    |
| [Row 2]                                                                                            |
| +---------------------------------------------------+ +------------------------------------------+ |
| | Primary Emergency Contact Card (col-span-4)       | | Medical Baseline & Clinical Card (span-8)| |
| | - Emergency Contact Name & Relation Badge         | | - Verification State Header (Badge + Meta) |
| | - Formatted Phone Number (Monospace)              | | - Critical Allergy Alert Box (D10 Red)   | |
| | - [One-Tap Call Button (tel:)] (44px min)         | | - Chronic Medical Conditions Chips       | |
| | - [Edit Emergency Contact Button]                 | | - Active Medications & Surgical History | |
| |                                                   | | - [Edit Baseline Button] (if unverified) | |
| +---------------------------------------------------+ +------------------------------------------+ |
|                                                                                                    |
| [Row 3]                                                                                            |
| +---------------------------------------------------+ +------------------------------------------+ |
| | Demographics Card (col-span-6)                    | | Family Dependents Card (col-span-6)      | |
| | - Primary Contact Phone                           | | - Spouse & Dependents List (max 10)      | |
| | - Residential Home Address                        | | - Relationship, Age, Phone tags          | |
| | - Invariant N1 Privacy Assurance Pill             | | - [Add Dependent Button] + Inline Delete | |
| | - [Edit Demographics Button]                      | | - Invariant N1 Privacy Assurance Pill    | |
| +---------------------------------------------------+ +------------------------------------------+ |
+----------------------------------------------------------------------------------------------------+
```

---

### 2.3 Mobile Layout (375x667 Viewport)

On mobile viewports (e.g. iPhone SE 375x667), the Bento grid seamlessly collapses into a single-column linear stack (`grid-cols-1 gap-4`). The visual hierarchy is prioritized for acute emergency utility:

1. **Top Bar**: Umbrella logo, Patient Code with copy icon button.
2. **Hero Profile Card**: Patient name, prominent `BloodGroupPill`, age, verification status.
3. **Emergency QR Studio Card**: Instant QR code view ready to be presented on the phone screen to first responders, with 44px download and preview action buttons.
4. **Primary Emergency Contact Card**: Direct one-touch phone call button (`tel:`) with 56px touch target for rapid roadside dialing.
5. **Medical Baseline Card**: Critical Allergy alert box followed by chronic conditions and active medications.
6. **Demographics Card**: Contact phone and address.
7. **Family Dependents Card**: Expandable/collapsible list of dependents.

---

## 3. Card-by-Card Architectural Blueprint

### 3.1 Hero Profile Card (`HeroProfileCard`)
- **File**: `src/components/patient/hero-profile-card.tsx`
- **Data Source**: `accounts.full_name`, `accounts.email`, `patient_profiles.patient_code`, `patient_profiles.age`, `patient_profiles.blood_group`, `clinical_records.is_doctor_verified`.
- **UI Structure**:
  - **Left Section**:
    - Monogram avatar badge (48px) with patient initials.
    - Full Name (`text-2xl font-bold tracking-[-0.03em]`).
    - Account email (`text-sm text-text-body-secondary`).
    - Identity metadata pills:
      - `patient_code` interactive chip: displays `UMB-XXXXXX` with clipboard copy button (`Copy` icon, 44px min target). Shows green "Copied to clipboard" feedback via `aria-live="polite"`.
      - Age badge: `${age} years old`.
      - Verification pill: If `is_doctor_verified === true`, renders green badge (`CheckCircle2` + "Clinically Verified"); if `false`, renders amber badge (`Clock` + "Self-Reported Baseline").
  - **Right Section**:
    - Embedded `BloodGroupPill` (`bloodGroup={blood_group}`, `size="lg"`). Highlights the critical triage marker in bold red outline and high-contrast typography.
  - **Bottom Banner**:
    - Subtle contextual caption: *"Your Umbrella Emergency Medical ID is active. First responders can access your critical triage info immediately upon scanning your unique QR code."*

---

### 3.2 Emergency QR Studio Card (`EmergencyQrCard`)
- **File**: `src/components/patient/emergency-qr-card.tsx`
- **Data Source**: `patient_profiles.qr_token`, `patient_profiles.patient_code`, `accounts.full_name`, `patient_profiles.blood_group`.
- **Compliance Rules**: N6, D12, umbrella-qr-card skill.
- **UI Structure**:
  - **Card Header**:
    - Title: "Emergency QR Studio" + `QrCode` icon.
    - Description: "Physical & digital access pass for roadside triage."
  - **QR Code Viewport**:
    - Rendered using `QRCodeSVG` from `qrcode.react`:
      - `level="Q"` (25% Reed-Solomon error correction for dirty/scratched physical cards).
      - `marginSize={4}`.
      - `fgColor="#000000"`, `bgColor="#ffffff"` (strict black on white per skill).
      - Dimension: 180x180px (scales up to 224px on mobile phones).
    - Client-computation: `buildEmergencyUrl(origin, qr_token)` computed inside `useEffect` after mount. While mounting, renders a matching 180x180px animated skeleton pulse to prevent Next.js hydration mismatch.
  - **Environment Warning Notice (DECISIONS D12)**:
    - If `origin` is `localhost` or ends with `.vercel.app` (non-production):
      - Renders calm amber alert banner: *"Note: Testing environment. This QR points to `{origin}`. Physical cards printed from this preview only resolve while this environment is active."*
  - **Action Button Bar** (All >= 44px min touch height):
    1. **"Print Card (PDF)"**: Primary action button. Calls `generateCr80Pdf()` (via `src/lib/pdf.ts`), generating a 2-sided 300 DPI CR80 wallet card (`[85.6, 54] mm`).
    2. **"Save Image (PNG)"**: Secondary button. Offscreen canvas render (1080x1080) for phone wallpaper/lock screen.
    3. **"Preview Triage"**: Ghost button with `ExternalLink` icon. Opens `/emergency/[qr_token]` in a new tab with `rel="noopener noreferrer"`.
    4. **"Rotate QR"**: Destructive hairline button (`RefreshCw` icon). Opens `QrRotationModal`.

---

### 3.3 Primary Emergency Contact Card (`EmergencyContactCard`)
- **File**: `src/components/patient/emergency-contact-card.tsx`
- **Data Source**: `patient_profiles.emergency_contact_name`, `patient_profiles.emergency_contact_relation`, `patient_profiles.emergency_contact_phone`.
- **UI Structure**:
  - **Card Header**:
    - Icon: `HeartPulse` in red tinted circle.
    - Title: "Primary Emergency Contact"
    - Top-right Action: "Edit Contact" button (`Pencil` icon, min 44px).
  - **Contact Information Display**:
    - Name: `text-xl font-bold text-text-primary`.
    - Relationship Pill: `inline-flex px-3 py-1 rounded-full text-xs font-semibold bg-black/5 text-text-body-secondary` (e.g., "Spouse / Partner", "Parent", "Sibling").
    - Phone Number: Formatted via `formatPhone(phone)` in bold high-contrast font (`text-2xl font-bold text-accent-action tracking-tight`).
  - **Immediate Call CTA (N2 / A11y)**:
    - Sticky / Prominent button: `Button variant="emergency"` (or `variant="primary"` on desktop).
    - `href={`tel:${sanitizeTel(emergency_contact_phone)}`}`.
    - Min touch height: 48px–56px.
    - Icon: `Phone` with text "Call Emergency Contact".
  - **Quick Edit Modal**:
    - Controlled dialog using `Modal` (`components/ui/modal.tsx`).
    - Inputs: Contact Name, Relationship, Phone Number.
    - Validated with Zod `phoneRegex`.

---

### 3.4 Medical Baseline & Clinical Overview Card (`MedicalBaselineCard`)
- **File**: `src/components/patient/medical-baseline-card.tsx`
- **Data Source**: `clinical_records.medical_conditions`, `clinical_records.allergies`, `clinical_records.current_medication`, `clinical_records.previous_surgeries`, `clinical_records.is_doctor_verified`, `clinical_records.last_appointment_date`, `clinical_records.last_appointment_summary`.
- **Compliance Rules**: DECISIONS D7, D10.
- **UI Structure**:
  - **Status Header**:
    - If `is_doctor_verified === true`:
      - Green badge: `Badge variant="verified"` ("Doctor Verified").
      - Audit trail text: *"Verified by licensed clinician. Direct patient modifications are disabled to guarantee clinical integrity for emergency responders."*
    - If `is_doctor_verified === false`:
      - Amber badge: `Badge variant="pending"` ("Self-Reported Baseline").
      - Subtext: *"Initial baseline reported by patient. You can update your conditions and allergies below until a verified clinician confirms them."*
      - Action: "Edit Baseline" button (`Pencil` icon, min 44px).
  - **Critical Allergies Alert (DECISIONS D10)**:
    - Embedded `AllergyAlert` component:
      - If allergies exist: High-contrast red container (`bg-clinical-critical/10 border-2 border-clinical-critical`), `AlertOctagon` icon, white-on-red badge tags (`bg-clinical-critical text-white font-bold`).
      - If empty: Calm neutral panel: *"No known drug or environmental allergies reported."*
  - **Chronic Medical Conditions**:
    - Section header: "Medical Conditions & Diagnoses".
    - Badge cloud: Individual condition tags (`bg-black/5 text-text-primary px-3 py-1.5 rounded-xl font-medium text-sm`).
    - Empty state: *"No chronic conditions recorded."*
  - **Active Medications Grid**:
    - Section header: "Current Medications".
    - Two-column card grid:
      - Medication Name (`font-semibold text-text-primary`)
      - Dosage & Frequency badge (`bg-accent-action/10 text-accent-action text-xs px-2 py-0.5 rounded-md font-mono`)
      - Prescriber note if present (`text-xs text-text-body-secondary`)
  - **Previous Surgeries Timeline**:
    - Procedure name, Year badge (`1900–2099`), and surgical notes.
  - **Clinical Consultation History**:
    - Last appointment date formatted with `Intl.DateTimeFormat`.
    - Clinical summary excerpt from physician.

---

### 3.5 Demographics Card (`DemographicsCard`)
- **File**: `src/components/patient/demographics-card.tsx`
- **Data Source**: `accounts.contact_phone`, `patient_profiles.residential_address`, `accounts.email`.
- **Compliance Rules**: Invariant N1, DECISIONS D4.
- **UI Structure**:
  - **Card Header**:
    - Title: "Personal Demographics"
    - Privacy Pill: `Lock` icon + "Private Data (Excluded from Emergency Scans)"
  - **Field Display**:
    - Primary Phone: `accounts.contact_phone`
    - Registered Email: `accounts.email` (read-only)
    - Residential Home Address: `patient_profiles.residential_address` (multiline). If blank: *"No residential address provided."*
  - **Inline / Modal Edit Flow**:
    - Editable fields: `contact_phone`, `residential_address`.
    - Submits via Server Action `updateDemographicsAction` targeting allowed update columns in `patient_profiles` and `accounts`.

---

### 3.6 Family Dependents Manager Card (`DependentsCard`)
- **File**: `src/components/patient/dependents-card.tsx`
- **Data Source**: `patient_profiles.spouse_dependents` (`Json` array of `SpouseDependent`).
- **Compliance Rules**: Invariant N1, DECISIONS D3.
- **UI Structure**:
  - **Card Header**:
    - Title: "Spouse & Family Dependents"
    - Counter Badge: `${dependents.length} / 10`
    - Action: "Add Dependent" button (`UserPlus` icon, min 44px).
  - **List of Dependents**:
    - Card rows showing:
      - Full Name (`font-semibold`)
      - Relationship badge (`Spouse`, `Child`, `Dependent Parent`)
      - Age (`${age} yrs`) and contact phone if provided
      - Trash icon button (44px min target) to remove dependent
  - **Add/Edit Dependent Modal**:
    - Form inputs: Dependent Full Name, Relationship (dropdown / text), Age (optional, 0–130), Phone (optional, phoneRegex).
    - Enforces maximum 10 dependents constraint.
    - Saves updated JSON array to `patient_profiles.spouse_dependents`.

---

### 3.7 QR Rotation Warning Modal (`QrRotationModal`)
- **File**: `src/components/patient/qr-rotation-modal.tsx`
- **Data Source**: RPC `regenerate_qr_token()`.
- **Compliance Rules**: DECISIONS D3, umbrella-qr-card skill.
- **Modal Copy & Behavior**:
  - Title: "Regenerate Emergency QR Code?"
  - Severity: Destructive (`isDestructive={true}`).
  - Warning Copy: *"Your current QR code and emergency link will stop working immediately. Any printed ID cards or saved lock-screen images will show 'Not Found' to emergency responders. You will need to download and reprint your card. Do you want to continue?"*
  - Confirm Button: `Button variant="destructive" isLoading={isRotating}` ("Regenerate Token").
  - Cancel Button: `Button variant="secondary"` ("Keep Current Token").
  - On Success: Local state updates with new UUID, QR code re-renders instantly, success toast instructs user to print new card.

---

### 3.8 Baseline Submission Modal (`BaselineEditorModal`)
- **File**: `src/components/patient/baseline-editor-modal.tsx`
- **Data Source**: RPC `submit_self_reported_baseline(p_conditions, p_allergies)`.
- **Compliance Rules**: DECISIONS D7.
- **Behavior**:
  - Accessible ONLY when `is_doctor_verified === false`.
  - Condition chip input: Add/remove tag list for chronic conditions (up to 50 items).
  - Allergy chip input: Add/remove tag list for critical allergies (up to 50 items).
  - Submit button: Invokes `submitBaselineAction`.
  - On Success: Updates `clinical_records` and refreshes portal view.
  - If `is_doctor_verified === true`: Modal cannot be opened, trigger raises error if attempted.

---

## 4. Responsive & Accessibility Strategy

### 4.1 Responsive Viewport Strategy
| Dimension | Breakpoint | Layout Behavior | Focus Areas |
|---|---|---|---|
| **375 x 667** (Mobile) | `< 768px` (`col-1`) | Single vertical Bento stack; 16px page padding; 100% card width | Emergency QR above fold, 44px+ touch targets, direct `tel:` call button |
| **768 x 1024** (Tablet) | `md:grid-cols-2` | 2-column balanced grid; 20px padding | Hero + QR side-by-side; Demographics + Dependents side-by-side |
| **1280 x 800** (Desktop) | `lg:grid-cols-12` | 12-column Bento grid; 24px padding (`p-6`); 16px gaps | Full bento hierarchy: 8/4 hero-QR, 4/8 contact-baseline, 6/6 demographics |

### 4.2 Accessibility Compliance Checklist (WCAG 2.1 AA)
1. **Touch Target Size**: Every interactive control (buttons, tab items, copy triggers, modal close icons, trash icons) has a bounding box of at least **44 x 44px**.
2. **Focus Visibility**: All interactive elements specify `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action focus-visible:ring-offset-2`.
3. **Contrast Ratios (DECISIONS D10)**:
   - Body secondary text uses `#6e6e73` (4.6:1 contrast ratio against white `#ffffff`).
   - Critical allergy badge text uses `#d70015` (`--clinical-critical-text`).
   - Verified badge text uses `#1d7a37` (`--clinical-verified-text`).
   - Pending badge text uses `#8a5200` (`--clinical-pending-text`).
   - Blood group pill uses large 24px+ bold red font on white.
4. **Semantic Structure & ARIA**:
   - Page has single `<main id="main-content">`.
   - Cards are wrapped in `<section aria-labelledby="card-title-id">`.
   - Modals use `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, and implement keyboard focus traps (Tab, Shift+Tab, Escape).
   - Dynamic clipboard copy feedback uses `aria-live="polite"`.
5. **No Motion Flashes / Reduced Motion**:
   - Portal is wrapped in `<MotionConfig reducedMotion="user">`.
   - Users with `prefers-reduced-motion: reduce` receive instant transitions without positional or scale springs.

---

## 5. Motion Physics & Interactive Feedback

All animations adhere to **01-design-system.md** and leverage `src/lib/motion.ts`:

```typescript
// Shared Apple Spring (Stiffness: 120, Damping: 20, Mass: 1)
export const appleSpring: Transition = {
  type: 'spring',
  stiffness: 120,
  damping: 20,
  mass: 1,
};
```

1. **Button Hover & Tap Feedback**:
   - `whileHover={{ scale: 1.015 }}`
   - `whileTap={{ scale: 0.98 }}`
   - Smooth spring recovery; zero CSS color flashes.
2. **Modal Entry & Exit**:
   - Entrance: `initial={{ opacity: 0, scale: 0.96, y: 12 }}` -> `animate={{ opacity: 1, scale: 1, y: 0 }}` with `appleSpring`.
   - Exit: `exit={{ opacity: 0, scale: 0.96, y: 12 }}` with 150ms `easeOut`.
3. **Segmented Tabs / Pill Toggles**:
   - `layoutId="active-pill"` with `segmentedPillTransition` (`stiffness: 180, damping: 24`).

---

## 6. Component File Breakdown & Implementation Map

```text
src/
├── app/
│   └── portal/
│       └── patient/
│           ├── page.tsx                    # Server Component: user auth, DB fetch, role gate
│           ├── actions.ts                  # Server Actions: updateProfile, submitBaseline, rotateToken
│           └── loading.tsx                 # Bento skeleton loading state
├── components/
│   └── patient/
│       ├── patient-portal-shell.tsx        # Client shell managing state, toasts, modal visibility
│       ├── hero-profile-card.tsx           # Hero Card: Name, Code (Copy), BloodGroupPill, Age
│       ├── emergency-qr-card.tsx           # QR Card: QRCodeSVG, PDF/PNG triggers, Origin notice
│       ├── emergency-contact-card.tsx      # Emergency Contact: Name, Relation, Phone, tel: button
│       ├── medical-baseline-card.tsx       # Baseline Card: Verified/Pending badge, Allergies, Meds
│       ├── demographics-card.tsx           # Demographics: Phone, Residential Address, Privacy badge
│       ├── dependents-card.tsx             # Dependents: Spouse & family list (up to 10), Add/Delete
│       ├── qr-rotation-modal.tsx           # Token Rotation: Destructive warning dialog & RPC call
│       └── baseline-editor-modal.tsx       # Baseline Editor: Condition/Allergy form (unverified only)
└── lib/
    ├── utils.ts                            # formatPhone, sanitizeTel, safeNext, buildEmergencyUrl
    └── pdf.ts                              # generateCr80Pdf (jspdf 300 DPI CR80 wallet card)
```

---

## 7. Data Flow, Interfaces & Server Actions Contract

### 7.1 Server Page Entry Point (`src/app/portal/patient/page.tsx`)
```typescript
import { redirect } from 'next/navigation';
import { createClient } from '@/lib/supabase/server';
import { PatientPortalShell } from '@/components/patient/patient-portal-shell';

export const dynamic = 'force-dynamic';

export default async function PatientPortalPage() {
  const supabase = createClient();
  
  // N3: Server authentication strictly with auth.getUser()
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    redirect('/login?next=/portal/patient');
  }

  // Fetch account, profile, and clinical record in parallel
  const [accountRes, profileRes, clinicalRes] = await Promise.all([
    supabase.from('accounts').select('*').eq('id', user.id).single(),
    supabase.from('patient_profiles').select('*').eq('patient_id', user.id).single(),
    supabase.from('clinical_records').select('*').eq('patient_id', user.id).single(),
  ]);

  if (accountRes.data?.role === 'doctor') {
    redirect('/portal/doctor');
  }

  return (
    <PatientPortalShell
      account={accountRes.data!}
      profile={profileRes.data!}
      clinicalRecord={clinicalRes.data!}
    />
  );
}
```

### 7.2 Server Actions (`src/app/portal/patient/actions.ts`)
Three strongly-typed server actions validate inputs with Zod and execute under authenticated RLS:
1. `updateDemographicsAction(input: PatientProfileInput)`:
   - Validates fields via `patientProfileSchema`.
   - Updates `accounts.contact_phone` and `patient_profiles.residential_address`, `age`, `blood_group`.
   - Revalidates `/portal/patient`.
2. `updateDependentsAction(dependents: SpouseDependent[])`:
   - Validates array length (<= 10) and item schemas.
   - Updates `patient_profiles.spouse_dependents`.
3. `submitBaselineAction(input: BaselineSubmissionInput)`:
   - Validates arrays with `baselineSubmissionSchema`.
   - Executes RPC `submit_self_reported_baseline`.
4. `rotateQrTokenAction()`:
   - Executes RPC `regenerate_qr_token`.
   - Returns new UUID token.

---

## 8. Verification & QA Matrix

| Feature | Acceptance Criteria | Test Method |
|---|---|---|
| **Bento Grid Layout** | 24px padding, 16px gap, 18-20px rounded cards, hairline border, shadow ceiling | Visual inspection in browser; snapshot tests |
| **Desktop 1280x800** | 12-column grid: Hero (8) + QR (4), Contact (4) + Baseline (8), Demographics (6) + Dependents (6) | Playwright viewport test at 1280x800 |
| **Mobile 375x667** | Single column stack, zero horizontal scroll, critical cards above the fold | Playwright viewport test at 375x667 |
| **44px Touch Targets** | All buttons, copy triggers, modal dismissals, tab items have >= 44px touch box | Automated axe / Playwright touch target audit |
| **Privacy Hygiene (N1)** | Address and Dependents show private badge and are never rendered in emergency preview | Playwright assert `/emergency/[token]` DOM lacks address/dependents |
| **QR Client Computation** | QR code string derived post-mount in `useEffect` without SSR hydration mismatch | React hydration log check, Vitest URL builder test |
| **Origin Amber Notice** | Displays warning notice on localhost and preview deployments | Test with `window.location.origin = 'http://localhost:3000'` |
| **Baseline Disappearing UI** | Baseline editor accessible when `is_doctor_verified = false`; locked/hidden when `true` | Unit & E2E test verifying button toggle state |
| **Token Rotation** | Confirmation modal warns of invalidation; RPC updates token and redraws QR | E2E test clicking rotate, asserting new QR URL and old URL 404 |

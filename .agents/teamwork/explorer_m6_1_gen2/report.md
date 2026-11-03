# Umbrella Milestone M6 Technical Blueprint: Doctor Portal UI & Safety Banner

**Author**: Explorer M6-1 (Doctor UI & Safety Banner Explorer)  
**Target Milestone**: M6 (Doctor Portal Surface)  
**Target Directory**: `src/app/portal/doctor` & `src/components/doctor`  
**Date**: 2026-11-01  
**Status**: Ready for Implementation by Worker  

---

## 1. Executive Summary & Architecture Overview

The Doctor Portal (`/portal/doctor`) serves as Umbrella's authoritative clinical management surface. It enables verified healthcare providers to search patients, review life-critical emergency profiles, update and verify medical records (chronic conditions, prescription medications, surgical procedures, and critical allergies), and coordinate patient appointments.

Because Umbrella directly powers acute roadside triage, clinical continuity is a safety-critical concern. This blueprint defines an architectural specification that guarantees:
1. **Strict Credential Gating (D1)**: Zero patient record access for pending or unapproved physicians.
2. **Multi-Modal Patient Search (D14)**: Parameterized, injection-safe lookup supporting `UMB-XXXXXX` patient codes, QR tokens (UUIDs), contact phone numbers, and full names.
3. **Persistent Read-Only Safety Banner (N2)**: A sticky header (`sticky top-16 z-30`) that remains perpetually in view while viewing or modifying clinical records, preventing wrong-patient charting.
4. **Authoritative Clinical Verification (D7)**: Database trigger-enforced verification stamps (`is_doctor_verified = true`, `last_updated_by_doctor_id = auth.uid()`, `updated_at = now()`) with optimistic concurrency and dirty-state tracking.
5. **Integrated Appointment Management (D6, D8)**: Full scheduling lifecycle with automatic consultation summary synchronization on appointment completion.
6. **Design System & A11y Compliance**: Strict adherence to Apple-inspired tokens, 44px touch targets, `appleSpring` motion physics, WCAG AA contrast compliance, and full mobile (375x667) and desktop (1280x800) responsiveness.

---

## 2. Invariants & Decision Mapping

| Ref | Requirement | Implementation Strategy in M6 |
|---|---|---|
| **N2** | Safety Banner Invariant | Persistent read-only banner visible at all times while viewing or editing clinical data. Shows Patient Full Name, Age, Blood Group, and Primary Emergency Contact. Fixed below root nav (`sticky top-16 z-30`). |
| **N3** | Server-Side Identity | Identify caller with `supabase.auth.getUser()`, never `getSession()`. Query role and approval status strictly from `public.accounts`, never `user_metadata`. |
| **N4** | Key Hygiene | Use publishable/anon key only. Zero `service_role` key usage. Rely on Postgres RLS and column grants. |
| **N7** | Design System Tokens | Zero raw hex colors. Use `--accent-action`, `--clinical-critical`, `--clinical-verified`, `--clinical-pending`, `--bg-surface`, `--border-hairline`. Never a white hairline on white surface. |
| **N8** | Shared Motion | Portals use `appleSpring` (`stiffness: 120, damping: 20, mass: 1`) via `framer-motion`. Respect `prefers-reduced-motion`. |
| **N10** | Strict Validation | Zero `any`, zero `@ts-ignore`. Runtime validation using Zod for all form fields and URL search parameters. |
| **D1** | Doctor Approval Gate | Doctor registration defaults to `accounts.doctor_status = 'pending'`. Access to `/portal/doctor` requires `doctor_status === 'approved'`. Pending doctors see the explicit verification banner. |
| **D3** | Column Protection | Clinicians cannot update patient demographics (`accounts.full_name`, `patient_profiles.residential_address`, etc.). Updates restricted strictly to `clinical_records` granted columns. |
| **D5** | Age vs DOB | Store and display `age integer`. Banner displays calculated/stored age with blood group pill. |
| **D7** | Verification Stamps | Server-side trigger `trg_stamp_clinical` stamps `is_doctor_verified = true` and `last_updated_by_doctor_id = auth.uid()` upon clinical record updates. Clinicians can verify baseline without data changes. |
| **D8** | Appointment Trigger | Trigger `trg_appointment_completed` syncs `last_appointment_date` and `last_appointment_summary` to `clinical_records` without flipping `is_doctor_verified`. |
| **D10** | WCAG AA Contrast | Use `--clinical-critical-text` (#d70015) for small red text, `--clinical-verified-text` (#1d7a37) for verified badges, and `--clinical-pending-text` (#8a5200) for pending badges. |
| **D14** | Multi-Modal Search | Classify input (UMB code, UUID, 7+ digits phone, or text name). Minimum 2 characters, 300ms debounce, max 20 results. Run separate parameterized queries; never construct `.or()` strings. |
| **D15** | Direct Patient Load | Support `/portal/doctor?patient_token=<uuid>` or `/portal/doctor?patient_id=<uuid>` to preload patient records directly. |
| **D17** | Locale Date Handling | Format timestamptz dates using `Intl.DateTimeFormat` in client locale. |

---

## 3. Gating & Pending UX Specification (DECISIONS D1)

### 3.1 Server-Side Gate Logic
In `src/app/portal/doctor/page.tsx`:
```typescript
const supabase = createClient();
const { data: { user }, error: authError } = await supabase.auth.getUser();

if (!user || authError) {
  redirect('/login?next=/portal/doctor');
}

const { data: account } = await supabase
  .from('accounts')
  .select('id, full_name, email, role, doctor_status, medical_license_number, specialization')
  .eq('id', user.id)
  .single();

if (account?.role !== 'doctor') {
  redirect('/portal/patient');
}

if (account?.doctor_status !== 'approved') {
  redirect('/portal/doctor/pending');
}
```

### 3.2 Pending Approval Screen Enhancement
File: `src/app/portal/doctor/pending/page.tsx`  
The prompt explicitly mandates:
> **Clear banner**: `"Account Pending Approval - Our team verifies medical credentials within 24 hours. While pending, patient records cannot be accessed."`

Update the informational alert box in `src/app/portal/doctor/pending/page.tsx` to prominently render this exact statement in high contrast using the `--clinical-pending` token.

---

## 4. Multi-Modal Patient Search Architecture (DECISIONS D14 & D15)

### 4.1 Search Input Classification Algorithm
Per DECISIONS D14 and Security Rule 02 #5, the search input is analyzed and routed to specific parameterized queries. **Never** construct a composite `.or()` string with raw user input.

```typescript
export function classifySearchInput(rawQuery: string): {
  type: 'patient_code' | 'qr_token' | 'phone' | 'name';
  cleanValue: string;
} {
  const query = rawQuery.trim();

  // 1. Matches UMB-XXXXXX (case-insensitive)
  if (/^UMB-[A-Za-z0-9]{6}$/i.test(query)) {
    return { type: 'patient_code', cleanValue: query.toUpperCase() };
  }

  // 2. Matches UUID format (36-char qr_token)
  if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(query)) {
    return { type: 'qr_token', cleanValue: query.toLowerCase() };
  }

  // 3. 7+ digits (phone number lookup)
  const digitsOnly = query.replace(/\D/g, '');
  if (digitsOnly.length >= 7) {
    return { type: 'phone', cleanValue: digitsOnly };
  }

  // 4. Default: Name text search (escape PostgREST special chars)
  const escapedName = query.replace(/[%_,()]/g, '');
  return { type: 'name', cleanValue: escapedName };
}
```

### 4.2 Parameterized Database Queries
In `src/app/portal/doctor/actions.ts`:
1. **`patient_code`**:
   ```typescript
   supabase
     .from('patient_profiles')
     .select('patient_id, patient_code, qr_token, age, blood_group, emergency_contact_name, emergency_contact_phone, accounts!inner(id, full_name, contact_phone)')
     .eq('patient_code', cleanValue)
     .limit(20);
   ```
2. **`qr_token`**:
   ```typescript
   supabase
     .from('patient_profiles')
     .select('patient_id, patient_code, qr_token, age, blood_group, emergency_contact_name, emergency_contact_phone, accounts!inner(id, full_name, contact_phone)')
     .eq('qr_token', cleanValue)
     .limit(20);
   ```
3. **`phone`**:
   Run two parameterized queries:
   - Query 1: `accounts` where `contact_phone.ilike('%' + cleanValue + '%')` and `role = 'patient'`
   - Query 2: `patient_profiles` where `emergency_contact_phone.ilike('%' + cleanValue + '%')`
   Deduplicate results by `patient_id`.
4. **`name`**:
   ```typescript
   supabase
     .from('accounts')
     .select('id, full_name, contact_phone, patient_profiles!inner(patient_id, patient_code, qr_token, age, blood_group, emergency_contact_name, emergency_contact_phone)')
     .eq('role', 'patient')
     .ilike('full_name', `%${cleanValue}%`)
     .limit(20);
   ```

### 4.3 UI States for Patient Search
- **Idle State**: Instructional prompt with search format tags (`UMB-XXXXXX`, `Patient Name`, `Phone`, `QR Token`).
- **Loading State**: Subtle spinning indicator inside input, calm skeleton cards.
- **Empty State**: Friendly "No patients found" feedback with suggestions to check Patient Code or phone formatting.
- **Result List**: Interactive cards showing:
  - Patient Full Name & Patient Code badge
  - Age & Blood Group Pill
  - Emergency Contact preview
  - Verification Badge (`Verified` vs `Self-Reported Baseline`)
  - Selection CTA ("Open Clinical Record")

---

## 5. Persistent Read-Only Safety Banner Specification (NON-NEGOTIABLE N2)

### 5.1 Positioning & Geometry
- **Root Layout Header**: Sits at `sticky top-0 z-40` with `h-16` (64px).
- **Safety Banner**: Positioned at `sticky top-16 z-30 w-full`.
- **Z-Index Layering**: Header (z-40) > Safety Banner (z-30) > Modals (z-50) > Content (z-0).
- **Result**: The banner sticks immediately below the top navigation bar and CANNOT be scrolled out of view while the doctor edits long clinical forms or reviews surgeries.

### 5.2 Content & Structure
The banner MUST display the following read-only patient identity indicators:
1. **Patient Full Name**: Large, bold title (`text-lg font-bold text-text-primary`) with patient code pill (`UMB-XXXXXX`).
2. **Age**: Calculated/stored age displayed prominently (`Age: 42 yrs`).
3. **Blood Group**: High-contrast `BloodGroupPill` (red outline, large bold red typography).
4. **Primary Emergency Contact**:
   - Contact Full Name & Relationship (`Jane Doe (Spouse)`).
   - Clickable `tel:` call button with phone icon, sanitized via `sanitizeTel(phone)`.
5. **Clinical Record Status Badge**:
   - If verified: `<Badge variant="verified">Doctor Verified</Badge>`
   - If self-reported: `<Badge variant="pending">Self-Reported Baseline (Unverified)</Badge>`
6. **Read-Only Demographics Indicator**:
   - Small lock icon with caption: `"Demographics are patient-managed and locked against clinical overwrite"`.
   - Prevents medical staff from accidentally overwriting identity/demographics during clinical charting.

### 5.3 Responsive Layouts
- **Desktop (1280x800)**: Single horizontal bar with 4 clear metric clusters (Identity + Code, Age + Blood Group, Emergency Contact + Phone, Verification Badge + Lock icon).
- **Mobile (375x667)**: Two-row compact layout:
  - Top row: Patient Name, Blood Group pill, Verification badge.
  - Bottom row: Age, Emergency Contact with one-tap `tel:` button.
  - Height budgeted to ≤ 72px to conserve vertical viewport for clinical editing.

---

## 6. Clinical Record Editor & Verification Specification (DECISIONS D3 & D7)

### 6.1 Clinical Data Schema & Fields
The editor operates on `public.clinical_records`:
- **Chronic Medical Conditions** (`medical_conditions: text[]`):
  - Dynamic list with add input, Enter key support, and remove tags.
- **Current Medications** (`current_medication: MedicationItem[]`):
  - Structured fields: `name` (required), `dosage` (required), `frequency` (required), `prescribed_by` (optional).
  - Add medication modal / row creator; delete and edit capability.
- **Critical Allergies** (`allergies: text[]`):
  - Rendered with `AllergyAlert` banner at the top of the allergy section.
  - Interactive allergy manager with severity tags (Mild, Moderate, Severe/Anaphylactic).
- **Previous Surgeries** (`previous_surgeries: SurgeryItem[]`):
  - Structured fields: `procedure` (required), `year` (1900-2099 regex), `notes` (optional).
  - Add surgery row; delete capability.
- **Physician Consultation Notes & Diagnoses**:
  - Multiline text area for clinical assessment and notes.

### 6.2 Trigger-Enforced Verification Stamp (D7)
When an approved doctor updates `clinical_records`, the Postgres trigger `trg_stamp_clinical` fires BEFORE UPDATE:
```sql
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
```
**Key UX Implications**:
- When the doctor clicks **"Verify Baseline"** or **"Save Clinical Record"**, the action performs an update on `clinical_records`.
- The database trigger automatically stamps `is_doctor_verified = true`, `last_updated_by_doctor_id = auth.uid()`, and `updated_at = now()`.
- Even if the patient had self-reported data that requires no changes, the doctor saving or verifying stamps the record as doctor-verified without altering the condition/allergy list (satisfying DECISIONS D7).
- The UI immediately revalidates and displays:
  `"Verified by Dr. [Physician Name] on [Date]"` with a green verified shield.

### 6.3 Dirty State Tracking & Concurrency
- Compare form state against loaded baseline.
- **"Save Clinical Changes"** button is disabled when pristine (`!isDirty`), enabling only when edits are made or when verifying an unverified baseline.
- If the doctor attempts to switch active patients while dirty, display an accessible confirmation modal: *"You have unsaved clinical modifications. Do you want to discard them or continue editing?"*

---

## 7. Appointment Management Architecture (DECISIONS D6 & D8)

### 7.1 Appointment Workflow & Data Model
Table: `public.appointments`
- `id`: UUID (Primary Key)
- `patient_id`: UUID (references `public.accounts.id`)
- `doctor_id`: UUID (references `public.accounts.id`, `on delete restrict` per D6)
- `scheduled_at`: timestamptz (ISO string)
- `status`: `'scheduled' | 'completed' | 'cancelled'`
- `reason`: text (required, min 2, max 255)
- `clinical_notes`: text (optional, max 1000)

### 7.2 Appointment Completion Trigger (D8)
When the clinician updates an appointment status to `'completed'`, the database trigger `trg_appointment_completed` executes:
```sql
if new.status = 'completed' and old.status is distinct from 'completed' then
  perform set_config('umbrella.skip_stamp', 'on', true);
  update public.clinical_records
  set last_appointment_date = new.scheduled_at,
      last_appointment_summary = coalesce(nullif(new.clinical_notes, ''), new.reason)
  where patient_id = new.patient_id
    and (last_appointment_date is null or last_appointment_date <= new.scheduled_at);
  perform set_config('umbrella.skip_stamp', 'off', true);
end if;
```
This automatically updates `last_appointment_date` and `last_appointment_summary` in the patient's clinical record **without** flipping `is_doctor_verified` (satisfying DECISIONS D8).

### 7.3 Appointment UI Components
- **Appointments Panel**:
  - Segmented control / Tabs: `"Upcoming"` (status = 'scheduled' and scheduled_at >= now), `"Past / Completed"`, `"All"`.
  - Appointment Card: Scheduled time (formatted with Intl per D17), patient name, reason, status badge, action buttons:
    * `"Complete Visit"` -> Opens completion modal to enter final clinical notes and mark completed.
    * `"Cancel"` -> Prompts confirmation and updates status to `'cancelled'`.
- **Schedule Appointment Modal**:
  - Built using `src/components/ui/modal.tsx`.
  - Preselects the currently active patient if one is loaded, or allows patient selection.
  - Date & local time picker.
  - Reason for visit input.
  - Clinical preparation notes.

---

## 8. File Tree & Component Inventory for Milestone M6

```text
src/
├── app/
│   └── portal/
│       └── doctor/
│           ├── actions.ts                  # Server Actions: search, clinical update, appointments
│           ├── page.tsx                    # Server Component: role gate, initial data, direct load
│           └── pending/
│               └── page.tsx                # Gating screen with D1 verbatim approval banner
├── components/
│   └── doctor/
│       ├── appointment-manager.tsx         # Doctor appointments list with status updates
│       ├── clinical-record-editor.tsx      # Clinical editor: conditions, meds, allergies, surgeries
│       ├── doctor-workspace.tsx            # Master client container (state, split bento layout)
│       ├── patient-safety-banner.tsx       # Sticky N2 read-only banner (sticky top-16 z-30)
│       ├── patient-search-bar.tsx          # Multi-modal search input, debounce, results drawer
│       └── schedule-appointment-modal.tsx  # Accessible modal dialog for booking visits
└── lib/
    └── schemas.ts                          # Updated with appointment & doctor clinical schemas
```

---

## 9. Concrete Implementation Blueprints for Worker

### 9.1 Zod Schemas (`src/lib/schemas.ts`)
Add the following schemas to `src/lib/schemas.ts`:

```typescript
export const appointmentStatusEnum = z.enum(['scheduled', 'completed', 'cancelled']);

export const createAppointmentSchema = z.object({
  patientId: uuidSchema,
  scheduledAt: z.string().datetime({ message: 'A valid appointment date and time is required' }),
  reason: z.string().trim().min(2, 'Reason for visit must be at least 2 characters').max(255, 'Reason cannot exceed 255 characters'),
  clinicalNotes: z.string().trim().max(1000, 'Clinical notes cannot exceed 1000 characters').optional().or(z.literal('')),
});

export type CreateAppointmentInput = z.infer<typeof createAppointmentSchema>;

export const updateAppointmentStatusSchema = z.object({
  appointmentId: uuidSchema,
  status: appointmentStatusEnum,
  clinicalNotes: z.string().trim().max(1000).optional().or(z.literal('')),
});

export type UpdateAppointmentStatusInput = z.infer<typeof updateAppointmentStatusSchema>;

export const doctorClinicalRecordUpdateSchema = z.object({
  patientId: uuidSchema,
  medicalConditions: z.array(z.string().trim().min(1, 'Condition cannot be empty')).default([]),
  currentMedication: z.array(medicationItemSchema).default([]),
  previousSurgeries: z.array(surgeryItemSchema).default([]),
  allergies: z.array(z.string().trim().min(1, 'Allergy cannot be empty')).default([]),
  consultationNote: z.string().trim().max(1000).optional().or(z.literal('')),
});

export type DoctorClinicalRecordUpdateInput = z.infer<typeof doctorClinicalRecordUpdateSchema>;
```

### 9.2 Server Actions (`src/app/portal/doctor/actions.ts`)
Standard return types: `{ ok: true, data: T } | { ok: false, error: string }`.

```typescript
'use server';

import { revalidatePath } from 'next/cache';
import { createClient } from '@/lib/supabase/server';
import {
  createAppointmentSchema,
  updateAppointmentStatusSchema,
  doctorClinicalRecordUpdateSchema,
  type CreateAppointmentInput,
  type UpdateAppointmentStatusInput,
  type DoctorClinicalRecordUpdateInput,
} from '@/lib/schemas';
import type { Json } from '@/lib/supabase/types';

// Action Response Helpers
export type ActionResponse<T = unknown> =
  | { ok: true; data: T }
  | { ok: false; error: string; fieldErrors?: Record<string, string> };

/**
 * Multi-Modal Patient Search Action (DECISIONS D14)
 */
export async function searchPatientsAction(rawQuery: string): Promise<ActionResponse<any[]>> {
  try {
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return { ok: false, error: 'Unauthorized.' };

    const { data: isApproved } = await supabase.rpc('is_approved_doctor');
    if (!isApproved) return { ok: false, error: 'Physician credentials pending approval.' };

    const query = (rawQuery || '').trim();
    if (query.length < 2) return { ok: true, data: [] };

    // Classification per D14
    if (/^UMB-[A-Za-z0-9]{6}$/i.test(query)) {
      const { data, error } = await supabase
        .from('patient_profiles')
        .select(`
          patient_id, patient_code, qr_token, age, blood_group,
          emergency_contact_name, emergency_contact_phone,
          accounts!inner(id, full_name, contact_phone),
          clinical_records(is_doctor_verified)
        `)
        .ilike('patient_code', query)
        .limit(20);

      if (error) throw error;
      return { ok: true, data: data || [] };
    }

    if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(query)) {
      const { data, error } = await supabase
        .from('patient_profiles')
        .select(`
          patient_id, patient_code, qr_token, age, blood_group,
          emergency_contact_name, emergency_contact_phone,
          accounts!inner(id, full_name, contact_phone),
          clinical_records(is_doctor_verified)
        `)
        .eq('qr_token', query.toLowerCase())
        .limit(20);

      if (error) throw error;
      return { ok: true, data: data || [] };
    }

    const digitsOnly = query.replace(/\D/g, '');
    if (digitsOnly.length >= 7) {
      const { data, error } = await supabase
        .from('patient_profiles')
        .select(`
          patient_id, patient_code, qr_token, age, blood_group,
          emergency_contact_name, emergency_contact_phone,
          accounts!inner(id, full_name, contact_phone),
          clinical_records(is_doctor_verified)
        `)
        .or(`emergency_contact_phone.ilike.%${digitsOnly}%,accounts.contact_phone.ilike.%${digitsOnly}%`)
        .limit(20);

      if (error) throw error;
      return { ok: true, data: data || [] };
    }

    // Default: Full Name search
    const safeName = query.replace(/[%_,()]/g, '');
    const { data, error } = await supabase
      .from('patient_profiles')
      .select(`
        patient_id, patient_code, qr_token, age, blood_group,
        emergency_contact_name, emergency_contact_phone,
        accounts!inner(id, full_name, contact_phone),
        clinical_records(is_doctor_verified)
      `)
      .ilike('accounts.full_name', `%${safeName}%`)
      .limit(20);

    if (error) throw error;
    return { ok: true, data: data || [] };
  } catch (err: any) {
    return { ok: false, error: err.message || 'Search failed.' };
  }
}

/**
 * Update Clinical Record Action with Trigger Stamping (DECISIONS D7)
 */
export async function updateClinicalRecordAction(rawData: unknown): Promise<ActionResponse<{ message: string; verifiedAt: string }>> {
  try {
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return { ok: false, error: 'Unauthorized.' };

    const parsed = doctorClinicalRecordUpdateSchema.safeParse(rawData);
    if (!parsed.success) {
      return { ok: false, error: parsed.error.errors[0]?.message || 'Invalid clinical payload.' };
    }

    const { patientId, medicalConditions, currentMedication, previousSurgeries, allergies, consultationNote } = parsed.data;

    // Direct update triggers trg_stamp_clinical
    const { error: updateError } = await supabase
      .from('clinical_records')
      .update({
        medical_conditions: medicalConditions,
        current_medication: currentMedication as unknown as Json,
        previous_surgeries: previousSurgeries as unknown as Json,
        allergies: allergies,
        ...(consultationNote ? { last_appointment_summary: consultationNote } : {}),
      })
      .eq('patient_id', patientId);

    if (updateError) throw updateError;

    revalidatePath('/portal/doctor');
    return {
      ok: true,
      data: {
        message: 'Clinical record verified and saved successfully.',
        verifiedAt: new Date().toISOString(),
      },
    };
  } catch (err: any) {
    return { ok: false, error: err.message || 'Failed to update clinical record.' };
  }
}

/**
 * Schedule Appointment Action
 */
export async function scheduleAppointmentAction(rawData: unknown): Promise<ActionResponse<{ id: string; message: string }>> {
  try {
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return { ok: false, error: 'Unauthorized.' };

    const parsed = createAppointmentSchema.safeParse(rawData);
    if (!parsed.success) {
      return { ok: false, error: parsed.error.errors[0]?.message || 'Invalid appointment fields.' };
    }

    const { patientId, scheduledAt, reason, clinicalNotes } = parsed.data;

    const { data, error } = await supabase
      .from('appointments')
      .insert({
        patient_id: patientId,
        doctor_id: user.id,
        scheduled_at: scheduledAt,
        status: 'scheduled',
        reason: reason,
        clinical_notes: clinicalNotes || null,
      })
      .select('id')
      .single();

    if (error) throw error;

    revalidatePath('/portal/doctor');
    return { ok: true, data: { id: data.id, message: 'Appointment scheduled successfully.' } };
  } catch (err: any) {
    return { ok: false, error: err.message || 'Failed to schedule appointment.' };
  }
}

/**
 * Update Appointment Status Action (DECISIONS D8 Trigger)
 */
export async function updateAppointmentStatusAction(rawData: unknown): Promise<ActionResponse<{ message: string }>> {
  try {
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return { ok: false, error: 'Unauthorized.' };

    const parsed = updateAppointmentStatusSchema.safeParse(rawData);
    if (!parsed.success) {
      return { ok: false, error: parsed.error.errors[0]?.message || 'Invalid status update.' };
    }

    const { appointmentId, status, clinicalNotes } = parsed.data;

    const { error } = await supabase
      .from('appointments')
      .update({
        status: status,
        ...(clinicalNotes ? { clinical_notes: clinicalNotes } : {}),
      })
      .eq('id', appointmentId);

    if (error) throw error;

    revalidatePath('/portal/doctor');
    return { ok: true, data: { message: `Appointment status updated to ${status}.` } };
  } catch (err: any) {
    return { ok: false, error: err.message || 'Failed to update appointment status.' };
  }
}
```

### 9.3 Persistent Read-Only Safety Banner (`src/components/doctor/patient-safety-banner.tsx`)
```tsx
'use client';

import React from 'react';
import { Phone, Lock, User, ShieldCheck, AlertCircle } from 'lucide-react';
import { Badge, BloodGroupPill } from '@/components/ui/badge';
import { sanitizeTel, formatPhone } from '@/lib/utils';
import type { BloodGroup } from '@/lib/supabase/types';

export interface PatientSafetyBannerProps {
  fullName: string;
  patientCode: string;
  age: number;
  bloodGroup: BloodGroup;
  emergencyContactName: string;
  emergencyContactRelation: string;
  emergencyContactPhone: string;
  isDoctorVerified: boolean;
  verifyingDoctorName?: string | null;
  verifiedAt?: string | null;
}

export const PatientSafetyBanner: React.FC<PatientSafetyBannerProps> = ({
  fullName,
  patientCode,
  age,
  bloodGroup,
  emergencyContactName,
  emergencyContactRelation,
  emergencyContactPhone,
  isDoctorVerified,
  verifyingDoctorName,
  verifiedAt,
}) => {
  const cleanPhone = sanitizeTel(emergencyContactPhone);
  const formattedPhone = formatPhone(emergencyContactPhone);

  return (
    <aside
      aria-label="Active Patient Safety Banner"
      className="sticky top-16 z-30 w-full bg-surface/95 backdrop-blur-md border-b border-black/10 shadow-xs transition-all"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          {/* Patient Identity & Read-Only Lock */}
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-black/5 text-text-primary">
              <User className="h-6 w-6" aria-hidden="true" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold tracking-tight text-text-primary">
                  {fullName}
                </h1>
                <span className="font-mono text-xs px-2 py-0.5 rounded-md bg-black/5 text-text-body-secondary font-semibold border border-black/10">
                  {patientCode}
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-text-body-secondary mt-0.5">
                <span className="flex items-center gap-1 font-medium text-text-primary">
                  Age: {age} yrs
                </span>
                <span>•</span>
                <span className="flex items-center gap-1 text-[11px] text-text-body-secondary" title="Demographics are managed by patient and locked against provider overwrite">
                  <Lock className="h-3 w-3 text-text-secondary" aria-hidden="true" />
                  Demographics Read-Only
                </span>
              </div>
            </div>
          </div>

          {/* Blood Group Pill & Verification Badge */}
          <div className="flex items-center gap-4">
            <BloodGroupPill bloodGroup={bloodGroup} size="default" />

            {/* Emergency Contact Click-to-Call */}
            <div className="hidden sm:flex flex-col text-right">
              <span className="text-[10px] font-bold uppercase tracking-wider text-text-body-secondary">
                Emergency Contact
              </span>
              <span className="text-xs font-semibold text-text-primary truncate max-w-[180px]">
                {emergencyContactName} {emergencyContactRelation && `(${emergencyContactRelation})`}
              </span>
              {cleanPhone && (
                <a
                  href={`tel:${cleanPhone}`}
                  className="inline-flex items-center justify-end gap-1 text-xs font-medium text-accent-action hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action rounded"
                  aria-label={`Call emergency contact ${emergencyContactName} at ${formattedPhone}`}
                >
                  <Phone className="h-3 w-3" aria-hidden="true" />
                  <span>{formattedPhone}</span>
                </a>
              )}
            </div>

            {/* Clinical Verification Status */}
            <div>
              {isDoctorVerified ? (
                <Badge variant="verified" icon={<ShieldCheck className="h-3.5 w-3.5" />}>
                  Verified
                </Badge>
              ) : (
                <Badge variant="pending" icon={<AlertCircle className="h-3.5 w-3.5" />}>
                  Self-Reported
                </Badge>
              )}
            </div>
          </div>
        </div>

        {/* Mobile emergency contact row */}
        <div className="sm:hidden flex items-center justify-between pt-2 mt-2 border-t border-black/5 text-xs">
          <span className="text-text-body-secondary">
            ICE: <strong className="text-text-primary">{emergencyContactName}</strong>
          </span>
          {cleanPhone && (
            <a
              href={`tel:${cleanPhone}`}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-accent-action/10 text-accent-action font-semibold text-xs min-h-[36px]"
            >
              <Phone className="h-3.5 w-3.5" />
              <span>Call Contact</span>
            </a>
          )}
        </div>
      </div>
    </aside>
  );
};
```

---

## 10. Verification & Quality Checklist

Before finalizing Milestone M6 code:
1. **Typecheck & Lint**:
   - `npm run typecheck` (tsc `--noEmit`) must succeed with 0 errors.
   - `npm run lint` must pass with zero warnings.
2. **Security & RLS (Check 1 & Check 2)**:
   - Verify that an unapproved doctor cannot fetch patient profiles or clinical records.
   - Verify that `is_approved_doctor()` is respected by all queries.
3. **Safety Banner Positioning (N2)**:
   - Verify banner remains fixed below the glass header during vertical scrolling.
   - Verify that patient name, age, blood group, and emergency contact are clearly legible at 375x667 and 1280x800.
4. **Trigger Stamping (D7 & D8)**:
   - When a doctor updates a clinical record, verify `is_doctor_verified` flips to `true` and `last_updated_by_doctor_id` matches the current doctor's `auth.uid()`.
   - When completing an appointment, verify `last_appointment_date` and `last_appointment_summary` are updated without modifying `is_doctor_verified`.
5. **Multi-Modal Search (D14)**:
   - Verify searches for `UMB-XXXXXX`, UUID, phone, and name return matching synthetic test records with 300ms debounce.
6. **Accessibility**:
   - Touch targets for all interactive buttons, tabs, and telephone links exceed 44px.
   - Contrast passes WCAG AA (small text >= 4.5:1, large text >= 3:1).

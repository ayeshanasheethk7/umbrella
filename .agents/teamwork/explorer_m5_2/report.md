# Architectural Blueprint: Patient Portal Data Fetching & Server Mutations (Milestone M5)

## Executive Summary
This report establishes the complete, production-grade architecture for data loading and server mutations on the Umbrella Patient Portal surface (`/portal/patient`). It reconciles initial requirements with the authoritative database schema (`0001_umbrella_schema.sql`), platform decisions (`docs/DECISIONS.md`), and non-negotiables (`AGENTS.md`), providing complete, ready-to-implement blueprints for `src/app/portal/patient/page.tsx`, `src/app/portal/patient/actions.ts`, and schema extensions in `src/lib/schemas.ts`.

---

## 1. Schema & Architecture Discrepancy Reconciliation

During initial exploration of `0001_umbrella_schema.sql`, `src/lib/supabase/types.ts`, and `docs/DECISIONS.md`, four crucial architectural discrepancies with the initial dispatch prompt were identified and resolved:

| Feature / Contract | Dispatch Prompt Assumption | Database Schema Reality (`0001_umbrella_schema.sql`) | Technical Resolution & Rationale |
|--------------------|----------------------------|------------------------------------------------------|-----------------------------------|
| **Patient Code Location** | Query `accounts` for `patient_code` | `patient_code` exists exclusively on `public.patient_profiles` (`UMB-XXXXXX`) | Query `patient_profiles` for `patient_code`. `accounts` contains `id, email, role, full_name, contact_phone, created_at, updated_at`. |
| **Emergency Token Storage** | Query `emergency_tokens` table for active token | No `emergency_tokens` table exists. `qr_token` is a UUID column on `public.patient_profiles` | Query `patient_profiles.qr_token` directly. A single active token per patient is maintained by design, rotatable via RPC `regenerate_qr_token()`. |
| **Demographics: Age vs DOB / Gender** | Query `date_of_birth, gender` | `patient_profiles` stores `age integer not null default 0`. No `gender` or `date_of_birth` column | Follow **DECISIONS D5**: v1 keeps `age integer`. Signup and demographics forms bind directly to `age` and `blood_group`. |
| **Baseline RPC Parameters** | `submit_self_reported_baseline(p_conditions, p_medications, p_surgeries, p_allergies)` | `submit_self_reported_baseline(p_conditions text[], p_allergies text[])` | Follow **DECISIONS D7**: Self-reported baseline is restricted to `conditions` and `allergies` while `is_doctor_verified = false`. Medications and surgeries are structured clinical JSON arrays managed by approved clinicians. |

---

## 2. Server Component Data Loading Architecture

### 2.1 File Location
- **Path**: `src/app/portal/patient/page.tsx`
- **Execution Environment**: Next.js App Router Server Component (`async function`)

### 2.2 Security & Authentication Workflow
1. **Identify Caller (Invariant N3)**:
   Must strictly use `const { data: { user }, error: authError } = await supabase.auth.getUser()`.
   Never use `getSession()` (which relies on unverified cookie claims).
2. **Unauthenticated Redirection**:
   If `!user || authError`, immediately issue `redirect('/login?next=/portal/patient')`.
3. **Role Verification & Redirection Guard**:
   Query `accounts` for `role, doctor_status`.
   If `account.role === 'doctor'`:
   - If `account.doctor_status === 'approved'`: redirect to `/portal/doctor`
   - If `account.doctor_status !== 'approved'`: redirect to `/portal/doctor/pending`
4. **Anon Key Isolation (Invariant N4)**:
   Instantiate client using `createClient()` from `@/lib/supabase/server`, using `NEXT_PUBLIC_SUPABASE_ANON_KEY` only. Zero `service_role` usage.

### 2.3 Parallel Data Fetching Design
To eliminate network waterfalls, data queries are executed concurrently via `Promise.all`:

```typescript
const [accountRes, profileRes, clinicalRes] = await Promise.all([
  supabase
    .from('accounts')
    .select('id, email, role, full_name, contact_phone, created_at, updated_at')
    .eq('id', user.id)
    .single(),
  supabase
    .from('patient_profiles')
    .select('patient_id, patient_code, qr_token, age, blood_group, emergency_contact_name, emergency_contact_phone, emergency_contact_relation, spouse_dependents, residential_address, created_at, updated_at')
    .eq('patient_id', user.id)
    .single(),
  supabase
    .from('clinical_records')
    .select('patient_id, medical_conditions, current_medication, previous_surgeries, allergies, is_doctor_verified, last_updated_by_doctor_id, last_appointment_date, last_appointment_summary, created_at, updated_at')
    .eq('patient_id', user.id)
    .single(),
]);
```

### 2.4 Complete Blueprint: `src/app/portal/patient/page.tsx`

```tsx
import React, { Suspense } from 'react';
import type { Metadata } from 'next';
import { redirect } from 'next/navigation';
import { createClient } from '@/lib/supabase/server';
import type {
  AccountRow,
  PatientProfileRow,
  ClinicalRecordRow,
  SpouseDependent,
  MedicationItem,
  SurgeryItem,
} from '@/lib/supabase/types';
import { PatientPortalClient } from '@/components/patient/patient-portal-client';
import { Card, CardContent } from '@/components/ui/card';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

export const metadata: Metadata = {
  title: 'Patient Medical ID Portal — Umbrella',
  description: 'Manage emergency ID credentials, vital medical demographics, and baseline health records.',
};

/**
 * Server Component: Entry point for /portal/patient
 * Complies with AGENTS.md N1-N10 & DECISIONS.md D1-D15
 */
export default async function PatientPortalPage() {
  const supabase = createClient();

  // 1. Invariant N3: Identify caller strictly with auth.getUser()
  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (!user || authError) {
    redirect('/login?next=/portal/patient');
  }

  // 2. Fetch Account, Profile, and Clinical Record concurrently
  const [accountRes, profileRes, clinicalRes] = await Promise.all([
    supabase
      .from('accounts')
      .select('id, email, role, full_name, contact_phone, created_at, updated_at')
      .eq('id', user.id)
      .single(),
    supabase
      .from('patient_profiles')
      .select(
        'patient_id, patient_code, qr_token, age, blood_group, emergency_contact_name, emergency_contact_phone, emergency_contact_relation, spouse_dependents, residential_address, created_at, updated_at'
      )
      .eq('patient_id', user.id)
      .single(),
    supabase
      .from('clinical_records')
      .select(
        'patient_id, medical_conditions, current_medication, previous_surgeries, allergies, is_doctor_verified, last_updated_by_doctor_id, last_appointment_date, last_appointment_summary, created_at, updated_at'
      )
      .eq('patient_id', user.id)
      .single(),
  ]);

  // Handle Account Fetch Error
  if (accountRes.error || !accountRes.data) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center p-6">
        <Card className="max-w-md w-full border-clinical-critical/20 bg-surface shadow-ceiling p-6 text-center">
          <AlertCircle className="mx-auto h-10 w-10 text-clinical-critical mb-3" />
          <h2 className="text-lg font-semibold text-text-primary">Account Profile Unavailable</h2>
          <p className="text-sm text-text-body-secondary mt-1">
            Unable to retrieve your identity profile. Please verify your connection or sign in again.
          </p>
          <div className="mt-5">
            <a href="/login">
              <Button variant="primary">Return to Sign In</Button>
            </a>
          </div>
        </Card>
      </div>
    );
  }

  const account = accountRes.data as AccountRow;

  // Role Gate: Redirect physicians away from patient portal
  if (account.role === 'doctor') {
    redirect('/portal/doctor');
  }

  // Handle Profile Fetch Failure (Self-healing fallback if trigger was delayed)
  if (profileRes.error || !profileRes.data) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center p-6">
        <Card className="max-w-md w-full border-clinical-pending/30 bg-surface shadow-ceiling p-6 text-center">
          <RefreshCw className="mx-auto h-10 w-10 text-clinical-pending-text mb-3 animate-spin" />
          <h2 className="text-lg font-semibold text-text-primary">Profile Initializing</h2>
          <p className="text-sm text-text-body-secondary mt-1">
            Your emergency profile record is being prepared. Please refresh in a moment.
          </p>
          <div className="mt-5">
            <a href="/portal/patient">
              <Button variant="secondary">Refresh Page</Button>
            </a>
          </div>
        </Card>
      </div>
    );
  }

  const profile = profileRes.data as PatientProfileRow;

  // Clinical record fallback (if empty record not yet generated)
  const clinical: ClinicalRecordRow = (clinicalRes.data as ClinicalRecordRow) || {
    patient_id: user.id,
    medical_conditions: [],
    current_medication: [],
    previous_surgeries: [],
    allergies: [],
    is_doctor_verified: false,
    last_updated_by_doctor_id: null,
    last_appointment_date: null,
    last_appointment_summary: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  // Safely parse JSON arrays conforming to domain schemas
  const parsedDependents: SpouseDependent[] = Array.isArray(profile.spouse_dependents)
    ? (profile.spouse_dependents as unknown as SpouseDependent[])
    : [];

  const parsedMedications: MedicationItem[] = Array.isArray(clinical.current_medication)
    ? (clinical.current_medication as unknown as MedicationItem[])
    : [];

  const parsedSurgeries: SurgeryItem[] = Array.isArray(clinical.previous_surgeries)
    ? (clinical.previous_surgeries as unknown as SurgeryItem[])
    : [];

  return (
    <main className="min-h-screen bg-canvas py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      <PatientPortalClient
        account={account}
        profile={{
          ...profile,
          spouse_dependents: parsedDependents,
        }}
        clinical={{
          ...clinical,
          current_medication: parsedMedications,
          previous_surgeries: parsedSurgeries,
        }}
      />
    </main>
  );
}
```

---

## 3. Server Actions & Mutations Architecture

### 3.1 File Location
- **Path**: `src/app/portal/patient/actions.ts`
- **Directive**: `'use server'`

### 3.2 Common Response Types & Error Formatting

```typescript
export type ActionSuccess<T = unknown> = {
  ok: true;
  data: T;
};

export type ActionFailure = {
  ok: false;
  error: string;
  fieldErrors?: Record<string, string>;
};

export type ActionResponse<T = unknown> = ActionSuccess<T> | ActionFailure;
```

### 3.3 Mutation 1: `updateDemographicsAction`
- **Objective**: Validates user inputs with Zod, writes updated full name / contact phone to `public.accounts`, and writes demographic attributes, emergency contact, residential address, and spouse/dependents to `public.patient_profiles`.
- **Authorization / RBAC**:
  - `accounts_update_self` RLS policy (`id = auth.uid()`)
  - `grant update (full_name, contact_phone) on accounts`
  - `pp_update_self` RLS policy (`patient_id = auth.uid()`)
  - `grant update (age, blood_group, emergency_contact_name, emergency_contact_phone, emergency_contact_relation, spouse_dependents, residential_address) on patient_profiles`
  - Token and patient code remain immutable per DB grant security.
- **Revalidation**: `revalidatePath('/portal/patient')`

### 3.4 Mutation 2: `submitBaselineAction`
- **Objective**: Patient submits self-reported medical conditions and allergies.
- **RPC Invocation**: `supabase.rpc('submit_self_reported_baseline', { p_conditions, p_allergies })`
- **Security Definer Enforcement**:
  - Function executes with `SECURITY DEFINER` and checks `is_doctor_verified = false`.
  - If array length > 50, raises exception `'Too many entries'`.
  - If `is_doctor_verified = true`, UPDATE finds 0 rows and raises exception: `'Record is already doctor-verified, or no patient profile exists'`.
- **Friendly Error Translation**:
  When Postgres returns the `'doctor-verified'` exception, the server action catches it and returns:
  `"This clinical record has been verified by a licensed physician and can no longer be self-edited. Please contact your healthcare provider to record updates."`
- **Revalidation**: `revalidatePath('/portal/patient')`

### 3.5 Mutation 3: `rotateQrTokenAction`
- **Objective**: Rotates patient's emergency QR token to a newly generated UUID, immediately invalidating physical prints in the wild.
- **RPC Invocation**: `supabase.rpc('regenerate_qr_token')`
- **Revalidation**: `revalidatePath('/portal/patient')`

### 3.6 Complete Blueprint: `src/app/portal/patient/actions.ts`

```typescript
'use server';

import { revalidatePath } from 'next/cache';
import { createClient } from '@/lib/supabase/server';
import {
  updateDemographicsSchema,
  baselineSubmissionSchema,
  type UpdateDemographicsInput,
  type BaselineSubmissionInput,
} from '@/lib/schemas';
import type { ActionResponse } from '@/lib/types';
import type { Json } from '@/lib/supabase/types';

/**
 * Server Action: Update patient demographics and account details
 * Bound to updateDemographicsSchema in src/lib/schemas.ts
 */
export async function updateDemographicsAction(
  rawData: unknown
): Promise<ActionResponse<{ message: string }>> {
  try {
    const supabase = createClient();

    // 1. Authenticate caller strictly via getUser() per Invariant N3
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (!user || authError) {
      return {
        ok: false,
        error: 'Unauthorized. Your session has expired; please sign in again.',
      };
    }

    // 2. Normalize and validate input against Zod schema
    const parseResult = updateDemographicsSchema.safeParse(rawData);
    if (!parseResult.success) {
      const fieldErrors: Record<string, string> = {};
      parseResult.error.errors.forEach((err) => {
        const key = err.path.join('.');
        fieldErrors[key] = err.message;
      });

      return {
        ok: false,
        error: parseResult.error.errors[0]?.message || 'Validation failed. Please review the highlighted fields.',
        fieldErrors,
      };
    }

    const data = parseResult.data;

    // 3. Update public.accounts (full_name, contact_phone)
    const { error: accountError } = await supabase
      .from('accounts')
      .update({
        full_name: data.fullName,
        contact_phone: data.contactPhone || '',
      })
      .eq('id', user.id);

    if (accountError) {
      return {
        ok: false,
        error: `Failed to update identity record: ${accountError.message}`,
      };
    }

    // 4. Update public.patient_profiles
    const { error: profileError } = await supabase
      .from('patient_profiles')
      .update({
        age: data.age,
        blood_group: data.bloodGroup,
        emergency_contact_name: data.emergencyContactName,
        emergency_contact_phone: data.emergencyContactPhone,
        emergency_contact_relation: data.emergencyContactRelation,
        residential_address: data.residentialAddress || '',
        spouse_dependents: (data.spouseDependents || []) as unknown as Json,
      })
      .eq('patient_id', user.id);

    if (profileError) {
      return {
        ok: false,
        error: `Failed to update demographic profile: ${profileError.message}`,
      };
    }

    // 5. Invalidate Next.js cache to trigger fresh Server Component rendering
    revalidatePath('/portal/patient');

    return {
      ok: true,
      data: { message: 'Profile details saved successfully.' },
    };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'An unexpected error occurred.';
    return { ok: false, error: message };
  }
}

/**
 * Server Action: Submit self-reported medical baseline
 * Bound to baselineSubmissionSchema & RPC submit_self_reported_baseline
 */
export async function submitBaselineAction(
  rawData: unknown
): Promise<ActionResponse<{ message: string }>> {
  try {
    const supabase = createClient();

    // 1. Authenticate caller strictly via getUser()
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (!user || authError) {
      return {
        ok: false,
        error: 'Unauthorized. Your session has expired; please sign in again.',
      };
    }

    // 2. Validate input against baseline schema
    const parseResult = baselineSubmissionSchema.safeParse(rawData);
    if (!parseResult.success) {
      const fieldErrors: Record<string, string> = {};
      parseResult.error.errors.forEach((err) => {
        const key = err.path.join('.');
        fieldErrors[key] = err.message;
      });

      return {
        ok: false,
        error: parseResult.error.errors[0]?.message || 'Invalid medical baseline submission.',
        fieldErrors,
      };
    }

    const { conditions, allergies } = parseResult.data;

    // 3. Execute Security Definer RPC
    const { error: rpcError } = await supabase.rpc('submit_self_reported_baseline', {
      p_conditions: conditions,
      p_allergies: allergies,
    });

    if (rpcError) {
      // Invariant D7 / Rule 7: Translate verification lockout into clear patient messaging
      if (
        rpcError.message.includes('doctor-verified') ||
        rpcError.message.includes('Record is already doctor-verified')
      ) {
        return {
          ok: false,
          error:
            'This medical baseline has been officially verified by a healthcare provider and can no longer be self-edited. Please consult your physician for updates.',
        };
      }

      if (rpcError.message.includes('Too many entries')) {
        return {
          ok: false,
          error: 'Maximum 50 conditions and 50 allergies permitted per submission.',
        };
      }

      return {
        ok: false,
        error: `Submission failed: ${rpcError.message}`,
      };
    }

    // 4. Revalidate cache
    revalidatePath('/portal/patient');

    return {
      ok: true,
      data: { message: 'Medical baseline updated successfully.' },
    };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'An unexpected error occurred.';
    return { ok: false, error: message };
  }
}

/**
 * Server Action: Regenerate active QR emergency token (DECISIONS D3)
 * Invalidates previous QR codes immediately in the database.
 */
export async function rotateQrTokenAction(): Promise<ActionResponse<{ qrToken: string; message: string }>> {
  try {
    const supabase = createClient();

    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (!user || authError) {
      return {
        ok: false,
        error: 'Unauthorized. Please sign in again.',
      };
    }

    const { data: newToken, error: rpcError } = await supabase.rpc('regenerate_qr_token');

    if (rpcError) {
      return {
        ok: false,
        error: `Failed to rotate QR token: ${rpcError.message}`,
      };
    }

    revalidatePath('/portal/patient');

    return {
      ok: true,
      data: {
        qrToken: newToken,
        message: 'Emergency QR code successfully rotated. Previous physical copies are now invalid.',
      },
    };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'An unexpected error occurred.';
    return { ok: false, error: message };
  }
}
```

---

## 4. Zod Schema Bindings (`src/lib/schemas.ts`)

To ensure seamless integration between client form validation and server action validation, `src/lib/schemas.ts` will be updated with `updateDemographicsSchema`:

```typescript
/**
 * Combined Demographics Update Schema
 * Extends patientProfileSchema with accounts table fields (fullName, contactPhone)
 */
export const updateDemographicsSchema = z.object({
  fullName: z
    .string()
    .trim()
    .min(2, 'Full name must be at least 2 characters')
    .max(100, 'Full name cannot exceed 100 characters'),
  contactPhone: z
    .string()
    .trim()
    .regex(phoneRegex, 'Please provide a valid contact phone number')
    .optional()
    .or(z.literal('')),
  age: z.coerce
    .number({ invalid_type_error: 'Age must be a whole number' })
    .int('Age must be a whole number')
    .min(0, 'Age cannot be negative')
    .max(130, 'Age cannot exceed 130'),
  bloodGroup: bloodGroupEnum,
  emergencyContactName: z
    .string()
    .trim()
    .min(2, 'Emergency contact name is required')
    .max(100, 'Name cannot exceed 100 characters'),
  emergencyContactPhone: z
    .string()
    .trim()
    .regex(phoneRegex, 'Emergency contact phone number must be valid'),
  emergencyContactRelation: z
    .string()
    .trim()
    .min(1, 'Relationship is required')
    .max(50, 'Relationship cannot exceed 50 characters'),
  residentialAddress: z
    .string()
    .trim()
    .max(255, 'Residential address cannot exceed 255 characters')
    .default(''),
  spouseDependents: z.array(spouseDependentSchema).max(10, 'Maximum 10 dependents allowed').default([]),
});

export type UpdateDemographicsInput = z.infer<typeof updateDemographicsSchema>;
```

---

## 5. Disappearing Edit UI & Client State Integration (D3, D7)

### 5.1 Verification State Matrix
The clinical record display on the patient portal follows a strict two-state rendering model:

| Clinical Record State | Status Badge | Edit Form Visible? | Lock Notice Displayed | Available User Action |
|-----------------------|--------------|-------------------|----------------------|-----------------------|
| `is_doctor_verified === false` | Amber pill (`#8a5200`): **Self-Reported** | **YES** — Active condition/allergy tag editor and submit button | Informational: "Self-reported baseline. Will lock once certified by a doctor." | Submit or modify conditions and allergies |
| `is_doctor_verified === true` | Green pill (`#1d7a37`): **Verified by Physician** | **NO** — Completely unmounted from DOM (Disappearing Edit UI) | Safety Alert: "Clinical record verified by licensed clinician. Read-only." | Contact physician to record clinical adjustments |

### 5.2 Optimistic UI & Transition Management
Client components use `useTransition()` to manage pending states cleanly without layout shift:

```tsx
const [isPending, startTransition] = useTransition();

const handleSaveDemographics = (values: UpdateDemographicsInput) => {
  setErrorMessage(null);
  setSuccessMessage(null);

  startTransition(async () => {
    const result = await updateDemographicsAction(values);
    if (!result.ok) {
      setErrorMessage(result.error);
      if (result.fieldErrors) setFieldErrors(result.fieldErrors);
    } else {
      setSuccessMessage(result.data.message);
    }
  });
};
```

---

## 6. Verification and Compliance Matrix

| Rule / Requirement | Description | Implementation Status & Verification Method |
|--------------------|-------------|--------------------------------------------|
| **N1** | Zero address/dependents on public emergency view | `updateDemographicsAction` updates `residential_address` and `spouse_dependents` only in `patient_profiles`. Public RPC `get_emergency_triage_by_token` strictly excludes them. |
| **N3** | Security lives in Postgres; caller identified via `getUser()` | `page.tsx` and all actions in `actions.ts` call `supabase.auth.getUser()`. Never `getSession()`. |
| **N4** | Anon key only; zero service_role | Uses `createClient()` from `@/lib/supabase/server` referencing `NEXT_PUBLIC_SUPABASE_ANON_KEY`. |
| **N6** | QR value computed on client after mount | Origin concatenated client-side: `window.location.origin + '/emergency/' + profile.qr_token`. |
| **N10** | Strict Zod validation on client & server; no `any` | Dual-sided validation via `updateDemographicsSchema` and `baselineSubmissionSchema`. |
| **D5** | Age integer maintained in v1 | All schemas and DB updates bind to `age: number`. |
| **D7** | Self-reported baseline restricted to conditions & allergies | Calls `submit_self_reported_baseline(p_conditions, p_allergies)`. Catches doctor verification lock. |

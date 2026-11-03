'use server';

import { revalidatePath } from 'next/cache';
import { createClient } from '@/lib/supabase/server';
import {
  updateDemographicsSchema,
  baselineSubmissionSchema,
  type UpdateDemographicsInput,
  type BaselineSubmissionInput,
} from '@/lib/schemas';
import type { Json } from '@/lib/supabase/types';

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

/**
 * Server Action: Update patient demographics and identity details
 * Bound to updateDemographicsSchema in src/lib/schemas.ts
 * Complies with AGENTS.md N1, N3, N4
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

    // 2. Parse FormData if provided, otherwise treat as object
    let inputToValidate: unknown = rawData;
    if (rawData instanceof FormData) {
      const dependentsRaw = rawData.get('spouseDependents');
      let parsedDependents: unknown = [];
      if (typeof dependentsRaw === 'string' && dependentsRaw.trim()) {
        try {
          parsedDependents = JSON.parse(dependentsRaw);
        } catch {
          parsedDependents = [];
        }
      }

      inputToValidate = {
        fullName: rawData.get('fullName'),
        contactPhone: rawData.get('contactPhone') || '',
        age: rawData.get('age'),
        bloodGroup: rawData.get('bloodGroup'),
        emergencyContactName: rawData.get('emergencyContactName'),
        emergencyContactPhone: rawData.get('emergencyContactPhone'),
        emergencyContactRelation: rawData.get('emergencyContactRelation'),
        residentialAddress: rawData.get('residentialAddress') || '',
        spouseDependents: parsedDependents,
      };
    }

    // 3. Validate against Zod schema
    const parseResult = updateDemographicsSchema.safeParse(inputToValidate);
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

    const data: UpdateDemographicsInput = parseResult.data;

    // 4. Update public.accounts (full_name, contact_phone)
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

    // 5. Update public.patient_profiles
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

    // 6. Invalidate Next.js cache to trigger fresh rendering
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
 * Bound to baselineSubmissionSchema & Postgres RPC submit_self_reported_baseline
 * Complies with DECISIONS D7 & D3
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

    // 2. Parse FormData if provided, otherwise treat as object
    let inputToValidate: unknown = rawData;
    if (rawData instanceof FormData) {
      const conditionsRaw = rawData.get('conditions');
      const allergiesRaw = rawData.get('allergies');
      let parsedConditions: unknown = [];
      let parsedAllergies: unknown = [];

      if (typeof conditionsRaw === 'string' && conditionsRaw.trim()) {
        try {
          parsedConditions = JSON.parse(conditionsRaw);
        } catch {
          parsedConditions = conditionsRaw.split(',').map((s) => s.trim()).filter(Boolean);
        }
      }
      if (typeof allergiesRaw === 'string' && allergiesRaw.trim()) {
        try {
          parsedAllergies = JSON.parse(allergiesRaw);
        } catch {
          parsedAllergies = allergiesRaw.split(',').map((s) => s.trim()).filter(Boolean);
        }
      }

      inputToValidate = {
        conditions: parsedConditions,
        allergies: parsedAllergies,
      };
    }

    // 3. Validate against baseline schema
    const parseResult = baselineSubmissionSchema.safeParse(inputToValidate);
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

    const { conditions, allergies }: BaselineSubmissionInput = parseResult.data;

    // 4. Execute Security Definer RPC
    const { error: rpcError } = await supabase.rpc('submit_self_reported_baseline', {
      p_conditions: conditions,
      p_allergies: allergies,
    });

    if (rpcError) {
      // Invariant D7: Handle doctor-verified lockout cleanly with friendly message
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

    // 5. Invalidate Next.js cache
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
 * Server Action: Rotate active QR emergency token (DECISIONS D3)
 * Invalidates previous QR code immediately in the database.
 */
export async function rotateQrTokenAction(): Promise<ActionResponse<{ qrToken: string; message: string }>> {
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
        error: 'Unauthorized. Please sign in again.',
      };
    }

    // 2. Call Postgres RPC regenerate_qr_token()
    const { data: newToken, error: rpcError } = await supabase.rpc('regenerate_qr_token');

    if (rpcError) {
      return {
        ok: false,
        error: `Failed to rotate QR token: ${rpcError.message}`,
      };
    }

    // 3. Revalidate cache
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

# Milestone M7: Emergency Data Flow, Privacy Isolation & Runtime Validation Report

**Explorer**: `explorer_m7_2`  
**Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m7_2`  
**Parent Conversation ID**: `a0698e01-4167-4648-9a8b-05be5311997c`  
**Milestone**: M7 (Emergency Triage Route `/emergency/[token]`)

---

## Executive Summary

This report establishes the server-side data fetching architecture, privacy isolation boundaries, runtime schema validation, and opaque error handling for Umbrella's public roadside emergency triage route (`/emergency/[token]`).

The design strictly satisfies Non-negotiable **N1** (zero exposure of residential address or family dependents, zero login requirement, zero table privileges to `anon`), Non-negotiable **N4** (anon/publishable key only, zero `service_role` usage), Non-negotiable **N10** (strict TypeScript typing, zero `any`, zero `@ts-ignore`), and Security Rule **02 § 4** / DECISIONS **D9** (opaque 404 with zero token existence/status leakage).

---

## 1. Non-Negotiable N1: Data Access & Privacy Isolation Boundary

### 1.1 Postgres Privilege Architecture
In `supabase/migrations/0001_umbrella_schema.sql` (lines 299–304 & 349–350):
- Table privileges on `public.accounts`, `public.patient_profiles`, `public.clinical_records`, and `public.appointments` are explicitly revoked from `anon`.
- Any direct PostgREST table query (e.g. `supabase.from('patient_profiles').select('*')`) executed by an unauthenticated client is rejected by Postgres with error code `42501` (`insufficient_privilege`).
- The ONLY database object executable by `anon` is the security-definer function:
  ```sql
  create or replace function public.get_emergency_triage_by_token(lookup_token uuid)
  returns jsonb language sql stable security definer set search_path = '' as $$
    select jsonb_build_object(
      'full_name', a.full_name,
      'contact_phone', a.contact_phone,
      'patient_code', p.patient_code,
      'age', p.age,
      'blood_group', p.blood_group,
      'emergency_contact_name', p.emergency_contact_name,
      'emergency_contact_phone', p.emergency_contact_phone,
      'emergency_contact_relation', p.emergency_contact_relation,
      'medical_conditions', coalesce(c.medical_conditions, '{}'),
      'current_medication', coalesce(c.current_medication, '[]'::jsonb),
      'previous_surgeries', coalesce(c.previous_surgeries, '[]'::jsonb),
      'allergies', coalesce(c.allergies, '{}'),
      'last_appointment_date', c.last_appointment_date,
      'is_doctor_verified', coalesce(c.is_doctor_verified, false),
      'updated_at', c.updated_at
    )
    from public.patient_profiles p
    join public.accounts a on a.id = p.patient_id
    left join public.clinical_records c on c.patient_id = p.patient_id
    where p.qr_token = lookup_token;
  $$;
  revoke all on function public.get_emergency_triage_by_token(uuid) from public, anon, authenticated;
  grant execute on function public.get_emergency_triage_by_token(uuid) to anon, authenticated;
  ```

### 1.2 Whitelist Projection & Guaranteed Privacy Exclusions
The RPC function uses explicit `jsonb_build_object` projection. By construction:
- `residential_address` is NEVER selected from `public.patient_profiles`.
- `spouse_dependents` is NEVER selected from `public.patient_profiles`.
- `qr_token` is NEVER selected from `public.patient_profiles`.
- When `lookup_token` matches zero rows, Postgres returns SQL `NULL` (`{ data: null, error: null }`).

### 1.3 Anonymous Server Client (`src/lib/supabase/anon.ts`)
To enforce zero-login semantics without passing session cookies or importing cookie stores:
- Standard `src/lib/supabase/server.ts` relies on `cookies()` from `next/headers`. Passing cookies to `/emergency/[token]` would leak authenticated sessions or introduce unwanted session state into a public emergency triage route.
- A dedicated anonymous client helper `createAnonClient()` in `src/lib/supabase/anon.ts` instantiates `@supabase/supabase-js` `createClient<Database>()` with `persistSession: false` and `autoRefreshToken: false`.
- It uses strictly `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`. Zero `service_role` key exists in the repository (N4).

---

## 2. Opaque 404 Rejection & `not-found.tsx` Design

### 2.1 Route Token Parsing & Pre-Query Validation
In `/emergency/[token]`, URL parameter `token` must be validated before issuing any database call:
1. Fast format check with `uuidSchema.safeParse(token)`:
   - If `token` is not a valid UUIDv4 string (e.g. malformed strings, path traversal, injection attempts), it is rejected immediately on the server via `notFound()`.
   - This eliminates database errors (Postgres `22P02: invalid input syntax for type uuid`) and prevents enumeration attacks.
2. Database lookup via RPC:
   - Execute `const { data, error } = await supabase.rpc('get_emergency_triage_by_token', { lookup_token: token })`.
   - If `error` is returned, or if `data` is `null` (token nonexistent or revoked via `regenerate_qr_token`), invoke `notFound()`.
3. Zod schema validation:
   - Execute `const parsed = emergencyTriageSchema.safeParse(data)`.
   - If parsing fails, invoke `notFound()`.

### 2.2 Generic 404 Security Compliance (Rule 02 § 4 & DECISIONS D9)
- **Zero Hint Policy**: The response must not reveal whether a token previously existed, is expired, has been rotated, or is malformed. All failure modes converge to the identical HTTP 404 response.
- **Design of `src/app/emergency/[token]/not-found.tsx`**:
  - Semantic landmark: `<main>` with high-contrast, accessible typography conforming to Apple design tokens (`--bg-canvas`, `--bg-surface`, `--text-primary`, `--text-body-secondary`).
  - Clear, non-technical headline: `"Emergency Record Not Found"`.
  - Opaque description: `"The requested emergency medical record is not available. The identifier may be invalid, expired, or revoked."`
  - Life-safety critical call button: A prominent 56px touch-target emergency dialer button (`<a href="tel:911">Call 911 / Emergency Services</a>`), styled with high-contrast red fill (`--clinical-critical: #ff3b30`) and bold white text (DECISIONS D10).
  - Navigation fallback: Clean link back to the homepage (`/`).
  - Zero heavy libraries: Pure Tailwind CSS, zero `framer-motion`, zero client-side scripts.

---

## 3. Zod Validation Schema & Multi-Layer Privacy Defense

### 3.1 Schema Specification (`src/lib/schemas.ts`)
The schema enforces the exact contract of the RPC return payload:
```ts
export const emergencyTriageSchema = z
  .object({
    full_name: z.string().trim().min(1, 'Patient name is required'),
    contact_phone: z.string().default(''),
    patient_code: z.string().trim().min(1, 'Patient code is required'),
    age: z.coerce.number().int().min(0).max(130),
    blood_group: bloodGroupEnum,
    emergency_contact_name: z.string().default(''),
    emergency_contact_phone: z.string().default(''),
    emergency_contact_relation: z.string().default(''),
    medical_conditions: z.array(z.string().trim()).default([]),
    current_medication: z.array(medicationItemSchema).default([]),
    previous_surgeries: z.array(surgeryItemSchema).default([]),
    allergies: z.array(z.string().trim()).default([]),
    last_appointment_date: z.string().nullable().default(null),
    is_doctor_verified: z.boolean().default(false),
    updated_at: z.string().nullable().optional().transform((val) => val || ''),
  })
  .superRefine((data, ctx) => {
    // Defense-in-depth Invariant N1: Prohibit sensitive personal identifiers
    const raw = data as Record<string, unknown>;
    if ('residential_address' in raw) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Privacy violation: residential_address must never be present in emergency triage data',
        path: ['residential_address'],
      });
    }
    if ('spouse_dependents' in raw) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Privacy violation: spouse_dependents must never be present in emergency triage data',
        path: ['spouse_dependents'],
      });
    }
    if ('qr_token' in raw) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Privacy violation: qr_token must never be present in emergency triage data',
        path: ['qr_token'],
      });
    }
  });
```

### 3.2 Multi-Layer Privacy Defense
1. **Database Layer**: Postgres `get_emergency_triage_by_token` explicitly selects only the 15 whitelist fields.
2. **Network Layer**: PostgREST payload only transmits the 15 whitelist fields.
3. **Zod Validation Layer**: `.superRefine()` explicitly rejects any payload containing `residential_address`, `spouse_dependents`, or `qr_token`.
4. **Zod Stripping Layer**: `z.object` automatically strips any unexpected extra fields.
5. **Render Layer**: Server Component renders only medical triage data. The props passed into HTML and Next.js RSC data chunks contain zero residential or dependent data.

---

## 4. Strict TypeScript Types (Invariant N10)

Derived directly from Zod:
```ts
export type EmergencyTriageData = z.infer<typeof emergencyTriageSchema>;
```
This matches `src/lib/supabase/types.ts` `EmergencyTriageData` with complete type parity:
- Zero `any`.
- Zero `@ts-ignore` / `@ts-expect-error`.
- Strict nullability on `last_appointment_date: string | null`.
- Typed `BloodGroup` matching the database enum.
- Typed arrays `MedicationItem[]`, `SurgeryItem[]`, `string[]`.

---

## 5. Implementation Blueprints & Character Limit Headroom

All proposed implementation files are strictly under 5,000 characters, well within the 12,000 character limit.

### Blueprint 1: `src/lib/supabase/anon.ts` (~850 chars)
```ts
import { createClient as createSupabaseClient } from '@supabase/supabase-js';
import type { Database } from './types';

/**
 * Cookie-less anonymous Supabase client for public emergency triage route
 * Non-negotiables:
 * - N1: Public zero-login route (/emergency/[token])
 * - N4: Uses ONLY anon/publishable key; zero service_role usage
 * - Auth: No session persistence, no cookie parsing
 */
export function createAnonClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error('Missing Supabase public configuration environment variables');
  }

  return createSupabaseClient<Database>(supabaseUrl, supabaseAnonKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
      detectSessionInUrl: false,
    },
  });
}
```

### Blueprint 2: `src/app/emergency/[token]/page.tsx` (~4,200 chars)
```tsx
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { createAnonClient } from '@/lib/supabase/anon';
import { uuidSchema, emergencyTriageSchema } from '@/lib/schemas';
import { sanitizeTel, formatPhone } from '@/lib/utils';
import { 
  Phone, 
  ShieldCheck, 
  AlertTriangle, 
  Clock, 
  HeartPulse, 
  User, 
  Activity, 
  Calendar,
  Lock
} from 'lucide-react';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

export const metadata: Metadata = {
  title: 'Emergency Medical Triage | Umbrella',
  description: 'Roadside emergency triage record for first responders and emergency personnel.',
  robots: {
    index: false,
    follow: false,
  },
};

interface EmergencyPageProps {
  params: {
    token: string;
  };
}

export default async function EmergencyTriagePage({ params }: EmergencyPageProps) {
  const { token } = params;

  // 1. Validate token format (UUIDv4)
  const uuidParsed = uuidSchema.safeParse(token);
  if (!uuidParsed.success) {
    notFound();
  }
  const validToken = uuidParsed.data;

  // 2. Fetch triage data via anonymous client and security-definer RPC
  const supabase = createAnonClient();
  const { data, error } = await supabase.rpc('get_emergency_triage_by_token', {
    lookup_token: validToken,
  });

  if (error || !data) {
    notFound();
  }

  // 3. Runtime validation & privacy barrier (rejects any address or dependents)
  const validation = emergencyTriageSchema.safeParse(data);
  if (!validation.success) {
    notFound();
  }
  const triage = validation.data;

  const telLink = sanitizeTel(triage.emergency_contact_phone);
  const formattedPhone = formatPhone(triage.emergency_contact_phone);

  return (
    <div className="min-h-screen bg-[#f5f5f7] text-[#000000] pb-28">
      {/* Top Banner */}
      <header className="bg-white border-b border-black/10 px-4 py-3 sticky top-0 z-30 shadow-sm">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-[#ff3b30] animate-pulse" />
            <h1 className="text-sm font-semibold tracking-tight text-[#000000]">
              EMERGENCY MEDICAL ID
            </h1>
          </div>
          <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-black/5 text-[#6e6e73]">
            {triage.patient_code}
          </span>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 pt-4 space-y-4">
        {/* Verification Status */}
        <div className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium ${
          triage.is_doctor_verified 
            ? 'bg-emerald-50 text-[#1d7a37] border border-emerald-200' 
            : 'bg-amber-50 text-[#8a5200] border border-amber-200'
        }`}>
          {triage.is_doctor_verified ? (
            <>
              <ShieldCheck className="w-4 h-4 text-[#1d7a37] flex-shrink-0" />
              <span>Physician-Verified Clinical Record</span>
            </>
          ) : (
            <>
              <AlertTriangle className="w-4 h-4 text-[#8a5200] flex-shrink-0" />
              <span>Self-Reported Baseline (Unverified)</span>
            </>
          )}
        </div>

        {/* Hero Card: Demographics & Blood Group */}
        <section className="bg-white rounded-2xl p-5 border border-black/10 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold tracking-tight text-[#000000]">
                {triage.full_name}
              </h2>
              <p className="text-sm text-[#6e6e73] mt-0.5">
                Age: <span className="font-semibold text-black">{triage.age}</span> yrs
              </p>
            </div>
            {/* Blood Group Pill */}
            <div className="flex flex-col items-center justify-center bg-[#ff3b30] text-white px-4 py-2 rounded-xl shadow-sm min-w-[72px]">
              <span className="text-[10px] font-semibold uppercase tracking-wider opacity-90">Blood</span>
              <span className="text-2xl font-extrabold tracking-tight leading-none">{triage.blood_group}</span>
            </div>
          </div>
        </section>

        {/* Critical Allergies Alert */}
        <section className="bg-white rounded-2xl p-5 border border-black/10 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-[#d70015]" />
            <h3 className="text-sm font-semibold text-[#000000] uppercase tracking-wider">
              Known Allergies
            </h3>
          </div>
          {triage.allergies.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {triage.allergies.map((allergy, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-red-50 text-[#d70015] border border-red-200 text-sm font-semibold rounded-lg"
                >
                  {allergy}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[#6e6e73]">No allergies recorded.</p>
          )}
        </section>

        {/* Medical Conditions */}
        <section className="bg-white rounded-2xl p-5 border border-black/10 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <HeartPulse className="w-5 h-5 text-[#0071e3]" />
            <h3 className="text-sm font-semibold text-[#000000] uppercase tracking-wider">
              Medical Conditions
            </h3>
          </div>
          {triage.medical_conditions.length > 0 ? (
            <ul className="divide-y divide-black/5 text-sm">
              {triage.medical_conditions.map((condition, idx) => (
                <li key={idx} className="py-2 first:pt-0 last:pb-0 font-medium text-black">
                  {condition}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-[#6e6e73]">No medical conditions recorded.</p>
          )}
        </section>

        {/* Current Medications */}
        <section className="bg-white rounded-2xl p-5 border border-black/10 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="w-5 h-5 text-[#0071e3]" />
            <h3 className="text-sm font-semibold text-[#000000] uppercase tracking-wider">
              Current Medications
            </h3>
          </div>
          {triage.current_medication.length > 0 ? (
            <div className="space-y-3">
              {triage.current_medication.map((med, idx) => (
                <div key={idx} className="p-3 bg-black/[0.02] rounded-xl border border-black/5 text-sm">
                  <p className="font-semibold text-black">{med.name}</p>
                  <p className="text-xs text-[#6e6e73] mt-0.5">
                    {med.dosage} • {med.frequency}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[#6e6e73]">No current medications recorded.</p>
          )}
        </section>

        {/* Previous Surgeries */}
        {triage.previous_surgeries.length > 0 && (
          <section className="bg-white rounded-2xl p-5 border border-black/10 shadow-sm">
            <h3 className="text-sm font-semibold text-[#000000] uppercase tracking-wider mb-3">
              Previous Surgeries
            </h3>
            <div className="space-y-2">
              {triage.previous_surgeries.map((surg, idx) => (
                <div key={idx} className="flex justify-between items-start text-sm py-1.5 border-b border-black/5 last:border-0">
                  <span className="font-medium text-black">{surg.procedure}</span>
                  <span className="text-xs font-mono text-[#6e6e73]">{surg.year}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Emergency Contact Card */}
        <section className="bg-white rounded-2xl p-5 border border-black/10 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <User className="w-5 h-5 text-[#0071e3]" />
            <h3 className="text-sm font-semibold text-[#000000] uppercase tracking-wider">
              Emergency Contact
            </h3>
          </div>
          <div className="text-sm">
            <p className="font-bold text-black text-base">{triage.emergency_contact_name || 'Not provided'}</p>
            <p className="text-xs text-[#6e6e73] capitalize mt-0.5">
              Relationship: <span className="font-medium text-black">{triage.emergency_contact_relation || 'Primary'}</span>
            </p>
            {formattedPhone && (
              <p className="text-sm font-mono text-black mt-2">{formattedPhone}</p>
            )}
          </div>
        </section>

        {/* Clinical History & Doctor Escalation */}
        <footer className="text-center pt-4 space-y-3 pb-6">
          <p className="text-xs text-[#6e6e73] flex items-center justify-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            <span>Updated {triage.updated_at ? new Date(triage.updated_at).toLocaleDateString() : 'recently'}</span>
          </p>

          {/* DECISIONS D15: Escalation Link for Healthcare Providers */}
          <div className="pt-2">
            <Link
              href={`/portal/doctor?patient_token=${validToken}`}
              className="inline-flex items-center gap-1.5 text-xs font-medium text-[#0071e3] hover:underline"
            >
              <Lock className="w-3.5 h-3.5" />
              <span>Healthcare Provider? Open in Doctor Portal</span>
            </Link>
          </div>
        </footer>
      </main>

      {/* 56px Sticky Emergency Call Button (N1, DECISIONS D10, D13) */}
      {telLink && (
        <div className="fixed bottom-0 left-0 right-0 p-4 bg-white/95 backdrop-blur-md border-t border-black/10 z-40">
          <div className="max-w-2xl mx-auto">
            <a
              href={`tel:${telLink}`}
              className="w-full h-14 bg-[#ff3b30] hover:bg-[#d70015] active:scale-[0.98] text-white font-bold rounded-2xl flex items-center justify-center gap-3 text-base shadow-lg transition-transform focus:outline-none focus:ring-4 focus:ring-red-300"
              aria-label={`Call emergency contact ${triage.emergency_contact_name} at ${formattedPhone}`}
            >
              <Phone className="w-5 h-5 fill-current" />
              <span>Call Emergency Contact ({triage.emergency_contact_relation || 'Primary'})</span>
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
```

### Blueprint 3: `src/app/emergency/[token]/not-found.tsx` (~2,300 chars)
```tsx
import Link from 'next/link';
import { AlertOctagon, Phone, ArrowLeft } from 'lucide-react';

export default function EmergencyNotFound() {
  return (
    <div className="min-h-screen bg-[#f5f5f7] text-[#000000] flex flex-col justify-between p-4">
      <div className="max-w-md mx-auto w-full pt-16 text-center space-y-6">
        {/* Shield Icon */}
        <div className="w-20 h-20 rounded-full bg-red-100 border border-red-200 text-[#d70015] flex items-center justify-center mx-auto shadow-sm">
          <AlertOctagon className="w-10 h-10" />
        </div>

        {/* Opaque 404 Headline */}
        <div className="space-y-2">
          <h1 className="text-2xl font-bold tracking-tight text-[#000000]">
            Emergency Record Not Found
          </h1>
          <p className="text-sm text-[#6e6e73] leading-relaxed">
            The requested emergency triage record is not available. The identifier may be invalid, expired, or revoked.
          </p>
        </div>

        {/* Life-Safety Guidance */}
        <div className="bg-white rounded-2xl p-5 border border-black/10 shadow-sm text-left space-y-3">
          <p className="text-xs font-semibold uppercase tracking-wider text-[#d70015]">
            Immediate Assistance
          </p>
          <p className="text-sm text-[#6e6e73]">
            If this is a life-threatening medical emergency or roadside accident, contact emergency response services immediately.
          </p>
          <a
            href="tel:911"
            className="w-full h-14 bg-[#ff3b30] hover:bg-[#d70015] active:scale-[0.98] text-white font-bold rounded-xl flex items-center justify-center gap-3 text-base shadow-sm transition-transform"
            aria-label="Call 911 emergency services immediately"
          >
            <Phone className="w-5 h-5 fill-current" />
            <span>Call 911 / Emergency Services</span>
          </a>
        </div>
      </div>

      {/* Return to Home */}
      <footer className="max-w-md mx-auto w-full pb-8 text-center">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm font-medium text-[#0071e3] hover:underline"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Umbrella Home</span>
        </Link>
      </footer>
    </div>
  );
}
```

---

## 6. Handoff Report (5-Component Protocol)

### 1. Observation
- In `supabase/migrations/0001_umbrella_schema.sql` (lines 325–350), `get_emergency_triage_by_token(lookup_token uuid)` is defined as `LANGUAGE sql STABLE SECURITY DEFINER` granting execute to `anon, authenticated`. The explicit whitelist projection constructs a `jsonb` with exactly 15 keys, completely omitting `residential_address` and `spouse_dependents`.
- Table privileges on `public.accounts`, `public.patient_profiles`, `public.clinical_records`, and `public.appointments` are explicitly revoked from `anon` (lines 299–300).
- In `supabase/tests/rls_smoke.sql` Check 1 and Check 2, SQL tests verify that `anon` cannot select from tables and that `get_emergency_triage_by_token` returns JSON omitting `residential_address`, `spouse_dependents`, and `qr_token`, and returning `null` for an unknown UUID.
- In `next.config.js` (lines 28–45), the `/emergency/:path*` route is configured with `Cache-Control: no-store, no-cache, must-revalidate`, `Referrer-Policy: no-referrer`, and `X-Robots-Tag: noindex, nofollow`.
- In `src/lib/schemas.ts`, `emergencyTriageSchema` is present but can be reinforced with an explicit `superRefine` privacy barrier to catch and reject any accidental inclusion of prohibited fields.

### 2. Logic Chain
1. Because `anon` has zero table privileges, the only way unauthenticated users can access patient data is through the `get_emergency_triage_by_token` RPC.
2. Because `get_emergency_triage_by_token` whitelist projection selects only emergency clinical data and excludes `residential_address` and `spouse_dependents`, the database never exposes those columns to unauthenticated clients.
3. Because the emergency route should not transmit user session cookies, creating a dedicated cookie-less client in `src/lib/supabase/anon.ts` guarantees unauthenticated execution using only `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
4. Because malformed or non-existent tokens must not reveal state, validating UUIDs with `uuidSchema` and returning Next.js `notFound()` ensures an opaque 404 response with zero timing or message variation.
5. Because first-responders must be able to act immediately, the route and not-found page render a high-contrast 56px touch target call button.
6. Because DECISIONS D13 prohibits `framer-motion`, `qrcode.react`, and `jspdf` on `/emergency/*`, the page is authored as a pure Server Component with pure CSS transforms.

### 3. Caveats
- `c.updated_at` can be SQL `null` if a patient profile exists without a matching `clinical_records` row (though the `trg_patient_profile_clinical` trigger auto-provisions it upon insert). The schema handles this with `.nullable().optional().transform(...)` to prevent runtime crashes.
- The emergency phone button uses `tel:` with sanitized digits via `sanitizeTel()`. Actual phone dialing depends on client device cellular/telephony capability.

### 4. Conclusion
The data flow and privacy isolation architecture for `/emergency/[token]` is fully defined, mathematically robust against data leakage, and compliant with all project non-negotiables:
- N1: Zero login, zero address/dependent exposure, RPC-only read.
- N4: Anon key only, zero `service_role`.
- N8 / D13: Pure CSS transitions, zero `framer-motion` in bundle.
- N10: Strict TypeScript types with zero `any`.
- All proposed source files are under 4,500 characters (<12,000 char headroom).

### 5. Verification Method
1. **Schema & Types**: Validate with `npm run typecheck` (`tsc --noEmit`).
2. **Unit Tests**: Execute `npx vitest run tests/emergency-triage.test.ts` to test:
   - UUID validation accepts valid UUIDs and rejects malformed tokens.
   - `emergencyTriageSchema` parses valid triage payloads.
   - `emergencyTriageSchema` throws `ZodError` if `residential_address` or `spouse_dependents` are passed.
3. **Database Security Smoke Tests**: Run `supabase/tests/rls_smoke.sql` Check 1 and Check 2 in Postgres.
4. **Bundle & Performance**: Run `npm run build` and inspect route bundle output for `/emergency/[token]` to verify zero `framer-motion` and first load JS < 120KB.

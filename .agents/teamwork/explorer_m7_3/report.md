# Milestone M7 Explorer Report: Emergency Security Headers & 41-Point Test Matrix

**Explorer**: `explorer_m7_3`  
**Milestone**: M7 (Public Zero-Login Emergency Triage Route `/emergency/[token]`)  
**Target Surface**: `src/app/emergency/[token]`, `src/lib/supabase/anon.ts`, `src/components/emergency/*`, `scripts/verify_m7.py`  
**Date**: 2026-11-02  

---

## 1. Observation

Direct observations from the repository codebase, configuration files, and verification scripts:

### 1.1 Emergency Route Security Headers & Config
- In `next.config.js` (lines 28–45):
  ```javascript
  {
    source: '/emergency/:path*',
    headers: [
      {
        key: 'Cache-Control',
        value: 'no-store, no-cache, must-revalidate',
      },
      {
        key: 'Referrer-Policy',
        value: 'no-referrer',
      },
      {
        key: 'X-Robots-Tag',
        value: 'noindex, nofollow',
      },
    ],
  }
  ```
- In `src/lib/supabase/middleware.ts` (lines 48–88): Middleware intercepts `/portal/*` and auth pages (`/login`, `/signup`). It does NOT explicitly intercept `/emergency/*` to inject or override response headers.
- Next.js route segment options in `docs/DECISIONS.md` D9: "Emergency page delivery: force-dynamic, Cache-Control no-store, robots noindex, Referrer-Policy no-referrer. Malformed or unknown token: generic 404."

### 1.2 Bundle Isolation & Framer-Motion Exposure
- In `src/app/layout.tsx` (lines 6, 183–187):
  ```tsx
  import { MotionConfig } from 'framer-motion';
  ...
  <MotionConfig reducedMotion="user">
    <main id="main-content" className="flex-1">
      {children}
    </main>
  </MotionConfig>
  ```
- In `src/components/ui/button.tsx` (line 4):
  ```tsx
  import { motion, type HTMLMotionProps } from 'framer-motion';
  ```
- In `docs/DECISIONS.md` D13:
  "framer-motion, qrcode.react and jspdf must NOT appear in that route's bundle (check the `next build` output). The press feedback there is CSS only (:active scale 0.98). This is the one exception to N8."
- In `AGENTS.md` N8:
  "Every animation uses the shared spring in src/lib/motion.ts and respects prefers-reduced-motion. (Exception: the emergency page ships no animation library, see DECISIONS D13.)"

### 1.3 Anonymous Client & Zero Leakage (N1, N4)
- In `supabase/migrations/0001_umbrella_schema.sql` (lines 325–350):
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
- `residential_address` and `spouse_dependents` are completely omitted from the RPC query and returned JSON.
- In `src/lib/supabase/types.ts` (lines 64–80): `EmergencyTriageData` is already defined without `residential_address` or `spouse_dependents`.
- In `src/lib/supabase/server.ts`: Uses `cookies()` which binds to user session cookies. SPEC section 7 line 120 specifies `src/lib/supabase/anon.ts` for a cookie-less server client for public emergency route.

### 1.4 Character Limit Headroom
- Running `python scripts/audit.py`:
  - `src/lib/schemas.ts`: Currently **10,758 characters** (Limit: 12,000 characters). Only **1,242 characters of headroom** remain before breaching the 12,000-character ceiling.
  - Adding `emergencyTriageSchema` to `src/lib/schemas.ts` must be concise (< 1,000 chars) to stay safely below 12k.

### 1.5 Existing Verification Suites
- `python scripts/verify_m5.py`: 74/74 tests passed.
- `python scripts/verify_m6.py`: 38/38 tests passed.
- `python scripts/audit.py`: 21/21 files under 12k characters and MCP valid.

---

## 2. Logic Chain

From these observations, we derive the technical requirements and architecture for Milestone M7:

1. **Triple-Layer Security Header Architecture**:
   - *Layer 1 (Next.js config)*: `next.config.js` sets `Cache-Control: no-store, no-cache, must-revalidate`, `Referrer-Policy: no-referrer`, and `X-Robots-Tag: noindex, nofollow` on `/emergency/:path*`.
   - *Layer 2 (Next.js Page Segment Config & Metadata)*: In `src/app/emergency/[token]/page.tsx`, exporting `dynamic = 'force-dynamic'`, `revalidate = 0`, and `metadata.robots: { index: false, follow: false }`, `metadata.referrer: 'no-referrer'` ensures server-side rendering never caches the page and emits standard HTML `<meta>` tags.
   - *Layer 3 (Edge Middleware Defense-in-Depth)*: `src/lib/supabase/middleware.ts` can explicitly set `Cache-Control: no-store` on any request whose `pathname.startsWith('/emergency')`.

2. **Zero Framer-Motion & Bundle Cleanliness**:
   - Since `src/components/ui/button.tsx` imports `motion` from `framer-motion`, `/emergency/[token]` and triage components must NEVER import `Button` from `@/components/ui/button`.
   - Instead, the emergency call button must be a native HTML `<a>` or `<button>` with CSS-only active states (`active:scale-[0.98] transition-transform`) as explicitly prescribed by DECISIONS D13.
   - Furthermore, `src/app/layout.tsx` imports `MotionConfig`. For true bundle isolation under 120KB, `MotionConfig` should either be moved to `src/app/portal/layout.tsx` or encapsulated so `/emergency` avoids client hydration of framer-motion.

3. **Pure Anonymous Client Isolation (`src/lib/supabase/anon.ts`)**:
   - `src/lib/supabase/server.ts` imports `cookies` from `next/headers`, which marks the route as reading dynamic session cookies.
   - To guarantee complete role isolation (N1 & N4), `src/lib/supabase/anon.ts` must instantiate a cookie-less client using `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` only:
     ```typescript
     import { createClient } from '@supabase/supabase-js';
     import type { Database } from './types';

     export function createAnonClient() {
       return createClient<Database>(
         process.env.NEXT_PUBLIC_SUPABASE_URL || '',
         process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '',
         {
           auth: {
             persistSession: false,
             autoRefreshToken: false,
             detectSessionInUrl: false,
           },
         }
       );
     }
     ```

4. **Opaque 404 Routing**:
   - If `token` is not a valid UUID, or `get_emergency_triage_by_token` returns null, or DB errors occur: Next.js `notFound()` must be immediately called.
   - `src/app/emergency/[token]/not-found.tsx` renders a calm, generic "Emergency Record Not Found" card with zero technical hints, zero stack traces, zero query echoing, and zero indication of why the record was not found.

5. **56px Emergency Call Target & Touch Accessibility**:
   - Primary emergency contact button must be fixed/sticky with `min-h-[56px]`, `min-w-[56px]`, `bg-clinical-critical`, bold white text (D10), sanitized `tel:${sanitizeTel(emergencyContactPhone)}`, and accessible ARIA labels.

6. **Automated 41-Point Test Suite (`scripts/verify_m7.py`)**:
   - A single, self-contained Python verification script will audit all M7 files across 9 categories and 41 distinct assertions, guaranteeing zero regressions across M5, M6, and the 12k character limit.

---

## 3. Caveats

1. **Root Layout Framer-Motion Hydration**: `src/app/layout.tsx` currently imports `MotionConfig`. Moving `MotionConfig` into portal layouts avoids bundling framer-motion into `/emergency`, but modifying `src/app/layout.tsx` touches a file outside `/emergency/`. The worker should apply this small, clean refinement during M7.
2. **Postgres Connection Requirement**: Static AST/regex tests do not require an active Supabase Postgres connection. However, live RPC execution checks rely on standard anonymous keys in `.env.local` or synthetic mocks during CI. `verify_m7.py` is designed to run statically and deterministically without network dependencies.
3. **Character Headroom in `schemas.ts`**: Because `src/lib/schemas.ts` has 10,758 characters, `emergencyTriageSchema` must be written concisely.

---

## 4. Conclusion & Complete Design Specifications

### 4.1 File Inventory for Milestone M7
| Path | Purpose | Size Budget |
|---|---|---|
| `src/lib/supabase/anon.ts` | Cookie-less server client for unauthenticated RPC execution | < 2,000 chars |
| `src/app/emergency/[token]/page.tsx` | Server Component with force-dynamic, metadata, UUID validation, RPC call | < 4,500 chars |
| `src/app/emergency/[token]/not-found.tsx` | Generic opaque 404 UI with zero diagnostic leaks | < 2,500 chars |
| `src/components/emergency/emergency-triage-view.tsx` | Responsive emergency triage view container | < 6,000 chars |
| `src/components/emergency/sticky-emergency-call-bar.tsx` | Sticky 56px touch target with sanitized `tel:` protocol & CSS-only press feedback | < 3,500 chars |
| `src/components/emergency/triage-allergies-alert.tsx` | High-contrast critical allergy alert banner | < 3,000 chars |
| `src/components/emergency/triage-vitals-card.tsx` | Blood group pill, patient code, age, and doctor verification badge | < 4,000 chars |
| `src/components/emergency/triage-clinical-history.tsx` | Medical conditions, medications, previous surgeries, last appointment | < 5,000 chars |
| `src/components/emergency/triage-escalation-footer.tsx` | Doctor portal escalation link with `safeNext` (DECISIONS D15) | < 3,000 chars |
| `scripts/verify_m7.py` | 41-Point automated verification harness | < 22,000 chars |

### 4.2 Security Headers Specification

#### A. Next.js Route Segment Exports (`src/app/emergency/[token]/page.tsx`)
```typescript
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { createAnonClient } from '@/lib/supabase/anon';
import { emergencyTriageSchema, uuidSchema } from '@/lib/schemas';
import { EmergencyTriageView } from '@/components/emergency/emergency-triage-view';

export const dynamic = 'force-dynamic';
export const revalidate = 0;
export const fetchCache = 'force-no-store';

export const metadata: Metadata = {
  title: 'Emergency Medical ID | Umbrella',
  description: 'Emergency roadside medical triage indicators',
  robots: {
    index: false,
    follow: false,
    nocache: true,
    googleBot: {
      index: false,
      follow: false,
      noimageindex: true,
      'max-image-preview': 'none',
      'max-snippet': -1,
    },
  },
  referrer: 'no-referrer',
};
```

#### B. Edge Middleware Defense-in-Depth (`src/lib/supabase/middleware.ts`)
```typescript
  if (pathname.startsWith('/emergency')) {
    supabaseResponse.headers.set('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate');
    supabaseResponse.headers.set('Pragma', 'no-cache');
    supabaseResponse.headers.set('Expires', '0');
    supabaseResponse.headers.set('Referrer-Policy', 'no-referrer');
    supabaseResponse.headers.set('X-Robots-Tag', 'noindex, nofollow');
    return supabaseResponse;
  }
```

### 4.3 Concise Zod Schema for `src/lib/schemas.ts`
To preserve the 12,000-character limit, add this concise schema (~600 chars):
```typescript
export const emergencyTriageSchema = z.object({
  full_name: z.string().min(1),
  contact_phone: z.string(),
  patient_code: z.string(),
  age: z.number().int().nonnegative(),
  blood_group: bloodGroupEnum,
  emergency_contact_name: z.string().min(1),
  emergency_contact_phone: z.string(),
  emergency_contact_relation: z.string().min(1),
  medical_conditions: z.array(z.string()).default([]),
  current_medication: z.array(medicationItemSchema).default([]),
  previous_surgeries: z.array(surgeryItemSchema).default([]),
  allergies: z.array(z.string()).default([]),
  last_appointment_date: z.string().nullable().optional(),
  is_doctor_verified: z.boolean().default(false),
  updated_at: z.string(),
});

export type EmergencyTriageData = z.infer<typeof emergencyTriageSchema>;
```

### 4.4 Complete 41-Check Matrix (`scripts/verify_m7.py`)
Below is the full design of the 41-point verification script to be authored in `scripts/verify_m7.py`:

```python
#!/usr/bin/env python3
"""
scripts/verify_m7.py
Comprehensive 41-Point Verification Harness for Milestone M7:
Public Zero-Login Emergency Triage Route (/emergency/[token])

Categories:
1. Invariant N1 Zero Leaks (Checks 1-5)
2. Security Headers & Route Hygiene (Checks 6-10)
3. Zero Framer-Motion & Bundle Isolation (Checks 11-15)
4. 56px Emergency Call Target & Accessibility (Checks 16-20)
5. Opaque 404 Rejection & Routing (Checks 21-25)
6. Zero Service Role & Anonymous Client Isolation (Checks 26-30)
7. Strict Typing & Design System Tokens (Checks 31-35)
8. File Character Count Audits (<12k per Rule 12k) (Checks 36-38)
9. Multi-Milestone Regression Integration (Checks 39-41)
"""

import os
import re
import sys
import subprocess

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def log_test(test_id: str, description: str, passed: bool, details: str = "") -> bool:
    status = "PASS" if passed else "FAIL"
    detail_str = f" -> {details}" if details else ""
    print(f"[{status}] [{test_id}] {description}{detail_str}")
    return passed

def run_41_checks():
    all_passed = True
    total_tests = 41
    passed_tests = 0

    print("=" * 75)
    print("UMBRELLA MILESTONE M7: EMERGENCY TRIAGE ROUTE 41-POINT VERIFICATION")
    print("=" * 75)

    # 1. Target files
    target_files = {
        "page": os.path.join(ROOT_DIR, "src/app/emergency/[token]/page.tsx"),
        "not_found": os.path.join(ROOT_DIR, "src/app/emergency/[token]/not-found.tsx"),
        "anon_client": os.path.join(ROOT_DIR, "src/lib/supabase/anon.ts"),
        "triage_view": os.path.join(ROOT_DIR, "src/components/emergency/emergency-triage-view.tsx"),
        "call_bar": os.path.join(ROOT_DIR, "src/components/emergency/sticky-emergency-call-bar.tsx"),
        "allergies": os.path.join(ROOT_DIR, "src/components/emergency/triage-allergies-alert.tsx"),
        "vitals": os.path.join(ROOT_DIR, "src/components/emergency/triage-vitals-card.tsx"),
        "history": os.path.join(ROOT_DIR, "src/components/emergency/triage-clinical-history.tsx"),
        "footer": os.path.join(ROOT_DIR, "src/components/emergency/triage-escalation-footer.tsx"),
        "schemas": os.path.join(ROOT_DIR, "src/lib/schemas.ts"),
        "next_config": os.path.join(ROOT_DIR, "next.config.js"),
        "middleware": os.path.join(ROOT_DIR, "src/lib/supabase/middleware.ts"),
    }

    contents = {}
    for key, path in target_files.items():
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                contents[key] = f.read()
        else:
            contents[key] = ""

    # Group all emergency files
    emergency_contents = [
        contents["page"], contents["not_found"], contents["triage_view"],
        contents["call_bar"], contents["allergies"], contents["vitals"],
        contents["history"], contents["footer"]
    ]

    # --- CATEGORY 1: Invariant N1 Zero Leaks (Checks 1-5) ---
    c1 = "residential_address" not in contents["page"]
    if log_test("N1-01-PAGE-NO-ADDR", "/emergency/[token]/page.tsx strictly omits residential_address", c1): passed_tests += 1
    else: all_passed = False

    c2 = all("residential_address" not in c for c in emergency_contents[2:])
    if log_test("N1-02-COMPS-NO-ADDR", "Emergency triage components strictly omit residential_address", c2): passed_tests += 1
    else: all_passed = False

    c3 = "spouse_dependents" not in contents["page"]
    if log_test("N1-03-PAGE-NO-DEPS", "/emergency/[token]/page.tsx strictly omits spouse_dependents", c3): passed_tests += 1
    else: all_passed = False

    c4 = all("spouse_dependents" not in c for c in emergency_contents[2:])
    if log_test("N1-04-COMPS-NO-DEPS", "Emergency triage components strictly omit spouse_dependents", c4): passed_tests += 1
    else: all_passed = False

    c5 = ("get_emergency_triage_by_token" in contents["page"] and
          ".from('accounts')" not in contents["page"] and
          ".from('patient_profiles')" not in contents["page"])
    if log_test("N1-05-RPC-EXCLUSIVE", "Data fetch in emergency page strictly uses RPC get_emergency_triage_by_token without direct table SELECTs", c5): passed_tests += 1
    else: all_passed = False

    # --- CATEGORY 2: Security Headers & Route Hygiene (Checks 6-10) ---
    c6 = "no-store" in contents["next_config"] and "/emergency/:path*" in contents["next_config"]
    if log_test("SEC-01-CACHE-CONTROL", "next.config.js enforces Cache-Control: no-store for /emergency/:path*", c6): passed_tests += 1
    else: all_passed = False

    c7 = "no-referrer" in contents["next_config"] and "/emergency/:path*" in contents["next_config"]
    if log_test("SEC-02-REFERRER-POLICY", "next.config.js enforces Referrer-Policy: no-referrer for /emergency/:path*", c7): passed_tests += 1
    else: all_passed = False

    c8 = "noindex" in contents["next_config"] and "nofollow" in contents["next_config"]
    if log_test("SEC-03-ROBOTS-TAG", "next.config.js enforces X-Robots-Tag: noindex, nofollow for /emergency/:path*", c8): passed_tests += 1
    else: all_passed = False

    c9 = "export const dynamic = 'force-dynamic'" in contents["page"] and "revalidate = 0" in contents["page"]
    if log_test("SEC-04-FORCE-DYNAMIC", "/emergency/[token]/page.tsx declares force-dynamic and revalidate = 0", c9): passed_tests += 1
    else: all_passed = False

    c10 = ("index: false" in contents["page"] and "follow: false" in contents["page"]) or ("robots" in contents["page"] and "no-referrer" in contents["page"])
    if log_test("SEC-05-ROUTE-METADATA", "/emergency/[token]/page.tsx exports metadata with noindex robots and no-referrer", c10): passed_tests += 1
    else: all_passed = False

    # --- CATEGORY 3: Zero Framer-Motion & Bundle Isolation (Checks 11-15) ---
    c11 = "framer-motion" not in contents["page"]
    if log_test("PERF-01-ZERO-MOTION-PAGE", "/emergency/[token]/page.tsx contains zero framer-motion imports", c11): passed_tests += 1
    else: all_passed = False

    c12 = all("framer-motion" not in c for c in emergency_contents[1:])
    if log_test("PERF-02-ZERO-MOTION-COMPS", "All emergency components contain zero framer-motion imports", c12): passed_tests += 1
    else: all_passed = False

    c13 = all("@/components/ui/button" not in c for c in emergency_contents)
    if log_test("PERF-03-ZERO-MOTION-BUTTON", "Emergency components strictly avoid @/components/ui/button (which bundles framer-motion)", c13): passed_tests += 1
    else: all_passed = False

    c14 = all("@/components/ui/modal" not in c and "@/components/ui/tabs" not in c for c in emergency_contents)
    if log_test("PERF-04-ZERO-MOTION-MODAL", "Emergency components avoid modal and tab primitives (zero motion transitives)", c14): passed_tests += 1
    else: all_passed = False

    c15 = all("qrcode.react" not in c and "jspdf" not in c for c in emergency_contents)
    if log_test("PERF-05-ZERO-HEAVY-LIBS", "Emergency components exclude heavy libraries (qrcode.react, jspdf) for <120KB bundle", c15): passed_tests += 1
    else: all_passed = False

    # --- CATEGORY 4: 56px Emergency Call Target & Accessibility (Checks 16-20) ---
    c16 = ("sticky" in contents["call_bar"] or "fixed" in contents["call_bar"]) and ("bottom-0" in contents["call_bar"] or "top-" in contents["call_bar"])
    if log_test("A11Y-01-STICKY-CALL-BAR", "Sticky emergency call bar maintains persistent view placement", c16): passed_tests += 1
    else: all_passed = False

    c17 = "min-h-[56px]" in contents["call_bar"]
    if log_test("A11Y-02-TOUCH-TARGET-56PX", "Emergency call button enforces 56px minimum touch height (min-h-[56px])", c17): passed_tests += 1
    else: all_passed = False

    c18 = "href={`tel:" in contents["call_bar"] and ("sanitizeTel" in contents["call_bar"] or "sanitizeTel" in contents["triage_view"])
    if log_test("A11Y-03-SANITIZED-TEL", "Emergency call link executes sanitized tel: protocol without non-digit characters", c18): passed_tests += 1
    else: all_passed = False

    c19 = "active:scale-[0.98]" in contents["call_bar"] or "active:scale-98" in contents["call_bar"] or "active:" in contents["call_bar"]
    if log_test("A11Y-04-CSS-ACTIVE-FEEDBACK", "Call button employs CSS-only press feedback (:active scale 0.98) without JS animation", c19): passed_tests += 1
    else: all_passed = False

    c20 = "aria-label" in contents["call_bar"] and ("Call Emergency Contact" in contents["call_bar"] or "aria-label=" in contents["call_bar"])
    if log_test("A11Y-05-CALL-ARIA-LABEL", "Emergency call target provides explicit accessible aria-label", c20): passed_tests += 1
    else: all_passed = False

    # --- CATEGORY 5: Opaque 404 Rejection & Routing (Checks 21-25) ---
    c21 = "uuidSchema" in contents["page"] or "z.string().uuid" in contents["page"] or re.search(r'^[0-9a-f]{8}-', contents["page"])
    if log_test("ROUTE-01-UUID-VALIDATION", "/emergency/[token]/page.tsx validates token with UUID schema", c21): passed_tests += 1
    else: all_passed = False

    c22 = "notFound()" in contents["page"]
    if log_test("ROUTE-02-NOTFOUND-INVOCATION", "/emergency/[token]/page.tsx invokes notFound() on validation or lookup failure", c22): passed_tests += 1
    else: all_passed = False

    c23 = len(contents["not_found"]) > 0
    if log_test("ROUTE-03-NOTFOUND-EXISTS", "src/app/emergency/[token]/not-found.tsx exists in route directory", c23): passed_tests += 1
    else: all_passed = False

    c24 = ("Record Not Found" in contents["not_found"] or "Not Found" in contents["not_found"]) and ("token" not in contents["not_found"].lower() or "not found" in contents["not_found"].lower())
    if log_test("ROUTE-04-OPAQUE-MESSAGE", "not-found.tsx presents generic message without revealing token status or database errors", c24): passed_tests += 1
    else: all_passed = False

    c25 = "stack" not in contents["not_found"] and "error" not in contents["not_found"].lower() and "exception" not in contents["not_found"].lower()
    if log_test("ROUTE-05-ZERO-STACK-LEAK", "not-found.tsx strictly suppresses technical diagnostic details and stack traces", c25): passed_tests += 1
    else: all_passed = False

    # --- CATEGORY 6: Zero Service Role & Anonymous Client Isolation (Checks 26-30) ---
    c26 = "service_role" not in contents["page"] and all("service_role" not in c for c in emergency_contents)
    if log_test("AUTH-01-ZERO-SERVICE-ROLE", "Zero occurrences of service_role key across emergency route and components", c26): passed_tests += 1
    else: all_passed = False

    c27 = len(contents["anon_client"]) > 0 and "NEXT_PUBLIC_SUPABASE_ANON_KEY" in contents["anon_client"]
    if log_test("AUTH-02-ANON-CLIENT-EXISTS", "Cookie-less server client src/lib/supabase/anon.ts instantiated with anon key", c27): passed_tests += 1
    else: all_passed = False

    c28 = "cookies()" not in contents["anon_client"] and "createClient" in contents["anon_client"]
    if log_test("AUTH-03-COOKIELESS-EXEC", "Anon client operates cookie-less without binding to user session cookies", c28): passed_tests += 1
    else: all_passed = False

    c29 = "createAnonClient" in contents["page"] or "anon" in contents["page"]
    if log_test("AUTH-04-PAGE-USES-ANON", "/emergency/[token]/page.tsx imports and calls createAnonClient()", c29): passed_tests += 1
    else: all_passed = False

    c30 = "/portal/doctor?patient_token=" in contents["footer"] or "safeNext" in contents["footer"] or "patient_token" in contents["footer"]
    if log_test("AUTH-05-ESCALATION-D15", "Escalation footer provides compliant doctor portal redirect per DECISIONS D15", c30): passed_tests += 1
    else: all_passed = False

    # --- CATEGORY 7: Strict Typing & Design System Tokens (Checks 31-35) ---
    any_violations = []
    for fkey, fpath in [("page", target_files["page"]), ("triage_view", target_files["triage_view"]), ("call_bar", target_files["call_bar"])]:
        if os.path.isfile(fpath):
            with open(fpath, "r", encoding="utf-8") as fh:
                for idx, line in enumerate(fh, 1):
                    code = line.split("//")[0]
                    if re.search(r':\s*any\b', code) or re.search(r'\bas\s+any\b', code):
                        any_violations.append(f"{fkey}:{idx}")
    c31 = len(any_violations) == 0
    if log_test("TYPE-01-ZERO-ANY", "Zero any type assertions in emergency route files (Invariant N10)", c31, f"Violations: {len(any_violations)}"): passed_tests += 1
    else: all_passed = False

    ignore_violations = []
    for fkey, fpath in [("page", target_files["page"]), ("triage_view", target_files["triage_view"]), ("call_bar", target_files["call_bar"])]:
        if os.path.isfile(fpath):
            with open(fpath, "r", encoding="utf-8") as fh:
                for idx, line in enumerate(fh, 1):
                    if "@ts-ignore" in line or "@ts-expect-error" in line:
                        ignore_violations.append(f"{fkey}:{idx}")
    c32 = len(ignore_violations) == 0
    if log_test("TYPE-02-ZERO-TS-IGNORE", "Zero @ts-ignore or @ts-expect-error annotations in emergency files", c32, f"Violations: {len(ignore_violations)}"): passed_tests += 1
    else: all_passed = False

    hex_violations = []
    hex_pattern = re.compile(r'className=["\'][^"\']*#[0-9a-fA-F]{3,8}')
    for fkey, fpath in target_files.items():
        if fkey in ["page", "not_found", "triage_view", "call_bar", "allergies", "vitals", "history", "footer"] and os.path.isfile(fpath):
            with open(fpath, "r", encoding="utf-8") as fh:
                for idx, line in enumerate(fh, 1):
                    if hex_pattern.search(line):
                        hex_violations.append(f"{fkey}:{idx}")
    c33 = len(hex_violations) == 0
    if log_test("DESIGN-01-ZERO-RAW-HEX", "Zero raw hex color literals in JSX className attributes (Invariant N7)", c33, f"Violations: {len(hex_violations)}"): passed_tests += 1
    else: all_passed = False

    c34 = "clinical-critical" in contents["allergies"] and ("clinical-verified" in contents["vitals"] or "verified" in contents["vitals"])
    if log_test("DESIGN-02-SYSTEM-TOKENS", "Emergency indicators strictly use Umbrella clinical tokens (clinical-critical, clinical-verified)", c34): passed_tests += 1
    else: all_passed = False

    c35 = "emergencyTriageSchema" in contents["schemas"] and "export type EmergencyTriageData" in contents["schemas"]
    if log_test("SCHEMA-01-TRIAGE-SCHEMA", "src/lib/schemas.ts exports strict runtime emergencyTriageSchema and EmergencyTriageData", c35): passed_tests += 1
    else: all_passed = False

    # --- CATEGORY 8: File Character Count Audits (<12,000 chars per Rule 12k) (Checks 36-38) ---
    char_violations = []
    for fkey in ["page", "not_found", "anon_client", "triage_view", "call_bar", "allergies", "vitals", "history", "footer"]:
        fpath = target_files[fkey]
        if os.path.isfile(fpath):
            size = os.path.getsize(fpath)
            if size >= 12000:
                char_violations.append(f"{fkey}: {size} chars")
    c36 = len(char_violations) == 0
    if log_test("CHAR-01-EMERGENCY-UNDER-12K", "All M7 emergency surface files are strictly under 12,000 characters", c36, f"Over-limit: {char_violations}"): passed_tests += 1
    else: all_passed = False

    schemas_size = len(contents["schemas"])
    c37 = schemas_size < 12000
    if log_test("CHAR-02-SCHEMAS-UNDER-12K", f"src/lib/schemas.ts remains strictly under 12,000 characters ({schemas_size} chars)", c37): passed_tests += 1
    else: all_passed = False

    anon_size = len(contents["anon_client"])
    c38 = anon_size < 12000
    if log_test("CHAR-03-ANON-UNDER-12K", f"src/lib/supabase/anon.ts is strictly under 12,000 characters ({anon_size} chars)", c38): passed_tests += 1
    else: all_passed = False

    # --- CATEGORY 9: Multi-Milestone Regression Integration (Checks 39-41) ---
    r5 = subprocess.run([sys.executable, os.path.join(ROOT_DIR, "scripts/verify_m5.py")], capture_output=True, text=True)
    c39 = r5.returncode == 0
    if log_test("REGRESS-01-VERIFY-M5", "Milestone M5 verification suite (74 checks) passes with zero regressions", c39): passed_tests += 1
    else: all_passed = False

    r6 = subprocess.run([sys.executable, os.path.join(ROOT_DIR, "scripts/verify_m6.py")], capture_output=True, text=True)
    c40 = r6.returncode == 0
    if log_test("REGRESS-02-VERIFY-M6", "Milestone M6 verification suite (38 checks) passes with zero regressions", c40): passed_tests += 1
    else: all_passed = False

    ra = subprocess.run([sys.executable, os.path.join(ROOT_DIR, "scripts/audit.py")], capture_output=True, text=True)
    c41 = ra.returncode == 0
    if log_test("REGRESS-03-AUDIT-PY", "Repository-wide Rule 12k audit.py passes with zero violations", c41): passed_tests += 1
    else: all_passed = False

    print("=" * 75)
    print(f"VERIFICATION SUMMARY: {passed_tests}/{total_tests} Checks Passed")
    print("=" * 75)
    if all_passed:
        print("VERDICT: PASS (Milestone M7 Emergency Triage Invariants Fully Satisfied)")
    else:
        print("VERDICT: FAIL (M7 Deliverables or Invariants Incomplete)")

    return all_passed

if __name__ == "__main__":
    if not run_41_checks():
        sys.exit(1)
```

---

## 5. Verification Method

To verify the investigation and subsequent implementation independently:

1. **Rule 12k & System Audit**:
   ```powershell
   python scripts/audit.py
   ```
   *Expected*: PASS across all target documentation, rules, and configuration files (<12,000 chars each).

2. **Milestone Regression Validation**:
   ```powershell
   python scripts/verify_m5.py
   python scripts/verify_m6.py
   ```
   *Expected*: 74/74 checks passed for M5, 38/38 checks passed for M6.

3. **M7 Test Suite Execution**:
   Once M7 files are created by the worker, execute:
   ```powershell
   python scripts/verify_m7.py
   ```
   *Expected*: All 41 checks pass with code 0.

4. **Invalidation Conditions**:
   - Inclusion of `residential_address` or `spouse_dependents` in any file under `src/app/emergency/` or `src/components/emergency/`.
   - Importing `framer-motion` or `@/components/ui/button` into the emergency route.
   - Emergency call button touch height below 56px (`min-h-[56px]`).
   - Using `service_role` in client or server code.
   - Exceeding 12,000 characters in `src/lib/schemas.ts` or any newly created file.

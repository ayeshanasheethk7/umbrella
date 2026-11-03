## 2026-11-01T20:07:06Z
You are Worker M4 (role: teamwork_worker).
Your working directory is: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m4

MANDATORY FIRST STEP:
Read c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md.
Read master PROJECT.md at: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\orchestrator\PROJECT.md.
Read database TypeScript types at: c:\Users\DELL\ayesha_pro\medi_qr\src\lib\supabase\types.ts.
Read rules: AGENTS.md, .agents/rules/01-design-system.md, .agents/rules/02-security-privacy.md, .agents/rules/03-typescript-nextjs.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

EXCLUSIVE WRITE OWNERSHIP:
- package.json
- tsconfig.json
- next.config.js
- tailwind.config.ts
- postcss.config.js
- src/lib/supabase/client.ts
- src/lib/supabase/server.ts
- src/lib/supabase/middleware.ts
- src/middleware.ts
- src/lib/motion.ts
- src/lib/schemas.ts
- src/lib/utils.ts
- src/app/layout.tsx
- src/app/page.tsx
- src/app/(auth)/login/page.tsx
- src/app/(auth)/signup/page.tsx
- src/app/auth/callback/route.ts
- src/components/ui/* (Button, Input, Card, Modal, Tabs, Badge)
- scripts/verify_m4.py

TASK REQUIREMENTS (Milestone M4: Zero-Mock Auth & App Shell Navigation):
1. Next.js App Router Scaffold & Configuration:
   - `package.json`: Fixed stack dependencies (@supabase/ssr, @supabase/supabase-js, react, react-dom, next, framer-motion, lucide-react, zod, qrcode.react, jspdf, tailwindcss, etc.). Scripts: dev, build, start, lint, typecheck, test, test:e2e.
   - `tsconfig.json`: Strict TypeScript with paths alias `@/*` pointing to `./src/*`.
   - `next.config.js`: Security headers (X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Referrer-Policy: strict-origin-when-cross-origin, Permissions-Policy).
   - `tailwind.config.ts`: Design system tokens (canvas #f5f5f7, surface #ffffff, text #000000, secondary #6e6e73, apple blue #0071e3, clinical red #ff3b30, clinical green #34c759).
2. Supabase SSR Client Suite:
   - `src/lib/supabase/client.ts`: `createBrowserClient` using process.env.NEXT_PUBLIC_SUPABASE_URL and process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY with Database generic type.
   - `src/lib/supabase/server.ts`: `createServerClient` using `cookies()` from `next/headers` with Database generic type.
   - `src/lib/supabase/middleware.ts`: updates session cookies, identifies user via `supabase.auth.getUser()` (never getSession per N3), and implements route protection (redirecting unauthorized users from `/portal/*` to `/login`).
   - `src/middleware.ts`: runs supabase middleware on protected routes.
3. Zero-Mock Auth Surfaces (N5):
   - `src/app/(auth)/login/page.tsx`:
     * Real `supabase.auth.signInWithPassword` call.
     * Zod validation (`loginSchema`), visible error banner on failure.
     * Redirect to `/portal/patient` or `/portal/doctor` based on account role.
   - `src/app/(auth)/signup/page.tsx`:
     * Tabs: "Patient" and "Doctor".
     * Real `supabase.auth.signUp` call with `data: { role, full_name, medical_license_number, specialization }`.
     * Zod validation, pending doctor notification on doctor signup ("Verification pending: Doctor accounts require manual verification per D1").
   - `src/app/auth/callback/route.ts`: route handler for code exchange.
4. App Shell & Public Home:
   - `src/app/layout.tsx`: Root HTML/body, Inter/system font, navigation header with Umbrella logo, active session indicators, Logout action calling `supabase.auth.signOut`.
   - `src/app/page.tsx`: Public portal with hero, emergency QR triage access, Patient portal gateway, and Doctor portal gateway.
5. Shared UI Atoms & Motion:
   - `src/lib/motion.ts`: exports `appleSpring` ({ type: "spring", stiffness: 120, damping: 20, mass: 1 }).
   - `src/lib/schemas.ts`: strict Zod schemas for login, patient signup, doctor signup, profile, emergency triage.
   - `src/lib/utils.ts`: `cn()` classnames helper, `safeNext(url)` redirect sanitizer against open redirect vulnerabilities.
   - `src/components/ui/`: reusable button (with loading spinner & 44px min touch target), input with label and error state, card, tabs, badge.
6. Verification:
   - Write and execute `scripts/verify_m4.py` checking syntax, type conformance, schema validation, and zero mock auth invariants.

OUTPUT:
- Write report to `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m4\report.md`.
- Write `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m4\handoff.md` with 5 components.
- Send completion message to orchestrator (conversation ID: 35ce3df7-e3d0-4998-8e4c-525735196d55).

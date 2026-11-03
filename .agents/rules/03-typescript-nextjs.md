---
trigger: glob
globs: src/**/*.{ts,tsx}
description: TypeScript strictness and Next.js/Supabase coding rules for Umbrella
---
# 03 TypeScript and Next.js

TypeScript
- tsconfig: strict + noUncheckedIndexedAccess. Use `import type`. Prefer `unknown` + zod over casts. Use `satisfies` for config objects.
- Discriminated unions for results and statuses; exhaustive switch with a `never` check. No enums (use `as const` unions).
- Named exports everywhere; default exports only for Next special files (page, layout, route, loading, error, not-found). No barrel files. No React.FC.
- Keep files under 300 lines; split by responsibility.

Next.js
- FIRST read the "next" version in package.json. Version 16 or newer: the request-interception file is src/proxy.ts exporting `proxy`. Version 15 or older: src/middleware.ts exporting `middleware`. The SPEC says middleware.ts; same job, same RBAC rules.
- params, searchParams, cookies() and headers() are Promises: always await them.
- /emergency/[token]/page.tsx: `export const dynamic = 'force-dynamic'`; metadata robots noindex; validate the token with zod uuid BEFORE any DB call.
- Fetch in Server Components. Avoid request waterfalls (Promise.all). Pass only needed fields to client components.
- Route layout exactly: (marketing), (auth), portal/patient, portal/doctor, emergency/[token].
- Add loading.tsx, error.tsx and not-found.tsx wherever a route fetches data.

Supabase clients
- createBrowserClient in src/lib/supabase/client.ts; createServerClient with the cookie getAll/setAll pattern in server.ts. Follow the installed @supabase/ssr README exactly. Always createClient<Database>.
- Never create a Supabase client at module top level in server code; create one per request.
- Identify the caller with auth.getUser(). The proxy also uses getUser() and then queries public.accounts for the role.

Forms and tests
- Controlled components + zod safeParse; map issues to field errors by path.
- Vitest for pure logic in src/lib/**; Playwright for user flows in e2e/.
- Comments explain why, not what.

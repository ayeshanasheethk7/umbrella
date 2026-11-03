# AGENTS.md: Umbrella (emergency medical ID platform)

Umbrella has three surfaces: a Patient portal, a Doctor portal, and a public
zero-login QR triage page (/emergency/[token]). It handles medical data:
treat every change as safety-relevant.

## 1. Source of truth: read in this order at the start of EVERY session
1. docs/PROGRESS.md: what is done, what is next, open questions
2. docs/DECISIONS.md: fixes to the spec. Wins over SPEC.md wherever they differ
3. docs/SPEC.md: the full spec. Before coding, read the sections the current phase names
4. This file, then .agents/rules/*
Installed skills are generic advice. If a skill conflicts with 1-3, follow 1-3 and say so.

## 2. Stack (fixed: do not swap or add alternatives)
Next.js App Router + TypeScript (strict) . React . Tailwind CSS . framer-motion . Supabase (Postgres, Auth, RLS) through @supabase/ssr and @supabase/supabase-js . qrcode.react . jspdf . zod . lucide-react . Vitest . Playwright . GitHub . Vercel.
Do not add a UI kit, CSS-in-JS, state library, ORM or form library without an entry in docs/DECISIONS.md.

## 3. Commands
npm run dev | typecheck (tsc --noEmit) | lint | test | test:e2e | build
A task is done only when typecheck, lint and build pass AND you have looked at the result running.

## 4. How you work
1. One phase at a time. The human says "Phase N"; do only that phase. Never start the next one.
2. Begin with a 3-line restatement of the goal and the list of files you will create or change. If anything is ambiguous or contradicts the spec, stop and ask ONE question. Do not guess.
3. Build real, working features. No placeholder buttons, no hard-coded demo data in the UI, no TODO/stub/"coming soon", no mock auth. If something cannot be built yet, say so in your report.
4. Verify, don't assume. Run the commands. For UI, open the running app (browser tool if available) at 375x667 and 1280x800 and check it. Report real results, including failures.
5. Finish by updating docs/PROGRESS.md (done, files touched, deviations, open questions, how the human can verify), commit, and STOP.
6. Small diffs. Do not refactor, rename or reformat code unrelated to the task. Do not delete files you did not create without asking.
7. If the same error repeats 3 times, stop. Summarise what you tried and offer 2 options.
8. Be concise in chat: results, not narration.

## 5. Non-negotiables (breaking any = failed task)
N1. /emergency/[token] never requires login. It reads data ONLY through the RPC get_emergency_triage_by_token. Residential address and spouse/dependents never appear there (not in the RPC output, not in the HTML, not in any JSON).
N2. The Doctor portal always shows a read-only banner with patient name, age, blood group and emergency contact while editing clinical data.
N3. Security lives in Postgres (RLS, grants, SECURITY DEFINER functions) and server code. Hiding a button is not security. Never trust a role sent by the client. Never authorise from user_metadata. In server code identify the caller with supabase.auth.getUser(), never getSession().
N4. v1 uses the anon/publishable key only. The service_role key must never appear in code, .env.example, logs, commits or chat.
N5. Zero mock auth: /login and /signup call supabase.auth.signInWithPassword and supabase.auth.signUp for real.
N6. The QR value is window.location.origin + '/emergency/' + qr_token, computed on the client after mount.
N7. Design tokens, spacing-by-route and motion come from .agents/rules/01-design-system.md. Never a white hairline on a white surface. No purple/neon gradients, no heavy shadows.
N8. Every animation uses the shared spring in src/lib/motion.ts and respects prefers-reduced-motion. (Exception: the emergency page ships no animation library, see DECISIONS D13.)
N9. Synthetic data only. Never put real personal or medical data in code, seeds, screenshots or chat.
N10. No `any`, no @ts-ignore/@ts-expect-error without a written reason, no non-null assertions on external data. Validate every form field and URL parameter with zod.

## 6. Code conventions
- Server Components by default. Add "use client" only for state, effects, browser APIs or framer-motion.
- Folder structure exactly as SPEC section 7. Shared UI in src/components/ui; domain components in qr/, patient/, doctor/.
- DB types live in src/lib/supabase/types.ts (generated). Never hand-edit; never use a column name that is not in it.
- Mutations return typed results {ok:true,data} | {ok:false,error}. Show human-readable errors in the UI.
- Every async view has loading, empty and error states. Every form has labels, inline validation, and a button disabled while submitting.
- Accessibility baseline: semantic landmarks, visible :focus-visible ring, 44px minimum touch target (56px for the emergency call button), colour is never the only signal, aria labels, prefers-reduced-motion honoured.
- UI text: plain English, no emojis, no lorem ipsum.

## 7. Git
Work on branch phase/<n>-<slug>. One commit per finished task, Conventional Commit messages. Commit only when typecheck, lint and build pass. Never push, force-push, merge or rewrite history: the human does that.

## 8. Ask before running
rm -rf (anything except .next or node_modules), git push, git reset --hard, supabase db reset/push/link, any SQL containing DROP or TRUNCATE, curl | sh, editing .env* or files outside this repo, installing a package not listed in section 2.

## 9. Slash workflows
/start-phase . /verify . /security-audit . /design-review (in .agents/workflows/)

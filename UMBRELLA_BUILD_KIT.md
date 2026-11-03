# Umbrella: Antigravity + Gemini 3.8 Flash Build Kit

Companion to *"Umbrella Master Technical Specification v2.0"*. Everything below is copy-paste ready. Skill names, install commands and file locations were checked against current docs. Where a menu label may differ in your Antigravity version, it is noted.

---

## Part 0: How this kit works (read first)

Gemini 3.8 Flash is fast and strong on long coding runs, but it stays accurate when three things are true:
1. **The always-on rules are short** (Antigravity caps each rules file at 12,000 characters).
2. **The heavy detail lives in files it re-reads on demand** (the spec, the decisions file, the progress ledger).
3. **The build is cut into phases with a hard stop after each one**, and each phase starts in a fresh conversation.

### The Six Layers

| Layer | Where | What it does | When the agent sees it |
|---|---|---|---|
| `AGENTS.md` | project root | Non-negotiables and working protocol | Always |
| `GEMINI.md` | project root | Antigravity-only extras (tiny) | Always |
| Rules | `.agents/rules/` | Design, security, TypeScript/Next, SQL rules | By file pattern |
| Workflows | `.agents/workflows/` | Slash commands (`/verify`, `/security-audit`...) | When you type them |
| Skills | `.agents/skills/` | Expert playbooks (installed + 2 custom) | Agent picks by description |
| Docs | `docs/` | SPEC (full spec), DECISIONS (fixes), PROGRESS (ledger) | When told to read them |

**Precedence when instructions disagree:**
`your latest message` > `docs/DECISIONS.md` > `docs/SPEC.md` > `AGENTS.md and rules` > `installed skills`.

### Quick start (do these in order):
1. Install the tools (1.1).
2. Create the Supabase project and GitHub repo (1.3, 1.4).
3. Scaffold the Next.js app (1.5). Do this before adding any kit files, because newer `create-next-app` versions can generate their own `AGENTS.md`.
4. Add the kit files from Parts 3 to 7 (`AGENTS.md`, `GEMINI.md`, rules, workflows, custom skills, docs).
5. Save your spec as `docs/SPEC.md` (1.6 lists two formatting fixes).
6. Install skills (Part 2).
7. Open the folder in Antigravity and select Gemini 3.8 Flash (1.2).
8. Paste the Phase 0 prompt (Part 8). One phase per conversation, always.

---

## Part 1: Environment setup

### 1.1 Tools to install

| Tool | Version | Check with |
|---|---|---|
| Node.js | 20.9 or newer (22 LTS recommended) | `node -v` |
| npm | ships with Node | `npm -v` |
| Git | any recent | `git --version` |
| Google Antigravity | current, signed in | open the app |
| GitHub, Supabase, Vercel accounts | free tiers are enough | log in once |
| Docker Desktop | optional (this kit tests RLS with plain SQL, so you can skip it) | |

> **Windows note:** use Git Bash or WSL2. If you use WSL2, keep the project inside the Linux filesystem (for example `~/projects/umbrella`), not under `/mnt/c/...`. Skills reportedly fail to load from Windows-mounted paths.

### 1.2 Antigravity settings
Open the `umbrella` folder as the workspace, then:
- **Model:** Gemini 3.8 Flash. It supports low / medium / high thinking and deliberately spends more tokens on long multi-step tasks, so on a small UI tweak you can lower the level. If your build exposes a thinking-level control: Medium by default, High for Phases 1, 3 and 10 (database, auth, security), Low for pure styling.
- **Conversation mode:** Planning for Phases 1, 3, 10, 11 (it produces a plan you approve first). Fast for the rest.
- **Terminal execution:** set to ask / request review, not auto-run. Put these on the deny list if your version has one: `rm -rf`, `git push`, `git reset --hard`, `supabase db reset`.
- **Browser tool:** allow it, restricted to `localhost`. The agent uses it to screenshot the app at phone and desktop sizes.
- **Turn off any auto-commit or auto-push option.**

*Menu names differ slightly between Antigravity versions. The intent matters: ask before running commands, never push automatically.*

### 1.3 Supabase project
1. Supabase dashboard > New project named `umbrella-dev`. Choose the region closest to your users (for India: Mumbai, `ap-south-1`). Save the database password in a password manager.
2. Authentication > Providers > Email: enabled. For development turn Confirm email OFF so signup logs the user in immediately. Turn it back ON before launch (the app must handle both, see DECISIONS D11).
3. Authentication > URL Configuration: Site URL `http://localhost:3000`. Add redirect URL `http://localhost:3000/**`. You add your Vercel URLs in Phase 11.
4. Project Settings > API: copy the Project URL and the anon / publishable key. Never copy or use the `service_role` key anywhere in this project.

### 1.4 GitHub repo
Create a private empty repo named `umbrella` (no README). Connect it after the scaffold:
```bash
git remote add origin https://github.com/<you>/umbrella.git
```

### 1.5 Scaffold the app (human does this, once)
```bash
npx create-next-app@latest umbrella --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm
```
Answer No to the React Compiler prompt. Then:
```bash
cd umbrella
git add -A && git commit -m "chore: scaffold next app"
```
Create `.env.local` (never committed; `create-next-app` already ignores `.env*`):
```env
NEXT_PUBLIC_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=YOUR-ANON-OR-PUBLISHABLE-KEY
```
The variable keeps the name `..._ANON_KEY` (as in the spec) even if you paste the newer publishable key.
If the scaffold generated its own `AGENTS.md` or `CLAUDE.md`, delete them. Ours replaces them.

### 1.6 Save the spec
Paste your whole Master Technical Specification into `docs/SPEC.md` verbatim, with two formatting repairs, because small formatting errors confuse agents:
- Delete the stray `s` line before the CSS tokens block, and wrap that block in a ` ```css ` fence.
- Wrap the folder tree in Section 7 in a ` ```text ` fence.

### 1.7 Habits that protect you
- **Fake data only:** invented names, phone numbers, allergies. Real health data needs a privacy and legal review first (India's DPDP Act treats this as sensitive personal data).
- **Never paste the service_role key or your DB password** into the agent chat.
- **One phase = one conversation = one branch = one commit review.** Read the diff before you merge.

---

## Part 2: Skills (what to install and why)

### 2.1 How skills work in Antigravity
A skill is a folder with a `SKILL.md`. Antigravity reads only each skill's short description at startup and loads the rest when a task matches. Project skills live in `<project>/.agents/skills/<name>/` (the older `.agent/skills/` still works). Global ones live in `~/.gemini/antigravity/skills/`. We install at project level so the setup is committed and reproducible.

### 2.2 Install script (run from the project root)
```bash
# 1) Apple design (web-oriented Human Interface Guidelines skill)
npx skills@latest add axiaoge2/apple-hig-designer --agent antigravity -y

# 2) Claude skills from Anthropic
npx skills@latest add anthropics/skills --skill frontend-design --agent antigravity -y
npx skills@latest add anthropics/skills --skill webapp-testing --agent antigravity -y

# 3) Vercel: React/Next best practices, web interface audit, component composition, deploy
npx skills@latest add vercel-labs/agent-skills --skill vercel-react-best-practices --agent antigravity -y
npx skills@latest add vercel-labs/agent-skills --skill web-design-guidelines --agent antigravity -y
npx skills@latest add vercel-labs/agent-skills --skill vercel-composition-patterns --agent antigravity -y
npx skills@latest add vercel-labs/agent-skills --skill deploy-to-vercel --agent antigravity -y

# 4) Supabase
npx skills@latest add supabase/agent-skills --skill supabase --agent antigravity -y
npx skills@latest add supabase/agent-skills --skill supabase-postgres-best-practices --agent antigravity -y

# 5) Matt Pocock (interactive: tick the skills listed in 2.3, choose Antigravity)
npx skills@latest add mattpocock/skills --agent antigravity
```
Then check: `ls .agents/skills`. If a flag is rejected in your CLI version, run `npx skills@latest --help`. If the Apple skill can't be found by the CLI, clone it:
```bash
git clone https://github.com/axiaoge2/apple-hig-designer .agents/skills/apple-hig-designer
```

### 2.3 Matt Pocock skills: which to tick
Skip `to-prd` (your spec is the PRD) and `triage` (team issue workflow).

| Skill | Use in Umbrella |
|---|---|
| `setup-matt-pocock-skills` | Run once (`/setup-matt-pocock-skills`). It asks where issues live: pick local markdown files unless you have the GitHub CLI logged in. It appends an "Agent skills" block to AGENTS.md. Afterwards check AGENTS.md is still under 12,000 characters. |
| `grill-with-docs` | Before changing scope: the agent interviews you against the spec instead of guessing. |
| `tdd` | Phase 1 (SQL policy tests) and any pure logic (lookup-query parser, QR card layout math). |
| `diagnose` | Disciplined bug-hunting loop when something breaks. |
| `zoom-out` | Re-orients the agent in a new conversation. |
| `improve-codebase-architecture` | Phase 10 cleanup pass. |

### 2.4 What each skill is for
| Group | Skill | Role in this project |
|---|---|---|
| Apple design | `apple-hig-designer` | Reference for Apple typography, spacing, materials, hierarchy. Reference only: it ships its own tokens and React samples, but the Umbrella tokens in rule 01 always win. |
| Claude | `frontend-design` | Composition, type hierarchy, avoiding generic "AI look". It pushes bold aesthetics; Umbrella is restrained Apple, so use it for craft, not for style direction. |
| Claude | `webapp-testing` | Playwright helper for checking flows in a real browser. |
| Web best practices | `vercel-react-best-practices` | Server Components, avoiding request waterfalls, bundle size. Vital for the emergency page. |
| Web design / UX audit | `web-design-guidelines` | Audits UI code against Vercel's current Web Interface Guidelines (accessibility, forms, focus, performance). Needs internet. Run via `/design-review`. |
| Web design | `vercel-composition-patterns` | Clean component APIs for the `ui/` primitives. |
| Deploy | `deploy-to-vercel` | Phase 11. Optional: the Vercel dashboard + GitHub import also works. |
| Backend | `supabase` | Auth with `@supabase/ssr`, RLS, migrations, `getUser` over `getSession`. |
| Backend | `supabase-postgres-best-practices` | RLS performance, indexes on policy columns, schema design. |
| Custom | `umbrella-supabase-rls` | Our exact SQL patterns for policies, grants, triggers, RPCs and the test harness (Part 6). |
| Custom | `umbrella-qr-card` | QR rendering, PNG/PDF card export, token rotation (Part 6). |

### 2.5 Safety and limits
- Skills are instructions and sometimes scripts. Before trusting one, open its `SKILL.md` and any `scripts/` folder. Commit `.agents/skills/` so any update shows up as a git diff.
- About 15 skills is the practical ceiling. More skills means more descriptions competing for attention.
- Don't enable auto-update on skills during the build. Update between phases.
- If a skill conflicts with `AGENTS.md`, `DECISIONS` or `SPEC`, the agent must follow ours and say so.

---

## Part 3: Agent-config layout
```text
umbrella/
├── AGENTS.md
├── GEMINI.md
├── docs/
│   ├── SPEC.md               # your spec, verbatim (1.6)
│   ├── DECISIONS.md          # Part 7: fixes to spec gaps and security holes
│   └── PROGRESS.md           # agent's ledger (starter text in Part 7)
├── .agents/
│   ├── rules/                # 01-design-system.md 02-security-privacy.md
│   │                         # 03-typescript-nextjs.md 04-supabase-sql.md
│   ├── workflows/            # start-phase.md verify.md security-audit.md design-review.md
│   └── skills/               # installed skills + umbrella-supabase-rls/ + umbrella-qr-card/
├── src/                      # exactly as SPEC section 7
├── supabase/
│   ├── migrations/0001_umbrella_schema.sql
│   ├── seed.sql
│   └── tests/rls_smoke.sql
├── .env.example
└── package.json
```

---

## Part 4: AGENTS.md (create at the project root)

```markdown
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
```

---

## Part 5: GEMINI.md, rules and workflows

### 5.1 GEMINI.md (project root, deliberately tiny)
In Antigravity, `GEMINI.md` takes precedence over `AGENTS.md`, so it must only add behaviour, never restate or contradict rules.

```markdown
# GEMINI.md: Antigravity-only extras

AGENTS.md is the single source of project rules. Read it first. This file only adds Antigravity-specific behaviour and never overrides AGENTS.md.

- Planning-mode phases (1, 3, 10, 11): produce the implementation plan first, list every file you will touch, and wait for approval before coding.
- Fast-mode phases: still restate the goal in 3 lines before editing.
- UI verification: use the browser tool on localhost at 375x667 and 1280x800 and attach the screenshots to your walkthrough.
- Think hard on RLS, auth redirects, token handling and anything in the emergency route. Keep reasoning short on mechanical edits.
- Do not narrate each step. Report: what changed, what you ran, what passed or failed, what is left.
- Never invent library APIs. If unsure about an API (Supabase, Next.js, framer-motion, qrcode.react, jspdf), read the installed package's types or README in node_modules before writing code.
```

### 5.2 Rules (`.agents/rules/`)

Each file stays far below the 12,000-character cap.

#### `.agents/rules/01-design-system.md`
```markdown
---
trigger: glob
globs: src/**/*.{ts,tsx,css}
description: Umbrella design system (Apple aesthetic). Tokens, spacing per route, motion, forbidden patterns.
---
# 01 Design system

## Tokens (single source: src/app/globals.css)
Define as CSS variables in :root and [data-theme="dark"], expose to Tailwind with @theme (Tailwind v4 is CSS-first; no tailwind.config.js unless needed).
Components use token-backed utilities, never raw hex.

Light (default)
- --bg-canvas #f5f5f7 | --bg-surface #ffffff | --bg-glass rgba(255,255,255,0.72)
- --text-primary #000000
- --text-secondary #86868b (large or decorative text ONLY)
- --text-body-secondary #6e6e73 (any text under 18px)
- --border-hairline 1px solid rgba(0,0,0,0.1)
- --accent-action #0071e3
- --clinical-critical #ff3b30 (fills, large bold text) | --clinical-critical-text #d70015 (small red text)
- --clinical-verified #34c759 (fill/icon) | --clinical-verified-text #1d7a37 (text)
- --clinical-pending #ff9f0a (fill) | --clinical-pending-text #8a5200 (text) (self-reported badge)

Dark (hero showcase sections only)
- canvas #000000 | surface #1d1d1f | glass rgba(0,0,0,0.72) | text #f5f5f7 | secondary #86868b | hairline 1px solid rgba(255,255,255,0.1)

Type
- --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif. No webfonts.
- Hero: weight 700, tracking -0.03em. Headings: weight 600, tracking -0.022em.

## Spacing by route (SPEC section 8 check 4)
| Route | Padding | Layout |
|---|---|---|
| / | 120-160px vertical between sections | Editorial, one focal visual per section |
| /portal/* | 24px page padding, 16px gaps | Compact bento |
| /emergency/[token] | 24px (16px under 360px wide) | Compact; triage data above the fold on 375x667 |

## Surfaces
- Cards: bg-surface, radius 18-20px, hairline border. Light surfaces use rgba(0,0,0,0.1). ONLY dark surfaces use the white hairline. Never a white hairline on a white card.
- Shadow ceiling: 0 1px 2px rgba(0,0,0,.04), 0 8px 24px rgba(0,0,0,.06).
- Glass header: background var(--bg-glass); backdrop-filter: saturate(180%) blur(20px) (+ -webkit- prefix); hairline bottom border; solid-colour fallback inside @supports not (backdrop-filter: blur(1px)).

## Motion (src/lib/motion.ts is the only source)
- appleSpring = { type: "spring", stiffness: 120, damping: 20, mass: 1 }
- Scroll reveal (marketing only): initial {opacity:0, y:30} to {opacity:1, y:0}, whileInView, viewport {once:true, margin:"-80px"}.
- Buttons: whileHover {scale:1.015}, whileTap {scale:0.98}. No colour flash on hover.
- Wrap the app in <MotionConfig reducedMotion="user">. Movement and scale use springs. Pure colour/opacity changes may use 150ms ease-out.
- Never use CSS ease-in-out for movement.

## Forbidden
Purple/cyan/neon gradients. Shadows heavier than the ceiling. Four-column marketing card grids (max 3, prefer one focal element). Emojis in UI. Stock illustrations. Skeuomorphism other than the Wallet-style ID card.

## Component requirements
- Button: primary filled --accent-action, secondary hairline, destructive. Min height 44px. Focus ring: 2px --accent-action with 2px offset on :focus-visible.
- Input: 16px font (prevents iOS zoom), visible label, inline error text.
- Segmented control: spring-animated pill using layoutId. Modal: focus trap, Esc closes, backdrop click closes unless destructive.
- Badges: always text + icon, never colour alone. Blood group: large pill. Allergies: --clinical-critical alert box.

## Emergency page specifics
Server Component. Light theme forced, maximum contrast. System font only. No framer-motion. Inline SVG icons only. Order above the fold: banner, verification badge, name and age, blood group pill, allergies alert, sticky call bar (56px tall).
```

#### `.agents/rules/02-security-privacy.md`
```markdown
---
trigger: always_on
description: Umbrella security and privacy rules for medical data
---
# 02 Security and privacy

1. Data access
- The anon role has NO table privileges. The public page uses only the RPC get_emergency_triage_by_token.
- Every table has RLS enabled. Policies use (select auth.uid()) and the helper public.is_approved_doctor().
- Column-level GRANTs protect role, doctor_status, patient_code and qr_token. See skill umbrella-supabase-rls.

2. Roles
- role and doctor_status are read from public.accounts on the server. Never from JWT user_metadata, localStorage, query strings or form fields.
- Doctor signup creates a PENDING account. A pending doctor can read no patient data.

3. Secrets
- No secrets in client code. .env.local is never committed. v1 has exactly two env vars: NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.

4. Emergency route hygiene
- Cache-Control: no-store. robots noindex,nofollow. Referrer-Policy: no-referrer.
- Unknown or malformed token: 404 with no hint about why.
- No analytics or third-party scripts. Never log the token or any patient data.

5. Input
- zod validation on the client and again in every server action.
- Never interpolate user text into PostgREST .or()/.filter() strings or SQL. Escape % _ , ( ) in search terms.

6. Output
- Render user text through React only (no dangerouslySetInnerHTML). For tel: links strip the number to digits and one leading +.

7. Errors
- Friendly messages only. Never show raw DB errors or stack traces.

8. Logs, tests, screenshots: synthetic data only. Never console.log patient objects.

9. Headers in next.config: X-Content-Type-Options nosniff, X-Frame-Options DENY, Referrer-Policy strict-origin-when-cross-origin (no-referrer on /emergency/*), Permissions-Policy camera=(), microphone=(), geolocation=().
```

#### `.agents/rules/03-typescript-nextjs.md`
```markdown
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
```

#### `.agents/rules/04-supabase-sql.md`
```markdown
---
trigger: glob
globs: supabase/**/*.sql
description: Rules for writing Umbrella migrations, seeds and SQL tests
---
# 04 Supabase SQL

- Schema changes only through numbered files in supabase/migrations/. Never edit a migration that has run on a remote project; add a new one.
- Schema source: SPEC section 4.2 amended by docs/DECISIONS.md. Pattern library: skill umbrella-supabase-rls (references/rls-patterns.sql). Copy its patterns; do not improvise policies.
- Every function: schema-qualified names; SECURITY DEFINER functions use `set search_path = ''`; `revoke all on function ... from public;` then grant only to the roles that need it.
- Every table: enable RLS in the migration that creates it. Revoke privileges you do not need (anon gets none).
- Policies use (select auth.uid()), never bare auth.uid(). Index every column used in a policy or foreign key.
- timestamptz for times, text + check constraints (the only enum is user_role, per the spec), gen_random_uuid() for ids.
- Seeds are idempotent and synthetic.
- rls_smoke.sql runs inside BEGIN ... ROLLBACK using `set local role` and set_config('request.jwt.claims', ...). Every policy and RPC gets at least one ALLOW test and one DENY test.
- After a migration is run, the human regenerates src/lib/supabase/types.ts.
```

### 5.3 Workflows (`.agents/workflows/`)

Typed in chat as `/start-phase`, `/verify`, `/security-audit`, `/design-review`.

#### `.agents/workflows/start-phase.md`
```markdown
---
description: Begin a build phase safely (read context, restate goal, list files, wait for go)
---
1. Read docs/PROGRESS.md, docs/DECISIONS.md, AGENTS.md and the SPEC sections named in the phase prompt.
2. Run `git status` and `git branch --show-current`. If not on phase/<n>-<slug>, say so and ask to create it.
3. Reply with: the goal in 3 lines, files to create or change, spec conflicts or risks, and the exact checks you will run at the end.
4. If anything conflicts with DECISIONS or SPEC, ask ONE question and wait. Otherwise proceed.
```

#### `.agents/workflows/verify.md`
```markdown
---
description: Run all checks and visually verify the current work
---
1. Run `npm run typecheck && npm run lint && npm run build`. Fix failures you caused.
2. Run `npm run test` if tests exist.
3. Start `npm run dev` if it is not running. With the browser tool load every route touched this phase at 375x667 and 1280x800 and screenshot each.
4. Check: no console errors; keyboard-only navigation works; focus ring visible; no horizontal scroll; critical data above the fold on portal and emergency routes.
5. Report a table: check | result | evidence. Include failures. Do not fix unrelated issues.
```

#### `.agents/workflows/security-audit.md`
```markdown
---
description: Audit auth, RLS and emergency-route privacy against Umbrella's non-negotiables
---
1. Re-read AGENTS.md section 5 (N1-N10), rule 02 and skill umbrella-supabase-rls.
2. Search the codebase for: service_role, getSession(, dangerouslySetInnerHTML, user_metadata, console.log, .or(, localStorage, residential_address, spouse_dependents.
3. For each hit say whether it is allowed and why. residential_address and spouse_dependents may appear only in patient/doctor portal code and the database, never under src/app/emergency.
4. Open supabase/migrations and supabase/tests. Confirm: every table has RLS enabled; anon has no table grants; role, doctor_status, qr_token and patient_code are not updatable by authenticated users; rls_smoke.sql covers every case in the skill checklist.
5. Test live: an unauthenticated GET of /emergency/<random uuid> returns 404; /portal/patient and /portal/doctor redirect to /login; a patient session cannot open /portal/doctor.
6. Output PASS/FAIL per item with file:line evidence, then a prioritised fix list.
```

#### `.agents/workflows/design-review.md`
```markdown
---
description: Review UI against the Umbrella design system and Vercel web interface guidelines
---
1. Run the web-design-guidelines skill on the files changed in this phase (git diff --name-only main). Fix violations you caused.
2. Check against rule 01: tokens only (search for raw hex outside globals.css), spacing per route, hairline colour vs surface, springs from src/lib/motion.ts, reduced-motion support, forbidden patterns.
3. Check the contrast of every text/background pair against WCAG AA (4.5:1 normal text, 3:1 large). Fix with the colours in DECISIONS D10.
4. Screenshot at 375x667 and 1280x800.
5. Report violations as a file:line list plus what you changed.
```

---

## Part 6: Two custom Umbrella skills

### 6.1 `.agents/skills/umbrella-supabase-rls/SKILL.md`
```markdown
---
name: umbrella-supabase-rls
description: Use when writing or reviewing Umbrella's Supabase schema, RLS policies, grants, triggers, RPC functions, signup trigger, or SQL security tests. Contains the reference SQL and the test checklist.
---
# Umbrella Supabase RLS playbook

Read references/rls-patterns.sql before writing any SQL for Umbrella. It is the reference implementation of SPEC section 4 amended by docs/DECISIONS.md (D1-D9). Copy its structure.

## Workflow
1. Write supabase/migrations/0001_umbrella_schema.sql in this order: extension, enum, tables (with DECISIONS changes), indexes, helper function, triggers, RLS enable + policies, grants/revokes, RPCs.
2. Write supabase/tests/rls_smoke.sql covering every item in the checklist.
3. Tell the human how to run both (Supabase SQL Editor, or `supabase db push` after `supabase login` and `supabase link`), then to regenerate src/lib/supabase/types.ts.

## Test checklist (an ALLOW and a DENY test wherever both apply)
1. anon cannot select from accounts, patient_profiles, clinical_records, appointments (permission denied).
2. anon: get_emergency_triage_by_token(valid token) returns JSON with NO keys residential_address, spouse_dependents or qr_token; unknown token returns null.
3. Patient A cannot read patient B's profile, clinical record or appointments; can read their own.
4. Patient can update own demographics; cannot update qr_token, patient_code or patient_id.
5. Patient cannot update accounts.role or doctor_status (permission denied); can update full_name.
6. Signup metadata role='admin' (or anything except 'doctor') creates a patient; role='doctor' creates doctor_status='pending'.
7. A pending doctor reads zero patient rows; an approved doctor reads all.
8. Patient cannot update clinical_records directly; submit_self_reported_baseline works while unverified and raises after verification.
9. Approved doctor's UPDATE on clinical_records sets is_doctor_verified=true and last_updated_by_doctor_id=auth.uid(), even if the client sent other values. A no-op update (set allergies = allergies) also verifies.
10. Approved doctor inserts an appointment only with their own doctor_id; a patient cannot insert appointments.
11. Completing an appointment sets last_appointment_date and last_appointment_summary but does NOT flip is_doctor_verified.
12. regenerate_qr_token returns a new uuid; the old token now returns null from the emergency RPC.
13. DELETE on any of the four tables as authenticated fails.

## Gotchas
- Supabase grants EXECUTE on new functions to anon and authenticated by default. `revoke ... from public` is NOT enough: revoke from public, anon, authenticated, then grant back explicitly.
- Policies on accounts must not query accounts directly (recursion). Use is_approved_doctor() (SECURITY DEFINER).
- Write (select auth.uid()), not bare auth.uid(), in policies.
- Column grants only bite after `revoke update on the table`; the reference SQL revokes everything first, then grants back.
- SECURITY DEFINER functions need `set search_path = ''` and schema-qualified names.
```

### 6.2 `.agents/skills/umbrella-supabase-rls/references/rls-patterns.sql`
```sql
-- Reference patterns for supabase/migrations/0001_umbrella_schema.sql
-- SPEC section 4.2 plus DECISIONS D1-D9. Tables not shown here are exactly
-- as in SPEC 4.2 with the noted changes.

create extension if not exists "pgcrypto";
create type public.user_role as enum ('patient', 'doctor');

-- accounts (D1): doctors start as 'pending'; patients have doctor_status null
create table public.accounts (
  id uuid primary key references auth.users(id) on delete cascade,
  email text unique not null,
  role public.user_role not null default 'patient',
  full_name text not null,
  contact_phone text not null default '',
  medical_license_number text,
  specialization text,
  doctor_status text check (doctor_status in ('pending','approved','rejected')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint accounts_role_fields_chk check (
    (role = 'doctor' and doctor_status is not null and medical_license_number is not null)
    or (role = 'patient' and doctor_status is null)
  )
);

-- patient_profiles: as SPEC 4.2 BUT residential_address text not null default '' (D4)
-- clinical_records: as SPEC 4.2 (its row is auto-created by trigger below)
-- appointments: as SPEC 4.2 BUT doctor_id uuid not null references public.accounts(id) on delete restrict (D6)
create index on public.appointments (patient_id, scheduled_at desc);
create index on public.appointments (doctor_id);
create index on public.accounts (contact_phone);

-- helper: approved doctor? (SECURITY DEFINER avoids RLS recursion)
create or replace function public.is_approved_doctor()
returns boolean language sql stable security definer set search_path = '' as
$$
  select exists (
    select 1 from public.accounts a
    where a.id = (select auth.uid()) and a.role = 'doctor' and a.doctor_status = 'approved'
  );
$$;
revoke all on function public.is_approved_doctor() from public, anon, authenticated;
grant execute on function public.is_approved_doctor() to authenticated;

-- generic updated_at
create or replace function public.set_updated_at()
returns trigger language plpgsql set search_path = '' as $$
begin new.updated_at := now(); return new; end $$;
create trigger trg_accounts_updated before update on public.accounts
for each row execute function public.set_updated_at();
create trigger trg_patient_profiles_updated before update on public.patient_profiles
for each row execute function public.set_updated_at();

-- signup trigger (D2): reads metadata ONCE; unknown roles become 'patient'
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = '' as $$
declare
  meta jsonb := coalesce(new.raw_user_meta_data, '{}'::jsonb);
  v_role public.user_role := case when meta->>'role' = 'doctor'
    then 'doctor'::public.user_role else 'patient'::public.user_role end;
begin
  insert into public.accounts (id, email, role, full_name, contact_phone, medical_license_number, specialization, doctor_status)
  values (
    new.id,
    new.email,
    v_role,
    coalesce(nullif(meta->>'full_name',''), 'Unknown'),
    coalesce(meta->>'contact_phone', ''),
    case when v_role = 'doctor' then meta->>'medical_license_number' end,
    case when v_role = 'doctor' then meta->>'specialization' end,
    case when v_role = 'doctor' then 'pending' end
  );

  if v_role = 'patient' then
    insert into public.patient_profiles (patient_id, age, blood_group, emergency_contact_name, emergency_contact_phone, emergency_contact_relation)
    values (
      new.id,
      coalesce(nullif(meta->>'age','')::int, 0),
      case when meta->>'blood_group' in ('A+','A-','B+','B-','AB+','AB-','O+','O-')
        then meta->>'blood_group' else 'Unknown' end,
      coalesce(meta->>'emergency_contact_name', ''),
      coalesce(meta->>'emergency_contact_phone', ''),
      coalesce(meta->>'emergency_contact_relation', '')
    );
  end if;
  return new;
end $$;
revoke all on function public.handle_new_user() from public, anon, authenticated;
create trigger on_auth_user_created after insert on auth.users
for each row execute function public.handle_new_user();

-- every patient gets an empty clinical record (D7)
create or replace function public.create_clinical_record()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  insert into public.clinical_records (patient_id) values (new.patient_id) on conflict do nothing;
  return new;
end $$;
revoke all on function public.create_clinical_record() from public, anon, authenticated;
create trigger trg_patient_profile_clinical after insert on public.patient_profiles
for each row execute function public.create_clinical_record();

-- server-side verification stamp (D7): client values are ignored
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
revoke all on function public.stamp_clinical_update() from public, anon, authenticated;
create trigger trg_stamp_clinical before update on public.clinical_records
for each row execute function public.stamp_clinical_update();

-- completing an appointment fills last_appointment_* without verifying (D8)
create or replace function public.on_appointment_completed()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  if new.status = 'completed' and old.status is distinct from 'completed' then
    perform set_config('umbrella.skip_stamp', 'on', true);
    update public.clinical_records
    set last_appointment_date = new.scheduled_at,
        last_appointment_summary = coalesce(nullif(new.clinical_notes, ''), new.reason)
    where patient_id = new.patient_id
      and (last_appointment_date is null or last_appointment_date <= new.scheduled_at);
    perform set_config('umbrella.skip_stamp', 'off', true);
  end if;
  return new;
end $$;
revoke all on function public.on_appointment_completed() from public, anon, authenticated;
create trigger trg_appointment_completed after update on public.appointments
for each row execute function public.on_appointment_completed();

-- RLS
alter table public.accounts enable row level security;
alter table public.patient_profiles enable row level security;
alter table public.clinical_records enable row level security;
alter table public.appointments enable row level security;

create policy accounts_select_self on public.accounts for select to authenticated
  using (id = (select auth.uid()));
create policy accounts_select_patients_for_doctors on public.accounts for select to authenticated
  using (role = 'patient' and (select public.is_approved_doctor()));
create policy accounts_select_my_doctors on public.accounts for select to authenticated
  using (role = 'doctor' and exists (
    select 1 from public.appointments ap
    where ap.doctor_id = accounts.id and ap.patient_id = (select auth.uid())
  ));
create policy accounts_update_self on public.accounts for update to authenticated
  using (id = (select auth.uid())) with check (id = (select auth.uid()));

create policy pp_select on public.patient_profiles for select to authenticated
  using (patient_id = (select auth.uid()) or (select public.is_approved_doctor()));
create policy pp_update_self on public.patient_profiles for update to authenticated
  using (patient_id = (select auth.uid())) with check (patient_id = (select auth.uid()));
-- no INSERT policy: rows are created by handle_new_user

create policy cr_select on public.clinical_records for select to authenticated
  using (patient_id = (select auth.uid()) or (select public.is_approved_doctor()));
create policy cr_update_doctor on public.clinical_records for update to authenticated
  using ((select public.is_approved_doctor())) with check ((select public.is_approved_doctor()));

create policy ap_select on public.appointments for select to authenticated
  using (patient_id = (select auth.uid()) or (select public.is_approved_doctor()));
create policy ap_insert_doctor on public.appointments for insert to authenticated
  with check ((select public.is_approved_doctor()) and doctor_id = (select auth.uid()));
create policy ap_update_doctor on public.appointments for update to authenticated
  using ((select public.is_approved_doctor())) with check ((select public.is_approved_doctor()));

-- GRANTS (D3): start from zero, grant back only what policies need
revoke all on public.accounts, public.patient_profiles, public.clinical_records, public.appointments from anon;
revoke all on public.accounts, public.patient_profiles, public.clinical_records, public.appointments from authenticated;
grant select on public.accounts, public.patient_profiles, public.clinical_records, public.appointments to authenticated;
grant update (full_name, contact_phone, specialization) on public.accounts to authenticated;
grant update (age, blood_group, emergency_contact_name, emergency_contact_phone, emergency_contact_relation, spouse_dependents, residential_address)
  on public.patient_profiles to authenticated;
grant update (medical_conditions, current_medication, previous_surgeries, allergies)
  on public.clinical_records to authenticated;
grant insert on public.appointments to authenticated;
grant update (scheduled_at, status, reason, clinical_notes) on public.appointments to authenticated;

-- RPC 1: public emergency triage (SPEC 4.2, hardened). Never returns address, dependents or qr_token.
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
revoke all on function public.get_emergency_triage_by_token(uuid) from public;
grant execute on function public.get_emergency_triage_by_token(uuid) to anon, authenticated;

-- RPC 2: patient self-reported baseline (D7). Only while the record is NOT doctor-verified.
create or replace function public.submit_self_reported_baseline(p_conditions text[], p_allergies text[])
returns void language plpgsql security definer set search_path = '' as $$
begin
  if coalesce(array_length(p_conditions, 1), 0) > 50 or coalesce(array_length(p_allergies, 1), 0) > 50 then
    raise exception 'Too many entries';
  end if;
  update public.clinical_records
  set medical_conditions = coalesce(p_conditions, '{}'),
      allergies = coalesce(p_allergies, '{}')
  where patient_id = (select auth.uid()) and is_doctor_verified = false;
  if not found then
    raise exception 'Record is already doctor-verified, or no patient profile exists';
  end if;
end $$;
revoke all on function public.submit_self_reported_baseline(text[], text[]) from public, anon, authenticated;
grant execute on function public.submit_self_reported_baseline(text[], text[]) to authenticated;

-- RPC 3: rotate the QR token (D3). Affects only the caller's own row.
create or replace function public.regenerate_qr_token()
returns uuid language plpgsql security definer set search_path = '' as $$
declare v_token uuid := gen_random_uuid();
begin
  update public.patient_profiles set qr_token = v_token where patient_id = (select auth.uid());
  if not found then raise exception 'No patient profile for this user'; end if;
  return v_token;
end $$;
revoke all on function public.regenerate_qr_token() from public, anon, authenticated;
grant execute on function public.regenerate_qr_token() to authenticated;

-- TEST HARNESS PATTERN (supabase/tests/rls_smoke.sql): everything inside BEGIN ... ROLLBACK
-- begin;
-- insert into auth.users (id, aud, role, email, raw_user_meta_data) values
-- ('00000000-0000-0000-0000-0000000000a1','authenticated','authenticated','pat.a@example.test',
--  '{"role":"patient","full_name":"Test Patient A","age":"34","blood_group":"O+","emergency_contact_name":"Test Contact","emergency_contact_phone":"+910000000001","emergency_contact_relation":"Sibling"}'),
-- ('00000000-0000-0000-0000-0000000000d1','authenticated','authenticated','doc.d@example.test',
--  '{"role":"doctor","full_name":"Test Doctor","medical_license_number":"TEST-0001"}');
-- update public.accounts set doctor_status = 'approved' where id = '00000000-0000-0000-0000-0000000000d1';
-- set local role authenticated;
-- select set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000a1","role":"authenticated"}', true);
-- do $$ begin
--   begin update public.accounts set role = 'doctor' where id = (select auth.uid());
--   raise exception 'FAIL: role escalation allowed';
--   exception when insufficient_privilege then null; end;
-- end $$;
-- reset role;
-- rollback;
-- (If the auth.users insert complains about a missing column in your project, add that column.)
```

### 6.3 `.agents/skills/umbrella-qr-card/SKILL.md`
```markdown
---
name: umbrella-qr-card
description: Use when building or changing Umbrella's QR Studio: rendering the emergency QR, exporting the PNG and printable PDF ID card, previewing the public page, or rotating the qr_token.
---
# Umbrella QR Studio playbook

## Value and origin
- URL = window.location.origin + '/emergency/' + qr_token (N6). Compute it inside useEffect after mount to avoid a hydration mismatch; render a same-size skeleton until ready. Put the string-building in a pure function buildEmergencyUrl(origin, token) in src/lib/ and unit-test it.
- If origin is localhost, or the host ends with .vercel.app and is not the production domain, show a calm amber note under the QR: "This QR points to <origin>. Cards printed here only work while that site is online." (DECISIONS D12). Never block the download.

## Rendering (qrcode.react)
- Use QRCodeSVG with level="Q", marginSize={4}, fgColor="#000000", bgColor="#ffffff". Always black on white, even in dark sections, so every scanner reads it.
- Minimum on-screen size 224px on phones; keep a 1:1 box.
- Read the installed qrcode.react types before use (prop names changed between major versions).

## PNG export (lock screen / wallet)
- Draw to an offscreen canvas 1080x1080: white background, QR centred at 840px, then "EMERGENCY MEDICAL ID" label, patient name and patient code below it.
- Convert the SVG to an image with XMLSerializer + Blob URL, wait for img.onload, canvas.toBlob('image/png'), download through an anchor with a Blob URL, then revoke the URL.
- Filename: umbrella-emergency-id-<patient_code>.png

## Printable card (PDF with jspdf)
- Page size [85.6, 54] mm, landscape. Two pages: front and back.
- Front: "EMERGENCY MEDICAL ID" label, patient name (bold), blood-group pill (large), patient code, QR on the right (about 30mm), caption "Scan for medical info. No login needed."
- Back: "In an emergency call:" then emergency contact name, relation and phone, plus the full URL in small monospace text.
- NEVER print the residential address or dependents.
- Render each side to a canvas at 300 dpi (1011x638 px), addImage as PNG, save as umbrella-emergency-card-<patient_code>.pdf. System sans font only.

## Regenerate QR link
- Button opens a confirmation modal. Copy: "Your current QR code will stop working immediately. Printed or saved copies will show 'not found'. Continue?"
- On confirm call rpc('regenerate_qr_token'), update local state with the returned uuid, redraw the QR, show a success message that reminds the user to re-download and reprint. Disable the button while pending; show errors inline.

## Preview Public Emergency View
- Opens /emergency/<qr_token> in a new tab with rel="noopener".

## Tests
- Vitest: buildEmergencyUrl and the card layout maths. Playwright: the download buttons produce files; rotating changes the displayed URL; the old token then returns 404.
```

---

## Part 7: The docs the agent reads

### 7.1 `docs/DECISIONS.md`
```markdown
# DECISIONS.md: fixes and clarifications to SPEC v2.0
This file WINS over docs/SPEC.md wherever they differ.

## Security
D1. Doctor approval gate. SPEC lets anyone self-register as a doctor and instantly read every patient's home address. Instead: doctor signup creates accounts.doctor_status='pending'. All doctor privileges (RLS, proxy, UI) require doctor_status='approved' via public.is_approved_doctor(). Pending doctors see a "Verification pending" screen. The owner approves in Supabase: update public.accounts set doctor_status='approved' where email='...'. The dev seed approves one synthetic doctor.

D2. Role handling. options.data.role is read ONCE by the signup trigger; anything other than 'doctor' becomes 'patient'. Afterwards authorisation uses public.accounts only, never user_metadata (users can edit their own metadata).

D3. Column protection. Authenticated users cannot update accounts.role/doctor_status/email or patient_profiles.patient_code/qr_token, or any column outside the granted lists. qr_token changes only through rpc regenerate_qr_token.

D9. Emergency page delivery: force-dynamic, Cache-Control no-store, robots noindex, Referrer-Policy no-referrer. Malformed or unknown token: generic 404.

## Schema gaps
D4. residential_address is `text not null default ''` because the signup form (SPEC 6.2) does not collect it.

D5. Age. SPEC 3.1 says age is computed from date_of_birth, but 4.2 stores `age integer` and signup collects Age. v1 keeps `age`. Known limitation: it goes stale. Backlog: switch to date_of_birth.

D6. appointments.doctor_id is `not null` AND `on delete set null` in the spec (contradiction). Use `on delete restrict`.

D7. Self-reported baseline. SPEC 6.3 lets patients submit a baseline but 4.3 makes clinical_records doctor-only. Resolution: rpc submit_self_reported_baseline (conditions and allergies only, only while is_doctor_verified=false). The clinical_records row is auto-created by a trigger when the patient profile is created. Verification stamps (is_doctor_verified, last_updated_by_doctor_id, updated_at) are set by a BEFORE UPDATE trigger, never by client values. A doctor can verify unchanged self-reported data by saving it.

D8. Completing an appointment fills last_appointment_date and last_appointment_summary through a trigger and does NOT flip is_doctor_verified.

## Product and UX
D10. Contrast. #86868b on white fails WCAG AA for small text; #ff3b30 with small white text fails too. Use #6e6e73 for text under 18px; --clinical-critical-text #d70015 for small red text; red fills carry large bold white text (20px+). Green text #1d7a37 and amber text #8a5200 are the text variants for verified and self-reported badges.

D11. Email confirmation may be ON or OFF. If signUp returns no session, show "Check your email to confirm your account", then send them to /login. Profile rows are created by the DB trigger, so the client never inserts them.

D12. QR origin is window.location.origin (SPEC check 5), plus the non-blocking warning described in skill umbrella-qr-card.

D13. Performance. "Under 300ms on 3G" is not guaranteed by any stack, so we use measurable budgets for /emergency/[token]: TTFB under 300ms when warm and same-region; Lighthouse mobile performance 95 or higher; LCP under 2.0s on simulated Slow 4G; as little client JS as possible (target under 120KB gzipped first load); framer-motion, qrcode.react and jspdf must NOT appear in that route's bundle (check the `next build` output). The press feedback there is CSS only (:active scale 0.98). This is the one exception to N8.

D14. Doctor lookup. Classify the input: matches UMB-XXXXXX (case-insensitive): exact patient_code. UUID: exact qr_token. Mostly digits (7+): phone contains. Otherwise: name ilike. Run separate parameterised queries; never build an .or() string from raw input. Minimum 2 characters, 300ms debounce, max 20 results showing name, code, age, blood group.

D15. Escalation link. Footer goes to /portal/doctor?patient_token=<uuid>. If logged out: redirect to /login?next=<encoded path+query>; after login an approved doctor lands with the patient pre-loaded. A logged-in non-doctor sees a "Doctor account required" screen, never a 500. Accept `next` only if it is a relative path starting with a single "/".

D16. Tooling. Use whatever `create-next-app@latest` produced; do not downgrade to match "Next 14/15" or "React 18". Interception file name per rule 03. Tailwind v4 CSS-first. Use the `framer-motion` package. Env var names exactly as in SPEC.

D17. Dates are stored as timestamptz and shown with Intl.DateTimeFormat in the viewer's locale. The appointment picker uses local time.

D18. Out of scope for v1 (backlog): admin UI for doctor approval, SMS, audit-log table, rate limiting, i18n, native wallet passes, push notifications.
```

### 7.2 `docs/PROGRESS.md` (starter)
```markdown
# PROGRESS.md
The agent updates this at the end of every phase.

## Status
| Phase | Name | Status | Branch / commit |
|---|---|---|---|
| 0 | Bootstrap | not started | |
| 1 | Database | not started | |
| 2 | Design-system primitives | not started | |
| 3 | Supabase clients, RBAC, auth pages | not started | |
| 4 | Emergency triage page | not started | |
| 5 | Patient portal: shell + QR Studio | not started | |
| 6 | Patient portal: demographics + clinical view | not started | |
| 7 | Doctor portal: lookup + clinical editor | not started | |
| 8 | Doctor portal: appointments + escalation | not started | |
| 9 | Marketing landing page | not started | |
| 10 | QA and hardening | not started | |
| 11 | Deploy | not started | |

## Deviations from SPEC / DECISIONS
(none)

## Open questions for the human
(none)

## Human verification log
(none)
```

---

## Part 8: The build, phase by phase

### 8.1 The loop (repeat for every phase)
1. **Branch:** `git checkout -b phase/<n>-<slug>` (for example `phase/1-database`).
2. **New Antigravity conversation.** Pick the mode shown in the prompt (Planning or Fast). Fresh conversations stop old context from drifting.
3. **Paste the phase prompt below.** In Planning mode, read the plan it shows and approve it only if the file list looks right.
4. **Let it run**, then read its entry in `docs/PROGRESS.md`.
5. **You verify** (each phase lists what to click). Run `npm run dev` yourself and try it. Do not rely on the agent's word alone.
6. **Skim the diff** (`git diff main --stat`), then merge and push:
   `git checkout main && git merge phase/<n>-<slug> && git push`.
7. **Next phase, new conversation.**

> If something fails, paste the exact error text into a new conversation with: *"Run /start-phase, use the diagnose skill, fix only this error: ..."*.

### 8.2 Phase map

| # | Phase | Mode | Main spec sections |
|---|---|---|---|
| 0 | Bootstrap | Fast | 2, 7 |
| 1 | Database | Planning, High thinking | 3, 4 |
| 2 | Design-system primitives | Fast | 5, 8 |
| 3 | Clients, RBAC, auth pages | Planning, High thinking | 3.2, 6.2 |
| 4 | Emergency triage page | Fast | 6.5 |
| 5 | Patient portal: shell + QR Studio | Fast | 6.3 |
| 6 | Patient portal: demographics + clinical | Fast | 6.3 |
| 7 | Doctor portal: lookup + clinical editor | Planning | 6.4 |
| 8 | Doctor portal: appointments + escalation | Fast | 6.4, 6.5 |
| 9 | Marketing landing page | Fast | 6.1 |
| 10 | QA and hardening | Planning, High thinking | all |
| 11 | Deploy | Planning | 2 |

---

### 8.3 Phase 0: Bootstrap (Fast)

```text
Phase 0: Bootstrap. Run /start-phase first.
Read: AGENTS.md, docs/DECISIONS.md (D16), SPEC sections 2 and 7.
Goal: turn the fresh create-next-app project into the Umbrella foundation. No product pages yet.

Tasks:
1. Confirm these exist: AGENTS.md, GEMINI.md, docs/SPEC.md, docs/DECISIONS.md, docs/PROGRESS.md, .agents/rules/*, .agents/workflows/*. If any is missing, stop and tell me which.
2. Read package.json and record the next, react and tailwindcss versions in PROGRESS.md.
3. Install: npm i @supabase/supabase-js @supabase/ssr framer-motion qrcode.react jspdf zod lucide-react ; npm i -D vitest @playwright/test ; then npx playwright install chromium.
4. tsconfig.json: strict true and noUncheckedIndexedAccess true.
5. package.json scripts: typecheck (tsc --noEmit), test (vitest run), test:e2e (playwright test). Keep dev, build, lint. Add vitest.config.ts and playwright.config.ts (baseURL http://localhost:3000, webServer npm run dev, projects: a mobile Chromium device and desktop Chromium).
6. src/app/globals.css: implement ALL tokens from rule 01 (:root and [data-theme="dark"]), map them to Tailwind with @theme, add base styles (canvas background, system font, text colour, :focus-visible ring, hairline utilities). Remove the create-next-app demo styles.
7. src/lib/motion.ts exporting appleSpring, revealVariants and buttonMotion ({ whileHover: { scale: 1.015 }, whileTap: { scale: 0.98 }, transition: appleSpring }).
8. src/app/layout.tsx: lang="en", metadata (title Umbrella), viewport themeColor, children wrapped by a client Providers component using <MotionConfig reducedMotion="user" transition={appleSpring}>. No webfonts.
9. next.config: the security headers from rule 02 item 9.
10. .env.example with the two variable names and empty values. Confirm .gitignore ignores .env*.
11. README.md: install, env, run and scripts.
12. src/app/page.tsx: a minimal page that says "Umbrella" (the only allowed temporary page; the landing page arrives in Phase 9).

Acceptance: typecheck, lint and build pass; page uses token colours; nothing breaks with OS reduced-motion on.
Finish: update PROGRESS.md, commit "chore: foundation", STOP.
You verify: npm run dev shows a clean page; .env.local does not appear in git status.
```

---

### 8.4 Phase 1: Database (Planning, High thinking)

```text
Phase 1: Database. Run /start-phase first. Planning mode.
Read: SPEC sections 3 and 4 (all); DECISIONS D1-D9; skill umbrella-supabase-rls (SKILL.md and references/rls-patterns.sql); skill supabase-postgres-best-practices; rule 04.
Goal: the complete, secure database layer as SQL files. You cannot run them against my project; I will.

Tasks:
1. supabase/migrations/0001_umbrella_schema.sql: SPEC 4.2 tables + DECISIONS changes + everything in the reference patterns (helper, triggers, policies, grants, 3 RPCs). Keep SPEC column names exactly.
2. supabase/seed.sql: idempotent and synthetic. It only approves the dev doctor by email (doctor.dev@example.test). Comments explain that users are created through /signup or Dashboard > Authentication > Add user. No auth.users inserts with passwords.
3. supabase/tests/rls_smoke.sql: every item (1-13) of the skill checklist, each as a DO block inside BEGIN ... ROLLBACK, raising 'FAIL: ...' on a violation and ending with select 'ALL RLS TESTS PASSED'. Use the tdd skill: write each failing expectation first, then confirm the policy satisfies it.
4. docs/DB-RUNBOOK.md, numbered steps for me: (a) paste the migration into the SQL Editor and run it; (b) run rls_smoke.sql; (c) after creating users through the app, run seed.sql; (d) regenerate types: npx supabase login ; npx supabase gen types typescript --project-id <ref> > src/lib/supabase/types.ts.
5. src/lib/supabase/types.ts: only if types are not generated yet, a hand-written Database type with a first-line comment "REPLACE with generated types".
6. src/lib/schemas.ts: zod schemas for blood group, phone, emergency contact, dependents[], medications[], surgeries[], allergies[], appointment input, patient signup, doctor signup, lookup input.
7. Vitest tests for the schemas (invalid age, invalid blood group, malformed uuid, phone sanitiser).

Self-review before finishing: apply /security-audit steps 3 and 4 to your SQL and list any checklist item you could not cover.
Acceptance: every table has RLS enabled; anon has no table grants; typecheck, lint and tests pass.
Finish: update PROGRESS.md, commit, STOP.
You verify: run runbook steps (a) and (b) yourself. If any test prints FAIL, paste the output into the next conversation.
```

---

### 8.5 Phase 2: Design-system primitives (Fast)

```text
Phase 2: Design-system primitives. Run /start-phase first.
Read: rule 01; SPEC sections 5 and 8 (checks 3 and 4); DECISIONS D10.
Skills: apple-hig-designer, vercel-composition-patterns, frontend-design (craft only), web-design-guidelines.
Goal: the reusable, accessible, spring-animated UI kit in src/components/ui. No product features yet.

Build (typed components, variants via props, no barrel files):
1. Button (primary, secondary, destructive, ghost; md and lg(56px); loading state) and LinkButton (Next Link look-alike; plain anchor for tel:). Motion from lib/motion.ts.
2. GlassNav (sticky, glass tokens, left/center/right slots, solid fallback).
3. SegmentedControl (spring pill with layoutId, arrow-key support, correct roles, controlled).
4. TextField, SelectField, TextareaField (label, hint, error, 16px font, aria-describedby) and PasswordField (show/hide).
5. TagInput (chips: add on Enter or comma, remove by button or Backspace, max count, accessible).
6. Badge (tones critical, verified, pending, neutral; always icon + text) and BloodGroupPill (md, xl).
7. Card (surface, hairline, radius 20, compact 24px or roomy padding) and SectionHeading.
8. Modal (focus trap, Esc, backdrop, spring in/out, aria-modal, returns focus) and ConfirmDialog built on it.
9. Alert (info, success, error; role status or alert) and Skeleton, Spinner, Icon wrapper (lucide-react).
10. A dev-only gallery at src/app/(dev)/ui/page.tsx showing every component in light and dark; call notFound() when NODE_ENV is production.
Rules: tokens only, no raw hex; every interactive element has a visible focus ring and 44px minimum target.

Acceptance: /verify passes; /design-review reports zero violations on these files; keyboard-only walkthrough of the gallery works (Tab, Shift+Tab, Esc, arrows).
Finish: update PROGRESS.md, commit, STOP.
You verify: open /ui in light and dark, tab through everything, toggle OS reduced motion.
```

---

### 8.6 Phase 3: Clients, RBAC and auth pages (Planning, High thinking)

```text
Phase 3: Supabase clients, RBAC and auth pages. Run /start-phase first. Planning mode.
Read: SPEC sections 3.2, 6.2, 8 (checks 1, 2, 6); DECISIONS D1, D2, D11, D15, D16; rules 02 and 03; skill supabase; AGENTS N3-N5.
Prerequisite (me): the migration is run, types are generated into src/lib/supabase/types.ts, .env.local is filled. If types.ts still says REPLACE, stop and tell me.

Tasks:
1. src/lib/supabase/client.ts and server.ts following the installed @supabase/ssr README.
2. src/lib/auth/session.ts: getCurrentUser() (uses getUser()) and getAccount() reading public.accounts. Return a discriminated union: anonymous | patient | doctor_pending | doctor_approved | doctor_rejected.
3. The request-interception file (proxy.ts or middleware.ts per rule 03) implementing SPEC 3.2: unauthenticated /portal/* goes to /login?next=...; a patient reaching /portal/doctor goes to /portal/patient; an approved doctor goes to /portal/doctor; pending or rejected doctors reach /portal/doctor, where the PAGE shows the verification screen. /login and /signup redirect logged-in users to their portal. Matcher skips static assets. / and /emergency/* are always public and untouched.
4. /login: email + password wired to supabase.auth.signInWithPassword, zod validation, friendly errors, loading state, validated `next`. Include the Patient/Doctor SegmentedControl from SPEC 6.2: it only changes heading and helper text. After sign-in route by the account's REAL role; if it differs from the selected tab, show a one-line notice such as "Signed in to your doctor account".
5. /signup (reads ?role=patient|doctor to preset the control): Patient and Doctor fields exactly as SPEC 6.2 (blood group select with the 8 groups + Unknown). Call supabase.auth.signUp with options.data holding role and every profile field (the DB trigger consumes them). Handle both outcomes: session returned means redirect to the portal; no session means the "check your email" state. The doctor success message explains that approval is required.
6. A reusable SignOutButton (client) that calls supabase.auth.signOut and redirects to /login.
7. Replace nothing with placeholders: create /portal/patient/page.tsx and /portal/doctor/page.tsx that render the real GlassNav with the account name and SignOutButton, and for doctor_pending the real "Verification pending" screen. Everything else on those pages says plainly which phase builds it. This is the one allowed temporary content (replaced in Phases 5 and 7).
8. Vitest: safeNext() (rejects //evil.com, absolute URLs, backslashes) and a pure role-routing function tested with a table of cases.
9. Playwright e2e/auth.spec.ts: patient signup lands in /portal/patient; an anonymous visit to /portal/patient redirects to /login. Use synthetic emails with a random suffix.

Acceptance: /verify; /security-audit items 2 and 5 pass; a patient cannot open /portal/doctor; no getSession() or user_metadata used for authorisation.
Finish: update PROGRESS.md, commit, STOP.
You verify: sign up a patient and a doctor; the doctor sees "pending"; approve with the SQL in DECISIONS D1; the doctor now reaches the doctor page.
```

---

### 8.7 Phase 4: Emergency triage page (Fast)

```text
Phase 4: Emergency triage page. Run /start-phase first.
Read: SPEC 6.5, 5.1, 8 (checks 1, 2, 4); DECISIONS D9, D10, D13, D15; rules 01-03; AGENTS N1; skills vercel-react-best-practices, web-design-guidelines.
Goal: /emergency/[token] is fast, needs no login, and ships almost no client JavaScript.

Tasks:
1. src/app/emergency/[token]/page.tsx: async Server Component. await params; zod-validate the uuid (invalid: notFound()). Call rpc get_emergency_triage_by_token through a cookie-less anon server client (src/lib/supabase/anon.ts). null: notFound(). force-dynamic; metadata robots noindex; headers per D9 set in next.config for /emergency/:path*.
2. Above the fold at 375x667, in this order: banner "EMERGENCY MEDICAL ID" + verification Badge (Doctor Verified or Patient Self-Reported); name and age (tracking -0.03em); BloodGroupPill xl; critical Allergies alert box (if none recorded show neutral "No known allergies recorded", never wording that implies none exist); sticky bottom action bar "Call Emergency Contact: [Name] ([Relation])" as <a href="tel:+digits">, 56px tall.
3. Cards below: Active Medical Conditions, Current Medications (name, dosage, frequency), Previous Surgeries (procedure, year, notes), last updated and last appointment dates. Empty state per card: "Nothing recorded".
4. Clinician footer: "Are you the treating physician? Log in to update clinical record" linking to /portal/doctor?patient_token=<token>. If a doctor session is detected (server client with cookies, role from public.accounts) show an elevated top bar "Edit Clinical Record in Doctor Portal". Detection must never delay or block the public render: on any failure render the public view.
5. Route-level not-found.tsx: "This emergency ID was not found. Ask the person to open Umbrella and share their QR again." No hint about why.
6. No framer-motion; no client components unless unavoidable. Light theme forced. Components in src/components/emergency/ (server components).
7. Vitest: tel href sanitiser, age and date formatters. Playwright: a valid token shows blood group and the call link; a random uuid gives 404; response has Cache-Control no-store; the HTML contains neither the address nor dependents.

Acceptance: /verify; /security-audit item 5; report the `next build` first-load JS for this route and confirm framer-motion, qrcode.react and jspdf are absent from it; run Lighthouse mobile via the browser tool if available and report the score, otherwise tell me how.
Finish: update PROGRESS.md, commit, STOP.
You verify: sign up a patient, copy qr_token from the Supabase table editor, open /emergency/<token> in DevTools at 375px width and check everything important is visible without scrolling.
```

---

### 8.8 Phase 5: Patient portal shell + QR Studio (Fast)

```text
Phase 5: Patient portal shell + QR Studio. Run /start-phase first.
Read: SPEC 6.3 (top bar and Module 1), 3.1, 8 (checks 3, 4, 5); DECISIONS D3, D12; skill umbrella-qr-card; rule 01; AGENTS N6.

Tasks:
1. src/app/portal/patient/page.tsx (replace Phase 3's temporary content): Server Component that fetches account, patient_profiles, clinical_records and appointments with Promise.all and passes only needed fields to client components.
2. Top bar (GlassNav): patient name, patient code UMB-XXXXXX with a copy button, Sign Out.
3. Compact bento layout (rule 01). Only the QR Studio exists for now; leave NO placeholder cards for Phase 6.
4. QR Studio in src/components/qr/ exactly as the skill describes: QR, URL text with Copy, "Download High-Res PNG (Lockscreen / Wallet)", "Download Printable Emergency ID Card (PDF)", "Preview Public Emergency View", "Regenerate QR Link" with ConfirmDialog calling rpc regenerate_qr_token, and the origin warning (D12). Unit-test buildEmergencyUrl.
5. Loading, error and empty states.

Acceptance: /verify; scanning the QR (or decoding it in a Playwright test) opens the correct /emergency/<token>; regenerating makes the old token 404; open the downloaded PDF and confirm it contains no address; /design-review clean.
Finish: update PROGRESS.md, commit, STOP.
You verify: scan the on-screen QR with your phone; rotate the token, then rescan the old PNG and confirm it fails.
```

---

### 8.9 Phase 6: Patient portal demographics + clinical summary (Fast)

```text
Phase 6: Patient portal demographics + clinical summary. Run /start-phase first.
Read: SPEC 6.3 (Modules 2 and 3), 3.1; DECISIONS D3, D5, D7, D10; skills umbrella-supabase-rls, vercel-composition-patterns.

Tasks:
1. Demographics form in src/components/patient/: name and phone (accounts), age, blood group, emergency contact (name, phone, relation), spouse/dependents dynamic rows (name, relation, age, phone; add and remove; max 10), residential address. zod validation; one Save per card with inline success or error; send only changed fields; update only the granted columns.
2. Clinical summary (read-only): Allergies, Medical Conditions, Current Medications, Previous Surgeries, Last Appointment (date + summary), Scheduled Appointments (date, reason, doctor name + specialization). A verification Badge on top: "Doctor Verified" with date, or amber "Self-Reported (Pending Doctor Verification)".
3. Self-reported baseline, shown ONLY while is_doctor_verified is false: TagInput for conditions and allergies, saved through rpc submit_self_reported_baseline. Once verified the editor disappears and a note says "Your clinical record is managed by your doctor."
4. Past appointments (completed, cancelled), with notes shown only if a doctor wrote them.
5. Compact bento, 24px spacing. On mobile the order is QR Studio, Clinical summary, Demographics.

Tests (Playwright): edit emergency contact, refresh, it persists, and /emergency/<token> shows the new contact; no baseline editor once verified; address and dependents never appear on /emergency.
Acceptance: /verify; /security-audit; /design-review.
Finish: update PROGRESS.md, commit, STOP.
You verify: change the blood group and see it on the emergency page; add a dependent and confirm it does NOT appear there.
```

---

### 8.10 Phase 7: Doctor portal lookup + clinical editor (Planning)

```text
Phase 7: Doctor portal: lookup + clinical editor. Run /start-phase first. Planning mode.
Read: SPEC 6.4, 3.1, 8 (check 1); DECISIONS D1, D7, D14, D15; skills umbrella-supabase-rls, supabase.

Tasks:
1. /portal/doctor (replace Phase 3's temporary content for approved doctors; pending and rejected doctors keep the verification screen): GlassNav with doctor name, License Badge, specialization, and a prominent Patient Lookup Bar following D14 (classification, result list, keyboard navigation, empty and error states).
2. Selecting a patient loads the workspace. The URL stays shareable via ?patient=<patient_code>; also accept ?patient_token=<uuid> (D15) and resolve it.
3. Sticky Patient Context Banner, read-only (N2): Name, Age, Blood Group pill, Contact Phone, Emergency Contact (name, relation, phone with tel link), Spouse/Dependents, Address.
4. Clinical Record Editor in src/components/doctor/: Allergies TagInput; Medical Conditions list manager; Current Medications rows (name, dosage, frequency, prescribed_by optional); Previous Surgeries rows (procedure, year, notes). Dirty-state detection, an unsaved-changes guard, and one "Save & Verify" button that updates the 4 granted columns (the DB trigger stamps verification). After saving show "Verified by you just now".
5. Show the current verification state and last-updated info. If the record is self-reported, pre-fill the patient's baseline with the hint "Review and save to verify".
6. Optimistic concurrency: filter the update with the updated_at you loaded and treat 0 updated rows as "This record changed since you opened it. Reload."

Tests (Playwright, approved doctor + patient): lookup by code, by name and by phone; save, then /emergency/<token> shows "Doctor Verified" and the new allergy; a patient session cannot reach /portal/doctor; a pending doctor sees no patient data.
Acceptance: /verify; /security-audit; /design-review.
Finish: update PROGRESS.md, commit, STOP.
You verify: run the whole flow by hand with two browser profiles (one patient, one doctor).
```

---

### 8.11 Phase 8: Doctor portal appointments + escalation (Fast)

```text
Phase 8: Doctor portal: appointments + escalation. Run /start-phase first.
Read: SPEC 6.4 (Appointments Manager), 6.5 (escalation); DECISIONS D8, D15, D17.

Tasks:
1. Appointments Manager inside the patient workspace: upcoming (scheduled) and past (completed, cancelled) lists; a "Schedule appointment" form (datetime-local in local time, stored as UTC; reason required; must be in the future; zod); row actions Mark Completed (optional clinical notes) and Cancel (with confirmation).
2. Completing an appointment updates the patient's Last Appointment through the DB trigger; refresh the workspace so the new Last Appointment shows without a manual reload.
3. Escalation round trip: /emergency/<token> footer, then login, then /portal/doctor?patient_token=..., then the workspace pre-loaded. A logged-in non-doctor sees the "Doctor account required" screen (D15).
4. Empty, loading and error states; no double submit.

Tests (Playwright): a scheduled appointment appears in the patient's portal; Mark Completed updates the patient's Last Appointment and leaves the verification badge unchanged; the escalation flow works.
Acceptance: /verify; /security-audit; /design-review.
Finish: update PROGRESS.md, commit, STOP.
```

---

### 8.12 Phase 9: Marketing landing page (Fast)

```text
Phase 9: Marketing landing page. Run /start-phase first.
Read: SPEC 6.1, 5.1, 5.3, 8 (check 4); DECISIONS D10; rule 01; skills frontend-design, apple-hig-designer, web-design-guidelines, vercel-react-best-practices.

Tasks:
1. src/app/(marketing)/page.tsx (move the temporary root page into it). GlassNav with the brand on the left and a quiet "Doctor Portal" link on the right. Single primary CTA "Create Your Emergency Medical ID" linking to /signup?role=patient.
2. Section 1, Hero (weight 700, tracking -0.03em): "When seconds count, your medical history speaks for you." plus an interactive 3D-tilting Wallet-style ID card (pointer tilt with spring; disabled on touch and under reduced motion) with a live scannable QR. The QR encodes window.location.origin so it never points at a real patient; label the card "Demo card".
3. Section 2, sticky scroll story with 140px vertical padding: Build Your Profile; Doctor-Verified Clinical Sync; One-Scan Roadside Triage. Each step has a visual built from real components, not screenshots: a profile form fragment; a clinician editing allergy chips; a phone frame with a miniature triage view and a pressed call button. Use CSS position: sticky plus IntersectionObserver for the active step; reveals follow rule 01.
4. Section 3, Trust and security signals (three columns at most): revocable UUID token, home address hidden on public scans, clinician-verified badges.
5. Footer: short, with the line "Umbrella supports emergency responders and does not replace professional medical judgement."
6. Mobile first; check at 375, 768 and 1280. The LCP element is text, not an image. Lighthouse mobile performance 90 or higher (report it).

Acceptance: /verify; /design-review with zero violations; no purple gradients; no four-column grids.
Finish: update PROGRESS.md, commit, STOP.
```

---

### 8.13 Phase 10: QA and hardening (Planning, High thinking)

```text
Phase 10: QA and hardening. Run /start-phase first. Planning mode.
Read: AGENTS.md in full; DECISIONS in full; SPEC section 8.
Skills: web-design-guidelines, vercel-react-best-practices, supabase-postgres-best-practices, webapp-testing, improve-codebase-architecture, diagnose.
Report findings first, then fix in small commits.

Tasks:
1. Full /security-audit. Fix every FAIL.
2. /design-review across every route. Fix violations.
3. Run vercel-react-best-practices over src/app and src/components: waterfalls, bundle size, unnecessary "use client".
4. Accessibility pass: keyboard-only through signup, patient portal and doctor flow; screen-reader labels; contrast of every token pair; reduced motion; 200% zoom.
5. Performance: report the `next build` route table; check the emergency route against the D13 budget; Lighthouse mobile for /, /emergency/<token> and /portal/patient.
6. Database review with supabase-postgres-best-practices: an index on every policy and foreign-key column; EXPLAIN the doctor lookup queries; fix.
7. Tests: typecheck, lint, vitest, playwright (mobile + desktop) and build must all pass. Add .github/workflows/ci.yml running typecheck, lint, test and build (no secrets; e2e optional).
8. improve-codebase-architecture: propose refactors; apply only the clearly safe ones and ask before the rest.
9. Write docs/KNOWN-LIMITATIONS.md from DECISIONS D5 and D18 plus anything you found.

Acceptance: all checks green and a list of residual risks.
Finish: update PROGRESS.md, commit, STOP.
```

---

### 8.14 Phase 11: Deploy (Planning)

```text
Phase 11: Deploy. Run /start-phase first. Planning mode. Skill: deploy-to-vercel (optional).
Prerequisite (me): every phase is merged to main and pushed to GitHub.

Agent tasks:
1. Write docs/DEPLOY.md with the steps below, adapted to what you see in the repo.
2. Run the pre-deploy checks: build, env var names match .env.example, security headers present, no secrets in git history (git grep for service_role and the Supabase URL).
3. Do NOT run any deploy command. List the human steps.

Human steps I will do:
a. Vercel: Add New > Project > import the GitHub repo. Framework Next.js. Environment variables NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY for Production and Preview. Set the function region close to the Supabase region (Mumbai: bom1).
b. Supabase > Authentication > URL Configuration: Site URL is the production URL; add https://<project>.vercel.app/** and the custom domain /** as redirect URLs. Turn Confirm email ON.
c. Smoke test on the production URL: patient signup, QR scan from a phone, doctor approval SQL, doctor verify flow, regenerate token.
d. If any non-synthetic data will ever be stored, create a separate umbrella-prod Supabase project, run the same migration and tests there, and get a privacy review first.
Finish: update PROGRESS.md, commit, STOP.
```

---

## Part 9: When the agent misbehaves

| Symptom | What to say or do |
|---|---|
| It starts the next phase | "Stop. That breaks AGENTS.md 4.1. Revert unrelated changes (use git status) and finish only Phase N." |
| It invents tables or columns | "Read src/lib/supabase/types.ts. List every column you used and where it exists." |
| Raw hex colours, purple gradients, heavy shadows | Run `/design-review`. |
| Fake data, dead buttons, TODOs | "AGENTS.md 4.3: implement it for real or remove it and report." |
| It loops on one error | Stop. New conversation: paste the exact error and say "use the diagnose skill". |
| Long conversation gets sloppy | Start a new conversation and run `/start-phase`. The ledger carries the context. |
| A skill is ignored | Name it in your message. Check `ls .agents/skills` and that the skill's `SKILL.md` has a description line. |
| A rule is ignored | Check the file is in `.agents/rules/`, under 12,000 characters, and restart Antigravity. |
| Wrong file name for request interception (middleware vs proxy) | Point it at rule 03: check the next version in package.json first. |
| It ran a command you did not approve | Re-check the terminal execution setting from step 1.2. |
| It conflicts with a skill's advice | Remind it: DECISIONS > SPEC > AGENTS > skills. |

---

## Part 10: Go-live checklist (you, not the agent)

- [ ] All checks in `rls_smoke.sql` pass on the project you are deploying to.
- [ ] A doctor self-signup stays "pending" and sees no patient data.
- [ ] View-source of `/emergency/<token>` contains no address and no dependents.
- [ ] A random UUID on `/emergency/` shows the generic not-found page.
- [ ] A QR printed from the production URL scans correctly from a phone.
- [ ] Confirm email is ON in production.
- [ ] `git grep -i service_role` returns nothing; `.env.local` was never committed.
- [ ] Only synthetic data is stored, or a privacy and legal review is done.
- [ ] Check what backup options your Supabase plan includes before storing anything you care about.
- [ ] Lighthouse mobile on the emergency page meets the D13 budget.

### After v1 (backlog)
- `date_of_birth` instead of age
- Admin screen for approving doctors
- Audit log of who viewed or edited records
- Rate limiting on lookups
- SMS alerts to the emergency contact
- Localisation
- Apple / Google Wallet passes

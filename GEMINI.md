# GEMINI.md: Antigravity-only extras

AGENTS.md is the single source of project rules. Read it first. This file only adds Antigravity-specific behaviour and never overrides AGENTS.md.

- Planning-mode phases (1, 3, 10, 11): produce the implementation plan first, list every file you will touch, and wait for approval before coding.
- Fast-mode phases: still restate the goal in 3 lines before editing.
- UI verification: use the browser tool on localhost at 375x667 and 1280x800 and attach the screenshots to your walkthrough.
- Think hard on RLS, auth redirects, token handling and anything in the emergency route. Keep reasoning short on mechanical edits.
- Do not narrate each step. Report: what changed, what you ran, what passed or failed, what is left.
- Never invent library APIs. If unsure about an API (Supabase, Next.js, framer-motion, qrcode.react, jspdf), read the installed package's types or README in node_modules before writing code.

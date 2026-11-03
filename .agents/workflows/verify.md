---
description: Run all checks and visually verify the current work
---
1. Run `npm run typecheck && npm run lint && npm run build`. Fix failures you caused.
2. Run `npm run test` if tests exist.
3. Start `npm run dev` if it is not running. With the browser tool load every route touched this phase at 375x667 and 1280x800 and screenshot each.
4. Check: no console errors; keyboard-only navigation works; focus ring visible; no horizontal scroll; critical data above the fold on portal and emergency routes.
5. Report a table: check | result | evidence. Include failures. Do not fix unrelated issues.

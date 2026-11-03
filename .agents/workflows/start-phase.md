---
description: Begin a build phase safely (read context, restate goal, list files, wait for go)
---
1. Read docs/PROGRESS.md, docs/DECISIONS.md, AGENTS.md and the SPEC sections named in the phase prompt.
2. Run `git status` and `git branch --show-current`. If not on phase/<n>-<slug>, say so and ask to create it.
3. Reply with: the goal in 3 lines, files to create or change, spec conflicts or risks, and the exact checks you will run at the end.
4. If anything conflicts with DECISIONS or SPEC, ask ONE question and wait. Otherwise proceed.

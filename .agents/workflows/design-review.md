---
description: Review UI against the Umbrella design system and Vercel web interface guidelines
---
1. Run the web-design-guidelines skill on the files changed in this phase (git diff --name-only main). Fix violations you caused.
2. Check against rule 01: tokens only (search for raw hex outside globals.css), spacing per route, hairline colour vs surface, springs from src/lib/motion.ts, reduced-motion support, forbidden patterns.
3. Check the contrast of every text/background pair against WCAG AA (4.5:1 normal text, 3:1 large). Fix with the colours in DECISIONS D10.
4. Screenshot at 375x667 and 1280x800.
5. Report violations as a file:line list plus what you changed.

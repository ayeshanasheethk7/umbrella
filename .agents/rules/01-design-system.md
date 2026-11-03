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

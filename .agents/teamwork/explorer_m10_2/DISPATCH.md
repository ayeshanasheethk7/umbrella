# Task Assignment: Explorer M10-2 (UI Responsiveness, Design System, Accessibility & Performance Audit)

## Objective
Execute a deep-dive granular forensic audit across UI Responsiveness, Design Tokens, Accessibility (WCAG AA), Motion Physics, and Performance for Milestone M10 / Requirement R4 (28-Point System Audit).

## Identity & Paths
- **Identity**: `explorer_m10_2`
- **Archetype**: `teamwork_explorer`
- **Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m10_2`
- **Parent Conversation ID**: `67ffe189-e990-4d97-88ab-d83ec157f73f`
- **Original Request**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md`
- **Project Scope**: `c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md`
- **Design System Rules**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\rules\01-design-system.md`

## Audit Scope & Dimensions
Audit and rate the following specific points (11 to 20):
11. **Point 11 (Design Tokens & Color Palette)**: Audit `.agents/rules/01-design-system.md` adherence: system-canvas `#F5F5F7`, surface `#FFFFFF`, primary `#0071E3`, destructive `#FF3B30`, warning `#FF9500`, success `#34C759`. Verify zero white hairlines on white surfaces and zero heavy shadows.
12. **Point 12 (Mobile Responsiveness - 375x667)**: Audit viewport layout on 375x667 mobile screens for Patient portal, Doctor portal, and Emergency triage route. Verify zero horizontal overflow/scroll.
13. **Point 13 (Desktop Workstation - 1280x800)**: Audit viewport layout on 1280x800 desktop screens: multi-column bento grids, sticky sidebars, clinical editor ergonomics.
14. **Point 14 (Touch Target Ergonomics)**: Verify minimum 44x44px touch targets across all interactive buttons, inputs, and links; verify 56px sticky touch target for emergency call button.
15. **Point 15 (WCAG AA Contrast Ratios)**: Audit color contrast across all UI surfaces: minimum 4.5:1 for normal text and 3:1 for interactive controls/borders. Verify color is never the sole signal for state.
16. **Point 16 (Apple Spring Motion Physics - N8)**: Verify all portal animations use `appleSpring` from `src/lib/motion.ts` (stiffness 300, damping 30) with `prefers-reduced-motion` compliance. Zero linear or ease-in-out easing.
17. **Point 17 (Emergency Route Motion Prohibition - D13)**: Verify `/emergency/[token]` ships zero framer-motion library imports for zero-delay roadside rendering.
18. **Point 18 (Async View States)**: Verify every async page/component provides loading, empty, and error states with plain English messages.
19. **Point 19 (Semantic Landmarks & Focus Rings)**: Audit semantic HTML (`<main>`, `<nav>`, `<header>`, `<dialog>`), visible `:focus-visible` focus rings, and screen-reader aria labels.
20. **Point 20 (QR Code Display & CR80 PDF Geometry)**: Verify QRCodeSVG renders at level Q with phone-scanning viewport; verify printable card matches CR80 ISO 85.6x54mm specs at 300 DPI.

Provide ratings (Score / 10), verified evidence with line numbers, and concrete remediation recommendations (if any).
Write your findings to `report.md` and `handoff.md` and notify parent via `send_message`.


## 2026-11-02T17:36:00Z
Received system dispatch:
Target Milestone: M10 / Requirement R4 (28-Point System Audit).
Audit Points 11 to 20:
- Design tokens, 375x667 mobile & 1280x800 desktop ergonomics, touch targets (44px / 56px), WCAG AA contrast, Apple spring physics (N8), zero framer-motion in emergency (D13), async states, semantic landmarks, QR and CR80 card specs.
- Rate each point (Score / 10), cite line numbers, and identify any findings.
- Write report.md and handoff.md and notify parent via send_message.

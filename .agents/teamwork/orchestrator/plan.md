# Plan: Umbrella Autonomous End-to-End Implementation

## Overview
Umbrella is an emergency medical ID platform with three surfaces:
1. Patient portal (manage medical ID, conditions, allergies, medications, contacts, QR studio, token rotation)
2. Doctor portal (search patient, view read-only safety banner, record clinical edits/vitals/notes)
3. Zero-login public emergency triage page (`/emergency/[token]`) via SECURITY DEFINER RPC `get_emergency_triage_by_token`

## Execution Strategy (Project Pattern)
We execute strictly via subagents adhering to all constraints:
- Survey phase: 3 explorers/spec miners to survey UMBRELLA_BUILD_KIT.md, existing files, rules, and docs.
- Foundation & MCP Swarm Setup (R1): Worker builds foundational files, MCP configs, coordination plan, and skill integrations. Reviewers + Challenger verify.
- QA Challenger Audit & Refinement (R2): Independent QA Challenger tests and audits foundation, configurations, and plans. Remediate all gaps.
- Full-Scale Build (R3): Sub-orchestrators / iterative milestones implementing the complete application (DB, Auth, Patient, Doctor, Emergency, QR Studio, E2E tests).
- Granular Audit & Remediation (R4): Comprehensive audit across Security, RLS, Accessibility, Performance, UI. Remediation and final green test verification.

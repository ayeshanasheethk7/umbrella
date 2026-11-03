# Task Assignment: Explorer M10-1 (Security, RBAC, RLS & Secret Hygiene Audit)

## Objective
Execute a deep-dive granular forensic audit across Security, RBAC, RLS Policies, Column Grants, and Secret Hygiene for Milestone M10 / Requirement R4 (28-Point System Audit).

## Identity & Paths
- **Identity**: `explorer_m10_1`
- **Archetype**: `teamwork_explorer`
- **Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m10_1`
- **Parent Conversation ID**: `67ffe189-e990-4d97-88ab-d83ec157f73f`
- **Original Request**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md`
- **Project Scope**: `c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md`
- **Coordination Document**: `c:\Users\DELL\ayesha_pro\medi_qr\docs\SWARM_COORDINATION.md`

## Audit Scope & Dimensions
Audit and rate the following specific points (1 to 10):
1. **Point 1 (N1 - Public Zero-Login Isolation)**: Verify that `/emergency/[token]` reads exclusively through `get_emergency_triage_by_token`, anon role has 0 table grants, and `residential_address` & `spouse_dependents` are completely excluded.
2. **Point 2 (N2 - Persistent Safety Banner)**: Verify that `/portal/doctor` displays patient name, age, blood group, emergency contact at all times during clinical editing.
3. **Point 3 (N3 - Server Auth Identification)**: Verify all server actions and route handlers use `supabase.auth.getUser()`, never `getSession()`. Verify role is read from `accounts` table on server, never JWT metadata.
4. **Point 4 (N4 - Secret Hygiene)**: Audit the entire repository for zero occurrences of `service_role` in code, comments, `.env` templates, or SQL.
5. **Point 5 (N5 - Zero Mock Auth)**: Verify `/login` and `/signup` call genuine `signInWithPassword` and `signUp`.
6. **Point 6 (RLS Table Coverage)**: Verify RLS is enabled on all 4 core tables: `accounts`, `patient_profiles`, `clinical_records`, `appointments`.
7. **Point 7 (Column-Level Grants)**: Verify `role`, `doctor_status`, `patient_code`, and `qr_token` cannot be updated by arbitrary authenticated users.
8. **Point 8 (Doctor Onboarding Gate)**: Verify pending doctors cannot access patient records until approved (`is_approved_doctor()`).
9. **Point 9 (Optimistic Concurrency & Audit Triggers)**: Verify `clinical_records` enforces timestamp locking on update and audit triggers log updates.
10. **Point 10 (Injection Defense)**: Verify search inputs escape `%`, `_`, `(`, `)`, `,` and reject wildcard flooding.

Provide ratings (Score / 10), verified evidence with line numbers, and concrete remediation recommendations (if any).
Write your findings to `report.md` and `handoff.md` and notify parent via `send_message`.


## 2026-11-02T17:35:53Z
Sender: 67ffe189-e990-4d97-88ab-d83ec157f73f
Content:
You are explorer_m10_1.
Your archetype is teamwork_explorer.
Your working directory is: c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m10_1
Your parent is teamwork_orchestrator (conversation ID: 67ffe189-e990-4d97-88ab-d83ec157f73f).

MANDATORY INSTRUCTION: Read the original user request at:
c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\ORIGINAL_REQUEST.md
before starting your work.

Your task assignment and instructions are in:
c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m10_1\DISPATCH.md

Target Milestone: M10 / Requirement R4 (28-Point System Audit).
Audit Points 1 to 10:
- Security, RBAC, RLS policies, column grants, secret hygiene, zero service_role, zero getSession, doctor approval gate, optimistic concurrency, and injection defenses.
- Rate each point (Score / 10), cite line numbers, and identify any findings.
- Write report.md and handoff.md and notify parent via send_message.

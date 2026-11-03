# QA Challenger M1-1: Adversarial Foundation & Setup Audit Report

**Audit Date**: 2026-11-01T19:30:00Z  
**Auditor**: QA Challenger M1-1 (`teamwork_challenger`, Role: Critic & Specialist)  
**Target Milestone**: Milestone 1 (Foundation Layers, MCP Setup, Swarm Skills & Governance)  
**Directives Evaluated**: `ORIGINAL_REQUEST.md`, `UMBRELLA_BUILD_KIT.md`, Worker M1 Deliverables  
**Overall Verdict**: **REQUEST_CHANGES** (Actionable remediations required prior to Phase 0 build kickoff)

---

## 1. Executive Summary

As an independent, adversarial QA Challenger, M1-1 conducted a rigorous empirical audit of the Umbrella foundation layers, configurations, character limits, MCP setups, swarm coordination playbooks, and adherence to non-negotiables N1–N10.

While the foundation layers (`AGENTS.md`, `GEMINI.md`, `.agents/rules/*`, `.agents/workflows/*`, `docs/SPEC.md`, `docs/DECISIONS.md`) show high fidelity to the Build Kit, the adversarial audit uncovered **three critical defects**, **two architectural discrepancies**, and **one operational blocker** that must be remediated:
1. **Critical Security / N4 Conflict in MCP Config**: `mcp_config.json` embeds `"SUPABASE_SERVICE_ROLE_KEY"`, which directly violates Non-Negotiable N4's prohibition against service-role keys in repo configs, creates a false-security vulnerability in MCP-driven testing (RLS bypass), and causes the pre-deployment leak check in `docs/DEPLOY.md` to fail.
2. **Interface Contract Mismatch in `PROJECT.md`**: `PROJECT.md` defines public emergency RPC keys (`emergency_contacts`, `conditions`, `current_medications`, `past_surgeries`, `doctor_verified_at`) that contradict the actual database schema and reference implementation in `rls-patterns.sql` (`emergency_contact_name`, `medical_conditions`, `current_medication`, `previous_surgeries`, `updated_at`).
3. **Migration Filename & Tooling Discrepancy in `PROJECT.md`**: `PROJECT.md` specifies `supabase/migrations/20261101_init_schema.sql` (contradicting `0001_umbrella_schema.sql` in Build Kit Part 3/4/6/8 and `docs/SPEC.md`), and pins Next.js 14 / React 18 (contradicting DECISIONS D16).
4. **Environment Execution Blocker**: Neither `node`, `npm`, `npx`, nor `git` is currently available in the Windows execution PATH, which blocks MCP server spawning and Phase 0 scaffolding.
5. **Character Cap Edge Case**: `.agents/skills/umbrella-supabase-rls/references/rls-patterns.sql` is 13,845 characters. While rules files in `.agents/rules/` are strictly compliant (<12k), any blind character-cap enforcement on skill directories could truncate SQL reference logic.
6. **Workspace Hygiene Violation**: `worker_m1` created `verify_chars.ps1` inside `.agents/teamwork/worker_m1/`, violating Subagent Handling Law 1 (metadata-only in `.agents/teamwork/`).

---

## 2. Granular Audit Findings

### Finding 1: [Critical / Security] Presence of `SUPABASE_SERVICE_ROLE_KEY` in `mcp_config.json`
- **Location**: `C:\Users\DELL\.gemini\config\mcp_config.json` line 20 and `.gemini/mcp_config.json` line 20:
  ```json
  "SUPABASE_SERVICE_ROLE_KEY": "PLACEHOLDER_FOR_LATER_PROVISION_IF_AUTHORIZED"
  ```
- **Violations**:
  - **Non-Negotiable N4**: *"v1 uses the anon/publishable key only. The service_role key must never appear in code, .env.example, logs, commits or chat."*
  - **`UMBRELLA_BUILD_KIT.md` §1.3 & §1.7**: *"Never copy or use the service_role key anywhere in this project. Never paste the service_role key or your DB password into the agent chat."*
  - **`docs/DEPLOY.md` Section 1**: Mandates that `git grep -i "SUPABASE_SERVICE_ROLE_KEY"` and `git grep -i "service_role"` must return **ZERO** matches. Having this key in `.gemini/mcp_config.json` will fail pre-deployment validation immediately.
- **Attack Scenario & Blast Radius**:
  If an operator or agent populates this placeholder with a live `service_role` key, the Supabase MCP server will execute queries with PostgreSQL superuser privileges, completely bypassing Row Level Security. Testing via MCP will produce false positives—queries will appear to succeed even if policies and column grants are broken or missing. Furthermore, committing `.gemini/mcp_config.json` introduces persistent secret-scanning exposure.
- **Remediation**:
  Remove `"SUPABASE_SERVICE_ROLE_KEY"` entirely from both `C:\Users\DELL\.gemini\config\mcp_config.json` and `.gemini/mcp_config.json`. Configure Supabase MCP strictly with `SUPABASE_URL` and `SUPABASE_ANON_KEY`, or use a Personal Access Token (`SUPABASE_ACCESS_TOKEN`) for management APIs if authorized.

---

### Finding 2: [High / Interface Contract] RPC Return Key Mismatch in `PROJECT.md`
- **Location**: `PROJECT.md` line 49 vs `rls-patterns.sql` lines 187–205:
  - **`PROJECT.md` line 49**:
    ```text
    keys: patient_code, full_name, age, blood_group, contact_phone, emergency_contacts (jsonb array), conditions (text[]), allergies (text[]), current_medications (text[]), past_surgeries (text[]), is_doctor_verified (boolean), doctor_verified_at (timestamptz)
    ```
  - **Reference Implementation (`rls-patterns.sql` & Phase 4 §8.7)**:
    ```sql
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
    ```
- **Discrepancies**:
  1. `PROJECT.md` specifies `emergency_contacts` (jsonb array), whereas the database and UI expect flat fields `emergency_contact_name`, `emergency_contact_phone`, `emergency_contact_relation`.
  2. `PROJECT.md` specifies `conditions (text[])`, database produces `medical_conditions`.
  3. `PROJECT.md` specifies `current_medications (text[])`, database produces `current_medication (jsonb)`.
  4. `PROJECT.md` specifies `past_surgeries (text[])`, database produces `previous_surgeries (jsonb)`.
  5. `PROJECT.md` specifies `doctor_verified_at`, database produces `updated_at`.
- **Attack Scenario & Blast Radius**:
  If Phase 4 (`/emergency/[token]`) is developed against `PROJECT.md`'s contract, the emergency page will attempt to read `data.conditions` and `data.emergency_contacts`, resulting in `undefined` values. Critical triage data (allergies, emergency phone number) will fail to render during roadside emergency scans.
- **Remediation**:
  Update `PROJECT.md` Section 4 ("Interface Contracts") to synchronize verbatim with the JSON output of `get_emergency_triage_by_token` from `rls-patterns.sql`.

---

### Finding 3: [High / Architecture Alignment] Migration Name & Tooling Conflicts in `PROJECT.md`
- **Location**: `PROJECT.md` lines 3–4, 91:
  - Line 91 specifies: `supabase/migrations/20261101_init_schema.sql`.
  - Lines 3–4 specify: `Next.js 14 App Router, React 18`.
- **Contradictions with Build Kit & Spec**:
  - `UMBRELLA_BUILD_KIT.md` Part 3, Part 4, Part 6, and `docs/SPEC.md` line 128 explicitly mandate: `supabase/migrations/0001_umbrella_schema.sql`.
  - `docs/DECISIONS.md` D16 explicitly states: *"Tooling. Use whatever `create-next-app@latest` produced; do not downgrade to match 'Next 14/15' or 'React 18'."*
- **Attack Scenario & Blast Radius**:
  Using `20261101_init_schema.sql` creates split migration paths where runbooks refer to `0001_umbrella_schema.sql` while other documentation references timestamped migrations. Hardcoding Next 14 / React 18 invites unauthorized package downgrades that conflict with Tailwind v4 and modern `@supabase/ssr` requirements.
- **Remediation**:
  Update `PROJECT.md` line 91 to `0001_umbrella_schema.sql` and align lines 3–4 with DECISIONS D16.

---

### Finding 4: [Medium / Environment] Execution Toolchain Missing from Host PATH
- **Location**: System environment / terminal execution.
- **Observation**:
  - `node --version`: `The term 'node' is not recognized`
  - `npm --version`: `The term 'npm' is not recognized`
  - `npx --version`: `The term 'npx' is not recognized`
  - `git --version`: `The term 'git' is not recognized`
- **Attack Scenario & Blast Radius**:
  While declarative configurations are complete, autonomous execution of Phase 0 (`npx create-next-app`, package installation), MCP server initialization (`npx @modelcontextprotocol/server-memory`), and git branch management cannot execute until the toolchain is accessible in the terminal environment.
- **Remediation**:
  Ensure Node.js LTS (20.9+ or 22 LTS) and Git are installed and their paths are registered in the Windows system environment PATH before Phase 0 dispatch.

---

### Finding 5: [Medium / Specification Nuance] Reference SQL Character Count
- **Location**: `.agents/skills/umbrella-supabase-rls/references/rls-patterns.sql` (13,845 characters).
- **Observation**:
  `UMBRELLA_BUILD_KIT.md` Part 0 notes: *"Antigravity caps each rules file at 12,000 characters"*.
  `ORIGINAL_REQUEST.md` Requirement R1 states: *"adhering to the 12,000 character limit on rules and kit specifications"*.
  Our empirical script confirmed that all rules in `.agents/rules/*.md` and `AGENTS.md` are well below 12,000 chars (1,289 to 5,511 chars). However, `rls-patterns.sql` is 13,845 characters (exact copy of kit §6.2).
- **Risk**:
  If an automated lint or agent ingestion tool applies a flat 12k cutoff to all files within `.agents/`, the bottom of `rls-patterns.sql` (RPC 3 and test harness patterns) could be truncated.
- **Remediation**:
  Clarify in `SWARM_COORDINATION.md` that the 12,000 character limit applies strictly to always-on rules (`.agents/rules/*`, `AGENTS.md`, and top-level `SKILL.md` files).

---

### Finding 6: [Low / Hygiene] Script Placement in `.agents/teamwork/`
- **Location**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m1\verify_chars.ps1`
- **Observation**:
  Worker M1 committed a `.ps1` script to its teamwork workspace directory.
- **Violation**:
  Subagent Handling SOP Law 1: *"` .agents/teamwork/` must NEVER contain source code, test files, or application assets."*
- **Remediation**:
  Subagents must execute verification scripts via standard PowerShell/Python stdin streams (`@' ... '@ | python -`) without saving script files into `.agents/teamwork/`.

---

## 3. Empirical Verification Results

| Dimension / Asset | Verification Method | Result | Status |
|---|---|---|---|
| **Character Caps: Rules & Docs** | Stdin Python character measurement | All rules (1.2k–3.7k), `AGENTS.md` (5.5k), `SPEC.md` (9.9k) < 12k | **PASS** |
| **Character Caps: Skills References** | Stdin Python character measurement | `rls-patterns.sql` = 13,845 chars | **FLAGGED** (Advisory) |
| **Fidelity: `AGENTS.md` vs Kit** | Unified diff against `UMBRELLA_BUILD_KIT.md` | 0 diff lines | **PASS** |
| **Fidelity: `GEMINI.md` vs Kit** | Unified diff against `UMBRELLA_BUILD_KIT.md` | 0 diff lines | **PASS** |
| **Fidelity: Rules 01–04 vs Kit** | Unified diff against `UMBRELLA_BUILD_KIT.md` | 0 diff lines | **PASS** |
| **Fidelity: Workflows vs Kit** | Unified diff against `UMBRELLA_BUILD_KIT.md` | 0 diff lines | **PASS** |
| **Fidelity: `docs/DECISIONS.md`** | Unified diff against `UMBRELLA_BUILD_KIT.md` | 0 diff lines | **PASS** |
| **Fidelity: `docs/PROGRESS.md`** | Unified diff against `UMBRELLA_BUILD_KIT.md` | 0 diff lines | **PASS** |
| **SPEC.md Formatting Repairs** | Inspected lines 48 & 97, regex for stray `s` | ` ```css ` present, ` ```text ` present, no stray `s` | **PASS** |
| **MCP Syntax & Schema** | `json.loads()` validation | Valid JSON, 3 servers (`memory`, `supabase`, `vercel`) | **PASS** |
| **MCP Security Hygiene (N4)** | Regex scan for `service_role` | `SUPABASE_SERVICE_ROLE_KEY` placeholder present | **FAIL** (Blocker) |
| **Interface Contract Sync** | Diff `PROJECT.md` §4 vs `rls-patterns.sql` | 5 field mismatches in `get_emergency_triage_by_token` | **FAIL** (Blocker) |
| **Swarm Coordination Plan** | Evaluated roles, phase matrix, isolation | Sound architecture, single-writer & 5-component handoffs enforced | **PASS** |
| **Host Toolchain Liveness** | Execution of `node`, `npm`, `npx`, `git` | CommandNotFoundException on all four tools | **FAIL** (Operational) |

---

## 4. Remediation Punchlist (Action Items for Orchestrator & Worker)

Before Milestone 1 can be formally APPROVED and Phase 0 build initiated, the following remediation steps must be executed:

1. **Fix MCP Security Hygiene**:
   - In `C:\Users\DELL\.gemini\config\mcp_config.json` and `.gemini/mcp_config.json`, delete the line:
     `"SUPABASE_SERVICE_ROLE_KEY": "PLACEHOLDER_FOR_LATER_PROVISION_IF_AUTHORIZED"`.
   - Ensure only `SUPABASE_URL` and `SUPABASE_ANON_KEY` are present under `supabase.env`.

2. **Synchronize `PROJECT.md` Interface Contracts**:
   - Update `PROJECT.md` line 49 to list the exact return keys of `get_emergency_triage_by_token`:
     `full_name`, `contact_phone`, `patient_code`, `age`, `blood_group`, `emergency_contact_name`, `emergency_contact_phone`, `emergency_contact_relation`, `medical_conditions` (text[]), `current_medication` (jsonb), `previous_surgeries` (jsonb), `allergies` (text[]), `last_appointment_date` (timestamptz), `is_doctor_verified` (boolean), `updated_at` (timestamptz).
   - Update `PROJECT.md` line 91 migration path to `supabase/migrations/0001_umbrella_schema.sql`.
   - Align stack description in lines 3–4 with DECISIONS D16.

3. **Resolve Environment Path for Build Toolchain**:
   - Ensure Node.js 20.9+ / 22 LTS and Git are available in the shell environment.

4. **Clean Workspace Hygiene**:
   - Remove `verify_chars.ps1` from `.agents/teamwork/worker_m1/`.

---

## 5. Challenger Verdict

**VERDICT: REQUEST_CHANGES**  
The foundation documentation and swarm playbooks are structurally impressive and closely adhere to the Umbrella specification. However, because medical application safety is paramount, the security risk of `SUPABASE_SERVICE_ROLE_KEY` in MCP configurations and the interface contract divergence in `PROJECT.md` cannot be passed into the build phase. Upon application of the 4 items in the Remediation Punchlist, Milestone 1 will be immediately ready for final sign-off.

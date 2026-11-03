Invoke the full team, structured as hierarchical swarms that include reviews and challengers. Set up the foundational configuration and MCP/skill integrations from UMBRELLA_BUILD_KIT.md, validate and refine the setup through an independent QA challenger review, and execute an autonomous, end-to-end full-scale implementation through to final completion, comprehensive audit, remediation, and testing.

Working directory: c:\Users\DELL\ayesha_pro\medi_qr
Integrity mode: development

## Verification Resources

- Specification and Build Kit: c:\Users\DELL\ayesha_pro\medi_qr\UMBRELLA_BUILD_KIT.md

## Requirements

### R1. Foundation Layers, MCPs, and Swarm Skill Setup
Generate and configure all foundation layers defined in `UMBRELLA_BUILD_KIT.md` (`AGENTS.md`, `GEMINI.md`, `.agents/rules/*`, `.agents/workflows/*`, `.agents/skills/*`, `docs/*`), adhering to the 12,000 character limit on rules and kit specifications. Establish and configure required MCP integrations (Memory MCP, Supabase MCP with credentials placeholder for later provision, Vercel MCP for deployment stages) and acquire/integrate subagent coordination skills (including graphify and subagent handling skills) directly into workflows and agent behavior. Produce a structured coordination plan for team-lead level agents to distribute tasks across swarm members without inter-team conflicts.

### R2. QA Challenger Review and Iterative Refinement
Deploy a verification sub-agent with independent context and a challenging mindset to serve as a QA challenger. The challenger must conduct a rigorous review of the plan, configurations, MCP setups, workflows, skills, and documentation against `UMBRELLA_BUILD_KIT.md`, iteratively driving revisions until all deficiencies and gaps are resolved.

### R3. End-to-End Autonomous Build Execution
Autonomously execute the complete, full-scale implementation through to the final phase of the web application as defined in the build kit without stopping at simple scaffolding. Implement all client and server components, auth, database integrations, RLS policies, zero-login emergency triage, doctor and patient portals, and deployment configs according to the spec, maintaining clean code without bloat.

### R4. Granular System Audit, Rated Review, and Remediation
Conduct a deep-dive granular audit across all subsystems (security, RLS, accessibility, UI responsiveness, performance, and API hygiene). Compile a comprehensive rated review document detailing findings, execute systematic remediations to resolve every identified issue, and establish complete test coverage and system documentation before final reporting.

## Acceptance Criteria

### Foundation, MCPs, and Swarm Coordination
- [ ] `AGENTS.md`, `GEMINI.md`, rules in `.agents/rules/` (<12k chars each), workflows in `.agents/workflows/`, and docs in `docs/` match `UMBRELLA_BUILD_KIT.md`
- [ ] Memory MCP, Supabase MCP (configured for subsequent credential entry), and Vercel MCP configs are established
- [ ] Subagent management and knowledge skills (including graphify and subagent handling skills) are installed and integrated into workflow commands
- [ ] A structured coordination plan defining roles, responsibilities, and conflict-avoidance rules for lead agents and swarm subagents is documented

### QA Challenger Audit and Refinement
- [ ] Independent QA challenger audit report is generated evaluating the initial plan, configurations, and skills
- [ ] All action items, omissions, and rule violations flagged by the challenger are remediated and verified

### End-to-End Build and Implementation
- [ ] Scaffolding, database schema, RLS policies, RPC functions, and Next.js App Router surfaces (Patient, Doctor, Emergency triage route) are fully implemented
- [ ] Zero mock auth: Supabase authentication flows and role handling operate as specified
- [ ] Mobile (375x667) and desktop (1280x800) responsive UI implementations meet design tokens without placeholder stubs

### Granular Audit, Remediation, and Testing
- [ ] A granular, rated review document auditing all system layers (security, RLS, accessibility, performance) is produced
- [ ] All remediation items from the rated review are implemented and verified in the codebase
- [ ] Unit, integration, and E2E test suites (Vitest / Playwright) pass with zero errors
- [ ] Final project documentation reflecting the completed codebase is produced

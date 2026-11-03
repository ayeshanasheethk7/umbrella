# Adversarial Stress Test & QA Challenge Report: Milestone 1

**Agent**: Challenger M1-2 (`teamwork_challenger`)  
**Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\challenger_m1_2`  
**Evaluation Target**: Milestone 1 Deliverables (Foundation Layers, MCP Configurations, Subagent Coordination SOP, Docs)  
**Date**: 2026-11-01T19:30:00Z  

---

## Challenge Summary

**Overall risk assessment**: **HIGH**  

While Worker M1 successfully established the core foundation files under the 12,000-character ceiling and formatted `docs/SPEC.md` correctly, empirical adversarial stress testing exposed 5 significant defects and edge-case vulnerabilities across MCP configurations, security non-negotiables, subagent SOP recovery mechanics, and workspace directory discipline.

Most critically, `.gemini/mcp_config.json` contains the forbidden key string `SUPABASE_SERVICE_ROLE_KEY`, which directly violates Non-Negotiable **N4** and will cause immediate failure of the pre-deployment checks defined in `docs/DEPLOY.md` (`git grep -i "SUPABASE_SERVICE_ROLE_KEY"`). In addition, the subagent SOP lacks automated crash and hung-agent watchdog thresholds, which under Windows file-locking conditions leads to high-rate concurrency collisions.

---

## Challenges

### [Critical] Challenge 1: Forbidden `SUPABASE_SERVICE_ROLE_KEY` in Repo MCP Config Breaks Non-Negotiable N4 & Pre-Deploy Checks
- **Assumption challenged**: Worker M1 assumed declaring `"SUPABASE_SERVICE_ROLE_KEY": "PLACEHOLDER_FOR_LATER_PROVISION_IF_AUTHORIZED"` in `.gemini/mcp_config.json` is a safe placeholder.
- **Attack scenario**:
  1. `AGENTS.md` Rule 5 Non-Negotiable N4 states:
     > "N4. v1 uses the anon/publishable key only. The service_role key must never appear in code, .env.example, logs, commits or chat."
  2. `docs/DEPLOY.md` line 28–29 mandates pre-deploy secret scans:
     ```bash
     git grep -i "service_role"
     git grep -i "SUPABASE_SERVICE_ROLE_KEY"
     ```
     *"Both commands must return ZERO matches. If any matches are found, fail the check immediately and investigate."*
  3. Because `.gemini/mcp_config.json` is located inside the repository, running `git grep -i "SUPABASE_SERVICE_ROLE_KEY"` will return a hit on line 20, causing the pre-deploy gate to fail.
  4. Furthermore, `@supabase/mcp-server` operates via Supabase Personal Access Tokens (`SUPABASE_ACCESS_TOKEN`) or standard URL + anon key. It does not require a service role key.
- **Blast radius**: Pre-deployment gate failure in Phase 11, violation of core security non-negotiable N4, and potential accidental credential exposure if an operator enters an actual service role secret.
- **Mitigation**:
  1. Remove `"SUPABASE_SERVICE_ROLE_KEY"` entirely from `c:\Users\DELL\ayesha_pro\medi_qr\.gemini\mcp_config.json` and `C:\Users\DELL\.gemini\config\mcp_config.json`.
  2. If Supabase MCP needs administrative access for schema queries, configure `SUPABASE_ACCESS_TOKEN` (Personal Access Token) rather than the database-bypassing service role key, or add `.gemini/` to `.gitignore`.

---

### [High] Challenge 2: Runtime Unfeasibility of MCP Stdio Server Commands on Windows
- **Assumption challenged**: Worker M1 assumed defining `"command": "npx"` with `@modelcontextprotocol/server-memory`, `@supabase/mcp-server`, and `@vercel/mcp` is immediately executable.
- **Attack scenario**:
  1. Empirical execution check:
     `shutil.which("npx")` -> `NOT FOUND IN PATH`
     `shutil.which("node")` -> `NOT FOUND IN PATH`
     `subprocess.run(["npx", "--version"])` -> `FileNotFoundError: [WinError 2] The system cannot find the file specified`.
  2. Furthermore, on Windows OS, Node CLI tools are packaged as `.cmd` batch wrappers (`npx.cmd`). MCP clients executing child processes on Windows via `CreateProcessW` without `shell: true` or `.cmd` extension fail to resolve `npx` even after Node is installed.
- **Blast radius**: Antigravity or any MCP client will fail to boot all 3 configured MCP servers on launch, crashing background MCP processes.
- **Mitigation**:
  1. Document in `PROJECT.md` / `docs/DB-RUNBOOK.md` that Node.js 20+ must be added to system PATH before activating MCP servers.
  2. Note in MCP config documentation that Windows environments may require `cmd.exe /c npx` or `npx.cmd` depending on MCP client runner capabilities.

---

### [Medium] Challenge 3: Subagent SOP Missing Hung-Agent Watchdog & Crash Recovery Protocols
- **Assumption challenged**: Worker M1 assumed that stating "update progress.md every 5 minutes" in `subagent-handling/SKILL.md` is sufficient for swarm fault tolerance.
- **Attack scenario**:
  1. If a subagent process encounters an unhandled exception, OOM, or hangs on a network socket / infinite loop, it ceases updating `progress.md`.
  2. The SOP does not define:
     - **Watchdog Timeout Threshold**: At what elapsed time (e.g., 10 minutes or 15 minutes of stale `Last visited:` timestamp) does the Orchestrator declare the worker hung?
     - **Termination & Eviction**: How is the hung task terminated (e.g. `manage_task(Action='kill')`)?
     - **Atomic Write Discipline**: If an agent crashes midway through writing a 10KB spec or code file, a corrupt or truncated file remains.
  3. Empirical simulation of uncoordinated concurrent writes on Windows NTFS demonstrated **73 collisions out of 80 write attempts** (dirty reads and torn overwrites).
- **Blast radius**: Swarm deadlocks, silently hung agents blocking milestone progression, or truncated/corrupted deliverables.
- **Mitigation**:
  1. Add an explicit **Watchdog & Stalled Agent Recovery** section to `subagent-handling/SKILL.md`:
     - Heartbeat threshold: Maximum 10 minutes without update triggers `manage_task(Action='kill')`.
     - Invalidation: Mark task as failed, revert uncommitted changes, and respawn.
  2. Add an **Atomic Write Convention**: Write new content to `<file>.tmp`, verify integrity, then rename/move to target `<file>`.

---

### [Medium] Challenge 4: Prohibited Test Scripts Placed in `.agents/teamwork/` Folders
- **Assumption challenged**: Worker M1 assumed placing verification scripts (`verify_chars.ps1`) directly in its teamwork folder is acceptable.
- **Attack scenario**:
  1. System Rules & `subagent-handling/SKILL.md` Section 1.1 explicitly state:
     > "⚠️ `.agents/teamwork/` holds only agent metadata (plans, progress, handoffs). **NEVER** place source code, tests, or data files here."
  2. Review of the workspace reveals:
     - `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\worker_m1\verify_chars.ps1`
     - `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\auditor_m1_1\forensic_suite.ps1`
     - `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\auditor_m1_1\verify_mcp.ps1`
- **Blast radius**: Violates workspace layout compliance, polluting agent metadata space with executable PowerShell scripts.
- **Mitigation**:
  Move all test and verification scripts to a designated `scripts/` or `tests/` directory at the project root (e.g., `scripts/verify_chars.ps1`), keeping `.agents/teamwork/` strictly limited to markdown metadata (`BRIEFING.md`, `DISPATCH.md`, `progress.md`, `report.md`, `handoff.md`).

---

### [Low] Challenge 5: Inconsistency Between Root `PROJECT.md` and Orchestrator `PROJECT.md`
- **Assumption challenged**: Worker M1 updated root `PROJECT.md` without synchronizing the orchestrator mirror.
- **Attack scenario**:
  Diff between `PROJECT.md` (root) and `.agents/teamwork/orchestrator/PROJECT.md` reveals:
  - Root `PROJECT.md` line 61 uses ` ```text ` code fence.
  - Orchestrator `PROJECT.md` line 61 uses ` ``` ` without language specifier.
  - Formatting differences in directory tree indentations.
- **Blast radius**: Ambiguity on single source of truth for swarm leads.
- **Mitigation**:
  Enforce that `c:\Users\DELL\ayesha_pro\medi_qr\PROJECT.md` at root is the authoritative master, and remove or synchronize outdated copies in orchestrator subdirectories.

---

## Stress Test Results

| Test Scenario | Input / Attack Payload | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|---|
| **ST-01: MCP Strict JSON Parsing** | Current `mcp_config.json` | Valid RFC 8259 JSON | Clean parse (3 servers: memory, supabase, vercel) | **PASS** |
| **ST-02: Trailing Comma Resilience** | `{"mcpServers": {"memory": {"command": "npx"}},}` | Strict parser rejection | `JSONDecodeError: Illegal trailing comma` | **PASS** |
| **ST-03: Comments in MCP Config** | `// comment` and `/* block */` | Strict parser rejection | `JSONDecodeError: Expecting property name` | **PASS** |
| **ST-04: Duplicate Server Key Collision** | Duplicate `"srv"` keys | Detection of duplicate key | Parser silently overwrites first key with second key | **FAIL (Silent Overwrite)** |
| **ST-05: Path Traversal in Server Name** | `{"mcpServers": {"../../evil": ...}}` | Rejection of non-identifier keys | Parsed without error; no identifier validation | **FAIL (Missing Schema Validation)** |
| **ST-06: Windows Reserved Names in Keys** | Server named `"CON"`, `"NUL"` | Rejection of reserved device names | Parsed without error | **FAIL (Missing Schema Validation)** |
| **ST-07: Non-String Environment Values** | `{"PORT": 3000, "ACTIVE": true}` | Rejection of non-string env values | Parsed as JSON, but fails MCP schema validation | **FAIL (Schema Violation)** |
| **ST-08: Windows `npx` Path Resolution** | `shutil.which("npx")` | Executable found in PATH | `None` (FileNotFoundError / WinError 2) | **FAIL (Runtime Block)** |
| **ST-09: Forbidden Key Scan (`service_role`)** | Workspace text search | 0 hits in non-documentation files | Hit in `.gemini/mcp_config.json`: line 20 (`SUPABASE_SERVICE_ROLE_KEY`) | **FAIL (Rule N4 & Deploy Violation)** |
| **ST-10: Placeholder Token Scan** | Search for `TODO`, `FIXME`, `coming soon` | 0 dummy code stubs | Clean; tokens appear only in rule descriptions | **PASS** |
| **ST-11: Character Ceiling Audit** | 17 target files vs 12,000 char cap | All files < 12,000 chars | Highest: `docs/SPEC.md` (9,973 chars). All pass. | **PASS** |
| **ST-12: Concurrent File Overwrite Collisions** | 4 threads, 80 uncoordinated overwrites | Clean isolation | 73 out of 80 operations suffered race/dirty read collisions | **PASS (Proves Single-Writer Rule)** |
| **ST-13: Workspace Metadata Invariant** | Inspect `.agents/teamwork/` for scripts | Only metadata markdown files | Found `verify_chars.ps1`, `forensic_suite.ps1` | **FAIL (Layout Violation)** |

---

## Unchallenged Areas

- **Live Supabase SQL Schema Execution**: Out of scope for M1 (scheduled for Phase 1 / Milestone 3).
- **Next.js Package Installation & Scaffolding**: Out of scope for M1 (scheduled for Phase 0).

---

## Actionable Remediation Punchlist (Prerequisites for Approval)

1. [ ] **Fix Forbidden Key Violation**:
   Remove `"SUPABASE_SERVICE_ROLE_KEY"` from `c:\Users\DELL\ayesha_pro\medi_qr\.gemini\mcp_config.json` and `C:\Users\DELL\.gemini\config\mcp_config.json`. Configure with `SUPABASE_URL` and `SUPABASE_ANON_KEY` only.
2. [ ] **Relocate Test Scripts Out of `.agents/teamwork/`**:
   Move `worker_m1\verify_chars.ps1` and `auditor_m1_1\*.ps1` to `scripts/` to restore metadata-only purity of `.agents/teamwork/`.
3. [ ] **Update `subagent-handling/SKILL.md` with Fault Tolerance**:
   Add explicit 10-minute heartbeat timeout threshold, hung-agent termination via `manage_task`, and atomic file write recommendations.
4. [ ] **Synchronize `PROJECT.md`**:
   Align `.agents/teamwork/orchestrator/PROJECT.md` with root `PROJECT.md`.

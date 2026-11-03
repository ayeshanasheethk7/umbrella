---
name: subagent-handling
description: Teamwork subagent coordination standard operating procedure. Covers isolated workspace folders, single-writer rules, 5-component handoff reports, heartbeat liveness, hung-agent watchdog thresholds, and atomic write crash recovery.
---

# Subagent Handling Standard Operating Procedure

This skill defines the governance and execution protocol for coordinating subagents within hierarchical swarms on the Umbrella project. It guarantees deterministic progress, eliminates concurrency conflicts, prevents torn writes, and enforces rigorous verification standards.

---

## 1. Five Fundamental Laws of Subagent Coordination

1. **Workspace Folder Isolation**:
   - Every subagent is allocated an exclusive working directory: `.agents/teamwork/<agent_id>/`.
   - **Write Rule**: A subagent writes ONLY to its designated folder. It may never write directly to peer agent folders.
   - **Read Rule**: A subagent may read from any directory across the workspace to gain context.
   - **Prohibited Files**: `.agents/teamwork/` must NEVER contain source code, test files, or application assets. Never create files named `AGENTS.md` or `GEMINI.md` inside `.agents/teamwork/`.

2. **Single-Writer Rule (Conflict Avoidance)**:
   - Exactly one agent may hold exclusive write ownership over any production file or target directory at any time.
   - Cross-agent parallel edits to the same file are strictly prohibited.
   - When multiple agents contribute to a milestone, work must be partitioned strictly by file path or executed in phase-gated sequential turns.

3. **Liveness Heartbeat via `progress.md`**:
   - Each agent maintains a persistent `progress.md` in its directory.
   - Must include `Last visited: [ISO-8601 UTC timestamp]` updated at every meaningful execution step.
   - For long-running commands or background tasks, update `progress.md` at least once every 5 minutes as a liveness heartbeat.

4. **Situational Memory via `BRIEFING.md`**:
   - Every subagent initializes and maintains `BRIEFING.md` (<100 lines) as persistent working memory.
   - Contains immutable append-only sections:
     - `## 🔒 My Identity`: Archetype, roles, directory, milestone.
     - `## 🔒 Key Constraints`: Non-negotiables and exclusive ownership bounds.
   - Contains mutable sections: Task Summary, Key Decisions, Artifact Index, Change Tracker, Quality Status.

5. **Self-Contained 5-Component Handoff Protocol (`handoff.md`)**:
   Every task handoff must be completely self-contained, structured with these mandatory sections:
   - **1. Observation**: Verbatim file paths, line numbers, tool commands executed, exact error outputs. Quote directly.
   - **2. Logic Chain**: Step-by-step causal deduction connecting observations to technical decisions.
   - **3. Caveats**: Uninvestigated edge cases, assumptions, environment limitations. State "No caveats" if none.
   - **4. Conclusion**: Final verifiable status and concrete outcomes.
   - **5. Verification Method**: Specific commands (`npm run typecheck`, `npm run test`, `npm run build`), file inspection targets, and invalidation criteria.

---

## 2. Subagent Dispatch Lifecycle

```text
[ Orchestrator ]
       |
       | 1. Dispatches subagent with explicit scope & exclusive write ownership
       v
[ Subagent Initialized ]
       |
       | 2. Appends prompt to DISPATCH.md with UTC timestamp
       | 3. Initializes BRIEFING.md and progress.md
       | 4. Reads prerequisite specs (AGENTS.md, docs/SPEC.md, docs/DECISIONS.md)
       v
[ Execution & Verification ]
       |
       | 5. Modifies only owned targets; follows minimal-change principle
       | 6. Updates progress.md heartbeat (<5 min intervals)
       | 7. Runs typecheck, lint, test, build
       v
[ Handoff & Notification ]
       |
       | 8. Writes self-contained handoff.md and report.md
       | 9. Sends message to Orchestrator via send_message
       v
[ Orchestrator Verifies & Merges ]
```

---

## 3. Communication Protocol

- **Files for content delivery**: Reports (`report.md`), handoffs (`handoff.md`), specifications, code changes.
- **Messages for coordination**: Send brief notifications via `send_message` with recipient ID:
  ```text
  **Context**: [Milestone / Phase / Feature]
  **Content**: [Summary of completion or blocker]
  **Action**: [What the recipient is expected to do]
  ```

---

## 4. Hung-Agent Watchdog & Stalled Recovery Protocol

To ensure resilient swarm autonomy and prevent deadlocks on stalled processes:

1. **Watchdog Heartbeat Threshold (10 Minutes)**:
   - The Orchestrator monitors the `Last visited:` timestamp in every active worker's `progress.md`.
   - If an agent's heartbeat timestamp is older than **10 minutes** without tool activity or progress updates, the orchestrator flags the worker as stalled.
   - The Orchestrator checks task status via `manage_task(Action='status', TaskId=...)`.

2. **Termination & Eviction**:
   - If a stalled agent does not respond or update its heartbeat within the 10-minute threshold, the orchestrator terminates the background task using `manage_task(Action='kill', TaskId=...)`.
   - The agent's task state is formally marked as `FAILED / TIMED_OUT` in the orchestrator's `GATE_STATUS.md`.

3. **Hard Replacement Deadline (20 Minutes)**:
   - The Orchestrator enforces a hard **20-minute deadline** from initial stall detection to full replacement dispatch.
   - A replacement subagent is spawned with the original scope, taking ownership of the milestone.
   - The replacement inspects the stalled agent's workspace (`progress.md`, `BRIEFING.md`, intermediate artifacts) to preserve valid partial progress while discarding corrupted work.

---

## 5. Atomic Write Protocol & Crash Recovery

Windows NTFS file handles are prone to file-locking conflicts (sharing violations) and torn writes during concurrent access or sudden agent termination. The following rules govern file mutations:

1. **Atomic File Write Convention**:
   - For critical configuration, specification, or code files exceeding 2KB:
     1. Write full content to a temporary staging file: `<target_file>.tmp`.
     2. Verify file completeness (e.g. valid JSON parsing, non-zero length, matching closing brackets).
     3. Atomically overwrite or rename the staging file to `<target_file>`.
   - Never leave partial or truncated files in production directories.

2. **Concurrency Conflict Prevention**:
   - Strictly honor the Single-Writer Rule: No two agents may target the same file path simultaneously.
   - Background tasks must release open file descriptors immediately upon write completion.

3. **Crash Recovery Procedure**:
   When an agent initializes or recovers from an unexpected process failure:
   - **Step 1: Orphan Cleanup**: Scan owned directories for leftover `.tmp` or `.staged` files. Inspect their validity; delete corrupt fragments.
   - **Step 2: State Audit**: Compare current file state against the last recorded entries in `progress.md` and git commits.
   - **Step 3: Rollback Partial Mutations**: Revert torn or partially written files to their last clean state before reapplying changes.
   - **Step 4: Re-Establish Heartbeat**: Update `progress.md` with recovery timestamp and resume execution from the last intact milestone step.

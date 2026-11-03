---
name: graphify
description: AST and architectural knowledge graph skill for tracking project dependencies, exports, routes, and call graphs. Used in /start-phase, /verify, and code exploration.
---

# Graphify Knowledge Graph Playbook

The `graphify` skill builds and queries a deterministic Abstract Syntax Tree (AST) and architecture knowledge graph (`graph.json`). It enables instant lookup of dependencies, components, route handlers, database schemas, and shared utilities across Umbrella without incurring token-expensive recursive file scans.

---

## 1. Core Architecture

Graphify extracts codebase topology into a directed graph of typed nodes and relationships:
- **Node Types**:
  - `File`: Source code modules (`src/**/*.ts`, `src/**/*.tsx`, `supabase/**/*.sql`).
  - `Component`: React UI primitives, bento cards, and layout containers.
  - `Route`: Next.js App Router paths (`/`, `/login`, `/signup`, `/portal/patient`, `/portal/doctor`, `/emergency/[token]`).
  - `Table`: PostgreSQL entities (`accounts`, `patient_profiles`, `clinical_records`, `appointments`).
  - `RPC`: PostgreSQL security-definer procedures (`get_emergency_triage_by_token`, `submit_self_reported_baseline`, `regenerate_qr_token`).
  - `Schema`: Zod runtime validation schemas.
- **Edge Types**:
  - `imports`: Module dependency links.
  - `renders`: Component inclusion in page or composite component.
  - `calls_rpc`: Invocation of Supabase database RPCs.
  - `validates_with`: Form or route parameter binding to Zod schema.
  - `governs`: RLS policy or database trigger enforcement over a table.

---

## 2. Tools & Query Capabilities

When inspecting or refactoring the codebase, use graph queries before editing:

| Tool Command | Purpose | Usage Context |
|---|---|---|
| `query_graph(node_id)` | Retrieve node properties, incoming/outgoing edges | Inspecting a component or RPC before modification |
| `get_neighbors(node_id, depth)` | Extract local dependency subgraph | Assessing ripple effects of changing a schema or utility |
| `god_nodes()` | Identify highest-degree centrality nodes | Pinpointing critical architectural hubs (e.g., `src/lib/supabase/client.ts`) |
| `shortest_path(source, target)` | Trace dependency chain between two modules | Debugging circular dependencies or route leakage |

---

## 3. Workflow Integration

### Pre-Modification Impact Analysis (`/start-phase`)
1. Before modifying any component or lib utility, run `get_neighbors(target_node)` to identify all dependent surfaces.
2. Verify that changes to shared schemas in `src/lib/schemas.ts` do not inadvertently alter the public emergency triage contract or doctor portal validations.
3. Confirm that no public route (`/emergency/[token]`) acquires dependency edges to heavy packages (`framer-motion`, `qrcode.react`, `jspdf`).

### Post-Modification Verification (`/verify`)
1. Refresh the AST graph after code modifications.
2. Confirm zero disconnected "orphan" components or dead-code exports.
3. Validate that Non-Negotiable N1 holds: no edges exist from `residential_address` or `spouse_dependents` to `/emergency/[token]`.

---

## 4. Graph Maintenance
- The graph artifact is maintained at `.agents/graph.json`.
- Kept lightweight, machine-readable, and deterministic.

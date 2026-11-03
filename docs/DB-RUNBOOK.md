# Umbrella Database Runbook

This runbook outlines the required procedures for deploying, validating, seeding, and generating types for the Umbrella PostgreSQL database on Supabase.

---

## 1. Prerequisites & Host Environment Setup
- Access to the Supabase Project Dashboard (`https://supabase.com/dashboard/project/<PROJECT_ID>`).
- Supabase Project URL and Anon/Publishable Key configured in `.env.local`.
- Supabase CLI installed locally (optional, for CLI-driven workflows).
- Node.js 20.9+ LTS (or Node 22 LTS) with npm and Git installed and available in system PATH.
  - Windows Host Installation (via winget in PowerShell):
    ```powershell
    winget install OpenJS.NodeJS.LTS
    winget install Git.Git
    ```
  - Toolchain Verification:
    ```powershell
    node -v   # Expected: v20.x or v22.x
    npm -v    # Expected: 10.x+
    git -v    # Expected: 2.x+
    ```
  - Windows MCP Execution Note: `npx` executes via `npx.cmd`; ensure `C:\Program Files\nodejs\` is registered in the system PATH.


---

## 2. Step-by-Step Execution Sequence

### Step 1: Run the Database Migration
Apply the core schema, tables, triggers, RLS policies, and RPC functions.

1. Navigate to **Supabase Dashboard > SQL Editor > New query**.
2. Open `supabase/migrations/0001_umbrella_schema.sql` in your code editor.
3. Paste the entire SQL file content into the SQL Editor.
4. Click **Run**.
5. Confirm output: All 4 tables (`accounts`, `patient_profiles`, `clinical_records`, `appointments`), triggers, and RPC functions created successfully with zero errors.

*Alternative CLI execution:*
```bash
npx supabase login
npx supabase link --project-ref <YOUR_PROJECT_ID>
npx supabase db push
```

---

### Step 2: Execute RLS Smoke Tests
Validate that Row Level Security (RLS) policies and column-level update protections are active and enforcing security non-negotiables.

1. In the Supabase SQL Editor, open a new tab.
2. Open `supabase/tests/rls_smoke.sql`.
3. Paste the full script into the SQL Editor and click **Run**.
4. The test script executes within a transactional `BEGIN ... ROLLBACK` block:
   - Validates that `anon` has zero table access.
   - Validates that patients cannot escalate roles or read other patients' records.
   - Validates that pending doctors cannot read clinical data.
   - Validates that `get_emergency_triage_by_token` strictly excludes address and dependents.
   - Validates that token regeneration invalidates old tokens.
5. Expected Output:
   ```text
   ALL RLS TESTS PASSED
   ```
   If any statement raises `FAIL: ...`, halt and inspect the failing policy before proceeding.

---

### Step 3: Seed Synthetic Accounts (Post-Signup)
The seed file provides synthetic doctor approvals and test data. In accordance with zero-mock auth, actual authentication identities must exist in `auth.users`.

1. Launch the local application: `npm run dev`.
2. Register a synthetic doctor account at `http://localhost:3000/signup?role=doctor` with:
   - Full Name: `Dr. Dev Test`
   - Email: `doctor.dev@example.test`
   - Medical License: `LIC-DEV-9999`
   - Specialization: `Emergency Medicine`
3. Notice that the account is initialized with `doctor_status = 'pending'`.
4. Open `supabase/seed.sql` and run it in the Supabase SQL Editor:
   ```sql
   update public.accounts
   set doctor_status = 'approved'
   where email = 'doctor.dev@example.test';
   ```
5. Confirm that `doctor_status` is updated to `'approved'`. The doctor account now possesses full clinical read/write privileges.

---

### Step 4: Regenerate TypeScript Database Types
Keep `src/lib/supabase/types.ts` in lockstep with the remote database schema.

Run the following command from the project root:
```bash
npx supabase login
npx supabase gen types typescript --project-id <YOUR_PROJECT_ID> > src/lib/supabase/types.ts
```

Verify that `src/lib/supabase/types.ts` defines:
- Tables: `accounts`, `patient_profiles`, `clinical_records`, `appointments`.
- Functions: `get_emergency_triage_by_token`, `submit_self_reported_baseline`, `regenerate_qr_token`, `is_approved_doctor`.
- Enums: `user_role`.

---

## 3. Security Hygiene Checklist
- [ ] No `service_role` key was used or saved in client-facing files.
- [ ] RLS is confirmed active on all tables (`accounts`, `patient_profiles`, `clinical_records`, `appointments`).
- [ ] Anon role has `GRANT EXECUTE` on `get_emergency_triage_by_token` only.
- [ ] All `SECURITY DEFINER` functions explicitly set `search_path = ''`.
- [ ] Columns `role`, `doctor_status`, `patient_code`, and `qr_token` are protected from arbitrary update.

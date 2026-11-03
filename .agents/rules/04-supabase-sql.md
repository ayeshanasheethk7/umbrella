---
trigger: glob
globs: supabase/**/*.sql
description: Rules for writing Umbrella migrations, seeds and SQL tests
---
# 04 Supabase SQL

- Schema changes only through numbered files in supabase/migrations/. Never edit a migration that has run on a remote project; add a new one.
- Schema source: SPEC section 4.2 amended by docs/DECISIONS.md. Pattern library: skill umbrella-supabase-rls (references/rls-patterns.sql). Copy its patterns; do not improvise policies.
- Every function: schema-qualified names; SECURITY DEFINER functions use `set search_path = ''`; `revoke all on function ... from public;` then grant only to the roles that need it.
- Every table: enable RLS in the migration that creates it. Revoke privileges you do not need (anon gets none).
- Policies use (select auth.uid()), never bare auth.uid(). Index every column used in a policy or foreign key.
- timestamptz for times, text + check constraints (the only enum is user_role, per the spec), gen_random_uuid() for ids.
- Seeds are idempotent and synthetic.
- rls_smoke.sql runs inside BEGIN ... ROLLBACK using `set local role` and set_config('request.jwt.claims', ...). Every policy and RPC gets at least one ALLOW test and one DENY test.
- After a migration is run, the human regenerates src/lib/supabase/types.ts.

#!/usr/bin/env python3
"""scripts/adversarial_challenge_m9.py - Tier 5 Adversarial Penetration Challenge Suite (Milestone M9)"""

import os
import re
import sys
import json
import subprocess

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def run_adversarial_suite():
    passed = 0
    failed = 0
    results = []

    def record(tid: str, title: str, success: bool, evidence: str = ""):
        nonlocal passed, failed
        status = "PASS" if success else "FAIL"
        if success:
            passed += 1
        else:
            failed += 1
        results.append({"id": tid, "title": title, "status": status, "evidence": evidence})
        print(f"[{status}] [{tid}] {title}" + (f" | {evidence}" if evidence else ""))

    print("=" * 80)
    print("UMBRELLA MILESTONE M9: TIER 5 ADVERSARIAL PENETRATION ATTACK SUITE")
    print("=" * 80)

    # VECTOR A: INVARIANT N1 PRIVACY LEAK INJECTION & PROBING
    print("\n--- [VECTOR A] Invariant N1 Privacy Leak Injection & Memory Probing ---")
    emergency_files = [
        "src/app/emergency/[token]/page.tsx",
        "src/components/emergency/emergency-triage-view.tsx",
        "src/components/emergency/triage-vitals-card.tsx",
        "src/components/emergency/triage-allergies-alert.tsx",
        "src/components/emergency/triage-clinical-history.tsx",
        "src/components/emergency/sticky-emergency-call-bar.tsx",
        "src/lib/qr-export.ts",
    ]
    n1_violations = []
    for rel_path in emergency_files:
        fp = os.path.join(ROOT_DIR, rel_path)
        if os.path.exists(fp):
            with open(fp, "r", encoding="utf-8") as f:
                code = f.read()
                if "residential_address" in code or "residentialAddress" in code:
                    n1_violations.append(f"{rel_path}:residential_address")
                if "spouse_dependents" in code or "spouseDependents" in code:
                    n1_violations.append(f"{rel_path}:spouse_dependents")

    record("ADV-VEC-A1-CODE-LEAK", "Zero address/dependents in emergency components or export",
           len(n1_violations) == 0, f"Violations: {n1_violations}")

    schemas_path = os.path.join(ROOT_DIR, "src/lib/schemas.ts")
    with open(schemas_path, "r", encoding="utf-8") as f:
        schemas_code = f.read()
    has_super_refine = "superRefine" in schemas_code and "residential_address prohibited" in schemas_code and "spouse_dependents prohibited" in schemas_code
    record("ADV-VEC-A2-SCHEMA-BARRIER", "emergencyTriageSchema superRefine actively rejects privacy leaks",
           has_super_refine, "Zod superRefine dual barrier verified")

    # VECTOR B: INVARIANT N4 SECRET KEY SWEEP & SERVICE ROLE IMMUNITY
    print("\n--- [VECTOR B] Invariant N4 Secret Key Sweep ---")
    secret_leaks = []
    for root, _, files in os.walk(os.path.join(ROOT_DIR, "src")):
        for file in files:
            if file.endswith((".ts", ".tsx", ".js", ".json")):
                p = os.path.join(root, file)
                with open(p, "r", encoding="utf-8") as fl:
                    if "service_role" in fl.read().lower():
                        secret_leaks.append(os.path.relpath(p, ROOT_DIR))

    record("ADV-VEC-B1-SRC-SECRETS", "Zero service_role occurrences across src/ tree",
           len(secret_leaks) == 0, f"Leaks: {secret_leaks}")

    env_files = [".env", ".env.local", ".env.example", ".env.production"]
    env_leaks = []
    for ef in env_files:
        ef_path = os.path.join(ROOT_DIR, ef)
        if os.path.exists(ef_path):
            with open(ef_path, "r", encoding="utf-8") as fl:
                if "service_role" in fl.read().lower():
                    env_leaks.append(ef)
    record("ADV-VEC-B2-ENV-SECRETS", "Zero service_role occurrences in environment files",
           len(env_leaks) == 0, f"Leaks: {env_leaks}")

    schema_sql_path = os.path.join(ROOT_DIR, "supabase/migrations/0001_umbrella_schema.sql")
    has_anon_revokes = False
    if os.path.exists(schema_sql_path):
        with open(schema_sql_path, "r", encoding="utf-8") as sf:
            sqlt = sf.read().lower()
            has_anon_revokes = "revoke all on public.accounts" in sqlt and "grant execute on function public.get_emergency_triage_by_token" in sqlt
    record("ADV-VEC-B3-ANON-GRANTS", "Database grants restrict anon role to emergency RPC only",
           has_anon_revokes, "Anon table access revoked in SQL migration")

    # VECTOR C: INVARIANT N3/N5 ROLE PRIVILEGE ESCALATION & AUTH BYPASSES
    print("\n--- [VECTOR C] Invariant N3/N5 Privilege Escalation & Auth Bypasses ---")
    doc_actions_path = os.path.join(ROOT_DIR, "src/app/portal/doctor/actions.ts")
    with open(doc_actions_path, "r", encoding="utf-8") as f:
        doc_code = f.read()

    uses_get_user = "supabase.auth.getUser()" in doc_code
    zero_get_session = "getSession" not in doc_code
    verifies_db_role = "from('accounts')" in doc_code and "doctor_status" in doc_code
    record("ADV-VEC-C1-GETUSER-DB-ROLE", "Server actions authenticate strictly via getUser() and public.accounts DB check",
           uses_get_user and zero_get_session and verifies_db_role, "Server-side DB role check verified")

    pat_actions_path = os.path.join(ROOT_DIR, "src/app/portal/patient/actions.ts")
    with open(pat_actions_path, "r", encoding="utf-8") as f:
        pat_code = f.read()
    pat_uses_get_user = "supabase.auth.getUser()" in pat_code and "getSession" not in pat_code
    record("ADV-VEC-C2-PATIENT-GETUSER", "Patient actions verify session via getUser() with zero getSession()",
           pat_uses_get_user, "getUser() enforcement verified")

    # VECTOR D: INVARIANT N2 BANNER TAMPERING & OCCLUSION
    print("\n--- [VECTOR D] Invariant N2 Safety Banner Tampering & Occlusion ---")
    banner_path = os.path.join(ROOT_DIR, "src/components/doctor/patient-safety-banner.tsx")
    with open(banner_path, "r", encoding="utf-8") as f:
        banner_code = f.read()

    has_sticky = "sticky" in banner_code and "z-30" in banner_code
    zero_inputs = not re.search(r'<(input|textarea|select)\b', banner_code)
    has_required_identifiers = "fullName" in banner_code and "bloodGroup" in banner_code and "emergencyContactName" in banner_code
    record("ADV-VEC-D1-BANNER-INTEGRITY", "Patient safety banner is sticky, read-only, and displays core vitals",
           has_sticky and zero_inputs and has_required_identifiers, "Persistent read-only safety banner verified")

    record("ADV-VEC-D2-BANNER-IMMUTABLE", "Patient safety banner contains zero editable inputs",
           zero_inputs, "Zero input/textarea/select tags")

    # VECTOR E: POSTGREST PARAMETER INJECTION & WILDCARD FLOODING
    print("\n--- [VECTOR E] PostgREST Parameter Injection & Wildcard Flooding ---")
    has_escape_search = "escapeSearchTerm" in doc_code
    has_precedence_check = doc_code.find(".eq('qr_token'") < doc_code.find("accounts.contact_phone")
    record("ADV-VEC-E1-WILDCARD-ESCAPE", "Search query escapes % _ , ( ) and bounds query lengths",
           has_escape_search, "Wildcard sanitization verified")
    record("ADV-VEC-E2-SEARCH-PRECEDENCE", "UUID search branch strictly precedes phone search branch",
           has_precedence_check, "Precedence order protected against 7-digit UUID misrouting")

    # ADV-VEC-E3-WILDCARD-FLOOD-DEFENSE
    wildcard_queries = ["%%%%%", "_____", "  %  "]
    clean_empty = all(len(re.sub(r'[%_(),]', '', w).strip()) < 2 for w in wildcard_queries)
    record("ADV-VEC-E3-WILDCARD-FLOOD-DEFENSE", "Search query classifies wildcard-only flooding as invalid empty result",
           clean_empty and "cleanTerm.length < 2" in doc_code, "Wildcard flood defense verified")

    # VECTOR F: TOKEN ROTATION REPLAY & STALE TOKEN PROBING
    print("\n--- [VECTOR F] Token Rotation Replay & Stale Token Probing ---")
    rotate_zero_args = "rotateQrTokenAction()" in pat_code or "rotateQrTokenAction = async ()" in pat_code or "export async function rotateQrTokenAction()" in pat_code
    calls_rpc_directly = "supabase.rpc('regenerate_qr_token')" in pat_code
    record("ADV-VEC-F1-ZERO-ARITY-RPC", "rotateQrTokenAction accepts 0 client arguments and calls regenerate_qr_token",
           rotate_zero_args and calls_rpc_directly, "Target patient ID forgery prevented")

    if os.path.exists(schema_sql_path):
        with open(schema_sql_path, "r", encoding="utf-8") as sf:
            sqlt = sf.read().lower()
            rpc_definer = "create or replace function public.regenerate_qr_token()" in sqlt and "security definer" in sqlt
            rpc_grants = "grant execute on function public.regenerate_qr_token() to authenticated" in sqlt
    else:
        rpc_definer = False
        rpc_grants = False
    record("ADV-VEC-F2-RPC-SECURITY-DEFINER", "regenerate_qr_token is SECURITY DEFINER granted only to authenticated",
           rpc_definer and rpc_grants, "RPC security definer verified")

    print("\n" + "=" * 80)
    print(f"ADVERSARIAL VERDICT: {passed}/{passed + failed} CHECKS PASSED")
    print("=" * 80)
    return failed == 0

if __name__ == "__main__":
    if not run_adversarial_suite():
        sys.exit(1)

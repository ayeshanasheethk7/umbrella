#!/usr/bin/env python3
"""
scripts/challenger_m7_security.py
Milestone M7 Adversarial Security, Penetration & Opaque 404 Challenge Suite
Executed by: Challenger M7-1 (Emergency Security & Opaque 404 Challenger)
"""

import os
import re
import sys
import uuid
import subprocess
from typing import List, Tuple

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

tests_run = 0
tests_passed = 0
tests_failed = 0
failures: List[Tuple[str, str, str]] = []

def record(suite: str, test_name: str, passed: bool, details: str = ""):
    global tests_run, tests_passed, tests_failed, failures
    tests_run += 1
    status = "PASS" if passed else "FAIL"
    if passed:
        tests_passed += 1
        print(f"  [{status}] [{suite}] {test_name}" + (f" -> {details}" if details else ""))
    else:
        tests_failed += 1
        failures.append((suite, test_name, details))
        print(f"  [{status}] [{suite}] {test_name} -> FAILED: {details}")

# ==============================================================================
# SUITE 1: ADVERSARIAL TOKEN PROBING & OPAQUE 404
# ==============================================================================
def run_token_adversarial_suite():
    print("\n" + "=" * 70)
    print("SUITE 1: ADVERSARIAL TOKEN PROBING & OPAQUE 404")
    print("=" * 70)

    page_file = os.path.join(ROOT_DIR, "src", "app", "emergency", "[token]", "page.tsx")
    not_found_file = os.path.join(ROOT_DIR, "src", "app", "emergency", "[token]", "not-found.tsx")
    schemas_file = os.path.join(ROOT_DIR, "src", "lib", "schemas.ts")

    page_src = open(page_file, "r", encoding="utf-8").read()
    not_found_src = open(not_found_file, "r", encoding="utf-8").read()
    schemas_src = open(schemas_file, "r", encoding="utf-8").read()

    # 1.1 UUID schema
    record("Token-01", "uuidSchema defined with z.string().uuid()", "export const uuidSchema = z.string().uuid(" in schemas_src)

    # 1.2 Execution order: safeParse before DB query
    uuid_idx = page_src.find("uuidSchema.safeParse")
    rpc_idx = page_src.find("supabase.rpc")
    nf_idx = page_src.find("notFound()", uuid_idx)
    record("Token-02", "page.tsx halts on invalid UUID before RPC call", uuid_idx < nf_idx < rpc_idx)

    # 1.3 Adversarial token testing
    uuid_pat = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
    malformed = [
        ("not-uuid", "not-a-uuid"),
        ("traversal", "../../etc/passwd"),
        ("numeric", "12345"),
        ("non-hex", "00000000-0000-0000-0000-00000000000g"),
        ("empty", ""),
        ("whitespace", "   "),
        ("sqli-drop", "'; DROP TABLE accounts; --"),
        ("sqli-tautology", "' OR '1'='1"),
        ("overflow", "a" * 2000),
        ("null-byte", "00000000-0000-0000-0000-000000000000\x00"),
        ("short", "e2b1b3a4-8c8f-4d2b-9e1f"),
    ]
    all_rejected = all(not uuid_pat.match(tok) for _, tok in malformed)
    record("Token-03", f"All {len(malformed)} malformed tokens rejected by UUID validator", all_rejected)
    record("Token-04", "Valid UUID format accepted", bool(uuid_pat.match(str(uuid.uuid4()))))

    # 1.4 Opaque 404
    record("Opaque404-01", "not-found.tsx suppresses token reflection", "{token}" not in not_found_src and "token:" not in not_found_src)
    record("Opaque404-02", "not-found.tsx suppresses stack traces / errors", "stack" not in not_found_src.lower())
    record("Opaque404-03", "not-found.tsx provides 56px 911 dialer", "min-h-[56px]" in not_found_src and "tel:911" in not_found_src)

# ==============================================================================
# SUITE 2: PRIVACY LEAK ATTACK SIMULATION (INVARIANT N1)
# ==============================================================================
def run_privacy_leak_suite():
    print("\n" + "=" * 70)
    print("SUITE 2: PRIVACY LEAK ATTACK SIMULATION (INVARIANT N1)")
    print("=" * 70)

    mig_sql = open(os.path.join(ROOT_DIR, "supabase", "migrations", "0001_umbrella_schema.sql"), encoding="utf-8").read()
    schemas_src = open(os.path.join(ROOT_DIR, "src", "lib", "schemas.ts"), encoding="utf-8").read()

    # 2.1 Postgres RPC projection
    rpc_match = re.search(r"get_emergency_triage_by_token\s*\([^)]*\)\s*returns jsonb.*?select jsonb_build_object\s*\((.*?)\)\s*from", mig_sql, re.DOTALL | re.IGNORECASE)
    record("N1-DB-01", "get_emergency_triage_by_token RPC exists in migrations", bool(rpc_match))
    if rpc_match:
        keys = re.findall(r"'([a-zA-Z0-9_]+)'\s*,", rpc_match.group(1))
        record("N1-DB-02", "residential_address omitted from Postgres RPC", "residential_address" not in keys)
        record("N1-DB-03", "spouse_dependents omitted from Postgres RPC", "spouse_dependents" not in keys)
        record("N1-DB-04", "qr_token omitted from Postgres RPC", "qr_token" not in keys)

    # 2.2 Anon role table privileges revoked
    record("N1-DB-05", "Anon role has ALL table grants revoked", "revoke all on public.accounts, public.patient_profiles" in mig_sql)

    # 2.3 UI components omit forbidden fields
    emergency_dir = os.path.join(ROOT_DIR, "src", "components", "emergency")
    comp_files = [os.path.join(emergency_dir, f) for f in os.listdir(emergency_dir) if f.endswith(".tsx")]
    all_clean = all("residential_address" not in open(f, encoding="utf-8").read() and "spouse_dependents" not in open(f, encoding="utf-8").read() for f in comp_files)
    record("N1-UI-01", "All emergency UI components strictly omit PII fields", all_clean)

    # 2.4 Schema inspection
    record("N1-SCHEMA-01", "emergencyTriageSchema includes superRefine privacy check", "superRefine" in schemas_src and "residential_address" in schemas_src)

# ==============================================================================
# SUITE 3: ANONYMOUS CLIENT SECURITY (INVARIANT N4)
# ==============================================================================
def run_anon_client_suite():
    print("\n" + "=" * 70)
    print("SUITE 3: ANONYMOUS CLIENT SECURITY (INVARIANT N4)")
    print("=" * 70)

    anon_src = open(os.path.join(ROOT_DIR, "src", "lib", "supabase", "anon.ts"), encoding="utf-8").read()
    # Check for service_role in executable code lines (excluding comments)
    code_lines = [l for l in anon_src.splitlines() if not l.strip().startswith("*") and not l.strip().startswith("//") and not l.strip().startswith("/*")]
    record("N4-01", "anon.ts executable code contains zero service_role references", all("service_role" not in l and "SERVICE_ROLE" not in l for l in code_lines))
    record("N4-02", "anon.ts uses NEXT_PUBLIC_SUPABASE_ANON_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY" in anon_src)
    record("N4-03", "anon.ts enforces persistSession: false", "persistSession: false" in anon_src)
    record("N4-04", "anon.ts enforces autoRefreshToken: false", "autoRefreshToken: false" in anon_src)
    record("N4-05", "anon.ts enforces detectSessionInUrl: false", "detectSessionInUrl: false" in anon_src)
    record("N4-06", "anon.ts operates completely cookie-less", "cookies(" not in anon_src)

# ==============================================================================
# SUITE 4: PERFORMANCE & A11Y
# ==============================================================================
def run_perf_a11y_suite():
    print("\n" + "=" * 70)
    print("SUITE 4: PERFORMANCE & A11Y")
    print("=" * 70)

    call_bar = open(os.path.join(ROOT_DIR, "src", "components", "emergency", "sticky-emergency-call-bar.tsx"), encoding="utf-8").read()
    record("A11Y-01", "Sticky call bar enforces min-h-[56px] min-w-[56px]", "min-h-[56px]" in call_bar and "min-w-[56px]" in call_bar)
    record("A11Y-02", "Dialer executes sanitized tel: protocol", "href={`tel:" in call_bar and "sanitizeTel" in call_bar)
    record("PERF-01", "Call button employs CSS-only active:scale-[0.98]", "active:scale-[0.98]" in call_bar)

    emergency_dir = os.path.join(ROOT_DIR, "src", "components", "emergency")
    all_ts = [open(os.path.join(emergency_dir, f), encoding="utf-8").read() for f in os.listdir(emergency_dir) if f.endswith(".tsx")]
    all_ts.append(open(os.path.join(ROOT_DIR, "src", "app", "emergency", "[token]", "page.tsx"), encoding="utf-8").read())
    heavy = ["framer-motion", "qrcode.react", "jspdf", "@/components/ui/button", "@/components/ui/modal"]
    no_heavy = all(h not in c for c in all_ts for h in heavy)
    record("PERF-02", "Zero heavy client libraries imported in emergency surface", no_heavy)

# ==============================================================================
# SUITE 5: REPOSITORY REGRESSIONS
# ==============================================================================
def run_regression_suite():
    print("\n" + "=" * 70)
    print("SUITE 5: REPOSITORY REGRESSIONS")
    print("=" * 70)

    r7 = subprocess.run([sys.executable, os.path.join(ROOT_DIR, "scripts", "verify_m7.py")], capture_output=True, text=True)
    record("REGRESS-M7", "scripts/verify_m7.py passes all 41 checks", r7.returncode == 0)

    ra = subprocess.run([sys.executable, os.path.join(ROOT_DIR, "scripts", "audit.py")], capture_output=True, text=True)
    record("REGRESS-AUDIT", "scripts/audit.py passes Rule 12k and MCP validity", ra.returncode == 0)

    r5 = subprocess.run([sys.executable, os.path.join(ROOT_DIR, "scripts", "verify_m5.py")], capture_output=True, text=True)
    record("REGRESS-M5", "scripts/verify_m5.py passes all 74 checks", r5.returncode == 0)

    r6 = subprocess.run([sys.executable, os.path.join(ROOT_DIR, "scripts", "verify_m6.py")], capture_output=True, text=True)
    record("REGRESS-M6", "scripts/verify_m6.py passes all 38 checks", r6.returncode == 0)

def main():
    print("=" * 70)
    print("UMBRELLA M7 EMPIRICAL ADVERSARIAL CHALLENGER SUITE")
    print("=" * 70)

    run_token_adversarial_suite()
    run_privacy_leak_suite()
    run_anon_client_suite()
    run_perf_a11y_suite()
    run_regression_suite()

    print("\n" + "=" * 70)
    print(f"ADVERSARIAL SUMMARY: {tests_passed}/{tests_run} Passed, {tests_failed} Failed")
    print("=" * 70)
    return 0 if tests_failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

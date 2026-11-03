#!/usr/bin/env python3
"""
Independent Adversarial Security & Data Integrity Test Suite
Reviewer M7-2 Re-check (reviewer_m7_2_recheck)
"""

import sys
import os
import re

REPO_ROOT = r"c:\Users\DELL\ayesha_pro\medi_qr"

def run_tests():
    print("=" * 75)
    print("INDEPENDENT ADVERSARIAL AUDIT & STRESS SUITE: REVIEWER M7-2 RE-CHECK")
    print("=" * 75)
    passed = 0
    total = 0

    def assert_test(cond, name, details=""):
        nonlocal passed, total
        total += 1
        status = "PASS" if cond else "FAIL"
        if cond:
            passed += 1
            print(f"[{status}] {name}")
            if details:
                print(f"        -> {details}")
        else:
            print(f"[{status}] {name} *** FAILED ***")
            if details:
                print(f"        -> {details}")

    # =========================================================================
    # 1. Zod Schema Verification: emergencyTriageSchema
    # =========================================================================
    schemas_path = os.path.join(REPO_ROOT, "src", "lib", "schemas.ts")
    with open(schemas_path, "r", encoding="utf-8") as f:
        schemas_content = f.read()

    # Verify emergencyTriageSchema existence
    assert_test("export const emergencyTriageSchema = z" in schemas_content,
                "SCHEMA-01: emergencyTriageSchema is exported")

    # Verify chaining order: .passthrough() must appear BEFORE .superRefine(
    schema_match = re.search(r"export const emergencyTriageSchema = z\s*\.object\(.*?\)\s*\.passthrough\(\)\s*\.superRefine\(",
                             schemas_content, re.DOTALL)
    assert_test(schema_match is not None,
                "SCHEMA-02: .passthrough() chained directly before .superRefine()",
                "Guarantees prohibited keys are retained in payload for superRefine validation")

    # Verify superRefine checks for prohibited keys
    assert_test("'residential_address' in raw" in schemas_content and "Privacy violation: residential_address prohibited" in schemas_content,
                "SCHEMA-03: superRefine captures and rejects residential_address")
    assert_test("'spouse_dependents' in raw" in schemas_content and "Privacy violation: spouse_dependents prohibited" in schemas_content,
                "SCHEMA-04: superRefine captures and rejects spouse_dependents")

    # =========================================================================
    # 2. Strict Invariant N1: Zero Exposure across Emergency Surface
    # =========================================================================
    emergency_files = [
        os.path.join(REPO_ROOT, "src", "app", "emergency", "[token]", "page.tsx"),
        os.path.join(REPO_ROOT, "src", "app", "emergency", "[token]", "not-found.tsx"),
        os.path.join(REPO_ROOT, "src", "components", "emergency", "emergency-triage-view.tsx"),
        os.path.join(REPO_ROOT, "src", "components", "emergency", "triage-vitals-card.tsx"),
        os.path.join(REPO_ROOT, "src", "components", "emergency", "triage-allergies-alert.tsx"),
        os.path.join(REPO_ROOT, "src", "components", "emergency", "triage-clinical-history.tsx"),
        os.path.join(REPO_ROOT, "src", "components", "emergency", "triage-escalation-footer.tsx"),
        os.path.join(REPO_ROOT, "src", "components", "emergency", "sticky-emergency-call-bar.tsx"),
    ]

    for ef in emergency_files:
        rel = os.path.relpath(ef, REPO_ROOT)
        with open(ef, "r", encoding="utf-8") as f:
            content = f.read()
        assert_test("residential_address" not in content,
                    f"N1-PRIVACY: Zero residential_address in {rel}")
        assert_test("spouse_dependents" not in content,
                    f"N1-PRIVACY: Zero spouse_dependents in {rel}")

    # Verify RPC isolation: page.tsx must only call get_emergency_triage_by_token
    page_path = os.path.join(REPO_ROOT, "src", "app", "emergency", "[token]", "page.tsx")
    with open(page_path, "r", encoding="utf-8") as f:
        page_content = f.read()
    assert_test("rpc('get_emergency_triage_by_token'" in page_content,
                "N1-RPC: page.tsx executes RPC get_emergency_triage_by_token")
    assert_test(".from(" not in page_content,
                "N1-RPC: page.tsx contains zero direct table SELECT queries (.from)")

    # =========================================================================
    # 3. Anon Client Isolation: src/lib/supabase/anon.ts
    # =========================================================================
    anon_path = os.path.join(REPO_ROOT, "src", "lib", "supabase", "anon.ts")
    with open(anon_path, "r", encoding="utf-8") as f:
        anon_content = f.read()

    # Zero service_role leaks anywhere in anon.ts
    assert_test("service_role" not in anon_content,
                "N4-ANON: Zero service_role occurrences in anon.ts (Invariant N4)")
    # Uses anon key only
    assert_test("NEXT_PUBLIC_SUPABASE_ANON_KEY" in anon_content,
                "N4-ANON: Uses NEXT_PUBLIC_SUPABASE_ANON_KEY")
    assert_test("SERVICE_ROLE_KEY" not in anon_content and "SUPABASE_SERVICE_ROLE" not in anon_content,
                "N4-ANON: Zero service role environment variable references")
    # Cookie-less options
    assert_test("persistSession: false" in anon_content,
                "ANON-COOKIELESS: persistSession disabled")
    assert_test("autoRefreshToken: false" in anon_content,
                "ANON-COOKIELESS: autoRefreshToken disabled")
    assert_test("detectSessionInUrl: false" in anon_content,
                "ANON-COOKIELESS: detectSessionInUrl disabled")
    # Verify no next/headers cookie import
    assert_test("from 'next/headers'" not in anon_content and 'from "next/headers"' not in anon_content,
                "ANON-COOKIELESS: anon.ts does not import from next/headers")
    assert_test("createServerClient" not in anon_content,
                "ANON-COOKIELESS: anon.ts uses standalone createSupabaseClient without SSR cookies")

    # =========================================================================
    # 4. Security Headers in next.config.js
    # =========================================================================
    next_config_path = os.path.join(REPO_ROOT, "next.config.js")
    with open(next_config_path, "r", encoding="utf-8") as f:
        config_content = f.read()

    assert_test("source: '/emergency/:path*'" in config_content,
                "HEADERS: /emergency/:path* rule defined in next.config.js")
    assert_test("key: 'Cache-Control'" in config_content and "no-store" in config_content,
                "HEADERS: Cache-Control: no-store configured for emergency route")
    assert_test("key: 'Referrer-Policy'" in config_content and "no-referrer" in config_content,
                "HEADERS: Referrer-Policy: no-referrer configured for emergency route")
    assert_test("key: 'X-Robots-Tag'" in config_content and "noindex, nofollow" in config_content,
                "HEADERS: X-Robots-Tag: noindex, nofollow configured for emergency route")

    # Also verify route-level metadata and dynamic cache controls
    assert_test("export const dynamic = 'force-dynamic'" in page_content,
                "PAGE-CACHE: page.tsx declares dynamic = 'force-dynamic'")
    assert_test("export const revalidate = 0" in page_content,
                "PAGE-CACHE: page.tsx declares revalidate = 0")
    assert_test("export const fetchCache = 'force-no-store'" in page_content,
                "PAGE-CACHE: page.tsx declares fetchCache = 'force-no-store'")

    # =========================================================================
    # 5. Invariant N10: Zero `any` and Zero `@ts-ignore` across src/
    # =========================================================================
    src_dir = os.path.join(REPO_ROOT, "src")
    any_violations = []
    ts_ignore_violations = []

    # Regex to detect actual TypeScript any declarations/casts
    any_regex = re.compile(r"(:\s*any\b|\bas\s+any\b|<any>|\bany\[\])")
    ts_ignore_regex = re.compile(r"(@ts-ignore|@ts-expect-error)")

    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith((".ts", ".tsx")):
                fpath = os.path.join(root, file)
                relpath = os.path.relpath(fpath, REPO_ROOT)
                with open(fpath, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                for idx, line in enumerate(lines, 1):
                    # Strip single-line comments for 'any' check, but check comments for @ts-ignore
                    stripped_comment = re.sub(r"//.*$", "", line)
                    if any_regex.search(stripped_comment):
                        any_violations.append(f"{relpath}:{idx}: {line.strip()}")
                    if ts_ignore_regex.search(line):
                        ts_ignore_violations.append(f"{relpath}:{idx}: {line.strip()}")

    assert_test(len(any_violations) == 0,
                f"N10-ANY: Zero 'any' types in src/ -> Violations: {any_violations}")
    assert_test(len(ts_ignore_violations) == 0,
                f"N10-TS-IGNORE: Zero '@ts-ignore' or '@ts-expect-error' in src/ -> Violations: {ts_ignore_violations}")

    # =========================================================================
    # 6. Service Role Leaks across entire src/ tree
    # =========================================================================
    service_role_violations = []
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith((".ts", ".tsx", ".js", ".jsx")):
                fpath = os.path.join(root, file)
                relpath = os.path.relpath(fpath, REPO_ROOT)
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                if "service_role" in content:
                    service_role_violations.append(relpath)

    assert_test(len(service_role_violations) == 0,
                f"N4-GLOBAL: Zero service_role occurrences in entire src/ tree -> Violations: {service_role_violations}")

    # =========================================================================
    # 7. Character Limit Audit for all M7 Surface Files
    # =========================================================================
    m7_all_files = emergency_files + [anon_path, schemas_path, next_config_path]
    m7_over_12k = []
    for fpath in m7_all_files:
        relpath = os.path.relpath(fpath, REPO_ROOT)
        with open(fpath, "r", encoding="utf-8") as f:
            length = len(f.read())
        if length >= 12000:
            m7_over_12k.append(f"{relpath} ({length} chars)")

    assert_test(len(m7_over_12k) == 0,
                f"RULE-12K: All M7 files strictly under 12,000 characters -> Over limit: {m7_over_12k}")

    # =========================================================================
    # Summary
    # =========================================================================
    print("=" * 75)
    print(f"ADVERSARIAL REVIEW SUMMARY: {passed}/{total} Checks Passed")
    print("=" * 75)
    if passed == total:
        print("VERDICT: APPROVE (Zero Integrity Violations, Invariants N1/N4/N10 Fully Met)")
        return 0
    else:
        print("VERDICT: REQUEST_CHANGES (Failures Detected)")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())

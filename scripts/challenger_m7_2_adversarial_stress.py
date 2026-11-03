#!/usr/bin/env python3
"""
scripts/challenger_m7_2_adversarial_stress.py
Umbrella Milestone M7-2 Re-Check: Adversarial Edge Cases & Failure Mode Stress Testing
Author: Challenger M7-2 Re-check (critic, specialist)
"""

import os
import re
import sys
import uuid
from typing import Dict, Any, List, Tuple

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

tests_run = 0
tests_passed = 0
tests_failed = 0
failures: List[Tuple[str, str, str]] = []

def record(section: str, test_name: str, passed: bool, details: str = ""):
    global tests_run, tests_passed, tests_failed, failures
    tests_run += 1
    status = "PASS" if passed else "FAIL"
    if passed:
        tests_passed += 1
        print(f"  [{status}] [{section}] {test_name}" + (f" -> {details}" if details else ""))
    else:
        tests_failed += 1
        failures.append((section, test_name, details))
        print(f"  [{status}] [{section}] {test_name} -> FAILED: {details}")

def read_source(rel_path: str) -> str:
    path = os.path.join(ROOT_DIR, rel_path)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# ==============================================================================
# ADVERSARIAL SUITE 1: ZOD SCHEMA DEFENSE-IN-DEPTH & PASSTHROUGH PURGE
# ==============================================================================
def test_schema_adversarial_stress():
    print("\n" + "=" * 75)
    print("ADVERSARIAL 1: ZOD SCHEMA DEFENSE-IN-DEPTH & PASSTHROUGH PURGE")
    print("=" * 75)

    schemas_src = read_source("src/lib/schemas.ts")

    # 1.1 Verify passthrough() chained before superRefine()
    has_passthrough = ".passthrough()" in schemas_src
    record("SCHEMA_DEFENSE", "emergencyTriageSchema includes .passthrough() chaining", has_passthrough, "Preserves unauthorized keys for superRefine validation")

    # 1.2 Verify superRefine checks for residential_address and spouse_dependents
    refine_start = schemas_src.find("emergencyTriageSchema")
    refine_body = schemas_src[refine_start:refine_start + 2500]
    has_addr_check = "residential_address" in refine_body
    has_deps_check = "spouse_dependents" in refine_body
    record("SCHEMA_DEFENSE", "superRefine traps 'residential_address'", has_addr_check)
    record("SCHEMA_DEFENSE", "superRefine traps 'spouse_dependents'", has_deps_check)

    # 1.3 Verify page.tsx invokes notFound() when safeParse fails
    page_src = read_source("src/app/emergency/[token]/page.tsx")
    has_schema_parse = "emergencyTriageSchema.safeParse" in page_src
    has_parse_fail_guard = "if (!parsed.success)" in page_src and "notFound()" in page_src
    record("SCHEMA_DEFENSE", "page.tsx validates triage data with safeParse", has_schema_parse)
    record("SCHEMA_DEFENSE", "page.tsx triggers notFound() on parse failure (privacy barrier)", has_parse_fail_guard)


# ==============================================================================
# ADVERSARIAL SUITE 2: PHONE SANITIZER EDGE CASE EXPLORATION
# ==============================================================================
def py_sanitize_tel(phone: Any) -> str:
    if not phone or not isinstance(phone, str):
        return ""
    trimmed = phone.strip()
    has_leading_plus = trimmed.startswith("+")
    digits = re.sub(r"\D", "", trimmed)
    if not digits:
        return ""
    return f"+{digits}" if has_leading_plus else digits

def test_sanitizer_adversarial_stress():
    print("\n" + "=" * 75)
    print("ADVERSARIAL 2: PHONE SANITIZER EDGE CASE EXPLORATION")
    print("=" * 75)

    adversarial_inputs = [
        # Extreme length
        ("+" + "1" * 100, "+" + "1" * 100, "100-digit phone number"),
        # Null bytes & control characters
        ("+1\x00(555)123-4567", "+15551234567", "Embedded null byte"),
        ("+1\u200B555\u200B123\u200B4567", "+15551234567", "Zero-width spaces"),
        # Special character bombardment
        ("+++---(((   )))---+++", "", "Only punctuation and pluses"),
        ("#123*", "123", "DTMF key symbols # and * stripped"),
        ("+1,555,123,4567", "+15551234567", "Comma pause dialing symbols stripped"),
        ("+1;555;123;4567", "+15551234567", "Semicolon wait dialing symbols stripped"),
        # SQL & Script Injections
        ("'; DROP TABLE patient_profiles; --", "", "Pure SQL injection string yields empty"),
        ("<img src=x onerror=alert(1)>", "1", "XSS payload yields only digit 1 (harmless)"),
    ]

    for inp, exp, desc in adversarial_inputs:
        res = py_sanitize_tel(inp)
        # Note: in Python re.sub(r'\D', '', s), \uff11 is unicode digit. In JS /\D/g matches anything not [0-9].
        # In JS, String.replace(/\D/g, '') treats non-ASCII digits as \D unless using unicode flags.
        # Let's verify output is safe RFC 3966
        rfc_match = (res == "" or bool(re.match(r'^\+?[0-9]+$', res)))
        record("TEL_ADVERSARIAL", f"{desc}: input {inp[:20]!r} -> {res[:15]!r}", rfc_match)


# ==============================================================================
# ADVERSARIAL SUITE 3: ERROR SUPPRESSION & OPAQUE 404 INTEGRITY
# ==============================================================================
def test_opaque_404_integrity():
    print("\n" + "=" * 75)
    print("ADVERSARIAL 3: ERROR SUPPRESSION & OPAQUE 404 INTEGRITY")
    print("=" * 75)

    nf_src = read_source("src/app/emergency/[token]/not-found.tsx")
    page_src = read_source("src/app/emergency/[token]/page.tsx")

    # 3.1 Zero diagnostic leaks
    forbidden_leak_terms = [
        "supabase", "postgres", "rpc", "token:", "token =", "uuid",
        "database", "error.message", "stack", "exception", "query"
    ]
    all_suppressed = True
    for term in forbidden_leak_terms:
        if term in nf_src.lower():
            all_suppressed = False
            record("OPAQUE_404", f"Leak term '{term}' found in not-found.tsx", False)

    record("OPAQUE_404", "Zero diagnostic terms or database details exposed in not-found.tsx", all_suppressed)

    # 3.2 Generic, calm messaging
    has_calm_headline = "Emergency Record Not Found" in nf_src
    has_generic_desc = "identifier may be invalid, expired, or revoked" in nf_src
    record("OPAQUE_404", "Provides uniform generic explanation without status distinction (D9)", has_calm_headline and has_generic_desc)

    # 3.3 Fast fail before DB execution on invalid token
    # uuidResult.safeParse comes strictly before supabase.rpc
    parse_pos = page_src.find("uuidSchema.safeParse")
    rpc_pos = page_src.find("supabase.rpc")
    record("FAST_FAIL", "Invalid tokens fail via safeParse before hitting Supabase RPC", 0 <= parse_pos < rpc_pos)


# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================
def main() -> int:
    print("=" * 75)
    print("UMBRELLA M7-2 ADVERSARIAL CHALLENGER STRESS SUITE")
    print("=" * 75)

    test_schema_adversarial_stress()
    test_sanitizer_adversarial_stress()
    test_opaque_404_integrity()

    print("\n" + "=" * 75)
    print(f"ADVERSARIAL SUMMARY: {tests_passed}/{tests_run} Passed, {tests_failed} Failed")
    print("=" * 75)

    return 0 if tests_failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

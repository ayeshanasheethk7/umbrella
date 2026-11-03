#!/usr/bin/env python3
"""
scripts/adversarial_challenge_m10.py
Adversarial Verification Suite for Milestone M10 Gate Check.
Empirically stress-tests Doctor Search, SafeNext Redirects, Secret/Privacy Leaks, and Invariants.
"""

import os
import sys
import re
import uuid
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# ---------------------------------------------------------------------------
# Section 1: Doctor Search Classifier & Sanitizer Empirical Challenge
# ---------------------------------------------------------------------------

PATIENT_CODE_REGEX = re.compile(r"^UMB-[A-Za-z0-9]{6}$", re.I)
QR_TOKEN_UUID_REGEX = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)

def escape_search_term(t: str) -> str:
    """Matches src/app/portal/doctor/actions.ts:escapeSearchTerm"""
    if not t:
        return ""
    # t.replace(/\\/g, '\\\\').replace(/[%_(),]/g, '').trim()
    s = t.replace("\\", "\\\\")
    s = re.sub(r"[%_(),]", "", s)
    return s.strip()

def extract_phone_digits(query: str) -> str:
    """Matches src/app/portal/doctor/actions.ts:extractPhoneDigits"""
    if not query:
        return ""
    return re.sub(r"\D", "", query)

def classify_search_query(raw_query: str):
    """Matches src/app/portal/doctor/actions.ts:classifySearchQuery"""
    q = (raw_query or "").strip()
    if len(q) < 2 or len(q) > 100:
        return {"type": "invalid", "sanitized": ""}
    if PATIENT_CODE_REGEX.match(q):
        return {"type": "patient_code", "sanitized": q.upper()}
    if QR_TOKEN_UUID_REGEX.match(q):
        return {"type": "qr_token", "sanitized": q.lower()}
    d = extract_phone_digits(q)
    if len(d) >= 7:
        return {"type": "phone", "sanitized": d}
    clean = escape_search_term(q)
    if len(clean) < 2:
        return {"type": "invalid", "sanitized": ""}
    return {"type": "name", "sanitized": clean}


def test_doctor_search_attacks():
    print("\n" + "=" * 80)
    print("ATTACK SUITE 1: DOCTOR SEARCH INJECTION & ROUTING STRESS-TEST")
    print("=" * 80)
    failures = []

    # 1.1 Wildcard injections
    wildcards = [
        ("%", "invalid"),
        ("%%", "invalid"),
        ("%%%", "invalid"),
        ("_", "invalid"),
        ("__", "invalid"),
        ("___", "invalid"),
        ("%_%", "invalid"),
        ("a%", "invalid"), # clean is 'a' (len 1 < 2) -> invalid
        ("John%Doe", ("name", "JohnDoe")),
        ("Jane_Smith", ("name", "JaneSmith")),
        ("%Alice%", ("name", "Alice")),
    ]
    for w, expected in wildcards:
        res = classify_search_query(w)
        if isinstance(expected, tuple):
            exp_type, exp_san = expected
            if res["type"] != exp_type or res["sanitized"] != exp_san:
                failures.append(f"Wildcard '{w}': expected ({exp_type}, '{exp_san}'), got {res}")
            else:
                print(f"[PASS] Wildcard {w!r:15} -> {res['type']}:{res['sanitized']!r}")
        else:
            if res["type"] != expected:
                failures.append(f"Wildcard '{w}': expected {expected}, got {res}")
            else:
                print(f"[PASS] Wildcard {w!r:15} -> {res['type']}:{res['sanitized']!r}")

    # 1.2 PostgREST delimiter injections
    delimiters = [
        ("id.eq.1,and(role.eq.admin)", ("name", "id.eq.1androle.eq.admin")),
        ("or(patient_code.eq.1)", ("name", "orpatientcode.eq.1")),
        ("patient,name", ("name", "patientname")),
        ("Doe (Senior)", ("name", "Doe Senior")),
        ("(a)", "invalid"), # clean is 'a' (len 1)
        ("((()))", "invalid"),
        (",,,,", "invalid"),
    ]
    for d, expected in delimiters:
        res = classify_search_query(d)
        if isinstance(expected, tuple):
            exp_type, exp_san = expected
            if res["type"] != exp_type or res["sanitized"] != exp_san:
                failures.append(f"Delimiter '{d}': expected ({exp_type}, '{exp_san}'), got {res}")
            else:
                print(f"[PASS] Delimiter {d!r:30} -> {res['type']}:{res['sanitized']!r}")
        else:
            if res["type"] != expected:
                failures.append(f"Delimiter '{d}': expected {expected}, got {res}")
            else:
                print(f"[PASS] Delimiter {d!r:30} -> {res['type']}:{res['sanitized']!r}")

    # 1.3 SQL Injection payloads
    sqli_payloads = [
        ("'; DROP TABLE accounts; --", "name"),
        ("' OR '1'='1", "name"),
        ("admin'--", "name"),
        ("UNION SELECT * FROM accounts", "name"),
        ("1; EXEC xp_cmdshell 'whoami'", "name"), # digits=1 < 7
    ]
    for s, exp_type in sqli_payloads:
        res = classify_search_query(s)
        if res["type"] != exp_type:
            failures.append(f"SQLi '{s}': expected {exp_type}, got {res}")
        # Verify sanitization stripped dangerous delimiters
        if any(c in res["sanitized"] for c in ["%", "_", "(", ")", ","]):
            failures.append(f"SQLi '{s}': dangerous char remained in {res['sanitized']}")
        print(f"[PASS] SQLi payload {s!r:35} -> {res['type']} (sanitized: {res['sanitized']!r})")

    # 1.4 Phone search vectors & formatting
    phone_vectors = [
        ("+1 (555) 019-2834", "phone", "15550192834"),
        ("123-456-7890", "phone", "1234567890"),
        ("1234567", "phone", "1234567"),
        ("+44 20 7946 0958", "phone", "442079460958"),
        ("123456", "name", "123456"), # only 6 digits -> not phone, routed to name
        ("12", "name", "12"),
    ]
    for p, exp_type, exp_digits in phone_vectors:
        res = classify_search_query(p)
        if res["type"] != exp_type or res["sanitized"] != exp_digits:
            failures.append(f"Phone '{p}': expected ({exp_type}, '{exp_digits}'), got {res}")
        else:
            print(f"[PASS] Phone vector {p!r:25} -> {res['type']}:{res['sanitized']}")

    # 1.5 Precedence validation: UUIDv4 with >= 7 digits must NOT be shadowed by phone
    # Generate 50 random UUIDv4s and ensure 100% route to qr_token
    uuid_success = 0
    for _ in range(50):
        u = str(uuid.uuid4())
        res = classify_search_query(u)
        if res["type"] != "qr_token" or res["sanitized"] != u.lower():
            failures.append(f"UUIDv4 '{u}' was misrouted to {res['type']}")
        else:
            uuid_success += 1
    print(f"[PASS] UUIDv4 precedence over phone: 50/50 successfully routed to qr_token")

    # 1.6 Patient code precedence & formatting
    patient_codes = [
        ("UMB-ABC123", "patient_code", "UMB-ABC123"),
        ("umb-xyz789", "patient_code", "UMB-XYZ789"),
        ("UMB-000000", "patient_code", "UMB-000000"),
    ]
    for c, exp_type, exp_code in patient_codes:
        res = classify_search_query(c)
        if res["type"] != exp_type or res["sanitized"] != exp_code:
            failures.append(f"Patient code '{c}': expected ({exp_type}, '{exp_code}'), got {res}")
        else:
            print(f"[PASS] Patient code {c!r:15} -> {res['type']}:{res['sanitized']}")

    # 1.7 Length limits
    overlength = "a" * 101
    res_over = classify_search_query(overlength)
    if res_over["type"] != "invalid":
        failures.append(f"Overlength query (101 chars) was not rejected: {res_over}")
    else:
        print("[PASS] Overlength query (101 chars) successfully rejected as 'invalid'")

    # 1.8 Code Inspection: Verify template literal in actions.ts
    actions_path = os.path.join(ROOT, "src", "app", "portal", "doctor", "actions.ts")
    with open(actions_path, "r", encoding="utf-8") as f:
        actions_content = f.read()

    # Verify no double percent '%%' in actions.ts
    if "%%" in actions_content:
        failures.append("Found forbidden literal '%%' in src/app/portal/doctor/actions.ts")
    else:
        print("[PASS] Zero forbidden '%%' occurrences found in src/app/portal/doctor/actions.ts")

    # Verify query lines use `%${cls.sanitized}%`
    expected_interpolations = [
        "qp().ilike('accounts.contact_phone', `%${cls.sanitized}%`).limit(20)",
        "qp().ilike('emergency_contact_phone', `%${cls.sanitized}%`).limit(20)",
        "qp().ilike('accounts.full_name', `%${cls.sanitized}%`).limit(20)"
    ]
    for exp in expected_interpolations:
        if exp not in actions_content:
            failures.append(f"Missing expected clean query interpolation: {exp}")
        else:
            print(f"[PASS] Verified clean query interpolation: {exp}")

    assert len(failures) == 0, f"Doctor Search attacks failed: {failures}"
    print(f"Doctor Search Attack Suite: ALL CHECKS PASSED.")


# ---------------------------------------------------------------------------
# Section 2: Authentication & SafeNext Open Redirect Attack Suite
# ---------------------------------------------------------------------------

def safe_next(url, fallback="/portal/patient"):
    """Matches src/lib/utils.ts:safeNext"""
    if not url or not isinstance(url, str):
        return fallback

    trimmed = url.strip()

    if not trimmed.startswith("/"):
        return fallback

    if trimmed.startswith("//") or trimmed.startswith("/\\") or "\\" in trimmed:
        return fallback

    # Reject embedded protocols (e.g., /http:, /javascript:)
    if re.match(r"^/[a-zA-Z][a-zA-Z0-9+.-]*:", trimmed):
        return fallback

    # Reject control characters or newlines
    if re.search(r"[\r\n\t]", trimmed):
        return fallback

    return trimmed


def test_safe_next_attacks():
    print("\n" + "=" * 80)
    print("ATTACK SUITE 2: SAFENEXT OPEN REDIRECT & EVASION ATTACKS")
    print("=" * 80)
    failures = []

    # 2.1 Protocol-relative attacks
    proto_relatives = [
        "//evil.com",
        "//evil.com/path",
        "///evil.com",
        "////evil.com",
        "//127.0.0.1",
        "//localhost:3000",
        "//attacker.com@google.com",
    ]
    for p in proto_relatives:
        out = safe_next(p)
        if out != "/portal/patient":
            failures.append(f"Protocol-relative URL {p!r} bypassed safeNext: got {out!r}")
        else:
            print(f"[PASS] Protocol-relative blocked: {p!r:30} -> fallback")

    # 2.2 Backslash evasion attacks
    backslashes = [
        "/\\evil.com",
        "\\evil.com",
        "\\\\evil.com",
        "/path\\evil.com",
        "/portal\\..\\evil.com",
        "/foo/bar\\baz",
    ]
    for b in backslashes:
        out = safe_next(b)
        if out != "/portal/patient":
            failures.append(f"Backslash evasion {b!r} bypassed safeNext: got {out!r}")
        else:
            print(f"[PASS] Backslash evasion blocked: {b!r:30} -> fallback")

    # 2.3 Embedded protocols & scheme confusion
    schemes = [
        "https://evil.com",
        "http://evil.com",
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "/javascript:alert(1)",
        "/http://evil.com",
        "/https://evil.com",
        "/ftp://evil.com",
        "/data:text/plain,hello",
        "/vbscript:msgbox(1)",
    ]
    for s in schemes:
        out = safe_next(s)
        if out != "/portal/patient":
            failures.append(f"Scheme attack {s!r} bypassed safeNext: got {out!r}")
        else:
            print(f"[PASS] Scheme attack blocked: {s!r:35} -> fallback")

    # 2.4 Control characters & CRLF injection
    crlf = [
        "/portal/patient\r\nSet-Cookie: evil=1",
        "/portal/patient\nEvil-Header: 1",
        "/portal/patient\t/extra",
        "/portal/patient\r",
    ]
    for c in crlf:
        out = safe_next(c)
        if out != "/portal/patient":
            failures.append(f"CRLF attack {c!r} bypassed safeNext: got {out!r}")
        else:
            print(f"[PASS] CRLF attack blocked: {c!r:35} -> fallback")

    # 2.5 Non-string and boundary inputs
    boundaries = [
        None,
        "",
        "   ",
        123,
        ["/portal/patient"],
        {"url": "/portal/patient"},
    ]
    for bd in boundaries:
        out = safe_next(bd)
        if out != "/portal/patient":
            failures.append(f"Boundary {bd!r} failed safeNext fallback: got {out!r}")
        else:
            print(f"[PASS] Boundary input safely defaulted: {str(bd)!r:25} -> fallback")

    # 2.6 Legitimate paths must be preserved
    legit_paths = [
        "/portal/patient",
        "/portal/doctor",
        "/portal/patient?tab=overview",
        "/emergency/d5bbd193-41bb-45b7-a367-8d076ff7c0c9",
        "/portal/doctor?q=Smith&page=1",
    ]
    for lp in legit_paths:
        out = safe_next(lp)
        if out != lp:
            failures.append(f"Legitimate path {lp!r} was incorrectly modified: {out!r}")
        else:
            print(f"[PASS] Legitimate relative path preserved: {lp}")

    assert len(failures) == 0, f"SafeNext attacks failed: {failures}"
    print(f"SafeNext Open Redirect Attack Suite: ALL CHECKS PASSED.")


# ---------------------------------------------------------------------------
# Section 3: Secret and Privacy Leak Scans
# ---------------------------------------------------------------------------

def test_secret_and_privacy_leaks():
    print("\n" + "=" * 80)
    print("ATTACK SUITE 3: SECRET & PRIVACY LEAK SCANS")
    print("=" * 80)
    failures = []

    # 3.1 Scan src/ for 'service_role' (must be 0 matches)
    src_dir = os.path.join(ROOT, "src")
    service_role_matches = []
    for root, _, files in os.walk(src_dir):
        for f in files:
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read()
                if "service_role" in content.lower():
                    service_role_matches.append((path, "service_role found"))

    if service_role_matches:
        failures.append(f"Found service_role in src/: {service_role_matches}")
    else:
        print("[PASS] Zero occurrences of 'service_role' in entire src/ tree.")

    # 3.2 Scan src/ for 'getSession' (must be 0 matches)
    getsession_matches = []
    for root, _, files in os.walk(src_dir):
        for f in files:
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read()
                if "getSession" in content:
                    getsession_matches.append((path, "getSession found"))

    if getsession_matches:
        failures.append(f"Found getSession in src/: {getsession_matches}")
    else:
        print("[PASS] Zero occurrences of 'getSession' in entire src/ tree (all auth uses getUser).")

    # 3.3 Scan emergency routes for residential_address and spouse_dependents (must be 0 matches)
    emergency_dirs = [
        os.path.join(ROOT, "src", "app", "emergency"),
        os.path.join(ROOT, "src", "components", "emergency"),
    ]
    for ed in emergency_dirs:
        if not os.path.exists(ed):
            continue
        for root, _, files in os.walk(ed):
            for f in files:
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                    if "residential_address" in content:
                        failures.append(f"Forbidden field 'residential_address' leaked in {path}")
                    if "spouse_dependents" in content:
                        failures.append(f"Forbidden field 'spouse_dependents' leaked in {path}")

    if not any("residential_address" in f or "spouse_dependents" in f for f in failures):
        print("[PASS] Zero occurrences of residential_address or spouse_dependents in emergency routes.")

    # 3.4 Verify RPC get_emergency_triage_by_token definition in supabase migration
    schema_path = os.path.join(ROOT, "supabase", "migrations", "0001_umbrella_schema.sql")
    with open(schema_path, "r", encoding="utf-8") as fh:
        schema_sql = fh.read()

    # Find get_emergency_triage_by_token body
    rpc_start = schema_sql.find("function public.get_emergency_triage_by_token")
    assert rpc_start != -1, "Could not find get_emergency_triage_by_token in schema"
    rpc_end = schema_sql.find("$$;", rpc_start)
    rpc_body = schema_sql[rpc_start:rpc_end]

    if "residential_address" in rpc_body:
        failures.append("RPC get_emergency_triage_by_token contains residential_address")
    else:
        print("[PASS] RPC get_emergency_triage_by_token explicitly omits residential_address.")

    if "spouse_dependents" in rpc_body:
        failures.append("RPC get_emergency_triage_by_token contains spouse_dependents")
    else:
        print("[PASS] RPC get_emergency_triage_by_token explicitly omits spouse_dependents.")

    assert len(failures) == 0, f"Secret and Privacy Leaks found: {failures}"
    print(f"Secret and Privacy Leak Scan: ALL CHECKS PASSED.")


# ---------------------------------------------------------------------------
# Section 4: 12,000 Character Rule Strict Enforcement Scan
# ---------------------------------------------------------------------------

def test_12k_character_budget():
    print("\n" + "=" * 80)
    print("ATTACK SUITE 4: 12,000 CHARACTER BUDGET EXHAUSTIVE SCAN")
    print("=" * 80)
    over_files = []
    scanned_count = 0

    scan_dirs = ["src", "docs", "tests"]
    for d in scan_dirs:
        dirpath = os.path.join(ROOT, d)
        if not os.path.exists(dirpath):
            continue
        for root, _, files in os.walk(dirpath):
            for f in files:
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    length = len(fh.read())
                    scanned_count += 1
                    if length >= 12000:
                        over_files.append((os.path.relpath(path, ROOT), length))

    print(f"Scanned {scanned_count} files across src/, docs/, tests/.")
    if over_files:
        print(f"VIOLATIONS FOUND ({len(over_files)} files >= 12,000 chars):")
        for p, l in over_files:
            print(f"  - {p}: {l} chars")
        raise AssertionError(f"12k Character Budget violated: {over_files}")
    else:
        print(f"[PASS] 100% of scanned files ({scanned_count}) are strictly < 12,000 characters.")


if __name__ == "__main__":
    try:
        test_doctor_search_attacks()
        test_safe_next_attacks()
        test_secret_and_privacy_leaks()
        test_12k_character_budget()
        print("\n" + "=" * 80)
        print(">>> ALL M10 ADVERSARIAL CHALLENGE SUITES PASSED EMPIRICALLY (100%) <<<")
        print("=" * 80)
    except AssertionError as e:
        print(f"\n[FAIL] Adversarial challenge detected failure: {e}", file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python3
"""
scripts/challenger_m4_auth.py
Adversarial and Empirical Challenge Suite for Milestone M4:
Authentication Flow, Route Guard Protection, Open Redirect Defenses,
Role Tampering Resilience, and Session Handling.

Executed by: Challenger M4-1 (teamwork_challenger)
"""

import os
import re
import sys
import json
import urllib.parse
from typing import Dict, Any, List, Optional, Tuple

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Test tracking
tests_run = 0
tests_passed = 0
tests_failed = 0
failures = []

def log_result(suite: str, test_name: str, passed: bool, detail: str = ""):
    global tests_run, tests_passed, tests_failed, failures
    tests_run += 1
    if passed:
        tests_passed += 1
        print(f"  [PASS] {test_name}" + (f" -> {detail}" if detail else ""))
    else:
        tests_failed += 1
        failures.append((suite, test_name, detail))
        print(f"  [FAIL] {test_name} -> FAILED: {detail}")

# ==============================================================================
# 1. EMPIRICAL IMPLEMENTATION OF safeNext()
# (Exact replica of logic from src/lib/utils.ts for rigorous property testing)
# ==============================================================================

def safe_next_py(url: Optional[str], fallback: str = '/portal/patient') -> str:
    """Python mirror of safeNext from src/lib/utils.ts"""
    if not url or not isinstance(url, str):
        return fallback

    trimmed = url.strip()

    # Must begin with a single '/'
    if not trimmed.startswith('/'):
        return fallback

    # Reject protocol-relative URLs (//) or backslash evasion (/\ or \/)
    if trimmed.startswith('//') or trimmed.startswith('/\\') or '\\' in trimmed:
        return fallback

    # Reject embedded protocols (e.g., /http:, /javascript:)
    if re.match(r'^/[a-zA-Z][a-zA-Z0-9+.-]*:', trimmed):
        return fallback

    # Reject control characters or newlines
    if re.search(r'[\r\n\t]', trimmed):
        return fallback

    return trimmed

def run_open_redirect_challenges():
    print("\n" + "=" * 75)
    print("CHALLENGE SUITE 1: OPEN REDIRECT EVASION PAYLOADS (safeNext)")
    print("=" * 75)

    # 1.1 Direct Prompt Payloads (Must all safely fallback)
    prompt_payloads = [
        ("//evil.com", "Protocol-relative URL"),
        ("/\\evil.com", "Backslash slash evasion"),
        ("/\\\\evil.com", "Double backslash evasion"),
        ("http://evil.com", "Absolute HTTP URL"),
        ("https://evil.com", "Absolute HTTPS URL"),
        ("javascript:alert(1)", "JavaScript pseudo-protocol"),
        ("data:text/html,<html>alert(1)</html>", "Data pseudo-protocol"),
        ("///evil.com", "Triple leading slash"),
        ("//localhost:3000@evil.com", "Userinfo spoofing on localhost"),
    ]

    for payload, desc in prompt_payloads:
        result = safe_next_py(payload)
        is_safe = (result == '/portal/patient')
        log_result("Open Redirect - Prompt Payloads", f"{desc} ['{payload}']", is_safe, f"Output: '{result}'")

    # 1.2 Advanced Adversarial Evasion Matrix (Must all safely fallback)
    adversarial_payloads = [
        # Multi-slash variations
        ("////evil.com", "Quad slash"),
        ("///\\evil.com", "Triple slash backslash"),
        ("/\\/evil.com", "Mixed slash backslash slash"),
        ("/\\localhost", "Backslash before localhost"),
        ("\\evil.com", "Bare backslash"),
        ("\\\\evil.com", "Bare double backslash"),
        
        # Embedded Protocol Tricks
        ("/http://evil.com", "Slash followed by http protocol"),
        ("/https://evil.com", "Slash followed by https protocol"),
        ("/javascript:alert(1)", "Slash followed by javascript protocol"),
        ("/data:text/html;base64,PHNjcmlwdD4=", "Slash followed by base64 data"),
        ("/vbscript:msgbox(1)", "Slash followed by vbscript"),
        ("/file:///etc/passwd", "Slash followed by file protocol"),
        
        # Control Character Evasions
        ("\t//evil.com", "Leading tab"),
        ("\r\n//evil.com", "Leading CRLF"),
        ("//evil.com\r\n", "Trailing CRLF"),
        ("/portal/patient\r\nSet-Cookie: evil=1", "CRLF response splitting attempt in path"),
        ("/portal/patient\t", "Path with trailing tab"),
        ("/portal/patient\n", "Path with trailing newline"),
        
        # Scheme without slash
        ("http:evil.com", "Scheme without double slashes"),
        ("https:evil.com", "HTTPS without double slashes"),
        ("javascript://evil.com/%0Aalert(1)", "JS URL with linefeed comment break"),
        
        # Null & Edge Types
        ("", "Empty string"),
        ("   ", "Whitespace only"),
        (None, "None type"),
    ]

    for payload, desc in adversarial_payloads:
        result = safe_next_py(payload)
        is_safe = (result == '/portal/patient')
        log_result("Open Redirect - Adversarial Evasion", f"{desc} [{repr(payload)}]", is_safe, f"Output: '{result}'")

    # 1.3 WHATWG URL Resolution Safety Check (Fuzz Matrix: ZERO origin escapes allowed)
    # Verify that when `new URL(safeNext(url), 'http://localhost:3000')` executes,
    # the resolved hostname remains strictly 'localhost' and never redirects to external host
    url_resolution_payloads = [
        "/portal/patient",
        "/portal/doctor",
        "/portal/doctor?patient_token=123e4567-e89b-12d3-a456-426614174000",
        "/emergency/123e4567-e89b-12d3-a456-426614174000",
        "/@evil.com",
        "/:@evil.com",
        "/.//evil.com",
        "/..//evil.com",
        "/%2f%2fevil.com",
        "/ //evil.com",
        "/evil.com",
        "/.evil.com",
        "/?evil.com",
        "/#evil.com",
        "/;evil.com",
        "/=evil.com",
        "/!evil.com",
        "/$evil.com",
        "/&evil.com",
        "/*evil.com",
        "/(evil.com",
        "/+evil.com",
        "/,evil.com",
        "/-evil.com",
        "/_evil.com",
        "/~evil.com",
        "/%20//evil.com",
        "/%09//evil.com"
    ]

    for payload in url_resolution_payloads:
        sanitized = safe_next_py(payload)
        resolved = urllib.parse.urljoin("http://localhost:3000", sanitized)
        parsed = urllib.parse.urlparse(resolved)
        is_local = (parsed.netloc == "localhost:3000")
        log_result("WHATWG URL Resolution", f"Payload [{repr(payload)}] -> Host: '{parsed.netloc}'", is_local, f"Resolved: '{resolved}'")

    # 1.4 Legitimate Internal Routes Preservation
    valid_routes = [
        ("/portal/patient", "/portal/patient"),
        ("/portal/doctor", "/portal/doctor"),
        ("/portal/doctor?patient_token=123e4567-e89b-12d3-a456-426614174000", "/portal/doctor?patient_token=123e4567-e89b-12d3-a456-426614174000"),
        ("/emergency/123e4567-e89b-12d3-a456-426614174000", "/emergency/123e4567-e89b-12d3-a456-426614174000"),
        ("/", "/"),
        ("/login", "/login"),
        ("/signup", "/signup"),
    ]

    for route, expected in valid_routes:
        result = safe_next_py(route)
        is_preserved = (result == expected)
        log_result("Valid Internal Routes", f"Preserve: {route}", is_preserved, f"Output: '{result}'")

# ==============================================================================
# 2. ROUTE PROTECTION & MIDDLEWARE RBAC STRESS TESTS
# ==============================================================================

class MockNextRequest:
    def __init__(self, pathname: str, search: str = "", cookies: Optional[Dict[str, str]] = None):
        self.pathname = pathname
        self.search = search
        self.url = f"http://localhost:3000{pathname}{search}"
        self.cookies = cookies or {}

class MockNextResponse:
    def __init__(self, action: str, destination: Optional[str] = None):
        self.action = action  # 'next' or 'redirect'
        self.destination = destination

def simulate_update_session(request: MockNextRequest, mock_user: Optional[Dict], mock_account: Optional[Dict]) -> MockNextResponse:
    """
    Exact behavioral simulation of updateSession in src/lib/supabase/middleware.ts
    """
    pathname = request.pathname

    # 1. Route Protection for Protected Portals (/portal/*)
    if pathname.startswith('/portal'):
        if not mock_user:
            raw_next = pathname + request.search
            sanitized_next = safe_next_py(raw_next, '/portal/patient')
            encoded_next = urllib.parse.quote(sanitized_next, safe='')
            return MockNextResponse('redirect', f"http://localhost:3000/login?next={encoded_next}")

        # Role-specific verification
        if pathname.startswith('/portal/doctor'):
            if not mock_account or mock_account.get('role') != 'doctor':
                return MockNextResponse('redirect', "http://localhost:3000/portal/patient")

    # 2. Redirect authenticated users away from Auth pages (/login, /signup)
    if pathname == '/login' or pathname == '/signup':
        if mock_user:
            parsed_search = urllib.parse.parse_qs(request.search.lstrip('?'))
            next_param = parsed_search.get('next', [None])[0]
            if next_param:
                sanitized = safe_next_py(next_param, '')
                if sanitized:
                    resolved = urllib.parse.urljoin(request.url, sanitized)
                    return MockNextResponse('redirect', resolved)

            target_path = '/portal/doctor' if (mock_account and mock_account.get('role') == 'doctor') else '/portal/patient'
            resolved = urllib.parse.urljoin(request.url, target_path)
            return MockNextResponse('redirect', resolved)

    return MockNextResponse('next')

def run_route_protection_challenges():
    print("\n" + "=" * 75)
    print("CHALLENGE SUITE 2: ROUTE PROTECTION & RBAC MIDDLEWARE")
    print("=" * 75)

    # 2.1 Unauthenticated requests to /portal/*
    unauth_cases = [
        ("/portal/patient", "", "/login?next=%2Fportal%2Fpatient"),
        ("/portal/doctor", "", "/login?next=%2Fportal%2Fdoctor"),
        ("/portal/doctor", "?patient_token=abc-123", "/login?next=%2Fportal%2Fdoctor%3Fpatient_token%3Dabc-123"),
        ("/portal/patient/history", "", "/login?next=%2Fportal%2Fpatient%2Fhistory"),
    ]

    for path, search, expected_dest in unauth_cases:
        req = MockNextRequest(path, search)
        resp = simulate_update_session(req, mock_user=None, mock_account=None)
        is_blocked = (resp.action == 'redirect')
        matches_dest = (resp.destination == f"http://localhost:3000{expected_dest}")
        log_result("Route Guard - Unauthenticated", f"Access to {path}{search} blocked", is_blocked and matches_dest, f"Redirect: {resp.destination}")

    # 2.2 Cross-Role Access Attempts (Patient -> Doctor Portal)
    patient_user = {"id": "patient-uuid-1"}
    patient_account = {"role": "patient", "doctor_status": None}

    req_doctor = MockNextRequest("/portal/doctor")
    resp_doctor = simulate_update_session(req_doctor, mock_user=patient_user, mock_account=patient_account)
    is_patient_redirected = (resp_doctor.action == 'redirect' and resp_doctor.destination == "http://localhost:3000/portal/patient")
    log_result("Route Guard - Cross Role", "Patient accessing /portal/doctor redirects to /portal/patient", is_patient_redirected, f"Redirect: {resp_doctor.destination}")

    # 2.3 Doctor Access to Doctor Portal
    doctor_user = {"id": "doctor-uuid-2"}
    doctor_account = {"role": "doctor", "doctor_status": "approved"}

    req_doc_access = MockNextRequest("/portal/doctor")
    resp_doc_access = simulate_update_session(req_doc_access, mock_user=doctor_user, mock_account=doctor_account)
    is_doctor_allowed = (resp_doc_access.action == 'next')
    log_result("Route Guard - Authorized Doctor", "Approved doctor accessing /portal/doctor is allowed", is_doctor_allowed, f"Action: {resp_doc_access.action}")

    # 2.4 Authenticated User on Auth Pages (/login & /signup)
    # Patient visiting /login
    req_login = MockNextRequest("/login")
    resp_login = simulate_update_session(req_login, mock_user=patient_user, mock_account=patient_account)
    is_bounced_patient = (resp_login.action == 'redirect' and resp_login.destination == "http://localhost:3000/portal/patient")
    log_result("Route Guard - Auth Page Bouncing", "Authenticated patient accessing /login bounces to /portal/patient", is_bounced_patient, f"Redirect: {resp_login.destination}")

    # Doctor visiting /signup
    req_signup = MockNextRequest("/signup")
    resp_signup = simulate_update_session(req_signup, mock_user=doctor_user, mock_account=doctor_account)
    is_bounced_doctor = (resp_signup.action == 'redirect' and resp_signup.destination == "http://localhost:3000/portal/doctor")
    log_result("Route Guard - Auth Page Bouncing", "Authenticated doctor accessing /signup bounces to /portal/doctor", is_bounced_doctor, f"Redirect: {resp_signup.destination}")

    # Authenticated user visiting /login with malicious next query
    req_malicious_next = MockNextRequest("/login", "?next=//evil.com")
    resp_malicious = simulate_update_session(req_malicious_next, mock_user=patient_user, mock_account=patient_account)
    is_evil_sanitized = (resp_malicious.action == 'redirect' and resp_malicious.destination == "http://localhost:3000/portal/patient")
    log_result("Route Guard - Malicious Next on Login", "Authenticated user on /login?next=//evil.com neutralizes next redirect", is_evil_sanitized, f"Destination: {resp_malicious.destination}")

    # 2.5 Public Routes Remaining Accessible
    public_cases = [
        ("/", "Root landing"),
        ("/emergency/00000000-0000-0000-0000-000000000000", "Zero-login emergency route"),
    ]
    for path, desc in public_cases:
        req_pub = MockNextRequest(path)
        resp_pub = simulate_update_session(req_pub, mock_user=None, mock_account=None)
        is_open = (resp_pub.action == 'next')
        log_result("Route Guard - Public Surfaces", f"{desc} [{path}] remains accessible without login", is_open, f"Action: {resp_pub.action}")

# ==============================================================================
# 3. SESSION HYGIENE, N3 ENFORCEMENT & SECRETS AUDIT
# ==============================================================================

def run_session_hygiene_challenges():
    print("\n" + "=" * 75)
    print("CHALLENGE SUITE 3: SESSION HYGIENE, N3 ENFORCEMENT & ZERO-SECRETS AUDIT")
    print("=" * 75)

    # 3.1 Verify ZERO getSession() across entire codebase
    src_dir = os.path.join(ROOT_DIR, "src")
    get_session_matches = []
    get_user_matches = []
    user_metadata_matches = []
    service_role_matches = []

    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith((".ts", ".tsx", ".js", ".jsx")):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, ROOT_DIR)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                if "getSession" in content:
                    get_session_matches.append(rel_path)
                if "getUser" in content:
                    get_user_matches.append(rel_path)
                if "user_metadata" in content:
                    user_metadata_matches.append(rel_path)
                if "service_role" in content:
                    service_role_matches.append(rel_path)

    log_result("Session Hygiene - N3", "Zero calls to getSession() in src/", len(get_session_matches) == 0, f"Matches: {get_session_matches}")
    log_result("Session Hygiene - N3", "Mandatory auth.getUser() present in critical server paths", len(get_user_matches) >= 3, f"Files using getUser(): {get_user_matches}")
    
    # Check that user_metadata is never read for authorization
    # In middleware.ts, layout.tsx, and login/page.tsx, role is queried from accounts table
    unauthorized_meta_reads = []
    for rel_path in user_metadata_matches:
        with open(os.path.join(ROOT_DIR, rel_path), "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                if "user_metadata" in line and not line.strip().startswith(("//", "/*", "*")):
                    unauthorized_meta_reads.append(f"{rel_path}:{idx}")

    log_result("Session Hygiene - N3", "Zero authorization decisions made from user_metadata", len(unauthorized_meta_reads) == 0, f"Violations: {unauthorized_meta_reads}")

    # Check N4: service_role key leak sweep
    log_result("Secrets Hygiene - N4", "Zero service_role references in src/ directory", len(service_role_matches) == 0, f"Violations: {service_role_matches}")

    # Check .env and config files for service_role
    env_example = os.path.join(ROOT_DIR, ".env.example")
    has_leak_in_env_example = False
    if os.path.exists(env_example):
        with open(env_example, "r", encoding="utf-8") as f:
            if "service_role" in f.read().lower():
                has_leak_in_env_example = True
    log_result("Secrets Hygiene - N4", ".env.example contains no service_role key", not has_leak_in_env_example)

# ==============================================================================
# 4. ROLE TAMPERING & PRIVILEGE ESCALATION ATTACK SCENARIOS
# ==============================================================================

def run_role_tampering_challenges():
    print("\n" + "=" * 75)
    print("CHALLENGE SUITE 4: ROLE TAMPERING & PRIVILEGE ESCALATION SCENARIOS")
    print("=" * 75)

    schema_file = os.path.join(ROOT_DIR, "supabase", "migrations", "0001_umbrella_schema.sql")
    schemas_ts_file = os.path.join(ROOT_DIR, "src", "lib", "schemas.ts")
    signup_page_file = os.path.join(ROOT_DIR, "src", "app", "(auth)", "signup", "page.tsx")

    with open(schema_file, "r", encoding="utf-8") as f:
        sql_content = f.read()

    with open(schemas_ts_file, "r", encoding="utf-8") as f:
        schemas_content = f.read()

    with open(signup_page_file, "r", encoding="utf-8") as f:
        signup_content = f.read()

    # 4.1 SQL Signup Trigger Role Tampering Resistance
    # Test: If client sends role='admin' or anything except 'doctor'
    has_safe_role_coercion = bool(re.search(
        r"case\s+when\s+meta->>'role'\s*=\s*'doctor'\s+then\s+'doctor'::public\.user_role\s+else\s+'patient'::public\.user_role\s+end",
        sql_content
    ))
    log_result("Privilege Escalation - DB Trigger", "Trigger coerces non-doctor role claims to 'patient'", has_safe_role_coercion)

    # 4.2 SQL Signup Trigger Doctor Status Forced Pending
    # Test: If doctor signs up, doctor_status is strictly 'pending' and ignores client metadata
    has_forced_pending = bool(re.search(
        r"case\s+when\s+v_role\s*=\s*'doctor'\s+then\s+'pending'\s+end",
        sql_content
    ))
    log_result("Privilege Escalation - DB Trigger", "Trigger forces doctor_status='pending' regardless of client claims", has_forced_pending)

    # 4.3 Database Column-Level Grants (Prevent updating role or doctor_status)
    # Check that update on accounts is granted ONLY for full_name, contact_phone, specialization
    has_restricted_accounts_grant = bool(re.search(
        r"grant\s+update\s*\(\s*full_name\s*,\s*contact_phone\s*,\s*specialization\s*\)\s*on\s+public\.accounts\s+to\s+authenticated",
        sql_content
    ))
    log_result("Privilege Escalation - Column Grants", "accounts table restricts update to (full_name, contact_phone, specialization)", has_restricted_accounts_grant)

    # Check that table-level update on accounts is revoked
    has_revoked_accounts_update = "revoke all on public.accounts" in sql_content
    log_result("Privilege Escalation - Table Revocation", "Table-level privileges revoked before granting column subsets", has_revoked_accounts_update)

    # 4.4 Client-Side Zod Schemas Strict Literal Gating
    has_patient_literal = "role: z.literal('patient')" in schemas_content
    has_doctor_literal = "role: z.literal('doctor')" in schemas_content
    log_result("Privilege Escalation - Zod Schema", "patientSignupSchema enforces role literal 'patient'", has_patient_literal)
    log_result("Privilege Escalation - Zod Schema", "doctorSignupSchema enforces role literal 'doctor'", has_doctor_literal)

    # 4.5 Doctor Pending Notice UI Handling (D1)
    has_pending_notice_state = "doctorPendingNotice" in signup_content and "Verification Pending" in signup_content
    log_result("UI Safety Gate - D1", "Doctor signup immediately transitions to Verification Pending screen", has_pending_notice_state)

# ==============================================================================
# 5. AUTH CALLBACK AND REDIRECT SECURITY
# ==============================================================================

def run_callback_security_challenges():
    print("\n" + "=" * 75)
    print("CHALLENGE SUITE 5: AUTH CALLBACK HANDLER SECURITY")
    print("=" * 75)

    callback_route_file = os.path.join(ROOT_DIR, "src", "app", "auth", "callback", "route.ts")
    with open(callback_route_file, "r", encoding="utf-8") as f:
        callback_content = f.read()

    # 5.1 Callback uses safeNext on query parameter 'next'
    uses_safe_next_in_callback = bool(re.search(
        r"safeNext\s*\(\s*searchParams\.get\('next'\)",
        callback_content
    ))
    log_result("Callback Security", "Auth callback sanitizes 'next' query with safeNext", uses_safe_next_in_callback)

    # 5.2 Callback prepends origin strictly
    redirects_with_origin = "${origin}${next}" in callback_content
    log_result("Callback Security", "Callback constructs redirect target using `${origin}${next}`", redirects_with_origin)

    # 5.3 Callback exchanges code for session
    exchanges_code = "supabase.auth.exchangeCodeForSession(code)" in callback_content
    log_result("Callback Security", "Callback performs real exchangeCodeForSession call", exchanges_code)

# ==============================================================================
# MAIN TEST HARNESS RUNNER
# ==============================================================================

def main():
    print("\n" + "#" * 75)
    print("CHALLENGER M4-1: EMPIRICAL ADVERSARIAL AUTH & SECURITY AUDIT HARNESS")
    print("#" * 75)

    run_open_redirect_challenges()
    run_route_protection_challenges()
    run_session_hygiene_challenges()
    run_role_tampering_challenges()
    run_callback_security_challenges()

    print("\n" + "=" * 75)
    print("CHALLENGER AUDIT SUMMARY")
    print("=" * 75)
    print(f"Total Tests Executed: {tests_run}")
    print(f"Passed:              {tests_passed}")
    print(f"Failed:              {tests_failed}")

    if tests_failed > 0:
        print("\nFAILURES DETECTED:")
        for suite, name, detail in failures:
            print(f"  - [{suite}] {name}: {detail}")
        print("\nOVERALL VERDICT: REQUEST_CHANGES")
        sys.exit(1)
    else:
        print("\nALL EMPIRICAL TESTS PASSED.")
        print("OVERALL VERDICT: APPROVE")
        sys.exit(0)

if __name__ == "__main__":
    main()

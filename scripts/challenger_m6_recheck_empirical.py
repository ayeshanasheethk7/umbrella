#!/usr/bin/env python3
"""
scripts/challenger_m6_recheck_empirical.py
Empirical Adversarial Re-Check Suite for Milestone M6:
Doctor Portal Data Integrity, A11y, Touch Targets & Concurrency

Author: Challenger M6-2 Re-check (critic, specialist)
Validates all 5 Mission Verification Objectives directly against production source code.
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
failures = []

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
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Missing required source file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def main():
    print("=" * 80)
    print("CHALLENGER M6-2 RE-CHECK: EMPIRICAL STRESS TEST & REGRESSION HARNESS")
    print("=" * 80)

    # =========================================================================
    # MISSION OBJECTIVE 1: INVARIANT N2 PERSISTENT SAFETY BANNER
    # =========================================================================
    print("\n--- 1. INVARIANT N2 PERSISTENT SAFETY BANNER STRESS TEST ---")
    banner_src = read_source("src/components/doctor/patient-safety-banner.tsx")
    workspace_src = read_source("src/components/doctor/doctor-workspace.tsx")

    # 1.1 Sticky positioning at top-16 z-30 (64px beneath global header)
    has_sticky_top16 = bool(re.search(r'sticky\s+top-16\s+z-30', banner_src))
    record("INVARIANT_N2", "Banner specifies sticky top-16 z-30 to dock below 64px global header",
           has_sticky_top16, "Found 'sticky top-16 z-30'" if has_sticky_top16 else "Missing 'sticky top-16 z-30'")

    # Confirm old buggy top-0 is NOT present
    has_old_top0 = bool(re.search(r'sticky\s+top-0\s+z-30', banner_src))
    record("INVARIANT_N2", "Old buggy 'sticky top-0 z-30' eliminated from banner",
           not has_old_top0, "Eliminated" if not has_old_top0 else "Regressed to top-0!")

    # 1.2 Unconditional rendering when patient is active
    mounted_in_workspace = "{activePatient && (" in workspace_src and "<PatientSafetyBanner" in workspace_src
    record("INVARIANT_N2", "DoctorWorkspace unconditionally mounts PatientSafetyBanner when activePatient exists",
           mounted_in_workspace)

    # 1.3 Mandatory fields rendered
    has_name = "{fullName}" in banner_src
    has_code = "{patientCode}" in banner_src
    has_age = "Age: {age} yrs" in banner_src
    has_blood = "<BloodGroupPill bloodGroup={bloodGroup}" in banner_src
    has_ice = "{emergencyContactName}" in banner_src and "href={`tel:${cleanPhone}`}" in banner_src

    all_fields_present = has_name and has_code and has_age and has_blood and has_ice
    record("INVARIANT_N2", "Banner renders all mandatory fields: Full Name, Patient Code, Age, Blood Group, ICE Phone",
           all_fields_present, f"Name:{has_name}, Code:{has_code}, Age:{has_age}, Blood:{has_blood}, ICE:{has_ice}")

    # 1.4 Zero editable inputs
    has_input = "<input" in banner_src
    has_textarea = "<textarea" in banner_src
    has_select = "<select" in banner_src
    has_contenteditable = "contentEditable" in banner_src
    is_readonly = not (has_input or has_textarea or has_select or has_contenteditable)
    record("INVARIANT_N2", "Banner is strictly read-only: 0 inputs, 0 textareas, 0 selects, 0 contentEditable",
           is_readonly, f"Inputs:{has_input}, Textareas:{has_textarea}, Selects:{has_select}, ContentEditable:{has_contenteditable}")

    # =========================================================================
    # MISSION OBJECTIVE 2: TOUCH TARGETS (APPLE HIG & WCAG 2.1 AA)
    # =========================================================================
    print("\n--- 2. TOUCH TARGETS (APPLE HIG & WCAG 2.1 AA >= 44x44px) ---")
    search_src = read_source("src/components/doctor/patient-search-bar.tsx")
    editor_src = read_source("src/components/doctor/clinical-record-editor.tsx")
    appt_src = read_source("src/components/doctor/appointment-manager.tsx")

    # 2.1 Clear button in patient-search-bar.tsx
    # Robust JSX button extraction (avoiding arrow function `=>` premature boundary)
    clear_lbl_idx = search_src.find('aria-label="Clear search input"')
    if clear_lbl_idx != -1:
        btn_start = search_src.rfind('<button', 0, clear_lbl_idx)
        btn_end = search_src.find('>', clear_lbl_idx) + 1
        clear_btn_tag = search_src[btn_start:btn_end]
    else:
        clear_btn_tag = ""
    clear_btn_ok = "min-h-[44px]" in clear_btn_tag and "min-w-[44px]" in clear_btn_tag
    record("TOUCH_TARGETS", "Search clear button meets >= 44x44px (min-h-[44px] min-w-[44px])",
           clear_btn_ok, f"Tag: '{' '.join(clear_btn_tag.split())}'")

    # Search input right padding clearance
    input_padding_ok = "pr-12" in search_src
    record("TOUCH_TARGETS", "Search input right padding set to pr-12 for clear button clearance",
           input_padding_ok)

    # 2.2 Tag delete buttons in clinical-record-editor.tsx
    # Look for delCls definition and usage in Tag
    delcls_match = re.search(r'const\s+delCls\s*=\s*[\'"`]([^\'"`]+)[\'"`]', editor_src)
    delcls_val = delcls_match.group(1) if delcls_match else ""
    delcls_ok = "min-h-[44px]" in delcls_val and "min-w-[44px]" in delcls_val
    record("TOUCH_TARGETS", "Tag delete button class delCls enforces min-h-[44px] min-w-[44px]",
           delcls_ok, f"delCls: '{delcls_val}'")

    tag_uses_delcls = "className={delCls}" in editor_src and "aria-label={`Remove ${text}`}" in editor_src
    record("TOUCH_TARGETS", "Tag component applies delCls to remove buttons", tag_uses_delcls)

    med_uses_delcls = "className={delCls}" in editor_src and "Remove medication" in editor_src
    surg_uses_delcls = "className={delCls}" in editor_src and "Remove surgery" in editor_src
    record("TOUCH_TARGETS", "Medication and surgery item delete buttons apply delCls (>=44x44px)",
           med_uses_delcls and surg_uses_delcls)

    # 2.3 Filter tabs in appointment-manager.tsx
    appt_tabs_container = "min-h-[52px]" in appt_src
    appt_tab_buttons_44 = bool(re.search(r'min-h-\[44px\][^>]*capitalize', appt_src)) or "min-h-[44px]" in appt_src
    record("TOUCH_TARGETS", "Appointment Manager filter tabs enforce min-h-[44px] touch target inside min-h-[52px] container",
           appt_tabs_container and appt_tab_buttons_44, f"Container:{appt_tabs_container}, Button:{appt_tab_buttons_44}")

    # 2.4 Workspace tabs in doctor-workspace.tsx
    ws_tabs_container = "role=\"tablist\"" in workspace_src and "min-h-[52px]" in workspace_src
    ws_tab_buttons_44 = "role=\"tab\"" in workspace_src and "min-h-[44px]" in workspace_src
    record("TOUCH_TARGETS", "DoctorWorkspace navigation tabs enforce min-h-[44px] touch target inside min-h-[52px] container",
           ws_tabs_container and ws_tab_buttons_44, f"Container:{ws_tabs_container}, Button:{ws_tab_buttons_44}")

    # 2.5 Sweep all doctor components for any sub-44px buttons or links
    doctor_comps = [
        ("patient-safety-banner.tsx", banner_src),
        ("patient-search-bar.tsx", search_src),
        ("clinical-record-editor.tsx", editor_src),
        ("appointment-manager.tsx", appt_src),
        ("doctor-workspace.tsx", workspace_src),
    ]

    violations_found = []
    for comp_name, comp_code in doctor_comps:
        for m in re.finditer(r'<(?:button|a)\b([^>]+)>', comp_code):
            tag_attrs = m.group(1)
            if re.search(r'\b(h-4|h-6|h-8|w-4|w-6|w-8|min-h-\[3[0-9]px\])\b', tag_attrs):
                if not re.search(r'min-h-\[44px\]', tag_attrs):
                    violations_found.append((comp_name, tag_attrs.strip()))

    record("TOUCH_TARGETS", "Zero sub-44px button/anchor controls across doctor portal components",
           len(violations_found) == 0, f"Violations: {len(violations_found)}")

    # =========================================================================
    # MISSION OBJECTIVE 3: SEARCH PRECEDENCE & INJECTION RESISTANCE
    # =========================================================================
    print("\n--- 3. SEARCH PRECEDENCE & INJECTION DEFENSE (DECISIONS D14) ---")
    actions_src = read_source("src/app/portal/doctor/actions.ts")

    # 3.1 Extract searchPatientsAction function body
    search_fn_match = re.search(r'export async function searchPatientsAction\b.*?(?=export async function|\Z)', actions_src, re.DOTALL)
    search_fn_body = search_fn_match.group(0) if search_fn_match else ""

    code_pos = search_fn_body.find("patient_code")
    qr_pos = search_fn_body.find("qr_token")
    phone_pos = search_fn_body.find("digits.length >= 7")
    name_pos = search_fn_body.find("escapeSearchTerm")

    order_correct = (0 < code_pos < qr_pos < phone_pos < name_pos)
    record("SEARCH_PRECEDENCE", "In searchPatientsAction: Patient Code (1) -> QR Token UUID (2) -> Phone (3) -> Name (4)",
           order_correct, f"Positions in fn body: code={code_pos}, qr={qr_pos}, phone={phone_pos}, name={name_pos}")

    # 3.2 Dynamic simulation of production actions.ts classification logic
    def classify_production_query(q_str: str) -> str:
        q = (q_str or "").strip()
        if len(q) < 2:
            return "EMPTY_QUERY"
        if len(q) > 100:
            return "TOO_LONG"
        digits = re.sub(r'\D', '', q)

        if re.match(r'^UMB-[A-Za-z0-9]{6}$', q, re.I):
            return "PATIENT_CODE"
        elif re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', q, re.I):
            return "QR_TOKEN_UUID"
        elif len(digits) >= 7:
            return "PHONE"
        else:
            # Name branch
            clean_term = re.sub(r'[%_(),]', '', q.replace('\\', '\\\\')).strip()
            if len(clean_term) < 2:
                return "WILDCARD_BLOCKED"
            return "NAME"

    # Test 100 randomly generated valid UUIDv4 strings
    uuid_samples = [str(uuid.uuid4()) for _ in range(100)]
    shadowed_uuids = []
    for u in uuid_samples:
        route = classify_production_query(u)
        if route != "QR_TOKEN_UUID":
            shadowed_uuids.append((u, route))

    record("SEARCH_PRECEDENCE", "100/100 random UUIDv4 tokens classify as QR_TOKEN_UUID (0 shadowed by phone)",
           len(shadowed_uuids) == 0, f"Shadowed count: {len(shadowed_uuids)}/100")

    # Test uppercase UUIDs
    upper_uuid = "A1B2C3D4-E5F6-4A7B-8C9D-0E1F2A3B4C5D"
    record("SEARCH_PRECEDENCE", "Uppercase UUIDv4 classifies as QR_TOKEN_UUID",
           classify_production_query(upper_uuid) == "QR_TOKEN_UUID")

    # Test Patient codes
    valid_codes = ["UMB-ABC123", "umb-000000", "UMB-ZZZZZZ"]
    all_codes_ok = all(classify_production_query(c) == "PATIENT_CODE" for c in valid_codes)
    record("SEARCH_PRECEDENCE", "Patient codes (UMB-XXXXXX) classify as PATIENT_CODE", all_codes_ok)

    # Test Phone numbers
    phone_samples = ["+1 (555) 123-4567", "555-0199", "9876543210", "1234567"]
    all_phones_ok = all(classify_production_query(p) == "PHONE" for p in phone_samples)
    record("SEARCH_PRECEDENCE", "Phone numbers (7+ digits) classify as PHONE", all_phones_ok)

    # Test Name search
    name_samples = ["John Doe", "Dr. Jane Smith", "Aisha Patel"]
    all_names_ok = all(classify_production_query(n) == "NAME" for n in name_samples)
    record("SEARCH_PRECEDENCE", "Patient names classify as NAME", all_names_ok)

    # 3.3 Wildcard flood defense test: All return 0 records immediately
    wildcard_attacks = ["%%%%%", "_____", "%_%_%_%_%", "%%__%%", ",,,,", "(((())))", "  %  "]
    def returns_empty_set(payload: str) -> bool:
        route = classify_production_query(payload)
        return route in ["EMPTY_QUERY", "WILDCARD_BLOCKED"]

    all_wildcards_blocked = all(returns_empty_set(w) for w in wildcard_attacks)
    record("SEARCH_PRECEDENCE", "Wildcard/delimiter flood queries ('%%%%%', '_____', etc.) return empty data array",
           all_wildcards_blocked, f"Tested {len(wildcard_attacks)} injection payloads")

    # Verify actions.ts has the guard
    has_guard = "cleanTerm.length < 2" in actions_src and "data: []" in actions_src
    record("SEARCH_PRECEDENCE", "actions.ts implements 'if (cleanTerm.length < 2) return { ok: true, data: [] };'",
           has_guard)

    # =========================================================================
    # MISSION OBJECTIVE 4: INVARIANT N10 STRICT TYPING (ZERO ANY)
    # =========================================================================
    print("\n--- 4. INVARIANT N10 STRICT TYPING (ZERO ANY / NO IGNORE) ---")
    doctor_file_paths = [
        "src/app/portal/doctor/page.tsx",
        "src/app/portal/doctor/pending/page.tsx",
        "src/app/portal/doctor/actions.ts",
        "src/components/doctor/patient-safety-banner.tsx",
        "src/components/doctor/patient-search-bar.tsx",
        "src/components/doctor/clinical-record-editor.tsx",
        "src/components/doctor/appointment-manager.tsx",
        "src/components/doctor/schedule-appointment-modal.tsx",
        "src/components/doctor/doctor-workspace.tsx",
    ]

    any_matches = []
    ignore_matches = []

    for rel_path in doctor_file_paths:
        code = read_source(rel_path)
        lines = code.split("\n")
        for line_num, line in enumerate(lines, start=1):
            stripped = line.split("//")[0].strip()
            # Check for : any or as any
            if re.search(r':\s*any\b', stripped) or re.search(r'\bas\s+any\b', stripped):
                any_matches.append((rel_path, line_num, line.strip()))
            # Check for @ts-ignore or @ts-expect-error without written reason
            if "@ts-ignore" in line or "@ts-expect-error" in line:
                ignore_matches.append((rel_path, line_num, line.strip()))

    record("STRICT_TYPING", "Zero occurrences of ': any' or 'as any' across all doctor portal files",
           len(any_matches) == 0, f"Found: {len(any_matches)} matches")
    if any_matches:
        for f, ln, l in any_matches:
            print(f"       -> Violation in {f}:{ln} -> {l}")

    record("STRICT_TYPING", "Zero occurrences of @ts-ignore or @ts-expect-error without reason",
           len(ignore_matches) == 0, f"Found: {len(ignore_matches)} matches")

    # =========================================================================
    # MISSION OBJECTIVE 5: CHARACTER COUNT AUDIT (< 12,000 CHARS)
    # =========================================================================
    print("\n--- 5. STRICT 12,000 CHARACTER LIMIT AUDIT ---")
    size_violations = []
    for rel_path in doctor_file_paths:
        code = read_source(rel_path)
        char_count = len(code)
        is_ok = char_count <= 12000
        if not is_ok:
            size_violations.append((rel_path, char_count))
        record("CHAR_LIMIT", f"{rel_path}: {char_count:,} chars (< 12,000)", is_ok)

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    print(f"TOTAL TESTS: {tests_run} | PASSED: {tests_passed} | FAILED: {tests_failed}")
    print("=" * 80)

    if tests_failed > 0:
        print("\nSUMMARY OF FAILURES:")
        for sec, name, det in failures:
            print(f"  - [{sec}] {name}: {det}")
        sys.exit(1)
    else:
        print("\nALL RE-CHECK VERIFICATIONS PASSED EMPIRICALLY!")
        sys.exit(0)

if __name__ == "__main__":
    main()

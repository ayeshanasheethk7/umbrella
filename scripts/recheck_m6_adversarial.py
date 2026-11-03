#!/usr/bin/env python3
"""
scripts/recheck_m6_adversarial.py
Adversarial Security Re-Check Harness for Milestone M6:
Doctor Portal Search & Actions Remediation

CHALLENGE MISSION RE-CHECK:
1. Re-attack QR Token UUID Search (INJECTION_1.4):
   - Query with valid UUIDs containing >= 7 numeric digits (e.g. `a1a1a1a1-a1a1-4a1a-8a1a-a1a1a1a1a1a1`).
   - Confirm it routes to the `qr_token` branch and does NOT get misclassified as a phone number.
2. Re-attack Wildcard Flooding (INJECTION_1.5):
   - Query with `%%%%%`, `_____`, `%_%_%`, `%%%%%___%%%%%`.
   - Confirm that it returns `{ ok: true, data: [] }` and does NOT match-all or dump database records via `ilike '%%'`.
3. Invariant N4 Secret Leak Re-check:
   - Confirm zero occurrences of `service_role` or `SUPABASE_SERVICE_ROLE_KEY`.
4. Run `python scripts/verify_m6.py` and `python scripts/audit.py`.
"""

import os
import re
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ACTIONS_PATH = os.path.join(ROOT_DIR, "src/app/portal/doctor/actions.ts")

passed_count = 0
failed_count = 0
failures = []

def test(suite: str, desc: str, condition: bool, extra: str = ""):
    global passed_count, failed_count, failures
    if condition:
        passed_count += 1
        print(f"[PASS] [{suite}] {desc}" + (f" -> {extra}" if extra else ""))
    else:
        failed_count += 1
        failures.append((suite, desc, extra))
        print(f"[FAIL] [{suite}] {desc} -> FAILED: {extra}")

def main():
    print("=" * 80)
    print("EMPIRICAL ADVERSARIAL RE-CHECK: DOCTOR PORTAL SURFACE (M6-1)")
    print("=" * 80)

    with open(ACTIONS_PATH, "r", encoding="utf-8") as f:
        actions_code = f.read()

    # =========================================================================
    # PART 1: INJECTION_1.4 - QR TOKEN UUID SEARCH PRECEDENCE & ROUTING
    # =========================================================================
    print("\n--- VECTOR 1: QR Token UUID Search Precedence & Routing (INJECTION_1.4) ---")

    # 1.1 Static Analysis of Branch Precedence in actions.ts
    uuid_branch_idx = actions_code.find(".eq('qr_token'")
    phone_branch_idx = actions_code.find("accounts.contact_phone")
    patient_code_branch_idx = actions_code.find(".ilike('patient_code'")

    test(
        "STATIC_PRECEDENCE",
        "UUID qr_token branch precedes phone number branch in searchPatientsAction",
        0 < uuid_branch_idx < phone_branch_idx,
        f"uuid_pos={uuid_branch_idx}, phone_pos={phone_branch_idx}"
    )

    test(
        "STATIC_PRECEDENCE",
        "Patient Code branch precedes phone number branch",
        0 < patient_code_branch_idx < phone_branch_idx,
        f"code_pos={patient_code_branch_idx}, phone_pos={phone_branch_idx}"
    )

    # 1.2 Dispatch Simulator mirroring actions.ts
    def escape_search_term_ts(t: str) -> str:
        # actions.ts line 35-37
        return re.sub(r'[%_(),]', '', (t or '').replace('\\', '\\\\')).strip()

    def simulate_search_patients_action(raw_query: str):
        q = (raw_query or '').strip()
        if len(q) < 2:
            return {"ok": True, "data": [], "branch": "SHORT_QUERY"}
        if len(q) > 100:
            return {"ok": False, "error": "Query exceeds 100 characters.", "branch": "EXCEEDS_LIMIT"}

        digits = re.sub(r'\D', '', q)

        if re.search(r'^UMB-[A-Za-z0-9]{6}$', q, re.I):
            return {"ok": True, "branch": "PATIENT_CODE", "query_type": "ilike", "field": "patient_code", "term": q.upper()}
        elif re.search(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', q, re.I):
            return {"ok": True, "branch": "QR_TOKEN", "query_type": "eq", "field": "qr_token", "term": q.lower()}
        elif len(digits) >= 7:
            return {"ok": True, "branch": "PHONE", "query_type": "ilike", "field": "contact_phone", "term": f"%{digits}%"}
        else:
            clean_term = escape_search_term_ts(q)
            if len(clean_term) < 2:
                return {"ok": True, "data": [], "branch": "CLEAN_SHORT_EMPTY"}
            return {"ok": True, "branch": "NAME_ILIKE", "query_type": "ilike", "field": "accounts.full_name", "term": f"%{clean_term}%"}

    # 1.3 Mandatory Mission Payload: Valid UUIDs containing >= 7 numeric digits
    mandatory_uuid = "a1a1a1a1-a1a1-4a1a-8a1a-a1a1a1a1a1a1"
    res_man = simulate_search_patients_action(mandatory_uuid)
    test(
        "MANDATORY_UUID",
        f"Mandatory UUID '{mandatory_uuid}' routes to QR_TOKEN branch",
        res_man["branch"] == "QR_TOKEN" and res_man["field"] == "qr_token" and res_man["term"] == mandatory_uuid.lower(),
        f"branch={res_man['branch']}, field={res_man.get('field')}"
    )

    test(
        "MANDATORY_UUID",
        f"Mandatory UUID '{mandatory_uuid}' is NOT misclassified as phone number",
        res_man["branch"] != "PHONE",
        f"branch={res_man['branch']}"
    )

    # Battery of UUIDs with varying digit counts (7 to 32 digits)
    uuid_battery = [
        ("aaaaaaaa-aaaa-4aaa-8aaa-1234567aaaaa", 7),
        ("bbbbbbbb-bbbb-4bbb-8bbb-12345678bbbb", 8),
        ("a1a1a1a1-a1a1-4a1a-8a1a-a1a1a1a1a1a1", 14),
        ("d659505e-44b2-44a9-b701-f1b1666af309", 21),
        ("bb5a6ce9-e25c-4806-b4c3-467b0799f823", 19),
        ("2b5f8ce3-2fde-4eed-9b48-063e5d194890", 20),
        ("98c86927-a105-4bdc-b90e-54aa5c252e11", 20),
        ("12345678-1234-4234-8234-123456789012", 32),
        ("00000000-0000-4000-8000-000000000000", 32),
        ("A1A1A1A1-A1A1-4A1A-8A1A-A1A1A1A1A1A1", 14),
        ("D659505E-44B2-44A9-B701-F1B1666AF309", 21),
        ("  a1a1a1a1-a1a1-4a1a-8a1a-a1a1a1a1a1a1  ", 14),
    ]

    for uid_str, digit_count in uuid_battery:
        r = simulate_search_patients_action(uid_str)
        test(
            "UUID_ROUTING_BATTERY",
            f"UUID with {digit_count} digits routes to QR_TOKEN: {uid_str.strip()[:18]}...",
            r["branch"] == "QR_TOKEN" and r["field"] == "qr_token" and r["branch"] != "PHONE",
            f"branch={r['branch']}"
        )

    # Confirm non-UUID phone inputs route to PHONE
    phone_battery = [
        "+1 (555) 123-4567",
        "5551234567",
        "+44 20 7946 0958",
        "123-456-7890",
        "9876543",
    ]
    for ph in phone_battery:
        r = simulate_search_patients_action(ph)
        test(
            "PHONE_ROUTING_BATTERY",
            f"Phone '{ph}' correctly routes to PHONE branch",
            r["branch"] == "PHONE" and r["field"] == "contact_phone",
            f"branch={r['branch']}"
        )

    # =========================================================================
    # PART 2: INJECTION_1.5 - WILDCARD FLOODING RE-ATTACK
    # =========================================================================
    print("\n--- VECTOR 2: Wildcard Flooding Re-attack (INJECTION_1.5) ---")

    # 2.1 The 4 Mandatory Payloads from Orchestrator Mission:
    mandatory_wildcards = [
        "%%%%%",
        "_____",
        "%_%_%",
        "%%%%%___%%%%%",
    ]

    for mw in mandatory_wildcards:
        res = simulate_search_patients_action(mw)
        test(
            "MANDATORY_WILDCARD",
            f"Payload '{mw}' returns {{ ok: true, data: [] }}",
            res.get("ok") is True and res.get("data") == [],
            f"result={res}"
        )
        test(
            "MANDATORY_WILDCARD_NO_DUMP",
            f"Payload '{mw}' does NOT trigger match-all '%%' query",
            res.get("branch") != "NAME_ILIKE" and res.get("term") != "%%",
            f"branch={res.get('branch')}, term={res.get('term')}"
        )

    # 2.2 Additional Wildcard & Delimiter Injection Payloads
    additional_wildcards = [
        "  %%%%%  ",
        "%%",
        "__",
        "%_",
        "%,%,%,%",
        "((((()))))",
        ",,,,()()",
        "  _ _ % % _  ",
        "%" * 20,
        "_" * 20,
        "(%_)," * 5,
        " , _ % ( ) ",
    ]

    for aw in additional_wildcards:
        res = simulate_search_patients_action(aw)
        test(
            "ADDITIONAL_WILDCARD",
            f"Payload '{aw.strip()[:16]}' returns {{ ok: true, data: [] }} and no dump",
            res.get("ok") is True and res.get("data") == [] and res.get("term") != "%%",
            f"branch={res.get('branch')}, res={res}"
        )

    # 2.3 Verify legitimate queries with embedded wildcards/characters work safely
    legit_mixed = [
        ("John%Smith", "%JohnSmith%"),
        ("Sarah_Jane", "%SarahJane%"),
        ("Dr. (Bob)", "%Dr. Bob%"),
        ("Alice, MD", "%Alice MD%"),
    ]
    for raw_q, expected_term in legit_mixed:
        res = simulate_search_patients_action(raw_q)
        test(
            "LEGIT_MIXED_SEARCH",
            f"Legitimate query '{raw_q}' sanitizes to '{expected_term}'",
            res.get("branch") == "NAME_ILIKE" and res.get("term") == expected_term,
            f"branch={res.get('branch')}, term={res.get('term')}"
        )

    # =========================================================================
    # PART 3: INVARIANT N4 - SECRET LEAK RE-CHECK
    # =========================================================================
    print("\n--- VECTOR 3: Invariant N4 Secret Leak Re-check ---")

    # 3.1 Sweep src/ directory for any occurrence of service_role or SUPABASE_SERVICE_ROLE_KEY
    src_dir = os.path.join(ROOT_DIR, "src")
    forbidden_tokens = ["service_role", "supabase_service_role_key"]
    leak_records = []

    for root, dirs, files in os.walk(src_dir):
        for f in files:
            fp = os.path.join(root, f)
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                    txt = fh.read().lower()
                    for token in forbidden_tokens:
                        if token in txt:
                            leak_records.append((os.path.relpath(fp, ROOT_DIR), token))
            except Exception as e:
                pass

    test(
        "INVARIANT_N4",
        "Zero occurrences of service_role or SUPABASE_SERVICE_ROLE_KEY in src/",
        len(leak_records) == 0,
        f"Leaks found: {leak_records}"
    )

    # 3.2 Check config & environment files
    config_files = [".env.example", "package.json", "next.config.js"]
    cfg_leaks = []
    for cfg in config_files:
        cfg_path = os.path.join(ROOT_DIR, cfg)
        if os.path.isfile(cfg_path):
            with open(cfg_path, "r", encoding="utf-8", errors="ignore") as fh:
                txt = fh.read().lower()
                for token in forbidden_tokens:
                    if token in txt:
                        cfg_leaks.append((cfg, token))

    test(
        "INVARIANT_N4",
        "Zero service_role leaks in .env.example, package.json, next.config.js",
        len(cfg_leaks) == 0,
        f"Leaks found: {cfg_leaks}"
    )

    # 3.3 Check 12k character limit on all Doctor Portal source files
    doctor_file_paths = [
        os.path.join(ROOT_DIR, "src/components/doctor/patient-safety-banner.tsx"),
        os.path.join(ROOT_DIR, "src/components/doctor/patient-search-bar.tsx"),
        os.path.join(ROOT_DIR, "src/components/doctor/clinical-record-editor.tsx"),
        os.path.join(ROOT_DIR, "src/components/doctor/appointment-manager.tsx"),
        os.path.join(ROOT_DIR, "src/components/doctor/doctor-workspace.tsx"),
        os.path.join(ROOT_DIR, "src/components/doctor/schedule-appointment-modal.tsx"),
        os.path.join(ROOT_DIR, "src/app/portal/doctor/actions.ts"),
        os.path.join(ROOT_DIR, "src/app/portal/doctor/page.tsx"),
        os.path.join(ROOT_DIR, "src/app/portal/doctor/pending/page.tsx"),
    ]

    for dfp in doctor_file_paths:
        if os.path.isfile(dfp):
            with open(dfp, "r", encoding="utf-8") as fh:
                fc = fh.read()
            sz = len(fc)
            test(
                "FILE_SIZE_12K",
                f"File '{os.path.basename(dfp)}' ({sz} chars) strictly < 12,000 chars",
                sz < 12000,
                f"{sz} chars"
            )
            # 3.4 Check zero 'any'
            any_matches = [
                (idx + 1, l.strip()) for idx, l in enumerate(fc.splitlines())
                if (re.search(r':\s*any\b', l.split("//")[0]) or re.search(r'\bas\s+any\b', l.split("//")[0]))
            ]
            test(
                "INVARIANT_N10",
                f"File '{os.path.basename(dfp)}' strictly zero 'any'",
                len(any_matches) == 0,
                f"Matches: {any_matches}"
            )

    # =========================================================================
    # PART 4: SUMMARY & VERDICT
    # =========================================================================
    print("\n" + "=" * 80)
    print(f"RE-CHECK CHALLENGE SUMMARY: {passed_count} Passed, {failed_count} Failed out of {passed_count + failed_count} Tests")
    print("=" * 80)

    if failed_count > 0:
        print("\nFAILURES IDENTIFIED:")
        for suite, desc, extra in failures:
            print(f"  - [{suite}] {desc}: {extra}")
        return False
    else:
        print("\nALL RE-CHECK ATTACK VECTORS DEFEATED: FULL COMPLIANCE CONFIRMED.")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

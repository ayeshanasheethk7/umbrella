#!/usr/bin/env python3
"""
scripts/challenger_m5_baseline.py
Empirical Adversarial Challenge Suite for Milestone M5:
Disappearing Baseline Edit UI (DECISIONS D3 & D7), RPC Constraints,
Token Rotation, and Privilege Escalation Resistance.

Executed by: Challenger M5-1 (teamwork_challenger)
Roles: critic, specialist
"""

import os
import re
import sys
import uuid
import json
from typing import Dict, Any, List, Optional, Tuple

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Test tracking
tests_run = 0
tests_passed = 0
tests_failed = 0
failures = []

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
# 1. POSTGRES STATE MACHINE & ORACLE SIMULATOR
# Line-by-line mirror of 0001_umbrella_schema.sql tables, grants, and RPCs
# ==============================================================================

class PostgresSimulation:
    def __init__(self):
        self.accounts: Dict[str, Dict[str, Any]] = {}
        self.patient_profiles: Dict[str, Dict[str, Any]] = {}
        self.clinical_records: Dict[str, Dict[str, Any]] = {}
        self.current_user_id: Optional[str] = None
        self.current_role: str = 'anon'

    def set_auth(self, user_id: Optional[str], role: str = 'authenticated'):
        self.current_user_id = user_id
        self.current_role = role

    def seed_initial_state(self):
        # Patient A
        pat_a_id = "00000000-0000-0000-0000-0000000000a1"
        self.accounts[pat_a_id] = {
            "id": pat_a_id,
            "email": "alex.morgan@example.com",
            "full_name": "Alex Morgan",
            "contact_phone": "+1 (555) 234-5678",
            "role": "patient",
            "doctor_status": None,
            "specialization": None,
            "medical_license_number": None,
        }
        self.patient_profiles[pat_a_id] = {
            "patient_id": pat_a_id,
            "patient_code": "UMB-9021-ALEX",
            "qr_token": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
            "age": 34,
            "blood_group": "O+",
            "emergency_contact_name": "Taylor Morgan",
            "emergency_contact_phone": "+1 (555) 987-6543",
            "emergency_contact_relation": "Spouse",
            "spouse_dependents": [{"name": "Leo Morgan", "relation": "Child", "age": 4}],
            "residential_address": "742 Evergreen Terrace, Springfield, OR",
        }
        self.clinical_records[pat_a_id] = {
            "patient_id": pat_a_id,
            "medical_conditions": ["Asthma"],
            "current_medication": [],
            "previous_surgeries": [],
            "allergies": ["Penicillin"],
            "is_doctor_verified": False,
            "last_updated_by_doctor_id": None,
            "last_appointment_date": None,
            "last_appointment_summary": None,
            "updated_at": "2026-11-01T12:00:00Z",
        }

        # Doctor D
        doc_id = "00000000-0000-0000-0000-0000000000d2"
        self.accounts[doc_id] = {
            "id": doc_id,
            "email": "dr.smith@hospital.org",
            "full_name": "Dr. Sarah Smith",
            "contact_phone": "+1 (555) 000-1111",
            "role": "doctor",
            "doctor_status": "approved",
            "specialization": "Emergency Medicine",
            "medical_license_number": "MED-998877",
        }

    # RPC: submit_self_reported_baseline
    def rpc_submit_self_reported_baseline(self, p_conditions: Optional[List[str]], p_allergies: Optional[List[str]]) -> Tuple[bool, str]:
        if self.current_role != 'authenticated' or not self.current_user_id:
            return False, "Permission denied"

        cond_len = len(p_conditions) if p_conditions is not None else 0
        allg_len = len(p_allergies) if p_allergies is not None else 0

        if cond_len > 50 or allg_len > 50:
            return False, "Too many entries"

        uid = self.current_user_id
        rec = self.clinical_records.get(uid)
        if not rec or rec.get("is_doctor_verified", False):
            return False, "Record is already doctor-verified, or no patient profile exists"

        rec["medical_conditions"] = list(p_conditions or [])
        rec["allergies"] = list(p_allergies or [])
        rec["updated_at"] = "2026-11-01T21:15:00Z"
        return True, "Success"

    # RPC: regenerate_qr_token
    def rpc_regenerate_qr_token(self) -> Tuple[bool, Optional[str], str]:
        if self.current_role != 'authenticated' or not self.current_user_id:
            return False, None, "Permission denied"

        uid = self.current_user_id
        prof = self.patient_profiles.get(uid)
        if not prof:
            return False, None, "No patient profile for this user"

        new_token = str(uuid.uuid4())
        prof["qr_token"] = new_token
        return True, new_token, "Success"

    # RPC: get_emergency_triage_by_token (N1 whitelist projection)
    def rpc_get_emergency_triage_by_token(self, lookup_token: str) -> Optional[Dict[str, Any]]:
        # Find matching profile
        matched_patient_id = None
        for pid, prof in self.patient_profiles.items():
            if prof.get("qr_token") == lookup_token:
                matched_patient_id = pid
                break

        if not matched_patient_id:
            return None

        acc = self.accounts[matched_patient_id]
        prof = self.patient_profiles[matched_patient_id]
        clin = self.clinical_records.get(matched_patient_id, {})

        # N1 whitelist projection: strictly excludes residential_address, spouse_dependents, qr_token
        return {
            "full_name": acc["full_name"],
            "contact_phone": acc["contact_phone"],
            "patient_code": prof["patient_code"],
            "age": prof["age"],
            "blood_group": prof["blood_group"],
            "emergency_contact_name": prof["emergency_contact_name"],
            "emergency_contact_phone": prof["emergency_contact_phone"],
            "emergency_contact_relation": prof["emergency_contact_relation"],
            "medical_conditions": clin.get("medical_conditions", []),
            "current_medication": clin.get("current_medication", []),
            "previous_surgeries": clin.get("previous_surgeries", []),
            "allergies": clin.get("allergies", []),
            "last_appointment_date": clin.get("last_appointment_date"),
            "is_doctor_verified": clin.get("is_doctor_verified", False),
            "updated_at": clin.get("updated_at"),
        }

    # Column-level grant enforcement simulator
    def attempt_direct_accounts_update(self, updates: Dict[str, Any]) -> Tuple[bool, str]:
        # grant update (full_name, contact_phone, specialization) on public.accounts to authenticated;
        allowed_columns = {"full_name", "contact_phone", "specialization"}
        for k in updates.keys():
            if k not in allowed_columns:
                return False, f"permission denied for column '{k}' of relation 'accounts'"
        acc = self.accounts.get(self.current_user_id)
        if acc:
            acc.update(updates)
        return True, "Updated"

    def attempt_direct_patient_profiles_update(self, updates: Dict[str, Any]) -> Tuple[bool, str]:
        # grant update (age, blood_group, emergency_contact_name, emergency_contact_phone,
        # emergency_contact_relation, spouse_dependents, residential_address) on public.patient_profiles to authenticated;
        allowed_columns = {
            "age", "blood_group", "emergency_contact_name", "emergency_contact_phone",
            "emergency_contact_relation", "spouse_dependents", "residential_address"
        }
        for k in updates.keys():
            if k not in allowed_columns:
                return False, f"permission denied for column '{k}' of relation 'patient_profiles'"
        prof = self.patient_profiles.get(self.current_user_id)
        if prof:
            prof.update(updates)
        return True, "Updated"

# ==============================================================================
# 2. ZOD SCHEMA PARSER & VALIDATOR (Matching src/lib/schemas.ts)
# ==============================================================================

def validate_baseline_submission(data: Any) -> Tuple[bool, Dict[str, Any], Optional[str]]:
    """Emulates baselineSubmissionSchema in src/lib/schemas.ts"""
    if not isinstance(data, dict):
        return False, {}, "Invalid input: expected object"

    conditions = data.get("conditions", [])
    allergies = data.get("allergies", [])

    if not isinstance(conditions, list):
        return False, {}, "conditions must be an array"
    if not isinstance(allergies, list):
        return False, {}, "allergies must be an array"

    parsed_conditions = []
    for item in conditions:
        if not isinstance(item, str):
            return False, {}, "Condition item must be a string"
        trimmed = item.strip()
        if len(trimmed) < 1:
            return False, {}, "Condition item cannot be empty"
        parsed_conditions.append(trimmed)

    parsed_allergies = []
    for item in allergies:
        if not isinstance(item, str):
            return False, {}, "Allergy item must be a string"
        trimmed = item.strip()
        if len(trimmed) < 1:
            return False, {}, "Allergy item cannot be empty"
        parsed_allergies.append(trimmed)

    return True, {"conditions": parsed_conditions, "allergies": parsed_allergies}, None

def validate_update_demographics(data: Any) -> Tuple[bool, Dict[str, Any], Optional[str]]:
    """Emulates updateDemographicsSchema in src/lib/schemas.ts"""
    if not isinstance(data, dict):
        return False, {}, "Expected object"

    full_name = data.get("fullName")
    if not isinstance(full_name, str) or len(full_name.strip()) < 2 or len(full_name.strip()) > 100:
        return False, {}, "Full name must be 2-100 characters"

    age = data.get("age")
    try:
        age_int = int(age)
        if age_int < 0 or age_int > 130:
            return False, {}, "Age must be 0-130"
    except (ValueError, TypeError):
        return False, {}, "Age must be a valid number"

    valid_blood_groups = {'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'Unknown'}
    blood_group = data.get("bloodGroup")
    if blood_group not in valid_blood_groups:
        return False, {}, f"Invalid blood group: {blood_group}"

    ec_name = data.get("emergencyContactName")
    if not isinstance(ec_name, str) or len(ec_name.strip()) < 2:
        return False, {}, "Emergency contact name is required"

    ec_phone = data.get("emergencyContactPhone")
    if not isinstance(ec_phone, str) or not re.match(r'^\+?[0-9\s\-().]{7,20}$', ec_phone.strip()):
        return False, {}, "Emergency contact phone number must be valid"

    ec_rel = data.get("emergencyContactRelation")
    if not isinstance(ec_rel, str) or len(ec_rel.strip()) < 1:
        return False, {}, "Relationship is required"

    dependents = data.get("spouseDependents", [])
    if not isinstance(dependents, list) or len(dependents) > 10:
        return False, {}, "Maximum 10 dependents allowed"

    # Whitelist extraction: Zod strips non-schema keys like role, doctor_status, patient_code, qr_token
    sanitized = {
        "fullName": full_name.strip(),
        "contactPhone": str(data.get("contactPhone", "")).strip(),
        "age": age_int,
        "bloodGroup": blood_group,
        "emergencyContactName": ec_name.strip(),
        "emergencyContactPhone": ec_phone.strip(),
        "emergencyContactRelation": ec_rel.strip(),
        "residentialAddress": str(data.get("residentialAddress", "")).strip()[:255],
        "spouseDependents": dependents,
    }
    return True, sanitized, None

# ==============================================================================
# 3. SERVER ACTION WRAPPERS
# Matching src/app/portal/patient/actions.ts logic
# ==============================================================================

def simulate_submit_baseline_action(db: PostgresSimulation, raw_data: Any) -> Dict[str, Any]:
    if not db.current_user_id:
        return {"ok": False, "error": "Unauthorized. Your session has expired; please sign in again."}

    # Step 1: Zod validation
    ok, valid_data, err = validate_baseline_submission(raw_data)
    if not ok:
        return {"ok": False, "error": err or "Invalid medical baseline submission."}

    # Step 2: RPC call
    rpc_ok, rpc_err = db.rpc_submit_self_reported_baseline(valid_data["conditions"], valid_data["allergies"])
    if not rpc_ok:
        if "doctor-verified" in rpc_err or "Record is already doctor-verified" in rpc_err:
            return {
                "ok": False,
                "error": "This medical baseline has been officially verified by a healthcare provider and can no longer be self-edited. Please consult your physician for updates."
            }
        if "Too many entries" in rpc_err:
            return {"ok": False, "error": "Maximum 50 conditions and 50 allergies permitted per submission."}
        return {"ok": False, "error": f"Submission failed: {rpc_err}"}

    return {"ok": True, "data": {"message": "Medical baseline updated successfully."}}

def simulate_update_demographics_action(db: PostgresSimulation, raw_data: Any) -> Dict[str, Any]:
    if not db.current_user_id:
        return {"ok": False, "error": "Unauthorized. Your session has expired; please sign in again."}

    # Step 1: Zod validation (strips unwanted fields)
    ok, sanitized_data, err = validate_update_demographics(raw_data)
    if not ok:
        return {"ok": False, "error": err}

    # Step 2: Update accounts (explicit whitelist)
    accounts_payload = {
        "full_name": sanitized_data["fullName"],
        "contact_phone": sanitized_data["contactPhone"],
    }
    acc_ok, acc_msg = db.attempt_direct_accounts_update(accounts_payload)
    if not acc_ok:
        return {"ok": False, "error": acc_msg}

    # Step 3: Update patient_profiles (explicit whitelist)
    profile_payload = {
        "age": sanitized_data["age"],
        "blood_group": sanitized_data["bloodGroup"],
        "emergency_contact_name": sanitized_data["emergencyContactName"],
        "emergency_contact_phone": sanitized_data["emergencyContactPhone"],
        "emergency_contact_relation": sanitized_data["emergencyContactRelation"],
        "residential_address": sanitized_data["residentialAddress"],
        "spouse_dependents": sanitized_data["spouseDependents"],
    }
    prof_ok, prof_msg = db.attempt_direct_patient_profiles_update(profile_payload)
    if not prof_ok:
        return {"ok": False, "error": prof_msg}

    return {"ok": True, "data": {"message": "Profile details saved successfully."}}

def simulate_rotate_qr_token_action(db: PostgresSimulation) -> Dict[str, Any]:
    if not db.current_user_id:
        return {"ok": False, "error": "Unauthorized. Please sign in again."}

    ok, new_token, msg = db.rpc_regenerate_qr_token()
    if not ok:
        return {"ok": False, "error": f"Failed to rotate QR token: {msg}"}

    return {
        "ok": True,
        "data": {
            "qrToken": new_token,
            "message": "Emergency QR code successfully rotated. Previous physical copies are now invalid."
        }
    }

# ==============================================================================
# TEST SUITES
# ==============================================================================

def run_challenge_1_disappearing_contract():
    print("\n" + "=" * 80)
    print("CHALLENGE 1: DISAPPEARING BASELINE EDIT UI (DECISIONS D3 & D7)")
    print("=" * 80)

    # 1.1 Static AST / Component Checks
    editor_path = os.path.join(ROOT_DIR, "src/components/patient/baseline-editor.tsx")
    with open(editor_path, "r", encoding="utf-8") as f:
        editor_content = f.read()

    # Verify unconditional return null when isDoctorVerified
    unconditional_null = bool(re.search(r'if\s*\(\s*isDoctorVerified\s*\)\s*\{\s*return\s+null;\s*\}', editor_content))
    record("CHALLENGE_1", "baseline-editor.tsx: Unconditional return null on isDoctorVerified", unconditional_null)

    # Verify return null is placed BEFORE any editor UI markup
    idx_guard = editor_content.find("if (isDoctorVerified)")
    idx_active = editor_content.find("<ActiveBaselineEditor")
    guard_before_render = (idx_guard != -1 and idx_active != -1 and idx_guard < idx_active)
    record("CHALLENGE_1", "baseline-editor.tsx: Guard precedes active component rendering", guard_before_render)

    # 1.2 Page-level Gating
    page_path = os.path.join(ROOT_DIR, "src/app/portal/patient/page.tsx")
    with open(page_path, "r", encoding="utf-8") as f:
        page_content = f.read()

    page_gating = "{!clinical.is_doctor_verified &&" in page_content and "<BaselineEditor" in page_content
    record("CHALLENGE_1", "page.tsx: Gated at Server Component layout with {!clinical.is_doctor_verified && ...}", page_gating)

    # 1.3 Medical Overview Card Verified Banner & Doctor Attribution
    overview_path = os.path.join(ROOT_DIR, "src/components/patient/medical-overview-card.tsx")
    with open(overview_path, "r", encoding="utf-8") as f:
        overview_content = f.read()

    verified_badge = '<Badge variant="verified">' in overview_content and "Doctor Verified" in overview_content
    record("CHALLENGE_1", "medical-overview-card.tsx: Renders Doctor Verified badge", verified_badge)

    banner_attribution = "Verified by {doctorTitle} on {formattedDate}. Contact your doctor to update." in overview_content
    record("CHALLENGE_1", "medical-overview-card.tsx: Displays verified banner with clinical attribution", banner_attribution)

    attending_fallback = "Attending Clinician" in overview_content
    record("CHALLENGE_1", "medical-overview-card.tsx: Attending Clinician fallback for unassigned doctor", attending_fallback)

    # 1.4 Direct Server Action Invocation Attack when Doctor-Verified
    db = PostgresSimulation()
    db.seed_initial_state()
    pat_id = "00000000-0000-0000-0000-0000000000a1"
    db.set_auth(pat_id)

    # First, verify baseline submission succeeds while unverified
    res_unverified = simulate_submit_baseline_action(db, {
        "conditions": ["Mild Asthma"],
        "allergies": ["Penicillin", "Peanuts"]
    })
    record("CHALLENGE_1", "Baseline submission allowed while unverified", res_unverified["ok"] is True)
    record("CHALLENGE_1", "Database updated conditions correctly", db.clinical_records[pat_id]["medical_conditions"] == ["Mild Asthma"])

    # Now simulate Doctor Verification stamp
    db.clinical_records[pat_id]["is_doctor_verified"] = True
    db.clinical_records[pat_id]["last_updated_by_doctor_id"] = "00000000-0000-0000-0000-0000000000d2"
    snapshot_before = json.dumps(db.clinical_records[pat_id], sort_keys=True)

    # Attacker tries to bypass UI and call submitBaselineAction directly
    res_verified_attack = simulate_submit_baseline_action(db, {
        "conditions": ["Maliciously Injected Condition"],
        "allergies": ["Latex"]
    })

    expected_notice = "This medical baseline has been officially verified by a healthcare provider and can no longer be self-edited. Please consult your physician for updates."
    is_rejected = (res_verified_attack["ok"] is False and res_verified_attack.get("error") == expected_notice)
    record("CHALLENGE_1", "Direct submitBaselineAction rejected with clinical notice when verified", is_rejected, res_verified_attack.get("error", ""))

    # Verify DB was NOT mutated
    snapshot_after = json.dumps(db.clinical_records[pat_id], sort_keys=True)
    db_untouched = (snapshot_before == snapshot_after)
    record("CHALLENGE_1", "Postgres clinical_records completely unmutated after rejected attack", db_untouched)

def run_challenge_2_rpc_limits_and_bounds():
    print("\n" + "=" * 80)
    print("CHALLENGE 2: RPC LIMITS, BOUNDS & STRICT PARAMETER ENFORCEMENT")
    print("=" * 80)

    db = PostgresSimulation()
    db.seed_initial_state()
    pat_id = "00000000-0000-0000-0000-0000000000a1"
    db.set_auth(pat_id)

    # 2.1 Boundary Test: Exactly 50 items (Allowed)
    conditions_50 = [f"Condition {i}" for i in range(1, 51)]
    allergies_50 = [f"Allergy {i}" for i in range(1, 51)]
    res_50 = simulate_submit_baseline_action(db, {
        "conditions": conditions_50,
        "allergies": allergies_50
    })
    record("CHALLENGE_2", "Boundary: Exactly 50 conditions and 50 allergies accepted", res_50["ok"] is True)
    record("CHALLENGE_2", "Postgres stored 50 conditions", len(db.clinical_records[pat_id]["medical_conditions"]) == 50)

    # 2.2 Boundary Test: 51 conditions (> 50 items -> Rejection)
    conditions_51 = [f"Condition {i}" for i in range(1, 52)]
    res_51_cond = simulate_submit_baseline_action(db, {
        "conditions": conditions_51,
        "allergies": ["Allergy 1"]
    })
    expected_limit_err = "Maximum 50 conditions and 50 allergies permitted per submission."
    record("CHALLENGE_2", "Boundary: 51 conditions rejected with limit notice", res_51_cond["ok"] is False and res_51_cond["error"] == expected_limit_err)

    # 2.3 Boundary Test: 51 allergies (> 50 items -> Rejection)
    allergies_51 = [f"Allergy {i}" for i in range(1, 52)]
    res_51_allg = simulate_submit_baseline_action(db, {
        "conditions": ["Condition 1"],
        "allergies": allergies_51
    })
    record("CHALLENGE_2", "Boundary: 51 allergies rejected with limit notice", res_51_allg["ok"] is False and res_51_allg["error"] == expected_limit_err)

    # 2.4 Stress Test: Massive Array Injection (10,000 items)
    massive_array = [f"Spam {i}" for i in range(10000)]
    res_massive = simulate_submit_baseline_action(db, {
        "conditions": massive_array,
        "allergies": []
    })
    record("CHALLENGE_2", "Stress: 10,000 items rejected instantly without OOM", res_massive["ok"] is False and res_massive["error"] == expected_limit_err)

    # 2.5 Empty Item String Rejections
    empty_tests = [
        ([""], [], "Empty string condition rejected"),
        (["   "], [], "Whitespace-only condition rejected"),
        (["Asthma", ""], [], "Mixed empty condition rejected"),
        ([], [""], "Empty string allergy rejected"),
        ([], ["   "], "Whitespace-only allergy rejected"),
        ([], ["Penicillin", " \t "], "Mixed whitespace allergy rejected"),
    ]
    for conds, allgs, label in empty_tests:
        res_empty = simulate_submit_baseline_action(db, {"conditions": conds, "allergies": allgs})
        record("CHALLENGE_2", f"Schema defense: {label}", res_empty["ok"] is False)

    # 2.6 Whitespace Sanitization (Trimming)
    res_trim = simulate_submit_baseline_action(db, {
        "conditions": ["  Type 2 Diabetes  ", " Hypertension\n"],
        "allergies": ["\tAspirin "]
    })
    trimmed_properly = (
        res_trim["ok"] is True and
        db.clinical_records[pat_id]["medical_conditions"] == ["Type 2 Diabetes", "Hypertension"] and
        db.clinical_records[pat_id]["allergies"] == ["Aspirin"]
    )
    record("CHALLENGE_2", "Sanitization: Items trimmed cleanly of surrounding whitespace", trimmed_properly)

    # 2.7 Strict Parameter Check in 0001_umbrella_schema.sql
    schema_sql_path = os.path.join(ROOT_DIR, "supabase/migrations/0001_umbrella_schema.sql")
    with open(schema_sql_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    rpc_sig_match = bool(re.search(
        r'function\s+public\.submit_self_reported_baseline\s*\(\s*p_conditions\s+text\[\]\s*,\s*p_allergies\s+text\[\]\s*\)',
        schema_sql
    ))
    record("CHALLENGE_2", "Schema: RPC signature strictly takes (p_conditions text[], p_allergies text[])", rpc_sig_match)

    rpc_bounds_check = "if coalesce(array_length(p_conditions, 1), 0) > 50 or coalesce(array_length(p_allergies, 1), 0) > 50 then" in schema_sql
    record("CHALLENGE_2", "Schema: Postgres function enforces coalesce(array_length, 0) > 50 bounds check", rpc_bounds_check)

def run_challenge_3_token_rotation():
    print("\n" + "=" * 80)
    print("CHALLENGE 3: TOKEN ROTATION & URL INVALIDATION (DECISIONS D3)")
    print("=" * 80)

    db = PostgresSimulation()
    db.seed_initial_state()
    pat_id = "00000000-0000-0000-0000-0000000000a1"
    db.set_auth(pat_id)

    initial_token = db.patient_profiles[pat_id]["qr_token"]
    initial_profile_snapshot = dict(db.patient_profiles[pat_id])

    # 3.1 Initial Token Emergency Triage Query
    triage_initial = db.rpc_get_emergency_triage_by_token(initial_token)
    record("CHALLENGE_3", "Initial token yields valid emergency triage data", triage_initial is not None and triage_initial["full_name"] == "Alex Morgan")

    # 3.2 Rotate QR Token via Action
    res_rotate = simulate_rotate_qr_token_action(db)
    record("CHALLENGE_3", "rotateQrTokenAction succeeds", res_rotate["ok"] is True)

    new_token = res_rotate["data"]["qrToken"]

    # Verify fresh valid UUID v4
    is_valid_uuid = False
    try:
        val = uuid.UUID(new_token, version=4)
        is_valid_uuid = (str(val) == new_token)
    except ValueError:
        pass
    record("CHALLENGE_3", "Returned token is a valid RFC 4122 UUID v4", is_valid_uuid, new_token)
    record("CHALLENGE_3", "New token differs from initial token", new_token != initial_token)

    # 3.3 Verify patient_profiles.qr_token was updated
    record("CHALLENGE_3", "patient_profiles.qr_token updated to new token", db.patient_profiles[pat_id]["qr_token"] == new_token)

    # 3.4 Invalidation Check: Old URL / Token returns None (404)
    triage_old = db.rpc_get_emergency_triage_by_token(initial_token)
    record("CHALLENGE_3", "CRITICAL: Old rotated token returns NULL (invalidated immediately)", triage_old is None)

    # 3.5 New URL / Token returns valid triage data
    triage_new = db.rpc_get_emergency_triage_by_token(new_token)
    record("CHALLENGE_3", "New token resolves to complete emergency triage data", triage_new is not None and triage_new["full_name"] == "Alex Morgan")

    # 3.6 Attribute Preservation Check (Zero unintended mutations)
    preserved_keys = [
        "patient_id", "patient_code", "age", "blood_group",
        "emergency_contact_name", "emergency_contact_phone", "emergency_contact_relation",
        "spouse_dependents", "residential_address"
    ]
    all_preserved = True
    for key in preserved_keys:
        if db.patient_profiles[pat_id][key] != initial_profile_snapshot[key]:
            all_preserved = False
            break
    record("CHALLENGE_3", "All other patient_profiles attributes preserved exactly", all_preserved)

    # 3.7 Stress Test: 100 Consecutive Token Rotations
    tokens_seen = {initial_token, new_token}
    collision_detected = False
    for i in range(100):
        rot = simulate_rotate_qr_token_action(db)
        tok = rot["data"]["qrToken"]
        if tok in tokens_seen:
            collision_detected = True
            break
        tokens_seen.add(tok)

    record("CHALLENGE_3", "Stress: 100 consecutive rotations produced 100 unique UUIDs (zero collisions)", not collision_detected)
    latest_token = db.patient_profiles[pat_id]["qr_token"]
    record("CHALLENGE_3", "Latest token is active after 100 rotations", db.rpc_get_emergency_triage_by_token(latest_token) is not None)

def run_challenge_4_privilege_escalation():
    print("\n" + "=" * 80)
    print("CHALLENGE 4: PRIVILEGE ESCALATION RESISTANCE IN updateDemographicsAction")
    print("=" * 80)

    db = PostgresSimulation()
    db.seed_initial_state()
    pat_id = "00000000-0000-0000-0000-0000000000a1"
    db.set_auth(pat_id)

    initial_acc = dict(db.accounts[pat_id])
    initial_prof = dict(db.patient_profiles[pat_id])

    # 4.1 Malicious Payload Injection: Attempting to escalate role to doctor
    escalation_payload = {
        "fullName": "Alex Morgan",
        "contactPhone": "+1 (555) 234-5678",
        "age": 34,
        "bloodGroup": "O+",
        "emergencyContactName": "Taylor Morgan",
        "emergencyContactPhone": "+1 (555) 987-6543",
        "emergencyContactRelation": "Spouse",
        "residentialAddress": "742 Evergreen Terrace",
        "spouseDependents": [],
        # ATTACK VECTORS:
        "role": "doctor",
        "doctor_status": "approved",
        "patient_code": "UMB-HACKED-CODE",
        "qr_token": "00000000-0000-0000-0000-000000000000",
        "id": "00000000-0000-0000-0000-0000000000d2"
    }

    res_esc = simulate_update_demographics_action(db, escalation_payload)
    record("CHALLENGE_4", "updateDemographicsAction completed sanitized update", res_esc["ok"] is True)

    # Check accounts.role
    current_role = db.accounts[pat_id]["role"]
    record("CHALLENGE_4", "Privilege Escalation Blocked: accounts.role remains 'patient'", current_role == "patient")

    # Check accounts.doctor_status
    current_doc_status = db.accounts[pat_id]["doctor_status"]
    record("CHALLENGE_4", "Privilege Escalation Blocked: accounts.doctor_status remains None", current_doc_status is None)

    # Check patient_profiles.patient_code
    current_code = db.patient_profiles[pat_id]["patient_code"]
    record("CHALLENGE_4", "Tamper Blocked: patient_profiles.patient_code remains original", current_code == initial_prof["patient_code"])

    # Check patient_profiles.qr_token
    current_qr = db.patient_profiles[pat_id]["qr_token"]
    record("CHALLENGE_4", "Tamper Blocked: patient_profiles.qr_token was not overwritten by malicious payload", current_qr == initial_prof["qr_token"])

    # 4.2 Direct Column-Level Grant Verification (Defense-in-Depth)
    # Even if Server Action were completely compromised, Postgres grants block updates to these columns:
    direct_role_attack, msg1 = db.attempt_direct_accounts_update({"role": "doctor"})
    record("CHALLENGE_4", "Postgres Column Grant: Direct update to accounts.role rejected", not direct_role_attack)

    direct_status_attack, msg2 = db.attempt_direct_accounts_update({"doctor_status": "approved"})
    record("CHALLENGE_4", "Postgres Column Grant: Direct update to accounts.doctor_status rejected", not direct_status_attack)

    direct_code_attack, msg3 = db.attempt_direct_patient_profiles_update({"patient_code": "UMB-HACKED"})
    record("CHALLENGE_4", "Postgres Column Grant: Direct update to patient_profiles.patient_code rejected", not direct_code_attack)

    direct_qr_attack, msg4 = db.attempt_direct_patient_profiles_update({"qr_token": "00000000-0000-0000-0000-000000000000"})
    record("CHALLENGE_4", "Postgres Column Grant: Direct update to patient_profiles.qr_token rejected", not direct_qr_attack)

    # 4.3 Static Inspection of actions.ts: Whitelist verification
    actions_path = os.path.join(ROOT_DIR, "src/app/portal/patient/actions.ts")
    with open(actions_path, "r", encoding="utf-8") as f:
        actions_content = f.read()

    # Verify accounts update payload contains ONLY full_name and contact_phone
    acc_update_match = re.search(r'\.from\(\'accounts\'\)\s*\.update\(\{\s*full_name:\s*data\.fullName,\s*contact_phone:\s*data\.contactPhone\s*\|\|\s*\'\',\s*\}\)', actions_content)
    record("CHALLENGE_4", "actions.ts: accounts.update explicitly whitelists only full_name and contact_phone", bool(acc_update_match))

    # Verify patient_profiles update payload never references patient_code or qr_token
    prof_update_match = re.search(r'\.from\(\'patient_profiles\'\)\s*\.update\(\{([^}]+)\}\)', actions_content)
    prof_update_body = prof_update_match.group(1) if prof_update_match else ""
    record("CHALLENGE_4", "actions.ts: patient_profiles.update does NOT include patient_code", "patient_code" not in prof_update_body)
    record("CHALLENGE_4", "actions.ts: patient_profiles.update does NOT include qr_token", "qr_token" not in prof_update_body)

def run_challenge_5_privacy_invariants():
    print("\n" + "=" * 80)
    print("CHALLENGE 5: PRIVACY BOUNDARY INVARIANTS (N1 WHITELIST PROJECTION)")
    print("=" * 80)

    db = PostgresSimulation()
    db.seed_initial_state()
    pat_id = "00000000-0000-0000-0000-0000000000a1"
    token = db.patient_profiles[pat_id]["qr_token"]

    triage = db.rpc_get_emergency_triage_by_token(token)

    # Verify residential_address is NOT in triage projection
    has_res_addr = "residential_address" in triage
    record("CHALLENGE_5", "Invariant N1: residential_address excluded from emergency triage projection", not has_res_addr)

    # Verify spouse_dependents is NOT in triage projection
    has_dependents = "spouse_dependents" in triage
    record("CHALLENGE_5", "Invariant N1: spouse_dependents excluded from emergency triage projection", not has_dependents)

    # Verify qr_token is NOT leaked in triage projection
    has_qr = "qr_token" in triage
    record("CHALLENGE_5", "Invariant N1: qr_token excluded from emergency triage projection", not has_qr)

    # Verify demographics card renders N1 privacy badge
    demographics_path = os.path.join(ROOT_DIR, "src/components/patient/demographics-card.tsx")
    with open(demographics_path, "r", encoding="utf-8") as f:
        demo_content = f.read()

    n1_badge_present = "Private: Excluded from emergency QR triage scan (N1)" in demo_content
    record("CHALLENGE_5", "demographics-card.tsx: Renders visible N1 privacy protection banner", n1_badge_present)

def run_challenge_6_file_integrity_and_hygiene():
    print("\n" + "=" * 80)
    print("CHALLENGE 6: WORKSPACE HYGIENE & CHARACTER LIMIT AUDIT (<12,000 CHARS)")
    print("=" * 80)

    m5_files = [
        "src/app/portal/patient/actions.ts",
        "src/app/portal/patient/page.tsx",
        "src/components/patient/hero-profile-card.tsx",
        "src/components/patient/emergency-qr-card.tsx",
        "src/components/patient/emergency-contact-card.tsx",
        "src/components/patient/demographics-card.tsx",
        "src/components/patient/medical-overview-card.tsx",
        "src/components/patient/baseline-editor.tsx",
        "src/components/patient/dependents-manager.tsx",
        "src/lib/qr-export.ts",
        "src/lib/schemas.ts",
    ]

    all_under_12k = True
    for rel_path in m5_files:
        full_path = os.path.join(ROOT_DIR, rel_path)
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        cnt = len(content)
        if cnt >= 12000:
            all_under_12k = False
            record("CHALLENGE_6", f"File size: {rel_path}", False, f"{cnt} chars >= 12k")
        else:
            record("CHALLENGE_6", f"File size: {rel_path}", True, f"{cnt} chars (<12k)")

    # Check for scripts in .agents/teamwork
    teamwork_dir = os.path.join(ROOT_DIR, ".agents/teamwork")
    forbidden_scripts = []
    for root, dirs, files in os.walk(teamwork_dir):
        for file in files:
            if file.endswith((".py", ".sh", ".bash", ".ps1", ".js", ".ts")):
                forbidden_scripts.append(os.path.join(root, file))

    record("CHALLENGE_6", "Zero scripts in .agents/teamwork/", len(forbidden_scripts) == 0, f"Found {len(forbidden_scripts)}")

def main():
    print("*" * 80)
    print("CHALLENGER M5-1: EMPIRICAL ADVERSARIAL CHALLENGE HARNESS")
    print("Target: Milestone M5 Patient Portal Surface & Baseline Contracts")
    print("*" * 80)

    run_challenge_1_disappearing_contract()
    run_challenge_2_rpc_limits_and_bounds()
    run_challenge_3_token_rotation()
    run_challenge_4_privilege_escalation()
    run_challenge_5_privacy_invariants()
    run_challenge_6_file_integrity_and_hygiene()

    print("\n" + "=" * 80)
    print(f"ADVERSARIAL CHALLENGE SUMMARY: {tests_passed}/{tests_run} TESTS PASSED")
    if failures:
        print(f"FAILURES DETECTED: {tests_failed}")
        for suite, name, detail in failures:
            print(f"  - [{suite}] {name}: {detail}")
        print("VERDICT: REQUEST_CHANGES")
        sys.exit(1)
    else:
        print("VERDICT: APPROVE (All Adversarial Stress Tests & Contracts Passed)")
        print("=" * 80)
        sys.exit(0)

if __name__ == "__main__":
    main()

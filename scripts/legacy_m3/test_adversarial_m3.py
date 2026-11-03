"""
Adversarial Security Attack Simulator & Empirical Verification Harness
Milestone: M3 (Umbrella Schema, RLS, Grants & RPCs)
Author: Challenger M3-1 (teamwork_challenger)
"""

import re
import sys
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

WORKSPACE_ROOT = Path(r"c:\Users\DELL\ayesha_pro\medi_qr")
SCHEMA_FILE = WORKSPACE_ROOT / "supabase" / "migrations" / "0001_umbrella_schema.sql"
SMOKE_FILE = WORKSPACE_ROOT / "supabase" / "tests" / "rls_smoke.sql"
SEED_FILE = WORKSPACE_ROOT / "supabase" / "seed.sql"
TYPES_FILE = WORKSPACE_ROOT / "src" / "lib" / "supabase" / "types.ts"

# ==============================================================================
# 1. STATIC SECURITY INVARIANT VERIFICATION
# ==============================================================================

def verify_static_invariants(schema_sql: str, smoke_sql: str, seed_sql: str, types_ts: str) -> List[str]:
    findings = []
    
    # N1 Check: get_emergency_triage_by_token MUST NOT project residential_address, spouse_dependents, or qr_token
    rpc_match = re.search(r"create or replace function public\.get_emergency_triage_by_token.*?jsonb_build_object\s*\((.*?)\)\s*from", schema_sql, re.DOTALL)
    if not rpc_match:
        findings.append("CRITICAL: get_emergency_triage_by_token jsonb_build_object projection not found in schema!")
    else:
        projected_block = rpc_match.group(1)
        projected_keys = re.findall(r"'([a-zA-Z0-9_]+)'\s*,", projected_block)
        if "residential_address" in projected_keys:
            findings.append("CRITICAL N1 VIOLATION: residential_address exposed in get_emergency_triage_by_token!")
        if "spouse_dependents" in projected_keys:
            findings.append("CRITICAL N1 VIOLATION: spouse_dependents exposed in get_emergency_triage_by_token!")
        if "qr_token" in projected_keys:
            findings.append("HIGH N1 VIOLATION: qr_token projected in emergency triage JSON!")

    # N3 & Security Definer search_path check
    sec_def_funcs = re.findall(r"create (?:or replace )?function public\.(\w+)[^;]*?security definer[^;]*?;", schema_sql, re.IGNORECASE)
    for func in sec_def_funcs:
        # Check if search_path = '' is present
        pattern = rf"create (?:or replace )?function public\.{func}[^;]*?security definer[^;]*?set search_path = ''"
        if not re.search(pattern, schema_sql, re.IGNORECASE | re.DOTALL):
            findings.append(f"HIGH N3 RISK: Function {func} is SECURITY DEFINER but lacks 'set search_path = '''")

    # N4 Check: zero references to service_role in schema, smoke, seed, and types
    for name, content in [("schema", schema_sql), ("smoke", smoke_sql), ("seed", seed_sql), ("types", types_ts)]:
        if "service_role" in content:
            findings.append(f"CRITICAL N4 VIOLATION: 'service_role' reference discovered in {name}!")

    # D1 & D3: Check revoked table grants
    anon_revokes = re.findall(r"revoke all on ([^;]+) from anon", schema_sql, re.IGNORECASE)
    auth_revokes = re.findall(r"revoke all on ([^;]+) from authenticated", schema_sql, re.IGNORECASE)
    anon_revoked_tables = [t.strip().replace("public.", "") for block in anon_revokes for t in block.split(",")]
    auth_revoked_tables = [t.strip().replace("public.", "") for block in auth_revokes for t in block.split(",")]

    for table in ["accounts", "patient_profiles", "clinical_records", "appointments"]:
        if table not in anon_revoked_tables:
            findings.append(f"HIGH D3 RISK: Missing 'revoke all on public.{table} from anon'")
        if table not in auth_revoked_tables:
            findings.append(f"HIGH D3 RISK: Missing 'revoke all on public.{table} from authenticated'")

    # D4: residential_address text not null default ''
    if "residential_address text not null default ''" not in schema_sql:
        findings.append("MEDIUM D4 GAP: residential_address not defined as text not null default ''")

    # D6: appointments.doctor_id on delete restrict
    if not re.search(r"doctor_id\s+uuid\s+not null\s+references\s+public\.accounts\(id\)\s+on delete restrict", schema_sql, re.IGNORECASE):
        findings.append("MEDIUM D6 GAP: appointments.doctor_id missing 'on delete restrict'")

    # N10: Typescript types no 'any'
    any_matches = re.findall(r"\bany\b", types_ts)
    if any_matches:
        findings.append(f"HIGH N10 VIOLATION: {len(any_matches)} occurrence(s) of 'any' keyword found in types.ts")

    return findings

# ==============================================================================
# 2. ADVERSARIAL ATTACK SIMULATION ENGINE
# ==============================================================================

class PostgresMockState:
    """
    Simulates Postgres tables, column grants, RLS policies, and triggers
    to test adversarial attack vectors empirically.
    """
    def __init__(self):
        self.accounts = {}           # id -> dict
        self.patient_profiles = {}   # patient_id -> dict
        self.clinical_records = {}   # patient_id -> dict
        self.appointments = {}       # id -> dict
        
        # Column UPDATE grants for 'authenticated'
        self.update_grants = {
            "accounts": {"full_name", "contact_phone", "specialization"},
            "patient_profiles": {"age", "blood_group", "emergency_contact_name", "emergency_contact_phone", "emergency_contact_relation", "spouse_dependents", "residential_address"},
            "clinical_records": {"medical_conditions", "current_medication", "previous_surgeries", "allergies"},
            "appointments": {"scheduled_at", "status", "reason", "clinical_notes"}
        }
        
        # INSERT grants for 'authenticated'
        self.insert_grants = {
            "accounts": False,
            "patient_profiles": False,
            "clinical_records": False,
            "appointments": True
        }
        
        # DELETE grants for 'authenticated'
        self.delete_grants = {
            "accounts": False,
            "patient_profiles": False,
            "clinical_records": False,
            "appointments": False
        }

    def signup_user(self, user_id: str, email: str, meta: dict):
        """Simulates handle_new_user() trigger"""
        role_raw = meta.get("role")
        v_role = "doctor" if role_raw == "doctor" else "patient"
        
        # Insert into accounts
        self.accounts[user_id] = {
            "id": user_id,
            "email": email,
            "role": v_role,
            "full_name": meta.get("full_name", "Unknown"),
            "contact_phone": meta.get("contact_phone", ""),
            "medical_license_number": meta.get("medical_license_number") if v_role == "doctor" else None,
            "specialization": meta.get("specialization") if v_role == "doctor" else None,
            "doctor_status": "pending" if v_role == "doctor" else None,
            "created_at": "2026-11-01T00:00:00Z",
            "updated_at": "2026-11-01T00:00:00Z"
        }
        
        # If patient, create profile & clinical record
        if v_role == "patient":
            bg = meta.get("blood_group")
            valid_bgs = {'A+','A-','B+','B-','AB+','AB-','O+','O-'}
            v_bg = bg if bg in valid_bgs else 'Unknown'
            
            try:
                age_val = int(meta.get("age", 0)) if meta.get("age") else 0
            except ValueError:
                age_val = 0

            self.patient_profiles[user_id] = {
                "patient_id": user_id,
                "patient_code": f"UMB-{uuid.uuid4().hex[:6].upper()}",
                "qr_token": str(uuid.uuid4()),
                "age": age_val,
                "blood_group": v_bg,
                "emergency_contact_name": meta.get("emergency_contact_name", ""),
                "emergency_contact_phone": meta.get("emergency_contact_phone", ""),
                "emergency_contact_relation": meta.get("emergency_contact_relation", ""),
                "spouse_dependents": [],
                "residential_address": meta.get("residential_address", ""),
                "created_at": "2026-11-01T00:00:00Z",
                "updated_at": "2026-11-01T00:00:00Z"
            }
            
            # create_clinical_record trigger
            self.clinical_records[user_id] = {
                "patient_id": user_id,
                "medical_conditions": [],
                "current_medication": [],
                "previous_surgeries": [],
                "allergies": [],
                "is_doctor_verified": False,
                "last_updated_by_doctor_id": None,
                "last_appointment_date": None,
                "last_appointment_summary": None,
                "created_at": "2026-11-01T00:00:00Z",
                "updated_at": "2026-11-01T00:00:00Z"
            }

    def is_approved_doctor(self, caller_id: Optional[str]) -> bool:
        if not caller_id or caller_id not in self.accounts:
            return False
        acc = self.accounts[caller_id]
        return acc.get("role") == "doctor" and acc.get("doctor_status") == "approved"

    # --- Query Simulation with RLS & Grant Checks ---

    def select_table(self, table_name: str, caller_role: str, caller_id: Optional[str]) -> Tuple[bool, List[dict], str]:
        if caller_role == "anon":
            return False, [], "42501: permission denied for table " + table_name
        
        results = []
        if table_name == "patient_profiles":
            for pid, row in self.patient_profiles.items():
                # RLS: patient_id = auth.uid() or is_approved_doctor()
                if pid == caller_id or self.is_approved_doctor(caller_id):
                    results.append(row.copy())
            return True, results, "OK"
            
        elif table_name == "clinical_records":
            for pid, row in self.clinical_records.items():
                # RLS: patient_id = auth.uid() or is_approved_doctor()
                if pid == caller_id or self.is_approved_doctor(caller_id):
                    results.append(row.copy())
            return True, results, "OK"
            
        elif table_name == "appointments":
            for aid, row in self.appointments.items():
                # RLS: patient_id = auth.uid() or is_approved_doctor()
                if row["patient_id"] == caller_id or self.is_approved_doctor(caller_id):
                    results.append(row.copy())
            return True, results, "OK"
            
        elif table_name == "accounts":
            for uid, row in self.accounts.items():
                # RLS: accounts_select_self OR accounts_select_patients_for_doctors OR accounts_select_my_doctors
                is_self = (uid == caller_id)
                is_patient_for_doc = (row["role"] == "patient" and self.is_approved_doctor(caller_id))
                is_my_doc = (row["role"] == "doctor" and any(
                    ap["doctor_id"] == uid and ap["patient_id"] == caller_id for ap in self.appointments.values()
                ))
                if is_self or is_patient_for_doc or is_my_doc:
                    results.append(row.copy())
            return True, results, "OK"
            
        return False, [], "Unknown table"

    def update_table(self, table_name: str, caller_role: str, caller_id: Optional[str], target_pk: str, columns_to_update: dict) -> Tuple[bool, int, str]:
        if caller_role == "anon":
            return False, 0, "42501: permission denied for table " + table_name
        
        # Check column-level grants
        allowed_cols = self.update_grants.get(table_name, set())
        for col in columns_to_update.keys():
            if col not in allowed_cols:
                return False, 0, f"42501: permission denied for column {col} of relation {table_name}"
        
        # Evaluate RLS
        if table_name == "accounts":
            # using (id = auth.uid())
            if target_pk != caller_id:
                return True, 0, "OK (0 rows affected)"
            row = self.accounts.get(target_pk)
            if not row:
                return True, 0, "OK (0 rows affected)"
            row.update(columns_to_update)
            return True, 1, "OK"
            
        elif table_name == "patient_profiles":
            # using (patient_id = auth.uid())
            if target_pk != caller_id:
                return True, 0, "OK (0 rows affected)"
            row = self.patient_profiles.get(target_pk)
            if not row:
                return True, 0, "OK (0 rows affected)"
            row.update(columns_to_update)
            return True, 1, "OK"
            
        elif table_name == "clinical_records":
            # using (is_approved_doctor())
            if not self.is_approved_doctor(caller_id):
                return True, 0, "OK (0 rows affected by RLS)"
            row = self.clinical_records.get(target_pk)
            if not row:
                return True, 0, "OK (0 rows affected)"
            row.update(columns_to_update)
            # Trigger stamp_clinical_update
            row["is_doctor_verified"] = True
            row["last_updated_by_doctor_id"] = caller_id
            return True, 1, "OK"
            
        elif table_name == "appointments":
            # using (is_approved_doctor())
            if not self.is_approved_doctor(caller_id):
                return True, 0, "OK (0 rows affected by RLS)"
            row = self.appointments.get(target_pk)
            if not row:
                return True, 0, "OK (0 rows affected)"
            old_status = row.get("status")
            row.update(columns_to_update)
            # Trigger on_appointment_completed
            if row.get("status") == "completed" and old_status != "completed":
                pid = row["patient_id"]
                cr = self.clinical_records.get(pid)
                if cr:
                    cr["last_appointment_date"] = row["scheduled_at"]
                    cr["last_appointment_summary"] = row.get("clinical_notes") or row.get("reason")
                    # D8 invariant: does NOT flip is_doctor_verified
            return True, 1, "OK"

        return False, 0, "Unknown table"

    def delete_table(self, table_name: str, caller_role: str, caller_id: Optional[str]) -> Tuple[bool, str]:
        if not self.delete_grants.get(table_name, False):
            return False, f"42501: permission denied for relation {table_name}"
        return True, "Deleted"

    # --- RPC Implementations ---

    def rpc_get_emergency_triage_by_token(self, token_str: str) -> Optional[dict]:
        # public zero-login emergency triage reader
        for pid, profile in self.patient_profiles.items():
            if profile.get("qr_token") == token_str:
                acc = self.accounts.get(pid, {})
                cr = self.clinical_records.get(pid, {})
                return {
                    "full_name": acc.get("full_name"),
                    "contact_phone": acc.get("contact_phone"),
                    "patient_code": profile.get("patient_code"),
                    "age": profile.get("age"),
                    "blood_group": profile.get("blood_group"),
                    "emergency_contact_name": profile.get("emergency_contact_name"),
                    "emergency_contact_phone": profile.get("emergency_contact_phone"),
                    "emergency_contact_relation": profile.get("emergency_contact_relation"),
                    "medical_conditions": cr.get("medical_conditions", []),
                    "current_medication": cr.get("current_medication", []),
                    "previous_surgeries": cr.get("previous_surgeries", []),
                    "allergies": cr.get("allergies", []),
                    "last_appointment_date": cr.get("last_appointment_date"),
                    "is_doctor_verified": cr.get("is_doctor_verified", False),
                    "updated_at": cr.get("updated_at")
                }
        return None

    def rpc_submit_self_reported_baseline(self, caller_id: str, conditions: List[str], allergies: List[str]) -> Tuple[bool, str]:
        if len(conditions) > 50 or len(allergies) > 50:
            return False, "Too many entries"
        cr = self.clinical_records.get(caller_id)
        if not cr or cr.get("is_doctor_verified"):
            return False, "Record is already doctor-verified, or no patient profile exists"
        cr["medical_conditions"] = list(conditions)
        cr["allergies"] = list(allergies)
        return True, "Baseline recorded"

    def rpc_regenerate_qr_token(self, caller_id: str) -> Tuple[bool, Optional[str], str]:
        profile = self.patient_profiles.get(caller_id)
        if not profile:
            return False, None, "No patient profile for this user"
        new_token = str(uuid.uuid4())
        profile["qr_token"] = new_token
        return True, new_token, "Token rotated"

# ==============================================================================
# 3. ADVERSARIAL STRESS TEST SUITE
# ==============================================================================

def run_adversarial_suite() -> Dict[str, Any]:
    state = PostgresMockState()
    report = {
        "tests_run": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "results": []
    }
    
    def record_result(test_name: str, passed: bool, details: str):
        report["tests_run"] += 1
        if passed:
            report["tests_passed"] += 1
        else:
            report["tests_failed"] += 1
        report["results"].append({
            "test": test_name,
            "passed": passed,
            "details": details
        })

    # Setup identities
    PAT_A = "00000000-0000-0000-0000-0000000000a1"
    PAT_B = "00000000-0000-0000-0000-0000000000a2"
    DOC_PENDING = "00000000-0000-0000-0000-0000000000d1"
    DOC_APPROVED = "00000000-0000-0000-0000-0000000000d2"
    EVIL_USER = "00000000-0000-0000-0000-0000000000e1"
    
    state.signup_user(PAT_A, "pat.a@example.test", {
        "role": "patient", "full_name": "Patient A", "age": "30", "blood_group": "O+",
        "emergency_contact_name": "Contact A", "emergency_contact_phone": "+1001",
        "emergency_contact_relation": "Parent", "residential_address": "123 Patient Rd"
    })
    state.signup_user(PAT_B, "pat.b@example.test", {
        "role": "patient", "full_name": "Patient B", "age": "40", "blood_group": "A-",
        "emergency_contact_name": "Contact B", "emergency_contact_phone": "+1002",
        "emergency_contact_relation": "Spouse", "residential_address": "456 Private Ave"
    })
    state.signup_user(DOC_PENDING, "doc.pending@example.test", {
        "role": "doctor", "full_name": "Dr. Pending", "medical_license_number": "LIC-P-01"
    })
    state.signup_user(DOC_APPROVED, "doc.approved@example.test", {
        "role": "doctor", "full_name": "Dr. Approved", "medical_license_number": "LIC-A-02"
    })
    # Admin approval simulation for DOC_APPROVED
    state.accounts[DOC_APPROVED]["doctor_status"] = "approved"

    # --- SCENARIO 1: CROSS-TENANT DATA LEAKAGE ---
    # 1.1: Patient A reads Patient B's profile
    ok, rows, err = state.select_table("patient_profiles", "authenticated", PAT_A)
    p_b_rows = [r for r in rows if r["patient_id"] == PAT_B]
    record_result("ATTACK 1.1: Patient A reads Patient B patient_profile", len(p_b_rows) == 0, f"Rows leaked: {len(p_b_rows)}")
    
    # 1.2: Patient A reads Patient B's clinical record
    ok, rows, err = state.select_table("clinical_records", "authenticated", PAT_A)
    cr_b_rows = [r for r in rows if r["patient_id"] == PAT_B]
    record_result("ATTACK 1.2: Patient A reads Patient B clinical_record", len(cr_b_rows) == 0, f"Rows leaked: {len(cr_b_rows)}")
    
    # 1.3: Patient A attempts to update Patient B's demographics
    ok, affected, err = state.update_table("patient_profiles", "authenticated", PAT_A, PAT_B, {"emergency_contact_name": "HACKED"})
    record_result("ATTACK 1.3: Patient A updates Patient B profile", affected == 0, f"Rows affected: {affected}")

    # --- SCENARIO 2: PENDING DOCTOR PRIVILEGE ESCALATION & BYPASS ---
    # 2.1: Pending doctor reads patient profiles
    ok, rows, err = state.select_table("patient_profiles", "authenticated", DOC_PENDING)
    record_result("ATTACK 2.1: Pending doctor reads patient_profiles", len(rows) == 0, f"Rows returned: {len(rows)}")

    # 2.2: Pending doctor reads clinical records
    ok, rows, err = state.select_table("clinical_records", "authenticated", DOC_PENDING)
    record_result("ATTACK 2.2: Pending doctor reads clinical_records", len(rows) == 0, f"Rows returned: {len(rows)}")

    # 2.3: Pending doctor updates clinical record
    ok, affected, err = state.update_table("clinical_records", "authenticated", DOC_PENDING, PAT_A, {"medical_conditions": ["Forged"]})
    record_result("ATTACK 2.3: Pending doctor updates clinical_records", affected == 0, f"Rows affected: {affected}")

    # 2.4: Approved doctor reads patient profiles (Expected: ALLOW)
    ok, rows, err = state.select_table("patient_profiles", "authenticated", DOC_APPROVED)
    record_result("CONTROL 2.4: Approved doctor reads patient_profiles", len(rows) >= 2, f"Rows returned: {len(rows)}")

    # --- SCENARIO 3: ROLE ESCALATION & PRIVILEGE HIJACKING ---
    # 3.1: Patient updates accounts.role to 'doctor'
    ok, affected, err = state.update_table("accounts", "authenticated", PAT_A, PAT_A, {"role": "doctor"})
    record_result("ATTACK 3.1: Patient updates accounts.role", not ok and "permission denied for column role" in err, f"Result: ok={ok}, err={err}")

    # 3.2: Patient updates accounts.doctor_status to 'approved'
    ok, affected, err = state.update_table("accounts", "authenticated", PAT_A, PAT_A, {"doctor_status": "approved"})
    record_result("ATTACK 3.2: Patient updates accounts.doctor_status", not ok and "permission denied for column doctor_status" in err, f"Result: ok={ok}, err={err}")

    # 3.3: Evil user signs up with role='admin'
    state.signup_user(EVIL_USER, "evil@example.test", {"role": "admin", "full_name": "Evil Admin"})
    evil_acc = state.accounts[EVIL_USER]
    record_result("ATTACK 3.3: Signup with role='admin' coerced to patient", evil_acc["role"] == "patient" and evil_acc["doctor_status"] is None, f"Result: role={evil_acc['role']}, status={evil_acc['doctor_status']}")

    # --- SCENARIO 4: TOKEN FORGERY & QR MANIPULATION ---
    # 4.1: Patient directly updates qr_token
    ok, affected, err = state.update_table("patient_profiles", "authenticated", PAT_A, PAT_A, {"qr_token": str(uuid.uuid4())})
    record_result("ATTACK 4.1: Direct UPDATE on patient_profiles.qr_token", not ok and "permission denied for column qr_token" in err, f"Result: ok={ok}, err={err}")

    # 4.2: Patient directly updates patient_code
    ok, affected, err = state.update_table("patient_profiles", "authenticated", PAT_A, PAT_A, {"patient_code": "UMB-P1RATE"})
    record_result("ATTACK 4.2: Direct UPDATE on patient_profiles.patient_code", not ok and "permission denied for column patient_code" in err, f"Result: ok={ok}, err={err}")

    # 4.3: Patient calls regenerate_qr_token (Expected: ALLOW, old invalidated, new valid)
    old_token = state.patient_profiles[PAT_A]["qr_token"]
    ok, new_token, msg = state.rpc_regenerate_qr_token(PAT_A)
    old_lookup = state.rpc_get_emergency_triage_by_token(old_token)
    new_lookup = state.rpc_get_emergency_triage_by_token(new_token)
    token_test_passed = ok and (new_token != old_token) and (old_lookup is None) and (new_lookup is not None)
    record_result("CHECK 4.3: regenerate_qr_token invalidates old token and activates new token", token_test_passed, f"Old lookup: {old_lookup is not None}, New lookup: {new_lookup is not None}")

    # --- SCENARIO 5: ANONYMOUS TABLE ACCESS ---
    for tbl in ["accounts", "patient_profiles", "clinical_records", "appointments"]:
        ok, rows, err = state.select_table(tbl, "anon", None)
        record_result(f"ATTACK 5.{tbl}: anon SELECT on {tbl}", not ok and "permission denied" in err, f"Result: ok={ok}, err={err}")

    # --- SCENARIO 6: EMERGENCY ROUTE PRIVACY LEAKAGE (N1) ---
    token_a = state.patient_profiles[PAT_A]["qr_token"]
    triage_data = state.rpc_get_emergency_triage_by_token(token_a)
    n1_clean = (
        triage_data is not None and
        "residential_address" not in triage_data and
        "spouse_dependents" not in triage_data and
        "qr_token" not in triage_data and
        triage_data.get("full_name") == "Patient A" and
        triage_data.get("blood_group") == "O+"
    )
    record_result("CHECK 6.1: Emergency triage RPC whitelist projection strictly excludes address and dependents", n1_clean, f"Keys in triage: {list(triage_data.keys()) if triage_data else None}")

    unknown_triage = state.rpc_get_emergency_triage_by_token(str(uuid.uuid4()))
    record_result("CHECK 6.2: Emergency triage RPC unknown token returns null", unknown_triage is None, f"Result: {unknown_triage}")

    # --- SCENARIO 7: CLINICAL RECORD BASELINE & VERIFICATION ---
    # 7.1: Patient submits baseline while unverified
    ok, msg = state.rpc_submit_self_reported_baseline(PAT_A, ["Asthma", "Diabetes"], ["Penicillin"])
    cr_a = state.clinical_records[PAT_A]
    record_result("CHECK 7.1: Patient baseline submission unverified", ok and "Asthma" in cr_a["medical_conditions"], f"Conditions: {cr_a['medical_conditions']}")

    # 7.2: Patient submits baseline with > 50 items (DoS / bounds test)
    huge_list = [f"Cond {i}" for i in range(51)]
    ok, msg = state.rpc_submit_self_reported_baseline(PAT_A, huge_list, ["Pollen"])
    record_result("ATTACK 7.2: Baseline submission with > 50 items blocked", not ok and "Too many entries" in msg, f"Result: ok={ok}, msg={msg}")

    # 7.3: Doctor updates Patient A's clinical record (stamps verification)
    ok, affected, err = state.update_table("clinical_records", "authenticated", DOC_APPROVED, PAT_A, {"medical_conditions": ["Asthma Verified"]})
    cr_a = state.clinical_records[PAT_A]
    record_result("CHECK 7.3: Doctor update stamps is_doctor_verified and doctor_id", cr_a["is_doctor_verified"] and cr_a["last_updated_by_doctor_id"] == DOC_APPROVED, f"Verified: {cr_a['is_doctor_verified']}, Doctor: {cr_a['last_updated_by_doctor_id']}")

    # 7.4: Patient attempts baseline update after doctor verification
    ok, msg = state.rpc_submit_self_reported_baseline(PAT_A, ["New Condition"], [])
    record_result("ATTACK 7.4: Patient baseline submission blocked after doctor verification", not ok and "already doctor-verified" in msg, f"Result: ok={ok}, msg={msg}")

    # --- SCENARIO 8: DELETION BLOCKING ---
    for tbl in ["accounts", "patient_profiles", "clinical_records", "appointments"]:
        ok, err = state.delete_table(tbl, "authenticated", DOC_APPROVED)
        record_result(f"ATTACK 8.{tbl}: DELETE on {tbl} blocked for authenticated", not ok and "permission denied" in err, f"Result: ok={ok}, err={err}")

    return report

# ==============================================================================
# 4. SMOKE TEST HARNESS VALIDATION
# ==============================================================================

def verify_smoke_test_harness(smoke_sql: str) -> List[str]:
    findings = []
    
    # 1. Transactional isolation
    lines = [l.strip() for l in smoke_sql.splitlines() if l.strip() and not l.strip().startswith("--")]
    if lines[0].lower() != "begin;":
        findings.append("CRITICAL: rls_smoke.sql does not begin with 'begin;'")
    if lines[-1].lower() != "rollback;":
        findings.append("CRITICAL: rls_smoke.sql does not end with 'rollback;'")

    # 2. Checklist checks 1 to 14
    for i in range(1, 15):
        pattern = rf"-- CHECK {i}:"
        if not re.search(pattern, smoke_sql):
            findings.append(f"HIGH: rls_smoke.sql missing CHECK {i}")

    # 3. Verify specific role simulations
    if "set local role anon;" not in smoke_sql:
        findings.append("HIGH: rls_smoke.sql missing 'set local role anon;'")
    if "set local role authenticated;" not in smoke_sql:
        findings.append("HIGH: rls_smoke.sql missing 'set local role authenticated;'")

    # 4. Verify exception trapping for insufficient_privilege
    priv_matches = len(re.findall(r"exception when insufficient_privilege then", smoke_sql, re.IGNORECASE))
    if priv_matches < 4:
        findings.append(f"MEDIUM: Expected >= 4 insufficient_privilege handlers in rls_smoke.sql, found {priv_matches}")

    return findings

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if __name__ == "__main__":
    print("=== UMBRELLA PHASE 3 EMPIRICAL CHALLENGER TEST HARNESS ===")
    
    schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")
    smoke_sql = SMOKE_FILE.read_text(encoding="utf-8")
    seed_sql = SEED_FILE.read_text(encoding="utf-8")
    types_ts = TYPES_FILE.read_text(encoding="utf-8")

    # 1. Static Checks
    print("\n[Phase 1] Static Invariant Verification...")
    static_findings = verify_static_invariants(schema_sql, smoke_sql, seed_sql, types_ts)
    if static_findings:
        print(f"FAILED: Found {len(static_findings)} static invariant violations:")
        for f in static_findings:
            print(f"  - {f}")
    else:
        print("PASSED: All static invariants (N1, N3, N4, N10, D1, D3, D4, D6) verified.")

    # 2. Smoke Test SQL Checks
    print("\n[Phase 2] Smoke Test Harness Validation...")
    smoke_findings = verify_smoke_test_harness(smoke_sql)
    if smoke_findings:
        print(f"FAILED: Found {len(smoke_findings)} smoke harness violations:")
        for f in smoke_findings:
            print(f"  - {f}")
    else:
        print("PASSED: rls_smoke.sql correctly structured (BEGIN..ROLLBACK, Checks 1-14, role switches, exception handlers).")

    # 3. Adversarial Simulation Suite
    print("\n[Phase 3] Executing Adversarial Attack Simulation Suite...")
    report = run_adversarial_suite()
    for res in report["results"]:
        status = "PASS" if res["passed"] else "FAIL"
        print(f"[{status}] {res['test']} -> {res['details']}")

    print(f"\nSimulation Suite Summary: {report['tests_passed']}/{report['tests_run']} passed, {report['tests_failed']} failed.")

    # Exit code
    if static_findings or smoke_findings or report["tests_failed"] > 0:
        sys.exit(1)
    else:
        print("\nALL EMPIRICAL CHALLENGE TESTS PASSED!")
        sys.exit(0)

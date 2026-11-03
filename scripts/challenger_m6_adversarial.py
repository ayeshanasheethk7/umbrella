#!/usr/bin/env python3
"""
scripts/challenger_m6_adversarial.py
Empirical Adversarial Security & Penetration Challenge Suite for Milestone M6:
Doctor Portal Surface (/portal/doctor)

Executed by: Challenger M6-1 (Doctor Portal Adversarial Security & Penetration Challenger)
Roles: critic, specialist

Probes 5 Core Challenge Vectors:
1. PostgREST Operator & SQL Injection Attacks on Patient Search
2. Authorization & RBAC Bypass Attacks (Anon, Patient, Pending Doctor, Declined Doctor)
3. Audit Stamp Tampering & Verification Spoofing Attacks
4. Concurrency Collision & Optimistic Locking Attacks
5. Invariant N4 Secret Leak & Security Invariant Sweep
"""

import os
import re
import sys
import uuid
import json
import datetime
from typing import Dict, Any, List, Optional, Tuple

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Global Test Counters
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
# POSTGRES ENGINE & ORACLE SIMULATOR
# Implements exact schema rules from supabase/migrations/0001_umbrella_schema.sql
# ==============================================================================

class PostgresOracle:
    def __init__(self):
        self.accounts: Dict[str, Dict[str, Any]] = {}
        self.patient_profiles: Dict[str, Dict[str, Any]] = {}
        self.clinical_records: Dict[str, Dict[str, Any]] = {}
        self.appointments: Dict[str, Dict[str, Any]] = {}
        
        # Session state
        self.current_user_id: Optional[str] = None
        self.current_role: str = 'anon'
        self.umbrella_skip_stamp: str = 'off'

    def set_session(self, user_id: Optional[str], role: str = 'authenticated'):
        self.current_user_id = user_id
        self.current_role = role if user_id else 'anon'

    def seed_data(self):
        # 1. Approved Doctor A
        doc_a_id = "00000000-0000-0000-0000-0000000000d1"
        self.accounts[doc_a_id] = {
            "id": doc_a_id, "full_name": "Dr. Sarah Chen, MD", "email": "sarah.chen@hospital.org",
            "role": "doctor", "doctor_status": "approved", "specialization": "Emergency Medicine",
            "medical_license_number": "MD-12345", "contact_phone": "+15550001111",
            "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"
        }

        # 2. Approved Doctor B
        doc_b_id = "00000000-0000-0000-0000-0000000000d2"
        self.accounts[doc_b_id] = {
            "id": doc_b_id, "full_name": "Dr. Robert Marcus, DO", "email": "robert.marcus@clinic.org",
            "role": "doctor", "doctor_status": "approved", "specialization": "Cardiology",
            "medical_license_number": "DO-98765", "contact_phone": "+15550002222",
            "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"
        }

        # 3. Pending Doctor C
        doc_c_id = "00000000-0000-0000-0000-0000000000d3"
        self.accounts[doc_c_id] = {
            "id": doc_c_id, "full_name": "Dr. Emily Taylor, MD", "email": "emily.taylor@med.org",
            "role": "doctor", "doctor_status": "pending", "specialization": "Pediatrics",
            "medical_license_number": "MD-55555", "contact_phone": "+15550003333",
            "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"
        }

        # 4. Declined Doctor D
        doc_d_id = "00000000-0000-0000-0000-0000000000d4"
        self.accounts[doc_d_id] = {
            "id": doc_d_id, "full_name": "Dr. Fraudster, MD", "email": "fake@med.org",
            "role": "doctor", "doctor_status": "declined", "specialization": "General",
            "medical_license_number": "FAKE-00000", "contact_phone": "+15550004444",
            "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"
        }

        # 5. Patient 1 (Alex Morgan - Unverified baseline)
        pat_1_id = "00000000-0000-0000-0000-0000000000a1"
        self.accounts[pat_1_id] = {
            "id": pat_1_id, "full_name": "Alex Morgan", "email": "alex.morgan@example.com",
            "role": "patient", "doctor_status": None, "specialization": None,
            "medical_license_number": None, "contact_phone": "+15551234567",
            "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"
        }
        self.patient_profiles[pat_1_id] = {
            "patient_id": pat_1_id, "patient_code": "UMB-ALX001",
            "qr_token": "a1a1a1a1-a1a1-4a1a-8a1a-a1a1a1a1a1a1", "age": 34, "blood_group": "O+",
            "emergency_contact_name": "Taylor Morgan", "emergency_contact_phone": "+15559876543",
            "emergency_contact_relation": "Spouse", "spouse_dependents": [],
            "residential_address": "123 Elm Street", "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z"
        }
        self.clinical_records[pat_1_id] = {
            "patient_id": pat_1_id,
            "medical_conditions": ["Mild Asthma"],
            "current_medication": [{"name": "Albuterol", "dosage": "90mcg", "frequency": "as needed"}],
            "previous_surgeries": [{"procedure": "Appendectomy", "year": 2018}],
            "allergies": ["Penicillin"],
            "last_appointment_date": None,
            "last_appointment_summary": None,
            "is_doctor_verified": False,
            "last_updated_by_doctor_id": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T10:00:00Z"
        }

        # 6. Patient 2 (Jordan Casey - Verified record)
        pat_2_id = "00000000-0000-0000-0000-0000000000a2"
        self.accounts[pat_2_id] = {
            "id": pat_2_id, "full_name": "Jordan Casey", "email": "jordan.casey@example.com",
            "role": "patient", "doctor_status": None, "specialization": None,
            "medical_license_number": None, "contact_phone": "+15552345678",
            "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"
        }
        self.patient_profiles[pat_2_id] = {
            "patient_id": pat_2_id, "patient_code": "UMB-JOR002",
            "qr_token": "b2b2b2b2-b2b2-4b2b-8b2b-b2b2b2b2b2b2", "age": 45, "blood_group": "A-",
            "emergency_contact_name": "Sam Casey", "emergency_contact_phone": "+15558765432",
            "emergency_contact_relation": "Brother", "spouse_dependents": [],
            "residential_address": "456 Oak Avenue", "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z"
        }
        self.clinical_records[pat_2_id] = {
            "patient_id": pat_2_id,
            "medical_conditions": ["Hypertension"],
            "current_medication": [{"name": "Lisinopril", "dosage": "10mg", "frequency": "once daily"}],
            "previous_surgeries": [],
            "allergies": ["Sulfa Drugs"],
            "last_appointment_date": "2026-01-15T09:00:00Z",
            "last_appointment_summary": "Routine cardiology review",
            "is_doctor_verified": True,
            "last_updated_by_doctor_id": doc_a_id,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-15T09:30:00Z"
        }

        # 7. Initial Appointment for Doctor A with Patient 1
        appt_1_id = "00000000-0000-0000-0000-0000000000e1"
        self.appointments[appt_1_id] = {
            "id": appt_1_id,
            "doctor_id": doc_a_id,
            "patient_id": pat_1_id,
            "scheduled_at": "2026-02-01T14:00:00Z",
            "status": "scheduled",
            "reason": "Asthma followup",
            "clinical_notes": None,
            "created_at": "2026-01-10T00:00:00Z",
            "updated_at": "2026-01-10T00:00:00Z"
        }

    # Helper: is_approved_doctor()
    def is_approved_doctor(self) -> bool:
        if not self.current_user_id:
            return False
        acc = self.accounts.get(self.current_user_id)
        if not acc:
            return False
        return acc.get("role") == "doctor" and acc.get("doctor_status") == "approved"

    # Direct RLS Check for SELECT patient_profiles
    def rls_can_select_patient_profile(self, patient_id: str) -> bool:
        if self.current_role != 'authenticated' or not self.current_user_id:
            return False
        # using (patient_id = (select auth.uid()) or (select public.is_approved_doctor()))
        return self.current_user_id == patient_id or self.is_approved_doctor()

    # Direct RLS Check for SELECT clinical_records
    def rls_can_select_clinical_record(self, patient_id: str) -> bool:
        if self.current_role != 'authenticated' or not self.current_user_id:
            return False
        # using (patient_id = (select auth.uid()) or (select public.is_approved_doctor()))
        return self.current_user_id == patient_id or self.is_approved_doctor()

    # Direct RLS Check for UPDATE clinical_records
    def rls_can_update_clinical_record(self) -> bool:
        if self.current_role != 'authenticated' or not self.current_user_id:
            return False
        # using ((select public.is_approved_doctor())) with check ((select public.is_approved_doctor()))
        return self.is_approved_doctor()

    # Direct RLS Check for INSERT appointments
    def rls_can_insert_appointment(self, doctor_id: str) -> bool:
        if self.current_role != 'authenticated' or not self.current_user_id:
            return False
        # with check ((select public.is_approved_doctor()) and doctor_id = (select auth.uid()))
        return self.is_approved_doctor() and doctor_id == self.current_user_id

    # Direct RLS Check for UPDATE appointments
    def rls_can_update_appointment(self) -> bool:
        if self.current_role != 'authenticated' or not self.current_user_id:
            return False
        # using ((select public.is_approved_doctor())) with check ((select public.is_approved_doctor()))
        return self.is_approved_doctor()

    # Trigger: trg_stamp_clinical
    def trigger_stamp_clinical(self, old_row: Dict[str, Any], new_row: Dict[str, Any]) -> Dict[str, Any]:
        stamped = dict(new_row)
        stamped["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if self.umbrella_skip_stamp != 'on' and self.is_approved_doctor():
            stamped["is_doctor_verified"] = True
            stamped["last_updated_by_doctor_id"] = self.current_user_id
        return stamped

    # Trigger: trg_appointment_completed
    def trigger_appointment_completed(self, old_row: Dict[str, Any], new_row: Dict[str, Any]):
        if new_row.get("status") == "completed" and old_row.get("status") != "completed":
            prev_skip = self.umbrella_skip_stamp
            self.umbrella_skip_stamp = "on"
            try:
                pat_id = new_row["patient_id"]
                cr = self.clinical_records.get(pat_id)
                if cr:
                    summary = new_row.get("clinical_notes") or new_row.get("reason")
                    cr["last_appointment_date"] = new_row["scheduled_at"]
                    cr["last_appointment_summary"] = summary
                    # trg_stamp_clinical runs on clinical_records update!
                    updated_cr = self.trigger_stamp_clinical(cr, cr)
                    self.clinical_records[pat_id] = updated_cr
            finally:
                self.umbrella_skip_stamp = prev_skip

# ==============================================================================
# SERVER ACTION EMULATION (Exact Mirror of src/app/portal/doctor/actions.ts)
# ==============================================================================

def escape_search_term(t: str) -> str:
    """Exact implementation from src/app/portal/doctor/actions.ts line 44-46"""
    return (t or '').replace('\\', '\\\\').replace('%', '').replace('_', '').replace('(', '').replace(')', '').replace(',', '').strip()

class DoctorActionHarness:
    def __init__(self, db: PostgresOracle):
        self.db = db

    def verify_approved_doctor(self) -> Dict[str, Any]:
        """Mirrors verifyApprovedDoctor() from actions.ts lines 21-42"""
        if not self.db.current_user_id or self.db.current_role != 'authenticated':
            return {"ok": False, "error": "Unauthorized. Please sign in.", "code": "UNAUTHORIZED"}

        acc = self.db.accounts.get(self.db.current_user_id)
        if not acc:
            return {"ok": False, "error": "Account not found.", "code": "FORBIDDEN"}
        if acc.get("role") != "doctor":
            return {"ok": False, "error": "Forbidden. Physician credentials required.", "code": "FORBIDDEN"}
        if acc.get("doctor_status") != "approved":
            return {
                "ok": False,
                "error": "Account Pending Approval - Our team verifies medical credentials within 24 hours. While pending, patient records cannot be accessed."
                if acc.get("doctor_status") == "pending"
                else "Physician account access declined.",
                "code": "PENDING",
            }
        return {"ok": True, "data": {"user": {"id": self.db.current_user_id, "email": acc.get("email")}, "account": acc}}

    def search_patients_action(self, raw_query: Any) -> Dict[str, Any]:
        """Mirrors searchPatientsAction() from actions.ts lines 68-108"""
        auth = self.verify_approved_doctor()
        if not auth["ok"]:
            return {"ok": False, "error": auth["error"]}

        # Defensive type check
        if not isinstance(raw_query, str):
            try:
                q = (raw_query or '').strip()
            except Exception as e:
                return {"ok": False, "error": str(e)}
        else:
            q = (raw_query or '').strip()

        if len(q) < 2:
            return {"ok": True, "data": []}
        if len(q) > 100:
            return {"ok": False, "error": "Query exceeds 100 characters."}

        digits = re.sub(r'\D', '', q)
        results = []

        if len(digits) >= 7:
            # Phone search
            for pid, prof in self.db.patient_profiles.items():
                acc = self.db.accounts.get(pid, {})
                c_phone = acc.get("contact_phone", "")
                em_phone = prof.get("emergency_contact_phone", "")
                if digits in re.sub(r'\D', '', c_phone) or digits in re.sub(r'\D', '', em_phone):
                    cr = self.db.clinical_records.get(pid, {})
                    results.append({
                        "patient_id": pid, "patient_code": prof["patient_code"], "qr_token": prof["qr_token"],
                        "full_name": acc.get("full_name", "Unknown"), "age": prof["age"], "blood_group": prof["blood_group"],
                        "contact_phone": c_phone, "emergency_contact_name": prof["emergency_contact_name"],
                        "emergency_contact_phone": prof["emergency_contact_phone"],
                        "emergency_contact_relation": prof["emergency_contact_relation"],
                        "is_doctor_verified": cr.get("is_doctor_verified", False)
                    })
            return {"ok": True, "data": results[:20]}

        if re.match(r'^UMB-[A-Za-z0-9]{6}$', q, re.IGNORECASE):
            # Patient code search
            for pid, prof in self.db.patient_profiles.items():
                if prof["patient_code"].upper() == q.upper():
                    acc = self.db.accounts.get(pid, {})
                    cr = self.db.clinical_records.get(pid, {})
                    results.append({
                        "patient_id": pid, "patient_code": prof["patient_code"], "qr_token": prof["qr_token"],
                        "full_name": acc.get("full_name", "Unknown"), "age": prof["age"], "blood_group": prof["blood_group"],
                        "contact_phone": acc.get("contact_phone", ""), "emergency_contact_name": prof["emergency_contact_name"],
                        "emergency_contact_phone": prof["emergency_contact_phone"],
                        "emergency_contact_relation": prof["emergency_contact_relation"],
                        "is_doctor_verified": cr.get("is_doctor_verified", False)
                    })
            return {"ok": True, "data": results[:20]}

        if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', q, re.IGNORECASE):
            # QR token search
            for pid, prof in self.db.patient_profiles.items():
                if prof["qr_token"].lower() == q.lower():
                    acc = self.db.accounts.get(pid, {})
                    cr = self.db.clinical_records.get(pid, {})
                    results.append({
                        "patient_id": pid, "patient_code": prof["patient_code"], "qr_token": prof["qr_token"],
                        "full_name": acc.get("full_name", "Unknown"), "age": prof["age"], "blood_group": prof["blood_group"],
                        "contact_phone": acc.get("contact_phone", ""), "emergency_contact_name": prof["emergency_contact_name"],
                        "emergency_contact_phone": prof["emergency_contact_phone"],
                        "emergency_contact_relation": prof["emergency_contact_relation"],
                        "is_doctor_verified": cr.get("is_doctor_verified", False)
                    })
            return {"ok": True, "data": results[:20]}

        # Name search with escaped term
        clean_q = escape_search_term(q).lower()
        for pid, prof in self.db.patient_profiles.items():
            acc = self.db.accounts.get(pid, {})
            name = acc.get("full_name", "").lower()
            if clean_q in name:
                cr = self.db.clinical_records.get(pid, {})
                results.append({
                    "patient_id": pid, "patient_code": prof["patient_code"], "qr_token": prof["qr_token"],
                    "full_name": acc.get("full_name", "Unknown"), "age": prof["age"], "blood_group": prof["blood_group"],
                    "contact_phone": acc.get("contact_phone", ""), "emergency_contact_name": prof["emergency_contact_name"],
                    "emergency_contact_phone": prof["emergency_contact_phone"],
                    "emergency_contact_relation": prof["emergency_contact_relation"],
                    "is_doctor_verified": cr.get("is_doctor_verified", False)
                })
        return {"ok": True, "data": results[:20]}

    def get_patient_clinical_record_action(self, patient_id: str) -> Dict[str, Any]:
        """Mirrors getPatientClinicalRecordAction() from actions.ts lines 115-132"""
        auth = self.verify_approved_doctor()
        if not auth["ok"]:
            return {"ok": False, "error": auth["error"]}

        prof = self.db.patient_profiles.get(patient_id)
        if not prof:
            return {"ok": False, "error": "Patient profile not found."}

        cr = self.db.clinical_records.get(patient_id)
        if not cr:
            return {"ok": False, "error": "Clinical record not found."}

        acc = self.db.accounts.get(patient_id, {})
        return {
            "ok": True,
            "data": {
                "profile": {
                    "patient_id": patient_id, "patient_code": prof["patient_code"], "qr_token": prof["qr_token"],
                    "full_name": acc.get("full_name", "Unknown"), "age": prof["age"], "blood_group": prof["blood_group"],
                    "contact_phone": acc.get("contact_phone", ""), "emergency_contact_name": prof["emergency_contact_name"],
                    "emergency_contact_phone": prof["emergency_contact_phone"],
                    "emergency_contact_relation": prof["emergency_contact_relation"],
                    "is_doctor_verified": cr["is_doctor_verified"]
                },
                "clinical": dict(cr)
            }
        }

    def update_clinical_record_action(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mirrors updateClinicalRecordAction() from actions.ts lines 134-178"""
        auth = self.verify_approved_doctor()
        if not auth["ok"]:
            return {"ok": False, "error": auth["error"]}

        # Schema Validation: doctorClinicalRecordUpdateSchema
        if not isinstance(raw_data, dict):
            return {"ok": False, "error": "Invalid clinical update."}
        
        patient_id = raw_data.get("patient_id")
        expected_updated_at = raw_data.get("expectedUpdatedAt")
        if not patient_id or not expected_updated_at:
            return {"ok": False, "error": "patient_id and expectedUpdatedAt are required."}

        # Check existing record
        existing = self.db.clinical_records.get(patient_id)
        if not existing:
            return {"ok": False, "error": "Record not found or update could not be applied."}

        # Optimistic Concurrency Control Check: .eq('updated_at', expectedUpdatedAt)
        if existing["updated_at"] != expected_updated_at:
            return {
                "ok": False,
                "conflict": True,
                "error": "Clinical Record Conflict: This record was modified by another healthcare provider while you were editing. Please refresh to load the latest data."
            }

        # Extract only permitted columns (D3 grants whitelist)
        medical_conditions = raw_data.get("medical_conditions", existing["medical_conditions"])
        current_medication = raw_data.get("current_medication", existing["current_medication"])
        previous_surgeries = raw_data.get("previous_surgeries", existing["previous_surgeries"])
        allergies = raw_data.get("allergies", existing["allergies"])

        updated_row = dict(existing)
        updated_row["medical_conditions"] = list(medical_conditions)
        updated_row["current_medication"] = list(current_medication)
        updated_row["previous_surgeries"] = list(previous_surgeries)
        updated_row["allergies"] = list(allergies)

        # Execute DB trigger trg_stamp_clinical
        final_record = self.db.trigger_stamp_clinical(existing, updated_row)
        self.db.clinical_records[patient_id] = final_record

        return {"ok": True, "data": final_record}

    def get_doctor_appointments_action(self, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Mirrors getDoctorAppointmentsAction() from actions.ts lines 188-221"""
        auth = self.verify_approved_doctor()
        if not auth["ok"]:
            return {"ok": False, "error": auth["error"]}

        doc_id = auth["data"]["user"]["id"]
        results = []
        for aid, appt in self.db.appointments.items():
            if appt["doctor_id"] == doc_id:
                if options and options.get("status") and appt["status"] != options["status"]:
                    continue
                if options and options.get("patientId") and appt["patient_id"] != options["patientId"]:
                    continue
                
                pat_id = appt["patient_id"]
                acc = self.db.accounts.get(pat_id, {})
                prof = self.db.patient_profiles.get(pat_id, {})
                results.append({
                    "id": aid, "patient_id": pat_id, "scheduled_at": appt["scheduled_at"],
                    "status": appt["status"], "reason": appt["reason"], "clinical_notes": appt.get("clinical_notes"),
                    "created_at": appt["created_at"],
                    "patient": {
                        "fullName": acc.get("full_name", "Unknown"), "contactPhone": acc.get("contact_phone", ""),
                        "patientCode": prof.get("patient_code", "N/A"), "age": prof.get("age", 0),
                        "bloodGroup": prof.get("blood_group", "Unknown")
                    }
                })
        return {"ok": True, "data": sorted(results, key=lambda x: x["scheduled_at"])}

    def create_appointment_action(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mirrors createAppointmentAction() from actions.ts lines 223-246"""
        auth = self.verify_approved_doctor()
        if not auth["ok"]:
            return {"ok": False, "error": auth["error"]}

        if not isinstance(raw_data, dict):
            return {"ok": False, "error": "Invalid appointment input."}

        patient_id = raw_data.get("patient_id")
        scheduled_at = raw_data.get("scheduled_at")
        reason = (raw_data.get("reason") or "").strip()
        clinical_notes = raw_data.get("clinical_notes")

        if not patient_id or not scheduled_at or len(reason) < 2 or len(reason) > 200:
            return {"ok": False, "error": "Invalid appointment input fields."}

        # Postgres RLS Check: ap_insert_doctor check check ((select public.is_approved_doctor()) and doctor_id = (select auth.uid()))
        doctor_id = auth["data"]["user"]["id"]
        if not self.db.rls_can_insert_appointment(doctor_id):
            return {"ok": False, "error": "RLS policy violation on appointment insert."}

        new_id = str(uuid.uuid4())
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        appt = {
            "id": new_id,
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "scheduled_at": scheduled_at,
            "status": "scheduled",
            "reason": reason,
            "clinical_notes": clinical_notes.strip() if clinical_notes else None,
            "created_at": created_at,
            "updated_at": created_at
        }
        self.db.appointments[new_id] = appt
        return {"ok": True, "data": appt}

    def update_appointment_status_action(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mirrors updateAppointmentStatusAction() from actions.ts lines 248-270"""
        auth = self.verify_approved_doctor()
        if not auth["ok"]:
            return {"ok": False, "error": auth["error"]}

        if not isinstance(raw_data, dict):
            return {"ok": False, "error": "Invalid status update."}

        appt_id = raw_data.get("appointment_id")
        status = raw_data.get("status")
        notes = raw_data.get("clinical_notes")

        if not appt_id or status not in ["scheduled", "completed", "cancelled"]:
            return {"ok": False, "error": "Invalid appointment status update input."}

        existing = self.db.appointments.get(appt_id)
        if not existing:
            return {"ok": False, "error": "Appointment not found."}

        updated = dict(existing)
        updated["status"] = status
        if notes is not None:
            updated["clinical_notes"] = notes
        updated["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Fire DB trigger trg_appointment_completed
        self.db.trigger_appointment_completed(existing, updated)
        self.db.appointments[appt_id] = updated

        return {"ok": True, "data": updated}

# ==============================================================================
# TEST SUITE 1: PostgREST Operator & SQL Injection Attacks on Patient Search
# ==============================================================================

def run_suite_1_injection_attacks():
    print("\n" + "=" * 80)
    print("SUITE 1: PostgREST Operator & SQL Injection Attacks on Patient Search")
    print("=" * 80)

    db = PostgresOracle()
    db.seed_data()
    harness = DoctorActionHarness(db)

    # Set approved doctor context
    doc_id = "00000000-0000-0000-0000-0000000000d1"
    db.set_session(doc_id)

    # 1.1 Direct PostgREST filter injection attempts
    postgrest_payloads = [
        (",full_name.neq.null", "Comma-separated filter injection"),
        ("(status.eq.approved)", "Parenthesized subfilter injection"),
        (",id.eq.null", "Identifier breakout attempt"),
        ("') or true --", "SQL quote termination injection"),
        ("1; DROP TABLE accounts; --", "SQL batch command injection"),
        ("full_name.eq.admin", "Direct PostgREST column operator"),
        ("&age=gt.0", "Query string parameter pollution"),
        ("?select=*", "Resource embedding breakout"),
        ("order=id.desc", "Sort clause injection"),
        ("limit=1000", "Row limit override attempt"),
    ]

    for payload, label in postgrest_payloads:
        escaped = escape_search_term(payload)
        # Verify that delimiters like , ( ) % _ are completely stripped
        delimiters_present = any(c in escaped for c in [',', '(', ')', '%', '_'])
        record("INJECTION_1.1", f"Sanitizer strips delimiters for: {label}", not delimiters_present, f"Input: '{payload}' -> Sanitized: '{escaped}'")

        # Test action execution
        res = harness.search_patients_action(payload)
        record("INJECTION_1.1", f"Action execution safe against: {label}", res["ok"] is True, f"Returned {len(res.get('data', []))} records")

    # 1.2 Deep wildcard flooding & ReDoS stress test
    wildcard_payloads = [
        ("%%%%%", "Percent wildcard flood"),
        ("_____", "Underscore single-char flood"),
        ("%_%_%_%_%", "Mixed wildcard chain"),
        ("%%__%%__%%__", "Alternating deep wildcard burst"),
        ("\\%\\_\\%\\_\\%", "Backslash-escaped wildcard injection"),
        ("%" * 90, "90-character wildcard saturation"),
        ("_" * 90, "90-character underscore saturation"),
    ]

    for payload, label in wildcard_payloads:
        escaped = escape_search_term(payload)
        clean = ("%" not in escaped) and ("_" not in escaped)
        record("INJECTION_1.2", f"Wildcards neutralized for: {label}", clean, f"Sanitized: '{escaped}'")

        res = harness.search_patients_action(payload)
        record("INJECTION_1.2", f"Action handles wildcard flood safely: {label}", res["ok"] is True)

    # 1.3 Boundary Length & Input Types
    # Length < 2
    res_short = harness.search_patients_action("a")
    record("INJECTION_1.3", "Query < 2 chars returns empty array with ok=true", res_short["ok"] is True and len(res_short["data"]) == 0)

    res_empty = harness.search_patients_action("")
    record("INJECTION_1.3", "Empty query returns empty array with ok=true", res_empty["ok"] is True and len(res_empty["data"]) == 0)

    # Length > 100
    res_long = harness.search_patients_action("x" * 101)
    record("INJECTION_1.3", "Query > 100 chars rejected with error", res_long["ok"] is False and "exceeds 100" in res_long["error"])

    # Non-string defensive tests
    res_none = harness.search_patients_action(None)
    record("INJECTION_1.3", "None/null query handled gracefully", res_none["ok"] is True and len(res_none["data"]) == 0)

    # 1.4 Route Classification Integrity & Shadowing Flaws
    # Patient Code route
    res_code = harness.search_patients_action("UMB-ALX001")
    code_match = res_code["ok"] and len(res_code["data"]) == 1 and res_code["data"][0]["patient_code"] == "UMB-ALX001"
    record("INJECTION_1.4", "Patient code route correctly classifies UMB-ALX001", code_match)

    # QR Token route with >= 7 numeric digits (Standard UUID v4)
    # Target UUID: a1a1a1a1-a1a1-4a1a-8a1a-a1a1a1a1a1a1 (contains 16 numeric digits)
    res_token = harness.search_patients_action("a1a1a1a1-a1a1-4a1a-8a1a-a1a1a1a1a1a1")
    token_match = res_token["ok"] and len(res_token["data"]) == 1 and res_token["data"][0]["patient_id"] == "00000000-0000-0000-0000-0000000000a1"
    fail_reason = (
        f"Returned {len(res_token.get('data', []))} records. Precedence bug in actions.ts: "
        f"digits.length >= 7 (phone search) executes before UUID regex, routing standard UUIDs to phone search!"
    )
    record("INJECTION_1.4", "QR token route correctly classifies valid UUID v4 with >=7 digits", token_match,
           details="" if token_match else fail_reason)

    # QR Token route with rare < 7 numeric digits (e.g. all letters)
    # Target UUID with 1 digit: aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa
    # Note: Alex Morgan's token has 16 digits, so it was shadowed.

    # Phone Number route
    res_phone = harness.search_patients_action("5551234")
    phone_match = res_phone["ok"] and len(res_phone["data"]) == 1 and res_phone["data"][0]["patient_id"] == "00000000-0000-0000-0000-0000000000a1"
    record("INJECTION_1.4", "Phone digits >= 7 route correctly matches patient phone", phone_match)

    # Name ILIKE route with valid name
    res_name = harness.search_patients_action("Alex")
    name_match = res_name["ok"] and len(res_name["data"]) == 1 and res_name["data"][0]["full_name"] == "Alex Morgan"
    record("INJECTION_1.4", "Name search correctly matches 'Alex Morgan'", name_match)

    # Wildcard Flood Match-All Query Probe
    res_flood = harness.search_patients_action("%%%%%")
    # If wildcards are stripped to empty string, it executes ilike '%%' which matches ALL records
    flood_matches_all = res_flood["ok"] and len(res_flood.get("data", [])) > 0
    record("INJECTION_1.5", "Wildcard flood '%%%%%' neutralizes to empty string without matching all patient records",
           not flood_matches_all,
           f"Returned {len(res_flood.get('data', []))} records via unconstrained '%%' query! (Should return 0 records)")


# ==============================================================================
# TEST SUITE 2: Authorization & RBAC Bypass Attacks
# ==============================================================================

def run_suite_2_rbac_bypass():
    print("\n" + "=" * 80)
    print("SUITE 2: Authorization & RBAC Bypass Attacks")
    print("=" * 80)

    db = PostgresOracle()
    db.seed_data()
    harness = DoctorActionHarness(db)

    pat_id = "00000000-0000-0000-0000-0000000000a1"
    pending_doc_id = "00000000-0000-0000-0000-0000000000d3"
    declined_doc_id = "00000000-0000-0000-0000-0000000000d4"

    # Action invocation helpers
    actions = [
        ("searchPatientsAction", lambda h: h.search_patients_action("Alex")),
        ("getPatientClinicalRecordAction", lambda h: h.get_patient_clinical_record_action(pat_id)),
        ("updateClinicalRecordAction", lambda h: h.update_clinical_record_action({
            "patient_id": pat_id, "expectedUpdatedAt": "2026-01-01T10:00:00Z", "medical_conditions": ["Hacked"]
        })),
        ("getDoctorAppointmentsAction", lambda h: h.get_doctor_appointments_action()),
        ("createAppointmentAction", lambda h: h.create_appointment_action({
            "patient_id": pat_id, "scheduled_at": "2026-03-01T10:00:00Z", "reason": "Checkup"
        })),
        ("updateAppointmentStatusAction", lambda h: h.update_appointment_status_action({
            "appointment_id": "00000000-0000-0000-0000-0000000000e1", "status": "completed"
        })),
    ]

    # 2.1 Unauthenticated Caller (anon)
    db.set_session(None, role='anon')
    for action_name, fn in actions:
        res = fn(harness)
        record("RBAC_2.1_ANON", f"{action_name} rejects unauthenticated caller",
               res["ok"] is False and "Unauthorized" in res["error"],
               f"Error: '{res.get('error')}'")

    # 2.2 Patient User Calling Doctor Actions
    db.set_session(pat_id, role='authenticated')
    for action_name, fn in actions:
        res = fn(harness)
        record("RBAC_2.2_PATIENT", f"{action_name} rejects patient caller with Forbidden",
               res["ok"] is False and "Physician credentials required" in res["error"],
               f"Error: '{res.get('error')}'")

    # 2.3 Pending Doctor Calling Doctor Actions (DECISIONS D1)
    db.set_session(pending_doc_id, role='authenticated')
    for action_name, fn in actions:
        res = fn(harness)
        record("RBAC_2.3_PENDING", f"{action_name} rejects pending doctor caller with D1 pending notice",
               res["ok"] is False and "Account Pending Approval" in res["error"],
               f"Error: '{res.get('error')}'")

    # 2.4 Declined Doctor Calling Doctor Actions
    db.set_session(declined_doc_id, role='authenticated')
    for action_name, fn in actions:
        res = fn(harness)
        record("RBAC_2.4_DECLINED", f"{action_name} rejects declined doctor caller",
               res["ok"] is False and "declined" in res["error"],
               f"Error: '{res.get('error')}'")

    # 2.5 Database RLS direct policy tests
    db.set_session(None, role='anon')
    record("RLS_2.5_ANON", "Anon denied direct SELECT on patient_profiles", not db.rls_can_select_patient_profile(pat_id))
    record("RLS_2.5_ANON", "Anon denied direct SELECT on clinical_records", not db.rls_can_select_clinical_record(pat_id))
    record("RLS_2.5_ANON", "Anon denied direct UPDATE on clinical_records", not db.rls_can_update_clinical_record())
    record("RLS_2.5_ANON", "Anon denied direct INSERT on appointments", not db.rls_can_insert_appointment("any-id"))

    db.set_session(pending_doc_id, role='authenticated')
    record("RLS_2.5_PENDING", "Pending doctor reads 0 patient profiles via RLS", not db.rls_can_select_patient_profile(pat_id))
    record("RLS_2.5_PENDING", "Pending doctor reads 0 clinical records via RLS", not db.rls_can_select_clinical_record(pat_id))
    record("RLS_2.5_PENDING", "Pending doctor cannot update clinical records via RLS", not db.rls_can_update_clinical_record())
    record("RLS_2.5_PENDING", "Pending doctor cannot insert appointments via RLS", not db.rls_can_insert_appointment(pending_doc_id))

# ==============================================================================
# TEST SUITE 3: Audit Stamp Tampering & Verification Spoofing Attacks
# ==============================================================================

def run_suite_3_audit_stamp_tampering():
    print("\n" + "=" * 80)
    print("SUITE 3: Audit Stamp Tampering & Verification Spoofing Attacks")
    print("=" * 80)

    db = PostgresOracle()
    db.seed_data()
    harness = DoctorActionHarness(db)

    doc_a_id = "00000000-0000-0000-0000-0000000000d1"
    doc_b_id = "00000000-0000-0000-0000-0000000000d2"
    pat_id = "00000000-0000-0000-0000-0000000000a1"

    # Authenticate as Doctor A
    db.set_session(doc_a_id)
    initial_cr = db.clinical_records[pat_id]
    record("STAMP_3.1", "Initial clinical record is unverified (is_doctor_verified = False)",
           initial_cr["is_doctor_verified"] is False)

    # 3.1 Attempt to inject is_doctor_verified = false and forged last_updated_by_doctor_id in update payload
    forged_doctor_id = "00000000-0000-0000-0000-999999999999"
    malicious_payload = {
        "patient_id": pat_id,
        "expectedUpdatedAt": initial_cr["updated_at"],
        "medical_conditions": ["Mild Asthma", "Controlled"],
        "allergies": ["Penicillin"],
        "is_doctor_verified": False,           # Attacker attempts to prevent verification
        "last_updated_by_doctor_id": forged_doctor_id,  # Attacker attempts to forge doctor attribution
        "updated_at": "1970-01-01T00:00:00Z"   # Attacker attempts to forge timestamp
    }

    res_tamper = harness.update_clinical_record_action(malicious_payload)
    record("STAMP_3.1", "updateClinicalRecordAction succeeds", res_tamper["ok"] is True)

    updated_cr = db.clinical_records[pat_id]

    # Verify that database trigger stamped is_doctor_verified = true
    record("STAMP_3.1", "DB trigger trg_stamp_clinical overrides payload: is_doctor_verified is TRUE",
           updated_cr["is_doctor_verified"] is True)

    # Verify that last_updated_by_doctor_id is Doctor A (authenticated caller), NOT forged ID
    record("STAMP_3.1", "DB trigger forces last_updated_by_doctor_id = auth.uid() (Doctor A)",
           updated_cr["last_updated_by_doctor_id"] == doc_a_id,
           f"Expected: {doc_a_id}, Actual: {updated_cr['last_updated_by_doctor_id']}")

    # Verify updated_at was updated to now, NOT 1970
    record("STAMP_3.1", "DB trigger forces updated_at = now()",
           updated_cr["updated_at"] != "1970-01-01T00:00:00Z")

    # 3.2 Verify Column-Level Grants in Schema
    schema_sql_path = os.path.join(ROOT_DIR, "supabase/migrations/0001_umbrella_schema.sql")
    with open(schema_sql_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    cr_grant_match = bool(re.search(
        r'grant\s+update\s*\(([^)]+)\)\s+on\s+public\.clinical_records\s+to\s+authenticated',
        schema_sql,
        re.IGNORECASE
    ))
    record("STAMP_3.2", "Schema specifies granular column update grants on clinical_records", cr_grant_match)

    if cr_grant_match:
        granted_cols = re.search(r'grant\s+update\s*\(([^)]+)\)\s+on\s+public\.clinical_records', schema_sql, re.IGNORECASE).group(1)
        no_verified_grant = "is_doctor_verified" not in granted_cols
        no_doc_id_grant = "last_updated_by_doctor_id" not in granted_cols
        record("STAMP_3.2", "is_doctor_verified is NOT granted for direct client UPDATE", no_verified_grant)
        record("STAMP_3.2", "last_updated_by_doctor_id is NOT granted for direct client UPDATE", no_doc_id_grant)

    # 3.3 Appointment Doctor Spoofing Attack
    # Doctor A attempts to insert appointment with doctor_id = Doctor B
    appt_spoof_payload = {
        "patient_id": pat_id,
        "scheduled_at": "2026-03-01T15:00:00Z",
        "reason": "Spoofed appointment consultation",
        "doctor_id": doc_b_id  # Spoofing Doctor B
    }
    res_appt = harness.create_appointment_action(appt_spoof_payload)
    record("STAMP_3.3", "createAppointmentAction sets doctor_id = auth.uid() ignoring spoofed payload",
           res_appt["ok"] is True and res_appt["data"]["doctor_id"] == doc_a_id,
           f"Assigned doctor_id: {res_appt.get('data', {}).get('doctor_id')}")

    # 3.4 Appointment Completion does NOT flip is_doctor_verified (DECISIONS D8)
    # Reset patient 1 clinical record to unverified
    db.clinical_records[pat_id]["is_doctor_verified"] = False
    new_appt_id = res_appt["data"]["id"]

    res_complete = harness.update_appointment_status_action({
        "appointment_id": new_appt_id,
        "status": "completed",
        "clinical_notes": "Completed patient visit summary"
    })
    record("STAMP_3.4", "updateAppointmentStatusAction completes appointment", res_complete["ok"] is True)

    after_complete_cr = db.clinical_records[pat_id]
    record("STAMP_3.4", "Appointment completion syncs last_appointment_date and summary",
           after_complete_cr["last_appointment_date"] == "2026-03-01T15:00:00Z" and
           after_complete_cr["last_appointment_summary"] == "Completed patient visit summary")

    record("STAMP_3.4", "CRITICAL INVARIANT D8: Appointment completion does NOT flip is_doctor_verified",
           after_complete_cr["is_doctor_verified"] is False)

# ==============================================================================
# TEST SUITE 4: Concurrency Collision & Stale Update Attacks
# ==============================================================================

def run_suite_4_concurrency_attacks():
    print("\n" + "=" * 80)
    print("SUITE 4: Concurrency Collision & Stale Update Attacks (Optimistic Locking)")
    print("=" * 80)

    db = PostgresOracle()
    db.seed_data()
    harness = DoctorActionHarness(db)

    doc_a_id = "00000000-0000-0000-0000-0000000000d1"
    doc_b_id = "00000000-0000-0000-0000-0000000000d2"
    pat_id = "00000000-0000-0000-0000-0000000000a1"

    # Step 1: Both Doctor A and Doctor B load the record at T0
    db.set_session(doc_a_id)
    doc_a_view = harness.get_patient_clinical_recordAction(pat_id) if hasattr(harness, 'get_patient_clinical_recordAction') else harness.get_patient_clinical_record_action(pat_id)
    t0_timestamp = doc_a_view["data"]["clinical"]["updated_at"]
    record("CONCUR_4.1", f"Doctor A loads record at T0: {t0_timestamp}", doc_a_view["ok"] is True)

    db.set_session(doc_b_id)
    doc_b_view = harness.get_patient_clinical_record_action(pat_id)
    record("CONCUR_4.1", f"Doctor B loads same record with expectedUpdatedAt = T0", doc_b_view["data"]["clinical"]["updated_at"] == t0_timestamp)

    # Step 2: Doctor B submits changes at T1 (adds allergy "Latex" and condition "Eczema")
    res_b_save = harness.update_clinical_record_action({
        "patient_id": pat_id,
        "expectedUpdatedAt": t0_timestamp,
        "medical_conditions": ["Mild Asthma", "Eczema"],
        "allergies": ["Penicillin", "Latex"],
        "current_medication": doc_b_view["data"]["clinical"]["current_medication"],
        "previous_surgeries": doc_b_view["data"]["clinical"]["previous_surgeries"]
    })
    t1_timestamp = res_b_save["data"]["updated_at"]
    record("CONCUR_4.2", f"Doctor B saves changes successfully at T1: {t1_timestamp}",
           res_b_save["ok"] is True and t1_timestamp != t0_timestamp)

    # Step 3: Doctor A (who still has T0 timestamp) attempts to submit changes at T2
    db.set_session(doc_a_id)
    res_a_stale_save = harness.update_clinical_record_action({
        "patient_id": pat_id,
        "expectedUpdatedAt": t0_timestamp,  # STALE TIMESTAMP!
        "medical_conditions": ["Mild Asthma", "Hypertension"],
        "allergies": ["Penicillin", "Aspirin"],
        "current_medication": doc_a_view["data"]["clinical"]["current_medication"],
        "previous_surgeries": doc_a_view["data"]["clinical"]["previous_surgeries"]
    })

    # Step 4: Verify Doctor A's update fails with conflict: true
    is_conflict = (res_a_stale_save["ok"] is False and
                   res_a_stale_save.get("conflict") is True and
                   "Conflict" in res_a_stale_save.get("error", ""))
    record("CONCUR_4.3", "Doctor A's stale update is rejected with conflict = True",
           is_conflict, f"Response: {res_a_stale_save}")

    # Step 5: Verify Doctor B's data was NOT overwritten
    current_cr = db.clinical_records[pat_id]
    data_preserved = ("Latex" in current_cr["allergies"] and
                      "Eczema" in current_cr["medical_conditions"] and
                      "Aspirin" not in current_cr["allergies"] and
                      "Hypertension" not in current_cr["medical_conditions"])
    record("CONCUR_4.4", "Doctor B's clinical notes/allergies preserved (zero lost updates)", data_preserved)

    # Step 6: Doctor A refreshes to T1 and reapplies
    res_a_fresh_save = harness.update_clinical_record_action({
        "patient_id": pat_id,
        "expectedUpdatedAt": t1_timestamp,  # FRESH TIMESTAMP
        "medical_conditions": current_cr["medical_conditions"] + ["Hypertension"],
        "allergies": current_cr["allergies"] + ["Aspirin"],
        "current_medication": current_cr["current_medication"],
        "previous_surgeries": current_cr["previous_surgeries"]
    })
    record("CONCUR_4.5", "Doctor A saves cleanly after refreshing to latest timestamp",
           res_a_fresh_save["ok"] is True and "Hypertension" in res_a_fresh_save["data"]["medical_conditions"])

# ==============================================================================
# TEST SUITE 5: Invariant N4 Secret Leak & Security Invariant Sweep
# ==============================================================================

def run_suite_5_secret_leak_and_invariants():
    print("\n" + "=" * 80)
    print("SUITE 5: Invariant N4 Secret Leak & Security Invariant Sweep")
    print("=" * 80)

    # 5.1 Sweep for SUPABASE_SERVICE_ROLE_KEY across all src/ and portal files
    src_dir = os.path.join(ROOT_DIR, "src")
    doctor_portal_files = []
    service_role_leaks = []
    get_session_leaks = []
    dangerously_set_html_leaks = []

    for root, dirs, files in os.walk(src_dir):
        for f in files:
            if f.endswith(('.ts', '.tsx', '.js', '.jsx')):
                fp = os.path.join(root, f)
                rel_path = os.path.relpath(fp, ROOT_DIR)
                if "doctor" in rel_path or "actions.ts" in rel_path:
                    doctor_portal_files.append(rel_path)
                with open(fp, "r", encoding="utf-8") as handle:
                    content = handle.read()
                    if "SUPABASE_SERVICE_ROLE_KEY" in content or "service_role" in content:
                        service_role_leaks.append(rel_path)
                    if "getSession()" in content:
                        get_session_leaks.append(rel_path)
                    if "dangerouslySetInnerHTML" in content and "doctor" in rel_path:
                        dangerously_set_html_leaks.append(rel_path)

    record("INVARIANT_5.1", f"Zero service_role references in src/ directory",
           len(service_role_leaks) == 0, f"Violations: {service_role_leaks}")

    record("INVARIANT_5.2", "Zero getSession() calls in doctor portal (N3 enforces getUser())",
           len(get_session_leaks) == 0, f"Violations: {get_session_leaks}")

    record("INVARIANT_5.3", "Zero dangerouslySetInnerHTML in doctor portal components",
           len(dangerously_set_html_leaks) == 0, f"Violations: {dangerously_set_html_leaks}")

    # 5.2 Check .env.example
    env_example = os.path.join(ROOT_DIR, ".env.example")
    env_clean = True
    if os.path.isfile(env_example):
        with open(env_example, "r", encoding="utf-8") as f:
            env_content = f.read()
            if "service_role" in env_content.lower():
                env_clean = False
    record("INVARIANT_5.4", ".env.example contains no service_role key", env_clean)

    # 5.3 Verify Invariant N2: Persistent Read-Only Safety Banner
    banner_file = os.path.join(ROOT_DIR, "src/components/doctor/patient-safety-banner.tsx")
    with open(banner_file, "r", encoding="utf-8") as f:
        banner_content = f.read()

    # Must contain sticky positioning
    sticky_banner = "sticky top-0 z-30" in banner_content or ("sticky" in banner_content and "z-30" in banner_content)
    record("INVARIANT_5.5", "Safety banner enforces sticky top-0 z-30 positioning (N2)", sticky_banner)

    # Must display Name, Age, BloodGroup, Emergency Phone
    mandatory_fields = all(x in banner_content for x in ["fullName", "age", "bloodGroup", "emergencyContactPhone"])
    record("INVARIANT_5.6", "Safety banner renders all N2 required clinical fields", mandatory_fields)

    # Must contain ZERO <input> or <textarea> elements (strictly read-only)
    read_only_clean = ("<input" not in banner_content) and ("<textarea" not in banner_content)
    record("INVARIANT_5.7", "Safety banner is strictly read-only with 0 input/textarea elements", read_only_clean)

    # 5.4 Check tel: link phone sanitization (Security rule 02-security-privacy.md item 6)
    tel_sanitized = "sanitizeTel" in banner_content and "href={`tel:${cleanPhone}`}" in banner_content
    record("INVARIANT_5.8", "Emergency phone link strictly sanitizes tel: URL", tel_sanitized)

# ==============================================================================
# MAIN TEST EXECUTION & REPORTING
# ==============================================================================

def main():
    print("=" * 80)
    print("UMBRELLA DOCTOR PORTAL EMPIRICAL ADVERSARIAL PENETRATION SUITE")
    print("Challenger M6-1 | Roles: critic, specialist")
    print("=" * 80)

    run_suite_1_injection_attacks()
    run_suite_2_rbac_bypass()
    run_suite_3_audit_stamp_tampering()
    run_suite_4_concurrency_attacks()
    run_suite_5_secret_leak_and_invariants()

    print("\n" + "=" * 80)
    print("CHALLENGE EXECUTION SUMMARY")
    print(f"Total Tests Run:    {tests_run}")
    print(f"Total Tests Passed: {tests_passed}")
    print(f"Total Tests Failed: {tests_failed}")
    print("=" * 80)

    if tests_failed > 0:
        print("\nFAILURES IDENTIFIED:")
        for suite, name, details in failures:
            print(f"  - [{suite}] {name}: {details}")
        print("\nFINAL VERDICT: REQUEST_CHANGES")
        sys.exit(1)
    else:
        print("\nALL EMPIRICAL ADVERSARIAL PENETRATION TESTS PASSED.")
        print("FINAL VERDICT: APPROVE")
        sys.exit(0)

if __name__ == "__main__":
    main()

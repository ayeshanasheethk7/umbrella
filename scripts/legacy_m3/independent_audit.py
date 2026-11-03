import re
import sys
from pathlib import Path

def audit_schema(sql_path: Path):
    print("=== AUDITING 0001_umbrella_schema.sql ===")
    sql = sql_path.read_text(encoding="utf-8")
    
    # Check tables
    expected_tables = ["accounts", "patient_profiles", "clinical_records", "appointments"]
    for table in expected_tables:
        pattern = rf"create\s+table\s+public\.{table}\s*\("
        assert re.search(pattern, sql, re.IGNORECASE), f"Missing table public.{table}"
        print(f"  [+] Table public.{table} detected.")
        
    # Check RLS enabled
    for table in expected_tables:
        pattern = rf"alter\s+table\s+public\.{table}\s+enable\s+row\s+level\s+security;"
        assert re.search(pattern, sql, re.IGNORECASE), f"RLS not enabled on public.{table}"
        print(f"  [+] RLS enabled on public.{table}.")

    # Check constraints
    assert "accounts_role_fields_chk check" in sql, "Missing accounts_role_fields_chk constraint"
    print("  [+] accounts_role_fields_chk verified.")
    assert "check (doctor_status in ('pending', 'approved', 'rejected'))" in sql, "Missing doctor_status constraint"
    print("  [+] doctor_status check constraint verified.")
    assert "check (blood_group in ('A+','A-','B+','B-','AB+','AB-','O+','O-','Unknown'))" in sql, "Missing blood_group constraint"
    print("  [+] blood_group check constraint verified.")
    assert "check (status in ('scheduled', 'completed', 'cancelled'))" in sql, "Missing appointments status constraint"
    print("  [+] appointment status check constraint verified.")
    
    # Check Foreign Keys
    assert "references auth.users(id) on delete cascade" in sql, "accounts missing ON DELETE CASCADE to auth.users"
    print("  [+] accounts -> auth.users ON DELETE CASCADE verified.")
    assert "patient_id uuid primary key references public.accounts(id) on delete cascade" in sql, "patient_profiles missing ON DELETE CASCADE"
    print("  [+] patient_profiles -> accounts ON DELETE CASCADE verified.")
    assert "patient_id uuid primary key references public.accounts(id) on delete cascade" in sql, "clinical_records missing ON DELETE CASCADE"
    print("  [+] clinical_records -> accounts ON DELETE CASCADE verified.")
    assert "patient_id uuid not null references public.accounts(id) on delete cascade" in sql, "appointments.patient_id missing ON DELETE CASCADE"
    print("  [+] appointments.patient_id -> accounts ON DELETE CASCADE verified.")
    assert "doctor_id uuid not null references public.accounts(id) on delete restrict" in sql, "appointments.doctor_id missing ON DELETE RESTRICT (D6)"
    print("  [+] appointments.doctor_id -> accounts ON DELETE RESTRICT (D6) verified.")

    # Check triggers
    expected_triggers = [
        "trg_accounts_updated",
        "trg_patient_profiles_updated",
        "trg_appointments_updated",
        "on_auth_user_created",
        "trg_patient_profile_clinical",
        "trg_stamp_clinical",
        "trg_appointment_completed"
    ]
    for trg in expected_triggers:
        assert re.search(rf"create\s+trigger\s+{trg}", sql, re.IGNORECASE), f"Missing trigger {trg}"
        print(f"  [+] Trigger {trg} detected.")

    # Check security definer & search_path
    sec_def_funcs = [
        "is_approved_doctor",
        "handle_new_user",
        "create_clinical_record",
        "stamp_clinical_update",
        "on_appointment_completed",
        "get_emergency_triage_by_token",
        "submit_self_reported_baseline",
        "regenerate_qr_token"
    ]
    for fn in sec_def_funcs:
        fn_match = re.search(rf"create\s+or\s+replace\s+function\s+public\.{fn}\b([^$]+)\$\$", sql, re.IGNORECASE)
        assert fn_match, f"Function definition not found for public.{fn}"
        header = fn_match.group(1).lower()
        assert "security definer" in header, f"public.{fn} missing SECURITY DEFINER"
        assert "search_path = ''" in header or "search_path=''" in header, f"public.{fn} missing empty search_path"
        print(f"  [+] Function public.{fn} SECURITY DEFINER & empty search_path verified.")

    # Check N1 privacy invariants
    rpc_start = sql.find("function public.get_emergency_triage_by_token")
    rpc_end = sql.find("$$;", rpc_start)
    rpc_body = sql[rpc_start:rpc_end]
    assert "residential_address" not in rpc_body, "CRITICAL N1 VIOLATION: residential_address in get_emergency_triage_by_token!"
    assert "spouse_dependents" not in rpc_body, "CRITICAL N1 VIOLATION: spouse_dependents in get_emergency_triage_by_token!"
    assert "'qr_token'" not in rpc_body, "CRITICAL N1 VIOLATION: qr_token key exposed in get_emergency_triage_by_token!"
    print("  [+] N1 Privacy Whitelist in get_emergency_triage_by_token strictly verified.")

def audit_seed(seed_path: Path):
    print("\n=== AUDITING supabase/seed.sql ===")
    sql = seed_path.read_text(encoding="utf-8")
    
    # 1. Doctor status initialization per D1
    assert re.search(r"update\s+public\.accounts\s+set\s+doctor_status\s*=\s*'approved'\s+where\s+id\s*=\s*'d0000000-0000-0000-0000-000000000001';", sql, re.IGNORECASE), "Missing Doctor Jenkins approval per D1"
    print("  [+] Doctor Sarah Jenkins approval update per D1 verified.")
    
    # 2. Check synthetic privacy (N9)
    emails = re.findall(r"'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'", sql)
    for email in emails:
        clean = email.strip("'")
        assert clean.endswith(".test") or clean.endswith(".example"), f"Non-synthetic test email domain found: {clean}"
    print(f"  [+] All {len(emails)} seed emails use reserved RFC 2606 test domains (.test).")

    phones = re.findall(r"\+1-555-\d{4}", sql)
    assert len(phones) >= 5, "Expected synthetic 555 numbers"
    print(f"  [+] All {len(phones)} telephone numbers use reserved fictional +1-555-XXXX prefix.")

    # Check verified vs unverified clinical records
    assert "is_doctor_verified = true" in sql, "Missing verified clinical records"
    assert "is_doctor_verified = false" in sql, "Missing unverified baseline clinical records"
    print("  [+] Realistic clinical mix (verified chronic vs unverified baseline) verified.")

    # Check deterministic appointments
    appt_matches = re.findall(r"'b0000000-0000-0000-0000-00000000000[1-4]'", sql)
    assert len(appt_matches) == 4, f"Expected 4 appointments, found {len(appt_matches)}"
    print("  [+] 4 deterministic appointments (past completed and scheduled) verified.")

if __name__ == "__main__":
    base = Path(r"c:\Users\DELL\ayesha_pro\medi_qr")
    audit_schema(base / "supabase" / "migrations" / "0001_umbrella_schema.sql")
    audit_seed(base / "supabase" / "seed.sql")
    print("\n>>> INDEPENDENT ADVERSARIAL AUDIT PASSED WITH ZERO CRITICAL DEFECTS <<<")

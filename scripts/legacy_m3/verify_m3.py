import re
import sys
from pathlib import Path

def test_schema(migration_path: Path):
    content = migration_path.read_text(encoding="utf-8")
    
    # 1. Extension
    assert 'create extension if not exists "pgcrypto"' in content, "Missing pgcrypto extension"
    
    # 2. Enum
    assert "create type public.user_role as enum ('patient', 'doctor');" in content, "Missing user_role enum"
    
    # 3. Core tables
    tables = ['accounts', 'patient_profiles', 'clinical_records', 'appointments']
    for t in tables:
        assert f"create table public.{t}" in content, f"Missing table {t}"
    
    # 4. Check constraints
    assert "accounts_role_fields_chk check" in content, "Missing accounts_role_fields_chk"
    assert "check (doctor_status in ('pending', 'approved', 'rejected'))" in content, "Missing doctor_status check"
    assert "check (status in ('scheduled', 'completed', 'cancelled'))" in content, "Missing appointment status check"
    assert "residential_address text not null default ''" in content, "Missing residential_address per D4"
    assert "on delete restrict" in content, "appointments.doctor_id must be on delete restrict per D6"

    # 5. Functions & Triggers
    assert "create or replace function public.is_approved_doctor()" in content, "Missing is_approved_doctor function"
    assert "set search_path = ''" in content, "Function search_path must be empty"
    assert "security definer" in content, "Security definer missing on helper"
    assert "create trigger trg_stamp_clinical" in content, "Missing clinical verification stamp trigger"
    assert "create trigger trg_appointment_completed" in content, "Missing appointment completion trigger"
    assert "create trigger on_auth_user_created" in content, "Missing signup trigger"

    # 6. RLS
    for t in tables:
        assert f"alter table public.{t} enable row level security;" in content, f"RLS not enabled on {t}"
    
    # 7. Grants
    assert "revoke all on public.accounts, public.patient_profiles, public.clinical_records, public.appointments from anon;" in content, "Missing anon revocation"
    assert "grant select on public.accounts, public.patient_profiles, public.clinical_records, public.appointments to authenticated;" in content, "Missing select grants"
    assert "grant update (full_name, contact_phone, specialization) on public.accounts to authenticated;" in content, "Missing accounts column update grants"

    # 8. RPCs
    assert "create or replace function public.get_emergency_triage_by_token" in content, "Missing emergency triage RPC"
    assert "residential_address" not in content.split("create or replace function public.get_emergency_triage_by_token")[1].split("$$;")[0], "N1 VIOLATION: residential_address in emergency RPC!"
    assert "spouse_dependents" not in content.split("create or replace function public.get_emergency_triage_by_token")[1].split("$$;")[0], "N1 VIOLATION: spouse_dependents in emergency RPC!"
    assert "create or replace function public.submit_self_reported_baseline" in content, "Missing baseline submission RPC"
    assert "create or replace function public.regenerate_qr_token" in content, "Missing QR token rotation RPC"

    dq_count = content.count("$$")
    assert dq_count % 2 == 0, f"Unbalanced $$ dollar quotes: {dq_count}"
    print("Schema migration validation: PASSED")

def test_smoke(smoke_path: Path):
    content = smoke_path.read_text(encoding="utf-8")
    non_comments = [l.strip() for l in content.splitlines() if l.strip() and not l.strip().startswith("--")]
    assert non_comments[0].lower() == "begin;", "rls_smoke.sql must start with begin;"
    assert content.strip().endswith("rollback;"), "rls_smoke.sql must end with rollback;"
    
    # Check all 13 checklist items + concurrency
    for i in range(1, 14):
        assert f"CHECK {i}:" in content, f"Missing CHECK {i} in rls_smoke.sql"
    assert "CHECK 14:" in content, "Missing CHECK 14 (concurrency) in rls_smoke.sql"
    
    # Specific assertions
    assert "anon" in content, "Missing anon tests"
    assert "get_emergency_triage_by_token" in content, "Missing RPC test"
    assert "is_doctor_verified" in content, "Missing verification test"
    assert "regenerate_qr_token" in content, "Missing token rotation test"
    assert "insufficient_privilege" in content, "Missing permission denial tests"
    print("RLS smoke test harness validation: PASSED")

def test_seed(seed_path: Path):
    content = seed_path.read_text(encoding="utf-8")
    assert "Dr. Sarah Jenkins" in content, "Missing approved synthetic doctor"
    assert "Dr. Marcus Vance" in content, "Missing pending synthetic doctor"
    assert "Alex Morgan" in content, "Missing synthetic patient 1"
    assert "Priya Sharma" in content, "Missing synthetic patient 2"
    assert "David Kim" in content, "Missing synthetic patient 3"
    assert "doctor_status = 'approved'" in content, "Dev seed must approve one doctor per D1"
    assert "11111111-1111-1111-1111-111111111111" in content, "Missing patient 1 QR token"
    assert "Type 1 Diabetes" in content, "Missing patient 1 medical history"
    print("Synthetic seed data validation: PASSED")

def test_types(types_path: Path):
    content = types_path.read_text(encoding="utf-8")
    assert "export interface Database" in content, "Missing Database interface"
    for t in ['accounts', 'patient_profiles', 'clinical_records', 'appointments']:
        assert f"{t}:" in content, f"Missing {t} in Database types"
    assert "get_emergency_triage_by_token:" in content, "Missing RPC in types"
    assert "is_approved_doctor:" in content, "Missing helper in types"
    assert "regenerate_qr_token:" in content, "Missing regenerate_qr_token in types"
    assert "submit_self_reported_baseline:" in content, "Missing submit_self_reported_baseline in types"
    assert "any" not in [w for w in re.findall(r"\bany\b", content)], "N10 VIOLATION: 'any' type keyword found in types.ts"
    print("TypeScript database types validation: PASSED")

if __name__ == "__main__":
    base = Path(r"c:\Users\DELL\ayesha_pro\medi_qr")
    test_schema(base / "supabase" / "migrations" / "0001_umbrella_schema.sql")
    test_smoke(base / "supabase" / "tests" / "rls_smoke.sql")
    test_seed(base / "supabase" / "seed.sql")
    test_types(base / "src" / "lib" / "supabase" / "types.ts")
    print("\nALL WORKER M3 ARTIFACT VALIDATIONS PASSED!")

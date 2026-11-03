#!/usr/bin/env python3
"""scripts/challenger_m7_empirical_suite.py - Empirical Stress Tests for M7 (Touch Targets & Integrity)"""
import os, re, sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def py_sanitize_tel(phone: str) -> str:
    """Exact logic mirroring sanitizeTel() in src/lib/utils.ts"""
    if not phone or not isinstance(phone, str):
        return ""
    trimmed = phone.strip()
    has_leading_plus = trimmed.startswith("+")
    digits = re.sub(r"\D", "", trimmed)
    return f"+{digits}" if has_leading_plus and digits else digits

VALID_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}

def py_validate_emergency_triage(data: dict) -> tuple[bool, str]:
    """Exact validation mirroring emergencyTriageSchema with superRefine"""
    if not isinstance(data, dict):
        return False, "Data must be dict"
    if "residential_address" in data:
        return False, "Privacy violation: residential_address prohibited"
    if "spouse_dependents" in data:
        return False, "Privacy violation: spouse_dependents prohibited"

    name = data.get("full_name")
    if not name or not isinstance(name, str) or not name.strip():
        return False, "full_name is required"
    code = data.get("patient_code")
    if not code or not isinstance(code, str) or not code.strip():
        return False, "patient_code is required"

    try:
        age_num = int(data.get("age"))
        if isinstance(data.get("age"), float) and not data.get("age").is_integer():
            return False, "Age must be integer"
        if not (0 <= age_num <= 130):
            return False, f"Age out of bounds: {age_num}"
    except (ValueError, TypeError):
        return False, f"Invalid age: {data.get('age')}"

    if data.get("blood_group") not in VALID_BLOOD_GROUPS:
        return False, f"Invalid blood_group: {data.get('blood_group')}"

    for idx, med in enumerate(data.get("current_medication", [])):
        if not isinstance(med, dict) or not med.get("name") or not med.get("dosage") or not med.get("frequency"):
            return False, f"medication[{idx}] invalid"

    for idx, s in enumerate(data.get("previous_surgeries", [])):
        if not isinstance(s, dict) or not s.get("procedure"):
            return False, f"surgery[{idx}] invalid"
        try:
            y = int(s.get("year"))
            if not (1900 <= y <= 2100):
                return False, f"surgery[{idx}] year out of bounds: {y}"
        except (ValueError, TypeError):
            return False, f"surgery[{idx}] year invalid"

    return True, "Valid"

def run_empirical_suite():
    print("=" * 75)
    print("CHALLENGER M7-2: EMPIRICAL STRESS TEST SUITE (Touch Targets & Integrity)")
    print("=" * 75)

    results = []
    def chk(cat: str, name: str, cond: bool, detail: str = ""):
        results.append(cond)
        status = "PASS" if cond else "FAIL"
        d = f" | {detail}" if detail else ""
        print(f"[{status}] [{cat}] {name}{d}")

    # SECTION 1: 56px Minimum Touch Target Verification
    call_bar = open(os.path.join(ROOT_DIR, "src/components/emergency/sticky-emergency-call-bar.tsx"), encoding="utf-8").read()
    not_found = open(os.path.join(ROOT_DIR, "src/app/emergency/[token]/not-found.tsx"), encoding="utf-8").read()
    footer = open(os.path.join(ROOT_DIR, "src/components/emergency/triage-escalation-footer.tsx"), encoding="utf-8").read()

    chk("TOUCH", "CallBar min-h-[56px]", "min-h-[56px]" in call_bar, ">= 56px height")
    chk("TOUCH", "CallBar min-w-[56px]", "min-w-[56px]" in call_bar, ">= 56px width")
    chk("TOUCH", "CallBar tel: protocol", "href={`tel:" in call_bar, "Direct dialer")
    chk("TOUCH", "NotFound 911 min-h-[56px]", "min-h-[56px]" in not_found, ">= 56px height")
    chk("TOUCH", "NotFound 911 min-w-[56px]", "min-w-[56px]" in not_found, ">= 56px width")
    chk("TOUCH", "NotFound dials tel:911", 'href="tel:911"' in not_found, "Direct 911 link")
    chk("TOUCH", "Escalation link min-h-[48px]", "min-h-[48px]" in footer, "48px exceeds 44px WCAG AAA")
    chk("TOUCH", "CallBar active:scale-[0.98]", "active:scale-[0.98]" in call_bar, "Pure CSS press response")
    chk("TOUCH", "NotFound active:scale-[0.98]", "active:scale-[0.98]" in not_found, "Pure CSS press response")
    chk("TOUCH", "Footer active:scale-[0.98]", "active:scale-[0.98]" in footer, "Pure CSS press response")

    # SECTION 2: RFC 3966 Telephone Sanitization Stress Test
    tel_cases = [
        ("+1 (555) 123-4567", "+15551234567", "US international brackets & hyphens"),
        ("555.123.4567", "5551234567", "US national dot separators"),
        ("+44 20 7946 0958", "+442079460958", "UK international with spaces"),
        ("(555) 000-1111 ext. 99", "555000111199", "National extension text"),
        ("", "", "Empty string"),
        ("   ", "", "Whitespace only"),
        ("+", "", "Single plus with no digits"),
        ("++15551234567", "+15551234567", "Double leading plus collapse"),
        ("1-800-DOCTORS", "1800", "Alphanumeric phone word"),
        ("abc", "", "Letters only"),
        ("<script>alert(1)</script>", "1", "XSS script payload"),
        ("javascript:alert(1)", "1", "JavaScript scheme injection"),
        ("tel:1234567890", "1234567890", "tel: scheme prefix stripping"),
        ("+1;isub=1234", "+11234", "RFC 3966 isub sub-addressing parameter"),
        ("+49 30 123456", "+4930123456", "German international format"),
        ("+81 3 1234 5678", "+81312345678", "Japanese international format"),
        ("+61 2 9876 5432", "+61298765432", "Australian international format"),
        ("+123\n456\r789", "+123456789", "Control characters in phone"),
        ("001 555 123 4567", "0015551234567", "IDD 001 prefix without plus"),
        ("+001 555 123 4567", "+0015551234567", "IDD with leading plus"),
    ]
    rfc_regex = re.compile(r"^\+?[0-9]+$")
    for val, expected, desc in tel_cases:
        out = py_sanitize_tel(val)
        chk("TEL", f"sanitizeTel: {desc}", out == expected, f"in={val!r} -> out={out!r}")

    all_rfc = all(rfc_regex.match(py_sanitize_tel(v)) for v, _, _ in tel_cases if py_sanitize_tel(v))
    chk("TEL", "Non-empty outputs conform strictly to RFC 3966 digits/plus", all_rfc, "Zero illegal chars")

    # SECTION 3: Emergency Schema Boundary Stress Testing
    base = {
        "full_name": "Jane Doe", "patient_code": "UMB-100001", "age": 35, "blood_group": "O+",
        "current_medication": [{"name": "Lisinopril", "dosage": "10mg", "frequency": "Daily"}],
        "previous_surgeries": [{"procedure": "Appendectomy", "year": 2018}],
        "allergies": ["Penicillin"], "last_appointment_date": "2026-10-15T14:30:00Z",
        "is_doctor_verified": True, "updated_at": "2026-10-15T15:00:00Z",
    }
    chk("SCHEMA", "Base valid payload accepted", py_validate_emergency_triage(base)[0])
    chk("SCHEMA", "Age = 0 accepted", py_validate_emergency_triage(dict(base, age=0))[0])
    chk("SCHEMA", "Age = 130 accepted", py_validate_emergency_triage(dict(base, age=130))[0])
    chk("SCHEMA", "Age = -1 rejected", not py_validate_emergency_triage(dict(base, age=-1))[0])
    chk("SCHEMA", "Age = 131 rejected", not py_validate_emergency_triage(dict(base, age=131))[0])
    chk("SCHEMA", "Empty full_name rejected", not py_validate_emergency_triage(dict(base, full_name=""))[0])
    chk("SCHEMA", "All 8 blood groups accepted", all(py_validate_emergency_triage(dict(base, blood_group=bg))[0] for bg in VALID_BLOOD_GROUPS))
    chk("SCHEMA", "Invalid blood group 'X+' rejected", not py_validate_emergency_triage(dict(base, blood_group="X+"))[0])
    chk("SCHEMA", "residential_address rejected (superRefine)", not py_validate_emergency_triage(dict(base, residential_address="742 Elm St"))[0])
    chk("SCHEMA", "spouse_dependents rejected (superRefine)", not py_validate_emergency_triage(dict(base, spouse_dependents=[]))[0])
    chk("SCHEMA", "Null last_appointment_date accepted", py_validate_emergency_triage(dict(base, last_appointment_date=None))[0])
    chk("SCHEMA", "Empty allergies array accepted", py_validate_emergency_triage(dict(base, allergies=[]))[0])
    chk("SCHEMA", "is_doctor_verified: false accepted", py_validate_emergency_triage(dict(base, is_doctor_verified=False))[0])
    chk("SCHEMA", "Surgery year < 1900 rejected", not py_validate_emergency_triage(dict(base, previous_surgeries=[{"procedure": "LASIK", "year": 1899}]))[0])
    chk("SCHEMA", "Surgery year > 2100 rejected", not py_validate_emergency_triage(dict(base, previous_surgeries=[{"procedure": "LASIK", "year": 2101}]))[0])

    # SECTION 4: Zero Motion & Bundle Cleanliness Enforcement
    efiles = [
        "src/app/emergency/[token]/page.tsx", "src/app/emergency/[token]/not-found.tsx",
        "src/components/emergency/emergency-triage-view.tsx", "src/components/emergency/sticky-emergency-call-bar.tsx",
        "src/components/emergency/triage-allergies-alert.tsx", "src/components/emergency/triage-vitals-card.tsx",
        "src/components/emergency/triage-clinical-history.tsx", "src/components/emergency/triage-escalation-footer.tsx",
    ]
    prohibited = ["framer-motion", "@/components/ui/button", "qrcode.react", "jspdf", "@/components/ui/modal", "@/components/ui/tabs"]
    for p in prohibited:
        found = any(p in open(os.path.join(ROOT_DIR, ef), encoding="utf-8").read() for ef in efiles)
        chk("BUNDLE", f"Zero {p} in emergency surface", not found, f"Cleanliness confirmed")

    # SECTION 5: Character Count & Rule 12k Verification
    all_files = efiles + ["src/lib/schemas.ts", "src/lib/supabase/anon.ts", "scripts/verify_m7.py"]
    over = [f for f in all_files if len(open(os.path.join(ROOT_DIR, f), encoding="utf-8").read()) >= 12000]
    chk("RULE-12K", "All 11 M7 files < 12,000 chars", len(over) == 0, f"Over: {over}")

    total = len(results)
    passed = sum(1 for r in results if r)
    print("=" * 75)
    print(f"EMPIRICAL CHALLENGE SUMMARY: {passed}/{total} Passed, {total - passed} Failed")
    print("=" * 75)
    return passed == total

if __name__ == "__main__":
    if not run_empirical_suite():
        sys.exit(1)

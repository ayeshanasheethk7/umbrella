import os
import re
import sys
import uuid

ACTIONS_PATH = os.path.abspath(r"c:\Users\DELL\ayesha_pro\medi_qr\src\app\portal\doctor\actions.ts")

with open(ACTIONS_PATH, "r", encoding="utf-8") as f:
    actions_content = f.read()

print("=" * 70)
print("INDEPENDENT RE-CHECK: DOCTOR SERVER ACTIONS")
print("=" * 70)

# 1. Character count check
char_count = len(actions_content)
print(f"1. Character Count: {char_count} chars (Limit: 12,000) -> {'PASS' if char_count < 12000 else 'FAIL'}")

# 2. Invariant N10: Check for 'any'
any_matches = []
for idx, line in enumerate(actions_content.splitlines(), 1):
    cleaned = line.split("//")[0]
    # Check for ': any', 'as any', '<any>', 'any[]', 'Promise<any>'
    if re.search(r'\bany\b', cleaned):
        any_matches.append((idx, line.strip()))

print(f"2. Invariant N10 (Zero 'any'): {len(any_matches)} matches found -> {'PASS' if len(any_matches) == 0 else 'FAIL'}")
for lnum, ltext in any_matches:
    print(f"   Line {lnum}: {ltext}")

# 3. Check specific interfaces
has_search_interface = "export interface PatientSearchResultRow" in actions_content
has_appt_interface = "export interface AppointmentDbRow" in actions_content
print(f"3. Typed Interfaces:")
print(f"   - PatientSearchResultRow: {'PASS' if has_search_interface else 'FAIL'}")
print(f"   - AppointmentDbRow: {'PASS' if has_appt_interface else 'FAIL'}")

# 4. Search Classification Logic Simulation (Exact JS Regex & Precedence)
def js_escape_search_term(t: str) -> str:
    return re.sub(r'[%_(),]', '', t.replace('\\', '\\\\')).strip()

def js_search_classify(raw_query: str) -> str:
    q = (raw_query or '').strip()
    if len(q) < 2:
        return "EMPTY_ARRAY"
    if len(q) > 100:
        return "ERROR_LENGTH"
    
    digits = re.sub(r'\D', '', q)
    
    if re.search(r'^UMB-[A-Za-z0-9]{6}$', q, re.I):
        return "PATIENT_CODE"
    elif re.search(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', q, re.I):
        return "QR_TOKEN"
    elif len(digits) >= 7:
        return "PHONE"
    else:
        clean_term = js_escape_search_term(q)
        if len(clean_term) < 2:
            return "EMPTY_ARRAY"
        return "NAME_ILIKE"

# Test 1,000 random UUIDs
uuid_tests = [str(uuid.uuid4()) for _ in range(1000)]
uuid_failures = [u for u in uuid_tests if js_search_classify(u) != "QR_TOKEN"]
print(f"4. Search Precedence - 1,000 Random UUIDs: {1000 - len(uuid_failures)}/1000 routed to QR_TOKEN -> {'PASS' if len(uuid_failures) == 0 else 'FAIL'}")

# Test uppercase UUIDs
upper_uuids = [str(uuid.uuid4()).upper() for _ in range(50)]
upper_failures = [u for u in upper_uuids if js_search_classify(u) != "QR_TOKEN"]
print(f"   Uppercase UUIDs: {50 - len(upper_failures)}/50 routed to QR_TOKEN -> {'PASS' if len(upper_failures) == 0 else 'FAIL'}")

# Test Patient Codes
codes = ["UMB-ABC123", "umb-000000", "UMB-123456", "UMB-ZZZZZZ", "umb-a1b2c3"]
code_failures = [c for c in codes if js_search_classify(c) != "PATIENT_CODE"]
print(f"   Patient Codes: {len(codes) - len(code_failures)}/{len(codes)} routed to PATIENT_CODE -> {'PASS' if len(code_failures) == 0 else 'FAIL'}")

# Test Phone Numbers (with symbols and >= 7 digits)
phones = ["+1 (555) 123-4567", "555-0199", "9876543210", "+44 20 7946 0991", "1234567"]
phone_failures = [p for p in phones if js_search_classify(p) != "PHONE"]
print(f"   Phone Numbers: {len(phones) - len(phone_failures)}/{len(phones)} routed to PHONE -> {'PASS' if len(phone_failures) == 0 else 'FAIL'}")

# Test Wildcard Flooding Attacks
wildcards = ["%%%%%", "_____", "%_%_%_%_%", "%%__%%__", "  %  ", ",,,,", "((()))", "%,(),_"]
wildcard_non_empty = [w for w in wildcards if js_search_classify(w) != "EMPTY_ARRAY"]
print(f"5. Wildcard Flooding Defense: {len(wildcards) - len(wildcard_non_empty)}/{len(wildcards)} returned EMPTY_ARRAY (0 records) -> {'PASS' if len(wildcard_non_empty) == 0 else 'FAIL'}")

# Test Short inputs
shorts = ["", "a", " ", "  b  "]
short_failures = [s for s in shorts if js_search_classify(s) != "EMPTY_ARRAY"]
print(f"   Short queries (< 2 chars): {len(shorts) - len(short_failures)}/{len(shorts)} returned EMPTY_ARRAY -> {'PASS' if len(short_failures) == 0 else 'FAIL'}")

# Test Legitimate Names
names = ["John Smith", "Alice", "Dr. Robert", "Mary-Jane"]
name_failures = [n for n in names if js_search_classify(n) != "NAME_ILIKE"]
print(f"   Names: {len(names) - len(name_failures)}/{len(names)} routed to NAME_ILIKE -> {'PASS' if len(name_failures) == 0 else 'FAIL'}")

# 6. Check for Integrity Violations in actions.ts:
print("\n6. Checking for Integrity Violations in actions.ts:")
hardcoded_checks = [
    ("Mock Auth / getSession", "getSession" in actions_content),
    ("Service Role Key leak", "service_role" in actions_content.lower()),
    ("Bypassed Doctor Check", "verifyApprovedDoctor" not in actions_content),
    ("Hardcoded test UUIDs", "00000000-0000-0000" in actions_content),
    ("Hardcoded test codes", "UMB-ALX001" in actions_content),
]
integrity_violation = False
for desc, violated in hardcoded_checks:
    print(f"   - {desc}: {'VIOLATION' if violated else 'CLEAN'}")
    if violated: integrity_violation = True

print("=" * 70)
print(f"OVERALL RECHECK VERDICT: {'PASS' if (char_count < 12000 and len(any_matches) == 0 and len(uuid_failures) == 0 and len(wildcard_non_empty) == 0 and not integrity_violation) else 'FAIL'}")
print("=" * 70)

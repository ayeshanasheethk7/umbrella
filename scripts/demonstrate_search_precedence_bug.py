#!/usr/bin/env python3
"""
scripts/demonstrate_search_precedence_bug.py
Empirical Demonstration of Search Precedence Shadowing Bug in searchPatientsAction.
"""

import re
import uuid

def current_implementation(q: str):
    digits = re.sub(r'\D', '', q)
    if len(digits) >= 7:
        return "PHONE_SEARCH (ilike accounts.contact_phone, emergency_contact_phone)"
    if re.match(r'^UMB-[A-Za-z0-9]{6}$', q, re.I):
        return "PATIENT_CODE_SEARCH (ilike patient_code)"
    elif re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', q, re.I):
        return "QR_TOKEN_SEARCH (eq qr_token)"
    else:
        return "NAME_ILIKE_SEARCH (ilike accounts.full_name)"

def d14_compliant_implementation(q: str):
    digits = re.sub(r'\D', '', q)
    if re.match(r'^UMB-[A-Za-z0-9]{6}$', q, re.I):
        return "PATIENT_CODE_SEARCH (ilike patient_code)"
    elif re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', q, re.I):
        return "QR_TOKEN_SEARCH (eq qr_token)"
    elif len(digits) >= 7:
        return "PHONE_SEARCH (ilike accounts.contact_phone, emergency_contact_phone)"
    else:
        return "NAME_ILIKE_SEARCH (ilike accounts.full_name)"

def main():
    print("=" * 75)
    print("DEMONSTRATION: SEARCH PRECEDENCE SHADOWING IN searchPatientsAction")
    print("=" * 75)

    # Generate 10 random UUIDs
    test_uuids = [str(uuid.uuid4()) for _ in range(10)]

    print("\n1. Testing 10 randomly generated valid UUIDv4 tokens:")
    shadowed_count = 0
    for u in test_uuids:
        cur_route = current_implementation(u)
        d14_route = d14_compliant_implementation(u)
        digits_count = len(re.sub(r'\D', '', u))
        is_shadowed = (cur_route != "QR_TOKEN_SEARCH (eq qr_token)")
        if is_shadowed:
            shadowed_count += 1
        print(f"UUID: {u} (Digits: {digits_count:2d})")
        print(f"   Current Route: {cur_route}")
        print(f"   D14 Expected : {d14_route}")
        print(f"   Shadowed: {is_shadowed}")

    print(f"\nResult: {shadowed_count}/10 valid UUIDs were SHADOWED and misrouted to PHONE search!")

    print("\n2. Testing Patient Codes:")
    codes = ["UMB-ABC123", "umb-000000", "UMB-123456"]
    for c in codes:
        cur_route = current_implementation(c)
        d14_route = d14_compliant_implementation(c)
        print(f"Code: {c} -> Current: {cur_route} | D14: {d14_route}")

    print("\n3. Testing Phone Numbers:")
    phones = ["+1 (555) 123-4567", "555-0199", "9876543210"]
    for p in phones:
        cur_route = current_implementation(p)
        d14_route = d14_compliant_implementation(p)
        print(f"Phone: {p} -> Current: {cur_route} | D14: {d14_route}")

    print("\n4. Testing Patient Names:")
    names = ["Jane Doe", "Smith", "John 777th Street Apartment 100"]
    for n in names:
        cur_route = current_implementation(n)
        d14_route = d14_compliant_implementation(n)
        print(f"Name: {n} -> Current: {cur_route} | D14: {d14_route}")

if __name__ == "__main__":
    main()

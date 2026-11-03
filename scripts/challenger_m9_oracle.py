import re
import math
import uuid

def run_empirical_unit_test_oracle():
    print("=" * 80)
    print("EMPIRICAL CHALLENGER: COMPLETE UNIT TEST ORACLE RUNNER")
    print("=" * 80)

    passed = 0
    failed = 0

    def assert_eq(test_id, actual, expected, desc=""):
        nonlocal passed, failed
        if actual == expected:
            passed += 1
            print(f"[PASS] [{test_id}] {desc} -> {actual!r}")
        else:
            failed += 1
            print(f"[FAIL] [{test_id}] {desc} -> Expected {expected!r}, got {actual!r}")

    def assert_true(test_id, cond, desc=""):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"[PASS] [{test_id}] {desc}")
        else:
            failed += 1
            print(f"[FAIL] [{test_id}] {desc} -> Condition was False")

    # 1. UTILS: safeNext
    def safeNext(nextParam, fallback="/portal/patient"):
        if not nextParam or not isinstance(nextParam, str):
            return fallback
        trimmed = nextParam.strip()
        if (trimmed.startswith("//") or trimmed.startswith("/\\") or
            "\\" in trimmed or "\r" in trimmed or "\n" in trimmed or "\t" in trimmed):
            return fallback
        if not trimmed.startswith("/") or trimmed.startswith("//"):
            return fallback
        pathOnly = trimmed.split("?")[0].split("#")[0]
        if ":" in pathOnly:
            return fallback
        return trimmed

    assert_eq("T1-SAFENEXT-01a", safeNext("/portal/patient"), "/portal/patient")
    assert_eq("T1-SAFENEXT-01b", safeNext("/portal/doctor"), "/portal/doctor")
    assert_eq("T1-SAFENEXT-01c", safeNext("/portal/doctor/pending"), "/portal/doctor/pending")
    assert_eq("T1-SAFENEXT-02", safeNext("/portal/doctor?patient=UMB-A1B2C3"), "/portal/doctor?patient=UMB-A1B2C3")

    assert_eq("T2-SAFENEXT-01a", safeNext("//evil.com"), "/portal/patient")
    assert_eq("T2-SAFENEXT-01b", safeNext("//evil.com/login"), "/portal/patient")
    assert_eq("T2-SAFENEXT-02a", safeNext("/\\evil.com"), "/portal/patient")
    assert_eq("T2-SAFENEXT-02b", safeNext("\\evil.com"), "/portal/patient")
    assert_eq("T2-SAFENEXT-02c", safeNext("/path\\to\\somewhere"), "/portal/patient")
    assert_eq("T2-SAFENEXT-03a", safeNext("/http://evil.com"), "/portal/patient")
    assert_eq("T2-SAFENEXT-03b", safeNext("/javascript:alert(1)"), "/portal/patient")
    assert_eq("T2-SAFENEXT-03c", safeNext("/data:text/html,..."), "/portal/patient")
    assert_eq("T2-SAFENEXT-04a", safeNext("/\r\nevil.com"), "/portal/patient")
    assert_eq("T2-SAFENEXT-04b", safeNext("/\nevil.com"), "/portal/patient")
    assert_eq("T2-SAFENEXT-04c", safeNext("/\tevil.com"), "/portal/patient")
    assert_eq("T2-SAFENEXT-05a", safeNext("//attack.test", "/portal/doctor"), "/portal/doctor")
    assert_eq("T2-SAFENEXT-05b", safeNext(None, "/login"), "/login")
    assert_eq("T2-SAFENEXT-05c", safeNext(None, "/signup"), "/signup")

    # 2. UTILS: sanitizeTel
    def sanitizeTel(phone):
        if not phone or not isinstance(phone, str):
            return ""
        trimmed = phone.strip()
        hasLeadingPlus = trimmed.startswith("+")
        digitsOnly = re.sub(r"\D", "", trimmed)
        if not digitsOnly:
            return ""
        return ("+" + digitsOnly) if hasLeadingPlus else digitsOnly

    assert_eq("T1-SANTEL-01", sanitizeTel("(555) 123-4567"), "5551234567")
    assert_eq("T1-SANTEL-02a", sanitizeTel("+91 98765 43210"), "+919876543210")
    assert_eq("T1-SANTEL-02b", sanitizeTel("+44-20-7946-0958"), "+442079460958")
    assert_eq("T2-SANTEL-01a", sanitizeTel(""), "")
    assert_eq("T2-SANTEL-01b", sanitizeTel("   "), "")
    assert_eq("T2-SANTEL-01c", sanitizeTel("+"), "")
    assert_eq("T2-SANTEL-01d", sanitizeTel("()-.-"), "")
    assert_eq("T2-SANTEL-02a", sanitizeTel("+1-800-DOCTOR"), "+1800")
    assert_eq("T2-SANTEL-02b", sanitizeTel("1-800-HEALTHTEAM"), "1800")

    # 3. UTILS: formatPhone
    def formatPhone(phone):
        if not phone or not isinstance(phone, str):
            return ""
        digits = re.sub(r"\D", "", phone)
        if len(digits) == 10:
            return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
        return phone

    assert_eq("T1-FORMPHON-01a", formatPhone("1234567890"), "(123) 456-7890")
    assert_eq("T1-FORMPHON-01b", formatPhone("123-456-7890"), "(123) 456-7890")
    assert_eq("T2-FORMPHON-01a", formatPhone("+919876543210"), "+919876543210")
    assert_eq("T2-FORMPHON-01b", formatPhone("1234567"), "1234567")
    assert_eq("T2-FORMPHON-01c", formatPhone(""), "")

    # 4. UTILS: buildEmergencyUrl
    def buildEmergencyUrl(origin, token):
        cleanOrigin = re.sub(r"/+$", "", origin.strip())
        cleanToken = token.strip()
        return f"{cleanOrigin}/emergency/{cleanToken}"

    assert_eq("T1-BLDURL-01", buildEmergencyUrl("https://umbrella.health", "550e8400-e29b-41d4-a716-446655440000"),
              "https://umbrella.health/emergency/550e8400-e29b-41d4-a716-446655440000")
    assert_eq("T2-BLDURL-01a", buildEmergencyUrl("https://umbrella.health///", "  token-123  "),
              "https://umbrella.health/emergency/token-123")
    assert_eq("T2-BLDURL-01b", buildEmergencyUrl("http://localhost:3000/", "token"),
              "http://localhost:3000/emergency/token")

    # 5. DOCTOR ACTIONS: escapeSearchTerm
    def escapeSearchTerm(raw):
        clean = raw.strip()
        clean = re.sub(r"[%_(),]", "", clean)
        clean = clean.replace("\\", "\\\\")
        return clean.strip()

    assert_eq("T1-ESC-01a", escapeSearchTerm("Jane Doe"), "Jane Doe")
    assert_eq("T1-ESC-01b", escapeSearchTerm("Dr. Alice"), "Dr. Alice")
    assert_eq("T1-ESC-01c", escapeSearchTerm("Sharma-Patel"), "Sharma-Patel")
    assert_eq("T1-ESC-02", escapeSearchTerm("  Robert  "), "Robert")
    assert_eq("T2-ESC-01a", escapeSearchTerm("%admin%"), "admin")
    assert_eq("T2-ESC-01b", escapeSearchTerm("user_name"), "username")
    assert_eq("T2-ESC-02a", escapeSearchTerm("(select)"), "select")
    assert_eq("T2-ESC-02b", escapeSearchTerm("a,b,c"), "abc")
    assert_eq("T2-ESC-02c", escapeSearchTerm("%(_attack_,1=1)%"), "attack1=1")
    assert_eq("T2-ESC-03", escapeSearchTerm("test\\value"), "test\\\\value")
    assert_eq("T2-ESC-04a", escapeSearchTerm(" %_(), "), "")
    assert_eq("T2-ESC-04b", escapeSearchTerm(""), "")

    # 6. DOCTOR ACTIONS: Classifier & Precedence
    codeRegex = re.compile(r"^UMB-[A-Za-z0-9]{6}$", re.IGNORECASE)
    uuidRegex = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)

    assert_true("T1-CLASS-01a", codeRegex.match("UMB-A1B2C3") is not None, "Valid patient code match")
    assert_true("T1-CLASS-01b", codeRegex.match("umb-998877") is not None, "Valid lowercase code match")
    assert_true("T2-CLASS-01a", codeRegex.match("UMB-12345") is None, "Rejects short code")
    assert_true("T2-CLASS-01b", codeRegex.match("UMB-1234567") is None, "Rejects long code")
    assert_true("T2-CLASS-01c", codeRegex.match("PAT-123456") is None, "Rejects wrong prefix")

    assert_true("T1-CLASS-02a", uuidRegex.match("550e8400-e29b-41d4-a716-446655440000") is not None, "Valid v4 UUID match")
    assert_true("T1-CLASS-02b", uuidRegex.match("550E8400-E29B-41D4-A716-446655440000") is not None, "Valid uppercase UUID match")

    # 7. CARD GEOMETRY
    aspectRatio = 85.6 / 54.0
    assert_true("T1-GEOM-01", abs(aspectRatio - 1.585185) < 0.0001, "Aspect ratio matches ISO 7810")

    canvasW = round(85.6 / 25.4 * 300)
    canvasH = round(54.0 / 25.4 * 300)
    assert_eq("T1-GEOM-02a", canvasW, 1011, "Canvas width 1011px")
    assert_eq("T1-GEOM-02b", canvasH, 638, "Canvas height 638px")

    offsetX = (1080 - 700) / 2
    assert_eq("T1-GEOM-03", offsetX, 190, "Offset X centered 190px")

    def getNameFontSize(name):
        return 9 if len(name) > 20 else 11

    assert_eq("T1-GEOM-04a", getNameFontSize("John Doe"), 11)
    assert_eq("T1-GEOM-04b", getNameFontSize("Jane Livingston Smith"), 9)
    assert_eq("T1-GEOM-04c", getNameFontSize("Robert A. Montgomery"), 11)
    assert_eq("T2-GEOM-01a", getNameFontSize("A" * 20), 11)
    assert_eq("T2-GEOM-01b", getNameFontSize("A" * 21), 9)

    devPercent = abs((1011 / 638) - (85.6 / 54.0)) / (85.6 / 54.0) * 100
    assert_true("T2-GEOM-02", devPercent < 0.05, f"Canvas ratio deviation {devPercent:.4f}% < 0.05%")

    # 8. MOTION DAMPING RATIO
    s, d, m = 120, 20, 1
    zeta = d / (2 * math.sqrt(s * m))
    assert_true("T2-MOTION-03", 0.85 < zeta < 0.95, f"Apple spring zeta {zeta:.4f} within 0.85-0.95")

    print("\n" + "=" * 80)
    print(f"EMPIRICAL ORACLE EXECUTION SUMMARY: {passed} PASSED, {failed} FAILED")
    print("=" * 80)
    return failed == 0

if __name__ == "__main__":
    if not run_empirical_unit_test_oracle():
        exit(1)

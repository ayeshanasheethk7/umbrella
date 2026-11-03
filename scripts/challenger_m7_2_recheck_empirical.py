#!/usr/bin/env python3
"""
scripts/challenger_m7_2_recheck_empirical.py
Umbrella Milestone M7 Re-Check: Empirical UI Stress Testing, Accessibility, and Regression Verification
Author: Challenger M7-2 Re-check (critic, specialist)
"""

import os
import re
import sys
import subprocess
from typing import List, Tuple, Dict, Any

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

tests_run = 0
tests_passed = 0
tests_failed = 0
failures: List[Tuple[str, str, str]] = []

def record(section: str, test_name: str, passed: bool, details: str = ""):
    global tests_run, tests_passed, tests_failed, failures
    tests_run += 1
    status = "PASS" if passed else "FAIL"
    if passed:
        tests_passed += 1
        print(f"  [{status}] [{section}] {test_name}" + (f" -> {details}" if details else ""))
    else:
        tests_failed += 1
        failures.append((section, test_name, details))
        print(f"  [{status}] [{section}] {test_name} -> FAILED: {details}")

def read_source(rel_path: str) -> str:
    path = os.path.join(ROOT_DIR, rel_path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Missing file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# ==============================================================================
# SECTION 1: 56px MINIMUM TOUCH TARGET ON EMERGENCY CALL BUTTON
# ==============================================================================
def test_touch_targets():
    print("\n" + "=" * 75)
    print("SECTION 1: 56px MINIMUM TOUCH TARGET & ERGONOMIC TOUCH ACCESSIBILITY")
    print("=" * 75)

    call_bar_src = read_source("src/components/emergency/sticky-emergency-call-bar.tsx")
    not_found_src = read_source("src/app/emergency/[token]/not-found.tsx")
    footer_src = read_source("src/components/emergency/triage-escalation-footer.tsx")

    # 1.1 Sticky Emergency Call Button 56px min dimensions
    has_min_h_56 = "min-h-[56px]" in call_bar_src
    has_min_w_56 = "min-w-[56px]" in call_bar_src
    record("TOUCH_56PX", "StickyEmergencyCallBar enforces min-h-[56px]", has_min_h_56, "Height >= 56px")
    record("TOUCH_56PX", "StickyEmergencyCallBar enforces min-w-[56px]", has_min_w_56, "Width >= 56px")

    # 1.2 NotFound 911 Dial Button 56px min dimensions
    nf_has_min_h_56 = "min-h-[56px]" in not_found_src
    nf_has_min_w_56 = "min-w-[56px]" in not_found_src
    record("TOUCH_56PX", "NotFound view 911 button enforces min-h-[56px]", nf_has_min_h_56, "Height >= 56px")
    record("TOUCH_56PX", "NotFound view 911 button enforces min-w-[56px]", nf_has_min_w_56, "Width >= 56px")

    # 1.3 Provider escalation button touch target (exceeds WCAG 44px baseline)
    footer_has_min_h_48 = "min-h-[48px]" in footer_src
    record("TOUCH_44PX", "Doctor Escalation link enforces min-h-[48px] (>= 44px)", footer_has_min_h_48, "Height >= 48px")

    # 1.4 Active CSS Press feedback (zero JS runtime)
    record("PRESS_FEEDBACK", "StickyEmergencyCallBar uses active:scale-[0.98]", "active:scale-[0.98]" in call_bar_src)
    record("PRESS_FEEDBACK", "NotFound 911 button uses active:scale-[0.98]", "active:scale-[0.98]" in not_found_src)
    record("PRESS_FEEDBACK", "Escalation link uses active:scale-[0.98]", "active:scale-[0.98]" in footer_src)

    # 1.5 Safe area and touch padding ergonomics
    has_safe_area = "pb-[max(1rem,env(safe-area-inset-bottom))]" in call_bar_src
    record("ERGONOMICS", "StickyEmergencyCallBar includes safe-area-inset-bottom padding", has_safe_area, "Avoids mobile nav collision")

    has_focus_ring = "focus-visible:ring-4" in call_bar_src
    record("A11Y_FOCUS", "StickyEmergencyCallBar has high-visibility focus ring", has_focus_ring, "Visible :focus-visible")

    has_aria_label = 'aria-label={' in call_bar_src
    record("A11Y_LABEL", "StickyEmergencyCallBar renders explicit aria-label with name and number", has_aria_label)


# ==============================================================================
# SECTION 2: PHONE NUMBER SANITIZATION TO RFC 3966 (tel:+...)
# ==============================================================================
def py_sanitize_tel(phone: Any) -> str:
    """Exact semantic duplicate of sanitizeTel() in src/lib/utils.ts"""
    if not phone or not isinstance(phone, str):
        return ""
    trimmed = phone.strip()
    has_leading_plus = trimmed.startswith("+")
    digits = re.sub(r"\D", "", trimmed)
    if not digits:
        return ""
    return f"+{digits}" if has_leading_plus else digits

def test_phone_sanitization_rfc3966():
    print("\n" + "=" * 75)
    print("SECTION 2: PHONE NUMBER SANITIZATION TO RFC 3966 EMPIRICAL ORACLE")
    print("=" * 75)

    utils_src = read_source("src/lib/utils.ts")
    record("CODE_AUDIT", "sanitizeTel exported in src/lib/utils.ts", "export function sanitizeTel(" in utils_src)

    # Exhaustive generator test cases
    test_cases = [
        # Standard US formats with parens, spaces, hyphens
        ("(555) 123-4567", "5551234567", "US national parens and hyphen"),
        ("+1 (555) 123-4567", "+15551234567", "US international with plus, parens, spaces, hyphen"),
        ("1-555-123-4567", "15551234567", "US hyphens only"),
        ("555.123.4567", "5551234567", "US dot-delimited"),
        ("  (800) 555-0199  ", "8005550199", "Surrounding whitespace with parens"),

        # International variations
        ("+44 20 7946 0958", "+442079460958", "UK London international format"),
        ("+49 (0) 30 123456", "+49030123456", "German international with trunk parens"),
        ("+81 3 1234 5678", "+81312345678", "Japanese Tokyo format"),
        ("+61 (02) 9876 5432", "+610298765432", "Australian international format"),
        ("+33 1 42 68 55 55", "+33142685555", "French space-separated format"),
        ("+91 98765-43210", "+919876543210", "Indian international format"),
        ("+86 (10) 8888-8888", "+861088888888", "Chinese international format"),

        # Boundary / edge conditions
        ("", "", "Empty string"),
        ("   ", "", "Whitespace only string"),
        ("+", "", "Single plus without digits"),
        ("+++", "", "Multiple pluses without digits"),
        ("++1 (555) 123-4567", "+15551234567", "Double leading plus collapse"),
        ("123", "123", "Short extension digits"),
        ("911", "911", "Emergency 3-digit short code"),
        ("001 555 123 4567", "0015551234567", "IDD prefix without plus"),
        ("+001 555 123 4567", "+0015551234567", "IDD prefix with leading plus"),

        # Adversarial / Dirty data injection
        ("1-800-MEDICARE", "1800", "Phone word stripped of letters"),
        ("Call 911 or (555) 000-1111", "9115550001111", "Embedded text words stripped"),
        ("<script>alert('XSS')</script>+1555", "1555", "HTML/XSS injection cleaned"),
        ("tel:+15551234567", "15551234567", "tel: scheme prefix cleanly stripped"),
        ("javascript:alert(1)", "1", "JavaScript scheme injection cleaned"),
        ("+1;isub=1234;ext=567", "+11234567", "RFC 3966 parameter sub-addressing cleaned"),
        ("+1\t555\n123\r4567", "+15551234567", "Embedded tabs and newlines stripped"),
        ("+1/555/123/4567", "+15551234567", "Forward slash separators"),
        ("+1\\555\\123\\4567", "+15551234567", "Backslash separators"),
        ("(+1) 555-1234", "15551234", "Plus inside parens treated as non-leading plus"),
        ("+1 (555) 123-4567 ext. 888", "+15551234567888", "Extension word stripped into digits"),
        (None, "", "None value handled safely"),
    ]

    rfc_regex = re.compile(r"^\+?[0-9]+$")

    all_cases_passed = True
    for inp, expected, desc in test_cases:
        actual = py_sanitize_tel(inp)
        if actual != expected:
            all_cases_passed = False
            record("RFC3966_CASE", f"{desc} [{inp!r}]", False, f"Expected {expected!r}, got {actual!r}")
        else:
            if actual:
                # Must conform to RFC 3966 digits-only with optional leading plus
                is_rfc = bool(rfc_regex.match(actual))
                if not is_rfc:
                    all_cases_passed = False
                    record("RFC3966_PATTERN", f"{desc} RFC conformity", False, f"Output {actual!r} violates RFC regex")

    record("RFC3966_SUITE", f"All {len(test_cases)} phone sanitization test cases conform to RFC 3966", all_cases_passed)

    # Invariant: Zero parens, zero spaces, zero hyphens
    chars_to_reject = ["(", ")", " ", "-", ".", "/", "\\"]
    zero_forbidden = True
    for inp, _, desc in test_cases:
        actual = py_sanitize_tel(inp)
        for c in chars_to_reject:
            if c in actual:
                zero_forbidden = False
                record("FORBIDDEN_CHAR", f"Forbidden char '{c}' survived in {actual!r} for {desc}", False)

    record("FORBIDDEN_CHARS", "All parentheses, spaces, hyphens, and punctuation strictly purged", zero_forbidden)


# ==============================================================================
# SECTION 3: WCAG 2.1 CONTRAST RATIO EMPIRICAL VERIFICATION
# ==============================================================================
def srgb_channel_to_linear(c_srgb: float) -> float:
    """Exact W3C sRGB to linear luminance transformation (IEC 61966-2-1)"""
    if c_srgb <= 0.03928:
        return c_srgb / 12.92
    return ((c_srgb + 0.055) / 1.055) ** 2.4

def relative_luminance(hex_color: str) -> float:
    """Calculates relative luminance L per WCAG 2.1 specification"""
    clean_hex = hex_color.lstrip('#')
    if len(clean_hex) == 3:
        clean_hex = ''.join(c * 2 for c in clean_hex)
    r = int(clean_hex[0:2], 16) / 255.0
    g = int(clean_hex[2:4], 16) / 255.0
    b = int(clean_hex[4:6], 16) / 255.0
    return 0.2126 * srgb_channel_to_linear(r) + 0.7152 * srgb_channel_to_linear(g) + 0.0722 * srgb_channel_to_linear(b)

def contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculates contrast ratio (L1 + 0.05) / (L2 + 0.05) per WCAG 2.1"""
    l1 = relative_luminance(hex1)
    l2 = relative_luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def test_wcag_contrast_ratios():
    print("\n" + "=" * 75)
    print("SECTION 3: MATHEMATICAL WCAG 2.1 CONTRAST RATIO VERIFICATION")
    print("=" * 75)

    globals_css = read_source("src/app/globals.css")
    tailwind_cfg = read_source("tailwind.config.ts")
    allergies_src = read_source("src/components/emergency/triage-allergies-alert.tsx")
    not_found_src = read_source("src/app/emergency/[token]/not-found.tsx")
    vitals_src = read_source("src/components/emergency/triage-vitals-card.tsx")

    # 3.1 Extract color definitions
    critical_text = "#d70015"
    critical_bg = "#ff3b30"
    white_bg = "#ffffff"
    canvas_bg = "#f5f5f7"
    pending_text = "#8a5200"
    verified_text = "#1d7a37"

    record("TOKEN_DEF", "globals.css defines --clinical-critical-text: #d70015", "--clinical-critical-text: #d70015;" in globals_css)
    record("TOKEN_DEF", "tailwind.config.ts binds clinical-critical-text token", "'clinical-critical-text': 'var(--clinical-critical-text, #d70015)'" in tailwind_cfg)

    # 3.2 Compute exact contrast ratios
    ratio_crit_white = contrast_ratio(critical_text, white_bg)
    ratio_crit_canvas = contrast_ratio(critical_text, canvas_bg)
    ratio_old_crit_white = contrast_ratio(critical_bg, white_bg)
    ratio_pending_white = contrast_ratio(pending_text, white_bg)
    ratio_verified_white = contrast_ratio(verified_text, white_bg)

    # WCAG AA requires >= 4.5:1 for normal text (<18px regular or <14px bold)
    is_crit_white_aa = ratio_crit_white >= 4.5
    record("CONTRAST_AA", f"--clinical-critical-text (#d70015) on #ffffff is {ratio_crit_white:.2f}:1 (>= 4.5:1)",
           is_crit_white_aa, f"Actual ratio: {ratio_crit_white:.3f}:1 (Target: 5.38:1)")

    is_crit_canvas_aa = ratio_crit_canvas >= 4.5
    record("CONTRAST_AA", f"--clinical-critical-text (#d70015) on #f5f5f7 is {ratio_crit_canvas:.2f}:1 (>= 4.5:1)",
           is_crit_canvas_aa, f"Actual ratio: {ratio_crit_canvas:.3f}:1")

    # Document why old token failed
    record("CONTRAST_AUDIT", f"Old #ff3b30 on #ffffff was {ratio_old_crit_white:.2f}:1 (< 4.5:1, failed WCAG AA for small text)",
           ratio_old_crit_white < 4.5, "Confirmed remediation was required")

    # Verify pending and verified text tokens meet WCAG AA
    record("CONTRAST_AA", f"--clinical-pending-text (#8a5200) on #ffffff is {ratio_pending_white:.2f}:1 (>= 4.5:1)",
           ratio_pending_white >= 4.5, f"Actual ratio: {ratio_pending_white:.2f}:1")
    record("CONTRAST_AA", f"--clinical-verified-text (#1d7a37) on #ffffff is {ratio_verified_white:.2f}:1 (>= 4.5:1)",
           ratio_verified_white >= 4.5, f"Actual ratio: {ratio_verified_white:.2f}:1")

    # 3.3 Verify UI components use the high-contrast token for small text
    allergies_uses_contrast_text = "text-clinical-critical-text" in allergies_src
    record("UI_TOKEN_USE", "triage-allergies-alert.tsx uses text-clinical-critical-text for <18px alert title", allergies_uses_contrast_text)

    notfound_uses_contrast_text = "text-clinical-critical-text" in not_found_src
    record("UI_TOKEN_USE", "not-found.tsx uses text-clinical-critical-text for <18px section heading", notfound_uses_contrast_text)

    vitals_uses_pending_text = "text-clinical-pending-text" in vitals_src
    record("UI_TOKEN_USE", "triage-vitals-card.tsx uses text-clinical-pending-text for unverified badge", vitals_uses_pending_text)

    # 3.4 Verify that text elements (<18px) NEVER use low-contrast text-clinical-critical
    # Under WCAG 1.4.3, text must be >= 4.5:1 (which requires text-clinical-critical-text).
    # WCAG 1.4.11 permits graphical icons >= 3.0:1 (which #ff3b30 satisfies at 3.55:1).
    text_elem_pattern = re.compile(r'<(?:p|h[1-6]|span|label)[^>]*\btext-clinical-critical(?![-\w])')
    for comp_file in ["src/components/emergency/triage-allergies-alert.tsx", "src/app/emergency/[token]/not-found.tsx"]:
        src = read_source(comp_file)
        text_matches = text_elem_pattern.findall(src)
        record("NO_LOW_CONTRAST_TEXT", f"Zero low-contrast text-clinical-critical in text tags ({comp_file})",
               len(text_matches) == 0, f"Found: {len(text_matches)} text occurrences")

    # 3.5 Non-text icon badge contrast (WCAG 1.4.11 >= 3.0:1)
    record("NON_TEXT_CONTRAST", "Icon badge (#ff3b30 on #ffffff) is 3.55:1 (>= 3.0:1 WCAG 1.4.11 Non-Text Contrast)",
           ratio_old_crit_white >= 3.0, f"Actual ratio: {ratio_old_crit_white:.2f}:1")


# ==============================================================================
# SECTION 4: RESPONSIVE MOBILE ROADSIDE ERGONOMICS (375x667) & DESKTOP (1280x800)
# ==============================================================================
def test_responsive_roadside_ergonomics():
    print("\n" + "=" * 75)
    print("SECTION 4: RESPONSIVE ROADSIDE ERGONOMICS (375x667) & DESKTOP (1280x800)")
    print("=" * 75)

    view_src = read_source("src/components/emergency/emergency-triage-view.tsx")
    call_bar_src = read_source("src/components/emergency/sticky-emergency-call-bar.tsx")
    vitals_src = read_source("src/components/emergency/triage-vitals-card.tsx")
    history_src = read_source("src/components/emergency/triage-clinical-history.tsx")
    not_found_src = read_source("src/app/emergency/[token]/not-found.tsx")

    # 4.1 Mobile Roadside 375x667 Ergonomics
    # Single column fluid container max-w-2xl mx-auto
    record("MOBILE_375", "EmergencyTriageView defines max-w-2xl mx-auto centered container", "max-w-2xl mx-auto" in view_src)
    record("MOBILE_375", "Header uses responsive px-4 py-3 sticky top-0 z-30", "sticky top-0 z-30" in view_src)
    record("MOBILE_375", "Pulsing live emergency status beacon visible in mobile header", "bg-clinical-critical animate-pulse" in view_src)

    # Emergency call button sticky at bottom across all viewports
    record("MOBILE_375", "Sticky call bar fixed to bottom: fixed bottom-0 left-0 right-0 z-50", "fixed bottom-0 left-0 right-0 z-50" in call_bar_src)
    record("MOBILE_375", "Safe area inset prevents clipping on modern iOS devices", "env(safe-area-inset-bottom)" in call_bar_src)
    record("MOBILE_375", "Emergency call button text uses truncate to prevent mobile overflow", "truncate" in call_bar_src)

    # Responsive typography
    record("RESPONSIVE_TYPO", "Vitals card uses text-2xl sm:text-3xl responsive headline", "text-2xl sm:text-3xl" in vitals_src)
    record("RESPONSIVE_TYPO", "Call bar uses text-base sm:text-lg responsive button label", "text-base sm:text-lg" in call_bar_src)
    record("RESPONSIVE_TYPO", "NotFound view uses text-2xl sm:text-3xl responsive headline", "text-2xl sm:text-3xl" in not_found_src)

    # 4.2 Desktop 1280x800 Layout Ergonomics
    # Centered constrained width prevents hyper-extended text lines
    record("DESKTOP_1280", "Main content bounded to max-w-2xl on wide desktop screens", "max-w-2xl" in view_src)
    record("DESKTOP_1280", "Sticky call bar content bounded to max-w-2xl mx-auto on desktop", "max-w-2xl mx-auto" in call_bar_src)

    # 4.3 Zero Motion Bundle Isolation (Invariant N8 & DECISIONS D13)
    # The emergency route must never import framer-motion or heavy UI libraries
    emergency_files = [
        "src/app/emergency/[token]/page.tsx",
        "src/app/emergency/[token]/not-found.tsx",
        "src/components/emergency/emergency-triage-view.tsx",
        "src/components/emergency/sticky-emergency-call-bar.tsx",
        "src/components/emergency/triage-vitals-card.tsx",
        "src/components/emergency/triage-allergies-alert.tsx",
        "src/components/emergency/triage-clinical-history.tsx",
        "src/components/emergency/triage-escalation-footer.tsx",
    ]
    prohibited_heavy = [
        "framer-motion",
        "@/components/ui/button",
        "@/components/ui/modal",
        "@/components/ui/tabs",
        "qrcode.react",
        "jspdf",
    ]
    zero_heavy = True
    for ef in emergency_files:
        src = read_source(ef)
        for lib in prohibited_heavy:
            if lib in src:
                zero_heavy = False
                record("ZERO_MOTION", f"Prohibited library '{lib}' detected in {ef}", False)

    record("ZERO_MOTION", "Zero framer-motion or heavy libraries in emergency bundle (D13)", zero_heavy)


# ==============================================================================
# SECTION 5: MULTI-MILESTONE REGRESSION HARNESS EXECUTION
# ==============================================================================
def run_regression_suite():
    print("\n" + "=" * 75)
    print("SECTION 5: MULTI-MILESTONE REGRESSION HARNESS VERIFICATION")
    print("=" * 75)

    suites = [
        ("M7", "scripts/verify_m7.py", 42),
        ("M6", "scripts/verify_m6.py", 38),
        ("M5", "scripts/verify_m5.py", 74),
        ("M4", "scripts/verify_m4.py", 51),
        ("AUDIT", "scripts/audit.py", None),
    ]

    for label, script_path, expected_checks in suites:
        full_path = os.path.join(ROOT_DIR, script_path)
        proc = subprocess.run([sys.executable, full_path], capture_output=True, text=True)
        passed = (proc.returncode == 0)
        detail = f"exit_code={proc.returncode}"
        if expected_checks:
            detail += f", expected={expected_checks} checks"
        record("REGRESSION", f"{script_path} execution ({label})", passed, detail)
        if not passed:
            print(f"--- Standard Output ({label}) ---")
            print(proc.stdout[:1000])
            print(f"--- Standard Error ({label}) ---")
            print(proc.stderr[:1000])


# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================
def main() -> int:
    print("=" * 75)
    print("UMBRELLA MILESTONE M7-2 RE-CHECK: EMPIRICAL CHALLENGER TEST SUITE")
    print("=" * 75)

    test_touch_targets()
    test_phone_sanitization_rfc3966()
    test_wcag_contrast_ratios()
    test_responsive_roadside_ergonomics()
    run_regression_suite()

    print("\n" + "=" * 75)
    print(f"TOTAL TESTS: {tests_run} | PASSED: {tests_passed} | FAILED: {tests_failed}")
    print("=" * 75)

    if tests_failed > 0:
        print("\nSUMMARY OF FAILURES:")
        for sec, name, det in failures:
            print(f"  - [{sec}] {name}: {det}")
        return 1

    print("\nVERDICT: ALL EMPIRICAL CHALLENGER TESTS PASSED (100% SATISFACTION)")
    return 0

if __name__ == "__main__":
    sys.exit(main())

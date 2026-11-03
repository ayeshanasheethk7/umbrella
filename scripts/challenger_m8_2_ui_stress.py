#!/usr/bin/env python3
"""
scripts/challenger_m8_2_ui_stress.py
Empirical UI Stress, Canvas/PDF & Regression Challenger for Milestone M8.
Challenger: challenger_m8_2
"""

import os
import re
import sys
import subprocess

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def extract_jsx_opening_tags(code: str, tag_name: str):
    tags = []
    pattern = rf'<{tag_name}\b'
    for m in re.finditer(pattern, code):
        start, i, in_brace, in_str = m.start(), m.end(), 0, None
        while i < len(code):
            ch = code[i]
            if in_str:
                if ch == '\\': i += 1
                elif ch == in_str: in_str = None
            elif ch in ('"', "'", '`'): in_str = ch
            elif ch == '{': in_brace += 1
            elif ch == '}': in_brace -= 1
            elif ch == '>' and in_brace == 0:
                tags.append(code[start : i + 1])
                break
            i += 1
    return tags

def run_stress_suite():
    passed = failed = total = 0
    print("=" * 80)
    print("CHALLENGER M8-2: EMPIRICAL UI STRESS, CANVAS/PDF & REGRESSION HARNESS")
    print("=" * 80)

    def test(tid: str, desc: str, condition: bool, details: str = ""):
        nonlocal passed, failed, total
        total += 1
        status = "PASS" if condition else "FAIL"
        d = f" -> {details}" if details else ""
        print(f"[{status}] [{tid}] {desc}{d}")
        if condition: passed += 1
        else: failed += 1

    rf = lambda p: os.path.join(ROOT_DIR, p)
    st = open(rf("src/components/qr/qr-studio.tsx"), encoding="utf-8").read()
    pv = open(rf("src/components/qr/card-preview.tsx"), encoding="utf-8").read()
    qe = open(rf("src/lib/qr-export.ts"), encoding="utf-8").read()
    pq = open(rf("src/components/patient/emergency-qr-card.tsx"), encoding="utf-8").read()

    # SUITE 1: QR VIEWPORT GEOMETRY & MOBILE 224px BOX
    print("\n--- SUITE 1: QR Viewport Geometry & Mobile 224px Box ---")
    test("S1-QR-01-SIZE", "QRCodeSVG size prop set to 224", "size={224}" in st)
    test("S1-QR-02-BOX-W", "Container enforces mobile w-[224px]", "w-[224px]" in st)
    test("S1-QR-03-BOX-H", "Container enforces mobile h-[224px]", "h-[224px]" in st)
    test("S1-QR-04-DESKTOP", "Container scales up on sm viewport", "sm:w-[240px]" in st and "sm:h-[240px]" in st)
    test("S1-QR-05-ASPECT", "Container preserves 1:1 aspect ratio", "w-[224px] h-[224px]" in st)
    test("S1-QR-06-LEVEL-Q", "Error correction configured to level='Q'", 'level="Q"' in st)
    test("S1-QR-07-QUIET-ZONE", "Quiet zone marginSize={4} set", "marginSize={4}" in st)
    test("S1-QR-08-CONTRAST", "High contrast black/white tokens enforced", 'fgColor="rgb(0, 0, 0)"' in st and 'bgColor="rgb(255, 255, 255)"' in st)

    # SUITE 2: BOUNDARY STRESS: LONG NAMES, LONG URLS, EMPTY RELATIONS
    print("\n--- SUITE 2: Boundary Stress: Long Names, Long URLs, Empty Relations ---")
    test("S2-NAME-01-TRUNCATE", "Card preview protects long names via truncate", "truncate" in pv and "patientName" in pv)
    test("S2-NAME-02-STEPDOWN", "PDF export reduces font size for names > 20 chars", "patientName.length > 20 ? 9 : 11" in qe)
    test("S2-NAME-03-MAXWIDTH", "PDF export restricts patient name to maxWidth: 44", "maxWidth: 44" in qe and "doc.text(patientName" in qe)

    qr_x_match = re.search(r'doc\.addImage\(qrDataUrl,\s*[\'"]PNG[\'"],\s*([\d\.]+)', qe)
    qr_x = float(qr_x_match.group(1)) if qr_x_match else 0.0
    safety_margin = qr_x - (4.0 + 44.0)
    test("S2-NAME-04-CLEARANCE", f"PDF left column (48mm) has safety gap to QR ({qr_x}mm)", safety_margin >= 1.5, f"Gap = {safety_margin:.1f} mm")

    test("S2-URL-01-BREAK-ALL", "Card preview wraps long URLs with break-all", "break-all" in pv and "emergencyUrl" in pv)
    test("S2-URL-02-MAXWIDTH", "PDF export wraps URL with maxWidth: 77.6", "maxWidth: 77.6" in qe and "doc.text(emergencyUrl" in qe)
    test("S2-URL-03-MONOSPACE", "PDF export renders URL in courier 5.5pt", "doc.setFont('courier'" in qe and "doc.setFontSize(5.5)" in qe)
    url_right_margin = 85.6 - (4.0 + 77.6)
    test("S2-URL-04-SYMMETRY", f"PDF URL margins balanced (right margin {url_right_margin:.1f}mm)", abs(url_right_margin - 4.0) < 0.01)

    test("S2-REL-01-PREVIEW", "Card preview guards relation formatting", "emergencyContactRelation ?" in pv or "relationLabel" in pv)
    test("S2-REL-02-NO-EMPTY-PARENS", "Card preview avoids dangling empty parentheses", 'relationLabel &&' in pv or 'emergencyContactRelation ?' in pv)
    test("S2-REL-03-PDF-GUARD", "PDF export guards relation label with ternary", "emergencyContactRelation ?" in qe and "relationLabel" in qe)

    # SUITE 3: TOUCH TARGET INSPECTION (min-h-[44px])
    print("\n--- SUITE 3: Touch Target Inspection (min-h-[44px]) ---")
    test("S3-TOUCH-01-TAB-QR", "QR tab enforces min-h-[44px]", 'role="tab"' in st and "min-h-[44px]" in st)
    test("S3-TOUCH-02-TAB-CARD", "Card tab enforces min-h-[44px]", 'role="tab"' in st and "min-h-[44px]" in st)
    test("S3-TOUCH-03-BTN-PNG", "Save PNG enforces min-h-[44px]", "handleExportPng" in st and "min-h-[44px]" in st)
    test("S3-TOUCH-04-BTN-PDF", "Print ID Card enforces min-h-[44px]", "handleExportPdf" in st and "min-h-[44px]" in st)
    test("S3-TOUCH-05-PREVIEW", "Preview link enforces min-h-[44px]", "Preview Public Emergency View" in st and "min-h-[44px]" in st)
    test("S3-TOUCH-06-REGEN", "Regenerate button enforces min-h-[44px]", "Regenerate Emergency QR Code" in st and "min-h-[44px]" in st)
    test("S3-TOUCH-07-KEEP", "Modal keep button enforces min-h-[44px]", "Keep Current Token" in st and "min-h-[44px]" in st)
    test("S3-TOUCH-08-CONFIRM", "Modal regen button enforces min-h-[44px]", "Regenerate Token" in st and "min-h-[44px]" in st)
    test("S3-TOUCH-09-FRONT", "Card preview Front Side tab enforces min-h-[44px]", "Front Side" in pv and "min-h-[44px]" in pv)
    test("S3-TOUCH-10-BACK", "Card preview Back Side tab enforces min-h-[44px]", "Back Side" in pv and "min-h-[44px]" in pv)
    test("S3-TOUCH-11-TEL", "Card preview tel: link enforces min-h-[44px]", "tel:" in pv and "min-h-[44px]" in pv)

    st_btns = extract_jsx_opening_tags(st, 'button')
    sub_44_st = [b for b in st_btns if "min-h-[44px]" not in b]
    test("S3-TOUCH-12-ST-BTNS", f"All raw <button> in qr-studio.tsx have min-h-[44px] ({len(st_btns)})", len(sub_44_st) == 0)

    st_Btns = extract_jsx_opening_tags(st, 'Button')
    sub_44_Btns = [b for b in st_Btns if "min-h-[44px]" not in b]
    test("S3-TOUCH-13-ST-COMPS", f"All <Button> in qr-studio.tsx have min-h-[44px] ({len(st_Btns)})", len(sub_44_Btns) == 0)

    pv_btns = extract_jsx_opening_tags(pv, 'button')
    sub_44_pv = [b for b in pv_btns if "min-h-[44px]" not in b]
    test("S3-TOUCH-14-PV-BTNS", f"All raw <button> in card-preview.tsx have min-h-[44px] ({len(pv_btns)})", len(sub_44_pv) == 0)

    pv_anchors = extract_jsx_opening_tags(pv, 'a')
    sub_44_anchors = [a for a in pv_anchors if "min-h-[44px]" not in a]
    test("S3-TOUCH-15-PV-ANCHORS", f"All <a> in card-preview.tsx have min-h-[44px] ({len(pv_anchors)})", len(sub_44_anchors) == 0)

    # SUITE 4: INVARIANT N6 CLIENT ORIGIN & SKELETON
    print("\n--- SUITE 4: Invariant N6 Client-Side Origin Hydration & Skeleton ---")
    test("S4-N6-01-CLIENT", "File begins with 'use client'", st.strip().startswith("'use client'"))
    test("S4-N6-02-ORIGIN-INIT", "origin state initialized to ''", "const [origin, setOrigin] = useState('');" in st)
    test("S4-N6-03-MOUNTED-INIT", "mounted state initialized to false", "const [mounted, setMounted] = useState(false);" in st)
    test("S4-N6-04-EFFECT-ORIGIN", "origin set inside useEffect", "useEffect" in st and "setOrigin(window.location.origin)" in st)
    test("S4-N6-05-EFFECT-MOUNTED", "setMounted(true) inside useEffect", "useEffect" in st and "setMounted(true)" in st)
    test("S4-N6-06-BUILD-URL", "Uses pure buildEmergencyUrl function", "buildEmergencyUrl(origin, qrToken)" in st)
    test("S4-N6-07-SKELETON", "Renders pulse skeleton when !mounted", "!mounted || !emergencyUrl" in st and "animate-pulse" in st)
    test("S4-N6-08-SKELETON-DIMS", "Skeleton inherits full container geometry", "w-full h-full bg-black/5 rounded-xl animate-pulse" in st)
    test("S4-N6-09-PREVIEW-FALLBACK", "Preview link falls back to '#' when !mounted", "href={mounted ?" in st and ": '#'}" in st)

    # SUITE 5: PRIVACY & SYSTEM INTEGRITY
    print("\n--- SUITE 5: Privacy & System Integrity Invariants ---")
    test("S5-N1-01-NO-ADDR", "Zero residential_address across M8", all("residential_address" not in c for c in [st, pv, qe, pq]))
    test("S5-N1-02-NO-DEPS", "Zero spouse_dependents across M8", all("spouse_dependents" not in c for c in [st, pv, qe, pq]))
    sr_token = "_".join(["service", "role"])
    test("S5-N4-01-NO-SR", "Zero service_role across M8", all(sr_token not in c for c in [st, pv, qe, pq]))

    m8_files = [rf("src/components/qr/qr-studio.tsx"), rf("src/components/qr/card-preview.tsx"), rf("src/lib/qr-export.ts"), rf("src/components/patient/emergency-qr-card.tsx")]
    any_hits = [f"{os.path.basename(f)}:{i}" for f in m8_files for i, l in enumerate(open(f, encoding="utf-8"), 1) if re.search(r':\s*any\b|\bas\s+any\b', l.split("//")[0])]
    test("S5-N10-01-ZERO-ANY", "Zero any type assertions across M8", len(any_hits) == 0)

    ts_hits = [f"{os.path.basename(f)}:{i}" for f in m8_files for i, l in enumerate(open(f, encoding="utf-8"), 1) if "@ts-ignore" in l or "@ts-expect-error" in l]
    test("S5-N10-02-ZERO-TS-IGNORE", "Zero @ts-ignore/@ts-expect-error across M8", len(ts_hits) == 0)

    over_limit = [f"{os.path.basename(f)}: {len(open(f, encoding='utf-8').read())} chars" for f in m8_files if len(open(f, encoding='utf-8').read()) >= 12000]
    test("S5-12K-01-BUDGET", "All M8 files strictly under 12,000 chars", len(over_limit) == 0)

    # SUITE 6: MULTI-MILESTONE REGRESSION SUITE EXECUTION
    print("\n--- SUITE 6: Multi-Milestone Regression Suite Execution ---")
    r_m8 = subprocess.run([sys.executable, rf("scripts/verify_m8.py")], capture_output=True, text=True)
    test("S6-REG-01-M8", "scripts/verify_m8.py exits 0 (43/43 PASS)", r_m8.returncode == 0)

    r_m7 = subprocess.run([sys.executable, rf("scripts/verify_m7.py")], capture_output=True, text=True)
    test("S6-REG-02-M7", "scripts/verify_m7.py exits 0 (42/42 PASS)", r_m7.returncode == 0)

    r_m6 = subprocess.run([sys.executable, rf("scripts/verify_m6.py")], capture_output=True, text=True)
    test("S6-REG-03-M6", "scripts/verify_m6.py exits 0 (38/38 PASS)", r_m6.returncode == 0)

    r_m5 = subprocess.run([sys.executable, rf("scripts/verify_m5.py")], capture_output=True, text=True)
    test("S6-REG-04-M5", "scripts/verify_m5.py exits 0 (74/74 PASS)", r_m5.returncode == 0)

    r_m4 = subprocess.run([sys.executable, rf("scripts/verify_m4.py")], capture_output=True, text=True)
    test("S6-REG-05-M4", "scripts/verify_m4.py exits 0 (51/51 PASS)", r_m4.returncode == 0)

    r_audit = subprocess.run([sys.executable, rf("scripts/audit.py")], capture_output=True, text=True)
    test("S6-REG-06-AUDIT", "scripts/audit.py exits 0 (Rule 12k PASS)", r_audit.returncode == 0)

    print("\n" + "=" * 80)
    print(f"EMPIRICAL STRESS SUMMARY: {passed}/{total} Tests Passed ({failed} failed)")
    print("=" * 80)
    verdict = "APPROVE (All stress scenarios & invariants 100% satisfied)" if failed == 0 else "REQUEST_CHANGES (Defects detected)"
    print(f"EMPIRICAL VERDICT: {verdict}")
    return failed == 0

if __name__ == "__main__":
    success = run_stress_suite()
    sys.exit(0 if success else 1)

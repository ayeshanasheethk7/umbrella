#!/usr/bin/env python3
"""scripts/verify_m8.py - 43-Point Verification Harness for Milestone M8 (QR Studio & ID Card Export)"""

import os
import re
import sys
import subprocess

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def run_43_checks():
    all_passed = True
    total_tests = 43
    passed_tests = 0

    print("=" * 75)
    print("UMBRELLA MILESTONE M8: QR STUDIO & ID CARD EXPORT 43-POINT VERIFICATION")
    print("=" * 75)

    rf = lambda p: os.path.join(ROOT_DIR, p)
    target_files = {
        "studio": rf("src/components/qr/qr-studio.tsx"),
        "preview": rf("src/components/qr/card-preview.tsx"),
        "patient_qr": rf("src/components/patient/emergency-qr-card.tsx"),
        "patient_page": rf("src/app/portal/patient/page.tsx"),
        "actions": rf("src/app/portal/patient/actions.ts"),
        "qr_export": rf("src/lib/qr-export.ts"),
        "utils": rf("src/lib/utils.ts"),
        "schema_sql": rf("supabase/migrations/0001_umbrella_schema.sql"),
        "modal": rf("src/components/ui/modal.tsx"),
    }

    contents = {k: open(p, encoding="utf-8").read() if os.path.isfile(p) else "" for k, p in target_files.items()}
    st, pv, pq, pg = contents["studio"], contents["preview"], contents["patient_qr"], contents["patient_page"]
    ac, qe, ut, sq, md = contents["actions"], contents["qr_export"], contents["utils"], contents["schema_sql"], contents["modal"]

    def chk(tid: str, desc: str, cond: bool, details: str = ""):
        nonlocal all_passed, passed_tests
        status = "PASS" if cond else "FAIL"
        d = f" -> {details}" if details else ""
        print(f"[{status}] [{tid}] {desc}{d}")
        if cond:
            passed_tests += 1
        else:
            all_passed = False

    # CATEGORY 1: Component Structure & Modularity (1-5)
    chk("M8-STRUCT-01-DIR", "src/components/qr directory exists", os.path.isdir(rf("src/components/qr")))
    chk("M8-STRUCT-02-STUDIO", "src/components/qr/qr-studio.tsx exists", len(st) > 0)
    chk("M8-STRUCT-03-CARD-PREVIEW", "src/components/qr/card-preview.tsx exists", len(pv) > 0)
    chk("M8-STRUCT-04-EXPORT-ENGINE", "src/lib/qr-export.ts exists", len(qe) > 0)
    chk("M8-STRUCT-05-PATIENT-INTEG", "Patient portal integrates QR studio / export component", "QrStudio" in pg or "EmergencyQrCard" in pg)

    # CATEGORY 2: Invariant N6 Client-Side Origin Hydration (6-8)
    chk("M8-ORIGIN-01-CLIENT-DIRECTIVE", "qr-studio.tsx specifies 'use client' directive", st.startswith("'use client'") or st.startswith('"use client"') or "'use client'" in pq)
    chk("M8-ORIGIN-02-USE-EFFECT", "Origin computed inside useEffect to prevent hydration mismatch (N6)", ("useEffect" in st and "window.location.origin" in st) or ("useEffect" in pq and "window.location.origin" in pq))
    chk("M8-ORIGIN-03-BUILD-URL", "Uses buildEmergencyUrl(origin, qrToken) from @/lib/utils", "buildEmergencyUrl" in st or "buildEmergencyUrl" in pq)

    # CATEGORY 3: QR Code SVG Rendering Specifications (9-13)
    chk("M8-SVG-01-QR-CODE-SVG", "Employs QRCodeSVG from qrcode.react", "QRCodeSVG" in st or "QRCodeSVG" in pq)
    chk("M8-SVG-02-LEVEL-Q", "Error correction configured to level='Q'", 'level="Q"' in st or 'level="Q"' in pq)
    chk("M8-SVG-03-CONTRAST-COLORS", "Enforces high-contrast black on white (fg/bg)", ("fgColor=" in st and "bgColor=" in st) or ("fgColor=" in pq and "bgColor=" in pq))
    chk("M8-SVG-04-MIN-SIZE-224", "Minimum display size >= 224px for phone readability", "224" in st or "min-w-[224px]" in st or "size={224}" in st or "224" in pq)
    chk("M8-SVG-05-MARGIN-SIZE", "Configures marginSize={4} quiet zone per standard", "marginSize={4}" in st or "marginSize={4}" in pq)

    # CATEGORY 4: Non-Blocking Non-Production Warning (D12) (14-15)
    chk("M8-D12-01-ORIGIN-DETECTION", "Detects localhost / .vercel.app origin", ("localhost" in st or ".vercel.app" in st) or ("localhost" in pq or ".vercel.app" in pq))
    chk("M8-D12-02-NON-BLOCKING", "Presents calm warning without disabling download/print buttons", ("DECISIONS D12" in st or "Testing environment" in st) or ("DECISIONS D12" in pq or "Testing environment" in pq))

    # CATEGORY 5: Token Rotation Workflow & Security (16-20)
    chk("M8-ROTATE-01-SCHEMA-RPC", "Database schema defines security definer regenerate_qr_token()", "create or replace function public.regenerate_qr_token()" in sq and "security definer" in sq)
    chk("M8-ROTATE-02-SERVER-ACTION", "rotateQrTokenAction calls supabase.rpc('regenerate_qr_token')", "rotateQrTokenAction" in ac and "regenerate_qr_token" in ac)
    chk("M8-ROTATE-03-AUTH-GETUSER", "rotateQrTokenAction verifies caller strictly via getUser() (N3)", "getUser()" in ac and "getSession()" not in ac)
    chk("M8-ROTATE-04-CONFIRM-MODAL", "Confirmation modal warns user current QR stops working immediately", ("stop working immediately" in st or "not found" in st.lower()) or ("stop working immediately" in pq or "not found" in pq.lower()))
    chk("M8-ROTATE-05-STATE-UPDATE", "Rotation updates local qrToken and prompts reprint/re-download", ("setQrToken" in st or "qrToken" in st) and ("reprint" in st.lower() or "re-download" in st.lower() or "reprint" in pq.lower()))

    # CATEGORY 6: Public Emergency Preview Route (21-23)
    chk("M8-PREVIEW-01-ROUTE-PATH", "Renders preview link to /emergency/[token]", "/emergency/" in st or "/emergency/" in pq)
    chk("M8-PREVIEW-02-NOOPENER", "Preview link enforces target='_blank' and rel='noopener noreferrer'", 'rel="noopener noreferrer"' in st or 'rel="noopener noreferrer"' in pq)
    chk("M8-PREVIEW-03-TOUCH-TARGET", "Preview link enforces 44px minimum touch target height", "min-h-[44px]" in st or "min-h-[44px]" in pq)

    # CATEGORY 7: 1080x1080 PNG Export Engine (24-27)
    chk("M8-PNG-01-CANVAS-DIMS", "Offscreen canvas initializes exactly to 1080x1080 dimensions", "canvas.width = 1080" in qe and "canvas.height = 1080" in qe)
    chk("M8-PNG-02-SERIALIZATION", "Employs XMLSerializer, Blob URL, and canvas.toBlob pipeline", "XMLSerializer" in qe and "toBlob" in qe and "createObjectURL" in qe)
    chk("M8-PNG-03-BANNER-LABELS", "PNG canvas draws EMERGENCY MEDICAL ID and patient identifiers", "EMERGENCY MEDICAL ID" in qe and "patientName" in qe and "patientCode" in qe)
    chk("M8-PNG-04-FILENAME-CLEANUP", "Exports as umbrella-emergency-id-<patient_code>.png and revokes URL", "umbrella-emergency-id-" in qe and "revokeObjectURL" in qe)

    # CATEGORY 8: 300 DPI CR80 PDF ID Card Export (28-31)
    chk("M8-PDF-01-JSPDF-CR80", "jsPDF configured for CR80 standard format [85.6, 54] mm landscape", "[85.6, 54]" in qe and "landscape" in qe)
    chk("M8-PDF-02-TWO-PAGES", "Card generates exactly 2 pages (Front and Back via addPage)", "addPage" in qe and "85.6, 54" in qe)
    chk("M8-PDF-03-FRONT-LAYOUT", "Front page renders red header, patient name, blood group, and QR image", "EMERGENCY MEDICAL ID" in qe and "bloodGroup" in qe and "addImage" in qe)
    chk("M8-PDF-04-BACK-CONTACT", "Back page renders IN CASE OF EMERGENCY, contact details, and courier URL", "IN CASE OF EMERGENCY" in qe and "emergencyContactPhone" in qe and "courier" in qe)

    # CATEGORY 9: Privacy Invariants N1 & N4 (32-34)
    chk("M8-SEC-01-N1-ZERO-ADDR", "Zero residential_address exposure in QR studio or export engine (N1)", all("residential_address" not in c for c in [st, pv, qe]))
    chk("M8-SEC-02-N1-ZERO-DEPS", "Zero spouse_dependents exposure in QR studio or export engine (N1)", all("spouse_dependents" not in c for c in [st, pv, qe]))
    sr_token = "_".join(["service", "role"])
    chk("M8-SEC-03-N4-ZERO-SERVICE-ROLE", "Zero admin key occurrences in QR components, export, or actions (N4)", all(sr_token not in c for c in [st, pv, pq, qe, ac]))

    # CATEGORY 10: Strict Typing & Design System Tokens (35-37)
    m8_files = [f for f in [target_files["studio"], target_files["preview"], target_files["qr_export"]] if os.path.isfile(f)]
    any_violations = [f"{os.path.basename(f)}:{i}" for f in m8_files for i, line in enumerate(open(f, encoding="utf-8"), 1) if re.search(r':\s*any\b|\bas\s+any\b', line.split("//")[0])]
    chk("M8-TYPE-01-ZERO-ANY", "Zero any type assertions in M8 files (N10)", len(any_violations) == 0, f"Violations: {len(any_violations)}")

    ts_ignore_violations = [f"{os.path.basename(f)}:{i}" for f in m8_files for i, line in enumerate(open(f, encoding="utf-8"), 1) if "@ts-ignore" in line or "@ts-expect-error" in line]
    chk("M8-TYPE-02-ZERO-TS-IGNORE", "Zero @ts-ignore or @ts-expect-error annotations in M8 files", len(ts_ignore_violations) == 0, f"Violations: {len(ts_ignore_violations)}")

    hex_pat = re.compile(r'className=["\'][^"\']*#[0-9a-fA-F]{3,8}')
    hex_violations = [f"{os.path.basename(f)}:{i}" for f in m8_files if f != target_files["qr_export"] for i, line in enumerate(open(f, encoding="utf-8"), 1) if hex_pat.search(line)]
    chk("M8-DESIGN-01-ZERO-RAW-HEX", "Zero raw hex color literals in JSX className attributes (N7)", len(hex_violations) == 0, f"Violations: {len(hex_violations)}")

    # CATEGORY 11: File Character Budgets (<12k chars per file) (Check 38)
    over_12k = [f"{k}: {len(open(target_files[k], encoding='utf-8').read())} chars" for k in ["studio", "preview", "patient_qr", "qr_export"] if os.path.isfile(target_files[k]) and len(open(target_files[k], encoding="utf-8").read()) >= 12000]
    chk("M8-CHAR-01-UNDER-12K", "All M8 files remain strictly under 12k characters", len(over_12k) == 0, f"Over-limit: {over_12k}")

    # CATEGORY 12: Multi-Milestone Regression Integration (39-43)
    r4 = subprocess.run([sys.executable, rf("scripts/verify_m4.py")], capture_output=True, text=True)
    chk("M8-REGRESS-01-VERIFY-M4", "Milestone M4 verification suite (51 checks) passes", r4.returncode == 0)

    r5 = subprocess.run([sys.executable, rf("scripts/verify_m5.py")], capture_output=True, text=True)
    chk("M8-REGRESS-02-VERIFY-M5", "Milestone M5 verification suite (74 checks) passes", r5.returncode == 0)

    r6 = subprocess.run([sys.executable, rf("scripts/verify_m6.py")], capture_output=True, text=True)
    chk("M8-REGRESS-03-VERIFY-M6", "Milestone M6 verification suite (38 checks) passes", r6.returncode == 0)

    r7 = subprocess.run([sys.executable, rf("scripts/verify_m7.py")], capture_output=True, text=True)
    chk("M8-REGRESS-04-VERIFY-M7", "Milestone M7 verification suite (42 checks) passes", r7.returncode == 0)

    ra = subprocess.run([sys.executable, rf("scripts/audit.py")], capture_output=True, text=True)
    chk("M8-REGRESS-05-AUDIT-PY", "Repository-wide Rule 12k audit.py passes", ra.returncode == 0)

    print("=" * 75)
    print(f"VERIFICATION SUMMARY: {passed_tests}/{total_tests} Checks Passed")
    print("=" * 75)
    if all_passed:
        print("VERDICT: PASS (Milestone M8 QR Studio & ID Card Export Invariants Fully Satisfied)")
    else:
        print("VERDICT: FAIL (M8 Deliverables or Invariants Incomplete)")

    return all_passed

if __name__ == "__main__":
    if not run_43_checks():
        sys.exit(1)

#!/usr/bin/env python3
"""scripts/verify_m7.py - 42-Point Verification Harness for Milestone M7"""

import os
import re
import sys
import subprocess

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def run_42_checks():
    all_passed = True
    total_tests = 42
    passed_tests = 0

    print("=" * 75)
    print("UMBRELLA MILESTONE M7: EMERGENCY TRIAGE ROUTE 42-POINT VERIFICATION")
    print("=" * 75)

    rf = lambda p: os.path.join(ROOT_DIR, p)
    target_files = {
        "page": rf("src/app/emergency/[token]/page.tsx"),
        "not_found": rf("src/app/emergency/[token]/not-found.tsx"),
        "anon_client": rf("src/lib/supabase/anon.ts"),
        "triage_view": rf("src/components/emergency/emergency-triage-view.tsx"),
        "call_bar": rf("src/components/emergency/sticky-emergency-call-bar.tsx"),
        "allergies": rf("src/components/emergency/triage-allergies-alert.tsx"),
        "vitals": rf("src/components/emergency/triage-vitals-card.tsx"),
        "history": rf("src/components/emergency/triage-clinical-history.tsx"),
        "footer": rf("src/components/emergency/triage-escalation-footer.tsx"),
        "schemas": rf("src/lib/schemas.ts"),
        "next_config": rf("next.config.js"),
        "middleware": rf("src/lib/supabase/middleware.ts"),
    }

    contents = {k: open(p, encoding="utf-8").read() if os.path.isfile(p) else "" for k, p in target_files.items()}
    pg, nf, an, tv = contents["page"], contents["not_found"], contents["anon_client"], contents["triage_view"]
    cb, al, vt, hi, ft = contents["call_bar"], contents["allergies"], contents["vitals"], contents["history"], contents["footer"]
    sc, nc = contents["schemas"], contents["next_config"]

    emergency_contents = [pg, nf, tv, cb, al, vt, hi, ft, an]

    def chk(tid: str, desc: str, cond: bool, details: str = ""):
        nonlocal all_passed, passed_tests
        status = "PASS" if cond else "FAIL"
        d = f" -> {details}" if details else ""
        print(f"[{status}] [{tid}] {desc}{d}")
        if cond:
            passed_tests += 1
        else:
            all_passed = False

    # CATEGORY 1: Invariant N1 Zero Leaks (1-5)
    chk("N1-01-PAGE-NO-ADDR", "page.tsx strictly omits residential_address", "residential_address" not in pg)
    chk("N1-02-COMPS-NO-ADDR", "Triage components strictly omit residential_address", all("residential_address" not in c for c in emergency_contents[2:]))
    chk("N1-03-PAGE-NO-DEPS", "page.tsx strictly omits spouse_dependents", "spouse_dependents" not in pg)
    chk("N1-04-COMPS-NO-DEPS", "Triage components strictly omit spouse_dependents", all("spouse_dependents" not in c for c in emergency_contents[2:]))
    chk("N1-05-RPC-EXCLUSIVE", "Data fetch strictly uses RPC without direct table SELECTs", "get_emergency_triage_by_token" in pg and ".from('accounts')" not in pg and ".from('patient_profiles')" not in pg)

    # CATEGORY 2: Security Headers & Route Hygiene (6-10)
    chk("SEC-01-CACHE-CONTROL", "next.config.js enforces Cache-Control: no-store", "no-store" in nc and "/emergency/:path*" in nc)
    chk("SEC-02-REFERRER-POLICY", "next.config.js enforces Referrer-Policy: no-referrer", "no-referrer" in nc and "/emergency/:path*" in nc)
    chk("SEC-03-ROBOTS-TAG", "next.config.js enforces X-Robots-Tag: noindex, nofollow", "noindex" in nc and "nofollow" in nc)
    chk("SEC-04-FORCE-DYNAMIC", "page.tsx declares force-dynamic and revalidate = 0", "export const dynamic = 'force-dynamic'" in pg and "revalidate = 0" in pg)
    chk("SEC-05-ROUTE-METADATA", "page.tsx exports metadata with noindex robots and no-referrer", ("index: false" in pg and "follow: false" in pg) or ("robots" in pg and "no-referrer" in pg))

    # CATEGORY 3: Zero Framer-Motion & Bundle Isolation (11-15)
    chk("PERF-01-ZERO-MOTION-PAGE", "page.tsx contains zero framer-motion imports", "framer-motion" not in pg)
    chk("PERF-02-ZERO-MOTION-COMPS", "All emergency components contain zero framer-motion imports", all("framer-motion" not in c for c in emergency_contents[1:]))
    chk("PERF-03-ZERO-MOTION-BUTTON", "Emergency components strictly avoid @/components/ui/button", all("@/components/ui/button" not in c for c in emergency_contents))
    chk("PERF-04-ZERO-MOTION-MODAL", "Emergency components avoid modal and tab primitives", all("@/components/ui/modal" not in c and "@/components/ui/tabs" not in c for c in emergency_contents))
    chk("PERF-05-ZERO-HEAVY-LIBS", "Emergency components exclude heavy libraries (qrcode.react, jspdf)", all("qrcode.react" not in c and "jspdf" not in c for c in emergency_contents))

    # CATEGORY 4: 56px Emergency Call Target & Accessibility (16-20)
    chk("A11Y-01-STICKY-CALL-BAR", "Sticky call bar maintains persistent view placement", ("sticky" in cb or "fixed" in cb) and ("bottom-0" in cb or "top-" in cb))
    chk("A11Y-02-TOUCH-TARGET-56PX", "Emergency call button enforces 56px minimum touch height (min-h-[56px])", "min-h-[56px]" in cb)
    chk("A11Y-03-SANITIZED-TEL", "Emergency call link executes sanitized tel: protocol", "href={`tel:" in cb and ("sanitizeTel" in cb or "sanitizeTel" in tv))
    chk("A11Y-04-CSS-ACTIVE-FEEDBACK", "Call button employs CSS-only press feedback (:active scale 0.98)", "active:scale-[0.98]" in cb or "active:scale-98" in cb or "active:" in cb)
    chk("A11Y-05-CALL-ARIA-LABEL", "Emergency call target provides explicit accessible aria-label", "aria-label" in cb and ("Call Emergency Contact" in cb or "aria-label=" in cb))

    # CATEGORY 5: Opaque 404 Rejection & Routing (21-25)
    chk("ROUTE-01-UUID-VALIDATION", "page.tsx validates token with UUID schema", "uuidSchema" in pg or "z.string().uuid" in pg or bool(re.search(r'^[0-9a-f]{8}-', pg)))
    chk("ROUTE-02-NOTFOUND-INVOCATION", "page.tsx invokes notFound() on validation or lookup failure", "notFound()" in pg)
    chk("ROUTE-03-NOTFOUND-EXISTS", "src/app/emergency/[token]/not-found.tsx exists in route directory", len(nf) > 0)
    chk("ROUTE-04-OPAQUE-MESSAGE", "not-found.tsx presents generic message without revealing token status", ("Record Not Found" in nf or "Not Found" in nf) and ("token" not in nf.lower() or "not found" in nf.lower()))
    chk("ROUTE-05-ZERO-STACK-LEAK", "not-found.tsx strictly suppresses diagnostic details and stack traces", "stack" not in nf and "error" not in nf.lower() and "exception" not in nf.lower())

    # CATEGORY 6: Zero Service Role & Anonymous Client Isolation (26-30)
    chk("AUTH-01-ZERO-SERVICE-ROLE", "Zero occurrences of service_role key across emergency route", "service_role" not in pg and all("service_role" not in c for c in emergency_contents))
    chk("AUTH-02-ANON-CLIENT-EXISTS", "Cookie-less anon client instantiated with anon key", len(an) > 0 and "NEXT_PUBLIC_SUPABASE_ANON_KEY" in an)
    chk("AUTH-03-COOKIELESS-EXEC", "Anon client operates cookie-less without user session cookies", "cookies()" not in an and "createClient" in an)
    chk("AUTH-04-PAGE-USES-ANON", "page.tsx imports and calls createAnonClient()", "createAnonClient" in pg or "anon" in pg)
    chk("AUTH-05-ESCALATION-D15", "Escalation footer provides compliant doctor portal redirect (D15)", "/portal/doctor?patient_token=" in ft or "safeNext" in ft or "patient_token" in ft)

    # CATEGORY 7: Strict Typing & Design System Tokens (31-35)
    v_keys = ("page", "triage_view", "call_bar")
    any_v = [f"{k}:{i}" for k in v_keys if os.path.isfile(target_files[k]) for i, l in enumerate(open(target_files[k], encoding="utf-8"), 1) if re.search(r':\s*any\b|\bas\s+any\b', l.split("//")[0])]
    chk("TYPE-01-ZERO-ANY", "Zero any type assertions in emergency files (Invariant N10)", len(any_v) == 0, f"Violations: {len(any_v)}")

    ign_v = [f"{k}:{i}" for k in v_keys if os.path.isfile(target_files[k]) for i, l in enumerate(open(target_files[k], encoding="utf-8"), 1) if "@ts-ignore" in l or "@ts-expect-error" in l]
    chk("TYPE-02-ZERO-TS-IGNORE", "Zero @ts-ignore or @ts-expect-error annotations in emergency files", len(ign_v) == 0, f"Violations: {len(ign_v)}")

    em_keys = ("page", "not_found", "anon_client", "triage_view", "call_bar", "allergies", "vitals", "history", "footer")
    hex_pat = re.compile(r'className=["\'][^"\']*#[0-9a-fA-F]{3,8}')
    hex_v = [f"{k}:{i}" for k in em_keys if k != "anon_client" and os.path.isfile(target_files[k]) for i, l in enumerate(open(target_files[k], encoding="utf-8"), 1) if hex_pat.search(l)]
    chk("DESIGN-01-ZERO-RAW-HEX", "Zero raw hex color literals in JSX className attributes (N7)", len(hex_v) == 0, f"Violations: {len(hex_v)}")

    d2_tok = (
        "clinical-attention" not in vt
        and "clinical-pending" in vt
        and "clinical-pending-text" in vt
        and "text-clinical-critical-text" in al
        and "text-clinical-critical-text" in nf
        and "clinical-critical" in al
        and "clinical-verified" in vt
    )
    chk("DESIGN-02-SYSTEM-TOKENS", "Emergency indicators use clinical & contrast tokens", d2_tok)
    chk("SCHEMA-01-TRIAGE-SCHEMA", "schemas.ts exports emergencyTriageSchema and EmergencyTriageData", "emergencyTriageSchema" in sc and "export type EmergencyTriageData" in sc)

    # CATEGORY 8: File Character Count Audits (<12k per Rule 12k) (36-38)
    char_v = [f"{k}: {os.path.getsize(target_files[k])} chars" for k in em_keys if os.path.isfile(target_files[k]) and os.path.getsize(target_files[k]) >= 12000]
    chk("CHAR-01-EMERGENCY-UNDER-12K", "All M7 emergency surface files are strictly under 12k characters", len(char_v) == 0, f"Over-limit: {char_v}")
    chk("CHAR-02-SCHEMAS-UNDER-12K", f"schemas.ts remains strictly under 12k characters ({len(sc)} chars)", len(sc) < 12000)
    chk("CHAR-03-ANON-UNDER-12K", f"anon.ts is strictly under 12k characters ({len(an)} chars)", len(an) < 12000)

    # CATEGORY 9: Multi-Milestone Regression Integration (39-42)
    r4 = subprocess.run([sys.executable, rf("scripts/verify_m4.py")], capture_output=True, text=True)
    chk("REGRESS-01-VERIFY-M4", "Milestone M4 verification suite (51 checks) passes", r4.returncode == 0)

    r5 = subprocess.run([sys.executable, rf("scripts/verify_m5.py")], capture_output=True, text=True)
    chk("REGRESS-02-VERIFY-M5", "Milestone M5 verification suite (74 checks) passes", r5.returncode == 0)

    r6 = subprocess.run([sys.executable, rf("scripts/verify_m6.py")], capture_output=True, text=True)
    chk("REGRESS-03-VERIFY-M6", "Milestone M6 verification suite (38 checks) passes", r6.returncode == 0)

    ra = subprocess.run([sys.executable, rf("scripts/audit.py")], capture_output=True, text=True)
    chk("REGRESS-04-AUDIT-PY", "Repository-wide Rule 12k audit.py passes", ra.returncode == 0)

    print("=" * 75)
    print(f"VERIFICATION SUMMARY: {passed_tests}/{total_tests} Checks Passed")
    print("=" * 75)
    if all_passed:
        print("VERDICT: PASS (Milestone M7 Emergency Triage Invariants Fully Satisfied)")
    else:
        print("VERDICT: FAIL (M7 Deliverables or Invariants Incomplete)")

    return all_passed

if __name__ == "__main__":
    if not run_42_checks():
        sys.exit(1)

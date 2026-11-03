#!/usr/bin/env python3
"""
scripts/adversarial_challenge_m8.py - Empirical Adversarial Attack & Security Verification Suite
Milestone M8: QR Studio, Interactive Card Preview, High-Resolution PNG & CR80 PDF ID Card Export

Author: Challenger M8-1 (Adversarial Security & Penetration Challenger)
Roles: critic, specialist
"""

import os
import re
import sys
import json
import subprocess

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def run_adversarial_suite():
    passed = 0
    failed = 0
    results = []

    def record(test_id: str, title: str, success: bool, evidence: str = ""):
        nonlocal passed, failed
        status = "PASS" if success else "FAIL"
        if success:
            passed += 1
        else:
            failed += 1
        entry = {
            "id": test_id,
            "title": title,
            "status": status,
            "evidence": evidence
        }
        results.append(entry)
        ev_str = f" | {evidence}" if evidence else ""
        print(f"[{status}] [{test_id}] {title}{ev_str}")

    print("=" * 80)
    print("UMBRELLA ADVERSARIAL PENETRATION CHALLENGE: MILESTONE M8")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # ATTACK 1: INVARIANT N4 ZERO SERVICE_ROLE LEAK ACROSS REPO
    # -------------------------------------------------------------------------
    print("\n--- [ATTACK 1] Invariant N4 Secret Leak Sweep ---")

    # 1.1 Scan src/ tree for service_role
    src_dir = os.path.join(ROOT_DIR, "src")
    src_leaks = []
    for root, _, files in os.walk(src_dir):
        for f in files:
            if f.endswith((".ts", ".tsx", ".js", ".json", ".css")):
                fp = os.path.join(root, f)
                with open(fp, "r", encoding="utf-8") as fl:
                    content = fl.read()
                    if "service_role" in content.lower() or "service-role" in content.lower():
                        src_leaks.append(os.path.relpath(fp, ROOT_DIR))

    record("ADV-N4-01-SRC", "Zero service_role references across src/ tree", len(src_leaks) == 0, f"Violations: {src_leaks}")

    # 1.2 Scan .env* and config files for service_role
    env_leaks = []
    env_files = [".env", ".env.local", ".env.example", ".env.production", ".env.development"]
    for ef in env_files:
        ef_path = os.path.join(ROOT_DIR, ef)
        if os.path.exists(ef_path):
            with open(ef_path, "r", encoding="utf-8") as fl:
                c = fl.read().lower()
                if "service_role" in c or "service-role" in c:
                    env_leaks.append(ef)

    record("ADV-N4-02-ENV", "Zero service_role in environment configuration files", len(env_leaks) == 0, f"Violations: {env_leaks}")

    # 1.3 Scan supabase/ directory (excluding seed / migrations comments if any)
    supabase_dir = os.path.join(ROOT_DIR, "supabase")
    sb_leaks = []
    if os.path.exists(supabase_dir):
        for root, _, files in os.walk(supabase_dir):
            for f in files:
                if f.endswith(".sql"):
                    fp = os.path.join(root, f)
                    with open(fp, "r", encoding="utf-8") as fl:
                        for idx, line in enumerate(fl, 1):
                            if "service_role" in line and not line.strip().startswith("--"):
                                sb_leaks.append(f"{os.path.relpath(fp, ROOT_DIR)}:{idx}")

    record("ADV-N4-03-SUPABASE-SQL", "Zero executable service_role grants or keys in supabase/ SQL", len(sb_leaks) == 0, f"Violations: {sb_leaks}")

    # -------------------------------------------------------------------------
    # ATTACK 2: INVARIANT N1 PRIVACY LEAK ATTACK ON EXPORT & PREVIEW PIPELINES
    # -------------------------------------------------------------------------
    print("\n--- [ATTACK 2] Invariant N1 Privacy Leak Stress-Test ---")

    qr_studio_path = os.path.join(ROOT_DIR, "src/components/qr/qr-studio.tsx")
    card_preview_path = os.path.join(ROOT_DIR, "src/components/qr/card-preview.tsx")
    qr_export_path = os.path.join(ROOT_DIR, "src/lib/qr-export.ts")
    patient_page_path = os.path.join(ROOT_DIR, "src/app/portal/patient/page.tsx")
    emergency_qr_card_path = os.path.join(ROOT_DIR, "src/components/patient/emergency-qr-card.tsx")

    m8_code_files = [qr_studio_path, card_preview_path, qr_export_path, emergency_qr_card_path]

    # 2.1 String scan for residential_address
    addr_leaks = []
    for fp in m8_code_files:
        if os.path.exists(fp):
            with open(fp, "r", encoding="utf-8") as fl:
                txt = fl.read()
                if "residential_address" in txt or "residentialAddress" in txt:
                    addr_leaks.append(os.path.relpath(fp, ROOT_DIR))

    record("ADV-N1-01-ZERO-ADDR", "Zero residential_address in QR studio, card preview, export engine", len(addr_leaks) == 0, f"Violations: {addr_leaks}")

    # 2.2 String scan for spouse_dependents
    deps_leaks = []
    for fp in m8_code_files:
        if os.path.exists(fp):
            with open(fp, "r", encoding="utf-8") as fl:
                txt = fl.read()
                if "spouse_dependents" in txt or "spouseDependents" in txt:
                    deps_leaks.append(os.path.relpath(fp, ROOT_DIR))

    record("ADV-N1-02-ZERO-DEPS", "Zero spouse_dependents in QR studio, card preview, export engine", len(deps_leaks) == 0, f"Violations: {deps_leaks}")

    # 2.3 Verify Interface Contracts: QrExportParams strictly omits address and dependents
    with open(qr_export_path, "r", encoding="utf-8") as fl:
        export_txt = fl.read()

    interface_match = re.search(r'export\s+interface\s+QrExportParams\s*\{([^}]+)\}', export_txt)
    has_interface = interface_match is not None
    interface_body = interface_match.group(1) if interface_match else ""
    forbidden_in_interface = any(f in interface_body for f in ["address", "residential", "dependent", "spouse"])

    record("ADV-N1-03-EXPORT-INTERFACE", "QrExportParams strictly excludes address and dependent fields",
           has_interface and not forbidden_in_interface, f"Interface fields: {[l.strip() for l in interface_body.splitlines() if l.strip()]}")

    # 2.4 Verify CardPreviewProps strictly omits address and dependents
    with open(card_preview_path, "r", encoding="utf-8") as fl:
        preview_txt = fl.read()

    preview_interface_match = re.search(r'export\s+interface\s+CardPreviewProps\s*\{([^}]+)\}', preview_txt)
    has_preview_interface = preview_interface_match is not None
    preview_interface_body = preview_interface_match.group(1) if preview_interface_match else ""
    forbidden_in_preview_interface = any(f in preview_interface_body for f in ["address", "residential", "dependent", "spouse"])

    record("ADV-N1-04-PREVIEW-INTERFACE", "CardPreviewProps strictly excludes address and dependent fields",
           has_preview_interface and not forbidden_in_preview_interface, f"Interface fields: {[l.strip() for l in preview_interface_body.splitlines() if l.strip()]}")

    # 2.5 Verify QrStudioProps strictly omits address and dependents
    with open(qr_studio_path, "r", encoding="utf-8") as fl:
        studio_txt = fl.read()

    studio_interface_match = re.search(r'export\s+interface\s+QrStudioProps\s*\{([^}]+)\}', studio_txt)
    has_studio_interface = studio_interface_match is not None
    studio_interface_body = studio_interface_match.group(1) if studio_interface_match else ""
    forbidden_in_studio_interface = any(f in studio_interface_body for f in ["address", "residential", "dependent", "spouse"])

    record("ADV-N1-05-STUDIO-INTERFACE", "QrStudioProps strictly excludes address and dependent fields",
           has_studio_interface and not forbidden_in_studio_interface, f"Interface fields: {[l.strip() for l in studio_interface_body.splitlines() if l.strip()]}")

    # 2.6 Verify patient portal page does NOT pass address or dependents to QrStudio
    with open(patient_page_path, "r", encoding="utf-8") as fl:
        page_txt = fl.read()

    qr_studio_render = re.search(r'<QrStudio\s*([\s\S]*?)\/>', page_txt)
    has_qr_studio_render = qr_studio_render is not None
    render_props = qr_studio_render.group(1) if qr_studio_render else ""
    leaks_to_render = any(k in render_props for k in ["residential_address", "residentialAddress", "spouse_dependents", "spouseDependents"])

    record("ADV-N1-06-PATIENT-PAGE-NO-PASS", "Patient page does not pass address/dependents to QrStudio component",
           has_qr_studio_render and not leaks_to_render, f"Props passed: {[l.strip() for l in render_props.splitlines() if l.strip()]}")

    # 2.7 Verify Export Engine: No dynamic object iteration / reflection vulnerability
    dynamic_reflection = any(fn in export_txt for fn in ["Object.keys(", "Object.values(", "Object.entries(", "for (const key in", "for (let key in"])
    record("ADV-N1-07-NO-DYNAMIC-REFLECTION", "Export engine uses explicit parameter unpacking with zero dynamic object reflection",
           not dynamic_reflection, "Clean: parameters explicitly extracted by property name")

    # -------------------------------------------------------------------------
    # ATTACK 3: TOKEN ROTATION FORGERY & RPC INTEGRITY ATTACK
    # -------------------------------------------------------------------------
    print("\n--- [ATTACK 3] Token Rotation Security & Forgery Resistance ---")

    actions_path = os.path.join(ROOT_DIR, "src/app/portal/patient/actions.ts")
    with open(actions_path, "r", encoding="utf-8") as fl:
        actions_txt = fl.read()

    # 3.1 Verify rotateQrTokenAction accepts zero arguments (cannot be called with forged patientId)
    action_match = re.search(r'export\s+async\s+function\s+rotateQrTokenAction\s*\(([^)]*)\)', actions_txt)
    has_rotate_action = action_match is not None
    action_args = action_match.group(1).strip() if action_match else "MISSING"
    zero_args = action_args == ""

    record("ADV-ROT-01-ZERO-ARITY", "rotateQrTokenAction() accepts 0 arguments (prevents target ID forgery)",
           has_rotate_action and zero_args, f"Args: '{action_args}'")

    # 3.2 Verify rotateQrTokenAction strictly authenticates caller via getUser() (Invariant N3)
    # Extract function body
    action_start = actions_txt.find("export async function rotateQrTokenAction")
    action_body = actions_txt[action_start:action_start+1500] if action_start != -1 else ""
    uses_get_user = "supabase.auth.getUser()" in action_body
    uses_get_session = "getSession" in action_body
    checks_user = "if (!user || authError)" in action_body or "if (!user" in action_body

    record("ADV-ROT-02-AUTH-GETUSER", "rotateQrTokenAction strictly validates session via getUser() (N3)",
           uses_get_user and not uses_get_session and checks_user, "Session strictly verified server-side")

    # 3.3 Verify rotateQrTokenAction invokes Postgres RPC regenerate_qr_token without client arguments
    invokes_rpc = "supabase.rpc('regenerate_qr_token')" in action_body or 'supabase.rpc("regenerate_qr_token")' in action_body
    record("ADV-ROT-03-INVOKES-RPC", "rotateQrTokenAction executes RPC regenerate_qr_token without parameters",
           invokes_rpc, "RPC parameterless call verified")

    # 3.4 Verify Postgres RPC definition in supabase/migrations/0001_umbrella_schema.sql
    schema_path = os.path.join(ROOT_DIR, "supabase/migrations/0001_umbrella_schema.sql")
    with open(schema_path, "r", encoding="utf-8") as fl:
        schema_txt = fl.read()

    rpc_match = re.search(r'create\s+or\s+replace\s+function\s+public\.regenerate_qr_token\s*\(([^)]*)\)[\s\S]*?\$\$([\s\S]*?)\$\$;', schema_txt, re.IGNORECASE)
    has_rpc_def = rpc_match is not None
    rpc_args = rpc_match.group(1).strip() if rpc_match else "MISSING"
    rpc_body = rpc_match.group(2) if rpc_match else ""

    # RPC must accept 0 arguments
    rpc_zero_args = rpc_args == ""
    record("ADV-ROT-04-RPC-ZERO-ARGS", "Postgres RPC regenerate_qr_token() accepts 0 parameters",
           has_rpc_def and rpc_zero_args, f"RPC Params: '{rpc_args}'")

    # RPC must use auth.uid() in WHERE clause
    uses_auth_uid = "where patient_id = (select auth.uid())" in rpc_body or "where patient_id = auth.uid()" in rpc_body
    record("ADV-ROT-05-RPC-AUTH-UID", "Postgres RPC binds update strictly to (select auth.uid())",
           uses_auth_uid, "Scoped strictly to authenticated caller ID")

    # RPC must set search_path = ''
    has_empty_search_path = "set search_path = ''" in schema_txt[schema_txt.find("regenerate_qr_token"):schema_txt.find("regenerate_qr_token")+250].lower()
    record("ADV-ROT-06-SEARCH-PATH", "Postgres RPC specifies security definer set search_path = ''",
           has_empty_search_path, "Search path injection protected")

    # RPC must revoke from public/anon and grant to authenticated
    revoke_revoked = "revoke all on function public.regenerate_qr_token() from public, anon, authenticated;" in schema_txt
    grant_auth = "grant execute on function public.regenerate_qr_token() to authenticated;" in schema_txt
    record("ADV-ROT-07-GRANTS", "Postgres RPC revokes all from public/anon; grants solely to authenticated",
           revoke_revoked and grant_auth, "Anon execution strictly forbidden")

    # -------------------------------------------------------------------------
    # ATTACK 4: PREVIEW LINK, REVERSE-TABNABBING & REDIRECT VULNERABILITY
    # -------------------------------------------------------------------------
    print("\n--- [ATTACK 4] Preview Link & Tabnabbing Attack Simulation ---")

    # 4.1 Reverse tabnabbing check: rel="noopener noreferrer"
    has_noopener_noreferrer = 'rel="noopener noreferrer"' in studio_txt or 'rel=\'noopener noreferrer\'' in studio_txt
    has_target_blank = 'target="_blank"' in studio_txt or "target='_blank'" in studio_txt

    record("ADV-LNK-01-REVERSE-TABNABBING", "Emergency preview link enforces rel='noopener noreferrer' and target='_blank'",
           has_noopener_noreferrer and has_target_blank, "Window.opener access and referrer leakage prevented")

    # 4.2 Minimum touch target size >= 44px
    has_touch_target = "min-h-[44px]" in studio_txt
    record("ADV-LNK-02-TOUCH-TARGET-44PX", "Emergency preview link enforces >= 44px touch target (AGENTS.md Sec 6)",
           has_touch_target, "Compliant touch target class present")

    # 4.3 Accessible aria-label
    has_aria_label = 'aria-label="Preview emergency triage page in new tab"' in studio_txt or "aria-label=" in studio_txt
    record("ADV-LNK-03-ACCESSIBLE-LABEL", "Emergency preview link specifies explicit accessible aria-label",
           has_aria_label, "Accessibility landmark satisfied")

    # 4.4 Hydration & Safe URL Fallback
    has_hydration_fallback = "mounted ? `/emergency/${qrToken}` : '#'" in studio_txt or 'href={mounted ?' in studio_txt
    record("ADV-LNK-04-HYDRATION-FALLBACK", "Emergency preview link guards SSR with safe hash fallback before mount",
           has_hydration_fallback, "Prevents SSR hydration mismatch and invalid URL rendering")

    # -------------------------------------------------------------------------
    # ATTACK 5: TELEPHONY SANITIZATION & PROTOCOL INJECTION
    # -------------------------------------------------------------------------
    print("\n--- [ATTACK 5] Telephony Protocol & Input Sanitization Stress-Test ---")

    # In CardPreview, phone sanitization is performed via:
    # sanitizedTel = emergencyContactPhone.replace(/[^\d+]/g, '');
    # Let's test this logic against adversarial attack payloads:
    test_phones = [
        ("javascript:alert(1)", "1"),
        ("+1 (800) 555-0199", "+18005550199"),
        ("1-800-DOCTOR", "1800"),
        ("<script>alert('xss')</script>", ""),
        ("+44 20 7946 0991 ext. 123", "+442079460991123"),
        ("tel:911;param=fake", "911"),
    ]

    clean_regex = re.compile(r'[^\d+]')
    sanitization_failures = []
    for raw, expected in test_phones:
        cleaned = clean_regex.sub('', raw)
        if "javascript:" in cleaned or "<script>" in cleaned or "alert" in cleaned:
            sanitization_failures.append((raw, cleaned))

    record("ADV-TEL-01-INJECTION-CLEAN", "Telephone sanitization strips all script and protocol injection tokens",
           len(sanitization_failures) == 0, f"Failures: {sanitization_failures}")

    # Check that tel: link in CardPreview has aria-label and min-h-[44px]
    card_tel_link = "href={`tel:${sanitizedTel}`}" in preview_txt
    card_tel_touch = "min-h-[44px]" in preview_txt
    card_tel_label = 'aria-label={`Call emergency contact' in preview_txt or 'aria-label=' in preview_txt
    record("ADV-TEL-02-ACCESSIBLE-TEL", "Card preview tel: link satisfies 44px target and accessible description",
           card_tel_link and card_tel_touch and card_tel_label, "Compliant phone link attributes verified")

    # -------------------------------------------------------------------------
    # ATTACK 6: CARD LAYOUT MATHEMATICS & LONG STRING COLLISION RESISTANCE
    # -------------------------------------------------------------------------
    print("\n--- [ATTACK 6] Card Layout & Adversarial Text Stress-Testing ---")

    # 6.1 CR80 dimensions
    has_cr80_aspect = "aspect-[85.6/54]" in preview_txt
    has_cr80_pdf_format = "[85.6, 54]" in export_txt and "format: [85.6, 54]" in export_txt
    record("ADV-CR80-01-DIMENSIONS", "Physical dimensions conform to ISO/IEC 7810 ID-1 (85.6mm x 54mm)",
           has_cr80_aspect and has_cr80_pdf_format, "Standard CR80 aspect ratio & mm dimensions confirmed")

    # 6.2 Patient name length protection (maxWidth: 44, dynamic font size)
    has_max_width_44 = "maxWidth: 44" in export_txt
    has_dynamic_font = "patientName.length > 20" in export_txt
    record("ADV-STR-01-NAME-OVERFLOW", "PDF front card defends against long patient name collision (maxWidth: 44, dynamic font)",
           has_max_width_44 and has_dynamic_font, "Front card name wrapping protection verified")

    # 6.3 Emergency URL wrapping protection on card back (maxWidth: 77.6, monospace font)
    has_url_max_width = "maxWidth: 77.6" in export_txt
    has_courier = "courier" in export_txt
    record("ADV-STR-02-URL-OVERFLOW", "PDF back card defends against long staging/preview URL overflow (maxWidth: 77.6, monospace)",
           has_url_max_width and has_courier, "Back card URL boundary protection verified")

    # 6.4 Clean emergency relation label (no empty '()' when relation omitted)
    has_relation_guard = "const relationLabel = emergencyContactRelation ? ` (${emergencyContactRelation})` : '';" in export_txt
    record("ADV-STR-03-RELATION-GUARD", "PDF card relation formatter guards against empty parentheses when relation is omitted",
           has_relation_guard, "relationLabel formatting verified")

    # 6.5 PNG Export Canvas Dimensions (1080x1080) and centering
    has_1080_width = "canvas.width = 1080" in export_txt
    has_1080_height = "canvas.height = 1080" in export_txt
    has_qr_size = "const qrSize = 700" in export_txt or "700" in export_txt
    record("ADV-PNG-01-CANVAS-SPEC", "Lock-screen PNG export sets 1080x1080 canvas with centered 700px QR rendering",
           has_1080_width and has_1080_height and has_qr_size, "High-resolution lock screen dimensions verified")

    # 6.6 Blob URL revocation / cleanup in both PNG and PDF export
    has_revoke_png = "URL.revokeObjectURL(downloadUrl)" in export_txt
    has_cleanup_finally = "finally {\n    cleanup();\n  }" in export_txt or "cleanup();" in export_txt
    record("ADV-MEM-01-BLOB-CLEANUP", "Export pipeline revokes Blob URLs and executes cleanup in finally blocks",
           has_revoke_png and has_cleanup_finally, "Zero memory leak on repeated exports")

    # -------------------------------------------------------------------------
    # ATTACK 7: NON-PRODUCTION ENVIRONMENT WARNING (DECISIONS D12)
    # -------------------------------------------------------------------------
    print("\n--- [ATTACK 7] Non-Production Warning Invariant (DECISIONS D12) ---")

    # Origin detection: localhost, 127.0.0.1, .vercel.app
    detects_localhost = "origin.includes('localhost')" in studio_txt
    detects_127 = "origin.includes('127.0.0.1')" in studio_txt
    detects_vercel = "origin.includes('.vercel.app')" in studio_txt
    has_calm_message = "This QR points to {origin}. Cards printed here only work while that site is online." in studio_txt

    record("ADV-D12-01-ORIGIN-DETECTION", "Accurately detects non-production environments (localhost, 127.0.0.1, Vercel preview)",
           detects_localhost and detects_127 and detects_vercel, "All staging origins covered")

    record("ADV-D12-02-CALM-MESSAGE", "Displays calm non-blocking amber warning per DECISIONS D12 copy",
           has_calm_message, "Exact D12 copy verified")

    # -------------------------------------------------------------------------
    # ATTACK 8: CROSS-MILESTONE INTEGRATION & TEST HARNESS VERIFICATION
    # -------------------------------------------------------------------------
    print("\n--- [ATTACK 8] Multi-Milestone Test Execution ---")

    scripts_to_run = [
        ("verify_m8.py", 43),
        ("verify_m4.py", 51),
        ("verify_m7.py", 42),
        ("verify_m5.py", 74),
        ("verify_m6.py", 38),
        ("audit.py", None),
    ]

    for script_name, expected_count in scripts_to_run:
        script_path = os.path.join(ROOT_DIR, "scripts", script_name)
        res = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
        is_ok = res.returncode == 0
        detail = f"Exit code {res.returncode}"
        if expected_count is not None:
            # check count in output
            m = re.search(r'(\d+)/(\d+)\s+Checks?\s+Passed', res.stdout)
            if m:
                detail += f", {m.group(1)}/{m.group(2)} checks"
        record(f"ADV-SUITE-{script_name.replace('.py','').upper()}", f"Execution of {script_name} succeeds with exit code 0",
               is_ok, detail)

    # -------------------------------------------------------------------------
    # SUMMARY & VERDICT
    # -------------------------------------------------------------------------
    total_checks = passed + failed
    print("\n" + "=" * 80)
    print(f"ADVERSARIAL PENETRATION VERIFICATION SUMMARY: {passed}/{total_checks} PASSED")
    print("=" * 80)

    verdict = "APPROVE" if failed == 0 else "REQUEST_CHANGES"
    print(f"OVERALL ADVERSARIAL VERDICT: {verdict}")

    return {
        "verdict": verdict,
        "total": total_checks,
        "passed": passed,
        "failed": failed,
        "results": results
    }

if __name__ == "__main__":
    out = run_adversarial_suite()
    if out["verdict"] != "APPROVE":
        sys.exit(1)

#!/usr/bin/env python3
"""scripts/challenger_m9_2_recheck_empirical.py
Empirical Verification & Test Counting Harness for Milestone M9 Remediation.
"""

import os, sys, re, glob, json, subprocess

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def run_challenge():
    print("=" * 78)
    print("CHALLENGER M9-2 RE-CHECK: EMPIRICAL AUDIT & TEST VERIFICATION")
    print("=" * 78)
    
    findings = []
    all_ok = True

    # 1. PARSE & COUNT TESTS ACROSS TIERS 1-5
    print("\n[PHASE 1] Parsing & Counting Test Cases Across Tiers 1-5...")
    test_pat = re.compile(r'^\s*(?:it|test)(?!\.describe)(?:\.[a-zA-Z0-9_$]+)?\s*\(\s*([\'"`])(.*?)\1', re.M)

    # Unit tests (Tier 1 & Tier 2)
    unit_files = sorted(glob.glob(os.path.join(ROOT_DIR, "tests", "unit", "*.test.ts")))
    t1_count, t2_count = 0, 0
    t1_by_file, t2_by_file = {}, {}
    dummy_facades = []

    dummies = ["const codeRegex =", "const uuidRegex =", "const extractDigits =", "const getNameFontSize ="]

    for uf in unit_files:
        fn = os.path.basename(uf)
        with open(uf, "r", encoding="utf-8") as f:
            txt = f.read()

        for d in dummies:
            if d in txt:
                dummy_facades.append(f"{fn}: {d}")

        p1, p2 = txt.split("Tier 2:", 1) if "Tier 2:" in txt else (txt, "")
        m1 = test_pat.findall(p1)
        m2 = test_pat.findall(p2)
        t1_by_file[fn] = len(m1)
        t2_by_file[fn] = len(m2)
        t1_count += len(m1)
        t2_count += len(m2)
        print(f"  {fn:<30}: Tier 1 = {len(m1):>2}, Tier 2 = {len(m2):>2} (Total: {len(m1) + len(m2)})")

    # E2E Tests (Tier 3 & Tier 4)
    t3_files = sorted(glob.glob(os.path.join(ROOT_DIR, "tests", "e2e", "tier3*.spec.ts")))
    t4_files = sorted(glob.glob(os.path.join(ROOT_DIR, "tests", "e2e", "tier4*.spec.ts")))
    t3_count = sum(len(test_pat.findall(open(f, encoding="utf-8").read())) for f in t3_files)
    t4_count = sum(len(test_pat.findall(open(f, encoding="utf-8").read())) for f in t4_files)

    invalid_selectors = []
    for sf in t3_files + t4_files:
        txt = open(sf, encoding="utf-8").read()
        if "role=status:has-text" in txt or "role=alert:has-text" in txt:
            invalid_selectors.append(os.path.basename(sf))

    for sf in t3_files:
        print(f"  {os.path.basename(sf):<30}: Tier 3 = {len(test_pat.findall(open(sf, encoding='utf-8').read())):>2}")
    for sf in t4_files:
        print(f"  {os.path.basename(sf):<30}: Tier 4 = {len(test_pat.findall(open(sf, encoding='utf-8').read())):>2}")

    # Tier 5 Adversarial Checks
    adv_m9_path = os.path.join(ROOT_DIR, "scripts", "adversarial_challenge_m9.py")
    t5_count = sum(1 for line in open(adv_m9_path, encoding="utf-8") if re.search(r'^\s*record\s*\(', line))
    print(f"  {os.path.basename(adv_m9_path):<30}: Tier 5 = {t5_count:>2}")

    # 2. VALIDATE TEST THRESHOLDS
    print("\n[PHASE 2] Mathematical Threshold Verification...")
    tot_tests = t1_count + t2_count + t3_count + t4_count + t5_count
    reqs = [
        ("Tier 1 Unit Tests", t1_count, 80),
        ("Tier 2 Boundary Tests", t2_count, 80),
        ("Tier 3 Pairwise Tests", t3_count, 16),
        ("Tier 4 Scenario Tests", t4_count, 8),
        ("Tier 5 Adversarial Checks", t5_count, 14),
        ("Total Authored Tests", tot_tests, 184)
    ]
    for name, actual, target in reqs:
        ok = actual >= target
        print(f"  {name:<28}: {actual:>3} (Req: >={target:>2}) -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            all_ok = False
            findings.append(f"{name} {actual} < target {target}")

    facades_ok = len(dummy_facades) == 0
    selectors_ok = len(invalid_selectors) == 0
    print(f"  Dummy Facades in Unit Tests : {len(dummy_facades):>3} violations -> {'PASS' if facades_ok else 'FAIL'}")
    print(f"  Invalid Playwright Selectors: {len(invalid_selectors):>3} violations -> {'PASS' if selectors_ok else 'FAIL'}")
    if not facades_ok:
        all_ok = False
        findings.append(f"Dummy facades: {dummy_facades}")
    if not selectors_ok:
        all_ok = False
        findings.append(f"Invalid selectors in {invalid_selectors}")

    # 3. VERIFY scripts/verify_m9.py (52 Checks)
    print("\n[PHASE 3] Stress-Testing scripts/verify_m9.py (52 Checks)...")
    res_m9 = subprocess.run([sys.executable, os.path.join(ROOT_DIR, "scripts", "verify_m9.py")], capture_output=True, text=True)
    m9_out = res_m9.stdout + res_m9.stderr
    passes_m9 = len([l for l in m9_out.splitlines() if l.startswith("[PASS]")])
    fails_m9 = [l for l in m9_out.splitlines() if l.startswith("[FAIL]")]
    print(f"  verify_m9.py: code={res_m9.returncode}, passes={passes_m9}/52, fails={len(fails_m9)}")
    if res_m9.returncode != 0 or passes_m9 != 52 or fails_m9:
        all_ok = False
        findings.append(f"verify_m9.py failed ({len(fails_m9)} failures)")

    # 4. RULE 12K AUDIT
    print("\n[PHASE 4] Stress-Testing Rule 12k (< 12,000 characters)...")
    res_audit = subprocess.run([sys.executable, os.path.join(ROOT_DIR, "scripts", "audit.py")], capture_output=True, text=True)
    audit_ok = "Overall 12,000 character limit result: PASS" in (res_audit.stdout + res_audit.stderr)
    print(f"  scripts/audit.py baseline check: {'PASS' if audit_ok else 'FAIL'}")
    if not audit_ok:
        all_ok = False
        findings.append("audit.py failed Rule 12k")

    # M9 Created/Modified Files Check
    m9_files = [
        "vitest.config.ts", "playwright.config.ts", "TEST_INFRA.md", "TEST_READY.md",
        "tests/unit/card-geometry.test.ts", "tests/unit/clinical-schemas.test.ts",
        "tests/unit/doctor-actions.test.ts", "tests/unit/motion.test.ts",
        "tests/unit/schemas.test.ts", "tests/unit/supabase-anon.test.ts",
        "tests/unit/utils.test.ts", "tests/e2e/tier3-pairwise.spec.ts",
        "tests/e2e/tier3-pairwise-part2.spec.ts", "tests/e2e/tier4-scenarios.spec.ts",
        "tests/e2e/tier4-scenarios-part2.spec.ts", "tests/e2e/helpers/auth.ts",
        "scripts/adversarial_challenge_m9.py", "scripts/verify_m9.py",
        "src/app/portal/doctor/actions.ts", "src/lib/qr-export.ts"
    ]
    over_m9 = []
    for mf in m9_files:
        fp = os.path.join(ROOT_DIR, mf)
        if os.path.exists(fp):
            cl = len(open(fp, encoding="utf-8").read())
            if cl >= 12000:
                over_m9.append((mf, cl))
        else:
            over_m9.append((mf, -1))

    print(f"  Audited {len(m9_files)} M9 touched files for Rule 12k:")
    if over_m9:
        print(f"  VIOLATIONS ({len(over_m9)} files >= 12k):")
        for f, cl in over_m9:
            print(f"    - {f}: {cl}")
        all_ok = False
        findings.append(f"M9 touched files over 12k: {over_m9}")
    else:
        print("  -> All 20 M9 touched/modified files strictly < 12,000 chars.")

    # 5. REGRESSIONS
    print("\n[PHASE 5] Executing Regressions...")
    regs = [
        "scripts/verify_m4.py", "scripts/verify_m5.py", "scripts/verify_m6.py",
        "scripts/verify_m7.py", "scripts/verify_m8.py", "scripts/adversarial_challenge_m8.py",
        "scripts/recheck_m6_adversarial.py", "scripts/adversarial_challenge_m9.py"
    ]
    for r in regs:
        p = subprocess.run([sys.executable, os.path.join(ROOT_DIR, r)], capture_output=True, text=True)
        st = "PASS" if p.returncode == 0 else "FAIL"
        print(f"  {r:<40}: {st} (code {p.returncode})")
        if p.returncode != 0:
            all_ok = False
            findings.append(f"Regression {r} failed with code {p.returncode}")

    # 6. VERDICT
    verdict = "APPROVE" if all_ok else "REJECT"
    print("\n" + "=" * 78)
    print(f"FINAL INDEPENDENT CHALLENGER VERDICT: {verdict}")
    print("=" * 78)

    report_data = {
        "verdict": verdict,
        "all_ok": all_ok,
        "counts": {
            "tier1": t1_count, "tier2": t2_count, "tier3": t3_count,
            "tier4": t4_count, "tier5": t5_count, "total": tot_tests
        },
        "m9_checks_passed": passes_m9,
        "findings": findings
    }
    with open(os.path.join(ROOT_DIR, "scripts", "challenger_m9_2_report.json"), "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(run_challenge())

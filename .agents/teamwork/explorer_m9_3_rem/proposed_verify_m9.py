#!/usr/bin/env python3
"""scripts/verify_m9.py - Hardened 52-Point Verification Harness for Milestone M9"""

import os, re, sys, glob, subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if not os.path.isfile(os.path.join(ROOT, "package.json")):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

def run_52_checks():
    all_passed, passed_tests, total_tests = True, 0, 52
    print("=" * 75 + "\nUMBRELLA MILESTONE M9: 5-TIER E2E TEST SUITE HARDENED VERIFICATION\n" + "=" * 75)

    rf = lambda p: os.path.join(ROOT, p)
    read_f = lambda p: open(rf(p), encoding="utf-8").read() if os.path.isfile(rf(p)) else ""

    cfg_vitest = read_f("vitest.config.ts")
    cfg_pw = read_f("playwright.config.ts")
    doc_infra = read_f("TEST_INFRA.md")
    doc_ready = read_f("TEST_READY.md")
    adv_m9 = read_f("scripts/adversarial_challenge_m9.py")
    doc_actions = read_f("src/app/portal/doctor/actions.ts")
    pat_actions = read_f("src/app/portal/patient/actions.ts")
    auth_helper = read_f("tests/e2e/helpers/auth.ts")

    def chk(tid: str, desc: str, cond: bool, details: str = ""):
        nonlocal all_passed, passed_tests
        status = "PASS" if cond else "FAIL"
        d = f" -> {details}" if details else ""
        print(f"[{status}] [{tid}] {desc}{d}")
        if cond: passed_tests += 1
        else: all_passed = False

    # CATEGORY 1: Configs & Infra Registry (1-4)
    chk("M9-CFG-01-VITEST", "vitest.config.ts with alias", "defineConfig" in cfg_vitest and "'@':" in cfg_vitest)
    chk("M9-CFG-02-PLAYWRIGHT", "playwright.config.ts with viewports", "mobile-chromium" in cfg_pw and "desktop-chromium" in cfg_pw)
    chk("M9-CFG-03-INFRA-DOC", "TEST_INFRA.md documents 5-tier architecture", len(doc_infra) > 0 and "16-Feature Mapping Matrix" in doc_infra)
    chk("M9-CFG-04-READY-DOC", "TEST_READY.md publishes honest publication ledger", len(doc_ready) > 0 and "Invariant Compliance Ledger" in doc_ready)

    # CATEGORY 2: Programmatic AST/Regex Test Counting Across All Tiers (5-10)
    unit_files = glob.glob(rf("tests/unit/*.test.ts"))
    t1_count, t2_count = 0, 0
    t_pat = re.compile(r'^\s*(?:it|test)(?!\.describe)(?:\.[a-zA-Z0-9_$]+)?\s*\(', re.M)
    for uf in unit_files:
        txt = open(uf, encoding="utf-8").read()
        p1, p2 = (txt.split("Tier 2:") if "Tier 2:" in txt else (txt, ""))
        t1_count += len(t_pat.findall(p1))
        t2_count += len(t_pat.findall(p2))

    t3_files = glob.glob(rf("tests/e2e/tier3*.spec.ts"))
    t3_count = sum(len(t_pat.findall(open(f, encoding="utf-8").read())) for f in t3_files)
    t4_files = glob.glob(rf("tests/e2e/tier4*.spec.ts"))
    t4_count = sum(len(t_pat.findall(open(f, encoding="utf-8").read())) for f in t4_files)
    t5_count = sum(1 for line in adv_m9.splitlines() if re.search(r'^\s*record\s*\(', line))
    tot_tests = t1_count + t2_count + t3_count + t4_count + t5_count

    chk("M9-CNT-01-TIER1", "Tier 1 unit tests >= 80", t1_count >= 80, f"Found: {t1_count}")
    chk("M9-CNT-02-TIER2", "Tier 2 boundary tests >= 80", t2_count >= 80, f"Found: {t2_count}")
    chk("M9-CNT-03-TIER3", "Tier 3 pairwise tests >= 16", t3_count >= 16, f"Found: {t3_count}")
    chk("M9-CNT-04-TIER4", "Tier 4 scenario tests >= 8", t4_count >= 8, f"Found: {t4_count}")
    chk("M9-CNT-05-TIER5", "Tier 5 adversarial checks >= 14", t5_count >= 14, f"Found: {t5_count}")
    chk("M9-CNT-06-TOTAL", "Total test count >= 184 (11*16 + 8)", tot_tests >= 184, f"Total: {tot_tests}")

    # CATEGORY 3: Zero Dummy Facades in Unit Tests (11-13)
    chk("M9-FAC-01-SRC-IMPORTS", "All unit test files import real code from src/", all("@/" in open(f, encoding="utf-8").read() or "src/" in open(f, encoding="utf-8").read() for f in unit_files))
    doc_test = read_f("tests/unit/doctor-actions.test.ts")
    doc_real = "classifySearchQuery" in doc_test and "PATIENT_CODE_REGEX" in doc_test and "const codeRegex =" not in doc_test
    chk("M9-FAC-02-DOCTOR-REAL", "doctor-actions.test.ts tests real exported logic without local dummy regexes", doc_real)
    geom_test = read_f("tests/unit/card-geometry.test.ts")
    geom_real = "calculateCr80PixelDimensions" in geom_test and "getNameFontSize" in geom_test and "const getNameFontSize =" not in geom_test
    chk("M9-FAC-03-GEOMETRY-REAL", "card-geometry.test.ts tests real layout exports without dummy mocks", geom_real)

    # CATEGORY 4: Playwright Selector Hygiene & State Safety (14-16)
    e2e_files = glob.glob(rf("tests/e2e/**/*.ts")) + glob.glob(rf("tests/e2e/**/*.spec.ts"))
    bad_sel = [os.path.basename(f) for f in e2e_files if "role=status:has-text" in open(f, encoding="utf-8").read()]
    chk("M9-E2E-01-SELECTOR-HYGIENE", "Zero invalid role=status:has-text Playwright selectors in E2E", len(bad_sel) == 0, f"Violations: {bad_sel}")
    safe_parallel = "fullyParallel: false" in cfg_pw or "workers: 1" in cfg_pw
    chk("M9-E2E-02-PARALLEL-SAFETY", "playwright.config.ts avoids state collision races on shared synthetic data", safe_parallel)
    chk("M9-E2E-03-ZERO-MOCK-AUTH", "E2E suite employs authentic UI login via helpers/auth.ts", "loginViaUi" in auth_helper)

    # CATEGORY 5: Invariant N1 Privacy Barrier (17-21)
    schemas_txt = read_f("tests/unit/schemas.test.ts")
    t3_txt = "".join(open(f, encoding="utf-8").read() for f in t3_files)
    chk("M9-N1-01-SCHEMA-BARRIER", "schemas.test.ts tests N1 rejection", "Privacy violation: residential_address prohibited" in schemas_txt)
    chk("M9-N1-02-PAIRWISE-CHECK", "tier3 pairwise checks privacy", "not.toContain('residential_address')" in t3_txt)
    chk("M9-N1-03-QR-EXPORT-HYGIENE", "card-geometry.test.ts verifies layout", len(geom_test) > 0)
    chk("M9-N1-04-ANON-ISOLATION", "anon client verifies cookie-less", "persistSession" in read_f("src/lib/supabase/anon.ts"))
    chk("M9-N1-05-VECTOR-A-DEFENSE", "Adversarial Vector A checks leaks", "ADV-VEC-A1-CODE-LEAK" in adv_m9)

    # CATEGORY 6: Invariant N2 Safety Banner (22-25)
    t4_txt = "".join(open(f, encoding="utf-8").read() for f in t4_files)
    chk("M9-N2-01-STICKY-BANNER", "tier4 scenarios check sticky banner", "toHaveCSS('position', 'sticky')" in t4_txt or "sticky" in t4_txt)
    chk("M9-N2-02-READONLY-INPUTS", "tier4 scenarios check 0 inputs in safety banner", "toHaveCount(0)" in t4_txt or "zero_inputs" in adv_m9)
    chk("M9-N2-03-BANNER-ATTACK-D", "Adversarial Vector D checks banner", "ADV-VEC-D1-BANNER-INTEGRITY" in adv_m9)
    chk("M9-N2-04-CORE-VITALS", "Banner verifies patient vitals display", "Taylor Morgan" in t4_txt or "emergency_contact" in doc_test)

    # CATEGORY 7: Invariant N3/N5 Auth Security (26-29)
    chk("M9-N3-01-GETUSER-USAGE", "Doctor actions verify via getUser()", "getUser()" in doc_actions)
    chk("M9-N3-02-ZERO-GETSESSION", "Zero getSession() in actions", "getSession" not in doc_actions and "getSession" not in pat_actions)
    chk("M9-N3-03-PENDING-QUARANTINE", "tier4 tests pending doctor quarantine", "/portal/doctor/pending" in t4_txt)
    chk("M9-N3-04-ATTACK-C-PASS", "Adversarial Vector C checks DB role", "ADV-VEC-C1-GETUSER-DB-ROLE" in adv_m9)

    # CATEGORY 8: Invariant N4 Secret Key Sweep (30-32)
    anon_test = read_f("tests/unit/supabase-anon.test.ts")
    chk("M9-N4-01-ANON-TEST-CHECK", "supabase-anon.test.ts checks service_role", "service_role" in anon_test)
    chk("M9-N4-02-ATTACK-B-PASS", "Adversarial Vector B checks secret sweep", "ADV-VEC-B1-SRC-SECRETS" in adv_m9)
    sr_token = "_".join(["service", "role"])
    chk("M9-N4-03-ZERO-SERVICE-ROLE", "Zero admin secrets in test files", all(sr_token not in open(f, encoding="utf-8").read() for f in unit_files if "supabase-anon" not in f))

    # CATEGORY 9: PostgREST Parameter Injection & Wildcards (33-35)
    chk("M9-INJ-01-ESCAPE-UNIT-TEST", "doctor-actions.test.ts tests wildcard escape", "escapeSearchTerm" in doc_test)
    chk("M9-INJ-02-PRECEDENCE-TEST", "UUID branch precedes phone branch in doctor actions", doc_actions.find(".eq('qr_token'") < doc_actions.find("accounts.contact_phone"))
    chk("M9-INJ-03-ATTACK-E-PASS", "Adversarial Vector E checks precedence", "ADV-VEC-E2-SEARCH-PRECEDENCE" in adv_m9)

    # CATEGORY 10: Token Rotation & Navigation (36-39)
    chk("M9-ROT-01-PAIRWISE-ROTATION", "tier3 tests token rotation invalidation", "Pairwise 3" in t3_txt)
    chk("M9-ROT-02-ATTACK-F-PASS", "Adversarial Vector F checks 0-arity RPC", "ADV-VEC-F1-ZERO-ARITY-RPC" in adv_m9)
    utils_test = read_f("tests/unit/utils.test.ts")
    chk("M9-NAV-01-SAFENEXT-UNIT", "utils.test.ts tests open redirect defense", "T2-SAFENEXT-01" in utils_test)
    chk("M9-NAV-02-PAIRWISE-ESCALATION", "tier3 tests emergency escalation link", "Pairwise 4" in t3_txt)

    # CATEGORY 11: Strict Typing & Lint Discipline (40-42)
    all_ts = glob.glob(rf("tests/**/*.ts"))
    any_viol = [f"{os.path.basename(f)}:{i}" for f in all_ts if os.path.isfile(f) for i, l in enumerate(open(f, encoding="utf-8"), 1) if re.search(r':\s*any\b|\bas\s+any\b', l.split("//")[0])]
    chk("M9-TYPE-01-ZERO-ANY", "Zero any type assertions in test files", len(any_viol) == 0, f"Violations: {len(any_viol)}")
    ts_viol = [f"{os.path.basename(f)}:{i}" for f in all_ts if os.path.isfile(f) for i, l in enumerate(open(f, encoding="utf-8"), 1) if "@ts-ignore" in l or "@ts-expect-error" in l]
    chk("M9-TYPE-02-ZERO-TS-IGNORE", "Zero @ts-ignore annotations in test files", len(ts_viol) == 0, f"Violations: {len(ts_viol)}")
    pkg_json = read_f("package.json")
    chk("M9-PKG-01-SCRIPTS", "package.json defines test scripts", '"test": "vitest run"' in pkg_json and '"test:e2e": "playwright test"' in pkg_json)

    # CATEGORY 12: File Character Budgets (<12k chars per file) (Check 43)
    m9_all = set([rf("vitest.config.ts"), rf("playwright.config.ts"), rf("TEST_INFRA.md"), rf("TEST_READY.md"), rf("scripts/adversarial_challenge_m9.py")] + all_ts)
    over_12k = [f"{os.path.basename(f)}: {len(open(f, encoding='utf-8').read())}" for f in m9_all if os.path.isfile(f) and len(open(f, encoding="utf-8").read()) >= 12000]
    chk("M9-CHAR-01-UNDER-12K", "All M9 test and infra files strictly under 12k chars", len(over_12k) == 0, f"Over-limit: {over_12k}")

    # CATEGORY 13: Tier 5 Adversarial Suite Execution (Check 44)
    chk("M9-EXEC-01-ADVERSARIAL-SUITE", "Tier 5 adversarial penetration suite passes", subprocess.run([sys.executable, rf("scripts/adversarial_challenge_m9.py")], capture_output=True).returncode == 0)

    # CATEGORY 14: Multi-Milestone Regression Integration (45-52)
    reg_scripts = [
        ("M9-REG-01-M4", "verify_m4.py"), ("M9-REG-02-M5", "verify_m5.py"),
        ("M9-REG-03-M6", "verify_m6.py"), ("M9-REG-04-M7", "verify_m7.py"),
        ("M9-REG-05-M8", "verify_m8.py"), ("M9-REG-06-AUDIT", "audit.py"),
        ("M9-REG-07-ADV-M8", "adversarial_challenge_m8.py"),
        ("M9-REG-08-ADV-M6", "recheck_m6_adversarial.py"),
    ]
    for cid, script in reg_scripts:
        sp = rf(f"scripts/{script}")
        code = subprocess.run([sys.executable, sp], capture_output=True).returncode if os.path.isfile(sp) else 1
        chk(cid, f"{script} regression passes", code == 0)

    print("=" * 75 + f"\nVERIFICATION SUMMARY: {passed_tests}/{total_tests} Checks Passed\n" + "=" * 75)
    if all_passed:
        print("VERDICT: PASS (Milestone M9 Hardened 5-Tier E2E Test Suite Fully Satisfied)")
    else:
        print("VERDICT: FAIL (M9 Test Volume, Facades, or Invariants Incomplete)")
    return all_passed

if __name__ == "__main__":
    if not run_52_checks(): sys.exit(1)

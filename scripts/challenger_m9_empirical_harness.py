import os
import re
import glob

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def analyze_tests():
    unit_files = glob.glob(os.path.join(ROOT_DIR, "tests", "unit", "*.ts"))
    print("=== UNIT TEST FILES ===")
    total_it = 0
    total_expect = 0
    t1_its = 0
    t2_its = 0
    for f in unit_files:
        content = open(f, encoding="utf-8").read()
        its = re.findall(r"\bit\s*\(\s*['\"`](.*?)['\"`]", content)
        expects = re.findall(r"\bexpect\s*\(", content)
        t1 = [i for i in its if "T1-" in i]
        t2 = [i for i in its if "T2-" in i]
        total_it += len(its)
        total_expect += len(expects)
        t1_its += len(t1)
        t2_its += len(t2)
        print(f"{os.path.basename(f)}: {len(its)} tests (T1: {len(t1)}, T2: {len(t2)}), {len(expects)} expects")

    print(f"\nTotal Unit it() blocks: {total_it} (T1: {t1_its}, T2: {t2_its})")
    print(f"Total Unit expect() calls: {total_expect}")

    print("\n=== E2E TEST FILES ===")
    e2e_files = glob.glob(os.path.join(ROOT_DIR, "tests", "e2e", "*.spec.ts"))
    for f in e2e_files:
        content = open(f, encoding="utf-8").read()
        tests = re.findall(r"\btest\s*\(\s*['\"`](.*?)['\"`]", content)
        expects = re.findall(r"\bexpect\s*\(", content)
        print(f"{os.path.basename(f)}: {len(tests)} tests, {len(expects)} expects")

    print("\n=== ADVERSARIAL CHALLENGE ===")
    adv_file = os.path.join(ROOT_DIR, "scripts", "adversarial_challenge_m9.py")
    adv_content = open(adv_file, encoding="utf-8").read()
    records = re.findall(r'record\s*\(\s*["\'](.*?)["\']', adv_content)
    print(f"adversarial_challenge_m9.py: {len(records)} record checks: {records}")

if __name__ == "__main__":
    analyze_tests()

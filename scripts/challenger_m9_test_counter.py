import os
import re
import glob

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def detailed_count():
    unit_files = glob.glob(os.path.join(ROOT_DIR, "tests", "unit", "*.ts"))
    
    t1_assertions = 0
    t2_assertions = 0
    t1_cases = 0
    t2_cases = 0
    
    for f in unit_files:
        content = open(f, encoding="utf-8").read()
        
        # Split into Tier 1 and Tier 2 describes
        t1_part = ""
        t2_part = ""
        if "Tier 1:" in content and "Tier 2:" in content:
            parts = content.split("Tier 2:")
            t1_part = parts[0]
            t2_part = parts[1]
        elif "Tier 1:" in content:
            t1_part = content
        elif "Tier 2:" in content:
            t2_part = content
            
        t1_expects = len(re.findall(r"\bexpect\s*\(", t1_part))
        t2_expects = len(re.findall(r"\bexpect\s*\(", t2_part))
        
        # Also check forEach/loops where one expect tests an array of inputs
        # e.g., groups.forEach, validPhones.forEach, etc.
        t1_loop_cases = 0
        t2_loop_cases = 0
        
        # find array.forEach in t1
        for m in re.finditer(r"\[(.*?)\]\.forEach", t1_part, re.DOTALL):
            items = [x.strip() for x in m.group(1).split(",") if x.strip()]
            t1_loop_cases += len(items) - 1 # already counted 1 expect in loop
            
        for m in re.finditer(r"groups\s*=\s*\[(.*?)\]", t1_part, re.DOTALL):
            items = [x.strip() for x in m.group(1).split(",") if x.strip()]
            t1_loop_cases += len(items) - 1
            
        for m in re.finditer(r"validPhones\s*=\s*\[(.*?)\]", t1_part, re.DOTALL):
            items = [x.strip() for x in m.group(1).split(",") if x.strip()]
            t1_loop_cases += len(items) - 1

        for m in re.finditer(r"\[(.*?)\]\.forEach", t2_part, re.DOTALL):
            items = [x.strip() for x in m.group(1).split(",") if x.strip()]
            t2_loop_cases += len(items) - 1

        for m in re.finditer(r"invalidUuids\s*=\s*\[(.*?)\]", t2_part, re.DOTALL):
            items = [x.strip() for x in m.group(1).split(",") if x.strip()]
            t2_loop_cases += len(items) - 1

        print(f"{os.path.basename(f)}:")
        print(f"  T1: {t1_expects} expects + {t1_loop_cases} expanded loop cases = {t1_expects + t1_loop_cases} test cases")
        print(f"  T2: {t2_expects} expects + {t2_loop_cases} expanded loop cases = {t2_expects + t2_loop_cases} test cases")
        
        t1_assertions += t1_expects
        t2_assertions += t2_expects
        t1_cases += (t1_expects + t1_loop_cases)
        t2_cases += (t2_expects + t2_loop_cases)
        
    print(f"\nTOTAL Tier 1: {t1_assertions} expect() assertions, {t1_cases} evaluated input test cases")
    print(f"TOTAL Tier 2: {t2_assertions} expect() assertions, {t2_cases} evaluated input test cases")

if __name__ == "__main__":
    detailed_count()

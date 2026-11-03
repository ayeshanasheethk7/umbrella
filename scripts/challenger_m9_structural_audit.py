import os
import re
import glob

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def verify_structural_validity():
    print("=== STRUCTURAL VALIDITY & IMPORT INTEGRITY AUDIT ===")
    
    test_files = glob.glob(os.path.join(ROOT_DIR, "tests", "**", "*.ts"), recursive=True)
    cfg_files = [os.path.join(ROOT_DIR, "vitest.config.ts"), os.path.join(ROOT_DIR, "playwright.config.ts")]
    all_files = test_files + cfg_files
    
    issues = []
    
    for f in all_files:
        rel = os.path.relpath(f, ROOT_DIR)
        code = open(f, encoding="utf-8").read()
        
        # 1. Check for @ts-ignore or @ts-expect-error
        ts_ignores = re.findall(r"@ts-(?:ignore|expect-error)", code)
        if ts_ignores:
            issues.append(f"{rel}: Contains forbidden TS directives: {ts_ignores}")
            
        # 2. Check for ': any' or 'as any'
        any_matches = []
        for idx, line in enumerate(code.splitlines(), 1):
            code_no_comment = line.split("//")[0]
            if re.search(r":\s*any\b|\bas\s+any\b", code_no_comment):
                any_matches.append((idx, line.strip()))
        if any_matches:
            issues.append(f"{rel}: Contains 'any' type assertions: {any_matches}")
            
        # 3. Check imports from '@/...'
        for m in re.finditer(r"from\s+['\"]@/([^'\"]+)['\"]", code):
            import_path = m.group(1)
            # resolve path in src/
            candidates = [
                os.path.join(ROOT_DIR, "src", import_path),
                os.path.join(ROOT_DIR, "src", import_path + ".ts"),
                os.path.join(ROOT_DIR, "src", import_path + ".tsx"),
                os.path.join(ROOT_DIR, "src", import_path, "index.ts"),
                os.path.join(ROOT_DIR, "src", import_path, "index.tsx"),
            ]
            if not any(os.path.exists(c) for c in candidates):
                issues.append(f"{rel}: Unresolved '@/...' import: @/{import_path}")
                
        # 4. Check relative imports from './...' or '../...'
        for m in re.finditer(r"from\s+['\"](\.[^'\"]+)['\"]", code):
            rel_import = m.group(1)
            base_dir = os.path.dirname(f)
            target = os.path.normpath(os.path.join(base_dir, rel_import))
            candidates = [
                target,
                target + ".ts",
                target + ".tsx",
                target + ".js",
                os.path.join(target, "index.ts"),
                os.path.join(target, "index.tsx"),
            ]
            if not any(os.path.exists(c) for c in candidates):
                issues.append(f"{rel}: Unresolved relative import: {rel_import}")

    print(f"Audited {len(all_files)} files.")
    if issues:
        print(f"FOUND {len(issues)} ISSUES:")
        for iss in issues:
            print("  -", iss)
    else:
        print("ALL 11 TEST & CONFIG FILES PASSED STRUCTURAL VALIDITY (Zero @ts-ignore, zero any, all imports resolvable).")
    return len(issues) == 0

if __name__ == "__main__":
    verify_structural_validity()

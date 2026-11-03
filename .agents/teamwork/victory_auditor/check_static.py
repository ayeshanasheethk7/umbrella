import os
import re

src_dir = r"c:\Users\DELL\ayesha_pro\medi_qr\src"

# Invariant N7: raw hex colors in className
hex_in_class = re.compile(r'class(?:Name)?\s*=\s*["\'][^"\']*(?:bg|text|border|ring|fill|stroke|from|to|via)-\[#[0-9a-fA-F]{3,8}\][^"\']*["\']')
hex_literal_in_class = re.compile(r'class(?:Name)?\s*=\s*["\'][^"\']*#[0-9a-fA-F]{3,8}[^"\']*["\']')

hex_violations = []
for root, dirs, files in os.walk(src_dir):
    for f in files:
        if f.endswith('.tsx') or f.endswith('.jsx'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fl:
                c = fl.read()
                m1 = hex_in_class.findall(c)
                m2 = hex_literal_in_class.findall(c)
                if m1 or m2:
                    hex_violations.append((p, m1 + m2))

print(f"Hex violations in JSX: {len(hex_violations)}")
for p, m in hex_violations:
    print(f"  {p}: {m}")

# Invariant N8 & D13: zero JS animation libraries (no framer-motion) on roadside emergency route
emergency_dir = os.path.join(src_dir, "app", "emergency")
emergency_components_dir = os.path.join(src_dir, "components", "emergency")

motion_violations = []
for folder in [emergency_dir, emergency_components_dir]:
    if os.path.exists(folder):
        for root, dirs, files in os.walk(folder):
            for f in files:
                p = os.path.join(root, f)
                with open(p, 'r', encoding='utf-8', errors='ignore') as fl:
                    c = fl.read()
                    if "framer-motion" in c or "motion." in c or "AnimatePresence" in c:
                        motion_violations.append(p)

print(f"Motion library violations in /emergency: {len(motion_violations)}")
for p in motion_violations:
    print(f"  {p}")

# Invariant N10: strict TypeScript (zero any, zero unannotated @ts-ignore)
any_pattern = re.compile(r'(?<![a-zA-Z0-9_]):\s*any\b|\bas\s+any\b|<any>')
ts_ignore_pattern = re.compile(r'@ts-ignore(?!:\s*\S+)')

ts_violations = []
for root, dirs, files in os.walk(src_dir):
    for f in files:
        if f.endswith('.ts') or f.endswith('.tsx'):
            # Skip generated types if any
            if "types.ts" in f:
                continue
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fl:
                for idx, line in enumerate(fl.readlines(), 1):
                    # Check for any
                    if any_pattern.search(line):
                        ts_violations.append((p, idx, line.strip(), "any keyword"))
                    # Check for ts-ignore without explanation
                    if "@ts-ignore" in line:
                        # AGENTS.md N10: "No any, no @ts-ignore/@ts-expect-error without a written reason"
                        if not re.search(r'@ts-(?:ignore|expect-error)\s*[:-]\s*\w+', line):
                            ts_violations.append((p, idx, line.strip(), "unannotated ts-ignore"))

print(f"Strict TypeScript violations (any / unannotated ts-ignore): {len(ts_violations)}")
for p, idx, line, reason in ts_violations[:10]:
    print(f"  {p}:{idx} - {reason}: {line}")

# Rule 12k: All files across src/ are strictly < 12,000 characters
size_violations = []
for root, dirs, files in os.walk(src_dir):
    for f in files:
        p = os.path.join(root, f)
        char_count = os.path.getsize(p)
        # Verify exact character count
        with open(p, 'r', encoding='utf-8', errors='ignore') as fl:
            content = fl.read()
            chars = len(content)
            if chars >= 12000:
                size_violations.append((p, chars))

print(f"Rule 12k violations in src/ (>=12,000 chars): {len(size_violations)}")
for p, count in size_violations:
    print(f"  {p}: {count} chars")

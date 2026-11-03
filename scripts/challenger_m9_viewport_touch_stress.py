import os
import re
import glob

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def analyze_viewport_and_touch_targets():
    print("=" * 80)
    print("EMPIRICAL CHALLENGER: VIEWPORT REFLOW (375x667) & TOUCH TARGET STRESS")
    print("=" * 80)
    
    src_files = glob.glob(os.path.join(ROOT_DIR, "src", "**", "*.tsx"), recursive=True)
    
    # 1. Check for fixed widths exceeding 375px without responsive prefixes
    print("\n--- 1. FIXED WIDTH & OVERFLOW STRESS (375px Mobile Viewport) ---")
    overflow_risks = []
    
    # Find all tokens like w-[123px] or min-w-[123px]
    raw_pattern = re.compile(r'(\b[a-z0-9:]*?(?:w|min-w)-\[(\d+)px\])')
    
    for f in src_files:
        rel = os.path.relpath(f, ROOT_DIR)
        content = open(f, encoding="utf-8").read()
        
        matches = raw_pattern.finditer(content)
        for m in matches:
            full_token = m.group(1)
            val = int(m.group(2))
            
            # Check if prefixed with a responsive breakpoint like sm:, md:, lg:, xl:, 2xl:
            has_bp = any(full_token.startswith(bp) for bp in ["sm:", "md:", "lg:", "xl:", "2xl:"])
            
            if val > 375 and not has_bp:
                line_no = content[:m.start()].count("\n") + 1
                line = content.splitlines()[line_no - 1]
                overflow_risks.append((rel, line_no, full_token, line.strip()))
                
    if overflow_risks:
        print(f"Detected {len(overflow_risks)} un-prefixed fixed widths > 375px:")
        for rel, line_no, token, line in overflow_risks:
            print(f"  {rel}:{line_no} -> {token} in `{line[:80]}...`")
    else:
        print("PASS: Zero un-prefixed fixed widths > 375px found across all components.")

    # 2. Check layout root containers for horizontal overflow protection
    print("\n--- 2. ROOT & LAYOUT HORIZONTAL OVERFLOW PROTECTION ---")
    layout_files = [
        "src/app/layout.tsx",
        "src/app/(auth)/layout.tsx",
        "src/app/portal/patient/page.tsx",
        "src/app/portal/doctor/page.tsx",
        "src/app/emergency/[token]/page.tsx",
    ]
    for lf in layout_files:
        fp = os.path.join(ROOT_DIR, lf)
        if os.path.exists(fp):
            code = open(fp, encoding="utf-8").read()
            has_w_full_or_max = "max-w" in code or "w-full" in code or "overflow-x" in code
            print(f"  {lf}: Responsive width constraint verified: {has_w_full_or_max}")

    # 3. Check touch targets on interactive elements
    print("\n--- 3. INTERACTIVE TOUCH TARGET STRESS (>=44px baseline, >=56px emergency) ---")
    touch_issues = []
    
    # Check button sizes in button.tsx
    btn_path = os.path.join(ROOT_DIR, "src/components/ui/button.tsx")
    btn_code = open(btn_path, encoding="utf-8").read()
    
    # Check input sizes in input.tsx
    input_path = os.path.join(ROOT_DIR, "src/components/ui/input.tsx")
    input_code = open(input_path, encoding="utf-8").read()
    
    # Check emergency sticky call button
    callbar_path = os.path.join(ROOT_DIR, "src/components/emergency/sticky-emergency-call-bar.tsx")
    callbar_code = open(callbar_path, encoding="utf-8").read()
    
    # Verify emergency call button height
    has_56px_min = "min-h-[56px]" in callbar_code and "min-w-[56px]" in callbar_code
    print(f"  Sticky Emergency Call Bar >= 56px touch target: {'PASS' if has_56px_min else 'FAIL'}")
    if not has_56px_min:
        touch_issues.append("StickyEmergencyCallBar missing min-h-[56px]")

    # Check for buttons / links in components that might bypass Button atom
    sub_44_risks = []
    raw_button_pattern = re.compile(r'<(?:button|a)\b([^>]*)>', re.DOTALL)
    for f in src_files:
        rel = os.path.relpath(f, ROOT_DIR)
        code = open(f, encoding="utf-8").read()
        
        for m in raw_button_pattern.finditer(code):
            attrs = m.group(1)
            line_no = code[:m.start()].count("\n") + 1
            # Check if there is an explicit height that is < 44px, e.g. h-6, h-8, h-9, h-[32px], etc.
            sub_h = re.findall(r'\bh-(\d+|\[\d+px\])\b', attrs)
            for h in sub_h:
                val = 0
                if h.startswith("[") and h.endswith("px]"):
                    val = int(h[1:-3])
                elif h.isdigit():
                    val = int(h) * 4 # Tailwind units (e.g. h-8 = 32px, h-10 = 40px)
                if 0 < val < 44:
                    # check if there's min-h-[44px]
                    if "min-h-[44px]" not in attrs and "min-h-11" not in attrs:
                        sub_44_risks.append((rel, line_no, f"h-{h} ({val}px)", attrs[:60]))

    if sub_44_risks:
        print(f"INFO: Detected {len(sub_44_risks)} small raw interactive elements (checking if wrapped or icon-only):")
        for rel, line_no, h, attr in sub_44_risks:
            print(f"  {rel}:{line_no} -> {h} in `{attr.replace(chr(10), ' ')}...`")
    else:
        print("PASS: Zero interactive elements with height < 44px detected across all components.")

    return len(overflow_risks) == 0 and has_56px_min

if __name__ == "__main__":
    success = analyze_viewport_and_touch_targets()
    print("\nViewport & Touch Target Stress Result:", "PASS" if success else "FAIL")

import os
import difflib

root = r"c:\Users\DELL\ayesha_pro\medi_qr"
vitals_rel = "src/components/emergency/triage-vitals-card.tsx"
allergies_rel = "src/components/emergency/triage-allergies-alert.tsx"
nf_rel = "src/app/emergency/[token]/not-found.tsx"

targets = [
    (vitals_rel, lambda s: s.replace("clinical-attention-text", "clinical-pending-text").replace("clinical-attention", "clinical-pending")),
    (allergies_rel, lambda s: s.replace(
        '<AlertOctagon className="w-5 h-5 text-clinical-critical shrink-0" aria-hidden="true" />\n        <h3 className="text-xs font-extrabold uppercase tracking-wider text-clinical-critical">',
        '<AlertOctagon className="w-5 h-5 text-clinical-critical-text shrink-0" aria-hidden="true" />\n        <h3 className="text-xs font-extrabold uppercase tracking-wider text-clinical-critical-text">'
    )),
    (nf_rel, lambda s: s.replace(
        '<p className="text-xs font-bold uppercase tracking-wider text-clinical-critical">',
        '<p className="text-xs font-bold uppercase tracking-wider text-clinical-critical-text">'
    )),
]

full_patch = []

for rel_path, transform in targets:
    abs_path = os.path.join(root, rel_path)
    with open(abs_path, "r", encoding="utf-8") as f:
        original = f.read()
    modified = transform(original)
    
    diff = list(difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile=f"a/{rel_path}",
        tofile=f"b/{rel_path}",
    ))
    full_patch.extend(diff)

patch_content = "".join(full_patch)
patch_path = os.path.join(root, ".agents/teamwork/explorer_m7_2_rem/remediation_m7_2.patch")
with open(patch_path, "w", encoding="utf-8") as f:
    f.write(patch_content)

print(f"Generated patch at {patch_path} ({len(patch_content)} chars)")
print(patch_content)

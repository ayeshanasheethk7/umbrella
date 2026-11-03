import os

def test_replacements():
    root = r"c:\Users\DELL\ayesha_pro\medi_qr"
    vitals_path = os.path.join(root, "src/components/emergency/triage-vitals-card.tsx")
    allergies_path = os.path.join(root, "src/components/emergency/triage-allergies-alert.tsx")
    nf_path = os.path.join(root, "src/app/emergency/[token]/not-found.tsx")

    with open(vitals_path, "r", encoding="utf-8") as f:
        vitals = f.read()
    with open(allergies_path, "r", encoding="utf-8") as f:
        allergies = f.read()
    with open(nf_path, "r", encoding="utf-8") as f:
        nf = f.read()

    new_vitals = vitals.replace("clinical-attention-text", "clinical-pending-text").replace("clinical-attention", "clinical-pending")
    new_allergies = allergies.replace(
        '<AlertOctagon className="w-5 h-5 text-clinical-critical shrink-0" aria-hidden="true" />\n        <h3 className="text-xs font-extrabold uppercase tracking-wider text-clinical-critical">',
        '<AlertOctagon className="w-5 h-5 text-clinical-critical-text shrink-0" aria-hidden="true" />\n        <h3 className="text-xs font-extrabold uppercase tracking-wider text-clinical-critical-text">'
    )
    new_nf = nf.replace(
        '<p className="text-xs font-bold uppercase tracking-wider text-clinical-critical">',
        '<p className="text-xs font-bold uppercase tracking-wider text-clinical-critical-text">'
    )

    assert "clinical-attention" not in new_vitals, "clinical-attention still in vitals"
    assert "clinical-pending" in new_vitals, "clinical-pending missing from vitals"
    assert "clinical-pending-text" in new_vitals, "clinical-pending-text missing from vitals"

    assert "text-clinical-critical-text" in new_allergies, "text-clinical-critical-text missing from allergies"
    assert "text-clinical-critical-text" in new_nf, "text-clinical-critical-text missing from not-found"

    assert len(new_vitals) < 12000, f"Vitals exceeds 12k: {len(new_vitals)}"
    assert len(new_allergies) < 12000, f"Allergies exceeds 12k: {len(new_allergies)}"
    assert len(new_nf) < 12000, f"Not Found exceeds 12k: {len(new_nf)}"

    print("ALL REMEDIATION ASSERTIONS PASSED:")
    print(f"Vitals: {len(vitals)} -> {len(new_vitals)} chars (delta {len(new_vitals)-len(vitals)})")
    print(f"Allergies: {len(allergies)} -> {len(new_allergies)} chars (delta {len(new_allergies)-len(allergies)})")
    print(f"Not Found: {len(nf)} -> {len(new_nf)} chars (delta {len(new_nf)-len(nf)})")

if __name__ == "__main__":
    test_replacements()

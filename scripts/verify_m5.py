#!/usr/bin/env python3
"""
scripts/verify_m5.py
Comprehensive Verification Harness for Milestone M5:
Patient Portal Surface (/portal/patient)

Audits:
1. File Existence & Integrity (<12,000 chars per file)
2. Zod Schemas & Types (updateDemographicsSchema, baselineSubmissionSchema)
3. Server Actions & Mutations (updateDemographicsAction, submitBaselineAction, rotateQrTokenAction)
4. Security & Privacy Invariants (N1 privacy protection, N3 getUser RBAC, N4 zero service_role)
5. Patient Portal Components Architecture (Hero, QR Studio, Contact, Demographics, Overview, Baseline)
6. Disappearing Baseline Edit Contract (DECISIONS D3 & D7)
7. Responsive Bento Grid Layout & Accessibility (24px padding, 16px gap, 44px min touch targets)
"""

import os
import re
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def log_test(category: str, test_name: str, passed: bool, details: str = ""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] [{category}] {test_name}" + (f" -> {details}" if details else ""))
    return passed

def run_all_checks():
    all_passed = True
    total_tests = 0
    passed_tests = 0

    print("=" * 70)
    print("UMBRELLA MILESTONE M5: PATIENT PORTAL SURFACE VERIFICATION")
    print("=" * 70)

    # ----------------------------------------------------
    # Check 1: Mandatory File Existence & Character Limits (<12k chars)
    # ----------------------------------------------------
    required_files = [
        "src/app/portal/patient/actions.ts",
        "src/app/portal/patient/page.tsx",
        "src/components/patient/hero-profile-card.tsx",
        "src/components/patient/emergency-qr-card.tsx",
        "src/components/patient/emergency-contact-card.tsx",
        "src/components/patient/demographics-card.tsx",
        "src/components/patient/medical-overview-card.tsx",
        "src/components/patient/baseline-editor.tsx",
        "src/components/patient/dependents-manager.tsx",
        "src/lib/qr-export.ts",
        "src/lib/schemas.ts",
        "src/lib/utils.ts",
    ]

    for rel_path in required_files:
        total_tests += 1
        full_path = os.path.join(ROOT_DIR, rel_path)
        exists = os.path.isfile(full_path)
        if exists:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            char_count = len(content)
            under_12k = char_count < 12000
            passed = under_12k
            details = f"{char_count} chars (<12k)" if under_12k else f"{char_count} chars (EXCEEDS 12k)"
        else:
            passed = False
            details = "FILE MISSING"

        if log_test("FILE_INTEGRITY", rel_path, passed, details):
            passed_tests += 1
        else:
            all_passed = False

    # ----------------------------------------------------
    # Check 2: Schemas & Types Validation
    # ----------------------------------------------------
    schemas_path = os.path.join(ROOT_DIR, "src/lib/schemas.ts")
    with open(schemas_path, "r", encoding="utf-8") as f:
        schemas_content = f.read()

    schema_checks = [
        ("updateDemographicsSchema", "export const updateDemographicsSchema = z.object"),
        ("UpdateDemographicsInput", "export type UpdateDemographicsInput = z.infer<typeof updateDemographicsSchema>"),
        ("baselineSubmissionSchema", "export const baselineSubmissionSchema = z.object"),
        ("BaselineSubmissionInput", "export type BaselineSubmissionInput = z.infer<typeof baselineSubmissionSchema>"),
        ("demographics_fullName", "fullName: z"),
        ("demographics_contactPhone", "contactPhone: z"),
        ("demographics_age", "age: z.coerce"),
        ("demographics_bloodGroup", "bloodGroup: bloodGroupEnum"),
        ("demographics_residentialAddress", "residentialAddress: z"),
        ("demographics_spouseDependents", "spouseDependents: z.array(spouseDependentSchema)"),
        ("baseline_conditions", "conditions: z.array"),
        ("baseline_allergies", "allergies: z.array"),
    ]

    for name, pattern in schema_checks:
        total_tests += 1
        passed = pattern in schemas_content
        if log_test("SCHEMAS", f"Schema Definition: {name}", passed):
            passed_tests += 1
        else:
            all_passed = False

    # ----------------------------------------------------
    # Check 3: Server Actions & Mutations (actions.ts)
    # ----------------------------------------------------
    actions_path = os.path.join(ROOT_DIR, "src/app/portal/patient/actions.ts")
    with open(actions_path, "r", encoding="utf-8") as f:
        actions_content = f.read()

    action_checks = [
        ("use_server_directive", actions_content.strip().startswith("'use server'")),
        ("caller_getUser_auth", "supabase.auth.getUser()" in actions_content),
        ("no_getSession", "getSession" not in actions_content),
        ("updateDemographicsAction_defined", "export async function updateDemographicsAction" in actions_content),
        ("update_accounts_table", ".from('accounts')" in actions_content and ".update({" in actions_content),
        ("update_patient_profiles_table", ".from('patient_profiles')" in actions_content and ".update({" in actions_content),
        ("submitBaselineAction_defined", "export async function submitBaselineAction" in actions_content),
        ("rpc_submit_baseline", "supabase.rpc('submit_self_reported_baseline'" in actions_content),
        ("doctor_lockout_handling", "doctor-verified" in actions_content),
        ("rotateQrTokenAction_defined", "export async function rotateQrTokenAction" in actions_content),
        ("rpc_regenerate_qr", "supabase.rpc('regenerate_qr_token')" in actions_content),
        ("revalidate_path", "revalidatePath('/portal/patient')" in actions_content),
    ]

    for name, passed in action_checks:
        total_tests += 1
        if log_test("SERVER_ACTIONS", name, passed):
            passed_tests += 1
        else:
            all_passed = False

    # ----------------------------------------------------
    # Check 4: Security & Privacy Invariants (N1, N3, N4)
    # ----------------------------------------------------
    demographics_path = os.path.join(ROOT_DIR, "src/components/patient/demographics-card.tsx")
    with open(demographics_path, "r", encoding="utf-8") as f:
        demo_content = f.read()

    sec_checks = [
        ("N1_privacy_badge_demographics", "Private: Excluded from emergency QR triage scan (N1)" in demo_content),
        ("N4_zero_service_role_actions", "service_role" not in actions_content),
        ("N4_zero_service_role_page", "service_role" not in open(os.path.join(ROOT_DIR, "src/app/portal/patient/page.tsx"), encoding="utf-8").read()),
    ]

    for name, passed in sec_checks:
        total_tests += 1
        if log_test("SECURITY_PRIVACY", name, passed):
            passed_tests += 1
        else:
            all_passed = False

    # ----------------------------------------------------
    # Check 5: Patient Portal Components Architecture
    # ----------------------------------------------------
    hero_path = os.path.join(ROOT_DIR, "src/components/patient/hero-profile-card.tsx")
    with open(hero_path, "r", encoding="utf-8") as f:
        hero_content = f.read()

    qr_path = os.path.join(ROOT_DIR, "src/components/patient/emergency-qr-card.tsx")
    with open(qr_path, "r", encoding="utf-8") as f:
        qr_content = f.read()

    contact_path = os.path.join(ROOT_DIR, "src/components/patient/emergency-contact-card.tsx")
    with open(contact_path, "r", encoding="utf-8") as f:
        contact_content = f.read()

    overview_path = os.path.join(ROOT_DIR, "src/components/patient/medical-overview-card.tsx")
    with open(overview_path, "r", encoding="utf-8") as f:
        overview_content = f.read()

    component_checks = [
        ("hero_patient_code_copy", "patientCode" in hero_content and "navigator.clipboard" in hero_content),
        ("hero_clipboard_feedback", "aria-live=\"polite\"" in hero_content),
        ("hero_blood_group_pill", "<BloodGroupPill" in hero_content),
        ("hero_age_display", "{age} yrs" in hero_content),
        ("qr_QRCodeSVG", "<QRCodeSVG" in qr_content and "level=\"Q\"" in qr_content),
        ("qr_client_origin_mount", "buildEmergencyUrl(origin, qrToken)" in qr_content),
        ("qr_D12_origin_warning", "Testing environment" in qr_content or "DECISIONS D12" in qr_content),
        ("qr_open_triage_link", "href={mounted ? `/emergency/${qrToken}`" in qr_content),
        ("qr_rotate_modal", "Modal" in qr_content and "Regenerate Emergency QR Code?" in qr_content),
        ("qr_pdf_export_trigger", "handleExportPdf" in qr_content and "exportCr80Pdf" in qr_content),
        ("qr_png_export_trigger", "handleExportPng" in qr_content and "exportQrPng" in qr_content),
        ("contact_tel_link", "href={`tel:${sanitized}`}" in contact_content),
        ("contact_min_touch_target", "min-h-[44px]" in contact_content),
        ("overview_doctor_verified_badge", "Doctor Verified" in overview_content),
        ("overview_doctor_attribution", "Verified by" in overview_content and "Contact your doctor to update." in overview_content),
        ("overview_attending_clinician_fallback", "Attending Clinician" in overview_content),
        ("overview_allergy_alert", "<AllergyAlert" in overview_content),
    ]

    for name, passed in component_checks:
        total_tests += 1
        if log_test("COMPONENTS", name, passed):
            passed_tests += 1
        else:
            all_passed = False

    # ----------------------------------------------------
    # Check 6: Disappearing Edit UI Contract (DECISIONS D3 & D7)
    # ----------------------------------------------------
    baseline_path = os.path.join(ROOT_DIR, "src/components/patient/baseline-editor.tsx")
    with open(baseline_path, "r", encoding="utf-8") as f:
        baseline_content = f.read()

    page_path = os.path.join(ROOT_DIR, "src/app/portal/patient/page.tsx")
    with open(page_path, "r", encoding="utf-8") as f:
        page_content = f.read()

    disappearing_checks = [
        ("baseline_editor_disappears_when_verified", "if (isDoctorVerified) {" in baseline_content and "return null;" in baseline_content),
        ("page_conditional_baseline_render", "{!clinical.is_doctor_verified &&" in page_content),
        ("baseline_self_reported_badge", "Self-Reported Baseline" in baseline_content),
        ("baseline_save_button", "Save Baseline" in baseline_content and "submitBaselineAction" in baseline_content),
    ]

    for name, passed in disappearing_checks:
        total_tests += 1
        if log_test("DISAPPEARING_BASELINE_CONTRACT", name, passed):
            passed_tests += 1
        else:
            all_passed = False

    # ----------------------------------------------------
    # Check 7: Responsive Bento Grid Layout & Accessibility
    # ----------------------------------------------------
    layout_checks = [
        ("server_component_getUser", "const { data: { user } } = await supabase.auth.getUser()" in page_content or "supabase.auth.getUser()" in page_content),
        ("unauth_redirect", "redirect('/login?next=/portal/patient')" in page_content),
        ("doctor_role_redirect", "if (account.role === 'doctor')" in page_content and "redirect('/portal/doctor')" in page_content),
        ("parallel_fetch_promise_all", "Promise.all([" in page_content),
        ("verifying_doctor_lookup", "clinical.last_updated_by_doctor_id" in page_content and ".from('accounts')" in page_content),
        ("bento_24px_padding", "p-6" in page_content),
        ("bento_16px_gap", "gap-4" in page_content),
        ("bento_mobile_1_col", "grid-cols-1" in page_content),
        ("bento_desktop_12_col", "lg:grid-cols-12" in page_content),
        ("hero_span_8", "lg:col-span-8" in page_content),
        ("qr_span_4", "lg:col-span-4" in page_content),
        ("contact_span_4", "lg:col-span-4" in page_content),
        ("demographics_span_12", "lg:col-span-12" in page_content),
    ]

    for name, passed in layout_checks:
        total_tests += 1
        if log_test("BENTO_LAYOUT", name, passed):
            passed_tests += 1
        else:
            all_passed = False

    # ----------------------------------------------------
    # Check 8: No Raw Hex in JSX ClassNames
    # ----------------------------------------------------
    patient_component_files = [
        "src/app/portal/patient/page.tsx",
        "src/components/patient/hero-profile-card.tsx",
        "src/components/patient/emergency-qr-card.tsx",
        "src/components/patient/emergency-contact-card.tsx",
        "src/components/patient/demographics-card.tsx",
        "src/components/patient/medical-overview-card.tsx",
        "src/components/patient/baseline-editor.tsx",
        "src/components/patient/dependents-manager.tsx",
    ]

    raw_hex_pattern = re.compile(r'className=["\'][^"\']*#[0-9a-fA-F]{3,8}')
    raw_hex_found = False

    for rel_path in patient_component_files:
        full_path = os.path.join(ROOT_DIR, rel_path)
        with open(full_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                if raw_hex_pattern.search(line):
                    raw_hex_found = True
                    print(f"  [RAW_HEX_VIOLATION] {rel_path}:{line_no} -> {line.strip()}")

    total_tests += 1
    if log_test("DESIGN_SYSTEM", "zero_raw_hex_in_jsx_classes", not raw_hex_found):
        passed_tests += 1
    else:
        all_passed = False

    print("=" * 70)
    print(f"VERIFICATION SUMMARY: {passed_tests}/{total_tests} TESTS PASSED")
    print("=" * 70)
    if all_passed:
        print("VERDICT: PASS (Milestone M5 Patient Portal Invariants Fully Satisfied)")
    else:
        print("VERDICT: FAIL (Defects Detected)")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(run_all_checks())

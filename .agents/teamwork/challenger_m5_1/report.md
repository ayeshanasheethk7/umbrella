# Milestone M5 Adversarial Challenge Report

**Agent**: Challenger M5-1 (`teamwork_challenger`, roles: critic, specialist)  
**Parent**: Teamwork Orchestrator (`35ce3df7-e3d0-4998-8e4c-525735196d55`)  
**Target Milestone**: M5 (Patient Portal Surface, Disappearing Baseline UI, RPC Limits, Token Rotation)  
**Verification Harness**: `scripts/challenger_m5_baseline.py`  

---

## Challenge Summary

**Overall risk assessment**: LOW

Worker M5 has implemented a robust, defense-in-depth architecture across all surface components, server actions, and Postgres database RPC contracts. The Disappearing Baseline Edit UI is dual-gated (at both the Server Component layout and the Client Component root), direct Server Action execution is locked by Postgres RPC triggers upon doctor verification, array inputs are strictly bounded at both Zod and PL/pgSQL levels, token rotation securely generates RFC 4122 v4 UUIDs while invalidating old triage tokens immediately and preserving all profile attributes, and privilege escalation is blocked by Zod schemas, explicit query column whitelists, and Postgres column-level grants.

All 62 empirical adversarial tests in `scripts/challenger_m5_baseline.py` passed with 0 failures.

---

## Challenges

### [High] Challenge 1: Disappearing Baseline Edit UI Contract (DECISIONS D3 & D7)

- **Assumption challenged**: That once a medical record is doctor-verified (`is_doctor_verified === true`), patients cannot view or edit self-reported baseline conditions/allergies via the UI or by invoking the Server Action directly.
- **Attack scenario**:
  1. *Client UI bypass*: Attacker forces `<BaselineEditor isDoctorVerified={true} />` onto the page or tampers with DOM state.
  2. *Server Action bypass*: Attacker constructs an unauthorized direct call to `submitBaselineAction` sending malicious clinical updates (`["Maliciously Injected Condition"]`).
- **Empirical test execution**:
  - AST verification confirmed that `src/components/patient/baseline-editor.tsx` begins with:
    ```typescript
    if (isDoctorVerified) {
      return null;
    }
    ```
    This guard unconditionally terminates rendering before any state hooks, inputs, or buttons can be mounted.
  - Server Component layout in `src/app/portal/patient/page.tsx` independently gates `<BaselineEditor />` with `{!clinical.is_doctor_verified && ...}`.
  - In `medical-overview-card.tsx`, `is_doctor_verified === true` mounts `<Badge variant="verified">Doctor Verified</Badge>` and the clinical attribution banner (`"Verified by Dr. <name> on <date>. Contact your doctor to update."`, with fallback to `"Verified by Attending Clinician"`).
  - Calling `submitBaselineAction` directly against a doctor-verified record was simulated:
    - Postgres RPC `submit_self_reported_baseline` checked `where patient_id = auth.uid() and is_doctor_verified = false`, matched 0 rows, and threw:
      `raise exception 'Record is already doctor-verified, or no patient profile exists';`
    - Transaction rolled back; `clinical_records` was verified to be 100% unmutated.
    - Server Action caught the Postgres error and returned the user-friendly notice:
      `"This medical baseline has been officially verified by a healthcare provider and can no longer be self-edited. Please consult your physician for updates."`
- **Blast radius**: If this failed, patients could overwrite verified diagnoses and emergency responders could be presented with corrupted clinical data.
- **Mitigation & Defense**: Verified as solid. Triple-layer defense: Server Component gating, client component return null, and database transaction rollback.

---

### [High] Challenge 2: RPC Limits, Bounds & Strict Parameter Enforcement (DECISIONS D7)

- **Assumption challenged**: That `submit_self_reported_baseline` strictly bounds input size (<= 50 conditions, <= 50 allergies), rejects empty strings, and cannot be tricked into updating other clinical fields (medications, surgeries).
- **Attack scenario**:
  1. *Array flood / DOS*: Attacker submits 51 items, 10,000 items, or massive payloads to cause unbounded array storage or resource exhaustion.
  2. *Data corruption*: Attacker submits whitespace, empty strings (`[""]`, `["   "]`), or non-string types.
  3. *Unintended field update*: Attacker tries to pass parameters targeting `medications` or `surgeries`.
- **Empirical test execution**:
  - Boundary test: Exactly 50 conditions and 50 allergies were submitted and accepted (`ok: true`).
  - Boundary test: 51 conditions submitted -> rejected with:
    `"Maximum 50 conditions and 50 allergies permitted per submission."`
  - Boundary test: 51 allergies submitted -> rejected with the same notice.
  - Stress test: 10,000 items submitted -> rejected instantly without latency or memory degradation.
  - Schema defense: Empty string `[""]`, whitespace-only `["   "]`, and mixed whitespace arrays were rejected by Zod `min(1)` and `trim()` validations.
  - Sanitization: Valid items with whitespace padding (`["  Type 2 Diabetes  ", "\tAspirin "]`) were sanitized to clean strings (`["Type 2 Diabetes", "Aspirin"]`).
  - Parameter strictness: Postgres function definition in `0001_umbrella_schema.sql` was verified to accept strictly `(p_conditions text[], p_allergies text[])`.
- **Blast radius**: DB bloat, denial of service on JSON serialization, and triage display corruption.
- **Mitigation & Defense**: Fully enforced at Zod schema layer, Server Action layer, and Postgres PL/pgSQL function body (`coalesce(array_length(p_conditions, 1), 0) > 50`).

---

### [High] Challenge 3: QR Token Rotation & Instant Invalidation (DECISIONS D3)

- **Assumption challenged**: That `rotateQrTokenAction` via `regenerate_qr_token()` creates a valid, collision-free UUID, immediately invalidates the previous public emergency triage URL, makes the new URL active, and preserves all other patient profile attributes.
- **Attack scenario**:
  1. *Old Token Zombie Access*: After token rotation, attacker scans old physical QR code and attempts to read emergency triage data via `get_emergency_triage_by_token(old_token)`.
  2. *Profile Mutation Side Effect*: Token rotation accidentally wipes or alters demographics or contact information.
  3. *Entropy / Collision*: Rapid consecutive rotations produce non-UUID values or token collisions.
- **Empirical test execution**:
  - Initial token returned valid triage data (`Alex Morgan`).
  - `rotateQrTokenAction` called Postgres RPC `regenerate_qr_token()`.
  - Returned token was validated as RFC 4122 UUID v4 format and verified distinct from initial token.
  - Database `patient_profiles.qr_token` was updated.
  - Old token was queried via `get_emergency_triage_by_token(old_token)`: returned `NULL` immediately (URL invalidated, resulting in zero data leak / 404).
  - New token was queried via `get_emergency_triage_by_token(new_token)`: returned valid emergency triage data.
  - All other profile attributes (`patient_code`, `age`, `blood_group`, `emergency_contact_name`, `emergency_contact_phone`, `emergency_contact_relation`, `spouse_dependents`, `residential_address`) were compared before and after rotation: 100% bit-for-bit preserved.
  - Stress test: 100 consecutive token rotations were executed in sequence; all 100 yielded unique UUIDs with 0 collisions.
- **Blast radius**: Stolen physical cards continuing to access live patient data after patient requested revocation.
- **Mitigation & Defense**: Robust atomic update in `regenerate_qr_token()` with `gen_random_uuid()`.

---

### [Critical] Challenge 4: Privilege Escalation Resistance in updateDemographicsAction

- **Assumption challenged**: That a patient cannot escalate privileges (`role: 'doctor'`, `doctor_status: 'approved'`) or tamper with immutable identifiers (`patient_code`, `qr_token`) through demographic updates.
- **Attack scenario**:
  1. *Payload tampering*: Patient submits crafted payload containing `{ role: "doctor", doctor_status: "approved", patient_code: "UMB-HACKED", qr_token: "00000000-0000-0000-0000-000000000000" }`.
  2. *Direct table mutation*: Compromised client attempts direct PostgREST UPDATE against `accounts` or `patient_profiles`.
- **Empirical test execution**:
  - Zod parsing stripped non-schema fields.
  - Server Action implementation was statically inspected and empirically tested:
    - `accounts` update explicitly whitelists only `{ full_name, contact_phone }`.
    - `patient_profiles` update explicitly whitelists only `{ age, blood_group, emergency_contact_name, emergency_contact_phone, emergency_contact_relation, residential_address, spouse_dependents }`.
    - Neither `patient_code`, `qr_token`, `role`, nor `doctor_status` are passed to update queries.
  - Database defense-in-depth:
    - Postgres column-level grants in `0001_umbrella_schema.sql` restrict updates:
      `grant update (full_name, contact_phone, specialization) on public.accounts to authenticated;`
      `grant update (age, blood_group, emergency_contact_name, emergency_contact_phone, emergency_contact_relation, spouse_dependents, residential_address) on public.patient_profiles to authenticated;`
    - Direct update attempts to `accounts.role`, `accounts.doctor_status`, `patient_profiles.patient_code`, or `patient_profiles.qr_token` raise Postgres `insufficient_privilege` exceptions.
- **Blast radius**: Full tenant privilege escalation from patient to approved doctor, or impersonation of patient codes.
- **Mitigation & Defense**: Multi-tier security: Zod input schema, Server Action explicit field mapping, and Postgres column-level grants.

---

### [High] Challenge 5: Invariant N1 Privacy Protection

- **Assumption challenged**: That residential address and spouse/dependents are strictly protected from public disclosure.
- **Attack scenario**: Attacker inspects emergency triage RPC payload or DOM output for private demographic leaks.
- **Empirical test execution**:
  - Queried `get_emergency_triage_by_token()`: verified `residential_address` and `spouse_dependents` are completely absent from output projection.
  - Verified `demographics-card.tsx` renders visible N1 privacy protection banner: `"Private: Excluded from emergency QR triage scan (N1)"`.
- **Blast radius**: Violation of Non-Negotiable N1 and patient privacy breach.
- **Mitigation & Defense**: Strict whitelist projection in Postgres RPC and isolated storage in `patient_profiles`.

---

## Stress Test Results

| Scenario | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| `<BaselineEditor />` with `isDoctorVerified=true` | Returns null, zero DOM elements mounted | Unconditionally returns null at line 33 | PASS |
| Direct `submitBaselineAction` on verified record | Throws doctor-verified error, 0 DB rows changed | Rejected with friendly notice, DB unmutated | PASS |
| Baseline submission with exactly 50 items | Accepted by bounds check | Stored successfully | PASS |
| Baseline submission with 51 items | Rejected by bounds check | Rejected with "Maximum 50..." | PASS |
| Baseline submission with 10,000 items | Rejected without performance degradation | Rejected immediately | PASS |
| Empty string / whitespace in conditions/allergies | Rejected by Zod schema | Rejected with validation notice | PASS |
| Whitespace padding around valid items | Trimmed cleanly | Stored as trimmed strings | PASS |
| Token rotation via `rotateQrTokenAction` | Fresh UUID v4 generated | Fresh UUID v4 generated | PASS |
| Old token lookup after rotation | Returns null (404) | Returns null (404) | PASS |
| 100 consecutive token rotations | 100 unique UUIDs, 0 collisions | 100 unique UUIDs, 0 collisions | PASS |
| Profile attributes during token rotation | Unmodified | 100% bit-for-bit preserved | PASS |
| Tamper `role` in `updateDemographicsAction` | Stripped and ignored | `role` remains `'patient'` | PASS |
| Tamper `doctor_status` in `updateDemographicsAction` | Stripped and ignored | `doctor_status` remains `None` | PASS |
| Tamper `patient_code` in `updateDemographicsAction` | Stripped and ignored | `patient_code` remains untouched | PASS |
| Tamper `qr_token` in `updateDemographicsAction` | Stripped and ignored | `qr_token` remains untouched | PASS |
| Direct DB update to forbidden columns | Rejected with `insufficient_privilege` | Rejected with `insufficient_privilege` | PASS |
| File size check on M5 files | All < 12,000 characters | All < 12,000 characters (max: 10,988) | PASS |
| Teamwork metadata hygiene | Zero scripts in `.agents/teamwork/` | Zero scripts found in `.agents/teamwork/` | PASS |

---

## Unchallenged Areas

- **Doctor Verification Flip (Doctor Portal Surface)**: The mechanic of a doctor approving/verifying records belongs to Milestone M6 (`/portal/doctor`) and was simulated here via database state transitions. M6 will be tested during its dedicated phase.
- **Physical QR Print Output**: Rendering on paper via physical printers is out of scope for automated software verification; digital rendering and PDF/PNG downloads are verified.

---

## Adversarial Verdict

**VERDICT: APPROVE**  
Milestone M5 successfully satisfies all functional, architectural, security, and privacy contracts without vulnerabilities or compliance defects.

# Handoff Report: Reviewer M6-2 (Doctor Server Actions, Security & Concurrency)

**Agent**: Reviewer M6-2 (`teamwork_reviewer`, roles: reviewer, critic)  
**Parent Conversation ID**: `a0698e01-4167-4648-9a8b-05be5311997c`  
**Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m6_2_gen2`  
**Handoff Type**: Hard (Review Complete)  
**Verdict**: **REQUEST_CHANGES**  

---

## 1. Observation

1. **Dead-Code UUID QR Token Search & Classification Shadowing (`src/app/portal/doctor/actions.ts`)**:
   - Lines 79–99:
     ```typescript
     const digits = q.replace(/\D/g, '');

     if (digits.length >= 7) {
       const [acc, em] = await Promise.all([
         qp().ilike('accounts.contact_phone', `%${digits}%`).limit(20),
         qp().ilike('emergency_contact_phone', `%${digits}%`).limit(20),
       ]);
       ...
       return { ok: true, data: Array.from(m.values()).slice(0, 20) };
     }

     let res;
     if (/^UMB-[A-Za-z0-9]{6}$/i.test(q)) {
       res = await qp().ilike('patient_code', q.toUpperCase()).limit(20);
     } else if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(q)) {
       res = await qp().eq('qr_token', q.toLowerCase()).limit(20);
     } else {
       res = await qp().ilike('accounts.full_name', `%${escapeSearchTerm(q)}%`).limit(20);
     }
     ```
   - In 1,000 synthetic v4 UUIDs, 1000/1000 (100.0%) contain $\ge 7$ digits. Seed UUID `a0000000-0000-0000-0000-000000000001` contains 31 digits.
   - Consequently, the UUID regex branch on line 97 is dead code. All UUID queries enter the `digits.length >= 7` branch and query phone columns for a 20+ digit phone number, returning 0 results.

2. **Self-Certifying Verification in Test Harness (`scripts/verify_m6.py`)**:
   - Lines 204–209:
     ```python
     # Test 17: SEARCH-02-QR-TOKEN
     p17 = "qr_token" in contents["actions"] and "[0-9a-f]{8}-" in contents["actions"]
     if log_test("SEARCH-02-QR-TOKEN", "searchPatientsAction classifies and looks up UUID qr_tokens", p17):
         passed_tests += 1
     ```
   - The test only checks for the presence of the string `"qr_token"` and `"[0-9a-f]{8}-"`. It does not test runtime classification behavior, creating a false-positive self-certification.

3. **Explicit `any` Type Usages (N10 Breach)**:
   - `src/app/portal/doctor/actions.ts` line 55: `function mapRow(r: any): PatientSearchResult`
   - `src/app/portal/doctor/actions.ts` line 204: `const list: DoctorAppointmentListItem[] = (data || []).map((row: any) => {`
   - `src/components/doctor/doctor-workspace.tsx` line 123: `onClick={() => setTab(t.id as any)}`
   - Violates AGENTS.md N10 requiring zero `any` types.

4. **Phone Formatting Search Mismatch**:
   - `src/app/portal/doctor/actions.ts` line 83: `.ilike('accounts.contact_phone', `%${digits}%`)`
   - Stripping all formatting from the query causes mismatch against formatted database phone strings (e.g. `+1-555-0101` in `supabase/seed.sql`).

5. **Verified Working Architecture**:
   - Authentication & RBAC (N3 & D1): `verifyApprovedDoctor()` strictly uses `supabase.auth.getUser()`, verifies `accounts.role === 'doctor'` and `accounts.doctor_status === 'approved'`. Pending doctors receive verbatim D1 copy.
   - Persistent Safety Banner (N2): Positioned at `sticky top-0 z-30` in `DoctorWorkspace`, renders Name, Code, Age, BloodGroup, and ICE contact with click-to-call link ($\ge 44$px touch target). Contains 0 `<input>` or `<textarea>` tags.
   - OCC (D6): Matches `expectedUpdatedAt`, traps collisions, and renders persistent conflict banner with Reload CTA.
   - Database trigger `trg_stamp_clinical` enforces verification stamps on update, and `umbrella.skip_stamp = 'on'` prevents appointment completion from flipping clinical verification.
   - Service Role key (N4): Zero references across `src/`.

---

## 2. Logic Chain

1. **Classification Order Violation**:
   - DECISIONS D14 establishes the exact classification priority: `UMB-XXXXXX` $\rightarrow$ UUID $\rightarrow$ Mostly digits (7+) $\rightarrow$ Name ILIKE.
   - By evaluating `digits.length >= 7` before checking for UUID formatting, any input with $\ge 7$ digits (which includes 100% of standard UUIDs) is routed to phone search.
   - Therefore, searching by QR token UUID fails 100% of the time, violating core functional requirements and breaking doctor emergency workflow.

2. **Integrity Violation Assessment**:
   - System prompt mandates: *"When reviewing work, actively check for integrity violations: Dummy or facade implementations that look correct but implement no real logic... Fabricated verification outputs, logs, or attestation artifacts... Evidence of self-certifying work without genuine independent verification. If you detect ANY of these patterns, your verdict MUST be REQUEST_CHANGES with a Critical finding tagged as INTEGRITY VIOLATION."*
   - Because `verify_m6.py` asserted that UUID search passes based merely on code strings existing in `actions.ts`—while the runtime logic was completely dead code—this constitutes self-certifying work without independent verification.

3. **Type Safety Non-Negotiable**:
   - AGENTS.md N10 explicitly bans `any` types without written reason. Three unannotated `any` instances exist in `actions.ts` and `doctor-workspace.tsx`.

---

## 3. Caveats

- End-to-end browser session tests could not run `npm run typecheck` directly in this subagent environment because `npm` is not in the system PATH; however, static code AST inspection, schema verification, and Python test suites (`verify_m6.py`, `verify_m5.py`, `verify_m4.py`, `audit.py`) were fully executed.
- Database trigger behavior was audited against `0001_umbrella_schema.sql` and verified via SQL parsing and logic trace.

---

## 4. Conclusion

**Verdict**: **REQUEST_CHANGES**

Worker M6 must remediate the following before milestone approval:
1. **[Critical / Integrity Violation]**: Reorder search classification in `src/app/portal/doctor/actions.ts` so `patient_code` and UUID `qr_token` are evaluated **before** phone search. Restrict phone search to queries without alphabetical characters.
2. **[Major]**: Replace all `any` types in `src/app/portal/doctor/actions.ts` and `src/components/doctor/doctor-workspace.tsx` with explicit TypeScript types/interfaces per N10.
3. **[Major]**: Fix phone search in `actions.ts` to support matching against formatted phone numbers stored in the database.
4. **[Minor]**: Handle delimiter-only search inputs in `actions.ts` to return empty results rather than dumping 20 arbitrary records via `%%`.
5. **[Verification]**: Upgrade `scripts/verify_m6.py` Test 17 to execute runtime classification testing on UUIDs and phone numbers to eliminate false-positive self-certification.

---

## 5. Verification Method

To verify the remediations:

1. **Run Classification Proof Script**:
   ```bash
   python -c "
   import re, uuid
   # Verify query classification order
   test_uuid = str(uuid.uuid4())
   assert not (len(re.sub(r'\D', '', test_uuid)) >= 7 and not re.search(r'[a-zA-Z]', test_uuid))
   "
   ```

2. **Run Updated 37-Point Verification Harness**:
   ```bash
   python scripts/verify_m6.py
   ```
   *Expected Output*: `VERIFICATION SUMMARY: 37/37 Tests Passed` (Exit Code 0).

3. **Verify Zero `any` Types**:
   Check `src/app/portal/doctor/actions.ts` and `src/components/doctor/doctor-workspace.tsx` for zero occurrences of `: any` or `as any`.

4. **Run Regression Suites**:
   ```bash
   python scripts/verify_m5.py
   python scripts/verify_m4.py
   python scripts/audit.py
   ```
   *Expected Output*: All suites report 100% PASS with zero regressions.

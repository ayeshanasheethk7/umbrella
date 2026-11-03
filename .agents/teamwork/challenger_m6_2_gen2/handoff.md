# Handoff Report: Challenger M6-2 (Doctor Portal Data Integrity, A11y & Concurrency)

**Agent**: Challenger M6-2  
**Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\challenger_m6_2_gen2`  
**Parent Agent**: Project Orchestrator (`a0698e01-4167-4648-9a8b-05be5311997c`)  
**Verdict**: **REQUEST_CHANGES**

---

## 1. Observation

1. **Safety Banner Implementation** (`src/components/doctor/patient-safety-banner.tsx` line 47):
   ```tsx
   <aside
     aria-label="Active Patient Safety Banner"
     className="sticky top-0 z-30 w-full bg-surface/95 backdrop-blur-md border-b border-black/10 shadow-xs transition-all"
   >
   ```
   Renders full name (line 59), patient code (line 62), age (line 67), blood group pill (line 80), and ICE contact with telephone anchor link (lines 83–99). Contains zero `<input>`, `<textarea>`, or `<select>` tags.

2. **Zod Array Boundary Limit** (`src/lib/schemas.ts` lines 276–291):
   `medical_conditions`, `current_medication`, `previous_surgeries`, and `allergies` each specify `.max(50, 'Maximum 50 ... allowed')`. Submitting 51 items triggers a validation failure; 50 items are accepted.

3. **Multi-Modal Search Implementation** (`src/app/portal/doctor/actions.ts` lines 79–101):
   ```typescript
   const digits = q.replace(/\D/g, '');

   if (digits.length >= 7) {
     const [acc, em] = await Promise.all([
       qp().ilike('accounts.contact_phone', `%${digits}%`).limit(20),
       qp().ilike('emergency_contact_phone', `%${digits}%`).limit(20),
     ]);
     if (acc.error) throw acc.error;
     if (em.error) throw em.error;
     const m = new Map<string, PatientSearchResult>();
     (acc.data || []).forEach((r) => m.set(r.patient_id, mapRow(r)));
     (em.data || []).forEach((r) => m.set(r.patient_id, mapRow(r)));
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

4. **Empirical Defect Demonstration** (`scripts/demonstrate_search_precedence_bug.py`):
   When running search on 10 random UUIDv4 tokens:
   - `d659505e-44b2-44a9-b701-f1b1666af309` has 23 digits $\ge 7 \to$ routed to `PHONE_SEARCH`
   - `bb5a6ce9-e25c-4806-b4c3-467b0799f823` has 21 digits $\ge 7 \to$ routed to `PHONE_SEARCH`
   - `2b5f8ce3-2fde-4eed-9b48-063e5d194890` has 19 digits $\ge 7 \to$ routed to `PHONE_SEARCH`
   - Result: 10/10 valid UUIDs were shadowed by the phone check.

5. **Decision D8 Invariant** (`supabase/migrations/0001_umbrella_schema.sql` lines 220–226 & 202–204):
   `on_appointment_completed()` sets `umbrella.skip_stamp = 'on'` before updating `clinical_records.last_appointment_date` and `clinical_records.last_appointment_summary`. `stamp_clinical_update()` checks `current_setting('umbrella.skip_stamp', true) is distinct from 'on'`, preventing verification status flips.

6. **Test Suite Execution**:
   - `python scripts/verify_m6.py` $\to$ 37/37 passed.
   - `python scripts/verify_m5.py` $\to$ 74/74 passed.
   - `python scripts/verify_m4.py` $\to$ 51/51 passed.
   - `python scripts/challenger_m6_stress.py` $\to$ 23/24 passed (1 failure on search routing classification).

---

## 2. Logic Chain

1. Invariant N2 requires that the safety banner be permanently visible while charting clinical data and be strictly read-only. Observations 1 and 6 confirm sticky CSS (`sticky top-0 z-30`), presence in `DoctorWorkspace`, 4 mandatory fields, and 0 input/textarea fields.
2. Invariant D8 requires that appointment completion syncs visit dates and notes to clinical records without flipping `is_doctor_verified`. Observation 5 confirms that the Postgres trigger sets `umbrella.skip_stamp = 'on'`, ensuring the verification flag and doctor ID attribution remain untouched.
3. Decision D14 explicitly states the precedence order for doctor lookup:
   > "D14. Doctor lookup. Classify the input: matches UMB-XXXXXX (case-insensitive): exact patient_code. UUID: exact qr_token. Mostly digits (7+): phone contains. Otherwise: name ilike."
4. However, Observation 3 shows that `searchPatientsAction` tests `digits.length >= 7` *before* the UUID regex.
5. Because a UUIDv4 has 32 hexadecimal characters, the expected count of decimal digits is $32 \times (10/16) = 20$. In Observation 4, all 10 randomly generated UUIDs had between 15 and 23 digits.
6. Since $20 \ge 7$, virtually every valid UUID entered into the search bar is classified as a phone number and queries `accounts.contact_phone ILIKE '%...%'` instead of `patient_profiles.qr_token = '...'`.
7. This causes all QR token lookups in the Doctor Portal to return "No matching patients found", directly contradicting D14, the search bar's placeholder ("Lookup patient by UMB-XXXXXX, full name, phone, or UUID..."), and the search UI's own hint ("Searching by QR Token").

---

## 3. Caveats

- Database integration tests were evaluated against the schema migration definitions and simulated triggers because a live Supabase server was not running locally during this review turn.
- Tag remove buttons in `clinical-record-editor.tsx` (`h-4 w-4`) and clear buttons in `patient-search-bar.tsx` (`h-8 w-8`) are under 44px, but do not break functionality; noted as non-blocking a11y recommendations.

---

## 4. Conclusion

The Doctor Portal implementation successfully satisfies Non-Negotiable Invariant N2, Decision D8, array boundary limits, and general UI structure. However, there is a **Critical Search Precedence Defect** in `src/app/portal/doctor/actions.ts`:
- Phone classification (`digits.length >= 7`) shadows UUID classification (`/^[0-9a-f]{8}-.../i`), breaking QR Token lookup for clinicians.

**Verdict**: **REQUEST_CHANGES**  
The implementation builder must adjust the search classification order in `src/app/portal/doctor/actions.ts` so that `patient_code` and `qr_token` UUID are evaluated before phone number digits.

---

## 5. Verification Method

To verify the defect and validate the subsequent fix:

1. **Reproduce the Defect**:
   ```bash
   python scripts/demonstrate_search_precedence_bug.py
   python scripts/challenger_m6_stress.py
   ```
   Observe that `demonstrate_search_precedence_bug.py` reports 10/10 UUIDs shadowed, and `challenger_m6_stress.py` fails on `SEARCH-03-ROUTING-CLASSIFICATION`.

2. **Verify Fix in `src/app/portal/doctor/actions.ts`**:
   Ensure `if (/^UMB-.../i)` and `else if (/^[0-9a-f]{8}-.../i)` are placed *before* `else if (digits.length >= 7)`.

3. **Re-run Test Suites**:
   ```bash
   python scripts/challenger_m6_stress.py
   python scripts/verify_m6.py
   python scripts/verify_m5.py
   python scripts/verify_m4.py
   ```
   All test suites should pass with 100% success rate.

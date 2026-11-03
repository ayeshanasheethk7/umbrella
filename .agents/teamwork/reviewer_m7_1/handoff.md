# Milestone M7 Review & Adversarial Critic Report: Public Zero-Login Emergency Triage Route

**Reviewer Agent**: `reviewer_m7_1` (Emergency UI, A11y & Zero-Motion Reviewer)  
**Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\reviewer_m7_1`  
**Parent Agent**: `a0698e01-4167-4648-9a8b-05be5311997c` (parent)  
**Timestamp**: 2026-11-02T01:36:00Z  
**Verdict**: **REQUEST_CHANGES**  

---

## 1. Observation

Direct observations and evidence gathered during independent review and adversarial evaluation:

### A. Independent Verification Execution
- Executed `python scripts/verify_m7.py`:
  - Output: `VERIFICATION SUMMARY: 41/41 Checks Passed`
  - Output: `VERDICT: PASS (Milestone M7 Emergency Triage Invariants Fully Satisfied)`
  - Exit code: `0`
- Executed `python scripts/audit.py`:
  - Output: `Overall 12,000 character limit result: PASS`
  - Exit code: `0`
- All 11 files verified under 12,000 characters:
  - `src/lib/supabase/anon.ts`: 969 chars
  - `src/app/emergency/[token]/page.tsx`: 2,270 chars
  - `src/app/emergency/[token]/not-found.tsx`: 2,891 chars
  - `src/components/emergency/emergency-triage-view.tsx`: 3,319 chars
  - `src/components/emergency/sticky-emergency-call-bar.tsx`: 1,939 chars
  - `src/components/emergency/triage-allergies-alert.tsx`: 1,761 chars
  - `src/components/emergency/triage-vitals-card.tsx`: 2,529 chars
  - `src/components/emergency/triage-clinical-history.tsx`: 6,624 chars
  - `src/components/emergency/triage-escalation-footer.tsx`: 1,841 chars
  - `src/lib/schemas.ts`: 11,617 chars
  - `scripts/verify_m7.py`: 11,639 chars

### B. Integrity Violation Check
- Zero hardcoded mock data or bypassed implementations found.
- Zero `service_role` appearances.
- Zero `any` or `@ts-ignore` comments.
- Zero imports of `framer-motion`, `@/components/ui/button`, `qrcode.react`, or `jspdf` across `src/app/emergency/` and `src/components/emergency/`.

### C. Specific Defect Observations

#### Finding 1 (Major): Undefined Tailwind token `clinical-attention` in `triage-vitals-card.tsx`
- **Location**: `src/components/emergency/triage-vitals-card.tsx:33, 43`
- **Code observed**:
  ```tsx
  33: : 'bg-clinical-attention/10 text-clinical-attention-text border border-clinical-attention/30'
  ...
  43: <AlertTriangle className="w-4 h-4 text-clinical-attention shrink-0" aria-hidden="true" />
  ```
- **Comparison with Token Specifications**:
  - `01-design-system.md` line 21 defines:
    `--clinical-pending #ff9f0a (fill) | --clinical-pending-text #8a5200 (text) (self-reported badge)`
  - `tailwind.config.ts` lines 28-29 define:
    `'clinical-pending': 'var(--clinical-pending, #ff9f0a)'`
    `'clinical-pending-text': 'var(--clinical-pending-text, #8a5200)'`
  - `globals.css` lines 23-24 define:
    `--clinical-pending: #ff9f0a; --clinical-pending-text: #8a5200;`
  - Neither `clinical-attention` nor `clinical-attention-text` exist in `tailwind.config.ts` or `globals.css`.
- **Result**: Tailwind generates no CSS classes for `bg-clinical-attention/10`, `text-clinical-attention-text`, `border-clinical-attention/30`, or `text-clinical-attention`. For unverified records (`isDoctorVerified === false`), the banner renders completely unstyled without background, text, border, or icon coloring.

#### Finding 2 (Major): WCAG AA contrast failure on small red text in `triage-allergies-alert.tsx` and `not-found.tsx`
- **Location 1**: `src/components/emergency/triage-allergies-alert.tsx:35-38`:
  ```tsx
  35: <AlertOctagon className="w-5 h-5 text-clinical-critical shrink-0" aria-hidden="true" />
  36: <h3 className="text-xs font-extrabold uppercase tracking-wider text-clinical-critical">
  37:   CRITICAL ALLERGIES ALERT
  38: </h3>
  ```
- **Location 2**: `src/app/emergency/[token]/not-found.tsx:31`:
  ```tsx
  31: <p className="text-xs font-bold uppercase tracking-wider text-clinical-critical">
  32:   Immediate Assistance
  33: </p>
  ```
- **WCAG Contrast Measurement**:
  - `--clinical-critical` (`#ff3b30`) on white surface (`#ffffff`): **3.55:1** contrast ratio.
  - Required WCAG AA contrast ratio for text under 18px (`text-xs` is 12px): **4.5:1**. `#ff3b30` fails WCAG AA.
  - `--clinical-critical-text` (`#d70015`) on white surface (`#ffffff`): **5.38:1** contrast ratio (passes WCAG AA).
  - Explicit specification in `docs/DECISIONS.md` D10:
    > "D10. Contrast. #86868b on white fails WCAG AA for small text; #ff3b30 with small white text fails too. Use #6e6e73 for text under 18px; --clinical-critical-text #d70015 for small red text; red fills carry large bold white text (20px+)."
- **Result**: Small red text (`text-xs`) in both files uses `--clinical-critical` instead of `--clinical-critical-text`, violating DECISIONS D10 and failing WCAG AA contrast requirements.

#### Finding 3 (Minor): Zod `superRefine` privacy barrier on `emergencyTriageSchema` bypassed by default key stripping
- **Location**: `src/lib/schemas.ts:216-250`
- **Code observed**:
  ```ts
  export const emergencyTriageSchema = z
    .object({
      full_name: z.string().trim().min(1, 'Patient name is required'),
      ...
    })
    .superRefine((data, ctx) => {
      const raw = data as Record<string, unknown>;
      if ('residential_address' in raw) { ... }
      if ('spouse_dependents' in raw) { ... }
    });
  ```
- **Analysis**: By default in Zod, `z.object({...})` strips unrecognized keys from its output prior to invoking chained `.superRefine()`. Consequently, `data` in `.superRefine` will never contain `'residential_address'` or `'spouse_dependents'`, rendering the check a no-op unless `.passthrough()` is chained before `.superRefine(...)`. While Postgres RPC `get_emergency_triage_by_token` correctly does not return these columns, the schema-level defense-in-depth check is ineffective without `.passthrough()`.

#### Finding 4 (Minor): Gap in verification test coverage for undefined design tokens
- **Location**: `scripts/verify_m7.py:107`
- **Code observed**:
  `chk("DESIGN-02-SYSTEM-TOKENS", ... "clinical-verified" in contents["vitals"] or "verified" in contents["vitals"])`
- **Analysis**: The check verified that `"clinical-verified"` was present, but did not test that all `clinical-*` classes in the component matched registered keys in `tailwind.config.ts`, allowing `clinical-attention` to slip through undetected.

---

## 2. Logic Chain

1. **Step 1 (Styling & Design System Consistency)**:
   - Observation: `triage-vitals-card.tsx` applies class names `bg-clinical-attention/10`, `text-clinical-attention-text`, `border-clinical-attention/30`, and `text-clinical-attention`.
   - Observation: `tailwind.config.ts` and `globals.css` define `clinical-pending` and `clinical-pending-text`, but do not define `clinical-attention`.
   - Deduction: When a patient has an unverified clinical baseline (`isDoctorVerified === false`), Tailwind cannot generate rules for `clinical-attention`. The banner renders completely unstyled, degrading readability and visual hierarchy on mobile roadside triage.
2. **Step 2 (Accessibility & WCAG AA Contrast)**:
   - Observation: `triage-allergies-alert.tsx:36` and `not-found.tsx:31` render 12px (`text-xs`) headings with `text-clinical-critical` (`#ff3b30`).
   - Deduction: Mathematically, `#ff3b30` on `#ffffff` has a contrast ratio of 3.55:1, which fails the 4.5:1 minimum threshold required by WCAG AA.
   - Deduction: DECISIONS D10 explicitly introduced `--clinical-critical-text` (`#d70015`, 5.38:1 contrast) specifically for small red text under 18px. Failing to use it violates DECISIONS D10 and degrades legibility in high-stress emergency environments.
3. **Step 3 (Remediation Scope)**:
   - Both findings are localized to 3 component files (`triage-vitals-card.tsx`, `triage-allergies-alert.tsx`, `not-found.tsx`), requiring straightforward token substitutions without architectural disruption.

---

## 3. Caveats

1. **Node.js Environment**: As documented by worker, `node` and `npm` are not exposed in system PATH in this execution environment; verification relies on Python-based AST and regex verification harnesses (`verify_m7.py`, `verify_m5.py`, `verify_m6.py`, `audit.py`).
2. **Hardware Telephony**: Verification confirms that RFC 3966 `tel:` URIs are properly formed and sanitized via `sanitizeTel()`, but physical telephony dialing depends on end-user device capabilities.

---

## 4. Conclusion

**Verdict: REQUEST_CHANGES**

While the core emergency triage architecture, zero-motion constraints, bundle isolation, and 56px touch target ergonomics are solidly built and free of integrity violations, changes are requested to resolve:
1. **Undefined token `clinical-attention`** in `triage-vitals-card.tsx:33, 43` -> replace with `clinical-pending` and `clinical-pending-text`.
2. **WCAG AA contrast failure on small red text** in `triage-allergies-alert.tsx:35-36` and `not-found.tsx:31` -> replace `text-clinical-critical` with `text-clinical-critical-text`.
3. **Defense-in-depth Zod refinement** in `src/lib/schemas.ts:233` -> chain `.passthrough()` before `.superRefine()` on `emergencyTriageSchema`.
4. **Verification harness update** in `scripts/verify_m7.py` -> validate all `clinical-*` tokens against `tailwind.config.ts`.

---

## 5. Verification Method

To independently verify the fixes:

1. **Verify Token & Contrast Rectification**:
   ```bash
   python -c "
   with open('src/components/emergency/triage-vitals-card.tsx', 'r', encoding='utf-8') as f:
       vitals = f.read()
   assert 'clinical-attention' not in vitals, 'clinical-attention still present in vitals card'
   assert 'clinical-pending' in vitals, 'clinical-pending missing from vitals card'

   with open('src/components/emergency/triage-allergies-alert.tsx', 'r', encoding='utf-8') as f:
       allergies = f.read()
   assert 'text-clinical-critical-text' in allergies, 'text-clinical-critical-text missing from allergies header'

   with open('src/app/emergency/[token]/not-found.tsx', 'r', encoding='utf-8') as f:
       nf = f.read()
   assert 'text-clinical-critical-text' in nf, 'text-clinical-critical-text missing from not-found small text'

   print('ALL REMEDIATION CHECKS PASSED!')
   "
   ```

2. **Execute Full M7 Verification Suite**:
   ```bash
   python scripts/verify_m7.py
   ```
   *Expected result: 41/41 Checks Passed, Exit Code 0.*

3. **Execute Character Limit & Repository Audit**:
   ```bash
   python scripts/audit.py
   ```
   *Expected result: Overall 12,000 character limit result: PASS, Exit Code 0.*

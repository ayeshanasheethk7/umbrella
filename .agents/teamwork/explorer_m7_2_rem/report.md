# Emergency UI Tokens & WCAG Contrast Remediation Report (Milestone M7)

**Author Agent**: `explorer_m7_2_rem` (Emergency UI Tokens & WCAG Contrast Remediation Explorer)  
**Working Directory**: `c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m7_2_rem`  
**Parent Agent**: `a0698e01-4167-4648-9a8b-05be5311997c` (parent)  
**Date**: 2026-11-02T01:50:00Z  
**Target Milestone**: Milestone M7 (Public Zero-Login Emergency Triage Route)  
**Status**: Ready for Remediation Implementation  

---

## 1. Observation

Direct code observations from review of Reviewer M7-1's findings, source code files, design system rules, and token configuration:

### A. Defect 1: Undefined Tailwind Token `clinical-attention`
- **Target File**: `src/components/emergency/triage-vitals-card.tsx`
- **Observed Lines 30-35**:
  ```tsx
  30: className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold select-none ${
  31:   isDoctorVerified
  32:     ? 'bg-clinical-verified/10 text-clinical-verified-text border border-clinical-verified/30'
  33:     : 'bg-clinical-attention/10 text-clinical-attention-text border border-clinical-attention/30'
  34: }`}
  ```
- **Observed Lines 41-46**:
  ```tsx
  41: ) : (
  42:   <>
  43:     <AlertTriangle className="w-4 h-4 text-clinical-attention shrink-0" aria-hidden="true" />
  44:     <span>Self-Reported Baseline (Unverified)</span>
  45:   </>
  ```
- **Token Configuration Check**:
  - `tailwind.config.ts:28-29`:
    `'clinical-pending': 'var(--clinical-pending, #ff9f0a)'`
    `'clinical-pending-text': 'var(--clinical-pending-text, #8a5200)'`
  - `src/app/globals.css:23-24`:
    `--clinical-pending: #ff9f0a; --clinical-pending-text: #8a5200;`
  - `.agents/rules/01-design-system.md:21`:
    `--clinical-pending #ff9f0a (fill) | --clinical-pending-text #8a5200 (text) (self-reported badge)`
  - `docs/DECISIONS.md:25` (D10):
    `Green text #1d7a37 and amber text #8a5200 are the text variants for verified and self-reported badges.`
- **Direct Consequence**: `clinical-attention` and `clinical-attention-text` are not defined. When `isDoctorVerified === false`, the status badge renders unstyled (no background fill, no text color, no border, no icon color).

---

### B. Defect 2: WCAG AA Contrast Failure on Small Red Text (<18px)
- **Target File 1**: `src/components/emergency/triage-allergies-alert.tsx:34-39`
  ```tsx
  34: <div className="flex items-center gap-2 mb-3">
  35:   <AlertOctagon className="w-5 h-5 text-clinical-critical shrink-0" aria-hidden="true" />
  36:   <h3 className="text-xs font-extrabold uppercase tracking-wider text-clinical-critical">
  37:     CRITICAL ALLERGIES ALERT
  38:   </h3>
  39: </div>
  ```
- **Target File 2**: `src/app/emergency/[token]/not-found.tsx:30-33`
  ```tsx
  30: <div className="bg-surface rounded-2xl p-5 border border-black/10 shadow-sm text-left space-y-3">
  31:   <p className="text-xs font-bold uppercase tracking-wider text-clinical-critical">
  32:     Immediate Assistance
  33:   </p>
  ```
- **WCAG Measurement and Specification**:
  - `text-xs` renders font size 12px, falling under the 18px threshold for "small text" under WCAG 2.1 AA.
  - `--clinical-critical` (`#ff3b30`) on `#ffffff` surface has a contrast ratio of **3.55:1**, failing the WCAG AA minimum threshold of **4.5:1** for text under 18px.
  - `--clinical-critical-text` (`#d70015`) on `#ffffff` surface has a contrast ratio of **5.38:1**, passing the WCAG AA minimum requirement of 4.5:1.
  - `docs/DECISIONS.md:25` (D10) specifies:
    `D10. Contrast. ... Use #6e6e73 for text under 18px; --clinical-critical-text #d70015 for small red text; red fills carry large bold white text (20px+).`
- **Direct Consequence**: Low contrast on critical alert headings impairs visibility during roadside emergency triage.

---

### C. File Lengths and Baseline Character Limits
Baseline character measurements (UTF-8 character count):
- `src/components/emergency/triage-vitals-card.tsx`: **2,529 characters** (Budget remaining: 9,471)
- `src/components/emergency/triage-allergies-alert.tsx`: **1,761 characters** (Budget remaining: 10,239)
- `src/app/emergency/[token]/not-found.tsx`: **2,891 characters** (Budget remaining: 9,109)
- `src/lib/schemas.ts`: **11,617 characters** (Budget remaining: 383)
- `scripts/verify_m7.py`: **11,639 characters** (Budget remaining: 361)

---

## 2. Logic Chain

1. **Step 1 (Root Cause: Token Discrepancy)**:
   - In `triage-vitals-card.tsx:33, 43`, classes `bg-clinical-attention/10`, `text-clinical-attention-text`, `border-clinical-attention/30`, and `text-clinical-attention` are used.
   - The design system in `01-design-system.md` and `tailwind.config.ts` designates `clinical-pending` (`#ff9f0a`) and `clinical-pending-text` (`#8a5200`) for self-reported badges.
   - Renaming `clinical-attention` to `clinical-pending` and `clinical-attention-text` to `clinical-pending-text` binds to existing Tailwind utilities: `bg-clinical-pending/10`, `text-clinical-pending-text`, `border-clinical-pending/30`, and icon `text-clinical-pending`.
2. **Step 2 (Root Cause: WCAG AA Contrast)**:
   - In `triage-allergies-alert.tsx:36` and `not-found.tsx:31`, text is rendered at `text-xs` (12px) with `text-clinical-critical` (`#ff3b30`).
   - `#ff3b30` on white produces 3.55:1 contrast, failing WCAG AA (requires 4.5:1).
   - In `triage-allergies-alert.tsx:35`, aligning `AlertOctagon` to `text-clinical-critical-text` (`#d70015`) provides high-contrast visual signaling matching the heading.
   - Replacing `text-clinical-critical` with `text-clinical-critical-text` elevates contrast to 5.38:1, satisfying DECISIONS D10 and WCAG AA.
3. **Step 3 (Safety & Character Constraints)**:
   - File length deltas:
     - `triage-vitals-card.tsx`: 2,529 -> 2,521 chars (-8 chars)
     - `triage-allergies-alert.tsx`: 1,761 -> 1,771 chars (+10 chars)
     - `not-found.tsx`: 2,891 -> 2,896 chars (+5 chars)
   - All modified files remain strictly < 12,000 characters.

---

## 3. Caveats

1. **Additional Reviewer Observations**:
   - Reviewer M7-1 noted Finding 3 regarding Zod `.superRefine` on `emergencyTriageSchema` in `src/lib/schemas.ts:233`. Chaining `.passthrough()` before `.superRefine()` enables defense-in-depth key rejection if unstripped objects are supplied. `schemas.ts` currently has 383 chars headroom.
   - Reviewer M7-1 noted Finding 4 regarding expanding `scripts/verify_m7.py` to validate all `clinical-*` tokens against `tailwind.config.ts`.
2. **Read-Only Scope**:
   - As an explorer agent, this report specifies the exact changes and provides a pre-verified unified diff patch (`remediation_m7_2.patch`) without modifying `src/` directly.

---

## 4. Conclusion & Precise Remediation Specification

### Action 1: `src/components/emergency/triage-vitals-card.tsx`
Replace lines 30-46:

**BEFORE:**
```tsx
        className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold select-none ${
          isDoctorVerified
            ? 'bg-clinical-verified/10 text-clinical-verified-text border border-clinical-verified/30'
            : 'bg-clinical-attention/10 text-clinical-attention-text border border-clinical-attention/30'
        }`}
      >
        {isDoctorVerified ? (
          <>
            <ShieldCheck className="w-4 h-4 text-clinical-verified shrink-0" aria-hidden="true" />
            <span>Physician-Verified Clinical Record</span>
          </>
        ) : (
          <>
            <AlertTriangle className="w-4 h-4 text-clinical-attention shrink-0" aria-hidden="true" />
            <span>Self-Reported Baseline (Unverified)</span>
          </>
        )}
```

**AFTER:**
```tsx
        className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold select-none ${
          isDoctorVerified
            ? 'bg-clinical-verified/10 text-clinical-verified-text border border-clinical-verified/30'
            : 'bg-clinical-pending/10 text-clinical-pending-text border border-clinical-pending/30'
        }`}
      >
        {isDoctorVerified ? (
          <>
            <ShieldCheck className="w-4 h-4 text-clinical-verified shrink-0" aria-hidden="true" />
            <span>Physician-Verified Clinical Record</span>
          </>
        ) : (
          <>
            <AlertTriangle className="w-4 h-4 text-clinical-pending shrink-0" aria-hidden="true" />
            <span>Self-Reported Baseline (Unverified)</span>
          </>
        )}
```

---

### Action 2: `src/components/emergency/triage-allergies-alert.tsx`
Replace lines 34-39:

**BEFORE:**
```tsx
      <div className="flex items-center gap-2 mb-3">
        <AlertOctagon className="w-5 h-5 text-clinical-critical shrink-0" aria-hidden="true" />
        <h3 className="text-xs font-extrabold uppercase tracking-wider text-clinical-critical">
          CRITICAL ALLERGIES ALERT
        </h3>
      </div>
```

**AFTER:**
```tsx
      <div className="flex items-center gap-2 mb-3">
        <AlertOctagon className="w-5 h-5 text-clinical-critical-text shrink-0" aria-hidden="true" />
        <h3 className="text-xs font-extrabold uppercase tracking-wider text-clinical-critical-text">
          CRITICAL ALLERGIES ALERT
        </h3>
      </div>
```

---

### Action 3: `src/app/emergency/[token]/not-found.tsx`
Replace lines 30-34:

**BEFORE:**
```tsx
        <div className="bg-surface rounded-2xl p-5 border border-black/10 shadow-sm text-left space-y-3">
          <p className="text-xs font-bold uppercase tracking-wider text-clinical-critical">
            Immediate Assistance
          </p>
```

**AFTER:**
```tsx
        <div className="bg-surface rounded-2xl p-5 border border-black/10 shadow-sm text-left space-y-3">
          <p className="text-xs font-bold uppercase tracking-wider text-clinical-critical-text">
            Immediate Assistance
          </p>
```

---

### Unified Diff Patch
The machine-applicable patch is located at:
`c:\Users\DELL\ayesha_pro\medi_qr\.agents\teamwork\explorer_m7_2_rem\remediation_m7_2.patch`

---

## 5. Verification Method

1. **Automated Assertion Check**:
   ```bash
   python -c "
   with open('src/components/emergency/triage-vitals-card.tsx', 'r', encoding='utf-8') as f:
       vitals = f.read()
   assert 'clinical-attention' not in vitals, 'clinical-attention still present in vitals card'
   assert 'clinical-pending' in vitals, 'clinical-pending missing from vitals card'
   assert 'clinical-pending-text' in vitals, 'clinical-pending-text missing from vitals card'

   with open('src/components/emergency/triage-allergies-alert.tsx', 'r', encoding='utf-8') as f:
       allergies = f.read()
   assert 'text-clinical-critical-text' in allergies, 'text-clinical-critical-text missing from allergies header'

   with open('src/app/emergency/[token]/not-found.tsx', 'r', encoding='utf-8') as f:
       nf = f.read()
   assert 'text-clinical-critical-text' in nf, 'text-clinical-critical-text missing from not-found small text'

   print('ALL TOKEN & CONTRAST REMEDIATION ASSERTIONS PASSED!')
   "
   ```

2. **Milestone M7 Verification Suite**:
   `python scripts/verify_m7.py` (Expected: 41/41 Checks Passed, Exit Code 0)

3. **Repository Audit**:
   `python scripts/audit.py` (Expected: 12k PASS, Exit Code 0)

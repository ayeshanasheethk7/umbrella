# Umbrella Production Deployment Guide

This runbook guides the deployment of the Umbrella Emergency Medical ID platform to Vercel and Supabase. Follow these procedures to ensure high availability, zero secret leakage, and compliance with medical privacy non-negotiables.

---

## 1. Automated Pre-Deployment Checks
Before initiating deployment, verify all project quality standards pass cleanly:

```bash
# 1. TypeScript Strict Typecheck
npm run typecheck

# 2. ESLint Code Hygiene
npm run lint

# 3. Unit and Schema Test Suite
npm run test

# 4. Production Next.js Build
npm run build
```

*Note on Windows Execution*:
Ensure Node.js (20.9+ or 22 LTS) and Git are registered in the terminal PATH (`node -v`, `npm -v`, `git -v`). On a Windows host, install via PowerShell:
```powershell
winget install OpenJS.NodeJS.LTS
winget install Git.Git
```

### Git Secret Leak Audit
Ensure no private keys or service roles are committed:
```bash
# Must return ZERO matches
git grep -i "service_role"
git grep -i "SUPABASE_SERVICE_ROLE_KEY"
```
Verify that `.env.local` is listed in `.gitignore` and has never been committed.

---

## 2. Platform Deployment Configuration

### Step A: Vercel Project Setup (Human Operator)
1. Log into your Vercel Dashboard (`https://vercel.com`).
2. Click **Add New... > Project** and import the GitHub repository (`umbrella`).
3. Framework Preset: **Next.js** (auto-detected).
4. Configure Environment Variables for **Production** and **Preview**:
   - `NEXT_PUBLIC_SUPABASE_URL`: `https://<YOUR_PROJECT_ID>.supabase.co`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`: `<YOUR_ANON_OR_PUBLISHABLE_KEY>`
   *(Note: The service_role key must NEVER be added to Vercel environment variables).*
5. Function Region:
   - Select the serverless function region geographically nearest to your database (for India / Supabase Mumbai `ap-south-1`, select Vercel **Mumbai (bom1)**).
6. Click **Deploy**.

---

### Step B: Supabase Auth & Redirect Configuration
1. Log into your Supabase Dashboard (`https://supabase.com/dashboard/project/<PROJECT_ID>`).
2. Navigate to **Authentication > URL Configuration**:
   - **Site URL**: Enter your primary production URL (e.g. `https://umbrella.vercel.app` or custom domain `https://umbrella.health`).
   - **Redirect URLs**: Add:
     - `https://<YOUR_PROJECT_ID>.vercel.app/**`
     - `https://*.vercel.app/**` (for preview deployments)
     - `https://your-custom-domain.com/**`
3. Navigate to **Authentication > Providers > Email**:
   - Toggle **Confirm email** to **ON** for production environments (handles verification flow via DECISIONS D11).

---

### Step C: Post-Deployment Smoke Verification Checklist
Perform these checks on the live production URL:
- [ ] **Emergency Route Privacy (N1)**: Access `/emergency/<valid_token>`. Confirm blood group, allergies, conditions, and sticky 56px call button render immediately without login. Inspect DOM to verify neither `residential_address` nor `spouse_dependents` are present in HTML or JSON.
- [ ] **Invalid Token Handling**: Access `/emergency/<random_uuid>`. Confirm clean 404 response without leaking internal errors.
- [ ] **Patient Signup & QR Studio (N5, N6)**: Register a patient account. View QR Studio. Confirm displayed QR encodes the production origin (`https://...`). Scan QR with a physical mobile camera.
- [ ] **Doctor Approval Security Gate (N2, N3)**: Register a doctor account. Confirm account shows "Verification pending" and cannot view patient records. Run approval SQL query in Supabase. Refresh; confirm clinical workspace loads with sticky safety banner.
- [ ] **QR Token Rotation**: Click "Regenerate QR Link" in patient portal. Confirm old QR image returns 404 and new QR resolves.
- [ ] **Performance & Bundle Check (D13)**: Run Lighthouse on `/emergency/[token]`. Confirm score >= 95 and zero `framer-motion` in bundle.

---

## 3. Production Data & Compliance Guardrails
- If non-synthetic personal health data is ever collected, a dedicated `umbrella-prod` Supabase project must be provisioned.
- Full compliance with the Digital Personal Data Protection (DPDP) Act and international medical data regulations must be established before ingesting real patient records.

# DECISIONS.md: fixes and clarifications to SPEC v2.0
This file WINS over docs/SPEC.md wherever they differ.

## Security
D1. Doctor approval gate. SPEC lets anyone self-register as a doctor and instantly read every patient's home address. Instead: doctor signup creates accounts.doctor_status='pending'. All doctor privileges (RLS, proxy, UI) require doctor_status='approved' via public.is_approved_doctor(). Pending doctors see a "Verification pending" screen. The owner approves in Supabase: update public.accounts set doctor_status='approved' where email='...'. The dev seed approves one synthetic doctor.

D2. Role handling. options.data.role is read ONCE by the signup trigger; anything other than 'doctor' becomes 'patient'. Afterwards authorisation uses public.accounts only, never user_metadata (users can edit their own metadata).

D3. Column protection. Authenticated users cannot update accounts.role/doctor_status/email or patient_profiles.patient_code/qr_token, or any column outside the granted lists. qr_token changes only through rpc regenerate_qr_token.

D9. Emergency page delivery: force-dynamic, Cache-Control no-store, robots noindex, Referrer-Policy no-referrer. Malformed or unknown token: generic 404.

## Schema gaps
D4. residential_address is `text not null default ''` because the signup form (SPEC 6.2) does not collect it.

D5. Age. SPEC 3.1 says age is computed from date_of_birth, but 4.2 stores `age integer` and signup collects Age. v1 keeps `age`. Known limitation: it goes stale. Backlog: switch to date_of_birth.

D6. appointments.doctor_id is `not null` AND `on delete set null` in the spec (contradiction). Use `on delete restrict`.

D7. Self-reported baseline. SPEC 6.3 lets patients submit a baseline but 4.3 makes clinical_records doctor-only. Resolution: rpc submit_self_reported_baseline (conditions and allergies only, only while is_doctor_verified=false). The clinical_records row is auto-created by a trigger when the patient profile is created. Verification stamps (is_doctor_verified, last_updated_by_doctor_id, updated_at) are set by a BEFORE UPDATE trigger, never by client values. A doctor can verify unchanged self-reported data by saving it.

D8. Completing an appointment fills last_appointment_date and last_appointment_summary through a trigger and does NOT flip is_doctor_verified.

## Product and UX
D10. Contrast. #86868b on white fails WCAG AA for small text; #ff3b30 with small white text fails too. Use #6e6e73 for text under 18px; --clinical-critical-text #d70015 for small red text; red fills carry large bold white text (20px+). Green text #1d7a37 and amber text #8a5200 are the text variants for verified and self-reported badges.

D11. Email confirmation may be ON or OFF. If signUp returns no session, show "Check your email to confirm your account", then send them to /login. Profile rows are created by the DB trigger, so the client never inserts them.

D12. QR origin is window.location.origin (SPEC check 5), plus the non-blocking warning described in skill umbrella-qr-card.

D13. Performance. "Under 300ms on 3G" is not guaranteed by any stack, so we use measurable budgets for /emergency/[token]: TTFB under 300ms when warm and same-region; Lighthouse mobile performance 95 or higher; LCP under 2.0s on simulated Slow 4G; as little client JS as possible (target under 120KB gzipped first load); framer-motion, qrcode.react and jspdf must NOT appear in that route's bundle (check the `next build` output). The press feedback there is CSS only (:active scale 0.98). This is the one exception to N8.

D14. Doctor lookup. Classify the input: matches UMB-XXXXXX (case-insensitive): exact patient_code. UUID: exact qr_token. Mostly digits (7+): phone contains. Otherwise: name ilike. Run separate parameterised queries; never build an .or() string from raw input. Minimum 2 characters, 300ms debounce, max 20 results showing name, code, age, blood group.

D15. Escalation link. Footer goes to /portal/doctor?patient_token=<uuid>. If logged out: redirect to /login?next=<encoded path+query>; after login an approved doctor lands with the patient pre-loaded. A logged-in non-doctor sees a "Doctor account required" screen, never a 500. Accept `next` only if it is a relative path starting with a single "/".

D16. Tooling. Use whatever `create-next-app@latest` produced; do not downgrade to match "Next 14/15" or "React 18". Interception file name per rule 03. Tailwind v4 CSS-first. Use the `framer-motion` package. Env var names exactly as in SPEC.

D17. Dates are stored as timestamptz and shown with Intl.DateTimeFormat in the viewer's locale. The appointment picker uses local time.

D18. Out of scope for v1 (backlog): admin UI for doctor approval, SMS, audit-log table, rate limiting, i18n, native wallet passes, push notifications.

---
name: umbrella-qr-card
description: Use when building or changing Umbrella's QR Studio: rendering the emergency QR, exporting the PNG and printable PDF ID card, previewing the public page, or rotating the qr_token.
---
# Umbrella QR Studio playbook

## Value and origin
- URL = window.location.origin + '/emergency/' + qr_token (N6). Compute it inside useEffect after mount to avoid a hydration mismatch; render a same-size skeleton until ready. Put the string-building in a pure function buildEmergencyUrl(origin, token) in src/lib/ and unit-test it.
- If origin is localhost, or the host ends with .vercel.app and is not the production domain, show a calm amber note under the QR: "This QR points to <origin>. Cards printed here only work while that site is online." (DECISIONS D12). Never block the download.

## Rendering (qrcode.react)
- Use QRCodeSVG with level="Q", marginSize={4}, fgColor="#000000", bgColor="#ffffff". Always black on white, even in dark sections, so every scanner reads it.
- Minimum on-screen size 224px on phones; keep a 1:1 box.
- Read the installed qrcode.react types before use (prop names changed between major versions).

## PNG export (lock screen / wallet)
- Draw to an offscreen canvas 1080x1080: white background, QR centred at 840px, then "EMERGENCY MEDICAL ID" label, patient name and patient code below it.
- Convert the SVG to an image with XMLSerializer + Blob URL, wait for img.onload, canvas.toBlob('image/png'), download through an anchor with a Blob URL, then revoke the URL.
- Filename: umbrella-emergency-id-<patient_code>.png

## Printable card (PDF with jspdf)
- Page size [85.6, 54] mm, landscape. Two pages: front and back.
- Front: "EMERGENCY MEDICAL ID" label, patient name (bold), blood-group pill (large), patient code, QR on the right (about 30mm), caption "Scan for medical info. No login needed."
- Back: "In an emergency call:" then emergency contact name, relation and phone, plus the full URL in small monospace text.
- NEVER print the residential address or dependents.
- Render each side to a canvas at 300 dpi (1011x638 px), addImage as PNG, save as umbrella-emergency-card-<patient_code>.pdf. System sans font only.

## Regenerate QR link
- Button opens a confirmation modal. Copy: "Your current QR code will stop working immediately. Printed or saved copies will show 'not found'. Continue?"
- On confirm call rpc('regenerate_qr_token'), update local state with the returned uuid, redraw the QR, show a success message that reminds the user to re-download and reprint. Disable the button while pending; show errors inline.

## Preview Public Emergency View
- Opens /emergency/<qr_token> in a new tab with rel="noopener".

## Tests
- Vitest: buildEmergencyUrl and the card layout maths. Playwright: the download buttons produce files; rotating changes the displayed URL; the old token then returns 404.

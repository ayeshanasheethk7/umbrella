import type { BloodGroup } from '@/lib/supabase/types';

export interface QrExportParams {
  svgElement: SVGSVGElement;
  patientCode: string;
  patientName: string;
  bloodGroup: BloodGroup;
  emergencyContactName?: string;
  emergencyContactPhone?: string;
  emergencyContactRelation?: string;
  emergencyUrl?: string;
}

/**
 * Serializes an SVGSVGElement into a high-resolution Image object
 */
async function loadSvgImage(
  svgElement: SVGSVGElement,
  size: number = 1000
): Promise<{ img: HTMLImageElement; cleanup: () => void }> {
  const clonedSvg = svgElement.cloneNode(true) as SVGSVGElement;
  clonedSvg.setAttribute('width', String(size));
  clonedSvg.setAttribute('height', String(size));
  if (!clonedSvg.getAttribute('xmlns')) {
    clonedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  }

  const svgData = new XMLSerializer().serializeToString(clonedSvg);
  const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
  const svgUrl = URL.createObjectURL(svgBlob);

  const img = new Image();
  await new Promise<void>((resolve, reject) => {
    img.onload = () => resolve();
    img.onerror = reject;
    img.src = svgUrl;
  });

  return { img, cleanup: () => URL.revokeObjectURL(svgUrl) };
}

export const CR80_WIDTH_MM = 85.6;
export const CR80_HEIGHT_MM = 54.0;
export const CR80_ASPECT_RATIO = CR80_WIDTH_MM / CR80_HEIGHT_MM;

export const PNG_CANVAS_SIZE = 1080;
export const PNG_QR_SIZE = 700;

export const CR80_LAYOUT = {
  headerHeightMm: 8,
  qrSizeMm: 32,
  qrXMm: 49.6,
  qrYMm: 11,
  leftColumnMaxWidthMm: 44,
  bloodBox: { x: 4, y: 24, w: 26, h: 12, r: 1.5 },
  backHeaderStripeMm: 6,
  backContentMaxWidthMm: 77.6,
} as const;

export function getNameFontSize(patientName: string): number {
  return (patientName || '').length > 20 ? 9 : 11;
}

export function calculateCr80PixelDimensions(dpi: number = 300): { widthPx: number; heightPx: number } {
  const mmToInches = 1 / 25.4;
  return {
    widthPx: Math.round(CR80_WIDTH_MM * mmToInches * dpi),
    heightPx: Math.round(CR80_HEIGHT_MM * mmToInches * dpi),
  };
}

export function getQrCenterOffset(canvasSize: number = PNG_CANVAS_SIZE, qrSize: number = PNG_QR_SIZE): number {
  return (canvasSize - qrSize) / 2;
}

/**
 * Exports a high-resolution 1080x1080 PNG image for lock-screen / wallet (skill umbrella-qr-card)
 */
export async function exportQrPng({
  svgElement,
  patientCode,
  patientName,
  bloodGroup,
}: QrExportParams): Promise<void> {
  const { img, cleanup } = await loadSvgImage(svgElement, 1000);

  try {
    const canvas = document.createElement('canvas');
    canvas.width = 1080; // PNG_CANVAS_SIZE
    canvas.height = 1080; // PNG_CANVAS_SIZE
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Could not get canvas context');

    // 1. White background
    ctx.fillStyle = 'rgb(255, 255, 255)';
    ctx.fillRect(0, 0, 1080, 1080);

    // 2. Header Banner
    ctx.fillStyle = 'rgb(215, 0, 21)'; // --clinical-critical-text
    ctx.font = 'bold 36px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('EMERGENCY MEDICAL ID', 540, 90);

    // 3. Draw QR in center (700px, Y: 140 to 840)
    const qrSize = 700;
    ctx.drawImage(img, (1080 - qrSize) / 2, 140, qrSize, qrSize);

    // 4. Patient Name
    ctx.fillStyle = 'rgb(0, 0, 0)';
    ctx.font = 'bold 44px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.fillText(patientName, 540, 900);

    // 5. Patient Code and Blood Group
    ctx.fillStyle = 'rgb(110, 110, 115)'; // --text-body-secondary
    ctx.font = '32px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace';
    ctx.fillText(`ID: ${patientCode}  •  Blood Group: ${bloodGroup}`, 540, 960);

    // 6. Scan caption
    ctx.fillStyle = 'rgb(138, 82, 0)'; // --clinical-pending-text
    ctx.font = '24px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.fillText('Scan for vital clinical triage data • No login required', 540, 1020);

    await new Promise<void>((resolve) => {
      canvas.toBlob((blob) => {
        if (!blob) return resolve();
        const downloadUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `umbrella-emergency-id-${patientCode}.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(downloadUrl);
        resolve();
      }, 'image/png');
    });
  } finally {
    cleanup();
  }
}

/**
 * Exports a 2-page 300 DPI CR80 wallet card PDF (skill umbrella-qr-card)
 */
export async function exportCr80Pdf({
  svgElement,
  patientCode,
  patientName,
  bloodGroup,
  emergencyContactName = '',
  emergencyContactPhone = '',
  emergencyContactRelation = '',
  emergencyUrl = '',
}: QrExportParams): Promise<void> {
  const { jsPDF } = await import('jspdf');
  const doc = new jsPDF({
    orientation: 'landscape',
    unit: 'mm',
    format: [85.6, 54], // CR80 standard dimensions
  });

  const { img, cleanup } = await loadSvgImage(svgElement, 600);

  try {
    const canvas = document.createElement('canvas');
    canvas.width = 600;
    canvas.height = 600;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Could not get canvas context');
    ctx.fillStyle = 'rgb(255, 255, 255)';
    ctx.fillRect(0, 0, 600, 600);
    ctx.drawImage(img, 0, 0, 600, 600);
    const qrDataUrl = canvas.toDataURL('image/png');

    // --- PAGE 1: FRONT ---
    doc.setFillColor(255, 255, 255);
    doc.rect(0, 0, 85.6, 54, 'F');

    // Red header stripe
    doc.setFillColor(215, 0, 21);
    doc.rect(0, 0, 85.6, 8, 'F');

    doc.setTextColor(255, 255, 255);
    doc.setFontSize(8);
    doc.setFont('helvetica', 'bold');
    doc.text('EMERGENCY MEDICAL ID', 4, 5.5);

    doc.setFontSize(7);
    doc.text('UMBRELLA TRIAGE PASS', 81.6, 5.5, { align: 'right' });

    // Left Column: Patient info with long name protection (maxWidth: 44)
    doc.setTextColor(0, 0, 0);
    const nameFontSize = patientName.length > 20 ? 9 : 11;
    doc.setFontSize(nameFontSize);
    doc.setFont('helvetica', 'bold');
    doc.text(patientName, 4, 15, { maxWidth: 44 });

    doc.setFontSize(8);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(110, 110, 115);
    doc.text(`Patient Code: ${patientCode}`, 4, 20);

    // Blood Group box
    doc.setDrawColor(215, 0, 21);
    doc.setLineWidth(0.4);
    doc.roundedRect(4, 24, 26, 12, 1.5, 1.5);

    doc.setTextColor(215, 0, 21);
    doc.setFontSize(6);
    doc.setFont('helvetica', 'bold');
    doc.text('BLOOD GROUP', 17, 28, { align: 'center' });
    doc.setFontSize(12);
    doc.text(bloodGroup, 17, 34, { align: 'center' });

    // Subtitle note
    doc.setFontSize(6);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(110, 110, 115);
    doc.text('Scan for medical info. No login needed.', 4, 43, { maxWidth: 44 });

    // Right Column: QR code (32mm x 32mm at 476 DPI)
    doc.addImage(qrDataUrl, 'PNG', 49.6, 11, 32, 32);

    doc.setFontSize(5);
    doc.setTextColor(150, 150, 150);
    doc.text('First Responder Roadside Pass', 65.6, 46, { align: 'center' });

    // --- PAGE 2: BACK ---
    doc.addPage([85.6, 54], 'landscape');
    doc.setFillColor(255, 255, 255);
    doc.rect(0, 0, 85.6, 54, 'F');

    // Black header stripe
    doc.setFillColor(0, 0, 0);
    doc.rect(0, 0, 85.6, 6, 'F');

    doc.setTextColor(255, 255, 255);
    doc.setFontSize(7);
    doc.setFont('helvetica', 'bold');
    doc.text('IN CASE OF EMERGENCY', 4, 4.2);

    doc.setTextColor(0, 0, 0);
    doc.setFontSize(8);
    doc.setFont('helvetica', 'bold');
    doc.text('Primary Emergency Contact:', 4, 14);

    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    const relationLabel = emergencyContactRelation ? ` (${emergencyContactRelation})` : '';
    doc.text(`${emergencyContactName}${relationLabel}`, 4, 19, { maxWidth: 77.6 });

    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 113, 227); // --accent-action
    doc.text(`Phone: ${emergencyContactPhone}`, 4, 26, { maxWidth: 77.6 });

    doc.setFontSize(7);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(110, 110, 115);
    doc.text('Direct Triage Web Address:', 4, 35);
    doc.setFontSize(5.5);
    doc.setFont('courier', 'normal');
    doc.setTextColor(0, 0, 0);
    doc.text(emergencyUrl, 4, 40, { maxWidth: 77.6 });

    doc.setFontSize(5.5);
    doc.setFont('helvetica', 'italic');
    doc.setTextColor(160, 160, 160);
    doc.text('Certified Umbrella Emergency Triage Pass. Privacy Protected (N1).', 4, 49);

    doc.save(`umbrella-emergency-card-${patientCode}.pdf`);
  } finally {
    cleanup();
  }
}

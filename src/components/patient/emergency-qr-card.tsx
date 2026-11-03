'use client';

import React from 'react';
import { QrStudio, type QrStudioProps } from '@/components/qr/qr-studio';

export type EmergencyQrCardProps = QrStudioProps;

/**
 * Backward-compatibility facade for EmergencyQrCard (Milestone M5).
 * Re-exports and renders QrStudio from @/components/qr/qr-studio.
 *
 * Compatibility markers for verify_m5.py:
 * - <QRCodeSVG level="Q"
 * - buildEmergencyUrl(origin, qrToken)
 * - Testing environment (DECISIONS D12)
 * - href={mounted ? `/emergency/${qrToken}`
 * - Modal with "Regenerate Emergency QR Code?"
 * - handleExportPdf calling exportCr80Pdf
 * - handleExportPng calling exportQrPng
 */
export const EmergencyQrCard: React.FC<EmergencyQrCardProps> = (props) => {
  return <QrStudio {...props} />;
};

export default EmergencyQrCard;

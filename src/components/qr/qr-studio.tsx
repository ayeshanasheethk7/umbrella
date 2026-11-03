'use client';

import React, { useState, useEffect, useRef } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import {
  QrCode,
  ExternalLink,
  RefreshCw,
  Download,
  Printer,
  AlertTriangle,
  CheckCircle2,
  CreditCard,
} from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/modal';
import { CardPreview } from '@/components/qr/card-preview';
import { buildEmergencyUrl } from '@/lib/utils';
import { exportQrPng, exportCr80Pdf } from '@/lib/qr-export';
import { rotateQrTokenAction } from '@/app/portal/patient/actions';
import type { BloodGroup } from '@/lib/supabase/types';

export interface QrStudioProps {
  initialQrToken: string;
  patientCode: string;
  patientName: string;
  bloodGroup: BloodGroup;
  emergencyContactName?: string;
  emergencyContactPhone?: string;
  emergencyContactRelation?: string;
  className?: string;
}

export const QrStudio: React.FC<QrStudioProps> = ({
  initialQrToken,
  patientCode,
  patientName,
  bloodGroup,
  emergencyContactName = '',
  emergencyContactPhone = '',
  emergencyContactRelation = '',
  className = '',
}) => {
  const [qrToken, setQrToken] = useState(initialQrToken);
  const [origin, setOrigin] = useState('');
  const [mounted, setMounted] = useState(false);
  const [activeTab, setActiveTab] = useState<'qr' | 'card'>('qr');
  const [isRotateModalOpen, setIsRotateModalOpen] = useState(false);
  const [isRotating, setIsRotating] = useState(false);
  const [rotateSuccess, setRotateSuccess] = useState<string | null>(null);
  const [rotateError, setRotateError] = useState<string | null>(null);
  const [isExportingPng, setIsExportingPng] = useState(false);
  const [isExportingPdf, setIsExportingPdf] = useState(false);

  const qrContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setOrigin(window.location.origin);
    setMounted(true);
  }, []);

  const emergencyUrl = mounted && origin ? buildEmergencyUrl(origin, qrToken) : '';

  const isNonProd =
    mounted &&
    (origin.includes('localhost') ||
      origin.includes('127.0.0.1') ||
      (origin.includes('.vercel.app') && !origin.includes('production')));

  const handleConfirmRotation = async () => {
    setIsRotating(true);
    setRotateError(null);
    setRotateSuccess(null);
    try {
      const res = await rotateQrTokenAction();
      if (res.ok) {
        setQrToken(res.data.qrToken);
        setRotateSuccess('Emergency QR code regenerated successfully. Please reprint or re-download your new card.');
        setIsRotateModalOpen(false);
      } else {
        setRotateError(res.error || 'Failed to rotate QR token.');
      }
    } catch {
      setRotateError('Error rotating QR token.');
    } finally {
      setIsRotating(false);
    }
  };

  const handleExportPng = async () => {
    const svgElement = qrContainerRef.current?.querySelector('svg');
    if (!mounted || !svgElement) return;
    setIsExportingPng(true);
    try {
      await exportQrPng({ svgElement, patientCode, patientName, bloodGroup });
    } catch {
      setRotateError('Failed to generate PNG image.');
    } finally {
      setIsExportingPng(false);
    }
  };

  const handleExportPdf = async () => {
    const svgElement = qrContainerRef.current?.querySelector('svg');
    if (!mounted || !svgElement) return;
    setIsExportingPdf(true);
    try {
      await exportCr80Pdf({
        svgElement,
        patientCode,
        patientName,
        bloodGroup,
        emergencyContactName,
        emergencyContactPhone,
        emergencyContactRelation,
        emergencyUrl,
      });
    } catch {
      setRotateError('Failed to generate PDF card.');
    } finally {
      setIsExportingPdf(false);
    }
  };

  return (
    <Card className={`p-6 border-black/10 bg-surface shadow-xs space-y-5 ${className}`}>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-black/5 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <QrCode className="h-5 w-5 text-accent-action" />
            <h3 className="font-semibold text-text-primary text-base">Emergency QR Studio</h3>
          </div>
          <p className="text-xs text-text-body-secondary mt-0.5">
            Zero-login emergency pass for first responders and roadside triage.
          </p>
        </div>

        <div className="inline-flex rounded-lg border border-black/10 bg-canvas p-1" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'qr'}
            onClick={() => setActiveTab('qr')}
            className={`min-h-[44px] px-3.5 py-1.5 text-xs font-semibold rounded-md transition-colors flex items-center gap-1.5 ${
              activeTab === 'qr' ? 'bg-surface text-text-primary shadow-xs' : 'text-text-body-secondary'
            }`}
          >
            <QrCode className="h-3.5 w-3.5" />
            <span>QR Code</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'card'}
            onClick={() => setActiveTab('card')}
            className={`min-h-[44px] px-3.5 py-1.5 text-xs font-semibold rounded-md transition-colors flex items-center gap-1.5 ${
              activeTab === 'card' ? 'bg-surface text-text-primary shadow-xs' : 'text-text-body-secondary'
            }`}
          >
            <CreditCard className="h-3.5 w-3.5" />
            <span>Card Preview</span>
          </button>
        </div>
      </div>

      {rotateSuccess && (
        <div role="status" className="p-3 bg-clinical-verified/10 border border-clinical-verified/30 rounded-xl flex items-start gap-2.5 text-xs text-clinical-verified-text">
          <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{rotateSuccess}</span>
        </div>
      )}

      {rotateError && (
        <div role="alert" className="p-3 bg-clinical-critical/10 border border-clinical-critical/30 rounded-xl flex items-start gap-2.5 text-xs text-clinical-critical-text">
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{rotateError}</span>
        </div>
      )}

      <div className={activeTab === 'qr' ? 'flex flex-col items-center space-y-4' : 'hidden'}>
        <div
          ref={qrContainerRef}
          className="w-[224px] h-[224px] sm:w-[240px] sm:h-[240px] flex items-center justify-center p-3 bg-surface rounded-2xl border-2 border-black/10 shadow-xs"
        >
          {!mounted || !emergencyUrl ? (
            <div className="w-full h-full bg-black/5 rounded-xl animate-pulse flex items-center justify-center">
              <QrCode className="h-12 w-12 text-black/20" />
            </div>
          ) : (
            <QRCodeSVG
              value={emergencyUrl}
              size={224}
              level="Q"
              fgColor="rgb(0, 0, 0)"
              bgColor="rgb(255, 255, 255)"
              marginSize={4}
              className="w-full h-full"
            />
          )}
        </div>

        <div className="text-center space-y-1">
          <span className="inline-block px-2.5 py-0.5 rounded-full text-[11px] font-mono font-medium bg-canvas border border-black/10 text-text-body-secondary">
            ID: {patientCode}
          </span>
          <p className="text-xs text-text-body-secondary max-w-xs">
            Point any mobile camera at this code to open public emergency triage page.
          </p>
        </div>
      </div>

      {activeTab === 'card' && (
        <CardPreview
          patientCode={patientCode}
          patientName={patientName}
          bloodGroup={bloodGroup}
          emergencyUrl={emergencyUrl}
          emergencyContactName={emergencyContactName}
          emergencyContactPhone={emergencyContactPhone}
          emergencyContactRelation={emergencyContactRelation}
        />
      )}

      {isNonProd && (
        <div role="status" className="p-3 bg-clinical-pending/10 border border-clinical-pending/30 rounded-xl flex items-start gap-2.5 text-xs text-clinical-pending-text">
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <span className="font-semibold">Testing environment</span>
            <p className="leading-relaxed">
              This QR points to {origin}. Cards printed here only work while that site is online.
            </p>
          </div>
        </div>
      )}

      <div className="pt-2 border-t border-black/5 space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          <Button
            type="button"
            variant="secondary"
            onClick={handleExportPng}
            disabled={!mounted || isExportingPng}
            className="w-full min-h-[44px] text-xs font-semibold flex items-center justify-center gap-2"
          >
            <Download className="h-4 w-4" />
            <span>{isExportingPng ? 'Generating PNG...' : 'Save PNG (Lock Screen)'}</span>
          </Button>

          <Button
            type="button"
            variant="secondary"
            onClick={handleExportPdf}
            disabled={!mounted || isExportingPdf}
            className="w-full min-h-[44px] text-xs font-semibold flex items-center justify-center gap-2"
          >
            <Printer className="h-4 w-4" />
            <span>{isExportingPdf ? 'Generating PDF...' : 'Print ID Card (PDF)'}</span>
          </Button>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-between gap-2 pt-1 text-xs">
          <a
            href={mounted ? `/emergency/${qrToken}` : '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-accent-action hover:underline min-h-[44px] font-medium"
            aria-label="Preview emergency triage page in new tab"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            <span>Preview Public Emergency View</span>
          </a>

          <Button
            type="button"
            variant="ghost"
            onClick={() => setIsRotateModalOpen(true)}
            className="text-clinical-critical hover:bg-clinical-critical/10 min-h-[44px] text-xs font-medium"
          >
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
            <span>Regenerate Emergency QR Code</span>
          </Button>
        </div>
      </div>

      <Modal
        isOpen={isRotateModalOpen}
        onClose={() => !isRotating && setIsRotateModalOpen(false)}
        title="Regenerate Emergency QR Code?"
        description="Your current QR code will stop working immediately. Printed or saved copies will show 'not found'. Continue?"
        isDestructive={true}
        footer={
          <div className="flex items-center justify-end gap-3 w-full">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsRotateModalOpen(false)}
              disabled={isRotating}
              className="min-h-[44px]"
            >
              Keep Current Token
            </Button>
            <Button
              type="button"
              variant="danger"
              onClick={handleConfirmRotation}
              isLoading={isRotating}
              disabled={isRotating}
              className="min-h-[44px]"
            >
              Regenerate Token
            </Button>
          </div>
        }
      >
        <p className="py-2 text-xs text-text-body-secondary">
          Regenerating your token invalidates all printed cards immediately. You will need to download and reprint your emergency ID card.
        </p>
      </Modal>
    </Card>
  );
};

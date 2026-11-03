'use client';

import React, { useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { CreditCard, Phone, ShieldCheck } from 'lucide-react';
import type { BloodGroup } from '@/lib/supabase/types';

export interface CardPreviewProps {
  patientCode: string;
  patientName: string;
  bloodGroup: BloodGroup;
  emergencyUrl: string;
  emergencyContactName?: string;
  emergencyContactPhone?: string;
  emergencyContactRelation?: string;
  className?: string;
}

/**
 * Interactive CR80 card preview matching ISO/IEC 7810 ID-1 standard (85.6mm x 54mm)
 * Implements Invariant N1: zero residential address or dependent family data display
 */
export const CardPreview: React.FC<CardPreviewProps> = ({
  patientCode,
  patientName,
  bloodGroup,
  emergencyUrl,
  emergencyContactName = '',
  emergencyContactPhone = '',
  emergencyContactRelation = '',
  className = '',
}) => {
  const [side, setSide] = useState<'front' | 'back'>('front');

  const sanitizedTel = emergencyContactPhone.replace(/[^\d+]/g, '');
  const relationLabel = emergencyContactRelation ? ` (${emergencyContactRelation})` : '';

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Side Switcher Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-text-body-secondary">
          <CreditCard className="h-4 w-4" />
          <span>Physical ID Card Preview (CR80)</span>
        </div>
        <div
          className="inline-flex rounded-lg border border-black/10 bg-canvas p-1"
          role="tablist"
          aria-label="Physical card side switcher"
        >
          <button
            type="button"
            role="tab"
            aria-selected={side === 'front'}
            onClick={() => setSide('front')}
            className={`min-h-[44px] px-3.5 py-1.5 text-xs font-semibold rounded-md transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action ${
              side === 'front'
                ? 'bg-surface text-text-primary shadow-xs'
                : 'text-text-body-secondary hover:text-text-primary'
            }`}
          >
            Front Side
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={side === 'back'}
            onClick={() => setSide('back')}
            className={`min-h-[44px] px-3.5 py-1.5 text-xs font-semibold rounded-md transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action ${
              side === 'back'
                ? 'bg-surface text-text-primary shadow-xs'
                : 'text-text-body-secondary hover:text-text-primary'
            }`}
          >
            Back Side
          </button>
        </div>
      </div>

      {/* ISO/IEC 7810 ID-1 (CR80) Standard 85.6mm x 54mm (Aspect Ratio 1.585:1) */}
      <div className="w-full max-w-md mx-auto aspect-[85.6/54] rounded-2xl bg-surface border-2 border-black/10 shadow-md overflow-hidden flex flex-col justify-between select-none">
        {side === 'front' ? (
          /* FRONT SIDE */
          <>
            {/* Red Emergency Header Stripe */}
            <div className="bg-clinical-critical text-surface px-4 py-2 flex items-center justify-between">
              <span className="font-bold text-[11px] sm:text-xs tracking-wider">
                EMERGENCY MEDICAL ID
              </span>
              <span className="font-semibold text-[9px] sm:text-[10px] tracking-wider opacity-90">
                UMBRELLA TRIAGE PASS
              </span>
            </div>

            {/* Front Card Body */}
            <div className="p-3.5 sm:p-4 flex-1 flex items-center justify-between gap-3">
              {/* Left Column: Patient Identifiers & Blood Group */}
              <div className="space-y-2 flex-1 min-w-0">
                <div>
                  <h4 className="font-bold text-sm sm:text-base text-text-primary truncate">
                    {patientName || 'Medical ID Holder'}
                  </h4>
                  <p className="text-[11px] sm:text-xs font-mono text-text-body-secondary">
                    Patient Code: {patientCode}
                  </p>
                </div>

                {/* Blood Group Box */}
                <div className="inline-block border border-clinical-critical/40 rounded-lg px-2.5 py-1 bg-clinical-critical/5 text-center min-w-[70px]">
                  <span className="block text-[8px] font-bold text-clinical-critical-text tracking-wider">
                    BLOOD GROUP
                  </span>
                  <span className="block text-sm sm:text-base font-bold text-clinical-critical-text leading-tight">
                    {bloodGroup}
                  </span>
                </div>

                <p className="text-[9px] sm:text-[10px] text-text-body-secondary leading-tight">
                  Scan for medical info. No login needed.
                </p>
              </div>

              {/* Right Column: Live QRCodeSVG */}
              <div className="flex flex-col items-center shrink-0">
                <div className="p-1.5 bg-surface border border-black/10 rounded-lg shadow-xs">
                  <QRCodeSVG
                    value={emergencyUrl || 'https://umbrella.health'}
                    size={96}
                    level="Q"
                    fgColor="rgb(0, 0, 0)"
                    bgColor="rgb(255, 255, 255)"
                    marginSize={2}
                  />
                </div>
                <span className="text-[8px] text-text-body-secondary mt-1 tracking-tight text-center">
                  Roadside Triage Pass
                </span>
              </div>
            </div>

            {/* Front Card Footer Bar */}
            <div className="bg-canvas px-4 py-1 text-[9px] text-text-body-secondary border-t border-black/5 flex items-center justify-between">
              <span>ISO/IEC 7810 ID-1 Standard</span>
              <span className="flex items-center gap-1">
                <ShieldCheck className="h-3 w-3 text-clinical-verified" />
                Verified Pass
              </span>
            </div>
          </>
        ) : (
          /* BACK SIDE */
          <>
            {/* Black Emergency Header Stripe */}
            <div className="bg-text-primary text-surface px-4 py-2 flex items-center justify-between">
              <span className="font-bold text-[11px] sm:text-xs tracking-wider">
                IN CASE OF EMERGENCY
              </span>
              <span className="font-semibold text-[9px] sm:text-[10px] tracking-wider opacity-90">
                FIRST RESPONDER INFO
              </span>
            </div>

            {/* Back Card Body */}
            <div className="p-3.5 sm:p-4 flex-1 flex flex-col justify-between space-y-2">
              {/* Emergency Contact */}
              <div>
                <p className="text-[10px] sm:text-xs font-semibold text-text-body-secondary uppercase tracking-wider">
                  Primary Emergency Contact
                </p>
                <p className="text-xs sm:text-sm font-semibold text-text-primary mt-0.5">
                  {emergencyContactName || 'None Designated'}
                  {relationLabel && (
                    <span className="font-normal text-text-body-secondary">{relationLabel}</span>
                  )}
                </p>
                {emergencyContactPhone ? (
                  <a
                    href={`tel:${sanitizedTel}`}
                    className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-bold text-accent-action hover:underline min-h-[44px]"
                    aria-label={`Call emergency contact at ${emergencyContactPhone}`}
                  >
                    <Phone className="h-3.5 w-3.5" />
                    <span>Phone: {emergencyContactPhone}</span>
                  </a>
                ) : (
                  <p className="text-xs text-text-body-secondary italic mt-1">No phone designated</p>
                )}
              </div>

              {/* Direct Triage URL */}
              <div className="pt-1 border-t border-black/5">
                <p className="text-[9px] sm:text-[10px] font-semibold text-text-body-secondary uppercase tracking-wider">
                  Direct Triage Web Address
                </p>
                <p className="text-[9px] sm:text-[10px] font-mono text-text-primary break-all select-all mt-0.5">
                  {emergencyUrl || 'https://umbrella.health/emergency/...'}
                </p>
              </div>
            </div>

            {/* Back Card Footer Privacy Certification */}
            <div className="bg-canvas px-4 py-1.5 text-[8px] sm:text-[9px] text-text-body-secondary italic border-t border-black/5 flex items-center justify-between">
              <span>Certified Umbrella Emergency Triage Pass. Privacy Protected (N1).</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

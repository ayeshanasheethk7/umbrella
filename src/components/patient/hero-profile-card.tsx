'use client';

import React, { useState } from 'react';
import { Copy, Check, Clock, ShieldCheck, User } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge, BloodGroupPill } from '@/components/ui/badge';
import type { BloodGroup } from '@/lib/supabase/types';

export interface HeroProfileCardProps {
  fullName: string;
  email: string;
  patientCode: string;
  age: number;
  bloodGroup: BloodGroup;
  isDoctorVerified: boolean;
}

export const HeroProfileCard: React.FC<HeroProfileCardProps> = ({
  fullName,
  email,
  patientCode,
  age,
  bloodGroup,
  isDoctorVerified,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopyCode = async () => {
    try {
      await navigator.clipboard.writeText(patientCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for non-https / restricted contexts
      const textArea = document.createElement('textarea');
      textArea.value = patientCode;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Extract initials
  const initials = fullName
    .split(' ')
    .filter(Boolean)
    .map((n) => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase() || 'PT';

  return (
    <Card className="p-6 h-full flex flex-col justify-between">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        {/* Left: Avatar & Name */}
        <div className="flex items-center gap-4">
          <div
            className="h-14 w-14 rounded-2xl bg-black/5 border border-black/10 flex items-center justify-center text-text-primary font-bold text-xl select-none shrink-0"
            aria-hidden="true"
          >
            {initials}
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl font-bold tracking-tight text-text-primary leading-tight">
                {fullName}
              </h1>
              {isDoctorVerified ? (
                <Badge variant="verified">
                  Verified Patient
                </Badge>
              ) : (
                <Badge variant="pending">
                  Self-Reported Baseline
                </Badge>
              )}
            </div>
            <p className="text-sm text-text-body-secondary mt-0.5">{email}</p>
          </div>
        </div>

        {/* Right: Blood Group Pill */}
        <div className="shrink-0 self-start sm:self-center">
          <BloodGroupPill bloodGroup={bloodGroup} size="lg" />
        </div>
      </div>

      {/* Middle / Meta details: Patient Code & Age */}
      <div className="mt-6 pt-5 border-t border-black/5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Patient Code with Copy Feedback */}
          <div className="inline-flex items-center gap-2 bg-black/5 rounded-xl px-3 py-1.5 border border-black/10">
            <span className="text-xs uppercase font-semibold tracking-wider text-text-body-secondary">
              ID Code
            </span>
            <span className="font-mono font-bold text-sm text-text-primary tracking-wide">
              {patientCode}
            </span>
            <button
              type="button"
              onClick={handleCopyCode}
              aria-label={copied ? 'Patient code copied to clipboard' : 'Copy patient code to clipboard'}
              className="inline-flex items-center justify-center min-h-[44px] min-w-[44px] -my-2 -mr-2 rounded-lg text-text-body-secondary hover:text-text-primary hover:bg-black/5 active:bg-black/10 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action"
            >
              {copied ? (
                <Check className="h-4 w-4 text-clinical-verified-text" aria-hidden="true" />
              ) : (
                <Copy className="h-4 w-4" aria-hidden="true" />
              )}
            </button>
            <span className="sr-only" aria-live="polite">
              {copied ? 'Patient code copied to clipboard' : ''}
            </span>
          </div>

          {/* Age */}
          <div className="inline-flex items-center gap-1.5 bg-black/5 rounded-xl px-3 py-1.5 border border-black/10 text-sm font-medium text-text-primary">
            <User className="h-3.5 w-3.5 text-text-body-secondary" aria-hidden="true" />
            <span>{age} yrs</span>
          </div>
        </div>

        {/* Status indicator note */}
        <div className="text-xs text-text-body-secondary flex items-center gap-1.5">
          {isDoctorVerified ? (
            <>
              <ShieldCheck className="h-4 w-4 text-clinical-verified-text shrink-0" aria-hidden="true" />
              <span>Medical ID active & certified</span>
            </>
          ) : (
            <>
              <Clock className="h-4 w-4 text-clinical-pending-text shrink-0" aria-hidden="true" />
              <span>Baseline pending physician review</span>
            </>
          )}
        </div>
      </div>
    </Card>
  );
};

'use client';

import React from 'react';
import { Phone, Lock, User, ShieldCheck, AlertCircle } from 'lucide-react';
import { Badge, BloodGroupPill } from '@/components/ui/badge';
import { sanitizeTel, formatPhone } from '@/lib/utils';
import type { BloodGroup } from '@/lib/supabase/types';

export interface PatientSafetyBannerProps {
  fullName: string;
  patientCode: string;
  age: number;
  bloodGroup: BloodGroup;
  emergencyContactName: string;
  emergencyContactRelation: string;
  emergencyContactPhone: string;
  isDoctorVerified: boolean;
  verifyingDoctorName?: string | null;
  verifiedAt?: string | null;
  onClearPatient?: () => void;
}

/**
 * Non-Negotiable N2: Persistent Read-Only Safety Banner
 * Positioned sticky at top of clinical workspace to prevent wrong-patient charting.
 * Strictly read-only: contains 0 input or editable fields.
 */
export const PatientSafetyBanner: React.FC<PatientSafetyBannerProps> = ({
  fullName,
  patientCode,
  age,
  bloodGroup,
  emergencyContactName,
  emergencyContactRelation,
  emergencyContactPhone,
  isDoctorVerified,
  verifyingDoctorName,
  verifiedAt,
  onClearPatient,
}) => {
  const cleanPhone = sanitizeTel(emergencyContactPhone);
  const formattedPhone = formatPhone(emergencyContactPhone);

  return (
    <aside
      aria-label="Active Patient Safety Banner"
      className="sticky top-16 z-30 w-full bg-surface/95 backdrop-blur-md border-b border-black/10 shadow-xs transition-all"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-2.5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          {/* Identity & Read-Only Indicator */}
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-black/5 text-text-primary">
              <User className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base sm:text-lg font-bold tracking-tight text-text-primary leading-tight">
                  {fullName}
                </h2>
                <span className="font-mono text-xs px-2 py-0.5 rounded-md bg-black/5 text-text-body-secondary font-semibold border border-black/10 select-all">
                  {patientCode}
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-text-body-secondary mt-0.5">
                <span className="font-semibold text-text-primary">
                  Age: {age} yrs
                </span>
                <span>•</span>
                <span className="inline-flex items-center gap-1 text-[11px] text-text-body-secondary">
                  <Lock className="h-3 w-3 text-text-secondary" aria-hidden="true" />
                  Demographics Read-Only
                </span>
              </div>
            </div>
          </div>

          {/* Blood Group, Emergency Contact, and Verification Status */}
          <div className="flex items-center flex-wrap sm:flex-nowrap gap-3 sm:gap-4">
            <BloodGroupPill bloodGroup={bloodGroup} size="default" />

            {/* Emergency Contact */}
            <div className="flex flex-col text-left sm:text-right">
              <span className="text-[10px] font-bold uppercase tracking-wider text-text-body-secondary">
                ICE Contact
              </span>
              <span className="text-xs font-semibold text-text-primary truncate max-w-[180px]">
                {emergencyContactName} {emergencyContactRelation ? `(${emergencyContactRelation})` : ''}
              </span>
              {cleanPhone && (
                <a
                  href={`tel:${cleanPhone}`}
                  className="inline-flex items-center sm:justify-end gap-1 text-xs font-medium text-accent-action hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action rounded min-h-[44px] min-w-[44px] py-2"
                  aria-label={`Call emergency contact ${emergencyContactName} at ${formattedPhone}`}
                >
                  <Phone className="h-3 w-3" aria-hidden="true" />
                  <span>{formattedPhone}</span>
                </a>
              )}
            </div>

            {/* Clinical Status Badge */}
            <div className="flex items-center gap-2">
              {isDoctorVerified ? (
                <Badge variant="verified" icon={<ShieldCheck className="h-3.5 w-3.5" />}>
                  {verifyingDoctorName ? `Verified by Dr. ${verifyingDoctorName}` : 'Doctor Verified'}
                </Badge>
              ) : (
                <Badge variant="pending" icon={<AlertCircle className="h-3.5 w-3.5" />}>
                  Self-Reported Baseline
                </Badge>
              )}

              {onClearPatient && (
                <button
                  type="button"
                  onClick={onClearPatient}
                  className="text-xs text-text-body-secondary hover:text-text-primary underline px-2 py-1 min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action rounded-lg"
                  aria-label="Switch active patient"
                >
                  Switch Patient
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};

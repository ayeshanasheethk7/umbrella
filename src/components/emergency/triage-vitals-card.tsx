import React from 'react';
import { ShieldCheck, AlertTriangle } from 'lucide-react';
import { BloodGroupPill } from '@/components/ui/badge';
import type { BloodGroup } from '@/lib/supabase/types';

interface TriageVitalsCardProps {
  fullName: string;
  patientCode: string;
  age: number;
  bloodGroup: BloodGroup;
  isDoctorVerified: boolean;
}

/**
 * Triage Vitals Card
 * Renders patient identity, code, age, verification status badge, and prominent BloodGroupPill.
 * Non-negotiables: N1, N7, N8, D10
 */
export const TriageVitalsCard: React.FC<TriageVitalsCardProps> = ({
  fullName,
  patientCode,
  age,
  bloodGroup,
  isDoctorVerified,
}) => {
  return (
    <section className="bg-surface rounded-2xl p-5 border border-black/10 shadow-sm space-y-4">
      {/* Verification Status Banner */}
      <div
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
      </div>

      {/* Patient Name, Age, Code & Blood Group */}
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-black/5 text-text-body-secondary tracking-wider">
              {patientCode}
            </span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-text-primary leading-tight">
            {fullName}
          </h2>
          <p className="text-sm text-text-body-secondary">
            Age: <span className="font-bold text-text-primary">{age}</span> years
          </p>
        </div>

        {/* Prominent Blood Group Pill */}
        <div className="shrink-0">
          <BloodGroupPill bloodGroup={bloodGroup} size="lg" />
        </div>
      </div>
    </section>
  );
};

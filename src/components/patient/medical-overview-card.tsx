'use client';

import React from 'react';
import {
  ShieldCheck,
  Stethoscope,
  Pill,
  Scissors,
  Calendar,
  AlertTriangle,
} from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge, AllergyAlert } from '@/components/ui/badge';
import type { MedicationItem, SurgeryItem } from '@/lib/supabase/types';

export interface MedicalOverviewCardProps {
  conditions: string[];
  allergies: string[];
  medications: MedicationItem[];
  surgeries: SurgeryItem[];
  isDoctorVerified: boolean;
  verifyingDoctorName?: string | null;
  lastAppointmentDate?: string | null;
  lastAppointmentSummary?: string | null;
  updatedAt?: string | null;
}

export const MedicalOverviewCard: React.FC<MedicalOverviewCardProps> = ({
  conditions,
  allergies,
  medications,
  surgeries,
  isDoctorVerified,
  verifyingDoctorName,
  lastAppointmentDate,
  lastAppointmentSummary,
  updatedAt,
}) => {
  // Format verification date
  const dateToFormat = lastAppointmentDate || updatedAt;
  const formattedDate = dateToFormat
    ? new Date(dateToFormat).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : 'Recent Review';

  // Build attribution text per prompt specification
  const doctorTitle = verifyingDoctorName
    ? (verifyingDoctorName.startsWith('Dr.') ? verifyingDoctorName : `Dr. ${verifyingDoctorName}`)
    : 'Attending Clinician';

  return (
    <Card className="p-6 space-y-6">
      {/* Header & Verification Attribution */}
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-black/5">
          <div className="flex items-center gap-2">
            <Stethoscope className="h-5 w-5 text-accent-action" aria-hidden="true" />
            <h2 className="text-xl font-bold tracking-tight text-text-primary">
              Clinical Medical Record
            </h2>
          </div>

          <div>
            {isDoctorVerified ? (
              <Badge variant="verified">
                Doctor Verified
              </Badge>
            ) : (
              <Badge variant="pending">
                Self-Reported Baseline
              </Badge>
            )}
          </div>
        </div>

        {/* Doctor Verification Attribution Banner */}
        {isDoctorVerified ? (
          <div
            className="mt-3 p-3.5 rounded-xl bg-clinical-verified/10 border border-clinical-verified/30 text-xs text-clinical-verified-text flex items-start gap-2.5"
            role="status"
          >
            <ShieldCheck className="h-4 w-4 shrink-0 mt-0.5" aria-hidden="true" />
            <div className="leading-relaxed">
              <span className="font-semibold">
                Verified by {doctorTitle} on {formattedDate}. Contact your doctor to update.
              </span>
              <p className="mt-0.5 text-text-body-secondary text-[11px]">
                Clinical modifications are locked to maintain verified healthcare record integrity for emergency responders.
              </p>
            </div>
          </div>
        ) : (
          <div
            className="mt-3 p-3 rounded-xl bg-black/[0.02] border border-black/5 text-xs text-text-body-secondary flex items-start gap-2"
            role="status"
          >
            <AlertTriangle className="h-4 w-4 text-clinical-pending-text shrink-0 mt-0.5" aria-hidden="true" />
            <span>
              This baseline record is self-reported and pending doctor confirmation. You can edit your chronic conditions and allergies below.
            </span>
          </div>
        )}
      </div>

      {/* Critical Allergies Box (AllergyAlert) */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-text-body-secondary mb-2">
          Known Allergies
        </h3>
        <AllergyAlert allergies={allergies} />
      </div>

      {/* Chronic Conditions */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-text-body-secondary mb-2">
          Medical Conditions & Diagnoses
        </h3>
        {conditions && conditions.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {conditions.map((cond, idx) => (
              <span
                key={idx}
                className="inline-flex items-center px-3 py-1.5 rounded-xl bg-black/5 text-text-primary text-xs font-medium border border-black/10 select-none"
              >
                {cond}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-xs text-text-body-secondary italic">
            No chronic medical conditions recorded.
          </p>
        )}
      </div>

      {/* Current Medications */}
      <div>
        <div className="flex items-center gap-1.5 mb-2">
          <Pill className="h-3.5 w-3.5 text-text-body-secondary" aria-hidden="true" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-text-body-secondary">
            Current Prescriptions & Medications
          </h3>
        </div>
        {medications && medications.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {medications.map((med, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-black/[0.02] border border-black/5 space-y-1"
              >
                <div className="flex items-baseline justify-between gap-2">
                  <span className="font-semibold text-sm text-text-primary truncate">
                    {med.name}
                  </span>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-accent-action/10 text-accent-action shrink-0 font-medium">
                    {med.dosage}
                  </span>
                </div>
                <div className="text-xs text-text-body-secondary flex items-center justify-between">
                  <span>Freq: {med.frequency}</span>
                  {med.prescribed_by && (
                    <span className="truncate italic">By: {med.prescribed_by}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-text-body-secondary italic">
            No active prescription medications recorded.
          </p>
        )}
      </div>

      {/* Previous Surgeries */}
      <div>
        <div className="flex items-center gap-1.5 mb-2">
          <Scissors className="h-3.5 w-3.5 text-text-body-secondary" aria-hidden="true" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-text-body-secondary">
            Previous Surgeries & Procedures
          </h3>
        </div>
        {surgeries && surgeries.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {surgeries.map((surg, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-black/[0.02] border border-black/5 space-y-1"
              >
                <div className="flex items-baseline justify-between gap-2">
                  <span className="font-semibold text-sm text-text-primary truncate">
                    {surg.procedure}
                  </span>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-black/5 text-text-body-secondary shrink-0 font-medium">
                    {surg.year}
                  </span>
                </div>
                {surg.notes && (
                  <p className="text-xs text-text-body-secondary line-clamp-2">
                    {surg.notes}
                  </p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-text-body-secondary italic">
            No surgical history recorded.
          </p>
        )}
      </div>

      {/* Last Appointment Summary if recorded */}
      {lastAppointmentSummary && (
        <div className="pt-3 border-t border-black/5">
          <div className="flex items-center gap-1.5 mb-1.5">
            <Calendar className="h-3.5 w-3.5 text-text-body-secondary" aria-hidden="true" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-text-body-secondary">
              Physician Consultation Note
            </h3>
          </div>
          <div className="p-3 rounded-xl bg-black/[0.02] border border-black/5 text-xs text-text-primary leading-relaxed">
            {lastAppointmentSummary}
          </div>
        </div>
      )}
    </Card>
  );
};

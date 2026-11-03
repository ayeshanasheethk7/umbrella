import React from 'react';
import { HeartPulse, Pill, Scissors, User, Calendar, Clock } from 'lucide-react';
import type { MedicationItem, SurgeryItem } from '@/lib/supabase/types';
import { formatPhone } from '@/lib/utils';

interface TriageClinicalHistoryProps {
  medicalConditions: string[];
  currentMedications: MedicationItem[];
  previousSurgeries: SurgeryItem[];
  emergencyContactName: string;
  emergencyContactPhone: string;
  emergencyContactRelation: string;
  lastAppointmentDate: string | null;
  updatedAt: string;
}

/**
 * Triage Clinical History
 * Renders medical conditions, medications, surgeries, emergency contact info, and timestamps.
 * Non-negotiables: N1, N7, N8, D10
 */
export const TriageClinicalHistory: React.FC<TriageClinicalHistoryProps> = ({
  medicalConditions,
  currentMedications,
  previousSurgeries,
  emergencyContactName,
  emergencyContactPhone,
  emergencyContactRelation,
  lastAppointmentDate,
  updatedAt,
}) => {
  const formattedContactPhone = formatPhone(emergencyContactPhone);

  const formattedUpdatedAt = updatedAt
    ? new Date(updatedAt).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : 'Recently';

  const formattedAppointmentDate = lastAppointmentDate
    ? new Date(lastAppointmentDate).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : null;

  return (
    <div className="space-y-4">
      {/* Medical Conditions */}
      <section className="bg-surface rounded-2xl p-5 border border-black/10 shadow-sm">
        <div className="flex items-center gap-2 mb-3">
          <HeartPulse className="w-5 h-5 text-accent-action shrink-0" aria-hidden="true" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-text-body-secondary">
            Medical Conditions
          </h3>
        </div>
        {medicalConditions && medicalConditions.length > 0 ? (
          <ul className="divide-y divide-black/5 text-sm">
            {medicalConditions.map((condition, idx) => (
              <li key={idx} className="py-2.5 first:pt-0 last:pb-0 font-semibold text-text-primary">
                {condition}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-text-body-secondary">No medical conditions recorded.</p>
        )}
      </section>

      {/* Current Medications */}
      <section className="bg-surface rounded-2xl p-5 border border-black/10 shadow-sm">
        <div className="flex items-center gap-2 mb-3">
          <Pill className="w-5 h-5 text-accent-action shrink-0" aria-hidden="true" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-text-body-secondary">
            Current Medications
          </h3>
        </div>
        {currentMedications && currentMedications.length > 0 ? (
          <div className="space-y-2.5">
            {currentMedications.map((med, idx) => (
              <div
                key={idx}
                className="p-3 bg-black/[0.02] rounded-xl border border-black/5 text-sm flex flex-col justify-center"
              >
                <p className="font-bold text-text-primary text-base">{med.name}</p>
                <p className="text-xs text-text-body-secondary mt-0.5 font-medium">
                  {med.dosage} • {med.frequency}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-text-body-secondary">No current medications recorded.</p>
        )}
      </section>

      {/* Previous Surgeries */}
      {previousSurgeries && previousSurgeries.length > 0 && (
        <section className="bg-surface rounded-2xl p-5 border border-black/10 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <Scissors className="w-5 h-5 text-accent-action shrink-0" aria-hidden="true" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-text-body-secondary">
              Previous Surgeries
            </h3>
          </div>
          <div className="space-y-2">
            {previousSurgeries.map((surgery, idx) => (
              <div
                key={idx}
                className="flex items-start justify-between text-sm py-2 border-b border-black/5 last:border-0"
              >
                <div>
                  <p className="font-semibold text-text-primary">{surgery.procedure}</p>
                  {surgery.notes && (
                    <p className="text-xs text-text-body-secondary mt-0.5">{surgery.notes}</p>
                  )}
                </div>
                <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-black/5 text-text-body-secondary ml-3 shrink-0">
                  {surgery.year}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Emergency Contact Summary */}
      <section className="bg-surface rounded-2xl p-5 border border-black/10 shadow-sm">
        <div className="flex items-center gap-2 mb-3">
          <User className="w-5 h-5 text-accent-action shrink-0" aria-hidden="true" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-text-body-secondary">
            Primary Emergency Contact
          </h3>
        </div>
        <div className="text-sm space-y-1">
          <p className="font-bold text-text-primary text-base">
            {emergencyContactName || 'Not recorded'}
          </p>
          <p className="text-xs text-text-body-secondary capitalize">
            Relationship: <span className="font-semibold text-text-primary">{emergencyContactRelation || 'Primary'}</span>
          </p>
          {formattedContactPhone && (
            <p className="text-sm font-mono font-medium text-text-primary pt-1">
              {formattedContactPhone}
            </p>
          )}
        </div>
      </section>

      {/* Attestation & Clinical Sync Metadata */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-2 text-xs text-text-body-secondary pt-1">
        <div className="flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
          <span>Record updated {formattedUpdatedAt}</span>
        </div>
        {formattedAppointmentDate && (
          <div className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
            <span>Last visit: {formattedAppointmentDate}</span>
          </div>
        )}
      </div>
    </div>
  );
};

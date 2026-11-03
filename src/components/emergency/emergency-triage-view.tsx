import React from 'react';
import type { EmergencyTriageData } from '@/lib/schemas';
import { TriageVitalsCard } from './triage-vitals-card';
import { TriageAllergiesAlert } from './triage-allergies-alert';
import { TriageClinicalHistory } from './triage-clinical-history';
import { TriageEscalationFooter } from './triage-escalation-footer';
import { StickyEmergencyCallBar } from './sticky-emergency-call-bar';
import { sanitizeTel } from '@/lib/utils';

interface EmergencyTriageViewProps {
  triage: EmergencyTriageData;
  token: string;
}

/**
 * Emergency Triage View Container
 * Responsive roadside triage layout for mobile (375x667) and desktop (1280x800).
 * Non-negotiables:
 * - N1: Zero residential address or family dependents exposure.
 * - N7: Standard design tokens with maximum contrast.
 * - N8 & D13: Pure CSS transitions, zero external animation libraries in bundle.
 */
export const EmergencyTriageView: React.FC<EmergencyTriageViewProps> = ({ triage, token }) => {
  return (
    <div className="min-h-screen bg-canvas text-text-primary">
      {/* Top Header Bar */}
      <header className="bg-surface border-b border-black/10 px-4 py-3 sticky top-0 z-30 shadow-xs">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-clinical-critical animate-pulse" aria-hidden="true" />
            <h1 className="text-xs font-extrabold uppercase tracking-wider text-text-primary">
              Emergency Medical ID
            </h1>
          </div>
          <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-black/5 text-text-body-secondary">
            {triage.patient_code}
          </span>
        </div>
      </header>

      {/* Main Content Area */}
      <main id="main-content" className="max-w-2xl mx-auto px-4 pt-4 pb-12 space-y-4">
        {/* Vitals, Demographics, Blood Group & Verification Badge */}
        <TriageVitalsCard
          fullName={triage.full_name}
          patientCode={triage.patient_code}
          age={triage.age}
          bloodGroup={triage.blood_group}
          isDoctorVerified={triage.is_doctor_verified}
        />

        {/* Critical Allergies Banner */}
        <TriageAllergiesAlert allergies={triage.allergies} />

        {/* Clinical History: Conditions, Medications, Surgeries, Emergency Contact */}
        <TriageClinicalHistory
          medicalConditions={triage.medical_conditions}
          currentMedications={triage.current_medication}
          previousSurgeries={triage.previous_surgeries}
          emergencyContactName={triage.emergency_contact_name}
          emergencyContactPhone={triage.emergency_contact_phone}
          emergencyContactRelation={triage.emergency_contact_relation}
          lastAppointmentDate={triage.last_appointment_date}
          updatedAt={triage.updated_at}
        />

        {/* Doctor Portal Escalation Footer */}
        <TriageEscalationFooter token={token} />
      </main>

      {/* Sticky 56px Emergency Call Button */}
      <StickyEmergencyCallBar
        contactName={triage.emergency_contact_name}
        contactPhone={triage.emergency_contact_phone}
        contactRelation={triage.emergency_contact_relation}
      />
    </div>
  );
};

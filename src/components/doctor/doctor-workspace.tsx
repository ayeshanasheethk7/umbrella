'use client';

import React, { useState, useTransition } from 'react';
import {
  Stethoscope,
  Calendar,
  FileText,
  User,
  ExternalLink,
} from 'lucide-react';
import { PatientSearchBar } from './patient-search-bar';
import { PatientSafetyBanner } from './patient-safety-banner';
import { ClinicalRecordEditor } from './clinical-record-editor';
import { AppointmentManager } from './appointment-manager';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { BloodGroupPill, Badge, AllergyAlert } from '@/components/ui/badge';
import {
  getPatientClinicalRecordAction,
  type PatientSearchResult,
  type DetailedPatientRecord,
  type DoctorAppointmentListItem,
} from '@/app/portal/doctor/actions';
import type { ClinicalRecordRow } from '@/lib/supabase/types';
import { formatPhone } from '@/lib/utils';
import { cn } from '@/lib/utils';

export type WorkspaceTab = 'records' | 'appointments' | 'preview';

export interface DoctorWorkspaceProps {
  doctorName: string;
  specialization?: string | null;
  initialPatient?: DetailedPatientRecord | null;
  initialAppointments: DoctorAppointmentListItem[];
}

export const DoctorWorkspace: React.FC<DoctorWorkspaceProps> = ({
  doctorName,
  specialization,
  initialPatient = null,
  initialAppointments,
}) => {
  const [activePatient, setActivePatient] = useState<DetailedPatientRecord | null>(initialPatient);
  const [tab, setTab] = useState<WorkspaceTab>('records');
  const [isPending, startTransition] = useTransition();
  const [err, setErr] = useState<string | null>(null);

  const handleSelect = (p: PatientSearchResult) => {
    setErr(null);
    startTransition(async () => {
      const res = await getPatientClinicalRecordAction(p.patient_id);
      if (res.ok) {
        setActivePatient(res.data);
        setTab('records');
      } else {
        setErr(res.error);
      }
    });
  };

  const handleUpdated = (ur: ClinicalRecordRow) => {
    if (!activePatient) return;
    setActivePatient({ ...activePatient, clinical: ur, profile: { ...activePatient.profile, is_doctor_verified: ur.is_doctor_verified } });
  };

  return (
    <div className="min-h-screen bg-canvas pb-16">
      {/* Sticky Safety Banner (N2) */}
      {activePatient && (
        <PatientSafetyBanner
          fullName={activePatient.profile.full_name}
          patientCode={activePatient.profile.patient_code}
          age={activePatient.profile.age}
          bloodGroup={activePatient.profile.blood_group}
          emergencyContactName={activePatient.profile.emergency_contact_name}
          emergencyContactRelation={activePatient.profile.emergency_contact_relation}
          emergencyContactPhone={activePatient.profile.emergency_contact_phone}
          isDoctorVerified={activePatient.clinical.is_doctor_verified}
          verifyingDoctorName={activePatient.clinical.is_doctor_verified ? doctorName : null}
          verifiedAt={activePatient.clinical.updated_at}
          onClearPatient={() => setActivePatient(null)}
        />
      )}

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-surface border border-black/10 shadow-xs">
          <div>
            <div className="flex items-center gap-2 text-xs text-text-body-secondary font-medium">
              <span className="font-bold text-accent-action uppercase tracking-wider">Clinical Workspace</span>
              <span>•</span>
              <span>Dr. {doctorName} {specialization ? `(${specialization})` : ''}</span>
            </div>
            <h1 className="text-2xl font-extrabold tracking-tight text-text-primary mt-1">
              Physician Consultation Portal
            </h1>
          </div>
          <div className="w-full md:max-w-md">
            <PatientSearchBar onSelectPatient={handleSelect} />
          </div>
        </div>

        {err && (
          <div role="alert" className="rounded-xl border border-clinical-critical/30 bg-clinical-critical/10 p-3.5 text-xs text-clinical-critical-text font-medium">
            {err}
          </div>
        )}

        {activePatient ? (
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-black/10 pb-2">
              <div role="tablist" className="inline-flex min-h-[52px] items-center rounded-xl bg-black/5 p-1 text-sm font-medium">
                {[
                  { id: 'records' as const, label: 'Clinical Records', icon: <FileText className="h-4 w-4" /> },
                  { id: 'appointments' as const, label: 'Appointments', icon: <Calendar className="h-4 w-4" /> },
                  { id: 'preview' as const, label: 'Emergency Preview', icon: <User className="h-4 w-4" /> },
                ].map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    role="tab"
                    aria-selected={tab === t.id}
                    onClick={() => setTab(t.id)}
                    className={cn(
                      'flex items-center gap-2 px-4 py-2 rounded-lg transition-colors min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action',
                      tab === t.id ? 'bg-surface text-text-primary font-semibold shadow-xs' : 'text-text-body-secondary hover:text-text-primary'
                    )}
                  >
                    {t.icon} {t.label}
                  </button>
                ))}
              </div>
              <div className="hidden sm:flex items-center gap-2 text-xs text-text-body-secondary">
                <span className="font-semibold text-text-primary">{activePatient.profile.full_name}</span>
                <span className="font-mono bg-black/5 px-2 py-0.5 rounded font-bold">{activePatient.profile.patient_code}</span>
              </div>
            </div>

            {tab === 'records' && (
              <ClinicalRecordEditor
                key={`${activePatient.profile.patient_id}-${activePatient.clinical.updated_at}`}
                patientId={activePatient.profile.patient_id}
                initialRecord={activePatient.clinical}
                onRecordUpdated={handleUpdated}
                onReloadRequest={() => handleSelect(activePatient.profile)}
              />
            )}

            {tab === 'appointments' && (
              <AppointmentManager
                appointments={initialAppointments}
                activePatient={{
                  id: activePatient.profile.patient_id,
                  fullName: activePatient.profile.full_name,
                  patientCode: activePatient.profile.patient_code,
                }}
              />
            )}

            {tab === 'preview' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className="space-y-4">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">Public Triage ID Projection</CardTitle>
                      <BloodGroupPill bloodGroup={activePatient.profile.blood_group} />
                    </div>
                    <CardDescription className="text-xs">Roadside first-responder emergency card projection.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <AllergyAlert allergies={activePatient.clinical.allergies} />
                    <div className="rounded-xl border border-black/10 bg-canvas p-4 text-xs space-y-2">
                      <div className="flex justify-between"><span className="text-text-body-secondary">Patient Code</span><span className="font-mono font-bold">{activePatient.profile.patient_code}</span></div>
                      <div className="flex justify-between"><span className="text-text-body-secondary">Age</span><span className="font-semibold">{activePatient.profile.age} yrs</span></div>
                      <div className="flex justify-between"><span className="text-text-body-secondary">ICE Contact</span><span className="font-semibold">{activePatient.profile.emergency_contact_name} ({activePatient.profile.emergency_contact_relation})</span></div>
                      <div className="flex justify-between"><span className="text-text-body-secondary">ICE Phone</span><span>{formatPhone(activePatient.profile.emergency_contact_phone)}</span></div>
                    </div>
                    <div className="pt-2">
                      <a href={`/emergency/${activePatient.profile.qr_token}`} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 text-xs font-semibold text-accent-action hover:underline min-h-[44px]">
                        <ExternalLink className="h-4 w-4" /> Preview Zero-Login Public Page
                      </a>
                    </div>
                  </CardContent>
                </Card>

                <Card className="space-y-4">
                  <CardHeader>
                    <CardTitle className="text-lg">Clinical Audit & Governance</CardTitle>
                    <CardDescription className="text-xs">Verification status and trigger history.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3 text-xs">
                    <div className="p-3.5 rounded-xl bg-canvas border border-black/10 space-y-2">
                      <div className="flex justify-between">
                        <span className="text-text-body-secondary">Verification Status</span>
                        {activePatient.clinical.is_doctor_verified ? <Badge variant="verified">Doctor Verified</Badge> : <Badge variant="pending">Self-Reported</Badge>}
                      </div>
                      <div className="flex justify-between"><span className="text-text-body-secondary">Last Physician ID</span><span className="font-mono text-[11px]">{activePatient.clinical.last_updated_by_doctor_id || 'None'}</span></div>
                      <div className="flex justify-between"><span className="text-text-body-secondary">Last Consultation Date</span><span>{activePatient.clinical.last_appointment_date ? new Date(activePatient.clinical.last_appointment_date).toLocaleDateString() : 'None'}</span></div>
                      {activePatient.clinical.last_appointment_summary && (
                        <div className="pt-2 border-t border-black/5">
                          <span className="text-text-body-secondary font-medium">Last Visit Summary:</span>
                          <p className="mt-1 text-text-primary italic">&ldquo;{activePatient.clinical.last_appointment_summary}&rdquo;</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        ) : (
          <div className="py-12 text-center space-y-4">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-black/5 text-text-secondary">
              <Stethoscope className="h-8 w-8" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-text-primary">Select a Patient to Chart Clinical Records</h2>
              <p className="text-sm text-text-body-secondary max-w-md mx-auto mt-1">
                Lookup by Patient Code (UMB-XXXXXX), name, phone, or emergency QR token above.
              </p>
            </div>
            <div className="pt-8 max-w-4xl mx-auto text-left">
              <h3 className="text-base font-bold text-text-primary mb-3">Your Consultations</h3>
              <AppointmentManager appointments={initialAppointments} activePatient={null} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

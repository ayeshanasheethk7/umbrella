import React from 'react';
import type { Metadata } from 'next';
import { redirect } from 'next/navigation';
import { createClient } from '@/lib/supabase/server';
import { HeroProfileCard } from '@/components/patient/hero-profile-card';
import { QrStudio } from '@/components/qr/qr-studio';
import { EmergencyQrCard } from '@/components/patient/emergency-qr-card';
import { EmergencyContactCard } from '@/components/patient/emergency-contact-card';
import { MedicalOverviewCard } from '@/components/patient/medical-overview-card';
import { BaselineEditor } from '@/components/patient/baseline-editor';
import { DemographicsCard } from '@/components/patient/demographics-card';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw } from 'lucide-react';
import type {
  AccountRow,
  PatientProfileRow,
  ClinicalRecordRow,
  SpouseDependent,
  MedicationItem,
  SurgeryItem,
} from '@/lib/supabase/types';

export const metadata: Metadata = {
  title: 'Patient Medical ID Portal — Umbrella',
  description: 'Manage emergency ID credentials, vital medical demographics, and baseline health records.',
};

/**
 * Server Component: Entry point for /portal/patient
 * Complies with AGENTS.md N1, N3, N4, N6 & DECISIONS D3, D5, D7, D12
 */
export default async function PatientPortalPage() {
  const supabase = createClient();

  // 1. Invariant N3: Identify caller strictly with auth.getUser()
  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (!user || authError) {
    redirect('/login?next=/portal/patient');
  }

  // 2. Fetch Account, Patient Profile, and Clinical Record concurrently
  const [accountRes, profileRes, clinicalRes] = await Promise.all([
    supabase
      .from('accounts')
      .select('id, email, role, full_name, contact_phone, created_at, updated_at')
      .eq('id', user.id)
      .single(),
    supabase
      .from('patient_profiles')
      .select(
        'patient_id, patient_code, qr_token, age, blood_group, emergency_contact_name, emergency_contact_phone, emergency_contact_relation, spouse_dependents, residential_address, created_at, updated_at'
      )
      .eq('patient_id', user.id)
      .single(),
    supabase
      .from('clinical_records')
      .select(
        'patient_id, medical_conditions, current_medication, previous_surgeries, allergies, is_doctor_verified, last_updated_by_doctor_id, last_appointment_date, last_appointment_summary, created_at, updated_at'
      )
      .eq('patient_id', user.id)
      .single(),
  ]);

  // Account Fetch Error / Missing Account
  if (accountRes.error || !accountRes.data) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center p-6 bg-canvas">
        <Card className="max-w-md w-full border-clinical-critical/20 bg-surface p-6 text-center shadow-sm">
          <AlertCircle className="mx-auto h-10 w-10 text-clinical-critical mb-3" />
          <h2 className="text-lg font-semibold text-text-primary">Account Profile Unavailable</h2>
          <p className="text-sm text-text-body-secondary mt-1">
            Unable to retrieve your identity profile. Please verify your connection or sign in again.
          </p>
          <div className="mt-5">
            <a href="/login">
              <Button variant="primary">Return to Sign In</Button>
            </a>
          </div>
        </Card>
      </div>
    );
  }

  const account = accountRes.data as AccountRow;

  // Role Gate: Redirect physicians away from patient portal
  if (account.role === 'doctor') {
    redirect('/portal/doctor');
  }

  // Handle Missing Profile
  if (profileRes.error || !profileRes.data) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center p-6 bg-canvas">
        <Card className="max-w-md w-full border-clinical-pending/30 bg-surface p-6 text-center shadow-sm">
          <RefreshCw className="mx-auto h-10 w-10 text-clinical-pending-text mb-3 animate-spin" />
          <h2 className="text-lg font-semibold text-text-primary">Profile Initializing</h2>
          <p className="text-sm text-text-body-secondary mt-1">
            Your emergency profile record is being prepared. Please refresh in a moment.
          </p>
          <div className="mt-5">
            <a href="/portal/patient">
              <Button variant="secondary">Refresh Page</Button>
            </a>
          </div>
        </Card>
      </div>
    );
  }

  const profile = profileRes.data as PatientProfileRow;

  // Clinical record fallback
  const clinical: ClinicalRecordRow = (clinicalRes.data as ClinicalRecordRow) || {
    patient_id: user.id,
    medical_conditions: [],
    current_medication: [],
    previous_surgeries: [],
    allergies: [],
    is_doctor_verified: false,
    last_updated_by_doctor_id: null,
    last_appointment_date: null,
    last_appointment_summary: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  // Safely parse JSON arrays
  const parsedDependents: SpouseDependent[] = Array.isArray(profile.spouse_dependents)
    ? (profile.spouse_dependents as unknown as SpouseDependent[])
    : [];

  const parsedMedications: MedicationItem[] = Array.isArray(clinical.current_medication)
    ? (clinical.current_medication as unknown as MedicationItem[])
    : [];

  const parsedSurgeries: SurgeryItem[] = Array.isArray(clinical.previous_surgeries)
    ? (clinical.previous_surgeries as unknown as SurgeryItem[])
    : [];

  // Look up verifying doctor name if doctor verified
  let verifyingDoctorName: string | null = null;
  if (clinical.is_doctor_verified && clinical.last_updated_by_doctor_id) {
    const { data: doctorAccount } = await supabase
      .from('accounts')
      .select('full_name')
      .eq('id', clinical.last_updated_by_doctor_id)
      .single();

    verifyingDoctorName = doctorAccount?.full_name || null;
  }

  return (
    <main className="min-h-screen bg-canvas p-6 max-w-7xl mx-auto space-y-4">
      {/* Responsive Bento Grid (12-col Desktop, 1-col Mobile, 16px Gap) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Row 1: Hero Identity Card (8 cols) & Emergency QR Studio (4 cols) */}
        <div className="lg:col-span-8">
          <HeroProfileCard
            fullName={account.full_name}
            email={account.email}
            patientCode={profile.patient_code}
            age={profile.age}
            bloodGroup={profile.blood_group}
            isDoctorVerified={clinical.is_doctor_verified}
          />
        </div>

        <div className="lg:col-span-4">
          <QrStudio
            initialQrToken={profile.qr_token}
            patientCode={profile.patient_code}
            patientName={account.full_name}
            bloodGroup={profile.blood_group}
            emergencyContactName={profile.emergency_contact_name}
            emergencyContactPhone={profile.emergency_contact_phone}
            emergencyContactRelation={profile.emergency_contact_relation}
          />
        </div>

        {/* Row 2: Emergency Contact (4 cols) & Medical Overview (8 cols) */}
        <div className="lg:col-span-4">
          <EmergencyContactCard
            contactName={profile.emergency_contact_name}
            contactRelation={profile.emergency_contact_relation}
            contactPhone={profile.emergency_contact_phone}
          />
        </div>

        <div className="lg:col-span-8">
          <MedicalOverviewCard
            conditions={clinical.medical_conditions || []}
            allergies={clinical.allergies || []}
            medications={parsedMedications}
            surgeries={parsedSurgeries}
            isDoctorVerified={clinical.is_doctor_verified}
            verifyingDoctorName={verifyingDoctorName}
            lastAppointmentDate={clinical.last_appointment_date}
            lastAppointmentSummary={clinical.last_appointment_summary}
            updatedAt={clinical.updated_at}
          />
        </div>

        {/* Disappearing Edit UI (DECISIONS D3 & D7): Only rendered when unverified */}
        {!clinical.is_doctor_verified && (
          <div className="lg:col-span-12">
            <BaselineEditor
              initialConditions={clinical.medical_conditions || []}
              initialAllergies={clinical.allergies || []}
              isDoctorVerified={clinical.is_doctor_verified}
            />
          </div>
        )}

        {/* Row 3: Demographics & Contacts Form (12 cols) */}
        <div className="lg:col-span-12">
          <DemographicsCard
            initialFullName={account.full_name}
            initialContactPhone={account.contact_phone}
            initialAge={profile.age}
            initialBloodGroup={profile.blood_group}
            initialEmergencyContactName={profile.emergency_contact_name}
            initialEmergencyContactPhone={profile.emergency_contact_phone}
            initialEmergencyContactRelation={profile.emergency_contact_relation}
            initialResidentialAddress={profile.residential_address}
            initialSpouseDependents={parsedDependents}
          />
        </div>
      </div>
    </main>
  );
}

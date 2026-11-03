import React from 'react';
import type { Metadata } from 'next';
import { redirect } from 'next/navigation';
import { createClient } from '@/lib/supabase/server';
import { DoctorWorkspace } from '@/components/doctor/doctor-workspace';
import {
  getPatientClinicalRecordAction,
  getDoctorAppointmentsAction,
  type DetailedPatientRecord,
} from '@/app/portal/doctor/actions';

export const metadata: Metadata = {
  title: 'Physician Consultation Portal — Umbrella',
  description: 'Authoritative clinical records, verification workflows, and appointment management.',
};

export interface DoctorPageProps {
  searchParams?: Promise<{
    patient_token?: string;
    patient_id?: string;
  }>;
}

export default async function DoctorPortalPage(props: DoctorPageProps) {
  const supabase = createClient();
  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (!user || authError) {
    redirect('/login?next=/portal/doctor');
  }

  const { data: account, error: accError } = await supabase
    .from('accounts')
    .select('id, full_name, email, role, doctor_status, specialization, medical_license_number')
    .eq('id', user.id)
    .single();

  if (accError || !account) {
    redirect('/login');
  }

  // Cross-role redirect
  if (account.role !== 'doctor') {
    redirect('/portal/patient');
  }

  // Approval gate (DECISIONS D1)
  if (account.doctor_status !== 'approved') {
    redirect('/portal/doctor/pending');
  }

  const params = props.searchParams ? await props.searchParams : {};
  let initialPatient: DetailedPatientRecord | null = null;

  // Direct-load patient support (DECISIONS D15)
  if (params.patient_id) {
    const res = await getPatientClinicalRecordAction(params.patient_id);
    if (res.ok) {
      initialPatient = res.data;
    }
  } else if (params.patient_token) {
    const { data: profile } = await supabase
      .from('patient_profiles')
      .select('patient_id')
      .eq('qr_token', params.patient_token.toLowerCase())
      .maybeSingle();

    if (profile) {
      const res = await getPatientClinicalRecordAction(profile.patient_id);
      if (res.ok) {
        initialPatient = res.data;
      }
    }
  }

  // Fetch initial appointments for the doctor
  const appointmentsRes = await getDoctorAppointmentsAction();
  const initialAppointments = appointmentsRes.ok ? appointmentsRes.data : [];

  return (
    <DoctorWorkspace
      doctorName={account.full_name}
      specialization={account.specialization}
      initialPatient={initialPatient}
      initialAppointments={initialAppointments}
    />
  );
}

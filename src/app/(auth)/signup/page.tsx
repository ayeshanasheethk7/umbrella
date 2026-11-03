'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { User, Stethoscope, AlertCircle, CheckCircle2, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs } from '@/components/ui/tabs';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { createClient } from '@/lib/supabase/client';
import { patientSignupSchema, doctorSignupSchema } from '@/lib/schemas';
import { PatientSignupForm } from '@/components/auth/patient-signup-form';
import { DoctorSignupForm } from '@/components/auth/doctor-signup-form';

export default function SignupPage() {
  const router = useRouter();
  const [role, setRole] = useState<'patient' | 'doctor'>('patient');

  // Status state
  const [authError, setAuthError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [doctorPendingNotice, setDoctorPendingNotice] = useState(false);
  const [confirmationNotice, setConfirmationNotice] = useState<string | null>(null);

  const handlePatientSubmit = async (formData: Record<string, unknown>, setFieldErrors: (e: Record<string, string>) => void) => {
    setAuthError(null);
    setFieldErrors({});

    const result = patientSignupSchema.safeParse(formData);
    if (!result.success) {
      const errors: Record<string, string> = {};
      result.error.errors.forEach((err) => {
        if (err.path[0]) errors[String(err.path[0])] = err.message;
      });
      setFieldErrors(errors);
      return;
    }

    setIsLoading(true);
    try {
      const supabase = createClient();
      const { data, error } = await supabase.auth.signUp({
        email: result.data.email,
        password: result.data.password,
        options: {
          data: {
            role: 'patient',
            full_name: result.data.fullName,
            contact_phone: result.data.contactPhone,
            age: result.data.age,
            blood_group: result.data.bloodGroup,
            emergency_contact_name: result.data.emergencyContactName,
            emergency_contact_phone: result.data.emergencyContactPhone,
            emergency_contact_relation: result.data.emergencyContactRelation,
          },
        },
      });

      if (error) {
        setAuthError(error.message || 'Unable to register patient account.');
        setIsLoading(false);
        return;
      }

      if (!data.session) {
        setConfirmationNotice(
          'Account created successfully! Check your email to confirm your account, then proceed to sign in.'
        );
        setIsLoading(false);
        return;
      }

      router.push('/portal/patient');
      router.refresh();
    } catch {
      setAuthError('An unexpected network error occurred. Please try again.');
      setIsLoading(false);
    }
  };

  const handleDoctorSubmit = async (formData: Record<string, unknown>, setFieldErrors: (e: Record<string, string>) => void) => {
    setAuthError(null);
    setFieldErrors({});

    const result = doctorSignupSchema.safeParse(formData);
    if (!result.success) {
      const errors: Record<string, string> = {};
      result.error.errors.forEach((err) => {
        if (err.path[0]) errors[String(err.path[0])] = err.message;
      });
      setFieldErrors(errors);
      return;
    }

    setIsLoading(true);
    try {
      const supabase = createClient();
      const { error } = await supabase.auth.signUp({
        email: result.data.email,
        password: result.data.password,
        options: {
          data: {
            role: 'doctor',
            full_name: result.data.fullName,
            contact_phone: result.data.contactPhone,
            medical_license_number: result.data.medicalLicenseNumber,
            specialization: result.data.specialization,
          },
        },
      });

      if (error) {
        setAuthError(error.message || 'Unable to register physician account.');
        setIsLoading(false);
        return;
      }

      setDoctorPendingNotice(true);
      setIsLoading(false);
    } catch {
      setAuthError('An unexpected network error occurred. Please try again.');
      setIsLoading(false);
    }
  };

  if (doctorPendingNotice) {
    return (
      <div className="flex min-h-[calc(100vh-140px)] items-center justify-center px-4 py-12">
        <Card className="w-full max-w-lg bg-surface shadow-ceiling border border-black/10">
          <CardHeader className="text-center pb-6">
            <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-clinical-pending/10 text-clinical-pending-text">
              <Clock className="h-7 w-7" aria-hidden="true" />
            </div>
            <CardTitle className="text-2xl font-bold tracking-tight text-text-primary">
              Verification Pending
            </CardTitle>
            <CardDescription className="text-base text-text-body-secondary mt-2">
              Doctor accounts require manual verification per platform policy D1.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-text-body-secondary leading-relaxed">
              Your registration as a licensed physician has been recorded with status{' '}
              <strong className="text-clinical-pending-text">pending</strong>. For patient safety, clinical
              lookup and editing privileges are restricted until credential verification is approved by
              platform administration.
            </p>
            <div className="pt-4">
              <Button
                variant="primary"
                size="lg"
                className="w-full"
                onClick={() => router.push('/login')}
              >
                Proceed to Sign In
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (confirmationNotice) {
    return (
      <div className="flex min-h-[calc(100vh-140px)] items-center justify-center px-4 py-12">
        <Card className="w-full max-w-lg bg-surface shadow-ceiling border border-black/10">
          <CardHeader className="text-center pb-6">
            <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-clinical-verified/10 text-clinical-verified-text">
              <CheckCircle2 className="h-7 w-7" aria-hidden="true" />
            </div>
            <CardTitle className="text-2xl font-bold tracking-tight text-text-primary">
              Check Your Email
            </CardTitle>
            <CardDescription className="text-base text-text-body-secondary mt-2">
              Confirmation link dispatched
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-text-body-secondary leading-relaxed">
              {confirmationNotice}
            </p>
            <div className="pt-4">
              <Button
                variant="primary"
                size="lg"
                className="w-full"
                onClick={() => router.push('/login')}
              >
                Return to Sign In
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-[calc(100vh-140px)] items-center justify-center px-4 py-12">
      <Card className="w-full max-w-xl bg-surface shadow-ceiling border border-black/10">
        <CardHeader className="text-center pb-4">
          <CardTitle className="text-2xl font-bold tracking-tight text-text-primary">
            Create an Umbrella Account
          </CardTitle>
          <CardDescription className="text-sm text-text-body-secondary mt-1">
            Choose your account type to create emergency credentials or provider access.
          </CardDescription>

          <div className="flex justify-center pt-4">
            <Tabs
              tabs={[
                {
                  id: 'patient',
                  label: 'Patient ID',
                  icon: <User className="h-4 w-4" />,
                },
                {
                  id: 'doctor',
                  label: 'Physician',
                  icon: <Stethoscope className="h-4 w-4" />,
                },
              ]}
              activeTab={role}
              onChange={(tabId) => {
                setRole(tabId as 'patient' | 'doctor');
                setAuthError(null);
              }}
            />
          </div>
        </CardHeader>

        <CardContent>
          {authError && (
            <div
              className="mb-5 flex items-start gap-3 rounded-xl border border-clinical-critical/30 bg-clinical-critical/10 p-3.5 text-sm text-clinical-critical-text"
              role="alert"
            >
              <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
              <div className="leading-snug">{authError}</div>
            </div>
          )}

          {role === 'patient' ? (
            <PatientSignupForm
              isLoading={isLoading}
              onSubmit={handlePatientSubmit}
            />
          ) : (
            <DoctorSignupForm
              isLoading={isLoading}
              onSubmit={handleDoctorSubmit}
            />
          )}

          <div className="mt-6 text-center text-sm text-text-body-secondary border-t border-black/5 pt-5">
            Already have an Umbrella account?{' '}
            <Link
              href="/login"
              className="font-medium text-accent-action hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action rounded-sm"
            >
              Sign In
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface DoctorSignupFormProps {
  isLoading: boolean;
  onSubmit: (formData: Record<string, unknown>, setFieldErrors: (e: Record<string, string>) => void) => Promise<void>;
}

export const DoctorSignupForm: React.FC<DoctorSignupFormProps> = ({
  isLoading,
  onSubmit,
}) => {
  const [doctorEmail, setDoctorEmail] = useState('');
  const [doctorPassword, setDoctorPassword] = useState('');
  const [doctorFullName, setDoctorFullName] = useState('');
  const [doctorPhone, setDoctorPhone] = useState('');
  const [doctorLicense, setDoctorLicense] = useState('');
  const [doctorSpecialization, setDoctorSpecialization] = useState('');

  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(
      {
        role: 'doctor',
        email: doctorEmail,
        password: doctorPassword,
        fullName: doctorFullName,
        contactPhone: doctorPhone,
        medicalLicenseNumber: doctorLicense,
        specialization: doctorSpecialization,
      },
      setFieldErrors
    );
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          id="doctor-fullname"
          label="Physician Full Name"
          required
          value={doctorFullName}
          onChange={(e) => setDoctorFullName(e.target.value)}
          error={fieldErrors.fullName}
          placeholder="Dr. Sarah Jenkins, MD"
        />
        <Input
          id="doctor-phone"
          label="Contact Phone"
          type="tel"
          required
          value={doctorPhone}
          onChange={(e) => setDoctorPhone(e.target.value)}
          error={fieldErrors.contactPhone}
          placeholder="(555) 123-4567"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          id="doctor-email"
          type="email"
          label="Medical Center / Clinic Email"
          required
          value={doctorEmail}
          onChange={(e) => setDoctorEmail(e.target.value)}
          error={fieldErrors.email}
          placeholder="dr.jenkins@hospital.org"
        />
        <Input
          id="doctor-password"
          type="password"
          label="Password (min 8 chars)"
          required
          value={doctorPassword}
          onChange={(e) => setDoctorPassword(e.target.value)}
          error={fieldErrors.password}
          placeholder="Create secure password"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          id="doctor-license"
          label="Medical License / Registration #"
          required
          value={doctorLicense}
          onChange={(e) => setDoctorLicense(e.target.value)}
          error={fieldErrors.medicalLicenseNumber}
          placeholder="MED-774921-X"
        />
        <Input
          id="doctor-specialization"
          label="Specialization"
          required
          value={doctorSpecialization}
          onChange={(e) => setDoctorSpecialization(e.target.value)}
          error={fieldErrors.specialization}
          placeholder="Emergency Medicine / Trauma"
        />
      </div>

      <div className="rounded-xl bg-clinical-pending/10 border border-clinical-pending/30 p-3 text-xs text-clinical-pending-text leading-relaxed">
        <strong>Provider Verification Notice:</strong> Doctor registrations are set to{' '}
        <em>pending</em> verification. Full clinical record lookup and verification rights are
        unlocked following institutional license confirmation.
      </div>

      <Button
        type="submit"
        size="lg"
        className="w-full mt-2 font-semibold"
        isLoading={isLoading}
      >
        Register as Physician
      </Button>
    </form>
  );
};

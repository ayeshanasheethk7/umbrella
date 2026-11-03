'use client';

import React, { useState } from 'react';
import { bloodGroupEnum } from '@/lib/schemas';
import type { BloodGroup } from '@/lib/supabase/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface PatientSignupFormProps {
  isLoading: boolean;
  onSubmit: (formData: Record<string, unknown>, setFieldErrors: (e: Record<string, string>) => void) => Promise<void>;
}

export const PatientSignupForm: React.FC<PatientSignupFormProps> = ({
  isLoading,
  onSubmit,
}) => {
  const [patientEmail, setPatientEmail] = useState('');
  const [patientPassword, setPatientPassword] = useState('');
  const [patientFullName, setPatientFullName] = useState('');
  const [patientPhone, setPatientPhone] = useState('');
  const [patientAge, setPatientAge] = useState('');
  const [patientBloodGroup, setPatientBloodGroup] = useState<BloodGroup>('O+');
  const [patientEContactName, setPatientEContactName] = useState('');
  const [patientEContactPhone, setPatientEContactPhone] = useState('');
  const [patientEContactRelation, setPatientEContactRelation] = useState('');

  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const bloodGroupOptions = bloodGroupEnum.options;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(
      {
        role: 'patient',
        email: patientEmail,
        password: patientPassword,
        fullName: patientFullName,
        contactPhone: patientPhone,
        age: patientAge ? Number(patientAge) : undefined,
        bloodGroup: patientBloodGroup,
        emergencyContactName: patientEContactName,
        emergencyContactPhone: patientEContactPhone,
        emergencyContactRelation: patientEContactRelation,
      },
      setFieldErrors
    );
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          id="patient-fullname"
          label="Full Name"
          required
          value={patientFullName}
          onChange={(e) => setPatientFullName(e.target.value)}
          error={fieldErrors.fullName}
          placeholder="Jane Doe"
        />
        <Input
          id="patient-phone"
          label="Contact Phone"
          type="tel"
          required
          value={patientPhone}
          onChange={(e) => setPatientPhone(e.target.value)}
          error={fieldErrors.contactPhone}
          placeholder="(555) 000-1122"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          id="patient-email"
          type="email"
          label="Email Address"
          required
          value={patientEmail}
          onChange={(e) => setPatientEmail(e.target.value)}
          error={fieldErrors.email}
          placeholder="jane@example.com"
        />
        <Input
          id="patient-password"
          type="password"
          label="Password (min 8 chars)"
          required
          value={patientPassword}
          onChange={(e) => setPatientPassword(e.target.value)}
          error={fieldErrors.password}
          placeholder="Create secure password"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          id="patient-age"
          type="number"
          label="Age"
          required
          min={0}
          max={130}
          value={patientAge}
          onChange={(e) => setPatientAge(e.target.value)}
          error={fieldErrors.age}
          placeholder="34"
        />
        <div className="space-y-1.5">
          <label
            htmlFor="patient-bloodgroup"
            className="block text-sm font-medium text-text-primary"
          >
            Blood Group <span className="text-clinical-critical-text">*</span>
          </label>
          <select
            id="patient-bloodgroup"
            value={patientBloodGroup}
            onChange={(e) => setPatientBloodGroup(e.target.value as BloodGroup)}
            className="flex h-[44px] min-h-[44px] w-full rounded-xl border border-black/10 bg-surface px-3.5 py-2 text-base text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action"
          >
            {bloodGroupOptions.map((bg) => (
              <option key={bg} value={bg}>
                {bg}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="pt-2 border-t border-black/5">
        <h4 className="text-sm font-semibold text-text-primary mb-3">
          Primary Emergency Contact (Required for Triage)
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <Input
            id="patient-econtact-name"
            label="Contact Name"
            required
            value={patientEContactName}
            onChange={(e) => setPatientEContactName(e.target.value)}
            error={fieldErrors.emergencyContactName}
            placeholder="John Doe"
          />
          <Input
            id="patient-econtact-phone"
            label="Contact Phone"
            type="tel"
            required
            value={patientEContactPhone}
            onChange={(e) => setPatientEContactPhone(e.target.value)}
            error={fieldErrors.emergencyContactPhone}
            placeholder="(555) 000-3344"
          />
          <Input
            id="patient-econtact-relation"
            label="Relationship"
            required
            value={patientEContactRelation}
            onChange={(e) => setPatientEContactRelation(e.target.value)}
            error={fieldErrors.emergencyContactRelation}
            placeholder="Spouse / Sibling"
          />
        </div>
      </div>

      <Button
        type="submit"
        size="lg"
        className="w-full mt-4 font-semibold"
        isLoading={isLoading}
      >
        Create Patient Medical ID
      </Button>
    </form>
  );
};

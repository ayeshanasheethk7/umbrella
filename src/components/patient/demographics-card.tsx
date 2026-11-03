'use client';

import React, { useState, useTransition } from 'react';
import { Lock, CheckCircle2, AlertCircle, Save } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { updateDemographicsAction } from '@/app/portal/patient/actions';
import { DependentsManager } from '@/components/patient/dependents-manager';
import type { BloodGroup, SpouseDependent } from '@/lib/supabase/types';

export interface DemographicsCardProps {
  initialFullName: string;
  initialContactPhone: string;
  initialAge: number;
  initialBloodGroup: BloodGroup;
  initialEmergencyContactName: string;
  initialEmergencyContactPhone: string;
  initialEmergencyContactRelation: string;
  initialResidentialAddress: string;
  initialSpouseDependents: SpouseDependent[];
}

export const DemographicsCard: React.FC<DemographicsCardProps> = ({
  initialFullName,
  initialContactPhone,
  initialAge,
  initialBloodGroup,
  initialEmergencyContactName,
  initialEmergencyContactPhone,
  initialEmergencyContactRelation,
  initialResidentialAddress,
  initialSpouseDependents,
}) => {
  const [isPending, startTransition] = useTransition();
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const [fullName, setFullName] = useState(initialFullName);
  const [contactPhone, setContactPhone] = useState(initialContactPhone);
  const [age, setAge] = useState(String(initialAge));
  const [bloodGroup, setBloodGroup] = useState<BloodGroup>(initialBloodGroup);
  const [emergencyContactName, setEmergencyContactName] = useState(initialEmergencyContactName);
  const [emergencyContactPhone, setEmergencyContactPhone] = useState(initialEmergencyContactPhone);
  const [emergencyContactRelation, setEmergencyContactRelation] = useState(initialEmergencyContactRelation);
  const [residentialAddress, setResidentialAddress] = useState(initialResidentialAddress);
  const [spouseDependents, setSpouseDependents] = useState<SpouseDependent[]>(
    initialSpouseDependents || []
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage(null);
    setErrorMessage(null);
    setFieldErrors({});

    startTransition(async () => {
      const payload = {
        fullName,
        contactPhone,
        age: parseInt(age, 10) || 0,
        bloodGroup,
        emergencyContactName,
        emergencyContactPhone,
        emergencyContactRelation,
        residentialAddress,
        spouseDependents,
      };

      const res = await updateDemographicsAction(payload);
      if (res.ok) {
        setSuccessMessage(res.data.message || 'Profile saved successfully.');
      } else {
        setErrorMessage(res.error || 'Failed to update demographics.');
        if (res.fieldErrors) {
          setFieldErrors(res.fieldErrors);
        }
      }
    });
  };

  return (
    <Card className="p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-black/5">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-text-primary">
            Personal Demographics & Contacts
          </h2>
          <p className="text-sm text-text-body-secondary mt-0.5">
            Manage your personal contact info, primary emergency designee, and family dependents.
          </p>
        </div>

        <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-black/5 border border-black/10 text-xs font-medium text-text-body-secondary select-none shrink-0 self-start sm:self-center">
          <Lock className="h-3.5 w-3.5 text-accent-action" aria-hidden="true" />
          <span>Private: Excluded from emergency QR triage scan (N1)</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="mt-6 space-y-6">
        {successMessage && (
          <div
            className="p-3.5 rounded-xl bg-clinical-verified/10 border border-clinical-verified/30 text-sm text-clinical-verified-text flex items-center gap-2"
            role="status"
          >
            <CheckCircle2 className="h-5 w-5 shrink-0" aria-hidden="true" />
            <span>{successMessage}</span>
          </div>
        )}

        {errorMessage && (
          <div
            className="p-3.5 rounded-xl bg-clinical-critical/10 border border-clinical-critical/30 text-sm text-clinical-critical-text flex items-center gap-2"
            role="alert"
          >
            <AlertCircle className="h-5 w-5 shrink-0" aria-hidden="true" />
            <span>{errorMessage}</span>
          </div>
        )}

        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-text-body-secondary mb-3">
            Patient Identity
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="lg:col-span-2">
              <Input
                label="Full Legal Name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                error={fieldErrors.fullName}
                required
              />
            </div>

            <div>
              <Input
                label="Contact Phone"
                type="tel"
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
                error={fieldErrors.contactPhone}
                helperText="Personal cell/landline"
              />
            </div>

            <div>
              <Input
                label="Age (Years)"
                type="number"
                min="0"
                max="130"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                error={fieldErrors.age}
                required
              />
            </div>

            <div>
              <label
                htmlFor="blood-group-select"
                className="block text-sm font-medium text-text-primary mb-1.5"
              >
                Blood Group <span className="text-clinical-critical-text">*</span>
              </label>
              <select
                id="blood-group-select"
                value={bloodGroup}
                onChange={(e) => setBloodGroup(e.target.value as BloodGroup)}
                className="flex h-[44px] min-h-[44px] w-full rounded-xl border border-black/10 bg-surface px-3.5 py-2 text-base text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action"
              >
                {(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'Unknown'] as BloodGroup[]).map(
                  (bg) => (
                    <option key={bg} value={bg}>
                      {bg}
                    </option>
                  )
                )}
              </select>
            </div>

            <div className="lg:col-span-3">
              <Input
                label="Residential Address"
                value={residentialAddress}
                onChange={(e) => setResidentialAddress(e.target.value)}
                error={fieldErrors.residentialAddress}
                helperText="Kept strictly confidential; never exposed to public triage scans (N1)."
              />
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-black/5">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-text-body-secondary mb-3">
            Primary Emergency Contact (Included on Triage Pass)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Input
                label="Contact Name"
                value={emergencyContactName}
                onChange={(e) => setEmergencyContactName(e.target.value)}
                error={fieldErrors.emergencyContactName}
                required
              />
            </div>

            <div>
              <Input
                label="Emergency Phone"
                type="tel"
                value={emergencyContactPhone}
                onChange={(e) => setEmergencyContactPhone(e.target.value)}
                error={fieldErrors.emergencyContactPhone}
                required
              />
            </div>

            <div>
              <Input
                label="Relationship"
                value={emergencyContactRelation}
                onChange={(e) => setEmergencyContactRelation(e.target.value)}
                error={fieldErrors.emergencyContactRelation}
                placeholder="e.g. Spouse, Parent, Sibling"
                required
              />
            </div>
          </div>
        </div>

        <DependentsManager dependents={spouseDependents} onChange={setSpouseDependents} />

        <div className="pt-4 border-t border-black/5 flex items-center justify-end">
          <Button
            type="submit"
            variant="primary"
            size="lg"
            isLoading={isPending}
            disabled={isPending}
          >
            <Save className="mr-2 h-4 w-4" aria-hidden="true" />
            <span>Save Demographics</span>
          </Button>
        </div>
      </form>
    </Card>
  );
};

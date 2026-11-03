'use client';

import React, { useState, useTransition } from 'react';
import {
  FileHeart,
  Plus,
  X,
  Save,
  CheckCircle2,
  AlertCircle,
  Clock,
} from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { submitBaselineAction } from '@/app/portal/patient/actions';

export interface BaselineEditorProps {
  initialConditions: string[];
  initialAllergies: string[];
  isDoctorVerified: boolean;
}

export const BaselineEditor: React.FC<BaselineEditorProps> = ({
  initialConditions,
  initialAllergies,
  isDoctorVerified,
}) => {
  // Invariant D3 & D7: Disappearing Edit UI
  // Must completely disappear from DOM once doctor verification has occurred
  if (isDoctorVerified) {
    return null;
  }

  return (
    <ActiveBaselineEditor
      initialConditions={initialConditions}
      initialAllergies={initialAllergies}
    />
  );
};

interface ActiveBaselineEditorProps {
  initialConditions: string[];
  initialAllergies: string[];
}

const ActiveBaselineEditor: React.FC<ActiveBaselineEditorProps> = ({
  initialConditions,
  initialAllergies,
}) => {
  const [conditions, setConditions] = useState<string[]>(initialConditions || []);
  const [allergies, setAllergies] = useState<string[]>(initialAllergies || []);

  const [newCondition, setNewCondition] = useState('');
  const [newAllergy, setNewAllergy] = useState('');

  const [isPending, startTransition] = useTransition();
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleAddCondition = () => {
    const trimmed = newCondition.trim();
    if (!trimmed) return;
    if (conditions.includes(trimmed)) {
      setErrorMessage(`"${trimmed}" is already added.`);
      return;
    }
    if (conditions.length >= 50) {
      setErrorMessage('Maximum 50 conditions allowed.');
      return;
    }
    setConditions([...conditions, trimmed]);
    setNewCondition('');
    setErrorMessage(null);
  };

  const handleRemoveCondition = (index: number) => {
    setConditions(conditions.filter((_, i) => i !== index));
  };

  const handleAddAllergy = () => {
    const trimmed = newAllergy.trim();
    if (!trimmed) return;
    if (allergies.includes(trimmed)) {
      setErrorMessage(`"${trimmed}" is already added.`);
      return;
    }
    if (allergies.length >= 50) {
      setErrorMessage('Maximum 50 allergies allowed.');
      return;
    }
    setAllergies([...allergies, trimmed]);
    setNewAllergy('');
    setErrorMessage(null);
  };

  const handleRemoveAllergy = (index: number) => {
    setAllergies(allergies.filter((_, i) => i !== index));
  };

  const handleSave = () => {
    setSuccessMessage(null);
    setErrorMessage(null);

    startTransition(async () => {
      const res = await submitBaselineAction({
        conditions,
        allergies,
      });

      if (res.ok) {
        setSuccessMessage(res.data.message || 'Medical baseline updated successfully.');
      } else {
        setErrorMessage(res.error || 'Failed to submit baseline.');
      }
    });
  };

  return (
    <Card className="p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-black/5">
        <div className="flex items-center gap-2">
          <FileHeart className="h-5 w-5 text-accent-action" aria-hidden="true" />
          <div>
            <h2 className="text-xl font-bold tracking-tight text-text-primary">
              Self-Reported Health Baseline
            </h2>
            <p className="text-xs text-text-body-secondary mt-0.5">
              Add your chronic health conditions and allergies. This will lock when confirmed by a physician (DECISIONS D7).
            </p>
          </div>
        </div>

        {/* Amber Self-Reported Baseline Badge */}
        <Badge variant="pending" className="shrink-0 self-start sm:self-center">
          Self-Reported Baseline
        </Badge>
      </div>

      <div className="mt-5 space-y-6">
        {/* Status Alerts */}
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

        {/* Section 1: Chronic Conditions Chips */}
        <div>
          <label
            htmlFor="condition-input"
            className="block text-sm font-semibold text-text-primary mb-1.5"
          >
            Medical Conditions ({conditions.length}/50)
          </label>
          <div className="flex gap-2">
            <Input
              id="condition-input"
              placeholder="e.g. Type 1 Diabetes, Asthma, Hypertension"
              value={newCondition}
              onChange={(e) => setNewCondition(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAddCondition();
                }
              }}
            />
            <Button
              type="button"
              variant="secondary"
              onClick={handleAddCondition}
              aria-label="Add condition to list"
              className="shrink-0"
            >
              <Plus className="mr-1.5 h-4 w-4" />
              Add
            </Button>
          </div>

          {/* Condition chips */}
          <div className="flex flex-wrap gap-2 mt-3 min-h-[36px]">
            {conditions.length > 0 ? (
              conditions.map((item, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-black/5 text-text-primary text-xs font-medium border border-black/10 select-none"
                >
                  <span>{item}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveCondition(idx)}
                    className="inline-flex items-center justify-center min-h-[44px] min-w-[44px] -my-2 -mr-2 p-1 rounded-md hover:bg-black/10 text-text-body-secondary hover:text-text-primary transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent-action"
                    aria-label={`Remove condition ${item}`}
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </span>
              ))
            ) : (
              <span className="text-xs text-text-body-secondary italic self-center">
                No conditions added yet. Type a diagnosis and click Add.
              </span>
            )}
          </div>
        </div>

        {/* Section 2: Allergies Chips */}
        <div className="pt-4 border-t border-black/5">
          <label
            htmlFor="allergy-input"
            className="block text-sm font-semibold text-text-primary mb-1.5"
          >
            Allergies & Drug Reactions ({allergies.length}/50)
          </label>
          <div className="flex gap-2">
            <Input
              id="allergy-input"
              placeholder="e.g. Penicillin, Peanuts, Latex"
              value={newAllergy}
              onChange={(e) => setNewAllergy(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAddAllergy();
                }
              }}
            />
            <Button
              type="button"
              variant="secondary"
              onClick={handleAddAllergy}
              aria-label="Add allergy to list"
              className="shrink-0"
            >
              <Plus className="mr-1.5 h-4 w-4" />
              Add
            </Button>
          </div>

          {/* Allergy chips */}
          <div className="flex flex-wrap gap-2 mt-3 min-h-[36px]">
            {allergies.length > 0 ? (
              allergies.map((item, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-clinical-critical/10 text-clinical-critical-text text-xs font-bold border border-clinical-critical/30 select-none"
                >
                  <span>{item}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveAllergy(idx)}
                    className="inline-flex items-center justify-center min-h-[44px] min-w-[44px] -my-2 -mr-2 p-1 rounded-md hover:bg-clinical-critical/20 text-clinical-critical-text transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent-action"
                    aria-label={`Remove allergy ${item}`}
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </span>
              ))
            ) : (
              <span className="text-xs text-text-body-secondary italic self-center">
                No allergies added yet. Type an allergen and click Add.
              </span>
            )}
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-4 border-t border-black/5 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs text-text-body-secondary">
            <Clock className="h-3.5 w-3.5 text-clinical-pending-text" aria-hidden="true" />
            <span>Updates become visible on emergency triage scans immediately.</span>
          </div>

          <Button
            type="button"
            variant="primary"
            size="lg"
            onClick={handleSave}
            isLoading={isPending}
            disabled={isPending}
          >
            <Save className="mr-2 h-4 w-4" aria-hidden="true" />
            <span>Save Baseline</span>
          </Button>
        </div>
      </div>
    </Card>
  );
};

'use client';

import React, { useState } from 'react';
import { Users, Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import type { SpouseDependent } from '@/lib/supabase/types';

export interface DependentsManagerProps {
  dependents: SpouseDependent[];
  onChange: (updated: SpouseDependent[]) => void;
}

export const DependentsManager: React.FC<DependentsManagerProps> = ({
  dependents,
  onChange,
}) => {
  const [name, setName] = useState('');
  const [relation, setRelation] = useState('');
  const [age, setAge] = useState('');
  const [phone, setPhone] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleAdd = () => {
    setError(null);
    if (!name.trim()) {
      setError('Dependent name is required.');
      return;
    }
    if (!relation.trim()) {
      setError('Relationship is required.');
      return;
    }
    if (dependents.length >= 10) {
      setError('Maximum 10 dependents allowed.');
      return;
    }

    const newDep: SpouseDependent = {
      name: name.trim(),
      relation: relation.trim(),
      age: age ? parseInt(age, 10) : undefined,
      phone: phone.trim() || undefined,
    };

    onChange([...dependents, newDep]);
    setName('');
    setRelation('');
    setAge('');
    setPhone('');
  };

  const handleRemove = (index: number) => {
    onChange(dependents.filter((_, i) => i !== index));
  };

  return (
    <div className="pt-4 border-t border-black/5">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Users className="h-4 w-4 text-text-body-secondary" aria-hidden="true" />
          <h3 className="text-sm font-semibold uppercase tracking-wider text-text-body-secondary">
            Spouse & Dependents ({dependents.length}/10)
          </h3>
        </div>
        <span className="text-xs text-text-body-secondary">Private record (N1)</span>
      </div>

      {dependents.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
          {dependents.map((dep, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between p-3 rounded-xl bg-black/[0.02] border border-black/5"
            >
              <div className="min-w-0 pr-2">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-sm text-text-primary truncate">{dep.name}</span>
                  <span className="text-xs px-2 py-0.5 rounded-md bg-black/5 text-text-body-secondary shrink-0">
                    {dep.relation}
                  </span>
                </div>
                <div className="text-xs text-text-body-secondary mt-0.5">
                  {dep.age !== undefined ? `${dep.age} yrs` : ''}
                  {dep.age !== undefined && dep.phone ? ' • ' : ''}
                  {dep.phone || ''}
                </div>
              </div>

              <button
                type="button"
                onClick={() => handleRemove(idx)}
                className="min-h-[44px] min-w-[44px] inline-flex items-center justify-center p-2 rounded-lg text-text-body-secondary hover:text-clinical-critical-text hover:bg-clinical-critical/10 transition-colors"
                aria-label={`Remove dependent ${dep.name}`}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-text-body-secondary mb-4 italic">No spouse or dependents recorded.</p>
      )}

      {dependents.length < 10 && (
        <div className="p-3.5 rounded-xl border border-dashed border-black/15 bg-black/[0.01] space-y-3">
          <span className="text-xs font-semibold text-text-primary block">Add Family Member</span>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
            <Input placeholder="Dependent Name" value={name} onChange={(e) => setName(e.target.value)} />
            <Input
              placeholder="Relationship (e.g. Child)"
              value={relation}
              onChange={(e) => setRelation(e.target.value)}
            />
            <Input
              placeholder="Age (Optional)"
              type="number"
              min="0"
              max="130"
              value={age}
              onChange={(e) => setAge(e.target.value)}
            />
            <Input placeholder="Phone (Optional)" type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </div>

          {error && (
            <p className="text-xs text-clinical-critical-text font-medium" role="alert">
              {error}
            </p>
          )}

          <div className="flex justify-end">
            <Button type="button" variant="secondary" size="sm" onClick={handleAdd}>
              <Plus className="mr-1.5 h-3.5 w-3.5" />
              Add Dependent Entry
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

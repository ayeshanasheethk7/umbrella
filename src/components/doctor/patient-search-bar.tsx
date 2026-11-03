'use client';

import React, { useState, useEffect, useRef, useTransition } from 'react';
import { Search, Loader2, X, User, ShieldCheck, AlertCircle } from 'lucide-react';
import { searchPatientsAction, type PatientSearchResult } from '@/app/portal/doctor/actions';
import { BloodGroupPill, Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export interface PatientSearchBarProps {
  onSelectPatient: (patient: PatientSearchResult) => void;
  className?: string;
  autoFocus?: boolean;
}

export const PatientSearchBar: React.FC<PatientSearchBarProps> = ({
  onSelectPatient,
  className,
  autoFocus = false,
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<PatientSearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [activeIndex, setActiveIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Debounce search by 300ms per D14
  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setResults([]);
      setError(null);
      setIsOpen(false);
      return;
    }

    const timer = setTimeout(() => {
      startTransition(async () => {
        setError(null);
        const res = await searchPatientsAction(trimmed);
        if (res.ok) {
          setResults(res.data);
          setIsOpen(true);
          setActiveIndex(-1);
        } else {
          setError(res.error);
          setResults([]);
          setIsOpen(true);
        }
      });
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Click outside listener
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (patient: PatientSearchResult) => {
    onSelectPatient(patient);
    setQuery('');
    setResults([]);
    setIsOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || results.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((prev) => (prev < results.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((prev) => (prev > 0 ? prev - 1 : results.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0 && activeIndex < results.length && results[activeIndex]) {
        handleSelect(results[activeIndex]);
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const getSearchHint = () => {
    const t = query.trim();
    if (/^UMB-[A-Za-z0-9]{0,6}$/i.test(t)) return 'Searching by Patient Code';
    if (/^[0-9a-f-]{10,}$/i.test(t)) return 'Searching by QR Token';
    if (t.replace(/\D/g, '').length >= 7) return 'Searching by Phone Number';
    if (t.length >= 2) return 'Searching by Patient Name';
    return null;
  };

  const hint = getSearchHint();

  return (
    <div ref={containerRef} className={cn('relative w-full', className)}>
      <div className="relative flex items-center">
        <label htmlFor="patient-search-input" className="sr-only">
          Search Patients by Code, Name, Phone, or QR Token
        </label>
        <div className="pointer-events-none absolute left-3.5 flex items-center text-text-secondary">
          {isPending ? (
            <Loader2 className="h-4 w-4 animate-spin text-accent-action" aria-hidden="true" />
          ) : (
            <Search className="h-4 w-4" aria-hidden="true" />
          )}
        </div>
        <input
          id="patient-search-input"
          ref={inputRef}
          type="search"
          role="combobox"
          aria-expanded={isOpen}
          aria-autocomplete="list"
          aria-controls="patient-search-results"
          aria-activedescendant={activeIndex >= 0 ? `result-item-${activeIndex}` : undefined}
          autoFocus={autoFocus}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => {
            if (results.length > 0) setIsOpen(true);
          }}
          onKeyDown={handleKeyDown}
          placeholder="Lookup patient by UMB-XXXXXX, full name, phone, or UUID..."
          className="h-[44px] min-h-[44px] w-full rounded-xl border border-black/10 bg-surface pl-10 pr-12 text-sm text-text-primary placeholder:text-text-secondary shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action transition-all"
        />
        {query && (
          <button
            type="button"
            onClick={() => {
              setQuery('');
              setResults([]);
              setIsOpen(false);
              inputRef.current?.focus();
            }}
            className="absolute right-0 flex min-h-[44px] min-w-[44px] items-center justify-center rounded-lg text-text-secondary hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action"
            aria-label="Clear search input"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        )}
      </div>

      {hint && query.trim().length >= 2 && (
        <div className="mt-1 flex items-center gap-1.5 px-1 text-[11px] text-text-body-secondary font-medium">
          <span className="h-1.5 w-1.5 rounded-full bg-accent-action" />
          <span>{hint}</span>
        </div>
      )}

      {/* Results Drawer */}
      {isOpen && (
        <div
          id="patient-search-results"
          role="listbox"
          className="absolute left-0 right-0 top-full z-40 mt-1.5 max-h-80 overflow-y-auto rounded-2xl border border-black/10 bg-surface p-2 shadow-ceiling"
        >
          {error && (
            <div className="p-3 text-xs text-clinical-critical-text font-medium text-center">
              {error}
            </div>
          )}

          {!error && results.length === 0 && !isPending && (
            <div className="p-4 text-center text-xs text-text-body-secondary space-y-1">
              <p className="font-semibold text-text-primary">No matching patients found</p>
              <p>Verify the patient code (UMB-XXXXXX) or check spelling.</p>
            </div>
          )}

          {results.map((patient, index) => {
            const isSelected = index === activeIndex;
            return (
              <div
                key={patient.patient_id}
                id={`result-item-${index}`}
                role="option"
                aria-selected={isSelected}
                onClick={() => handleSelect(patient)}
                onMouseEnter={() => setActiveIndex(index)}
                className={cn(
                  'flex items-center justify-between p-3 rounded-xl cursor-pointer transition-colors min-h-[44px]',
                  isSelected ? 'bg-black/5' : 'hover:bg-black/5'
                )}
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-black/5 text-text-primary">
                    <User className="h-4 w-4" aria-hidden="true" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-text-primary">
                        {patient.full_name}
                      </span>
                      <span className="font-mono text-xs px-1.5 py-0.5 rounded bg-black/5 text-text-body-secondary font-semibold">
                        {patient.patient_code}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-text-body-secondary mt-0.5">
                      <span>Age: {patient.age} yrs</span>
                      <span>•</span>
                      <span>ICE: {patient.emergency_contact_name}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <BloodGroupPill bloodGroup={patient.blood_group} size="default" />
                  {patient.is_doctor_verified ? (
                    <Badge variant="verified" icon={<ShieldCheck className="h-3 w-3" />}>
                      Verified
                    </Badge>
                  ) : (
                    <Badge variant="pending" icon={<AlertCircle className="h-3 w-3" />}>
                      Self-Reported
                    </Badge>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

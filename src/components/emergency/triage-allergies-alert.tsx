import React from 'react';
import { AlertOctagon } from 'lucide-react';

interface TriageAllergiesAlertProps {
  allergies: string[];
}

/**
 * High-contrast critical allergy alert banner using design system tokens.
 * Non-negotiables: N1, N7, N8, D10
 */
export const TriageAllergiesAlert: React.FC<TriageAllergiesAlertProps> = ({ allergies }) => {
  if (!allergies || allergies.length === 0) {
    return (
      <section className="bg-surface rounded-2xl p-5 border border-black/10 shadow-sm">
        <div className="flex items-center gap-2 mb-2">
          <AlertOctagon className="w-5 h-5 text-text-body-secondary shrink-0" aria-hidden="true" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-text-body-secondary">
            Allergies
          </h3>
        </div>
        <p className="text-sm text-text-body-secondary">
          No known drug or environmental allergies reported.
        </p>
      </section>
    );
  }

  return (
    <section
      role="alert"
      className="bg-surface rounded-2xl p-5 border-2 border-clinical-critical bg-clinical-critical/5 shadow-sm"
    >
      <div className="flex items-center gap-2 mb-3">
        <AlertOctagon className="w-5 h-5 text-clinical-critical-text shrink-0" aria-hidden="true" />
        <h3 className="text-xs font-extrabold uppercase tracking-wider text-clinical-critical-text">
          CRITICAL ALLERGIES ALERT
        </h3>
      </div>
      <div className="flex flex-wrap gap-2">
        {allergies.map((allergy, idx) => (
          <span
            key={idx}
            className="px-3 py-1.5 bg-clinical-critical text-white text-sm font-bold rounded-xl shadow-xs"
          >
            {allergy}
          </span>
        ))}
      </div>
    </section>
  );
};

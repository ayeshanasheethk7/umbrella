import React from 'react';
import Link from 'next/link';
import { Stethoscope } from 'lucide-react';

interface TriageEscalationFooterProps {
  token: string;
}

/**
 * Healthcare Provider Escalation Footer (DECISIONS D15)
 * Direct link to /portal/doctor?patient_token=<uuid>
 * Non-negotiables: N1, N7, N8, D15
 */
export const TriageEscalationFooter: React.FC<TriageEscalationFooterProps> = ({ token }) => {
  return (
    <footer className="pt-6 pb-20 sm:pb-24 border-t border-black/10">
      <div className="rounded-2xl bg-surface border border-black/10 p-5 shadow-xs space-y-3">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-text-body-secondary">
          <Stethoscope className="h-4 w-4 text-accent-action shrink-0" aria-hidden="true" />
          <span>Healthcare Provider Escalation</span>
        </div>
        <p className="text-xs text-text-body-secondary leading-relaxed">
          Licensed physicians and emergency clinical personnel with active Umbrella credentials can access the complete clinical workspace.
        </p>
        <Link
          href={`/portal/doctor?patient_token=${token}`}
          className="flex items-center justify-center gap-2.5 w-full min-h-[48px] px-5 py-3 rounded-xl bg-surface border border-black/15 hover:bg-black/5 active:scale-[0.98] text-sm font-bold text-text-primary shadow-xs transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action select-none"
        >
          <Stethoscope className="h-4 w-4 text-accent-action shrink-0" aria-hidden="true" />
          <span>Open in Doctor Portal</span>
        </Link>
      </div>
      <p className="text-[11px] text-text-body-secondary text-center mt-4">
        Umbrella Emergency Medical ID • Public Triage Protocol
      </p>
    </footer>
  );
};

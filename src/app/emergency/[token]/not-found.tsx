import React from 'react';
import Link from 'next/link';
import { AlertOctagon, Phone, ArrowLeft } from 'lucide-react';

/**
 * Opaque Emergency 404 View
 * Generic not-found UI with zero diagnostic leaks (DECISIONS D9, Rule 02).
 * Non-negotiables: N1, N7, N8, D10, D12
 */
export default function EmergencyNotFound() {
  return (
    <div className="min-h-screen bg-canvas text-text-primary flex flex-col justify-between p-4">
      <div className="max-w-md mx-auto w-full pt-16 text-center space-y-6">
        {/* Warning Icon Badge */}
        <div className="w-20 h-20 rounded-full bg-clinical-critical/10 border border-clinical-critical/30 text-clinical-critical flex items-center justify-center mx-auto shadow-sm">
          <AlertOctagon className="w-10 h-10 shrink-0" aria-hidden="true" />
        </div>

        {/* Opaque Headline & Non-Diagnostic Description */}
        <div className="space-y-2">
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-text-primary">
            Emergency Record Not Found
          </h1>
          <p className="text-sm text-text-body-secondary leading-relaxed">
            The requested emergency triage record is not available. The identifier may be invalid, expired, or revoked.
          </p>
        </div>

        {/* Life-Safety Guidance & 56px Call Button */}
        <div className="bg-surface rounded-2xl p-5 border border-black/10 shadow-sm text-left space-y-3">
          <p className="text-xs font-bold uppercase tracking-wider text-clinical-critical-text">
            Immediate Assistance
          </p>
          <p className="text-sm text-text-body-secondary leading-relaxed">
            If this is a life-threatening medical emergency or roadside collision, contact emergency response services immediately.
          </p>
          <a
            href="tel:911"
            className="w-full min-h-[56px] min-w-[56px] bg-clinical-critical hover:opacity-95 active:scale-[0.98] text-white font-extrabold rounded-2xl flex items-center justify-center gap-3 text-base shadow-sm transition-transform select-none cursor-pointer focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-clinical-critical/30"
            aria-label="Call 911 Emergency Services Immediately"
          >
            <Phone className="w-5 h-5 shrink-0 fill-current" aria-hidden="true" />
            <span>Call 911 / Emergency Services</span>
          </a>
        </div>
      </div>

      {/* Return to Home */}
      <footer className="max-w-md mx-auto w-full pb-8 text-center">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm font-semibold text-accent-action hover:underline select-none"
        >
          <ArrowLeft className="w-4 h-4 shrink-0" aria-hidden="true" />
          <span>Return to Umbrella Home</span>
        </Link>
      </footer>
    </div>
  );
}

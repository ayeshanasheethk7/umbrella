'use client';

import React from 'react';
import { Phone, HeartHandshake, ShieldAlert } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { sanitizeTel, formatPhone } from '@/lib/utils';

export interface EmergencyContactCardProps {
  contactName: string;
  contactRelation: string;
  contactPhone: string;
}

export const EmergencyContactCard: React.FC<EmergencyContactCardProps> = ({
  contactName,
  contactRelation,
  contactPhone,
}) => {
  const sanitized = sanitizeTel(contactPhone);
  const formatted = formatPhone(contactPhone);

  return (
    <Card className="p-6 h-full flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between pb-3 border-b border-black/5">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-clinical-critical/10 flex items-center justify-center text-clinical-critical shrink-0">
              <Phone className="h-4 w-4" aria-hidden="true" />
            </div>
            <div>
              <h2 className="text-lg font-semibold tracking-tight text-text-primary">
                Emergency Contact
              </h2>
            </div>
          </div>
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full bg-black/5 text-text-body-secondary border border-black/10">
            <HeartHandshake className="h-3.5 w-3.5 text-accent-action" aria-hidden="true" />
            <span>Primary</span>
          </span>
        </div>

        <p className="text-xs text-text-body-secondary mt-2">
          First responders will immediately dial this number during roadside triage.
        </p>

        {/* Contact Details */}
        <div className="mt-4 p-4 rounded-xl bg-black/[0.02] border border-black/5 space-y-2">
          <div className="flex items-baseline justify-between gap-2">
            <span className="text-xl font-bold text-text-primary tracking-tight">
              {contactName || 'No contact name designated'}
            </span>
            {contactRelation && (
              <span className="text-xs font-medium px-2 py-0.5 rounded-md bg-black/5 text-text-body-secondary shrink-0">
                {contactRelation}
              </span>
            )}
          </div>

          <div className="pt-1">
            <span className="text-xs font-medium uppercase tracking-wider text-text-body-secondary block mb-0.5">
              Phone Number
            </span>
            <span className="text-lg font-mono font-bold text-text-primary tracking-tight">
              {formatted || 'No phone number provided'}
            </span>
          </div>
        </div>
      </div>

      {/* Call CTA Button */}
      <div className="mt-5 pt-3 border-t border-black/5">
        {sanitized ? (
          <a
            href={`tel:${sanitized}`}
            className="flex items-center justify-center gap-2 w-full min-h-[44px] px-5 py-2.5 rounded-xl bg-accent-action text-white font-semibold text-sm hover:bg-accent-action-hover active:bg-accent-action-active transition-colors shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action focus-visible:ring-offset-2 select-none"
            aria-label={`Call emergency contact ${contactName} at ${formatted}`}
          >
            <Phone className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span>Call Primary Contact</span>
          </a>
        ) : (
          <div className="flex items-center gap-2 p-3 rounded-xl bg-clinical-pending/10 text-clinical-pending-text text-xs">
            <ShieldAlert className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span>Please configure a verified emergency phone number below.</span>
          </div>
        )}
      </div>
    </Card>
  );
};

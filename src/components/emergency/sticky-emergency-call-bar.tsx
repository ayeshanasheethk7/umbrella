import React from 'react';
import { Phone } from 'lucide-react';
import { sanitizeTel, formatPhone } from '@/lib/utils';

interface StickyEmergencyCallBarProps {
  contactName: string;
  contactPhone: string;
  contactRelation: string;
}

/**
 * Sticky 56px Emergency Call Button (Non-negotiables: N1, N8, D10, D12, D13)
 * - 56px minimum touch target for life-critical dialing
 * - Sanitized tel: protocol
 * - Pure CSS :active:scale-[0.98] (zero JS animation runtime)
 * - High contrast white text on clinical critical background
 */
export const StickyEmergencyCallBar: React.FC<StickyEmergencyCallBarProps> = ({
  contactName,
  contactPhone,
  contactRelation,
}) => {
  const sanitized = sanitizeTel(contactPhone);
  if (!sanitized) return null;

  const displayPhone = formatPhone(contactPhone);
  const relationLabel = contactRelation ? contactRelation.toUpperCase() : 'CONTACT';

  return (
    <aside
      aria-label="Emergency call action"
      className="fixed bottom-0 left-0 right-0 z-50 p-4 bg-surface/95 backdrop-blur-md border-t border-black/10 pb-[max(1rem,env(safe-area-inset-bottom))] shadow-lg"
    >
      <div className="max-w-2xl mx-auto">
        <a
          href={`tel:${sanitized}`}
          className="flex items-center justify-center gap-3 w-full min-h-[56px] min-w-[56px] px-6 py-3.5 rounded-2xl bg-clinical-critical text-white font-extrabold text-base sm:text-lg shadow-md hover:opacity-95 active:scale-[0.98] transition-transform duration-100 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-clinical-critical/30 select-none cursor-pointer"
          aria-label={`Call Emergency Contact: ${contactName} (${relationLabel}) at ${displayPhone}`}
        >
          <Phone className="h-6 w-6 shrink-0 fill-current" aria-hidden="true" />
          <span className="truncate">
            CALL {relationLabel}: {contactName}
          </span>
        </a>
      </div>
    </aside>
  );
};

import React from 'react';
import { CheckCircle2, Clock, AlertTriangle, Info, AlertOctagon } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { BloodGroup } from '@/lib/supabase/types';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'verified' | 'pending' | 'critical' | 'neutral';
  icon?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = 'neutral',
  icon,
  children,
  ...props
}) => {
  const configs = {
    verified: {
      classes: 'bg-clinical-verified/10 text-clinical-verified-text border border-clinical-verified/30',
      defaultIcon: <CheckCircle2 className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />,
    },
    pending: {
      classes: 'bg-clinical-pending/10 text-clinical-pending-text border border-clinical-pending/30',
      defaultIcon: <Clock className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />,
    },
    critical: {
      classes: 'bg-clinical-critical/10 text-clinical-critical-text border border-clinical-critical/30',
      defaultIcon: <AlertTriangle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />,
    },
    neutral: {
      classes: 'bg-black/5 text-text-body-secondary border border-black/10',
      defaultIcon: <Info className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />,
    },
  };

  const current = configs[variant];

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium select-none',
        current.classes,
        className
      )}
      {...props}
    >
      {icon ?? current.defaultIcon}
      <span>{children}</span>
    </span>
  );
};

export interface BloodGroupPillProps {
  bloodGroup: BloodGroup;
  className?: string;
  size?: 'default' | 'lg';
}

export const BloodGroupPill: React.FC<BloodGroupPillProps> = ({
  bloodGroup,
  className,
  size = 'default',
}) => {
  const isLarge = size === 'lg';
  return (
    <div
      className={cn(
        'inline-flex flex-col items-center justify-center rounded-2xl bg-surface border-2 border-clinical-critical shadow-sm select-none',
        isLarge ? 'px-6 py-3 min-w-[100px]' : 'px-4 py-1.5 min-w-[70px]',
        className
      )}
      aria-label={`Blood group ${bloodGroup}`}
    >
      <span className="text-[10px] font-bold uppercase tracking-wider text-clinical-critical">
        Blood Group
      </span>
      <span
        className={cn(
          'font-extrabold text-clinical-critical leading-tight',
          isLarge ? 'text-3xl' : 'text-xl'
        )}
      >
        {bloodGroup}
      </span>
    </div>
  );
};

export interface AllergyAlertProps {
  allergies: string[];
  className?: string;
}

export const AllergyAlert: React.FC<AllergyAlertProps> = ({
  allergies,
  className,
}) => {
  if (!allergies || allergies.length === 0) {
    return (
      <div className={cn('rounded-xl border border-black/10 bg-surface p-4 text-sm text-text-body-secondary', className)}>
        No known drug or environmental allergies reported.
      </div>
    );
  }

  return (
    <div
      className={cn(
        'rounded-xl border-2 border-clinical-critical bg-clinical-critical/10 p-4 text-text-primary shadow-sm',
        className
      )}
      role="alert"
    >
      <div className="flex items-center gap-2 text-clinical-critical font-bold text-sm mb-2">
        <AlertOctagon className="h-5 w-5 shrink-0" aria-hidden="true" />
        <span>CRITICAL ALLERGY ALERT</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {allergies.map((allergy, index) => (
          <span
            key={index}
            className="inline-flex items-center px-3 py-1 rounded-lg bg-clinical-critical text-white font-semibold text-sm shadow-xs"
          >
            {allergy}
          </span>
        ))}
      </div>
    </div>
  );
};

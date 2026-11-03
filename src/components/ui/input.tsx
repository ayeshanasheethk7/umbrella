import React from 'react';
import { cn } from '@/lib/utils';

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = 'text', label, error, helperText, id, required, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);
    const errorId = inputId ? `${inputId}-error` : undefined;
    const helperId = inputId ? `${inputId}-helper` : undefined;

    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-text-primary"
          >
            {label}
            {required && (
              <span className="text-clinical-critical-text ml-1" aria-hidden="true">
                *
              </span>
            )}
          </label>
        )}
        <input
          id={inputId}
          type={type}
          ref={ref}
          required={required}
          aria-invalid={Boolean(error)}
          aria-describedby={
            error ? errorId : helperText ? helperId : undefined
          }
          className={cn(
            'flex h-[44px] min-h-[44px] w-full rounded-xl border border-black/10 bg-surface px-3.5 py-2 text-base text-text-primary placeholder:text-text-secondary transition-colors',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action focus-visible:border-transparent',
            'disabled:cursor-not-allowed disabled:opacity-50',
            error && 'border-clinical-critical focus-visible:ring-clinical-critical',
            className
          )}
          {...props}
        />
        {error && (
          <p id={errorId} className="text-xs font-medium text-clinical-critical-text mt-1" role="alert">
            {error}
          </p>
        )}
        {!error && helperText && (
          <p id={helperId} className="text-xs text-text-body-secondary mt-1">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

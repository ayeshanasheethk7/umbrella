'use client';

import React from 'react';
import { motion, type HTMLMotionProps } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { appleSpring } from '@/lib/motion';

export interface ButtonProps
  extends Omit<HTMLMotionProps<'button'>, 'children'> {
  variant?: 'primary' | 'secondary' | 'destructive' | 'ghost' | 'emergency';
  size?: 'default' | 'sm' | 'lg' | 'emergency';
  isLoading?: boolean;
  children: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'default',
      isLoading = false,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      'inline-flex items-center justify-center font-medium rounded-xl transition-colors duration-150 ' +
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action focus-visible:ring-offset-2 ' +
      'disabled:pointer-events-none disabled:opacity-50 select-none';

    const variants = {
      primary:
        'bg-accent-action text-white hover:bg-accent-action-hover active:bg-accent-action-active shadow-sm',
      secondary:
        'bg-surface text-text-primary border border-black/10 hover:bg-black/5 active:bg-black/10',
      destructive:
        'bg-clinical-critical text-white hover:bg-clinical-critical-hover active:bg-clinical-critical-active shadow-sm',
      ghost:
        'bg-transparent text-text-primary hover:bg-black/5 active:bg-black/10',
      emergency:
        'bg-clinical-critical text-white font-bold text-lg hover:bg-clinical-critical-hover active:bg-clinical-critical-active shadow-md',
    };

    const sizes = {
      default: 'h-[44px] min-h-[44px] px-5 py-2 text-sm',
      sm: 'h-[44px] min-h-[44px] px-3.5 py-1 text-xs',
      lg: 'h-[50px] min-h-[50px] px-6 py-3 text-base',
      emergency: 'h-[56px] min-h-[56px] px-8 py-3.5 text-lg w-full',
    };

    return (
      <motion.button
        ref={ref}
        disabled={disabled || isLoading}
        whileHover={disabled || isLoading ? undefined : { scale: 1.015 }}
        whileTap={disabled || isLoading ? undefined : { scale: 0.98 }}
        transition={appleSpring}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      >
        {isLoading && (
          <Loader2 className="mr-2 h-4 w-4 animate-spin shrink-0" aria-hidden="true" />
        )}
        {children}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';

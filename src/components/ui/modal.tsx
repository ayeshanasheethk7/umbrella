'use client';

import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { modalDialogVariants } from '@/lib/motion';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  isDestructive?: boolean;
  footer?: React.ReactNode;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  isDestructive = false,
  footer,
}) => {
  const dialogRef = useRef<HTMLDivElement>(null);
  const previousActiveElementRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    // Save previous active element to restore focus on unmount/close
    previousActiveElementRef.current = document.activeElement as HTMLElement | null;

    const getFocusableElements = (): HTMLElement[] => {
      if (!dialogRef.current) return [];
      const selectors =
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
      return Array.from(dialogRef.current.querySelectorAll<HTMLElement>(selectors)).filter(
        (el) => el.offsetParent !== null || el.offsetWidth > 0 || el.offsetHeight > 0
      );
    };

    // Auto-focus first focusable element on open
    const focusTimer = setTimeout(() => {
      const focusable = getFocusableElements();
      if (focusable.length > 0) {
        focusable[0]?.focus();
      } else if (dialogRef.current) {
        dialogRef.current.focus();
      }
    }, 50);

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isDestructive) {
        e.preventDefault();
        onClose();
        return;
      }

      // Keyboard focus trap: Tab and Shift+Tab loop within modal
      if (e.key === 'Tab') {
        const focusable = getFocusableElements();
        if (focusable.length === 0) {
          e.preventDefault();
          return;
        }

        const firstElement = focusable[0];
        const lastElement = focusable[focusable.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === firstElement || !dialogRef.current?.contains(document.activeElement)) {
            e.preventDefault();
            lastElement?.focus();
          }
        } else {
          if (document.activeElement === lastElement || !dialogRef.current?.contains(document.activeElement)) {
            e.preventDefault();
            firstElement?.focus();
          }
        }
      }
    };

    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      clearTimeout(focusTimer);
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleKeyDown);
      if (previousActiveElementRef.current && typeof previousActiveElementRef.current.focus === 'function') {
        previousActiveElementRef.current.focus();
      }
    };
  }, [isOpen, onClose, isDestructive]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-title"
          aria-describedby={description ? 'modal-description' : undefined}
        >
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => {
              if (!isDestructive) onClose();
            }}
          />

          {/* Modal Content */}
          <motion.div
            ref={dialogRef}
            tabIndex={-1}
            variants={modalDialogVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className={cn(
              'relative z-10 w-full max-w-lg rounded-[20px] bg-surface p-6 shadow-2xl border border-black/10 focus:outline-none'
            )}
          >
            <div className="flex items-start justify-between pb-4">
              <div>
                <h2 id="modal-title" className="text-xl font-semibold text-text-primary tracking-[-0.022em]">
                  {title}
                </h2>
                {description && (
                  <p id="modal-description" className="text-sm text-text-body-secondary mt-1">
                    {description}
                  </p>
                )}
              </div>
              {!isDestructive && (
                <button
                  type="button"
                  onClick={onClose}
                  className="min-h-[44px] min-w-[44px] inline-flex items-center justify-center p-2 rounded-full text-text-secondary hover:bg-black/5 hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action transition-colors"
                  aria-label="Close modal"
                >
                  <X className="h-5 w-5" />
                </button>
              )}
            </div>
            <div className="mt-2">{children}</div>
            {footer && <div className="mt-4 pt-4 border-t border-black/5">{footer}</div>}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

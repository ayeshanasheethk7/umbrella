import type { Transition, Variants } from 'framer-motion';

/**
 * Shared Apple spring motion configuration (per AGENTS.md N8 & 01-design-system.md)
 * Stiffness: 120, Damping: 20, Mass: 1
 */
export const appleSpring: Transition = {
  type: 'spring',
  stiffness: 120,
  damping: 20,
  mass: 1,
};

/**
 * Button hover & tap physics
 */
export const buttonPressVariants: Variants = {
  initial: { scale: 1 },
  hover: { scale: 1.015, transition: appleSpring },
  tap: { scale: 0.98, transition: appleSpring },
};

/**
 * Editorial scroll reveal for showcase sections
 */
export const scrollRevealVariants: Variants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: appleSpring,
  },
};

/**
 * Card entrance and modal dialog transitions
 */
export const modalDialogVariants: Variants = {
  hidden: { opacity: 0, scale: 0.96, y: 12 },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: appleSpring,
  },
  exit: {
    opacity: 0,
    scale: 0.96,
    y: 12,
    transition: { duration: 0.15, ease: 'easeOut' },
  },
};

/**
 * Segmented control active pill layout transition
 */
export const segmentedPillTransition: Transition = {
  type: 'spring',
  stiffness: 180,
  damping: 24,
  mass: 1,
};

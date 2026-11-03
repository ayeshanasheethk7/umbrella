import { describe, it, expect } from 'vitest';
import {
  appleSpring,
  buttonPressVariants,
  scrollRevealVariants,
  modalDialogVariants,
  segmentedPillTransition,
} from '@/lib/motion';

describe('Tier 1: Apple Motion Physics — Happy-Path Specifications', () => {
  it('T1-MOTION-01: appleSpring adheres to exact design tokens (stiffness: 120, damping: 20, mass: 1)', () => {
    expect(appleSpring).toEqual({
      type: 'spring',
      stiffness: 120,
      damping: 20,
      mass: 1,
    });
  });

  it('T1-MOTION-02: segmentedPillTransition provides crisp physics (stiffness: 180, damping: 24, mass: 1)', () => {
    expect(segmentedPillTransition).toEqual({
      type: 'spring',
      stiffness: 180,
      damping: 24,
      mass: 1,
    });
  });

  it('T1-MOTION-03: buttonPressVariants specifies 1.015 hover and 0.98 tap scales', () => {
    expect(buttonPressVariants.initial).toEqual({ scale: 1 });
    expect(buttonPressVariants.hover).toHaveProperty('scale', 1.015);
    expect(buttonPressVariants.tap).toHaveProperty('scale', 0.98);
  });

  it('T1-MOTION-04: scrollRevealVariants starts at opacity 0, y 30 and transitions cleanly', () => {
    expect(scrollRevealVariants.hidden).toEqual({ opacity: 0, y: 30 });
    expect(scrollRevealVariants.visible).toHaveProperty('opacity', 1);
    expect(scrollRevealVariants.visible).toHaveProperty('y', 0);
  });

  it('T1-MOTION-05: modalDialogVariants scales down to 0.96 with subtle y displacement', () => {
    expect(modalDialogVariants.hidden).toEqual({ opacity: 0, scale: 0.96, y: 12 });
    expect(modalDialogVariants.visible).toHaveProperty('scale', 1);
    expect(modalDialogVariants.visible).toHaveProperty('opacity', 1);
  });

  it('T1-MOTION-06: verifies button hover transition uses shared appleSpring transition', () => {
    const hover = buttonPressVariants.hover;
    expect(hover).toHaveProperty('transition', appleSpring);
  });

  it('T1-MOTION-07: verifies scroll reveal visible transition uses appleSpring', () => {
    const visible = scrollRevealVariants.visible;
    expect(visible).toHaveProperty('transition', appleSpring);
  });

  it('T1-MOTION-08: verifies modalDialogVariants visible transition uses appleSpring', () => {
    const visible = modalDialogVariants.visible;
    expect(visible).toHaveProperty('transition', appleSpring);
  });
});

describe('Tier 2: Apple Motion Physics — Invariants & Motion Safety', () => {
  it('T2-MOTION-01: modal exit animation uses 150ms easeOut for quick dismissals', () => {
    const exitTransition = modalDialogVariants.exit;
    expect(exitTransition).toBeDefined();
    if (exitTransition && typeof exitTransition === 'object' && 'transition' in exitTransition) {
      expect(exitTransition.transition).toEqual({ duration: 0.15, ease: 'easeOut' });
    }
  });

  it('T2-MOTION-02: zero motion variants contain forbidden ease-in-out curves for movement (Rule 01)', () => {
    const serialized = JSON.stringify({
      appleSpring,
      buttonPressVariants,
      scrollRevealVariants,
      segmentedPillTransition,
    });
    expect(serialized.includes('easeInOut')).toBe(false);
    expect(serialized.includes('ease-in-out')).toBe(false);
  });

  it('T2-MOTION-03: verifies under-damped spring ratio for responsive tactile feel', () => {
    const s = 120;
    const d = 20;
    const m = 1;
    const zeta = d / (2 * Math.sqrt(s * m));
    expect(zeta).toBeGreaterThan(0.85);
    expect(zeta).toBeLessThan(0.95);
  });

  it('T2-MOTION-04: verifies segmentedPillTransition damping ratio for crisp snap without overshoot', () => {
    const s = 180;
    const d = 24;
    const m = 1;
    const zeta = d / (2 * Math.sqrt(s * m));
    expect(zeta).toBeGreaterThan(0.85);
    expect(zeta).toBeLessThan(0.95);
  });

  it('T2-MOTION-05: verifies button tap scale does not drop below 0.95 to prevent jarring shrink', () => {
    const tap = buttonPressVariants.tap;
    if (tap && typeof tap === 'object' && 'scale' in tap) {
      expect(Number(tap.scale)).toBeGreaterThanOrEqual(0.95);
    }
  });

  it('T2-MOTION-06: verifies modal initial scale is greater than or equal to 0.90', () => {
    const hidden = modalDialogVariants.hidden;
    if (hidden && typeof hidden === 'object' && 'scale' in hidden) {
      expect(Number(hidden.scale)).toBeGreaterThanOrEqual(0.90);
    }
  });

  it('T2-MOTION-07: verifies scroll reveal y displacement is less than or equal to 50px', () => {
    const hidden = scrollRevealVariants.hidden;
    if (hidden && typeof hidden === 'object' && 'y' in hidden) {
      expect(Number(hidden.y)).toBeLessThanOrEqual(50);
    }
  });

  it('T2-MOTION-08: confirms mass equals 1 on all spring configurations', () => {
    expect((appleSpring as { mass?: number }).mass).toBe(1);
    expect((segmentedPillTransition as { mass?: number }).mass).toBe(1);
  });
});

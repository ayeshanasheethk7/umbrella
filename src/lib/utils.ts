/**
 * Utility functions for Umbrella platform
 */

type ClassValue = string | number | boolean | undefined | null | { [key: string]: boolean | undefined | null } | ClassValue[];

/**
 * Combines class names into a single normalized string without extra dependencies
 */
export function cn(...inputs: ClassValue[]): string {
  const classes: string[] = [];

  for (const input of inputs) {
    if (!input) continue;

    if (typeof input === 'string' || typeof input === 'number') {
      classes.push(String(input));
    } else if (Array.isArray(input)) {
      const inner = cn(...input);
      if (inner) classes.push(inner);
    } else if (typeof input === 'object') {
      for (const [key, value] of Object.entries(input)) {
        if (value) classes.push(key);
      }
    }
  }

  return classes.join(' ');
}

/**
 * Sanitizes redirect destination URLs to prevent open redirect vulnerabilities (DECISIONS D15)
 * Accepts only relative paths starting with a single "/" (never "//" or "/\" or external protocols)
 */
export function safeNext(url: string | null | undefined, fallback: string = '/portal/patient'): string {
  if (!url || typeof url !== 'string') {
    return fallback;
  }

  const trimmed = url.trim();

  // Must begin with a single '/'
  if (!trimmed.startsWith('/')) {
    return fallback;
  }

  // Reject protocol-relative URLs (//) or backslash evasion (/\ or \/) or path traversal
  if (
    trimmed.startsWith('//') ||
    trimmed.startsWith('/\\') ||
    trimmed.includes('\\') ||
    trimmed.startsWith('/.') ||
    trimmed.includes('/..')
  ) {
    return fallback;
  }

  // Reject embedded protocols (e.g., /http:, /javascript:)
  if (/^\/[a-zA-Z][a-zA-Z0-9+.-]*:/.test(trimmed)) {
    return fallback;
  }

  // Reject control characters or newlines
  if (/[\r\n\t]/.test(trimmed)) {
    return fallback;
  }

  return trimmed;
}

/**
 * Sanitizes phone numbers for tel: links per Rule 02 (digits and one optional leading +)
 */
export function sanitizeTel(phone: string): string {
  if (!phone) return '';
  const hasPlus = phone.includes('+');
  const digits = phone.replace(/\D/g, '');
  if (!digits) return '';
  return hasPlus ? `+${digits}` : digits;
}

/**
 * Formats a phone number for human-readable display
 */
export function formatPhone(phone: string): string {
  if (!phone) return '';
  const digits = phone.replace(/\D/g, '');
  if (digits.length === 10) {
    return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
  }
  return phone;
}

/**
 * Builds the canonical public emergency triage URL (N6, skill umbrella-qr-card)
 */
export function buildEmergencyUrl(origin: string, qrToken: string): string {
  const cleanOrigin = (origin || '').replace(/\/+$/, '');
  const cleanToken = (qrToken || '').trim();
  return `${cleanOrigin}/emergency/${cleanToken}`;
}


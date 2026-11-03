import { describe, it, expect } from 'vitest';
import { safeNext, sanitizeTel, formatPhone, buildEmergencyUrl, cn } from '@/lib/utils';

describe('Tier 1: Platform Utilities — Happy-Path Isolation', () => {
  it('T1-SAFENEXT-01: accepts standard relative paths for portal routing', () => {
    expect(safeNext('/portal/patient')).toBe('/portal/patient');
    expect(safeNext('/portal/doctor')).toBe('/portal/doctor');
    expect(safeNext('/portal/doctor/pending')).toBe('/portal/doctor/pending');
  });

  it('T1-SAFENEXT-02: preserves permitted search query parameters', () => {
    const url = '/portal/doctor?patient=UMB-A1B2C3';
    expect(safeNext(url)).toBe(url);
  });

  it('T1-SAFENEXT-03: preserves path anchors and sub-tabs', () => {
    expect(safeNext('/portal/patient#qr-pass')).toBe('/portal/patient#qr-pass');
  });

  it('T1-SAFENEXT-04: returns default fallback when given null or undefined', () => {
    expect(safeNext(null)).toBe('/portal/patient');
    expect(safeNext(undefined)).toBe('/portal/patient');
  });

  it('T1-SANTEL-01: sanitizes formatted US phone numbers into clean digits', () => {
    expect(sanitizeTel('(555) 123-4567')).toBe('5551234567');
  });

  it('T1-SANTEL-02: preserves leading plus for international dialing', () => {
    expect(sanitizeTel('+91 98765 43210')).toBe('+919876543210');
    expect(sanitizeTel('+44-20-7946-0958')).toBe('+442079460958');
  });

  it('T1-SANTEL-03: handles dots and hyphens cleanly in phone strings', () => {
    expect(sanitizeTel('555.123.4567')).toBe('5551234567');
    expect(sanitizeTel('555-123-4567')).toBe('5551234567');
  });

  it('T1-FORMPHON-01: formats standard 10-digit numbers into (XXX) XXX-XXXX', () => {
    expect(formatPhone('1234567890')).toBe('(123) 456-7890');
  });

  it('T1-FORMPHON-02: formats already hyphenated 10-digit numbers into (XXX) XXX-XXXX', () => {
    expect(formatPhone('123-456-7890')).toBe('(123) 456-7890');
  });

  it('T1-BLDURL-01: composes canonical emergency URLs from origin and UUID token', () => {
    const origin = 'https://umbrella.health';
    const token = '550e8400-e29b-41d4-a716-446655440000';
    expect(buildEmergencyUrl(origin, token)).toBe('https://umbrella.health/emergency/550e8400-e29b-41d4-a716-446655440000');
  });

  it('T1-BLDURL-02: handles origin without trailing slash cleanly', () => {
    expect(buildEmergencyUrl('https://umbrella.app', 'token-123')).toBe('https://umbrella.app/emergency/token-123');
  });

  it('T1-BLDURL-03: composes URL with localhost and port', () => {
    expect(buildEmergencyUrl('http://localhost:3000', 'uuid-token')).toBe('http://localhost:3000/emergency/uuid-token');
  });

  it('T1-CN-01: combines class names, booleans, arrays, and objects cleanly', () => {
    expect(cn('btn', true && 'btn-primary', false && 'btn-disabled')).toBe('btn btn-primary');
    expect(cn(['px-4', 'py-2'], { 'bg-surface': true, hidden: false })).toBe('px-4 py-2 bg-surface');
  });

  it('T1-CN-02: ignores falsy values in className resolution', () => {
    expect(cn('valid', undefined, null, false, 0, '')).toBe('valid');
  });
});

describe('Tier 2: Platform Utilities — Boundaries & Adversarial Edge Cases', () => {
  it('T2-SAFENEXT-01: rejects protocol-relative open redirect attacks', () => {
    expect(safeNext('//evil.com')).toBe('/portal/patient');
    expect(safeNext('//evil.com/login')).toBe('/portal/patient');
  });

  it('T2-SAFENEXT-02: rejects backslash evasion techniques', () => {
    expect(safeNext('/\\evil.com')).toBe('/portal/patient');
    expect(safeNext('\\evil.com')).toBe('/portal/patient');
    expect(safeNext('/path\\to\\somewhere')).toBe('/portal/patient');
  });

  it('T2-SAFENEXT-03: rejects embedded external protocol injections', () => {
    expect(safeNext('/http://evil.com')).toBe('/portal/patient');
    expect(safeNext('/javascript:alert(1)')).toBe('/portal/patient');
  });

  it('T2-SAFENEXT-04: rejects CRLF and whitespace control characters', () => {
    expect(safeNext('/\r\nevil.com')).toBe('/portal/patient');
    expect(safeNext('/\nevil.com')).toBe('/portal/patient');
    expect(safeNext('/\tevil.com')).toBe('/portal/patient');
  });

  it('T2-SAFENEXT-05: honors custom fallback upon rejection', () => {
    expect(safeNext('//attack.test', '/portal/doctor')).toBe('/portal/doctor');
    expect(safeNext(null, '/login')).toBe('/login');
    expect(safeNext(undefined, '/signup')).toBe('/signup');
  });

  it('T2-SAFENEXT-06: rejects data URI schemes in redirect paths', () => {
    expect(safeNext('/data:text/html,...')).toBe('/portal/patient');
  });

  it('T2-SAFENEXT-07: rejects encoded or path traversal external protocol attacks', () => {
    expect(safeNext('/../evil.com')).toBe('/portal/patient');
  });

  it('T2-SANTEL-01: handles empty, whitespace, and punctuation-only inputs', () => {
    expect(sanitizeTel('')).toBe('');
    expect(sanitizeTel('   ')).toBe('');
    expect(sanitizeTel('+')).toBe('');
    expect(sanitizeTel('()-.-')).toBe('');
  });

  it('T2-SANTEL-02: strips alphabetic characters while preserving valid digits and plus', () => {
    expect(sanitizeTel('+1-800-DOCTOR')).toBe('+1800');
    expect(sanitizeTel('1-800-HEALTHTEAM')).toBe('1800');
  });

  it('T2-SANTEL-03: strips emojis and unicode symbols from telephone string', () => {
    expect(sanitizeTel('📞 +1-555-1234')).toBe('+15551234');
  });

  it('T2-FORMPHON-01: leaves non-10-digit numbers unaltered', () => {
    expect(formatPhone('+919876543210')).toBe('+919876543210');
  });

  it('T2-FORMPHON-02: leaves short numbers unaltered', () => {
    expect(formatPhone('1234567')).toBe('1234567');
    expect(formatPhone('')).toBe('');
  });

  it('T2-BLDURL-01: strips multiple trailing slashes from origin and trims token', () => {
    expect(buildEmergencyUrl('https://umbrella.health///', '  token-123  ')).toBe('https://umbrella.health/emergency/token-123');
    expect(buildEmergencyUrl('http://localhost:3000/', 'token')).toBe('http://localhost:3000/emergency/token');
  });

  it('T2-CN-01: handles empty arguments and nested falsy entries', () => {
    expect(cn()).toBe('');
    expect(cn(null, undefined, false, '')).toBe('');
    expect(cn('first', [null, undefined, ['second', false]])).toBe('first second');
  });
});

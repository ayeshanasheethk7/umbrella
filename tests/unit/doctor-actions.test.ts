import { describe, it, expect } from 'vitest';
import {
  escapeSearchTerm,
  PATIENT_CODE_REGEX,
  QR_TOKEN_UUID_REGEX,
  extractPhoneDigits,
  classifySearchQuery,
  mapPatientSearchRow,
  type SearchRow,
} from '@/app/portal/doctor/actions';

describe('Tier 1: Doctor Actions Pure Logic — Happy-Path Isolation', () => {
  it('T1-ESC-01: preserves standard alphanumeric clinician queries', () => {
    expect(escapeSearchTerm('Jane Doe')).toBe('Jane Doe');
    expect(escapeSearchTerm('Dr. Alice')).toBe('Dr. Alice');
    expect(escapeSearchTerm('Sharma-Patel')).toBe('Sharma-Patel');
  });

  it('T1-ESC-02: trims leading and trailing whitespace', () => {
    expect(escapeSearchTerm('  Robert  ')).toBe('Robert');
    expect(escapeSearchTerm('\tTaylor\n')).toBe('Taylor');
  });

  it('T1-CODE-01: PATIENT_CODE_REGEX matches standard uppercase code UMB-XXXXXX', () => {
    expect(PATIENT_CODE_REGEX.test('UMB-A1B2C3')).toBe(true);
    expect(PATIENT_CODE_REGEX.test('UMB-001122')).toBe(true);
  });

  it('T1-CODE-02: PATIENT_CODE_REGEX matches lowercase code umb-xxxxxx case-insensitively', () => {
    expect(PATIENT_CODE_REGEX.test('umb-a1b2c3')).toBe(true);
    expect(PATIENT_CODE_REGEX.test('umb-998877')).toBe(true);
  });

  it('T1-UUID-01: QR_TOKEN_UUID_REGEX matches standard RFC 4122 v4 lowercase UUID', () => {
    expect(QR_TOKEN_UUID_REGEX.test('550e8400-e29b-41d4-a716-446655440000')).toBe(true);
    expect(QR_TOKEN_UUID_REGEX.test('11111111-1111-1111-1111-111111111111')).toBe(true);
  });

  it('T1-UUID-02: QR_TOKEN_UUID_REGEX matches uppercase UUID v4 case-insensitively', () => {
    expect(QR_TOKEN_UUID_REGEX.test('550E8400-E29B-41D4-A716-446655440000')).toBe(true);
  });

  it('T1-PHONE-01: extractPhoneDigits extracts numeric string from US formatted phone', () => {
    expect(extractPhoneDigits('(555) 123-4567')).toBe('5551234567');
    expect(extractPhoneDigits('555-987-6543')).toBe('5559876543');
  });

  it('T1-PHONE-02: extractPhoneDigits extracts numeric string from international dialing format', () => {
    expect(extractPhoneDigits('+91 98765 43210')).toBe('919876543210');
    expect(extractPhoneDigits('+44 20 7946 0958')).toBe('442079460958');
  });

  it('T1-CLASS-01: classifySearchQuery classifies valid patient code and normalizes to uppercase', () => {
    const res = classifySearchQuery('umb-a1b2c3');
    expect(res).toEqual({ type: 'patient_code', sanitized: 'UMB-A1B2C3' });
  });

  it('T1-CLASS-02: classifySearchQuery classifies UUID query and normalizes to lowercase', () => {
    const res = classifySearchQuery('550E8400-E29B-41D4-A716-446655440000');
    expect(res).toEqual({ type: 'qr_token', sanitized: '550e8400-e29b-41d4-a716-446655440000' });
  });

  it('T1-CLASS-03: classifySearchQuery classifies phone query with 7+ digits as phone type', () => {
    const res = classifySearchQuery('(555) 123-4567');
    expect(res).toEqual({ type: 'phone', sanitized: '5551234567' });
  });

  it('T1-CLASS-04: classifySearchQuery classifies clinician name query and cleans SQL wildcards', () => {
    const res = classifySearchQuery('Dr. Sarah Connor');
    expect(res).toEqual({ type: 'name', sanitized: 'Dr. Sarah Connor' });
  });
});

describe('Tier 2: Doctor Actions Pure Logic — Boundaries & Injection Stripping', () => {
  it('T2-ESC-01: strips PostgREST wildcard % and _ characters to prevent wildcard attacks', () => {
    expect(escapeSearchTerm('%admin%')).toBe('admin');
    expect(escapeSearchTerm('user_name')).toBe('username');
    expect(escapeSearchTerm('___%%%')).toBe('');
  });

  it('T2-ESC-02: strips parentheses and commas to prevent filter syntax injection', () => {
    expect(escapeSearchTerm('(select)')).toBe('select');
    expect(escapeSearchTerm('a,b,c')).toBe('abc');
    expect(escapeSearchTerm('%(_attack_,1=1)%')).toBe('attack1=1');
  });

  it('T2-ESC-03: escapes backslashes cleanly for SQL escaping without doubling errors', () => {
    expect(escapeSearchTerm('test\\value')).toBe('test\\\\value');
    expect(escapeSearchTerm('\\')).toBe('\\\\');
  });

  it('T2-ESC-04: returns empty string when query consists solely of stripped characters', () => {
    expect(escapeSearchTerm(' %_(), ')).toBe('');
    expect(escapeSearchTerm('')).toBe('');
    expect(escapeSearchTerm('   ')).toBe('');
  });

  it('T2-CODE-01: PATIENT_CODE_REGEX rejects codes with non-6 character suffixes', () => {
    expect(PATIENT_CODE_REGEX.test('UMB-12345')).toBe(false);
    expect(PATIENT_CODE_REGEX.test('UMB-1234567')).toBe(false);
    expect(PATIENT_CODE_REGEX.test('UMB-')).toBe(false);
  });

  it('T2-CODE-02: PATIENT_CODE_REGEX rejects codes with invalid prefixes', () => {
    expect(PATIENT_CODE_REGEX.test('PAT-123456')).toBe(false);
    expect(PATIENT_CODE_REGEX.test('MED-A1B2C3')).toBe(false);
    expect(PATIENT_CODE_REGEX.test('123456')).toBe(false);
  });

  it('T2-UUID-01: QR_TOKEN_UUID_REGEX rejects truncated, malformed, or injection UUIDs', () => {
    expect(QR_TOKEN_UUID_REGEX.test('550e8400-e29b-41d4-a716-44665544000')).toBe(false);
    expect(QR_TOKEN_UUID_REGEX.test('550e8400e29b41d4a716446655440000')).toBe(false);
    expect(QR_TOKEN_UUID_REGEX.test('550e8400-e29b-41d4-a716-44665544000g')).toBe(false);
  });

  it('T2-PHONE-01: extractPhoneDigits returns empty string for non-numeric queries', () => {
    expect(extractPhoneDigits('John Doe')).toBe('');
    expect(extractPhoneDigits('!@#$%^&*()_+')).toBe('');
  });

  it('T2-CLASS-01: classifySearchQuery returns invalid for query with length < 2 characters', () => {
    expect(classifySearchQuery('')).toEqual({ type: 'invalid', sanitized: '' });
    expect(classifySearchQuery('A')).toEqual({ type: 'invalid', sanitized: '' });
    expect(classifySearchQuery('  A  ')).toEqual({ type: 'invalid', sanitized: '' });
  });

  it('T2-CLASS-02: classifySearchQuery returns invalid for query exceeding 100 characters', () => {
    const longQuery = 'A'.repeat(101);
    expect(classifySearchQuery(longQuery)).toEqual({ type: 'invalid', sanitized: '' });
    expect(classifySearchQuery('A'.repeat(100)).type).not.toBe('invalid');
  });

  it('T2-CLASS-03: classifySearchQuery returns invalid when query strips down to < 2 characters', () => {
    expect(classifySearchQuery('%_,()')).toEqual({ type: 'invalid', sanitized: '' });
    expect(classifySearchQuery(' %A_ ')).toEqual({ type: 'invalid', sanitized: '' });
  });

  it('T2-CLASS-04: mapPatientSearchRow maps emergency_contact details and verification status', () => {
    const mockRow: SearchRow = {
      patient_id: '11111111-1111-1111-1111-111111111111',
      patient_code: 'UMB-ALX001',
      qr_token: '550e8400-e29b-41d4-a716-446655440000',
      age: 34,
      blood_group: 'O+',
      emergency_contact_name: 'Taylor Morgan',
      emergency_contact_phone: '+1-555-0199',
      emergency_contact_relation: 'Spouse',
      accounts: { id: '11111111-1111-1111-1111-111111111111', full_name: 'Alex Morgan', contact_phone: '+1-555-0101' },
      clinical_records: { is_doctor_verified: true },
    };
    const res = mapPatientSearchRow(mockRow);
    expect(res.emergency_contact_name).toBe('Taylor Morgan');
    expect(res.emergency_contact_phone).toBe('+1-555-0199');
    expect(res.is_doctor_verified).toBe(true);
  });
});

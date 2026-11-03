import { describe, it, expect } from 'vitest';
import {
  bloodGroupEnum,
  uuidSchema,
  phoneRegex,
  surgeryYearRegex,
  loginSchema,
  patientSignupSchema,
  doctorSignupSchema,
  spouseDependentSchema,
  patientProfileSchema,
  updateDemographicsSchema,
  emergencyTriageSchema,
} from '@/lib/schemas';

const makePatient = (overrides = {}) => ({
  role: 'patient' as const, email: 'alex@example.test', password: 'password123',
  fullName: 'Alex Morgan', contactPhone: '+1-555-0101', age: 34, bloodGroup: 'O+' as const,
  emergencyContactName: 'Taylor Morgan', emergencyContactPhone: '+1-555-0199', emergencyContactRelation: 'Spouse',
  ...overrides,
});

const makeDoctor = (overrides = {}) => ({
  role: 'doctor' as const, email: 'dr.jenkins@hospital.test', password: 'password123',
  fullName: 'Dr. Sarah Jenkins', contactPhone: '+1-555-0201', medicalLicenseNumber: 'MD-99887',
  specialization: 'Emergency Medicine', ...overrides,
});

describe('Tier 1: Zod Runtime Schemas — Happy-Path Isolation', () => {
  it('T1-BG-01: validates all 8 standard ABO/Rh blood groups', () => {
    const groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'] as const;
    groups.forEach((bg) => expect(bloodGroupEnum.parse(bg)).toBe(bg));
  });

  it('T1-BG-02: validates fallback Unknown blood group', () => {
    expect(bloodGroupEnum.parse('Unknown')).toBe('Unknown');
  });

  it('T1-UUID-01: validates standard RFC 4122 v4 UUID format', () => {
    const validUuid = '550e8400-e29b-41d4-a716-446655440000';
    expect(uuidSchema.parse(validUuid)).toBe(validUuid);
  });

  it('T1-UUID-02: validates nil UUID format', () => {
    const nilUuid = '00000000-0000-0000-0000-000000000000';
    expect(uuidSchema.parse(nilUuid)).toBe(nilUuid);
  });

  it('T1-PHONE-01: validates standard domestic and international formats', () => {
    ['1234567890', '+919876543210', '(555) 123-4567', '555-123-4567'].forEach((p) => {
      expect(phoneRegex.test(p)).toBe(true);
    });
  });

  it('T1-YEAR-01: validates surgical years across 20th and 21st centuries', () => {
    ['1900', '1999', '2000', '2024', '2099'].forEach((y) => {
      expect(surgeryYearRegex.test(y)).toBe(true);
    });
  });

  it('T1-LOGIN-01: validates valid email and password format, lowercasing email', () => {
    const res = loginSchema.parse({ email: 'PATIENT@Example.Test', password: 'password123' });
    expect(res.email).toBe('patient@example.test');
  });

  it('T1-LOGIN-02: trims leading and trailing whitespace from email input', () => {
    const res = loginSchema.parse({ email: '  doctor@clinic.org  ', password: 'password123' });
    expect(res.email).toBe('doctor@clinic.org');
  });

  it('T1-PATIENT-SIGNUP-01: validates complete patient signup payload', () => {
    const res = patientSignupSchema.parse(makePatient());
    expect(res.role).toBe('patient');
    expect(res.age).toBe(34);
  });

  it('T1-PATIENT-SIGNUP-02: coerces numeric string age to integer', () => {
    const res = patientSignupSchema.parse(makePatient({ age: '45' }));
    expect(res.age).toBe(45);
  });

  it('T1-DOCTOR-SIGNUP-01: validates complete doctor signup payload with license', () => {
    const res = doctorSignupSchema.parse(makeDoctor());
    expect(res.role).toBe('doctor');
    expect(res.medicalLicenseNumber).toBe('MD-99887');
  });

  it('T1-DEMOGRAPHICS-01: validates demographics update payload', () => {
    const res = updateDemographicsSchema.parse({
      fullName: 'Alex Morgan Updated', contactPhone: '+1-555-0102', age: 35, bloodGroup: 'O+',
      residentialAddress: '123 Pine St, Suite 4B', spouseDependents: [{ fullName: 'Child Morgan', relation: 'Child' }],
    });
    expect(res.fullName).toBe('Alex Morgan Updated');
    expect(res.spouseDependents?.length).toBe(1);
  });

  it('T1-PROFILE-01: validates patientProfileSchema with default empty dependents array', () => {
    const res = patientProfileSchema.parse({
      age: 28, bloodGroup: 'B-', residentialAddress: null,
      emergencyContactName: 'Jordan Lee', emergencyContactPhone: '+1-555-0177', emergencyContactRelation: 'Sibling',
    });
    expect(res.spouseDependents).toEqual([]);
  });

  it('T1-DEPENDENT-01: validates spouseDependentSchema with name and relation', () => {
    const res = spouseDependentSchema.parse({ fullName: 'Sarah Connor', relation: 'Spouse', age: 32 });
    expect(res.fullName).toBe('Sarah Connor');
    expect(res.relation).toBe('Spouse');
  });

  it('T1-TRIAGE-01: validates full emergency triage record without prohibited fields', () => {
    const res = emergencyTriageSchema.parse({
      full_name: 'David Kim', age: 48, blood_group: 'AB-',
      emergency_contact_name: 'Helen Kim', emergency_contact_phone: '+1-555-0399', emergency_contact_relation: 'Spouse',
      medical_conditions: ['Hypertension'], current_medication: [{ name: 'Lisinopril', dosage: '10mg', frequency: 'daily' }],
      allergies: ['Penicillin'], is_doctor_verified: true, updated_at: '2026-11-01T12:00:00Z',
    });
    expect(res.full_name).toBe('David Kim');
    expect(res.is_doctor_verified).toBe(true);
  });
});

describe('Tier 2: Zod Runtime Schemas — Boundaries & Corner Cases', () => {
  it('T2-BG-01: rejects invalid blood group strings', () => {
    ['C+', 'Rh+', 'O', 'AB', 'Unknowns', ''].forEach((bg) => {
      expect(() => bloodGroupEnum.parse(bg)).toThrow();
    });
  });

  it('T2-UUID-01: rejects malformed, truncated, and path-traversal UUIDs', () => {
    ['550e8400-e29b-41d4-a716', '550e8400-e29b-41d4-a716-44665544000z', '../etc/passwd'].forEach((u) => {
      expect(() => uuidSchema.parse(u)).toThrow();
    });
  });

  it('T2-PHONE-01: enforces 7-digit minimum and 20-character maximum phone bounds', () => {
    expect(() => patientSignupSchema.parse(makePatient({ contactPhone: '12345' }))).toThrow();
    expect(() => patientSignupSchema.parse(makePatient({ contactPhone: '1'.repeat(21) }))).toThrow();
  });

  it('T2-YEAR-01: enforces 1900-2099 surgical year boundaries', () => {
    ['1899', '2100', '99', '202', 'abcd'].forEach((y) => {
      expect(surgeryYearRegex.test(y)).toBe(false);
    });
  });

  it('T2-AGE-01: enforces 0 to 130 age boundary in patient signup', () => {
    expect(() => patientSignupSchema.parse(makePatient({ age: -1 }))).toThrow();
    expect(() => patientSignupSchema.parse(makePatient({ age: 131 }))).toThrow();
  });

  it('T2-AGE-02: rejects non-integer float ages', () => {
    expect(() => patientSignupSchema.parse(makePatient({ age: 34.5 }))).toThrow();
  });

  it('T2-LOGIN-01: rejects password shorter than 8 characters', () => {
    expect(() => loginSchema.parse({ email: 'valid@test.org', password: 'short' })).toThrow();
  });

  it('T2-LOGIN-02: rejects password exceeding 128 characters', () => {
    expect(() => loginSchema.parse({ email: 'valid@test.org', password: 'a'.repeat(129) })).toThrow();
  });

  it('T2-LOGIN-03: rejects email exceeding RFC 5321 limit of 254 characters', () => {
    const longEmail = `${'a'.repeat(250)}@test.com`;
    expect(() => loginSchema.parse({ email: longEmail, password: 'password123' })).toThrow();
  });

  it('T2-LOGIN-04: rejects invalid email format without @', () => {
    expect(() => loginSchema.parse({ email: 'invalid-email', password: 'password123' })).toThrow();
  });

  it('T2-PATIENT-NAME-01: rejects full name shorter than 2 characters', () => {
    expect(() => patientSignupSchema.parse(makePatient({ fullName: 'A' }))).toThrow();
  });

  it('T2-DOCTOR-LIC-01: rejects medical license shorter than 3 characters', () => {
    expect(() => doctorSignupSchema.parse(makeDoctor({ medicalLicenseNumber: 'MD' }))).toThrow();
  });

  it('T2-N1-PRIVACY-01: rejects residential_address on emergency triage payload (Invariant N1)', () => {
    const dirty = {
      full_name: 'Priya Sharma', age: 29, blood_group: 'B+',
      emergency_contact_name: 'Aarav Sharma', emergency_contact_phone: '+91-98765-43210', emergency_contact_relation: 'Spouse',
      medical_conditions: [], current_medication: [], allergies: [], is_doctor_verified: false,
      residential_address: '45 Lotus Boulevard, Bangalore',
    };
    expect(() => emergencyTriageSchema.parse(dirty)).toThrow('Privacy violation: residential_address prohibited');
  });

  it('T2-N1-PRIVACY-02: rejects spouse_dependents on emergency triage payload (Invariant N1)', () => {
    const dirty = {
      full_name: 'Priya Sharma', age: 29, blood_group: 'B+',
      emergency_contact_name: 'Aarav Sharma', emergency_contact_phone: '+91-98765-43210', emergency_contact_relation: 'Spouse',
      medical_conditions: [], current_medication: [], allergies: [], is_doctor_verified: false,
      spouse_dependents: [{ fullName: 'Child Sharma' }],
    };
    expect(() => emergencyTriageSchema.parse(dirty)).toThrow('Privacy violation: spouse_dependents prohibited');
  });

  it('T2-DEPENDENTS-01: enforces maximum 10 dependents ceiling in patient profile', () => {
    const elevenDeps = Array.from({ length: 11 }, (_, i) => ({ fullName: `Child ${i}`, relation: 'Child' }));
    expect(() => patientProfileSchema.parse({
      age: 40, bloodGroup: 'O+', residentialAddress: null,
      emergencyContactName: 'Contact', emergencyContactPhone: '+1-555-0199', emergencyContactRelation: 'Spouse',
      spouseDependents: elevenDeps,
    })).toThrow();
  });
});

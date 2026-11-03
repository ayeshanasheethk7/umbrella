import { describe, it, expect } from 'vitest';
import {
  medicationItemSchema,
  surgeryItemSchema,
  clinicalRecordSchema,
  baselineSubmissionSchema,
  doctorClinicalRecordUpdateSchema,
  patientSearchQuerySchema,
  patientSearchObjectSchema,
  createAppointmentSchema,
  updateAppointmentStatusSchema,
  appointmentStatusEnum,
} from '@/lib/schemas';

describe('Tier 1: Clinical Domain Schemas — Happy-Path Isolation', () => {
  it('T1-MED-01: validates medicationItemSchema with name, dosage, and frequency', () => {
    const med = { name: 'Amoxicillin', dosage: '500mg', frequency: 'Three times daily' };
    const res = medicationItemSchema.parse(med);
    expect(res.name).toBe('Amoxicillin');
    expect(res.dosage).toBe('500mg');
  });

  it('T1-MED-02: validates medicationItemSchema with optional notes', () => {
    const med = { name: 'Metformin', dosage: '850mg', frequency: 'Twice daily', notes: 'Take with meals' };
    const res = medicationItemSchema.parse(med);
    expect(res.notes).toBe('Take with meals');
  });

  it('T1-SURG-01: validates surgeryItemSchema with procedure and 4-digit year', () => {
    const surg = { procedure: 'Appendectomy', year: '2015' };
    const res = surgeryItemSchema.parse(surg);
    expect(res.procedure).toBe('Appendectomy');
    expect(res.year).toBe('2015');
  });

  it('T1-SURG-02: validates surgeryItemSchema with numeric year coerced to string', () => {
    const surg = { procedure: 'Knee Arthroscopy', year: 2021 };
    const res = surgeryItemSchema.parse(surg);
    expect(res.year).toBe('2021');
  });

  it('T1-CLINICAL-01: validates clinicalRecordSchema with default empty arrays', () => {
    const res = clinicalRecordSchema.parse({});
    expect(res.medicalConditions).toEqual([]);
    expect(res.currentMedication).toEqual([]);
    expect(res.previousSurgeries).toEqual([]);
    expect(res.allergies).toEqual([]);
    expect(res.isDoctorVerified).toBe(false);
  });

  it('T1-CLINICAL-02: validates clinicalRecordSchema with verified status and doctor id', () => {
    const res = clinicalRecordSchema.parse({
      isDoctorVerified: true,
      verifiedByDoctorId: '11111111-1111-1111-1111-111111111111',
      medicalConditions: ['Asthma'],
    });
    expect(res.isDoctorVerified).toBe(true);
    expect(res.verifiedByDoctorId).toBe('11111111-1111-1111-1111-111111111111');
  });

  it('T1-BASELINE-01: validates baselineSubmissionSchema with conditions and allergies lists', () => {
    const res = baselineSubmissionSchema.parse({
      conditions: ['Hypertension', 'Type 2 Diabetes'],
      allergies: ['Penicillin', 'Sulfa drugs'],
    });
    expect(res.conditions.length).toBe(2);
    expect(res.allergies.length).toBe(2);
  });

  it('T1-BASELINE-02: validates baselineSubmissionSchema with empty arrays', () => {
    const res = baselineSubmissionSchema.parse({ conditions: [], allergies: [] });
    expect(res.conditions).toEqual([]);
    expect(res.allergies).toEqual([]);
  });

  it('T1-DOC-UPDATE-01: validates doctorClinicalRecordUpdateSchema with optimistic concurrency timestamp', () => {
    const res = doctorClinicalRecordUpdateSchema.parse({
      patient_id: '11111111-1111-1111-1111-111111111111',
      expectedUpdatedAt: '2026-11-01T12:00:00.000Z',
      medical_conditions: ['Atrial Fibrillation'],
      current_medication: [{ name: 'Warfarin', dosage: '5mg', frequency: 'daily' }],
      previous_surgeries: [{ procedure: 'Ablation', year: '2022' }],
      allergies: ['Aspirin'],
    });
    expect(res.patient_id).toBe('11111111-1111-1111-1111-111111111111');
    expect(res.expectedUpdatedAt).toBe('2026-11-01T12:00:00.000Z');
  });

  it('T1-SEARCH-01: validates patientSearchQuerySchema with valid query string', () => {
    expect(patientSearchQuerySchema.parse('Jane Doe')).toBe('Jane Doe');
    expect(patientSearchQuerySchema.parse('UMB-ALX001')).toBe('UMB-ALX001');
  });

  it('T1-SEARCH-OBJ-01: validates patientSearchObjectSchema with q parameter', () => {
    const res = patientSearchObjectSchema.parse({ q: 'UMB-PRY002' });
    expect(res.q).toBe('UMB-PRY002');
  });

  it('T1-APPT-STATUS-01: validates all 3 valid appointment statuses', () => {
    expect(appointmentStatusEnum.parse('scheduled')).toBe('scheduled');
    expect(appointmentStatusEnum.parse('completed')).toBe('completed');
    expect(appointmentStatusEnum.parse('cancelled')).toBe('cancelled');
  });

  it('T1-CREATE-APPT-01: validates createAppointmentSchema with valid ISO datetime and reason', () => {
    const res = createAppointmentSchema.parse({
      patient_id: '11111111-1111-1111-1111-111111111111',
      scheduled_at: '2026-11-15T09:30:00.000Z',
      reason: 'Routine Cardiology Follow-up',
      clinical_notes: 'Review ECG results',
    });
    expect(res.patient_id).toBe('11111111-1111-1111-1111-111111111111');
    expect(res.reason).toBe('Routine Cardiology Follow-up');
  });

  it('T1-UPDATE-APPT-01: validates updateAppointmentStatusSchema with status and notes', () => {
    const res = updateAppointmentStatusSchema.parse({
      appointment_id: '22222222-2222-2222-2222-222222222222',
      status: 'completed',
      clinical_notes: 'Consultation concluded successfully.',
    });
    expect(res.status).toBe('completed');
  });
});

describe('Tier 2: Clinical Domain Schemas — Boundaries & Invariants', () => {
  it('T2-MED-01: rejects medicationItemSchema with empty name', () => {
    expect(() => medicationItemSchema.parse({ name: '', dosage: '10mg', frequency: 'daily' })).toThrow();
  });

  it('T2-MED-02: rejects medicationItemSchema with empty dosage', () => {
    expect(() => medicationItemSchema.parse({ name: 'Aspirin', dosage: '', frequency: 'daily' })).toThrow();
  });

  it('T2-MED-03: rejects medicationItemSchema with empty frequency', () => {
    expect(() => medicationItemSchema.parse({ name: 'Aspirin', dosage: '81mg', frequency: '' })).toThrow();
  });

  it('T2-SURG-01: rejects surgeryItemSchema with empty procedure', () => {
    expect(() => surgeryItemSchema.parse({ procedure: '', year: '2020' })).toThrow();
  });

  it('T2-SURG-02: rejects surgeryItemSchema with year out of 1900-2099 bounds', () => {
    expect(() => surgeryItemSchema.parse({ procedure: 'Surgery', year: '1850' })).toThrow();
    expect(() => surgeryItemSchema.parse({ procedure: 'Surgery', year: '2105' })).toThrow();
  });

  it('T2-BASELINE-01: enforces maximum 50 conditions ceiling in baselineSubmissionSchema', () => {
    const fiftyOne = Array.from({ length: 51 }, (_, i) => `Condition ${i}`);
    expect(() => baselineSubmissionSchema.parse({ conditions: fiftyOne, allergies: [] })).toThrow();
  });

  it('T2-BASELINE-02: enforces maximum 50 allergies ceiling in baselineSubmissionSchema', () => {
    const fiftyOne = Array.from({ length: 51 }, (_, i) => `Allergy ${i}`);
    expect(() => baselineSubmissionSchema.parse({ conditions: [], allergies: fiftyOne })).toThrow();
  });

  it('T2-DOC-UPDATE-01: rejects doctorClinicalRecordUpdateSchema with missing or empty expectedUpdatedAt', () => {
    expect(() => doctorClinicalRecordUpdateSchema.parse({
      patient_id: '11111111-1111-1111-1111-111111111111',
      expectedUpdatedAt: '',
      medical_conditions: [],
    })).toThrow();
  });

  it('T2-DOC-UPDATE-02: enforces maximum 50 conditions ceiling in doctor update schema', () => {
    const fiftyOne = Array.from({ length: 51 }, (_, i) => `Condition ${i}`);
    expect(() => doctorClinicalRecordUpdateSchema.parse({
      patient_id: '11111111-1111-1111-1111-111111111111',
      expectedUpdatedAt: '2026-11-01T12:00:00Z',
      medical_conditions: fiftyOne,
    })).toThrow();
  });

  it('T2-SEARCH-01: rejects patientSearchQuerySchema shorter than 2 characters', () => {
    expect(() => patientSearchQuerySchema.parse('A')).toThrow();
    expect(() => patientSearchQuerySchema.parse('')).toThrow();
  });

  it('T2-SEARCH-02: rejects patientSearchQuerySchema exceeding 100 characters', () => {
    expect(() => patientSearchQuerySchema.parse('A'.repeat(101))).toThrow();
  });

  it('T2-APPT-ISO-01: rejects invalid non-ISO datetime format in createAppointmentSchema', () => {
    expect(() => createAppointmentSchema.parse({
      patient_id: '11111111-1111-1111-1111-111111111111',
      scheduled_at: 'tomorrow morning',
      reason: 'General consult',
    })).toThrow();
  });

  it('T2-APPT-REASON-01: rejects appointment reason shorter than 2 characters', () => {
    expect(() => createAppointmentSchema.parse({
      patient_id: '11111111-1111-1111-1111-111111111111',
      scheduled_at: '2026-11-20T10:00:00.000Z',
      reason: 'A',
    })).toThrow();
  });

  it('T2-APPT-STATUS-01: rejects arbitrary invalid status transition strings', () => {
    expect(() => appointmentStatusEnum.parse('pending')).toThrow();
    expect(() => appointmentStatusEnum.parse('in-progress')).toThrow();
    expect(() => appointmentStatusEnum.parse('')).toThrow();
  });
});

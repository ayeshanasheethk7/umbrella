import type { BloodGroup } from '@/lib/supabase/types';

export type SearchQueryType = 'patient_code' | 'qr_token' | 'phone' | 'name' | 'invalid';
export const PATIENT_CODE_REGEX = /^UMB-[A-Za-z0-9]{6}$/i;
export const QR_TOKEN_UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function escapeSearchTerm(t: string): string {
  return (t || '').replace(/\\/g, '\\\\').replace(/[%_(),]/g, '').trim();
}

export function extractPhoneDigits(query: string): string {
  return (query || '').replace(/\D/g, '');
}

export function classifySearchQuery(rawQuery: string): { type: SearchQueryType; sanitized: string } {
  const q = (rawQuery || '').trim();
  if (q.length < 2 || q.length > 100) return { type: 'invalid', sanitized: '' };
  if (PATIENT_CODE_REGEX.test(q)) return { type: 'patient_code', sanitized: q.toUpperCase() };
  if (QR_TOKEN_UUID_REGEX.test(q)) return { type: 'qr_token', sanitized: q.toLowerCase() };
  const d = extractPhoneDigits(q);
  if (d.length >= 7) return { type: 'phone', sanitized: d };
  const cleanTerm = escapeSearchTerm(q);
  return cleanTerm.length < 2 ? { type: 'invalid', sanitized: '' } : { type: 'name', sanitized: cleanTerm };
}

export interface PatientBase {
  patient_id: string;
  patient_code: string;
  qr_token: string;
  age: number;
  blood_group: BloodGroup;
  emergency_contact_name: string;
  emergency_contact_phone: string;
  emergency_contact_relation: string;
}

export interface PatientSearchResult extends PatientBase {
  full_name: string;
  contact_phone: string;
  is_doctor_verified: boolean;
}

export interface SearchRow extends PatientBase {
  accounts: { id?: string; full_name: string; contact_phone: string } | null;
  clinical_records: { is_doctor_verified: boolean } | { is_doctor_verified: boolean }[] | null;
}

export const mapRow = (r: SearchRow): PatientSearchResult => ({
  patient_id: r.patient_id,
  patient_code: r.patient_code,
  qr_token: r.qr_token,
  full_name: r.accounts?.full_name || 'Unknown Patient',
  age: r.age,
  blood_group: r.blood_group,
  contact_phone: r.accounts?.contact_phone || '',
  emergency_contact_name: r.emergency_contact_name,
  emergency_contact_phone: r.emergency_contact_phone,
  emergency_contact_relation: r.emergency_contact_relation,
  is_doctor_verified: Boolean(
    Array.isArray(r.clinical_records)
      ? r.clinical_records[0]?.is_doctor_verified
      : r.clinical_records?.is_doctor_verified
  ),
});

export const mapPatientSearchRow = mapRow;

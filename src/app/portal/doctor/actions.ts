'use server';

import { revalidatePath } from 'next/cache';
import { createClient } from '@/lib/supabase/server';
import { createAppointmentSchema, updateAppointmentStatusSchema, doctorClinicalRecordUpdateSchema, type AppointmentStatusType } from '@/lib/schemas';
import type { AccountRow, BloodGroup, ClinicalRecordRow, AppointmentRow, Json } from '@/lib/supabase/types';

export type ActionResponse<T = unknown> = { ok: true; data: T } | { ok: false; error: string; conflict?: boolean };

type DocAuth =
  | { ok: true; data: { user: { id: string; email?: string }; account: AccountRow } }
  | { ok: false; error: string; code?: 'UNAUTHORIZED' | 'FORBIDDEN' | 'PENDING' };

const fail = (m: string, code?: 'UNAUTHORIZED' | 'FORBIDDEN' | 'PENDING') => ({ ok: false as const, error: m, code });
const errFail = (e: unknown, d: string) => fail(e instanceof Error ? e.message : d);

export async function verifyApprovedDoctor(): Promise<DocAuth> {
  const supabase = createClient();
  const { data: { user }, error: authErr } = await supabase.auth.getUser();
  if (!user || authErr) return fail('Unauthorized', 'UNAUTHORIZED');
  const { data: acc } = await supabase.from('accounts').select('*').eq('id', user.id).single();
  if (!acc || acc.role !== 'doctor') return fail('Forbidden', 'FORBIDDEN');
  if (acc.doctor_status !== 'approved') {
    return fail(acc.doctor_status === 'pending' ? 'Account Pending Approval' : 'Declined', 'PENDING');
  }
  return { ok: true, data: { user: { id: user.id, email: user.email }, account: acc as AccountRow } };
}

function escapeSearchTerm(t: string): string {
  return (t || '').replace(/\\/g, '\\\\').replace(/[%_(),]/g, '').trim();
}

type SearchQueryType = 'patient_code' | 'qr_token' | 'phone' | 'name' | 'invalid';
const PATIENT_CODE_REGEX = /^UMB-[A-Za-z0-9]{6}$/i;
const QR_TOKEN_UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function extractPhoneDigits(query: string): string {
  return (query || '').replace(/\D/g, '');
}

function classifySearchQuery(rawQuery: string): { type: SearchQueryType; sanitized: string } {
  const q = (rawQuery || '').trim();
  if (q.length < 2 || q.length > 100) return { type: 'invalid', sanitized: '' };
  if (PATIENT_CODE_REGEX.test(q)) return { type: 'patient_code', sanitized: q.toUpperCase() };
  if (QR_TOKEN_UUID_REGEX.test(q)) return { type: 'qr_token', sanitized: q.toLowerCase() };
  const d = extractPhoneDigits(q);
  if (d.length >= 7) return { type: 'phone', sanitized: d };
  const cleanTerm = escapeSearchTerm(q);
  return cleanTerm.length < 2 ? { type: 'invalid', sanitized: '' } : { type: 'name', sanitized: cleanTerm };
}

interface PatientBase {
  patient_id: string; patient_code: string; qr_token: string; age: number; blood_group: BloodGroup;
  emergency_contact_name: string; emergency_contact_phone: string; emergency_contact_relation: string;
}
export interface PatientSearchResult extends PatientBase {
  full_name: string; contact_phone: string; is_doctor_verified: boolean;
}
export interface SearchRow extends PatientBase {
  accounts: { id?: string; full_name: string; contact_phone: string } | null;
  clinical_records: { is_doctor_verified: boolean } | { is_doctor_verified: boolean }[] | null;
}
const mapRow = (r: SearchRow): PatientSearchResult => ({
  patient_id: r.patient_id, patient_code: r.patient_code, qr_token: r.qr_token,
  full_name: r.accounts?.full_name || 'Unknown Patient', age: r.age, blood_group: r.blood_group,
  contact_phone: r.accounts?.contact_phone || '', emergency_contact_name: r.emergency_contact_name,
  emergency_contact_phone: r.emergency_contact_phone, emergency_contact_relation: r.emergency_contact_relation,
  is_doctor_verified: Boolean(Array.isArray(r.clinical_records) ? r.clinical_records[0]?.is_doctor_verified : r.clinical_records?.is_doctor_verified),
});

const SF = 'patient_id,patient_code,qr_token,age,blood_group,emergency_contact_name,emergency_contact_phone,emergency_contact_relation,accounts!inner(id,full_name,contact_phone),clinical_records(is_doctor_verified)';

export async function searchPatientsAction(rawQuery: string): Promise<ActionResponse<PatientSearchResult[]>> {
  try {
    const auth = await verifyApprovedDoctor();
    if (!auth.ok) return auth;
    if ((rawQuery || '').trim().length > 100) return fail('Query exceeds 100 characters.');
    const cls = classifySearchQuery(rawQuery);
    if (cls.type === 'invalid') return { ok: true, data: [] };

    const supabase = createClient();
    const qp = () => supabase.from('patient_profiles').select(SF);
    let res;
    if (cls.type === 'patient_code') res = await qp().ilike('patient_code', cls.sanitized).limit(20);
    else if (cls.type === 'qr_token') {
      res = await qp().eq('qr_token', cls.sanitized).limit(20);
      if (!res.data || res.data.length === 0) res = await qp().eq('patient_id', cls.sanitized).limit(20);
    }
    else if (cls.type === 'phone') {
      const [acc, em] = await Promise.all([
        qp().ilike('accounts.contact_phone', `%${cls.sanitized}%`).limit(20),
        qp().ilike('emergency_contact_phone', `%${cls.sanitized}%`).limit(20),
      ]);
      if (acc.error) throw acc.error;
      if (em.error) throw em.error;
      const m = new Map<string, PatientSearchResult>();
      ([...(acc.data || []), ...(em.data || [])] as unknown as SearchRow[]).forEach((r) => m.set(r.patient_id, mapRow(r)));
      return { ok: true, data: Array.from(m.values()).slice(0, 20) };
    } else {
      res = await qp().ilike('accounts.full_name', `%${cls.sanitized}%`).limit(20);
    }
    if (res.error) throw res.error;
    return { ok: true, data: ((res.data || []) as unknown as SearchRow[]).map(mapRow) };
  } catch (err) {
    return errFail(err, 'Search failed.');
  }
}

export interface DetailedPatientRecord {
  profile: PatientSearchResult; clinical: ClinicalRecordRow;
}

export async function getPatientClinicalRecordAction(patientId: string): Promise<ActionResponse<DetailedPatientRecord>> {
  try {
    const auth = await verifyApprovedDoctor();
    if (!auth.ok) return auth;
    const [p, c] = await Promise.all([
      createClient().from('patient_profiles').select(SF).eq('patient_id', patientId).single(),
      createClient().from('clinical_records').select('*').eq('patient_id', patientId).single(),
    ]);
    if (p.error || !p.data) return fail('Patient not found.');
    if (c.error || !c.data) return fail('Record not found.');
    return { ok: true, data: { profile: mapRow(p.data as unknown as SearchRow), clinical: c.data as ClinicalRecordRow } };
  } catch (err) {
    return errFail(err, 'Retrieve patient failed.');
  }
}

export async function updateClinicalRecordAction(rawData: unknown): Promise<ActionResponse<ClinicalRecordRow>> {
  try {
    const auth = await verifyApprovedDoctor();
    if (!auth.ok) return auth;
    const p = doctorClinicalRecordUpdateSchema.safeParse(rawData);
    if (!p.success) return fail(p.error.errors[0]?.message || 'Invalid clinical update.');
    const { patient_id: pid, expectedUpdatedAt, medical_conditions: mc, current_medication: cm, previous_surgeries: ps, allergies: al } = p.data;
    const sb = createClient();
    const { data, error } = await sb.from('clinical_records').update({
      medical_conditions: mc, current_medication: cm as unknown as Json,
      previous_surgeries: ps as unknown as Json, allergies: al,
    }).eq('patient_id', pid).eq('updated_at', expectedUpdatedAt).select('*').maybeSingle();
    if (error) return fail(error.message);
    if (!data) {
      const { data: ex } = await sb.from('clinical_records').select('updated_at').eq('patient_id', pid).maybeSingle();
      if (ex && ex.updated_at !== expectedUpdatedAt) {
        return { ok: false, conflict: true, error: 'Clinical Record Conflict: Stale record timestamp. Please reload.' };
      }
      return fail('Record not found.');
    }
    revalidatePath('/portal/doctor'); revalidatePath('/portal/patient');
    return { ok: true, data: data as ClinicalRecordRow };
  } catch (err) {
    return errFail(err, 'Clinical update failed.');
  }
}

export interface DoctorAppointmentListItem {
  id: string; patient_id: string; scheduled_at: string; status: AppointmentStatusType;
  reason: string; clinical_notes: string | null; created_at: string;
  patient: { fullName: string; contactPhone: string; patientCode: string; age: number; bloodGroup: BloodGroup };
}

type PP = { patient_code: string; age: number; blood_group: string };
interface ApptRow extends Omit<DoctorAppointmentListItem, 'patient' | 'status'> {
  status: string;
  accounts: { full_name: string; contact_phone: string; patient_profiles: PP | PP[] | null } | null;
}

const AQ = 'id,patient_id,scheduled_at,status,reason,clinical_notes,created_at,accounts!appointments_patient_id_fkey(full_name,contact_phone,patient_profiles(patient_code,age,blood_group))';

export async function getDoctorAppointmentsAction(opt?: { status?: AppointmentStatusType; patientId?: string }): Promise<ActionResponse<DoctorAppointmentListItem[]>> {
  try {
    const auth = await verifyApprovedDoctor();
    if (!auth.ok) return auth;
    let q = createClient().from('appointments').select(AQ).eq('doctor_id', auth.data.user.id);
    if (opt?.status) q = q.eq('status', opt.status);
    if (opt?.patientId) q = q.eq('patient_id', opt.patientId);
    const { data, error } = await q.order('scheduled_at', { ascending: true });
    if (error) throw error;
    return { ok: true, data: ((data || []) as unknown as ApptRow[]).map((r) => {
      const a = r.accounts, p = Array.isArray(a?.patient_profiles) ? a.patient_profiles[0] : a?.patient_profiles;
      return {
        id: r.id, patient_id: r.patient_id, scheduled_at: r.scheduled_at, status: r.status as AppointmentStatusType,
        reason: r.reason, clinical_notes: r.clinical_notes, created_at: r.created_at,
        patient: { fullName: a?.full_name || 'Unknown Patient', contactPhone: a?.contact_phone || '', patientCode: p?.patient_code || 'N/A', age: p?.age ?? 0, bloodGroup: (p?.blood_group || 'Unknown') as BloodGroup },
      };
    }) };
  } catch (err) {
    return errFail(err, 'Appointments query failed.');
  }
}

export async function createAppointmentAction(rawData: unknown): Promise<ActionResponse<AppointmentRow>> {
  try {
    const auth = await verifyApprovedDoctor();
    if (!auth.ok) return auth;
    const p = createAppointmentSchema.safeParse(rawData);
    if (!p.success) return fail(p.error.errors[0]?.message || 'Invalid appointment input.');
    const { patient_id, scheduled_at, reason, clinical_notes } = p.data;
    const { data, error } = await createClient().from('appointments').insert({
      doctor_id: auth.data.user.id, patient_id, scheduled_at, status: 'scheduled', reason, clinical_notes: clinical_notes || null,
    }).select('*').single();
    if (error) return fail(error.message);
    revalidatePath('/portal/doctor');
    return { ok: true, data: data as AppointmentRow };
  } catch (err) {
    return errFail(err, 'Appointment creation failed.');
  }
}

export async function updateAppointmentStatusAction(rawData: unknown): Promise<ActionResponse<AppointmentRow>> {
  try {
    const auth = await verifyApprovedDoctor();
    if (!auth.ok) return auth;
    const p = updateAppointmentStatusSchema.safeParse(rawData);
    if (!p.success) return fail(p.error.errors[0]?.message || 'Invalid status.');
    const { appointment_id, status, clinical_notes } = p.data;
    const pl: { status: AppointmentStatusType; clinical_notes?: string | null } = { status };
    if (clinical_notes !== undefined) pl.clinical_notes = clinical_notes;
    const { data, error } = await createClient().from('appointments').update(pl).eq('id', appointment_id).select('*').single();
    if (error) return fail(error.message);
    revalidatePath('/portal/doctor');
    return { ok: true, data: data as AppointmentRow };
  } catch (err) {
    return errFail(err, 'Status update failed.');
  }
}

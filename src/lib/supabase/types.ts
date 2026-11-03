/**
 * Umbrella Database TypeScript Definitions
 * Interface contracts conforming to Supabase SSR (@supabase/supabase-js, @supabase/ssr)
 * Database schema: public.accounts, public.patient_profiles, public.clinical_records, public.appointments
 * Strictly typed per AGENTS.md N10 (strict typing, strict nullability).
 */

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type UserRole = 'patient' | 'doctor';
export type DoctorStatus = 'pending' | 'approved' | 'rejected';
export type AppointmentStatus = 'scheduled' | 'completed' | 'cancelled';

export type BloodGroup =
  | 'A+'
  | 'A-'
  | 'B+'
  | 'B-'
  | 'AB+'
  | 'AB-'
  | 'O+'
  | 'O-'
  | 'Unknown';

/**
 * Structured schema for spouse / dependents entry (max 10 entries)
 */
export interface SpouseDependent {
  name: string;
  relation: string;
  age?: number;
  phone?: string;
}

/**
 * Structured schema for medication entry
 */
export interface MedicationItem {
  name: string;
  dosage: string;
  frequency: string;
  prescribed_by?: string;
}

/**
 * Structured schema for previous surgery entry
 */
export interface SurgeryItem {
  procedure: string;
  year: number | string;
  notes?: string;
}

/**
 * Whitelist payload returned strictly by public.get_emergency_triage_by_token(uuid).
 * Invariant N1: residential_address and spouse_dependents are strictly omitted.
 */
export interface EmergencyTriageData {
  full_name: string;
  contact_phone: string;
  patient_code: string;
  age: number;
  blood_group: BloodGroup;
  emergency_contact_name: string;
  emergency_contact_phone: string;
  emergency_contact_relation: string;
  medical_conditions: string[];
  current_medication: MedicationItem[];
  previous_surgeries: SurgeryItem[];
  allergies: string[];
  last_appointment_date: string | null;
  is_doctor_verified: boolean;
  updated_at: string;
}

export interface Database {
  public: {
    Tables: {
      accounts: {
        Row: {
          id: string;
          email: string;
          role: UserRole;
          full_name: string;
          contact_phone: string;
          medical_license_number: string | null;
          specialization: string | null;
          doctor_status: DoctorStatus | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id: string;
          email: string;
          role?: UserRole;
          full_name: string;
          contact_phone?: string;
          medical_license_number?: string | null;
          specialization?: string | null;
          doctor_status?: DoctorStatus | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          email?: string;
          role?: UserRole;
          full_name?: string;
          contact_phone?: string;
          medical_license_number?: string | null;
          specialization?: string | null;
          doctor_status?: DoctorStatus | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [];
      };
      patient_profiles: {
        Row: {
          patient_id: string;
          patient_code: string;
          qr_token: string;
          age: number;
          blood_group: BloodGroup;
          emergency_contact_name: string;
          emergency_contact_phone: string;
          emergency_contact_relation: string;
          spouse_dependents: Json;
          residential_address: string;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          patient_id: string;
          patient_code?: string;
          qr_token?: string;
          age?: number;
          blood_group?: BloodGroup;
          emergency_contact_name?: string;
          emergency_contact_phone?: string;
          emergency_contact_relation?: string;
          spouse_dependents?: Json;
          residential_address?: string;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          patient_id?: string;
          patient_code?: string;
          qr_token?: string;
          age?: number;
          blood_group?: BloodGroup;
          emergency_contact_name?: string;
          emergency_contact_phone?: string;
          emergency_contact_relation?: string;
          spouse_dependents?: Json;
          residential_address?: string;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'patient_profiles_patient_id_fkey';
            columns: ['patient_id'];
            isOneToOne: true;
            referencedRelation: 'accounts';
            referencedColumns: ['id'];
          }
        ];
      };
      clinical_records: {
        Row: {
          patient_id: string;
          medical_conditions: string[];
          current_medication: Json;
          previous_surgeries: Json;
          allergies: string[];
          is_doctor_verified: boolean;
          last_updated_by_doctor_id: string | null;
          last_appointment_date: string | null;
          last_appointment_summary: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          patient_id: string;
          medical_conditions?: string[];
          current_medication?: Json;
          previous_surgeries?: Json;
          allergies?: string[];
          is_doctor_verified?: boolean;
          last_updated_by_doctor_id?: string | null;
          last_appointment_date?: string | null;
          last_appointment_summary?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          patient_id?: string;
          medical_conditions?: string[];
          current_medication?: Json;
          previous_surgeries?: Json;
          allergies?: string[];
          is_doctor_verified?: boolean;
          last_updated_by_doctor_id?: string | null;
          last_appointment_date?: string | null;
          last_appointment_summary?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'clinical_records_patient_id_fkey';
            columns: ['patient_id'];
            isOneToOne: true;
            referencedRelation: 'accounts';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'clinical_records_last_updated_by_doctor_id_fkey';
            columns: ['last_updated_by_doctor_id'];
            isOneToOne: false;
            referencedRelation: 'accounts';
            referencedColumns: ['id'];
          }
        ];
      };
      appointments: {
        Row: {
          id: string;
          patient_id: string;
          doctor_id: string;
          scheduled_at: string;
          status: AppointmentStatus;
          reason: string;
          clinical_notes: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          patient_id: string;
          doctor_id: string;
          scheduled_at: string;
          status?: AppointmentStatus;
          reason: string;
          clinical_notes?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          patient_id?: string;
          doctor_id?: string;
          scheduled_at?: string;
          status?: AppointmentStatus;
          reason?: string;
          clinical_notes?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'appointments_patient_id_fkey';
            columns: ['patient_id'];
            isOneToOne: false;
            referencedRelation: 'accounts';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'appointments_doctor_id_fkey';
            columns: ['doctor_id'];
            isOneToOne: false;
            referencedRelation: 'accounts';
            referencedColumns: ['id'];
          }
        ];
      };
    };
    Views: Record<string, never>;
    Functions: {
      get_emergency_triage_by_token: {
        Args: {
          lookup_token: string;
        };
        Returns: EmergencyTriageData | null;
      };
      is_approved_doctor: {
        Args: Record<PropertyKey, never>;
        Returns: boolean;
      };
      regenerate_qr_token: {
        Args: Record<PropertyKey, never>;
        Returns: string;
      };
      submit_self_reported_baseline: {
        Args: {
          p_conditions: string[];
          p_allergies: string[];
        };
        Returns: void;
      };
    };
    Enums: {
      user_role: UserRole;
    };
    CompositeTypes: Record<string, never>;
  };
}

// Helper utility types for application components and actions
export type Tables<T extends keyof Database['public']['Tables']> =
  Database['public']['Tables'][T]['Row'];
export type TablesInsert<T extends keyof Database['public']['Tables']> =
  Database['public']['Tables'][T]['Insert'];
export type TablesUpdate<T extends keyof Database['public']['Tables']> =
  Database['public']['Tables'][T]['Update'];
export type Enums<T extends keyof Database['public']['Enums']> =
  Database['public']['Enums'][T];

// Domain Aliases
export type AccountRow = Tables<'accounts'>;
export type AccountInsert = TablesInsert<'accounts'>;
export type AccountUpdate = TablesUpdate<'accounts'>;

export type PatientProfileRow = Tables<'patient_profiles'>;
export type PatientProfileInsert = TablesInsert<'patient_profiles'>;
export type PatientProfileUpdate = TablesUpdate<'patient_profiles'>;

export type ClinicalRecordRow = Tables<'clinical_records'>;
export type ClinicalRecordInsert = TablesInsert<'clinical_records'>;
export type ClinicalRecordUpdate = TablesUpdate<'clinical_records'>;

export type AppointmentRow = Tables<'appointments'>;
export type AppointmentInsert = TablesInsert<'appointments'>;
export type AppointmentUpdate = TablesUpdate<'appointments'>;

/**
 * Discriminated union representing the authenticated account state
 */
export type AuthAccountState =
  | { status: 'anonymous' }
  | { status: 'patient'; account: AccountRow; profile: PatientProfileRow }
  | { status: 'doctor_pending'; account: AccountRow }
  | { status: 'doctor_approved'; account: AccountRow }
  | { status: 'doctor_rejected'; account: AccountRow };

import { z } from 'zod';

export const bloodGroupEnum = z.enum(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'Unknown']);
export const uuidSchema = z.string().uuid('Invalid UUID format');
export const phoneRegex = /^\+?[0-9\s\-().]{7,20}$/;
export const surgeryYearRegex = /^(19|20)\d{2}$/;

// Authentication schemas
export const loginSchema = z.object({
  email: z.string().trim().toLowerCase().email('Please enter a valid email address').max(254),
  password: z.string().min(8, 'Password must be at least 8 characters long').max(128),
});
export type LoginInput = z.infer<typeof loginSchema>;

export const patientSignupSchema = z.object({
  role: z.literal('patient').default('patient'),
  email: z.string().trim().toLowerCase().email('Please enter a valid email address').max(254),
  password: z.string().min(8, 'Password must be at least 8 characters long').max(128),
  fullName: z.string().trim().min(2, 'Full name must be at least 2 characters').max(100),
  contactPhone: z.string().trim().regex(phoneRegex, 'Please provide a valid contact phone number'),
  age: z.coerce.number().int('Age must be a whole number').min(0).max(130),
  bloodGroup: bloodGroupEnum,
  emergencyContactName: z.string().trim().min(2, 'Emergency contact name is required').max(100),
  emergencyContactPhone: z.string().trim().regex(phoneRegex, 'Emergency contact phone number must be a valid phone format'),
  emergencyContactRelation: z.string().trim().min(1, 'Relationship to emergency contact is required').max(50),
});
export type PatientSignupInput = z.infer<typeof patientSignupSchema>;

export const doctorSignupSchema = z.object({
  role: z.literal('doctor').default('doctor'),
  email: z.string().trim().toLowerCase().email('Please enter a valid medical email address').max(254),
  password: z.string().min(8, 'Password must be at least 8 characters long').max(128),
  fullName: z.string().trim().min(2, 'Full physician name is required').max(100),
  contactPhone: z.string().trim().regex(phoneRegex, 'Please provide a valid clinic/cell phone number'),
  medicalLicenseNumber: z.string().trim().min(3, 'Official medical license or registration number is required').max(50),
  specialization: z.string().trim().min(2, 'Medical specialization is required').max(100),
});
export type DoctorSignupInput = z.infer<typeof doctorSignupSchema>;

// Profile schemas
export const spouseDependentSchema = z.object({
  name: z.string().trim().min(1, 'Dependent name is required').max(100).optional(),
  fullName: z.string().trim().min(1, 'Dependent name is required').max(100).optional(),
  relation: z.string().trim().min(1, 'Relation is required').max(50),
  age: z.number().int().min(0).max(130).optional(),
  phone: z.string().trim().regex(phoneRegex, 'Phone must be a valid format').optional().or(z.literal('')),
}).refine((data) => data.name || data.fullName, {
  message: 'Dependent name is required',
}).transform((data) => ({
  name: data.name || data.fullName || '',
  fullName: data.fullName || data.name || '',
  relation: data.relation,
  age: data.age,
  phone: data.phone,
}));

export const patientProfileSchema = z.object({
  age: z.coerce.number().int().min(0).max(130),
  bloodGroup: bloodGroupEnum,
  emergencyContactName: z.string().trim().max(100).default(''),
  emergencyContactPhone: z.string().trim().default(''),
  emergencyContactRelation: z.string().trim().max(50).default(''),
  residentialAddress: z.string().trim().max(255).default('').nullable().transform((val) => val || ''),
  spouseDependents: z.array(spouseDependentSchema).max(10).default([]),
});
export type PatientProfileInput = z.infer<typeof patientProfileSchema>;

export const updateDemographicsSchema = z.object({
  fullName: z.string().trim().min(2, 'Full name must be at least 2 characters').max(100),
  contactPhone: z.string().trim().regex(phoneRegex, 'Please provide a valid contact phone number').optional().or(z.literal('')),
  age: z.coerce.number().int('Age must be a whole number').min(0).max(130),
  bloodGroup: bloodGroupEnum,
  emergencyContactName: z.string().trim().max(100).optional().or(z.literal('')),
  emergencyContactPhone: z.string().trim().optional().or(z.literal('')),
  emergencyContactRelation: z.string().trim().max(50).optional().or(z.literal('')),
  residentialAddress: z.string().trim().max(255).default('').nullable().transform((val) => val || ''),
  spouseDependents: z.array(spouseDependentSchema).max(10, 'Maximum 10 dependents allowed').default([]),
});
export type UpdateDemographicsInput = z.infer<typeof updateDemographicsSchema>;

// Clinical Record Schemas
export const medicationItemSchema = z.object({
  name: z.string().trim().min(1, 'Medication name is required').max(100),
  dosage: z.string().trim().min(1, 'Dosage is required').max(50),
  frequency: z.string().trim().min(1, 'Frequency is required').max(50),
  prescribed_by: z.string().trim().max(100).optional(),
  notes: z.string().trim().max(255).optional(),
});

export const surgeryItemSchema = z.object({
  procedure: z.string().trim().min(1, 'Surgical procedure is required').max(100),
  year: z.union([
    z.number().int().min(1900).max(2100).transform(String),
    z.string().trim().regex(surgeryYearRegex, 'Year must be a valid 4-digit year between 1900 and 2099'),
  ]),
  notes: z.string().trim().max(255).optional(),
});

export const clinicalRecordSchema = z.object({
  medicalConditions: z.array(z.string().trim().min(1, 'Medical condition item cannot be empty')).default([]),
  currentMedication: z.array(medicationItemSchema).default([]),
  previousSurgeries: z.array(surgeryItemSchema).default([]),
  allergies: z.array(z.string().trim().min(1, 'Allergy item cannot be empty')).default([]),
  isDoctorVerified: z.boolean().default(false),
  verifiedByDoctorId: z.string().uuid().nullable().optional(),
});
export type ClinicalRecordInput = z.infer<typeof clinicalRecordSchema>;

export const baselineSubmissionSchema = z.object({
  conditions: z.array(z.string().trim().min(1, 'Condition item cannot be empty')).max(50, 'Maximum 50 conditions allowed').default([]),
  allergies: z.array(z.string().trim().min(1, 'Allergy item cannot be empty')).max(50, 'Maximum 50 allergies allowed').default([]),
});
export type BaselineSubmissionInput = z.infer<typeof baselineSubmissionSchema>;

// Emergency triage schema (N1 whitelist projection)
export const emergencyTriageSchema = z
  .object({
    full_name: z.string().trim().min(1, 'Patient name is required'),
    contact_phone: z.string().default(''),
    patient_code: z.string().trim().default(''),
    age: z.coerce.number().int().min(0).max(130),
    blood_group: bloodGroupEnum,
    emergency_contact_name: z.string().default(''),
    emergency_contact_phone: z.string().default(''),
    emergency_contact_relation: z.string().default(''),
    medical_conditions: z.array(z.string().trim()).default([]),
    current_medication: z.array(medicationItemSchema).default([]),
    previous_surgeries: z.array(surgeryItemSchema).default([]),
    allergies: z.array(z.string().trim()).default([]),
    last_appointment_date: z.string().nullable().default(null),
    is_doctor_verified: z.boolean().default(false),
    updated_at: z.string().nullable().optional().transform((val) => val || ''),
  })
  .passthrough()
  .superRefine((data, ctx) => {
    const raw = data as Record<string, unknown>;
    if ('residential_address' in raw) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Privacy violation: residential_address prohibited',
      });
    }
    if ('spouse_dependents' in raw) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Privacy violation: spouse_dependents prohibited',
      });
    }
  });
export type EmergencyTriageData = z.infer<typeof emergencyTriageSchema>;
export type EmergencyTriageInput = EmergencyTriageData;

export const appointmentStatusEnum = z.enum(['scheduled', 'completed', 'cancelled']);
export type AppointmentStatusType = z.infer<typeof appointmentStatusEnum>;

export const createAppointmentSchema = z.object({
  patient_id: uuidSchema,
  scheduled_at: z.string().datetime({ message: 'Must be a valid ISO 8601 date string' }),
  reason: z.string().trim().min(2, 'Appointment reason must be at least 2 characters').max(255),
  clinical_notes: z.string().trim().max(1000).optional().nullable(),
});
export type CreateAppointmentInput = z.infer<typeof createAppointmentSchema>;

export const updateAppointmentStatusSchema = z.object({
  appointment_id: uuidSchema,
  status: appointmentStatusEnum,
  clinical_notes: z.string().trim().max(1000).optional().nullable(),
});
export type UpdateAppointmentStatusInput = z.infer<typeof updateAppointmentStatusSchema>;

export const doctorClinicalRecordUpdateSchema = z.object({
  patient_id: uuidSchema,
  expectedUpdatedAt: z.string().min(1, 'expectedUpdatedAt timestamp is required'),
  medical_conditions: z.array(z.string().trim().min(1)).max(50).default([]),
  current_medication: z.array(medicationItemSchema).max(50).default([]),
  previous_surgeries: z.array(surgeryItemSchema).max(50).default([]),
  allergies: z.array(z.string().trim().min(1)).max(50).default([]),
  consultation_notes: z.string().trim().max(1000).optional().nullable(),
});
export type DoctorClinicalRecordUpdateInput = z.infer<typeof doctorClinicalRecordUpdateSchema>;

export const patientSearchQuerySchema = z.string().trim().min(2).max(100);

export const patientSearchObjectSchema = z.object({
  query: patientSearchQuerySchema.optional(),
  q: patientSearchQuerySchema.optional(),
}).refine((data) => data.query || data.q, {
  message: 'Search query must be at least 2 characters',
}).transform((data) => ({
  query: data.query || data.q || '',
  q: data.q || data.query || '',
}));
export type PatientSearchQuery = z.infer<typeof patientSearchQuerySchema>;

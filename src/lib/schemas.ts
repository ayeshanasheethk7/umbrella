import { z } from 'zod';

export const bloodGroupEnum = z.enum([
  'A+',
  'A-',
  'B+',
  'B-',
  'AB+',
  'AB-',
  'O+',
  'O-',
  'Unknown',
]);

export const uuidSchema = z.string().uuid('Invalid UUID format');

/**
 * Standard phone regex: Optional leading + followed by 7 to 20 digits, spaces, hyphens, dots, parentheses
 */
export const phoneRegex = /^\+?[0-9\s\-().]{7,20}$/;

/**
 * 4-digit surgery year regex: 1900-2099
 */
export const surgeryYearRegex = /^(19|20)\d{2}$/;

/**
 * Authentication schemas
 */
export const loginSchema = z.object({
  email: z
    .string()
    .trim()
    .toLowerCase()
    .email('Please enter a valid email address')
    .max(254, 'Email address cannot exceed 254 characters'),
  password: z.string().min(8, 'Password must be at least 8 characters long').max(128, 'Password cannot exceed 128 characters'),
});

export type LoginInput = z.infer<typeof loginSchema>;

export const patientSignupSchema = z.object({
  role: z.literal('patient').default('patient'),
  email: z
    .string()
    .trim()
    .toLowerCase()
    .email('Please enter a valid email address')
    .max(254, 'Email address cannot exceed 254 characters'),
  password: z.string().min(8, 'Password must be at least 8 characters long').max(128, 'Password cannot exceed 128 characters'),
  fullName: z.string().trim().min(2, 'Full name must be at least 2 characters').max(100, 'Full name cannot exceed 100 characters'),
  contactPhone: z
    .string()
    .trim()
    .regex(phoneRegex, 'Please provide a valid contact phone number (7-20 digits and optional formatting)'),
  age: z.coerce
    .number({ invalid_type_error: 'Age must be a valid number' })
    .int('Age must be a whole number')
    .min(0, 'Age must be 0 or greater')
    .max(130, 'Age must be 130 or less'),
  bloodGroup: bloodGroupEnum,
  emergencyContactName: z
    .string()
    .trim()
    .min(2, 'Emergency contact name is required')
    .max(100, 'Emergency contact name cannot exceed 100 characters'),
  emergencyContactPhone: z
    .string()
    .trim()
    .regex(phoneRegex, 'Emergency contact phone number must be a valid phone format'),
  emergencyContactRelation: z
    .string()
    .trim()
    .min(1, 'Relationship to emergency contact is required')
    .max(50, 'Relationship cannot exceed 50 characters'),
});

export type PatientSignupInput = z.infer<typeof patientSignupSchema>;

export const doctorSignupSchema = z.object({
  role: z.literal('doctor').default('doctor'),
  email: z
    .string()
    .trim()
    .toLowerCase()
    .email('Please enter a valid medical email address')
    .max(254, 'Email address cannot exceed 254 characters'),
  password: z.string().min(8, 'Password must be at least 8 characters long').max(128, 'Password cannot exceed 128 characters'),
  fullName: z.string().trim().min(2, 'Full physician name is required').max(100, 'Physician name cannot exceed 100 characters'),
  contactPhone: z
    .string()
    .trim()
    .regex(phoneRegex, 'Please provide a valid clinic/cell phone number (7-20 digits and optional formatting)'),
  medicalLicenseNumber: z
    .string()
    .trim()
    .min(3, 'Official medical license or registration number is required')
    .max(50, 'Medical license number cannot exceed 50 characters'),
  specialization: z.string().trim().min(2, 'Medical specialization is required (e.g., Emergency Medicine, Cardiology)').max(100, 'Specialization cannot exceed 100 characters'),
});

export type DoctorSignupInput = z.infer<typeof doctorSignupSchema>;

/**
 * Profile schemas
 */
export const spouseDependentSchema = z.object({
  name: z.string().trim().min(1, 'Dependent name is required').max(100),
  relation: z.string().trim().min(1, 'Relation is required').max(50),
  age: z.number().int().min(0).max(130).optional(),
  phone: z.string().trim().regex(phoneRegex, 'Phone must be a valid format').optional().or(z.literal('')),
});

export const patientProfileSchema = z.object({
  age: z.coerce.number().int().min(0).max(130),
  bloodGroup: bloodGroupEnum,
  emergencyContactName: z.string().trim().min(2, 'Emergency contact name is required').max(100),
  emergencyContactPhone: z.string().trim().regex(phoneRegex, 'Emergency contact phone is required'),
  emergencyContactRelation: z.string().trim().min(1, 'Emergency contact relation is required').max(50),
  residentialAddress: z.string().trim().max(255).default(''),
  spouseDependents: z.array(spouseDependentSchema).max(10).default([]),
});

export type PatientProfileInput = z.infer<typeof patientProfileSchema>;

/**
 * Combined Demographics Update Schema for Patient Portal (Milestone M5)
 * Combines account fields (fullName, contactPhone) and patient_profiles fields
 */
export const updateDemographicsSchema = z.object({
  fullName: z
    .string()
    .trim()
    .min(2, 'Full name must be at least 2 characters')
    .max(100, 'Full name cannot exceed 100 characters'),
  contactPhone: z
    .string()
    .trim()
    .regex(phoneRegex, 'Please provide a valid contact phone number')
    .optional()
    .or(z.literal('')),
  age: z.coerce
    .number({ invalid_type_error: 'Age must be a whole number' })
    .int('Age must be a whole number')
    .min(0, 'Age cannot be negative')
    .max(130, 'Age cannot exceed 130'),
  bloodGroup: bloodGroupEnum,
  emergencyContactName: z
    .string()
    .trim()
    .min(2, 'Emergency contact name is required')
    .max(100, 'Name cannot exceed 100 characters'),
  emergencyContactPhone: z
    .string()
    .trim()
    .regex(phoneRegex, 'Emergency contact phone number must be valid'),
  emergencyContactRelation: z
    .string()
    .trim()
    .min(1, 'Relationship is required')
    .max(50, 'Relationship cannot exceed 50 characters'),
  residentialAddress: z
    .string()
    .trim()
    .max(255, 'Residential address cannot exceed 255 characters')
    .default(''),
  spouseDependents: z
    .array(spouseDependentSchema)
    .max(10, 'Maximum 10 dependents allowed')
    .default([]),
});

export type UpdateDemographicsInput = z.infer<typeof updateDemographicsSchema>;

/**
 * Clinical Record Schemas
 */
export const medicationItemSchema = z.object({
  name: z.string().trim().min(1, 'Medication name is required').max(100),
  dosage: z.string().trim().min(1, 'Dosage is required').max(50),
  frequency: z.string().trim().min(1, 'Frequency is required').max(50),
  prescribed_by: z.string().trim().max(100).optional(),
});

export const surgeryItemSchema = z.object({
  procedure: z.string().trim().min(1, 'Surgical procedure is required').max(100),
  year: z.union([
    z.number().int().min(1900).max(2100),
    z.string().trim().regex(surgeryYearRegex, 'Year must be a valid 4-digit year between 1900 and 2099'),
  ]),
  notes: z.string().trim().max(255).optional(),
});

export const clinicalRecordSchema = z.object({
  medicalConditions: z.array(z.string().trim().min(1, 'Medical condition item cannot be empty')).default([]),
  currentMedication: z.array(medicationItemSchema).default([]),
  previousSurgeries: z.array(surgeryItemSchema).default([]),
  allergies: z.array(z.string().trim().min(1, 'Allergy item cannot be empty')).default([]),
});

export type ClinicalRecordInput = z.infer<typeof clinicalRecordSchema>;

/**
 * Baseline self-reported schema (DECISIONS D7)
 */
export const baselineSubmissionSchema = z.object({
  conditions: z.array(z.string().trim().min(1, 'Condition item cannot be empty')).default([]),
  allergies: z.array(z.string().trim().min(1, 'Allergy item cannot be empty')).default([]),
});

export type BaselineSubmissionInput = z.infer<typeof baselineSubmissionSchema>;

/**
 * Emergency triage schema (N1 whitelist projection)
 */
export const emergencyTriageSchema = z
  .object({
    full_name: z.string().trim().min(1, 'Patient name is required'),
    contact_phone: z.string().default(''),
    patient_code: z.string().trim().min(1, 'Patient code is required'),
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
        path: ['residential_address'],
      });
    }
    if ('spouse_dependents' in raw) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Privacy violation: spouse_dependents prohibited',
        path: ['spouse_dependents'],
      });
    }
  });

export type EmergencyTriageData = z.infer<typeof emergencyTriageSchema>;

/**
 * Doctor Portal & Appointment Schemas (Milestone M6)
 */
export const appointmentStatusEnum = z.enum(['scheduled', 'completed', 'cancelled']);
export type AppointmentStatusType = z.infer<typeof appointmentStatusEnum>;

export const createAppointmentSchema = z.object({
  patient_id: uuidSchema,
  scheduled_at: z.string().datetime({ message: 'A valid ISO datetime is required' }),
  reason: z
    .string()
    .trim()
    .min(2, 'Reason for visit must be at least 2 characters')
    .max(200, 'Reason cannot exceed 200 characters'),
  clinical_notes: z
    .string()
    .trim()
    .max(1000, 'Clinical notes cannot exceed 1000 characters')
    .optional()
    .nullable(),
});

export type CreateAppointmentInput = z.infer<typeof createAppointmentSchema>;

export const updateAppointmentStatusSchema = z.object({
  appointment_id: uuidSchema,
  status: appointmentStatusEnum,
  clinical_notes: z
    .string()
    .trim()
    .max(1000, 'Clinical notes cannot exceed 1000 characters')
    .optional()
    .nullable(),
});

export type UpdateAppointmentStatusInput = z.infer<typeof updateAppointmentStatusSchema>;

export const doctorClinicalRecordUpdateSchema = z.object({
  patient_id: uuidSchema,
  expectedUpdatedAt: z.string().min(1, 'expectedUpdatedAt timestamp is required'),
  medical_conditions: z
    .array(z.string().trim().min(1, 'Medical condition cannot be empty'))
    .max(50, 'Maximum 50 conditions allowed')
    .default([]),
  current_medication: z
    .array(medicationItemSchema)
    .max(50, 'Maximum 50 medications allowed')
    .default([]),
  previous_surgeries: z
    .array(surgeryItemSchema)
    .max(50, 'Maximum 50 surgeries allowed')
    .default([]),
  allergies: z
    .array(z.string().trim().min(1, 'Allergy item cannot be empty'))
    .max(50, 'Maximum 50 allergies allowed')
    .default([]),
  consultation_notes: z
    .string()
    .trim()
    .max(1000, 'Consultation notes cannot exceed 1000 characters')
    .optional()
    .nullable(),
});

export type DoctorClinicalRecordUpdateInput = z.infer<typeof doctorClinicalRecordUpdateSchema>;

export const patientSearchQuerySchema = z
  .string()
  .trim()
  .min(2, 'Search query must be at least 2 characters')
  .max(100, 'Search query cannot exceed 100 characters');

export const patientSearchObjectSchema = z.object({
  query: patientSearchQuerySchema,
});

export type PatientSearchQuery = z.infer<typeof patientSearchQuerySchema>;


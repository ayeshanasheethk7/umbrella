'use client';

import React, { useState, useTransition } from 'react';
import { Calendar, Clock, FileText, Check } from 'lucide-react';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { createAppointmentAction } from '@/app/portal/doctor/actions';
import type { AppointmentRow } from '@/lib/supabase/types';

export interface ScheduleAppointmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  patientId: string;
  patientName: string;
  patientCode: string;
  onAppointmentCreated?: (newAppt: AppointmentRow) => void;
}

export const ScheduleAppointmentModal: React.FC<ScheduleAppointmentModalProps> = ({
  isOpen,
  onClose,
  patientId,
  patientName,
  patientCode,
  onAppointmentCreated,
}) => {
  const [scheduledDate, setScheduledDate] = useState('');
  const [scheduledTime, setScheduledTime] = useState('');
  const [reason, setReason] = useState('');
  const [clinicalNotes, setClinicalNotes] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!scheduledDate || !scheduledTime) {
      setError('Please select both a date and time for the consultation.');
      return;
    }

    const trimmedReason = reason.trim();
    if (trimmedReason.length < 2) {
      setError('Reason for visit must be at least 2 characters long.');
      return;
    }
    if (trimmedReason.length > 200) {
      setError('Reason cannot exceed 200 characters.');
      return;
    }

    try {
      const combinedDateTime = new Date(`${scheduledDate}T${scheduledTime}:00`);
      if (isNaN(combinedDateTime.getTime())) {
        setError('Invalid date or time entered.');
        return;
      }

      const isoString = combinedDateTime.toISOString();

      startTransition(async () => {
        const res = await createAppointmentAction({
          patient_id: patientId,
          scheduled_at: isoString,
          reason: trimmedReason,
          clinical_notes: clinicalNotes.trim() || null,
        });

        if (res.ok) {
          onAppointmentCreated?.(res.data);
          onClose();
          setReason('');
          setClinicalNotes('');
          setScheduledDate('');
          setScheduledTime('');
        } else {
          setError(res.error);
        }
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Scheduling failed.');
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Schedule Consultation"
      description={`Book a clinical appointment for ${patientName} (${patientCode}).`}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div
            role="alert"
            className="rounded-xl border border-clinical-critical/30 bg-clinical-critical/10 p-3 text-xs text-clinical-critical-text font-medium"
          >
            {error}
          </div>
        )}

        <div className="rounded-xl border border-black/10 bg-black/5 p-3 text-xs flex items-center justify-between">
          <span className="text-text-body-secondary">Active Patient</span>
          <span className="font-bold text-text-primary">
            {patientName} <span className="font-mono text-text-body-secondary font-semibold">({patientCode})</span>
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <label htmlFor="appt-date" className="block text-xs font-semibold text-text-primary">
              Appointment Date
            </label>
            <div className="relative">
              <input
                id="appt-date"
                type="date"
                required
                value={scheduledDate}
                onChange={(e) => setScheduledDate(e.target.value)}
                className="h-[44px] min-h-[44px] w-full rounded-xl border border-black/10 bg-surface px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label htmlFor="appt-time" className="block text-xs font-semibold text-text-primary">
              Time
            </label>
            <div className="relative">
              <input
                id="appt-time"
                type="time"
                required
                value={scheduledTime}
                onChange={(e) => setScheduledTime(e.target.value)}
                className="h-[44px] min-h-[44px] w-full rounded-xl border border-black/10 bg-surface px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action"
              />
            </div>
          </div>
        </div>

        <div className="space-y-1.5">
          <label htmlFor="appt-reason" className="block text-xs font-semibold text-text-primary">
            Reason for Visit <span className="text-clinical-critical">*</span>
          </label>
          <input
            id="appt-reason"
            type="text"
            required
            maxLength={200}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="e.g. Annual Cardiovascular Review & Medication Check"
            className="h-[44px] min-h-[44px] w-full rounded-xl border border-black/10 bg-surface px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action"
          />
        </div>

        <div className="space-y-1.5">
          <label htmlFor="appt-notes" className="block text-xs font-semibold text-text-primary">
            Clinical Preparation Notes <span className="text-text-body-secondary font-normal">(Optional)</span>
          </label>
          <textarea
            id="appt-notes"
            rows={3}
            maxLength={1000}
            value={clinicalNotes}
            onChange={(e) => setClinicalNotes(e.target.value)}
            placeholder="Preliminary clinical context, requested lab work, or patient instructions..."
            className="w-full rounded-xl border border-black/10 bg-surface p-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action resize-none"
          />
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-black/5">
          <Button
            type="button"
            variant="secondary"
            size="default"
            disabled={isPending}
            onClick={onClose}
            className="min-h-[44px]"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            size="default"
            isLoading={isPending}
            className="min-h-[44px]"
          >
            <Check className="mr-1.5 h-4 w-4" aria-hidden="true" />
            Book Consultation
          </Button>
        </div>
      </form>
    </Modal>
  );
};

'use client';

import React, { useState, useTransition } from 'react';
import { Calendar, Clock, CheckCircle2, XCircle, Plus, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Modal } from '@/components/ui/modal';
import {
  updateAppointmentStatusAction,
  type DoctorAppointmentListItem,
} from '@/app/portal/doctor/actions';
import { ScheduleAppointmentModal } from './schedule-appointment-modal';
import type { AppointmentRow } from '@/lib/supabase/types';
import { cn } from '@/lib/utils';

export interface AppointmentManagerProps {
  appointments: DoctorAppointmentListItem[];
  activePatient?: { id: string; fullName: string; patientCode: string } | null;
  onAppointmentsChanged?: () => void;
}

export const AppointmentManager: React.FC<AppointmentManagerProps> = ({
  appointments: initialAppointments,
  activePatient,
  onAppointmentsChanged,
}) => {
  const [appointments, setAppointments] = useState<DoctorAppointmentListItem[]>(initialAppointments);
  const [filter, setFilter] = useState<'upcoming' | 'completed' | 'all'>('upcoming');
  const [isScheduleOpen, setIsScheduleOpen] = useState(false);
  const [completingAppt, setCompletingAppt] = useState<DoctorAppointmentListItem | null>(null);
  const [notes, setNotes] = useState('');
  const [isPending, startTransition] = useTransition();
  const [err, setErr] = useState<string | null>(null);

  const filtered = appointments.filter((a) => {
    if (filter === 'upcoming') return a.status === 'scheduled';
    if (filter === 'completed') return a.status === 'completed';
    return true;
  });

  const handleCompleteSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!completingAppt) return;
    setErr(null);

    startTransition(async () => {
      const res = await updateAppointmentStatusAction({
        appointment_id: completingAppt.id,
        status: 'completed',
        clinical_notes: notes.trim() || undefined,
      });

      if (res.ok) {
        setAppointments((prev) =>
          prev.map((item) =>
            item.id === completingAppt.id
              ? { ...item, status: 'completed', clinical_notes: notes.trim() || item.clinical_notes }
              : item
          )
        );
        setCompletingAppt(null);
        setNotes('');
        onAppointmentsChanged?.();
      } else {
        setErr(res.error);
      }
    });
  };

  const handleCancel = (id: string) => {
    if (!window.confirm('Cancel this scheduled consultation?')) return;
    startTransition(async () => {
      const res = await updateAppointmentStatusAction({ appointment_id: id, status: 'cancelled' });
      if (res.ok) {
        setAppointments((prev) => prev.map((item) => (item.id === id ? { ...item, status: 'cancelled' } : item)));
        onAppointmentsChanged?.();
      } else {
        setErr(res.error);
      }
    });
  };

  const handleCreated = (newAppt: AppointmentRow) => {
    const newItem: DoctorAppointmentListItem = {
      id: newAppt.id,
      patient_id: newAppt.patient_id,
      scheduled_at: newAppt.scheduled_at,
      status: newAppt.status,
      reason: newAppt.reason,
      clinical_notes: newAppt.clinical_notes,
      created_at: newAppt.created_at,
      patient: {
        fullName: activePatient?.fullName || 'Active Patient',
        contactPhone: '',
        patientCode: activePatient?.patientCode || 'N/A',
        age: 0,
        bloodGroup: 'Unknown',
      },
    };
    setAppointments([newItem, ...appointments]);
    onAppointmentsChanged?.();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="inline-flex min-h-[52px] items-center rounded-xl bg-black/5 p-1 text-sm font-medium">
          {(['upcoming', 'completed', 'all'] as const).map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setFilter(tab)}
              className={cn(
                'flex items-center px-4 py-2 rounded-lg transition-colors min-h-[44px] capitalize focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action',
                filter === tab ? 'bg-surface text-text-primary font-semibold shadow-xs' : 'text-text-body-secondary hover:text-text-primary'
              )}
            >
              {tab === 'all' ? 'All Visits' : tab}
            </button>
          ))}
        </div>

        {activePatient && (
          <Button type="button" variant="primary" size="default" onClick={() => setIsScheduleOpen(true)} className="min-h-[44px]">
            <Plus className="mr-1.5 h-4 w-4" /> Book for {activePatient.fullName.split(' ')[0]}
          </Button>
        )}
      </div>

      {err && (
        <div role="alert" className="rounded-xl border border-clinical-critical/30 bg-clinical-critical/10 p-3 text-xs text-clinical-critical-text font-medium">
          {err}
        </div>
      )}

      <div className="space-y-3">
        {filtered.length === 0 ? (
          <Card className="text-center py-12">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-black/5 text-text-secondary mb-3">
              <Calendar className="h-6 w-6" />
            </div>
            <p className="text-sm font-semibold text-text-primary">No appointments found</p>
            <p className="text-xs text-text-body-secondary mt-1">No consultations in this category.</p>
          </Card>
        ) : (
          filtered.map((appt) => {
            const d = new Date(appt.scheduled_at);
            const dtStr = d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
            const tmStr = d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });

            return (
              <Card key={appt.id} className="p-4 sm:p-5">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <div className="flex h-12 w-12 shrink-0 flex-col items-center justify-center rounded-xl bg-black/5 text-text-primary border border-black/10">
                      <span className="text-[10px] uppercase font-bold text-text-body-secondary">{d.toLocaleDateString('en-US', { month: 'short' })}</span>
                      <span className="text-base font-extrabold leading-none">{d.getDate()}</span>
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-base font-bold text-text-primary">{appt.patient.fullName}</span>
                        <span className="font-mono text-xs px-2 py-0.5 rounded bg-black/5 text-text-body-secondary font-semibold">{appt.patient.patientCode}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-xs text-text-body-secondary mt-1">
                        <Clock className="h-3.5 w-3.5" />
                        <span>{dtStr} at {tmStr}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center flex-wrap gap-2">
                    {appt.status === 'completed' && <Badge variant="verified" icon={<CheckCircle2 className="h-3.5 w-3.5" />}>Completed</Badge>}
                    {appt.status === 'scheduled' && <Badge variant="pending" icon={<Clock className="h-3.5 w-3.5" />}>Scheduled</Badge>}
                    {appt.status === 'cancelled' && <Badge variant="critical" icon={<XCircle className="h-3.5 w-3.5" />}>Cancelled</Badge>}

                    {appt.status === 'scheduled' && (
                      <div className="flex items-center gap-2 ml-auto sm:ml-0">
                        <Button type="button" variant="secondary" size="sm" disabled={isPending} onClick={() => { setCompletingAppt(appt); setNotes(appt.clinical_notes || ''); }} className="min-h-[44px]">
                          <Check className="mr-1 h-3.5 w-3.5" /> Complete Visit
                        </Button>
                        <Button type="button" variant="ghost" size="sm" disabled={isPending} onClick={() => handleCancel(appt.id)} className="min-h-[44px] text-clinical-critical hover:bg-clinical-critical/10">
                          Cancel
                        </Button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-3.5 pt-3 border-t border-black/5 text-xs space-y-1">
                  <p className="text-text-primary font-medium"><span className="text-text-body-secondary font-normal">Reason:</span> {appt.reason}</p>
                  {appt.clinical_notes && <p className="text-text-body-secondary"><span className="font-medium text-text-primary">Clinical Notes:</span> {appt.clinical_notes}</p>}
                </div>
              </Card>
            );
          })
        )}
      </div>

      {activePatient && (
        <ScheduleAppointmentModal
          isOpen={isScheduleOpen}
          onClose={() => setIsScheduleOpen(false)}
          patientId={activePatient.id}
          patientName={activePatient.fullName}
          patientCode={activePatient.patientCode}
          onAppointmentCreated={handleCreated}
        />
      )}

      <Modal
        isOpen={Boolean(completingAppt)}
        onClose={() => setCompletingAppt(null)}
        title="Complete Clinical Consultation"
        description="Record final consultation assessment. Completing will sync summary notes with the patient's clinical file (D8)."
      >
        <form onSubmit={handleCompleteSubmit} className="space-y-4">
          <div className="rounded-xl border border-black/10 bg-black/5 p-3 text-xs">
            <span className="font-semibold text-text-primary">Patient: {completingAppt?.patient.fullName}</span>
            <p className="text-text-body-secondary mt-0.5">Reason: {completingAppt?.reason}</p>
          </div>
          <div className="space-y-1.5">
            <label htmlFor="completion-notes" className="block text-xs font-semibold text-text-primary">
              Clinical Summary & Instructions
            </label>
            <textarea
              id="completion-notes"
              rows={4}
              maxLength={1000}
              required
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Clinical findings, instructions, and follow-up plan..."
              className="w-full rounded-xl border border-black/10 bg-surface p-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action resize-none"
            />
          </div>
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-black/5">
            <Button type="button" variant="secondary" size="default" disabled={isPending} onClick={() => setCompletingAppt(null)} className="min-h-[44px]">Cancel</Button>
            <Button type="submit" variant="primary" size="default" isLoading={isPending} className="min-h-[44px]"><Check className="mr-1.5 h-4 w-4" /> Complete Consultation</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

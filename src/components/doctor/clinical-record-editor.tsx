'use client';

import React, { useState, useTransition } from 'react';
import { Save, Plus, Trash2, AlertTriangle, ShieldCheck, Clock, RefreshCw, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge, AllergyAlert } from '@/components/ui/badge';
import { updateClinicalRecordAction } from '@/app/portal/doctor/actions';
import type { ClinicalRecordRow, MedicationItem, SurgeryItem } from '@/lib/supabase/types';
import { cn } from '@/lib/utils';

export interface ClinicalRecordEditorProps {
  patientId: string;
  initialRecord: ClinicalRecordRow;
  onRecordUpdated?: (updated: ClinicalRecordRow) => void;
  onReloadRequest?: () => void;
}

const inpCls = 'h-[44px] min-h-[44px] rounded-xl border border-black/10 bg-surface px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action';
const delCls = 'min-h-[44px] min-w-[44px] p-2 rounded-lg text-text-secondary hover:text-clinical-critical flex items-center justify-center';

const Tag = ({ text, onRemove, isCrit }: { text: string; onRemove: () => void; isCrit?: boolean }) => (
  <span className={cn('inline-flex items-center gap-1 pl-3 pr-1 py-0.5 rounded-lg text-xs font-semibold min-h-[44px]', isCrit ? 'bg-clinical-critical/10 border border-clinical-critical/30 text-clinical-critical-text' : 'bg-black/5 border border-black/10 text-text-primary')}>
    <span>{text}</span>
    <button type="button" onClick={onRemove} className={delCls} aria-label={`Remove ${text}`}><Trash2 className="h-3.5 w-3.5" /></button>
  </span>
);

const Sec = ({ t, d, children }: { t: string; d: string; children: React.ReactNode }) => (
  <Card><CardHeader><CardTitle className="text-lg">{t}</CardTitle><CardDescription className="text-xs">{d}</CardDescription></CardHeader><CardContent className="space-y-4">{children}</CardContent></Card>
);

export const ClinicalRecordEditor: React.FC<ClinicalRecordEditorProps> = ({
  patientId,
  initialRecord,
  onRecordUpdated,
  onReloadRequest,
}) => {
  const [conditions, setConditions] = useState<string[]>(initialRecord.medical_conditions || []);
  const [newCond, setNewCond] = useState('');
  const [allergies, setAllergies] = useState<string[]>(initialRecord.allergies || []);
  const [newAllergy, setNewAllergy] = useState('');
  const [meds, setMeds] = useState<MedicationItem[]>(
    Array.isArray(initialRecord.current_medication) ? (initialRecord.current_medication as unknown as MedicationItem[]) : []
  );
  const [mName, setMName] = useState('');
  const [mDosage, setMDosage] = useState('');
  const [mFreq, setMFreq] = useState('');
  const [surgeries, setSurgeries] = useState<SurgeryItem[]>(
    Array.isArray(initialRecord.previous_surgeries) ? (initialRecord.previous_surgeries as unknown as SurgeryItem[]) : []
  );
  const [sProc, setSProc] = useState('');
  const [sYear, setSYear] = useState('');

  const [expectedUpdatedAt, setExpectedUpdatedAt] = useState(initialRecord.updated_at);
  const [isPending, startTransition] = useTransition();
  const [conflictError, setConflictError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const isVerified = initialRecord.is_doctor_verified;
  const s = JSON.stringify;
  const isDirty = s(conditions) !== s(initialRecord.medical_conditions || []) || s(allergies) !== s(initialRecord.allergies || []) || s(meds) !== s(initialRecord.current_medication || []) || s(surgeries) !== s(initialRecord.previous_surgeries || []);
  const canSave = isDirty || !isVerified;

  const handleSave = () => {
    setErr(null);
    setConflictError(null);
    setSuccessMsg(null);
    startTransition(async () => {
      const res = await updateClinicalRecordAction({
        patient_id: patientId,
        expectedUpdatedAt,
        medical_conditions: conditions,
        current_medication: meds,
        previous_surgeries: surgeries,
        allergies,
      });
      if (res.ok) {
        setExpectedUpdatedAt(res.data.updated_at);
        setSuccessMsg('Clinical record updated and physician verified successfully.');
        onRecordUpdated?.(res.data);
      } else if (res.conflict) {
        setConflictError(res.error);
      } else {
        setErr(res.error);
      }
    });
  };

  return (
    <div className="space-y-6">
      {conflictError && (
        <div role="alert" className="rounded-2xl border-2 border-clinical-pending bg-clinical-pending/10 p-4 text-clinical-pending-text shadow-sm">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
            <div className="flex-1 text-sm">
              <p className="font-bold text-base">Concurrency Conflict Detected</p>
              <p className="mt-1 leading-relaxed">{conflictError}</p>
              <div className="mt-3">
                <Button type="button" variant="secondary" size="sm" onClick={onReloadRequest} className="min-h-[44px]">
                  <RefreshCw className="mr-2 h-4 w-4" aria-hidden="true" /> Reload Latest Record
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {successMsg && (
        <div role="status" className="rounded-2xl border border-clinical-verified/30 bg-clinical-verified/10 p-3.5 text-xs text-clinical-verified-text flex items-center gap-2 font-medium">
          <Check className="h-4 w-4 shrink-0" aria-hidden="true" />
          <span>{successMsg}</span>
        </div>
      )}

      {err && <div role="alert" className="rounded-2xl border border-clinical-critical/30 bg-clinical-critical/10 p-3.5 text-xs text-clinical-critical-text font-medium">{err}</div>}

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-2xl bg-canvas border border-black/10">
        <div className="flex items-center gap-2">
          {isVerified ? (
            <Badge variant="verified" icon={<ShieldCheck className="h-4 w-4" />}>Doctor Verified Record</Badge>
          ) : (
            <Badge variant="pending" icon={<Clock className="h-4 w-4" />}>Self-Reported Baseline (Unverified)</Badge>
          )}
          <span className="text-xs text-text-body-secondary">Updated: {new Date(expectedUpdatedAt).toLocaleString()}</span>
        </div>
        <Button
          type="button"
          variant="primary"
          size="default"
          isLoading={isPending}
          disabled={!canSave || Boolean(conflictError)}
          onClick={handleSave}
          className="min-h-[44px] sm:w-auto w-full"
        >
          <Save className="mr-2 h-4 w-4" aria-hidden="true" />
          {!isVerified && !isDirty ? 'Verify Medical Baseline' : 'Save & Verify Record'}
        </Button>
      </div>

      <Sec t="Critical Allergies" d="Substances causing adverse reactions.">
        <AllergyAlert allergies={allergies} />
        <div className="flex flex-wrap gap-2 pt-2">
          {allergies.map((a, i) => <Tag key={i} text={a} onRemove={() => setAllergies(allergies.filter((_, idx) => idx !== i))} isCrit />)}
        </div>
        <form onSubmit={(e) => { e.preventDefault(); const v = newAllergy.trim(); if (v && !allergies.includes(v)) { setAllergies([...allergies, v]); setNewAllergy(''); } }} className="flex gap-2">
          <input type="text" value={newAllergy} onChange={(e) => setNewAllergy(e.target.value)} placeholder="Add critical allergy..." className={cn(inpCls, 'flex-1')} />
          <Button type="submit" variant="secondary" size="default" className="min-h-[44px]"><Plus className="mr-1.5 h-4 w-4" /> Add</Button>
        </form>
      </Sec>

      <Sec t="Chronic Medical Conditions" d="Active diagnoses and conditions.">
        <div className="flex flex-wrap gap-2">
          {conditions.length === 0 ? <p className="text-xs text-text-body-secondary italic">No conditions on file.</p> : conditions.map((c, i) => (
            <Tag key={i} text={c} onRemove={() => setConditions(conditions.filter((_, idx) => idx !== i))} />
          ))}
        </div>
        <form onSubmit={(e) => { e.preventDefault(); const v = newCond.trim(); if (v && !conditions.includes(v)) { setConditions([...conditions, v]); setNewCond(''); } }} className="flex gap-2">
          <input type="text" value={newCond} onChange={(e) => setNewCond(e.target.value)} placeholder="Add chronic condition..." className={cn(inpCls, 'flex-1')} />
          <Button type="submit" variant="secondary" size="default" className="min-h-[44px]"><Plus className="mr-1.5 h-4 w-4" /> Add</Button>
        </form>
      </Sec>

      <Sec t="Current Medications" d="Active prescriptions and dosages.">
        <div className="divide-y divide-black/5">
          {meds.length === 0 ? <p className="text-xs text-text-body-secondary italic py-2">No medications on file.</p> : meds.map((m, i) => (
            <div key={i} className="flex items-center justify-between py-2">
              <div><p className="text-sm font-semibold text-text-primary">{m.name}</p><p className="text-xs text-text-body-secondary">{m.dosage} • {m.frequency}</p></div>
              <button type="button" onClick={() => setMeds(meds.filter((_, idx) => idx !== i))} className={delCls} aria-label={`Remove medication ${m.name}`}><Trash2 className="h-4 w-4" /></button>
            </div>
          ))}
        </div>
        <form onSubmit={(e) => { e.preventDefault(); if (mName.trim() && mDosage.trim() && mFreq.trim()) { setMeds([...meds, { name: mName.trim(), dosage: mDosage.trim(), frequency: mFreq.trim() }]); setMName(''); setMDosage(''); setMFreq(''); } }} className="grid grid-cols-1 sm:grid-cols-4 gap-2 pt-2">
          <input type="text" value={mName} onChange={(e) => setMName(e.target.value)} placeholder="Name" className={inpCls} />
          <input type="text" value={mDosage} onChange={(e) => setMDosage(e.target.value)} placeholder="Dosage" className={inpCls} />
          <input type="text" value={mFreq} onChange={(e) => setMFreq(e.target.value)} placeholder="Frequency" className={inpCls} />
          <Button type="submit" variant="secondary" size="default" className="min-h-[44px]"><Plus className="mr-1.5 h-4 w-4" /> Add</Button>
        </form>
      </Sec>

      <Sec t="Previous Surgeries" d="Past surgical procedures.">
        <div className="divide-y divide-black/5">
          {surgeries.length === 0 ? <p className="text-xs text-text-body-secondary italic py-2">No surgeries recorded.</p> : surgeries.map((s, i) => (
            <div key={i} className="flex items-center justify-between py-2">
              <div><p className="text-sm font-semibold text-text-primary">{s.procedure}</p><p className="text-xs text-text-body-secondary">Year: {s.year}</p></div>
              <button type="button" onClick={() => setSurgeries(surgeries.filter((_, idx) => idx !== i))} className={delCls} aria-label={`Remove surgery ${s.procedure}`}><Trash2 className="h-4 w-4" /></button>
            </div>
          ))}
        </div>
        <form onSubmit={(e) => { e.preventDefault(); if (sProc.trim() && sYear.trim()) { setSurgeries([...surgeries, { procedure: sProc.trim(), year: sYear.trim() }]); setSProc(''); setSYear(''); } }} className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2">
          <input type="text" value={sProc} onChange={(e) => setSProc(e.target.value)} placeholder="Procedure" className={cn(inpCls, 'sm:col-span-2')} />
          <div className="flex gap-2">
            <input type="text" value={sYear} onChange={(e) => setSYear(e.target.value)} placeholder="Year" className={cn(inpCls, 'w-full')} />
            <Button type="submit" variant="secondary" size="default" className="min-h-[44px] shrink-0"><Plus className="mr-1.5 h-4 w-4" /> Add</Button>
          </div>
        </form>
      </Sec>
    </div>
  );
};

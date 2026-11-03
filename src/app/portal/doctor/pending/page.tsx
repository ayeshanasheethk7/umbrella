import React from 'react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { redirect } from 'next/navigation';
import { Clock, ShieldCheck, Stethoscope, LogOut, RefreshCw } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { createClient } from '@/lib/supabase/server';

export const metadata: Metadata = {
  title: 'Verification Pending — Umbrella Physician Portal',
  description: 'Physician credential verification pending approval per platform policy D1.',
};

async function handleSignOut() {
  'use server';
  const supabase = createClient();
  await supabase.auth.signOut();
  redirect('/login');
}

export default async function DoctorPendingPage() {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect('/login?next=/portal/doctor/pending');
  }

  const { data: account } = await supabase
    .from('accounts')
    .select('full_name, role, doctor_status, specialization')
    .eq('id', user.id)
    .single();

  if (account?.role !== 'doctor') {
    redirect('/portal/patient');
  }

  // If already approved, bounce to doctor portal
  if (account?.doctor_status === 'approved') {
    redirect('/portal/doctor');
  }

  return (
    <div className="flex min-h-[calc(100vh-140px)] items-center justify-center px-4 py-12">
      <Card className="w-full max-w-lg bg-surface shadow-ceiling border border-black/10">
        <CardHeader className="text-center pb-6">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-clinical-pending/10 text-clinical-pending-text shadow-xs">
            <Clock className="h-7 w-7" aria-hidden="true" />
          </div>
          <div className="flex items-center justify-center gap-2 mb-2">
            <Badge variant="pending">Account Status: Pending</Badge>
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight text-text-primary">
            Verification Pending
          </CardTitle>
          <CardDescription className="text-sm text-text-body-secondary mt-2 leading-relaxed">
            Physician accounts require administrative credential confirmation per platform security policy D1.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-5">
          <div className="rounded-xl border border-black/10 bg-canvas/50 p-4 text-xs text-text-body-secondary space-y-2">
            <div className="flex items-center justify-between text-text-primary font-medium">
              <span>Registered Physician</span>
              <span>{account.full_name}</span>
            </div>
            {account.specialization && (
              <div className="flex items-center justify-between">
                <span>Specialization</span>
                <span className="font-medium text-text-primary">{account.specialization}</span>
              </div>
            )}
            <div className="flex items-center justify-between">
              <span>Registered Email</span>
              <span className="font-mono">{user.email}</span>
            </div>
          </div>

          <div className="rounded-xl bg-clinical-pending/10 border border-clinical-pending/30 p-3.5 text-xs text-clinical-pending-text leading-relaxed">
            <p className="font-semibold mb-1 flex items-center gap-1.5">
              <ShieldCheck className="h-4 w-4 shrink-0" aria-hidden="true" />
              Account Pending Approval - Our team verifies medical credentials within 24 hours. While pending, patient records cannot be accessed.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            <Link href="/portal/doctor" className="flex-1">
              <Button
                variant="primary"
                size="default"
                className="w-full min-h-[44px] h-[44px]"
              >
                <RefreshCw className="mr-2 h-4 w-4" aria-hidden="true" />
                Check Status
              </Button>
            </Link>

            <form action={handleSignOut} className="flex-1">
              <Button
                type="submit"
                variant="secondary"
                size="default"
                className="w-full min-h-[44px] h-[44px]"
              >
                <LogOut className="mr-2 h-4 w-4" aria-hidden="true" />
                Sign Out
              </Button>
            </form>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

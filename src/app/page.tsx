'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  ShieldAlert,
  QrCode,
  UserCheck,
  Stethoscope,
  ArrowRight,
  Lock,
  HeartPulse,
  PhoneCall,
  Search,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

export default function HomePage() {
  const router = useRouter();
  const [tokenInput, setTokenInput] = useState('');
  const [tokenError, setTokenError] = useState('');

  const handleLookup = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = tokenInput.trim();
    if (!trimmed) {
      setTokenError('Please enter a token UUID or scan a QR code');
      return;
    }

    // Direct routing to emergency triage page per Non-negotiable N1
    router.push(`/emergency/${encodeURIComponent(trimmed)}`);
  };

  return (
    <div className="flex flex-col items-center justify-center">
      {/* Hero Section */}
      <section className="w-full max-w-5xl px-4 pt-16 pb-20 md:pt-24 md:pb-28 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-black/10 bg-surface px-4 py-1.5 text-xs font-semibold text-text-primary shadow-xs mb-8">
          <ShieldAlert className="h-4 w-4 text-clinical-critical" />
          <span>Zero-Login Emergency Roadside Triage Architecture</span>
        </div>

        <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-[-0.03em] text-text-primary leading-[1.08] max-w-3xl mx-auto">
          Life-saving medical details when seconds count.
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-text-body-secondary max-w-2xl mx-auto leading-relaxed">
          Umbrella equips first responders with instant, verified emergency health data from a physical
          or digital QR scan — zero authentication barrier, zero residential address exposure.
        </p>

        {/* Emergency Direct Lookup Input Box */}
        <div
          id="emergency-lookup"
          className="mt-10 mx-auto max-w-lg rounded-[22px] bg-surface p-4 sm:p-5 border border-black/10 shadow-ceiling"
        >
          <form onSubmit={handleLookup} className="space-y-3">
            <div className="flex items-center gap-2 text-left px-1">
              <QrCode className="h-5 w-5 text-clinical-critical" />
              <span className="text-sm font-semibold text-text-primary">
                First Responder Direct Token Access
              </span>
            </div>
            <div className="flex flex-col sm:flex-row gap-2">
              <div className="flex-1">
                <Input
                  id="emergency-token"
                  placeholder="Enter QR token UUID..."
                  value={tokenInput}
                  onChange={(e) => {
                    setTokenInput(e.target.value);
                    if (tokenError) setTokenError('');
                  }}
                  error={tokenError}
                />
              </div>
              <Button
                type="submit"
                variant="destructive"
                size="default"
                className="font-semibold shrink-0"
              >
                <Search className="h-4 w-4 mr-1.5" />
                Access Triage
              </Button>
            </div>
            <p className="text-[11px] text-text-body-secondary text-left px-1">
              Reads strictly through security-definer RPC with no authentication required.
            </p>
          </form>
        </div>
      </section>

      {/* Gateway Portals Section */}
      <section className="w-full bg-surface border-y border-black/10 py-16 md:py-24">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-text-primary">
              Two Dedicated Healthcare Surfaces
            </h2>
            <p className="mt-2 text-sm sm:text-base text-text-body-secondary">
              Engineered with Postgres Row Level Security, verified provider auditing, and patient privacy.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Patient Portal Gateway Card */}
            <Card className="flex flex-col justify-between border border-black/10 hover:border-black/20 transition-all shadow-sm">
              <CardHeader>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-black/5 text-accent-action mb-4">
                  <UserCheck className="h-6 w-6" />
                </div>
                <CardTitle className="text-2xl font-bold text-text-primary">
                  Patient Portal
                </CardTitle>
                <CardDescription className="text-sm text-text-body-secondary mt-2 leading-relaxed">
                  Generate your official QR ID card, record verified emergency contacts, manage spouse/dependents,
                  and submit your self-reported health baseline.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 pt-4">
                <ul className="space-y-2 text-sm text-text-body-secondary">
                  <li className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-accent-action" />
                    <span>Instant high-resolution QR Studio with Level Q error correction</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-accent-action" />
                    <span>Printable 300 DPI CR80 wallet ID card generation</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-accent-action" />
                    <span>One-click physical QR token rotation for lost credentials</span>
                  </li>
                </ul>
                <div className="pt-4 flex flex-col sm:flex-row gap-3">
                  <Link href="/portal/patient" className="flex-1">
                    <Button variant="primary" size="lg" className="w-full">
                      Open Patient Portal
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                  <Link href="/signup?role=patient" className="flex-1">
                    <Button variant="secondary" size="lg" className="w-full">
                      Create ID
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>

            {/* Doctor Portal Gateway Card */}
            <Card className="flex flex-col justify-between border border-black/10 hover:border-black/20 transition-all shadow-sm">
              <CardHeader>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-black/5 text-clinical-critical mb-4">
                  <Stethoscope className="h-6 w-6" />
                </div>
                <CardTitle className="text-2xl font-bold text-text-primary">
                  Doctor Clinical Portal
                </CardTitle>
                <CardDescription className="text-sm text-text-body-secondary mt-2 leading-relaxed">
                  Authorized healthcare provider clinical environment featuring multi-modal patient lookup,
                  persistent safety banners, and trigger-stamped clinical updates.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 pt-4">
                <ul className="space-y-2 text-sm text-text-body-secondary">
                  <li className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-clinical-critical" />
                    <span>Multi-modal lookup by patient code, QR token, or contact phone</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-clinical-critical" />
                    <span>Persistent read-only safety banner (N2) displaying critical indicators</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-clinical-critical" />
                    <span>Strict doctor approval gate (D1) protecting clinical records</span>
                  </li>
                </ul>
                <div className="pt-4 flex flex-col sm:flex-row gap-3">
                  <Link href="/portal/doctor" className="flex-1">
                    <Button variant="primary" size="lg" className="w-full">
                      Open Doctor Portal
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                  <Link href="/signup?role=doctor" className="flex-1">
                    <Button variant="secondary" size="lg" className="w-full">
                      Physician Onboarding
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Safety & Invariant Highlights */}
      <section className="w-full max-w-5xl px-4 py-16 md:py-24">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="rounded-[18px] bg-surface p-6 border border-black/10 shadow-xs">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-black/5 text-clinical-critical mb-4">
              <PhoneCall className="h-5 w-5" />
            </div>
            <h3 className="text-base font-semibold text-text-primary">56px One-Tap Call</h3>
            <p className="mt-2 text-xs text-text-body-secondary leading-relaxed">
              First responders can immediately dial primary emergency contacts directly from roadside triage
              screens with zero delay or login gates.
            </p>
          </div>

          <div className="rounded-[18px] bg-surface p-6 border border-black/10 shadow-xs">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-black/5 text-accent-action mb-4">
              <Lock className="h-5 w-5" />
            </div>
            <h3 className="text-base font-semibold text-text-primary">Zero Address Leaks (N1)</h3>
            <p className="mt-2 text-xs text-text-body-secondary leading-relaxed">
              Residential addresses and dependents are completely excluded from emergency database RPC projections,
              preventing physical home burglaries during accidents.
            </p>
          </div>

          <div className="rounded-[18px] bg-surface p-6 border border-black/10 shadow-xs">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-black/5 text-clinical-verified mb-4">
              <HeartPulse className="h-5 w-5" />
            </div>
            <h3 className="text-base font-semibold text-text-primary">Verified Clinical Badges</h3>
            <p className="mt-2 text-xs text-text-body-secondary leading-relaxed">
              Clear visual distinction between patient self-reported baselines and licensed physician
              verified medical history.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

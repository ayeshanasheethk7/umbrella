import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { createAnonClient } from '@/lib/supabase/anon';
import { uuidSchema, emergencyTriageSchema } from '@/lib/schemas';
import { EmergencyTriageView } from '@/components/emergency/emergency-triage-view';

export const dynamic = 'force-dynamic';
export const revalidate = 0;
export const fetchCache = 'force-no-store';

export const metadata: Metadata = {
  title: 'Emergency Medical ID | Umbrella',
  description: 'Emergency roadside medical triage indicators',
  robots: {
    index: false,
    follow: false,
    nocache: true,
    googleBot: {
      index: false,
      follow: false,
      noimageindex: true,
      'max-image-preview': 'none',
      'max-snippet': -1,
    },
  },
  referrer: 'no-referrer',
};

interface EmergencyPageProps {
  params: Promise<{ token: string }> | { token: string };
}

/**
 * Public Zero-Login Emergency Triage Route (/emergency/[token])
 * Non-negotiables:
 * - N1: Reads ONLY through RPC get_emergency_triage_by_token. Zero exposure of address or dependents.
 * - N4: Cookie-less anonymous client using anon key only.
 * - N8 & D13: Pure CSS transitions, zero external animation libraries in bundle.
 * - N10: Strict typing, zero any.
 * - D9: Opaque notFound() for invalid/expired tokens with zero diagnostic leaks.
 */
export default async function EmergencyTriagePage({ params }: EmergencyPageProps) {
  const resolvedParams = await Promise.resolve(params);
  const token = resolvedParams?.token;

  if (!token) {
    notFound();
  }

  // 1. Fast UUID format validation before issuing database query (clean spaces or URL encodings)
  const cleanToken = decodeURIComponent(token).trim().replace(/^\{|\}$/g, '');
  const uuidResult = uuidSchema.safeParse(cleanToken);
  if (!uuidResult.success) {
    notFound();
  }
  const validToken = uuidResult.data;

  // 2. Fetch triage data strictly via anonymous security-definer RPC
  const supabase = createAnonClient();
  const { data, error } = await supabase.rpc('get_emergency_triage_by_token', {
    lookup_token: validToken,
  });

  if (error || !data) {
    notFound();
  }

  // 3. Runtime schema validation & privacy barrier
  const parsed = emergencyTriageSchema.safeParse(data);
  if (!parsed.success) {
    notFound();
  }

  return <EmergencyTriageView triage={parsed.data} token={validToken} />;
}

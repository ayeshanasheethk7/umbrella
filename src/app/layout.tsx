import React from 'react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { redirect } from 'next/navigation';
import { Shield, LogOut, User, Stethoscope } from 'lucide-react';
import { MotionConfig } from 'framer-motion';
import { createClient } from '@/lib/supabase/server';
import './globals.css';

export const metadata: Metadata = {
  title: 'Umbrella — Emergency Medical ID Platform',
  description:
    'Instant, zero-login roadside emergency triage indicators with verified clinical provider updates.',
  viewport: 'width=device-width, initial-scale=1, maximum-scale=5',
};

async function handleLogout() {
  'use server';
  const supabase = createClient();
  await supabase.auth.signOut();
  redirect('/login');
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  let user = null;
  let account = null;

  try {
    const supabase = createClient();
    // N3: Server code identifies user strictly with auth.getUser()
    const {
      data: { user: currentUser },
    } = await supabase.auth.getUser();

    user = currentUser;

    if (user) {
      // Query role from public.accounts per N3
      const { data } = await supabase
        .from('accounts')
        .select('full_name, role, doctor_status')
        .eq('id', user.id)
        .single();
      account = data;
    }
  } catch {
    // Graceful fallback if database connection / environment is not configured during static check
    user = null;
    account = null;
  }

  return (
    <html lang="en">
      <body className="min-h-screen bg-canvas text-text-primary antialiased flex flex-col font-sans">
        {/* Apple-style Glass Navigation Header */}
        <header className="sticky top-0 z-40 w-full glass-header">
          <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
            {/* Brand Logo */}
            <Link
              href="/"
              className="flex items-center gap-2.5 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action"
              aria-label="Umbrella Emergency Medical ID - Home"
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-clinical-critical text-white shadow-xs">
                <Shield className="h-5 w-5" aria-hidden="true" />
              </div>
              <div className="flex flex-col">
                <span className="text-base font-bold tracking-tight text-text-primary leading-tight">
                  Umbrella
                </span>
                <span className="text-[10px] font-medium uppercase tracking-wider text-text-body-secondary leading-none">
                  Emergency ID
                </span>
              </div>
            </Link>

            {/* Navigation Links (Desktop) */}
            <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
              <Link
                href="/#emergency-lookup"
                className="text-text-body-secondary hover:text-text-primary transition-colors"
              >
                Emergency Lookup
              </Link>
              <Link
                href="/portal/patient"
                className="text-text-body-secondary hover:text-text-primary transition-colors"
              >
                Patient Portal
              </Link>
              <Link
                href="/portal/doctor"
                className="text-text-body-secondary hover:text-text-primary transition-colors"
              >
                Doctor Portal
              </Link>
            </nav>

            {/* Active Session Indicator / Auth CTAs */}
            <div className="flex items-center gap-3">
              {user && account ? (
                <div className="flex items-center gap-3">
                  <div className="hidden sm:flex flex-col items-end text-right">
                    <span className="text-sm font-semibold text-text-primary leading-tight">
                      {account.full_name || user.email}
                    </span>
                    <span className="text-[11px] font-medium text-text-body-secondary flex items-center gap-1">
                      {account.role === 'doctor' ? (
                        <>
                          <Stethoscope className="h-3 w-3 text-accent-action" />
                          Physician {account.doctor_status === 'approved' ? '(Verified)' : '(Pending)'}
                        </>
                      ) : (
                        <>
                          <User className="h-3 w-3 text-text-body-secondary" />
                          Patient
                        </>
                      )}
                    </span>
                  </div>

                  <form action={handleLogout}>
                    <button
                      type="submit"
                      className="inline-flex h-[44px] min-h-[44px] items-center gap-1.5 rounded-lg border border-black/10 bg-surface px-4 text-xs font-medium text-text-primary hover:bg-black/5 active:bg-black/10 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action"
                      aria-label="Sign out of Umbrella"
                    >
                      <LogOut className="h-3.5 w-3.5" aria-hidden="true" />
                      <span>Sign Out</span>
                    </button>
                  </form>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Link
                    href="/login"
                    className="inline-flex h-[44px] min-h-[44px] items-center justify-center rounded-lg px-4 text-xs font-medium text-text-primary hover:bg-black/5 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action"
                  >
                    Sign In
                  </Link>
                  <Link
                    href="/signup"
                    className="inline-flex h-[44px] min-h-[44px] items-center justify-center rounded-lg bg-accent-action px-4 text-xs font-semibold text-white hover:bg-accent-action-hover active:bg-accent-action-active transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action shadow-xs"
                  >
                    Sign Up
                  </Link>
                </div>
              )}
            </div>
          </div>

          {/* Mobile Responsive Navigation Bar */}
          <nav
            aria-label="Mobile navigation"
            className="flex md:hidden items-center justify-around border-t border-black/5 bg-surface/80 px-4 py-1 text-xs font-medium text-text-body-secondary"
          >
            <Link
              href="/#emergency-lookup"
              className="inline-flex h-[44px] min-h-[44px] items-center px-2 hover:text-text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action"
            >
              Emergency
            </Link>
            <Link
              href="/portal/patient"
              className="inline-flex h-[44px] min-h-[44px] items-center px-2 hover:text-text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action"
            >
              Patient Portal
            </Link>
            <Link
              href="/portal/doctor"
              className="inline-flex h-[44px] min-h-[44px] items-center px-2 hover:text-text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action"
            >
              Doctor Portal
            </Link>
          </nav>
        </header>

        {/* Main Application Shell with MotionConfig wrapper */}
        <MotionConfig reducedMotion="user">
          <div id="main-content" className="flex-1">
            {children}
          </div>
        </MotionConfig>

        {/* Global Footer */}
        <footer className="w-full border-t border-black/10 bg-surface py-8 text-center text-xs text-text-body-secondary">
          <div className="mx-auto max-w-6xl px-4 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-text-primary font-medium">
              <Shield className="h-4 w-4 text-clinical-critical" />
              <span>Umbrella Roadside Emergency Triage Platform</span>
            </div>
            <div className="flex items-center gap-6">
              <span>Zero-Login Emergency Route</span>
              <span>Postgres RLS Enforced</span>
              <span>Whitelisted RPC Data Only</span>
            </div>
            <div className="text-text-body-secondary">
              &copy; {new Date().getFullYear()} Umbrella ID. All rights reserved.
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}

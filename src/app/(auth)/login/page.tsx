'use client';

import React, { useState, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Shield, AlertCircle, ArrowRight } from 'lucide-react';
import { createClient } from '@/lib/supabase/client';
import { loginSchema } from '@/lib/schemas';
import { safeNext } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextUrl = searchParams.get('next');

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [authError, setAuthError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    setFieldErrors({});

    // Validate inputs with Zod
    const result = loginSchema.safeParse({ email, password });
    if (!result.success) {
      const errors: Record<string, string> = {};
      result.error.errors.forEach((err) => {
        if (err.path[0]) {
          errors[String(err.path[0])] = err.message;
        }
      });
      setFieldErrors(errors);
      return;
    }

    setIsLoading(true);

    try {
      const supabase = createClient();
      // Real Supabase Auth signInWithPassword call per Non-negotiable N5
      const { data, error } = await supabase.auth.signInWithPassword({
        email: result.data.email,
        password: result.data.password,
      });

      if (error) {
        setAuthError(error.message || 'Invalid email or password.');
        setIsLoading(false);
        return;
      }

      if (data.user) {
        // Query server role from accounts table per Non-negotiable N3
        const { data: account } = await supabase
          .from('accounts')
          .select('role')
          .eq('id', data.user.id)
          .single();

        const destination = nextUrl
          ? safeNext(nextUrl, account?.role === 'doctor' ? '/portal/doctor' : '/portal/patient')
          : account?.role === 'doctor'
            ? '/portal/doctor'
            : '/portal/patient';

        router.push(destination);
        router.refresh();
      }
    } catch (err) {
      setAuthError('An unexpected network error occurred. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md bg-surface shadow-ceiling border border-black/10">
      <CardHeader className="text-center pb-6">
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-black/5 text-accent-action">
          <Shield className="h-6 w-6" aria-hidden="true" />
        </div>
        <CardTitle className="text-2xl font-bold tracking-tight text-text-primary">
          Sign In to Umbrella
        </CardTitle>
        <CardDescription className="text-sm text-text-body-secondary mt-1">
          Access your emergency medical records or physician clinical portal.
        </CardDescription>
      </CardHeader>

      <CardContent>
        {authError && (
          <div
            className="mb-5 flex items-start gap-3 rounded-xl border border-clinical-critical/30 bg-clinical-critical/10 p-3.5 text-sm text-clinical-critical-text"
            role="alert"
          >
            <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
            <div className="leading-snug">{authError}</div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <Input
            id="login-email"
            type="email"
            label="Email Address"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={fieldErrors.email}
            placeholder="patient@example.com"
          />

          <Input
            id="login-password"
            type="password"
            label="Password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={fieldErrors.password}
            placeholder="Enter your password"
          />

          <Button
            type="submit"
            size="lg"
            className="w-full mt-2 font-semibold"
            isLoading={isLoading}
          >
            Sign In
            <ArrowRight className="ml-2 h-4 w-4" aria-hidden="true" />
          </Button>
        </form>

        <div className="mt-6 text-center text-sm text-text-body-secondary border-t border-black/5 pt-5">
          Don't have an Umbrella account?{' '}
          <Link
            href="/signup"
            className="font-medium text-accent-action hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-action rounded-sm"
          >
            Sign Up
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}

export default function LoginPage() {
  return (
    <div className="flex min-h-[calc(100vh-140px)] items-center justify-center px-4 py-12">
      <Suspense fallback={<div className="text-sm text-text-body-secondary">Loading sign in...</div>}>
        <LoginForm />
      </Suspense>
    </div>
  );
}

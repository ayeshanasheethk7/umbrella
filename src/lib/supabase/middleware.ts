import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';
import type { Database } from './types';
import { safeNext } from '@/lib/utils';

/**
 * Middleware session updater and route guard
 * Strictly complies with:
 * - N3: Server code identifies user strictly via supabase.auth.getUser()
 * - N3: Role & status verified from public.accounts, never user_metadata
 * - D1: Doctor access gated by accounts.doctor_status
 * - D15: Redirect destination sanitized against open redirects
 */
export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({
    request,
  });

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

  const supabase = createServerClient<Database>(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value }) =>
          request.cookies.set(name, value)
        );
        supabaseResponse = NextResponse.next({
          request,
        });
        cookiesToSet.forEach(({ name, value, options }) =>
          supabaseResponse.cookies.set(name, value, options)
        );
      },
    },
  });

  // IMPORTANT: N3 - Caller is strictly identified with auth.getUser()
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const pathname = request.nextUrl.pathname;

  // 1. Route Protection for Protected Portals (/portal/*)
  if (pathname.startsWith('/portal')) {
    if (!user) {
      const redirectUrl = request.nextUrl.clone();
      redirectUrl.pathname = '/login';
      const rawNext = pathname + request.nextUrl.search;
      redirectUrl.searchParams.set('next', safeNext(rawNext, '/portal/patient'));
      return NextResponse.redirect(redirectUrl);
    }

    // Role-specific verification
    if (pathname.startsWith('/portal/doctor')) {
      const { data: account } = await supabase
        .from('accounts')
        .select('role, doctor_status')
        .eq('id', user.id)
        .single();

      // DECISIONS D1: Doctor access requires role === 'doctor' AND doctor_status === 'approved'
      const isApprovedDoctor = account?.role === 'doctor' && account?.doctor_status === 'approved';

      if (!account || account.role !== 'doctor') {
        // Patient attempting to access doctor portal -> redirect to patient portal
        const redirectUrl = request.nextUrl.clone();
        redirectUrl.pathname = '/portal/patient';
        return NextResponse.redirect(redirectUrl);
      }

      if (account.doctor_status !== 'approved') {
        if (pathname !== '/portal/doctor/pending') {
          const redirectUrl = request.nextUrl.clone();
          redirectUrl.pathname = '/portal/doctor/pending';
          return NextResponse.redirect(redirectUrl);
        }
      } else if (pathname === '/portal/doctor/pending') {
        const redirectUrl = request.nextUrl.clone();
        redirectUrl.pathname = '/portal/doctor';
        return NextResponse.redirect(redirectUrl);
      }
    }
  }

  // 2. Redirect authenticated users away from Auth pages (/login, /signup)
  if (pathname === '/login' || pathname === '/signup') {
    if (user) {
      const nextParam = request.nextUrl.searchParams.get('next');
      if (nextParam) {
        const sanitized = safeNext(nextParam, '');
        if (sanitized) {
          return NextResponse.redirect(new URL(sanitized, request.url));
        }
      }

      // Query account role to land user on appropriate portal
      const { data: account } = await supabase
        .from('accounts')
        .select('role, doctor_status')
        .eq('id', user.id)
        .single();

      const targetPath =
        account?.role === 'doctor'
          ? (account.doctor_status === 'approved' ? '/portal/doctor' : '/portal/doctor/pending')
          : '/portal/patient';
      return NextResponse.redirect(new URL(targetPath, request.url));
    }
  }

  return supabaseResponse;
}

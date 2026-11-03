import { NextResponse, type NextRequest } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { safeNext } from '@/lib/utils';

/**
 * Auth Callback Route Handler
 * Exchanges OAuth or email verification code for an authenticated session
 */
export async function GET(request: NextRequest) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get('code');
  const next = safeNext(searchParams.get('next'), '/portal/patient');

  if (code) {
    const supabase = createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  // Return to login with error indicator if exchange fails
  return NextResponse.redirect(`${origin}/login?error=auth_callback_failed`);
}

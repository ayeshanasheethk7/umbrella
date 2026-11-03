import { createClient as createSupabaseClient } from '@supabase/supabase-js';
import type { Database } from './types';

/**
 * Cookie-less anonymous Supabase client for public emergency triage route (/emergency/[token]).
 * Non-negotiables:
 * - N1: Public zero-login route reads data ONLY through RPC get_emergency_triage_by_token.
 * - N4: Uses ONLY anon/publishable key; zero backend administrative key usage.
 * - Cookie-less: Does not access or bind user session cookies.
 */
export function createAnonClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error('Missing Supabase public configuration environment variables');
  }

  return createSupabaseClient<Database>(supabaseUrl, supabaseAnonKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
      detectSessionInUrl: false,
    },
  });
}

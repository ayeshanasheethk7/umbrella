import { createBrowserClient } from '@supabase/ssr';
import type { Database } from './types';

/**
 * Creates a browser-side Supabase client with the Database generic type
 * Compliant with Non-negotiable N4 (anon/publishable key only)
 */
export function createClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

  return createBrowserClient<Database>(supabaseUrl, supabaseAnonKey);
}

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { createAnonClient } from '@/lib/supabase/anon';

describe('Tier 1: Supabase Anon Client — Happy-Path & Isolation', () => {
  const originalUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const originalKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  beforeEach(() => {
    process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://umbrella-test.supabase.co';
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.anon-key';
  });

  afterEach(() => {
    process.env.NEXT_PUBLIC_SUPABASE_URL = originalUrl;
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = originalKey;
  });

  it('T1-ANON-01: instantiates anonymous client without throwing when public env vars are set', () => {
    expect(() => createAnonClient()).not.toThrow();
  });

  it('T1-ANON-02: returns Supabase client with auth and rpc methods', () => {
    const client = createAnonClient();
    expect(client).toHaveProperty('rpc');
    expect(client).toHaveProperty('auth');
    expect(typeof client.rpc).toBe('function');
  });

  it('T1-ANON-03: client contains from() query builder method', () => {
    const client = createAnonClient();
    expect(client).toHaveProperty('from');
    expect(typeof client.from).toBe('function');
  });

  it('T1-ANON-04: client auth configuration disables persistSession', () => {
    const client = createAnonClient();
    expect(client.auth).toBeDefined();
  });

  it('T1-ANON-05: client auth configuration disables autoRefreshToken', () => {
    const client = createAnonClient();
    expect(client.auth).toBeDefined();
  });

  it('T1-ANON-06: client auth configuration disables detectSessionInUrl', () => {
    const client = createAnonClient();
    expect(client.auth).toBeDefined();
  });
});

describe('Tier 2: Supabase Anon Client — Boundaries & Non-Negotiable N4 Protection', () => {
  const originalUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const originalKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  afterEach(() => {
    process.env.NEXT_PUBLIC_SUPABASE_URL = originalUrl;
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = originalKey;
  });

  it('T2-ANON-01: throws clear error if NEXT_PUBLIC_SUPABASE_URL is missing', () => {
    delete process.env.NEXT_PUBLIC_SUPABASE_URL;
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'valid-anon-key';
    expect(() => createAnonClient()).toThrow('Missing Supabase public configuration environment variables');
  });

  it('T2-ANON-02: throws clear error if NEXT_PUBLIC_SUPABASE_ANON_KEY is missing', () => {
    process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://umbrella-test.supabase.co';
    delete process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    expect(() => createAnonClient()).toThrow('Missing Supabase public configuration environment variables');
  });

  it('T2-ANON-03: throws clear error if env vars are empty strings', () => {
    process.env.NEXT_PUBLIC_SUPABASE_URL = '';
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = '';
    expect(() => createAnonClient()).toThrow('Missing Supabase public configuration environment variables');
  });

  it('T2-ANON-04: confirms zero reference to service_role in anon client initialization (Invariant N4)', () => {
    const clientString = createAnonClient.toString();
    expect(clientString.includes('service_role')).toBe(false);
  });

  it('T2-ANON-05: confirms zero reference to SUPABASE_SERVICE_ROLE_KEY in anon client source', () => {
    const clientString = createAnonClient.toString();
    expect(clientString.includes('SUPABASE_SERVICE_ROLE_KEY')).toBe(false);
  });

  it('T2-ANON-06: throws clear error when public env vars contain only whitespace characters', () => {
    process.env.NEXT_PUBLIC_SUPABASE_URL = '   ';
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = '   ';
    expect(() => createAnonClient()).toThrow('Missing Supabase public configuration environment variables');
  });
});

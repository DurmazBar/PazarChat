/**
 * Supabase client (web tarafı).
 *
 * Web tarafı anon key kullanır (RLS ile sınırlı). Sadece authenticated user
 * kendi user_id'sine ait verileri okuyabilir. Faz 3'te /hesabim sayfası için
 * aktif edilecek.
 */
import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

let _client: SupabaseClient | null = null;

export function getSupabase(): SupabaseClient {
  if (!url || !anonKey) {
    throw new Error(
      "Supabase env eksik: NEXT_PUBLIC_SUPABASE_URL ve NEXT_PUBLIC_SUPABASE_ANON_KEY .env.local'da olmalı."
    );
  }
  if (!_client) {
    _client = createClient(url, anonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: false,
      },
    });
  }
  return _client;
}

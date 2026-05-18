-- =============================================================================
-- 002 — Function search_path hardening
-- =============================================================================
-- Why: Postgres function'ları mutable search_path ile çalışırsa, kötü niyetli
-- bir attacker kendi schema'sını PATH'e ekleyip fonksiyonun yanlış nesneye
-- bakmasını sağlayabilir (search_path injection). Best practice: her function'a
-- açıkça `set search_path = ...` ekle.
--
-- Ref: https://supabase.com/docs/guides/database/database-linter?lint=0011_function_search_path_mutable
-- =============================================================================

create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;


create or replace function public.generate_api_key()
returns text
language plpgsql
set search_path = public, extensions, pg_catalog
as $$
begin
  -- gen_random_bytes pgcrypto extension'ında, Supabase'de "extensions" schema'sında
  return 'pzc_' || encode(gen_random_bytes(18), 'hex');
end;
$$;


create or replace function public.seed_default_ready_replies()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  insert into public.ready_replies (user_id, label, content, sort_order)
  values
    (new.id, '100m son fiyat',          '100m son fiyat',                 10),
    (new.id, 'Pazarlık yok',            'Pazarlık yok',                   20),
    (new.id, '5 dk geliyorum',          '5 dakika içinde geliyorum',      30),
    (new.id, 'Siparişin var mı?',       'Siparişin var mı?',              40),
    (new.id, 'Meşgulüm, sonra',         'Şu an meşgulüm, biraz sonra dönerim', 50);
  return new;
end;
$$;

-- =============================================================================
-- 004 — Bot: Davetiye kullanımı (atomic)
-- =============================================================================
-- /davetiye CODE komutu çağrıldığında bot şu adımları **atomik** yapmak zorunda:
--   1. invite_codes'ta kodu bul + kilitle (FOR UPDATE — double-use önlemek)
--   2. subscriptions'a beta kaydı ekle (plan='beta', valid_until = now + beta_days)
--   3. licenses'a yeni kayıt ekle (api_key default trigger ile auto-generate)
--   4. invite_codes'u used_by + used_at ile güncelle
--   5. audit_log'a kayıt ekle
--
-- Bu fonksiyon SECURITY DEFINER, service_role'den çağrılır. anon/authenticated
-- erişemez (revoke explicit).
--
-- p_user_id: bot ÖNCE public.users'a kayıt yapar (Telegram bilgileri ile), o
-- user'ın id'sini buraya geçer.
-- =============================================================================

create or replace function public.bot_redeem_invite(
  p_user_id uuid,
  p_invite_code text
)
returns table (
  license_id uuid,
  api_key text,
  valid_until timestamptz
)
language plpgsql
security definer
set search_path = public
as $$
declare
  v_invite_id uuid;
  v_beta_days int;
  v_subscription_id uuid;
  v_license_id uuid;
  v_api_key text;
  v_valid_until timestamptz;
begin
  -- 1) Davetiyeyi bul + kilitle. Aynı kodun iki kez kullanılmasını önle.
  select id, beta_days
    into v_invite_id, v_beta_days
  from public.invite_codes
  where code = p_invite_code
    and used_by is null
    and (expires_at is null or expires_at > now())
  for update;

  if v_invite_id is null then
    raise exception 'Davetiye kodu gecersiz, suresi dolmus veya zaten kullanilmis.';
  end if;

  v_valid_until := now() + (v_beta_days || ' days')::interval;

  -- 2) Subscription oluştur (beta planı)
  insert into public.subscriptions (
    user_id, plan, status, valid_from, valid_until, source, source_ref
  ) values (
    p_user_id, 'beta', 'active', now(), v_valid_until, 'invite', v_invite_id::text
  ) returning id into v_subscription_id;

  -- 3) License oluştur (api_key default fonksiyon ile üretilir)
  insert into public.licenses (user_id)
  values (p_user_id)
  returning id, public.licenses.api_key
    into v_license_id, v_api_key;

  -- 4) Davetiye'yi kullanılmış işaretle
  update public.invite_codes
  set used_by = p_user_id,
      used_at = now()
  where id = v_invite_id;

  -- 5) Audit log
  insert into public.audit_log (user_id, action, metadata)
  values (
    p_user_id,
    'invite_redeemed',
    jsonb_build_object(
      'invite_id', v_invite_id,
      'subscription_id', v_subscription_id,
      'license_id', v_license_id,
      'beta_days', v_beta_days
    )
  );

  return query select v_license_id, v_api_key, v_valid_until;
end;
$$;

-- Sadece service_role çağırsın. anon ve authenticated explicit kapatılır.
revoke execute on function public.bot_redeem_invite(uuid, text) from public, anon, authenticated;

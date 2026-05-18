-- =============================================================================
-- 003 — PC Service RPC Functions
-- =============================================================================
-- PC servisi service_role key kullanmaz (PC saldırıya uğrarsa tüm DB tehlikede).
-- Bunun yerine API key (licenses.api_key) ile çağrılan SECURITY DEFINER fonksiyonlar:
--   - pc_heartbeat: lisans doğrula + machine fingerprint kontrol + last_heartbeat update
--   - pc_insert_incoming_message: yakalanan PM'i mesajlara ekle
--   - pc_get_pending_outgoing: bekleyen cevapları (outgoing+new) çek
--   - pc_mark_message_sent: cevap PC panosuna kopyalandı olarak işaretle
--
-- Tüm fonksiyonlar API key validation yapar, geçersizse hata fırlatır.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Internal helper: API key'i doğrula, license + user id döndür
-- -----------------------------------------------------------------------------
-- Why ayrı fonksiyon: tüm RPC'lerde aynı doğrulama mantığını tekrarlamamak için.
create or replace function public._validate_api_key(p_api_key text)
returns table (license_id uuid, user_id uuid)
language plpgsql
security definer
set search_path = public
as $$
begin
  return query
  select l.id, l.user_id
  from public.licenses l
  inner join public.subscriptions s on s.user_id = l.user_id
  where l.api_key = p_api_key
    and l.is_active = true
    and l.revoked_at is null
    and s.status = 'active'
    and s.valid_until > now()
  order by s.valid_until desc
  limit 1;

  if not found then
    raise exception 'Geçersiz, iptal edilmiş veya abonelik süresi dolmuş API key'
      using errcode = '28000';   -- invalid_authorization_specification
  end if;
end;
$$;


-- -----------------------------------------------------------------------------
-- pc_heartbeat
-- -----------------------------------------------------------------------------
-- PC servisi 60 saniyede bir çağırır. İlk çağrıda machine_fingerprint NULL ise
-- set edilir; sonraki çağrılarda mismatch varsa hata (anti-paylaşım).
-- Karakter adı/server güncellenebilir.
create or replace function public.pc_heartbeat(
  p_api_key text,
  p_machine_fingerprint text,
  p_character_name text,
  p_server_name text default null
)
returns table (license_id uuid, valid_until timestamptz)
language plpgsql
security definer
set search_path = public
as $$
declare
  v_license_id uuid;
  v_user_id uuid;
  v_existing_fingerprint text;
  v_valid_until timestamptz;
begin
  -- 1) API key + abonelik doğrula
  select t.license_id, t.user_id into v_license_id, v_user_id
  from public._validate_api_key(p_api_key) t;

  -- 2) Fingerprint kontrolü
  select machine_fingerprint into v_existing_fingerprint
  from public.licenses where id = v_license_id;

  if v_existing_fingerprint is null then
    -- İlk login: fingerprint'i kaydet
    update public.licenses
    set machine_fingerprint = p_machine_fingerprint
    where id = v_license_id;
  elsif v_existing_fingerprint <> p_machine_fingerprint then
    raise exception 'Bu lisans başka bir bilgisayara bağlı. Lisans transfer için destek isteyin.'
      using errcode = '28000';
  end if;

  -- 3) Heartbeat + karakter bilgileri güncelle
  update public.licenses
  set last_heartbeat = now(),
      character_name = coalesce(p_character_name, character_name),
      server_name    = coalesce(p_server_name, server_name)
  where id = v_license_id;

  -- 4) Abonelik bitiş tarihini döndür
  select s.valid_until into v_valid_until
  from public.subscriptions s
  where s.user_id = v_user_id and s.status = 'active'
  order by s.valid_until desc limit 1;

  return query select v_license_id, v_valid_until;
end;
$$;


-- -----------------------------------------------------------------------------
-- pc_insert_incoming_message
-- -----------------------------------------------------------------------------
-- Yakalanan PM'i kaydeder. content_hash duplicate kontrolü için kullanılır.
-- Aynı (license_id, content_hash) 60 saniye içinde varsa duplicate sayılır,
-- sessizce atlanır (no-op, mevcut id döner).
create or replace function public.pc_insert_incoming_message(
  p_api_key text,
  p_from_character text,
  p_to_character text,
  p_content text,
  p_content_hash text
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_license_id uuid;
  v_user_id uuid;
  v_existing_id uuid;
  v_message_id uuid;
begin
  -- API key doğrula
  select t.license_id, t.user_id into v_license_id, v_user_id
  from public._validate_api_key(p_api_key) t;

  -- Duplicate kontrol: aynı hash son 60 saniyede var mı?
  select id into v_existing_id
  from public.messages
  where license_id = v_license_id
    and content_hash = p_content_hash
    and created_at > now() - interval '60 seconds'
  limit 1;

  if v_existing_id is not null then
    return v_existing_id;  -- duplicate, no-op
  end if;

  -- Yeni mesaj
  insert into public.messages (
    user_id, license_id, direction,
    from_character, to_character, content, content_hash, status
  ) values (
    v_user_id, v_license_id, 'incoming',
    p_from_character, p_to_character, p_content, p_content_hash, 'new'
  ) returning id into v_message_id;

  return v_message_id;
end;
$$;


-- -----------------------------------------------------------------------------
-- pc_get_pending_outgoing
-- -----------------------------------------------------------------------------
-- Bot tarafından yazılan ve PC'ye iletilmesi bekleyen cevapları döndürür.
-- PC servisi her 2-3 saniyede çağırır (polling). Realtime gerekmez.
create or replace function public.pc_get_pending_outgoing(p_api_key text)
returns table (
  id uuid,
  to_character text,
  content text,
  created_at timestamptz
)
language plpgsql
security definer
set search_path = public
as $$
declare
  v_license_id uuid;
begin
  select t.license_id into v_license_id
  from public._validate_api_key(p_api_key) t;

  return query
  select m.id, m.to_character, m.content, m.created_at
  from public.messages m
  where m.license_id = v_license_id
    and m.direction = 'outgoing'
    and m.status = 'new'
  order by m.created_at asc
  limit 10;
end;
$$;


-- -----------------------------------------------------------------------------
-- pc_mark_message_sent
-- -----------------------------------------------------------------------------
-- Cevap pano'ya kopyalanınca PC servisi bu fonksiyonu çağırır.
-- status → 'sent_to_pc' olur, bot kullanıcıya "Cevabın PC'de hazır" gösterir.
create or replace function public.pc_mark_message_sent(
  p_api_key text,
  p_message_id uuid
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_license_id uuid;
begin
  select t.license_id into v_license_id
  from public._validate_api_key(p_api_key) t;

  update public.messages
  set status = 'sent_to_pc'
  where id = p_message_id
    and license_id = v_license_id      -- başka lisansın mesajına dokunamasın
    and direction = 'outgoing'
    and status = 'new';

  if not found then
    raise exception 'Mesaj bulunamadı veya zaten işlenmiş'
      using errcode = '02000';   -- no_data
  end if;
end;
$$;


-- -----------------------------------------------------------------------------
-- İzinler — anon role'üne sadece public RPC'leri çağırma yetkisi
-- -----------------------------------------------------------------------------
-- _validate_api_key internal, anon çağıramaz (default zaten kapalı).
revoke execute on function public._validate_api_key(text) from public;

grant execute on function public.pc_heartbeat(text, text, text, text) to anon, authenticated;
grant execute on function public.pc_insert_incoming_message(text, text, text, text, text) to anon, authenticated;
grant execute on function public.pc_get_pending_outgoing(text) to anon, authenticated;
grant execute on function public.pc_mark_message_sent(text, uuid) to anon, authenticated;

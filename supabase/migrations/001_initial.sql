-- =============================================================================
-- PazarChat — 001 Initial Schema
-- =============================================================================
-- Telegram bot + multi-tenant + lisans sistemi + beta davetiye için temel şema.
-- Kararlar:
--   • Mesaj saklama: 30 gün (auto-delete sonraki migration'da, pg_cron ile)
--   • Hazır cevap: sistem default 5 adet + kullanıcı /cevaplar ile düzenler
--   • Heartbeat: PC servisi 60 saniyede bir last_heartbeat günceller
--   • RLS: tüm public tablolarda aktif, kullanıcı sadece kendi verisini görür
--   • Realtime: messages ve licenses publication'a eklenir
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Helpers
-- -----------------------------------------------------------------------------

-- updated_at otomatik güncelleme trigger fonksiyonu
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;


-- API key üretici: "pzc_" + 36 karakter hex (18 byte random)
-- Why: license rotation ve readability için sabit prefix. pgcrypto built-in.
create or replace function public.generate_api_key()
returns text
language plpgsql
as $$
begin
  return 'pzc_' || encode(gen_random_bytes(18), 'hex');
end;
$$;


-- =============================================================================
-- 1) users — Kullanıcı profili (auth.users ile 1:1, Telegram bağlantısı)
-- =============================================================================
-- Supabase Auth ile kayıt olan kullanıcının Telegram chat_id'sini bağlar.
-- telegram_chat_id ilk /davetiye CODE komutu sonrası kaydedilir.
create table public.users (
  id uuid primary key references auth.users(id) on delete cascade,
  telegram_chat_id bigint unique,
  telegram_username text,
  display_name text,
  status text not null default 'active'
    check (status in ('active', 'suspended', 'banned')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_users_telegram_chat_id on public.users(telegram_chat_id);

create trigger users_updated_at
  before update on public.users
  for each row execute function public.set_updated_at();


-- =============================================================================
-- 2) invite_codes — Beta davetiye kodları
-- =============================================================================
-- Admin tarafından üretilen tek kullanımlık kodlar. Beta testçiye verilir,
-- kullanıcı /davetiye CODE komutuyla bot'ta aktive eder.
create table public.invite_codes (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,
  notes text,                            -- "Ahmet için, KO tüccarı" gibi serbest not
  created_by uuid references auth.users(id),
  used_by uuid references public.users(id) on delete set null,
  used_at timestamptz,
  expires_at timestamptz,                -- null = süresiz
  beta_days int not null default 30,     -- aktivasyon sonrası kaç gün geçerli
  created_at timestamptz not null default now()
);

create index idx_invite_codes_code on public.invite_codes(code) where used_by is null;


-- =============================================================================
-- 3) subscriptions — Aboneliğin yaşam döngüsü
-- =============================================================================
-- 'beta' planı davetiye sonrası otomatik oluşur. 'monthly'/'quarterly'/'yearly'
-- ödeme sonrası oluşur veya yenilenir.
create table public.subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  plan text not null
    check (plan in ('beta', 'monthly', 'quarterly', 'yearly')),
  status text not null default 'active'
    check (status in ('active', 'expired', 'cancelled')),
  valid_from timestamptz not null default now(),
  valid_until timestamptz not null,
  source text not null
    check (source in ('invite', 'payment', 'admin')),
  source_ref text,                       -- davetiye id veya payment id (denormalize)
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_subscriptions_user_active
  on public.subscriptions(user_id, status, valid_until desc);

create trigger subscriptions_updated_at
  before update on public.subscriptions
  for each row execute function public.set_updated_at();


-- =============================================================================
-- 4) licenses — PC servisinin kimlik kanıtı
-- =============================================================================
-- 1 lisans = 1 PC kuralı. machine_fingerprint ilk login'de kaydedilir, sonraki
-- login'lerde eşleşme zorunlu (farklıysa eski kick edilir veya hesap suspend).
create table public.licenses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  api_key text unique not null default public.generate_api_key(),
  machine_fingerprint text,              -- CPU+disk+MAC hash; ilk login'de kaydedilir
  character_name text,                   -- KO karakter adı
  server_name text,
  is_active boolean not null default true,
  last_heartbeat timestamptz,            -- PC servisi 60 sn'de bir update eder
  revoked_at timestamptz,                -- iptal edilince doldurulur
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_licenses_api_key on public.licenses(api_key);
create index idx_licenses_user_active on public.licenses(user_id, is_active);

create trigger licenses_updated_at
  before update on public.licenses
  for each row execute function public.set_updated_at();


-- =============================================================================
-- 5) messages — Yakalanan PM'ler ve giden cevaplar
-- =============================================================================
-- Saklama süresi: 30 gün. Otomatik silme sonraki migration'da pg_cron ile.
-- content_hash duplicate filter için (OCR aynı PM'i tekrar yakalayabilir).
create table public.messages (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  license_id uuid references public.licenses(id) on delete set null,
  direction text not null
    check (direction in ('incoming', 'outgoing')),
  from_character text not null,
  to_character text not null,
  content text not null,
  content_hash text,                     -- (license_id, content) hash → duplicate önle
  status text not null default 'new'
    check (status in ('new', 'notified', 'replied', 'sent_to_pc', 'completed', 'failed')),
  telegram_message_id bigint,            -- bot'un gönderdiği mesaj ID (reply için)
  replied_at timestamptz,
  created_at timestamptz not null default now()
);

create index idx_messages_user_created
  on public.messages(user_id, created_at desc);

create index idx_messages_pending_outgoing
  on public.messages(user_id, status)
  where direction = 'outgoing' and status = 'new';

create index idx_messages_dup_window
  on public.messages(license_id, content_hash, created_at desc)
  where content_hash is not null;


-- =============================================================================
-- 6) ready_replies — Kullanıcının hazır cevap setleri
-- =============================================================================
-- Yeni kullanıcı kaydolunca trigger ile 5 default cevap eklenir.
-- Kullanıcı /cevaplar komutu ile ekler/siler/sıralar.
create table public.ready_replies (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  label text not null,                   -- buton üzerinde görünen kısa metin
  content text not null,                 -- PM'e gönderilecek tam metin
  sort_order int not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, label)
);

create index idx_ready_replies_user
  on public.ready_replies(user_id, sort_order);

create trigger ready_replies_updated_at
  before update on public.ready_replies
  for each row execute function public.set_updated_at();


-- Yeni kullanıcı eklendiğinde default 5 hazır cevap oluştur
create or replace function public.seed_default_ready_replies()
returns trigger
language plpgsql
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

create trigger users_seed_default_replies
  after insert on public.users
  for each row execute function public.seed_default_ready_replies();


-- =============================================================================
-- 7) payments — Ödeme kayıtları (faz 3'te aktif)
-- =============================================================================
-- iyzico/Shopier/manuel ödemelerin audit kaydı. subscriptions.source_ref ile
-- bağlanır.
create table public.payments (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  amount_try numeric(10, 2) not null,
  gateway text not null
    check (gateway in ('iyzico', 'shopier', 'manual', 'telegram_stars')),
  gateway_ref text,                      -- gateway'in döndürdüğü transaction ID
  status text not null default 'pending'
    check (status in ('pending', 'success', 'failed', 'refunded')),
  plan text not null                     -- hangi paket için ödeme yapıldı
    check (plan in ('monthly', 'quarterly', 'yearly')),
  metadata jsonb,                        -- gateway response detayları
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_payments_user_created
  on public.payments(user_id, created_at desc);

create trigger payments_updated_at
  before update on public.payments
  for each row execute function public.set_updated_at();


-- =============================================================================
-- 8) audit_log — KVKK ve müşteri destek için denetim kaydı
-- =============================================================================
-- Sensitive olmayan, append-only kayıt. Saklama süresi: 5 yıl (yasal).
-- RLS: kullanıcı kendi loglarını okuyabilir, ama yazma yetkisi yok (service_role).
create table public.audit_log (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id) on delete set null,
  action text not null,                  -- 'license_created', 'subscription_renewed', ...
  metadata jsonb,
  ip text,
  user_agent text,
  created_at timestamptz not null default now()
);

create index idx_audit_log_user_created
  on public.audit_log(user_id, created_at desc);

create index idx_audit_log_action_created
  on public.audit_log(action, created_at desc);


-- =============================================================================
-- RLS — Row Level Security
-- =============================================================================
-- Tüm tablolarda RLS aktif. Kullanıcı sadece kendi user_id'sine ait kayıtları
-- okuyabilir/değiştirebilir. PC servisi ve bot service_role ile bağlanır
-- (RLS bypass eder), web ise auth.uid() ile kullanıcı bağlamında çalışır.

alter table public.users           enable row level security;
alter table public.invite_codes    enable row level security;
alter table public.subscriptions   enable row level security;
alter table public.licenses        enable row level security;
alter table public.messages        enable row level security;
alter table public.ready_replies   enable row level security;
alter table public.payments        enable row level security;
alter table public.audit_log       enable row level security;

-- ---- users ----
create policy "users_select_own"
  on public.users for select
  using (auth.uid() = id);
create policy "users_update_own"
  on public.users for update
  using (auth.uid() = id) with check (auth.uid() = id);

-- ---- invite_codes ----
-- Sadece admin (service_role) erişebilir. Authenticated user görmez.
-- Davetiye doğrulaması bot tarafından service_role ile yapılır.

-- ---- subscriptions ----
create policy "subscriptions_select_own"
  on public.subscriptions for select
  using (auth.uid() = user_id);

-- ---- licenses ----
create policy "licenses_select_own"
  on public.licenses for select
  using (auth.uid() = user_id);
create policy "licenses_update_own_revoke"
  on public.licenses for update
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ---- messages ----
create policy "messages_select_own"
  on public.messages for select
  using (auth.uid() = user_id);
-- Insert ve update PC servisi/bot tarafından service_role ile yapılır.

-- ---- ready_replies ----
create policy "ready_replies_select_own"
  on public.ready_replies for select
  using (auth.uid() = user_id);
create policy "ready_replies_insert_own"
  on public.ready_replies for insert
  with check (auth.uid() = user_id);
create policy "ready_replies_update_own"
  on public.ready_replies for update
  using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "ready_replies_delete_own"
  on public.ready_replies for delete
  using (auth.uid() = user_id);

-- ---- payments ----
create policy "payments_select_own"
  on public.payments for select
  using (auth.uid() = user_id);
-- Insert/update sadece service_role (gateway callback).

-- ---- audit_log ----
create policy "audit_log_select_own"
  on public.audit_log for select
  using (auth.uid() = user_id);
-- Insert sadece service_role.


-- =============================================================================
-- Realtime Publication
-- =============================================================================
-- PC servisi ve bot bu tabloları WebSocket üzerinden anlık dinler.
alter publication supabase_realtime add table public.messages;
alter publication supabase_realtime add table public.licenses;

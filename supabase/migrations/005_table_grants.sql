-- =============================================================================
-- 005 — Table-level GRANT'lar
-- =============================================================================
-- Supabase projesinde "Automatically expose new tables" kapalı olduğu için
-- yeni yarattığımız tablolar default'ta hiçbir role'e GRANT almıyor.
-- service_role bile (RLS bypass etmesine rağmen) tabloya erişim için
-- table-level privilege gerektirir.
--
-- Bu migration:
--   - service_role: tüm tablolar üzerinde full access (bot bunu kullanır)
--   - authenticated: RLS-filtered access (web kullanıcısı için, faz 3+)
--   - anon: table-level grant YOK; sadece RPC fonksiyonları üzerinden erişir
--
-- Gelecekteki tablolar için default privileges set edilir (alter default).
-- =============================================================================

-- -----------------------------------------------------------------------------
-- service_role → tüm tablolarda full access
-- -----------------------------------------------------------------------------
grant all privileges on all tables in schema public to service_role;
grant all privileges on all sequences in schema public to service_role;
grant execute on all functions in schema public to service_role;

-- Gelecekteki tablolar/sequence'ler için default privilege
alter default privileges in schema public grant all on tables to service_role;
alter default privileges in schema public grant all on sequences to service_role;
alter default privileges in schema public grant execute on functions to service_role;


-- -----------------------------------------------------------------------------
-- authenticated → RLS ile filtreli access (web kullanıcısı)
-- -----------------------------------------------------------------------------
-- RLS policy'ler zaten her kullanıcıyı kendi user_id'siyle sınırlandırıyor;
-- buradaki table-level grant sadece PostgREST'in tabloyu görebilmesi için.
grant select, insert, update, delete on
  public.users,
  public.subscriptions,
  public.licenses,
  public.messages,
  public.ready_replies,
  public.payments
to authenticated;

-- audit_log için authenticated sadece okuyabilir (RLS kendi loglarına filtreler)
grant select on public.audit_log to authenticated;

-- invite_codes authenticated görmemeli (service_role only) — hiç grant verilmez


-- -----------------------------------------------------------------------------
-- anon → hiç table grant verilmez
-- -----------------------------------------------------------------------------
-- PC servisi anon key ile bağlanır ama tüm işlemleri RPC fonksiyonları
-- (pc_heartbeat, pc_insert_incoming_message vs.) üzerinden yapar. RPC grant'ı
-- migration 003'te zaten verildi.

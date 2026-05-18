"""
PazarChat Telegram Bot — Supabase Service
==========================================
Bot'un DB ile konuştuğu tek nokta. Tüm SQL/RPC çağrıları buradan geçer.

Bot service_role key kullanır (sunucu side-only). Bu key RLS bypass eder,
admin yetkisi vardır — .env'de saklanır, asla istemci tarafına gitmez.

Supabase Python SDK senkron çalışır; bot async olduğu için potansiyel olarak
blocking ama her çağrı ms-cinsinden. Yoğunluk arttığında asyncio.to_thread()
ile sarmalanabilir.
"""

from __future__ import annotations

import logging
import secrets
import string
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from supabase import Client, create_client

from config import settings


logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Data classes — DB satırlarını tip güvenli paketle
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class BotUser:
    """Bot'a kayıtlı bir kullanıcı (public.users + Telegram bilgileri)."""
    id: str
    telegram_chat_id: int
    telegram_username: Optional[str]
    display_name: Optional[str]
    status: str  # 'active' | 'suspended' | 'banned'


@dataclass(frozen=True)
class RedeemResult:
    """bot_redeem_invite RPC dönüşü."""
    license_id: str
    api_key: str
    valid_until: datetime


@dataclass(frozen=True)
class UserStatus:
    """/durum komutu için derlenmiş özet."""
    user: BotUser
    has_active_subscription: bool
    subscription_plan: Optional[str]
    valid_until: Optional[datetime]
    api_key: Optional[str]
    license_id: Optional[str]
    last_heartbeat: Optional[datetime]
    character_name: Optional[str]


@dataclass(frozen=True)
class IncomingMessage:
    """Polling sırasında çekilen, henüz bildirilmemiş bir PM."""
    id: str
    user_id: str
    telegram_chat_id: int
    from_character: str
    to_character: str
    content: str
    created_at: datetime


# -----------------------------------------------------------------------------
# Service
# -----------------------------------------------------------------------------

class SupabaseService:
    """Bot'un DB layer'ı. Async değil; bot içinde await edilmez."""

    def __init__(self) -> None:
        self._client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )

    # ------------------------------------------------------------------
    # User lifecycle
    # ------------------------------------------------------------------

    def get_user_by_chat_id(self, chat_id: int) -> Optional[BotUser]:
        """public.users'tan Telegram chat_id ile kullanıcıyı bul."""
        resp = (
            self._client.table("users")
            .select("id, telegram_chat_id, telegram_username, display_name, status")
            .eq("telegram_chat_id", chat_id)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        if not rows:
            return None
        return _row_to_user(rows[0])

    def ensure_user_exists(
        self,
        chat_id: int,
        username: Optional[str],
        display_name: Optional[str],
    ) -> BotUser:
        """Kullanıcı yoksa auth.users + public.users oluştur, varsa metadata güncelle.

        Why iki tablo: public.users.id auth.users.id'ye foreign key. Önce auth
        user yaratmak gerek (admin.create_user). Email dummy.
        """
        existing = self.get_user_by_chat_id(chat_id)
        if existing:
            # Telegram username değişmiş olabilir — sessizce update et
            if existing.telegram_username != username or existing.display_name != display_name:
                self._client.table("users").update({
                    "telegram_username": username,
                    "display_name": display_name,
                }).eq("id", existing.id).execute()
            return existing

        # 1) Supabase Auth'ta dummy user yarat
        email = settings.internal_email_for(chat_id)
        password = _random_password()
        try:
            auth_resp = self._client.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,  # email doğrulama atla
                "user_metadata": {
                    "source": "telegram_bot",
                    "telegram_chat_id": chat_id,
                },
            })
        except Exception as e:
            logger.exception("auth.admin.create_user başarısız chat_id=%d", chat_id)
            raise RuntimeError(f"Kullanıcı oluşturulamadı: {e}") from e

        auth_user = auth_resp.user
        if not auth_user or not auth_user.id:
            raise RuntimeError("auth.admin.create_user kullanıcı döndürmedi")

        # 2) public.users INSERT (id = auth.users.id)
        # Bu INSERT trigger (seed_default_ready_replies) ile otomatik 5 hazır cevap üretir
        self._client.table("users").insert({
            "id": auth_user.id,
            "telegram_chat_id": chat_id,
            "telegram_username": username,
            "display_name": display_name,
        }).execute()

        logger.info("Yeni kullanıcı: chat_id=%d username=%r id=%s", chat_id, username, auth_user.id)
        return BotUser(
            id=auth_user.id,
            telegram_chat_id=chat_id,
            telegram_username=username,
            display_name=display_name,
            status="active",
        )

    # ------------------------------------------------------------------
    # Davetiye + lisans
    # ------------------------------------------------------------------

    def redeem_invite(self, user_id: str, invite_code: str) -> RedeemResult:
        """bot_redeem_invite RPC çağır. Atomik: subscription + license + invite update."""
        resp = self._client.rpc("bot_redeem_invite", {
            "p_user_id": user_id,
            "p_invite_code": invite_code,
        }).execute()
        rows = resp.data or []
        if not rows:
            raise RuntimeError("RPC boş cevap döndü")
        row = rows[0]
        return RedeemResult(
            license_id=row["license_id"],
            api_key=row["api_key"],
            valid_until=_parse_dt(row["valid_until"]),
        )

    def create_invite_code(
        self,
        notes: str,
        beta_days: int = 30,
        created_by: Optional[str] = None,
    ) -> str:
        """Admin için: rastgele bir davetiye kodu üret + DB'ye kaydet."""
        code = _generate_invite_code()
        self._client.table("invite_codes").insert({
            "code": code,
            "notes": notes,
            "beta_days": beta_days,
            "created_by": created_by,
        }).execute()
        logger.info("Davetiye oluşturuldu: %s (notes=%r)", code, notes)
        return code

    # ------------------------------------------------------------------
    # Status sorgusu
    # ------------------------------------------------------------------

    def get_user_status(self, chat_id: int) -> Optional[UserStatus]:
        """/durum komutu için tüm bilgileri tek seferde derle."""
        user = self.get_user_by_chat_id(chat_id)
        if not user:
            return None

        # Aktif abonelik
        sub_resp = (
            self._client.table("subscriptions")
            .select("plan, valid_until")
            .eq("user_id", user.id)
            .eq("status", "active")
            .gt("valid_until", "now()")
            .order("valid_until", desc=True)
            .limit(1)
            .execute()
        )
        sub_rows = sub_resp.data or []
        has_sub = bool(sub_rows)
        sub_plan = sub_rows[0]["plan"] if has_sub else None
        sub_valid_until = _parse_dt(sub_rows[0]["valid_until"]) if has_sub else None

        # Aktif lisans
        lic_resp = (
            self._client.table("licenses")
            .select("id, api_key, last_heartbeat, character_name")
            .eq("user_id", user.id)
            .eq("is_active", True)
            .is_("revoked_at", "null")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        lic_rows = lic_resp.data or []
        if lic_rows:
            lic = lic_rows[0]
            license_id = lic["id"]
            api_key = lic["api_key"]
            last_hb = _parse_dt(lic["last_heartbeat"]) if lic.get("last_heartbeat") else None
            character_name = lic.get("character_name")
        else:
            license_id = api_key = last_hb = character_name = None

        return UserStatus(
            user=user,
            has_active_subscription=has_sub,
            subscription_plan=sub_plan,
            valid_until=sub_valid_until,
            api_key=api_key,
            license_id=license_id,
            last_heartbeat=last_hb,
            character_name=character_name,
        )

    # ------------------------------------------------------------------
    # Mesaj akışı
    # ------------------------------------------------------------------

    def get_unnotified_incoming(self, limit: int = 50) -> list[IncomingMessage]:
        """Henüz Telegram'a bildirilmemiş incoming PM'leri çek.

        status='new' AND direction='incoming' AND user'ın telegram_chat_id var.
        Bildirim sonrası status='notified' olur.
        """
        # JOIN için view kullanılabilir; şimdilik nested select.
        resp = (
            self._client.table("messages")
            .select(
                "id, user_id, from_character, to_character, content, created_at, "
                "users!inner(telegram_chat_id)"
            )
            .eq("status", "new")
            .eq("direction", "incoming")
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
        rows = resp.data or []
        result: list[IncomingMessage] = []
        for r in rows:
            user_data = r.get("users") or {}
            chat_id = user_data.get("telegram_chat_id")
            if not chat_id:
                continue  # bağlı Telegram hesabı yok → skip
            result.append(IncomingMessage(
                id=r["id"],
                user_id=r["user_id"],
                telegram_chat_id=chat_id,
                from_character=r["from_character"],
                to_character=r["to_character"],
                content=r["content"],
                created_at=_parse_dt(r["created_at"]),
            ))
        return result

    def mark_message_notified(self, message_id: str, telegram_message_id: int) -> None:
        """Mesajı 'notified' olarak işaretle + Telegram mesaj ID'sini kaydet."""
        self._client.table("messages").update({
            "status": "notified",
            "telegram_message_id": telegram_message_id,
        }).eq("id", message_id).execute()

    def insert_outgoing_reply(
        self,
        user_id: str,
        to_character: str,
        content: str,
    ) -> str:
        """Kullanıcının yazdığı cevabı outgoing olarak kaydet. license_id'yi
        kullanıcının aktif lisansından otomatik bağla.
        """
        # Önce kullanıcının aktif lisansını bul
        lic_resp = (
            self._client.table("licenses")
            .select("id, character_name")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .is_("revoked_at", "null")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        lic_rows = lic_resp.data or []
        if not lic_rows:
            raise RuntimeError("Aktif lisans bulunamadı")
        license_id = lic_rows[0]["id"]
        from_character = lic_rows[0].get("character_name") or "PazarChat"

        resp = self._client.table("messages").insert({
            "user_id": user_id,
            "license_id": license_id,
            "direction": "outgoing",
            "from_character": from_character,
            "to_character": to_character,
            "content": content,
            "status": "new",
        }).execute()
        rows = resp.data or []
        if not rows:
            raise RuntimeError("Outgoing INSERT boş cevap döndü")
        return rows[0]["id"]

    # ------------------------------------------------------------------
    # Hazır cevaplar
    # ------------------------------------------------------------------

    def get_ready_replies(self, user_id: str) -> list[dict]:
        """Kullanıcının hazır cevap listesini sort_order'a göre döndür."""
        resp = (
            self._client.table("ready_replies")
            .select("id, label, content, sort_order")
            .eq("user_id", user_id)
            .order("sort_order", desc=False)
            .execute()
        )
        return resp.data or []


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _row_to_user(row: dict) -> BotUser:
    return BotUser(
        id=row["id"],
        telegram_chat_id=row["telegram_chat_id"],
        telegram_username=row.get("telegram_username"),
        display_name=row.get("display_name"),
        status=row.get("status", "active"),
    )


def _parse_dt(value: str) -> datetime:
    """Postgres timestamptz parse."""
    if value.endswith("+00"):
        value = value + ":00"
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _random_password(length: int = 32) -> str:
    """auth.users için dummy şifre. Bot bu şifreyi hatırlamaz; user Telegram'la auth eder."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _generate_invite_code() -> str:
    """BETA-XXXXXX formatında okunabilir kod. 6 char, kafa karıştırıcı karakterler hariç."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # I, O, 0, 1 çıkarıldı
    suffix = "".join(secrets.choice(alphabet) for _ in range(6))
    return f"BETA-{suffix}"

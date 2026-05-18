"""
PazarChat PC Service — Supabase Client
=======================================
Tüm DB işlemleri RPC fonksiyonları üzerinden yapılır (003_pc_rpc_functions.sql).
PC servisi service_role key kullanmaz — sadece anon key + API key kombinasyonu.

Why RPC: API key SECURITY DEFINER fonksiyonlar içinde doğrulanır. PC saldırıya
uğrasa bile saldırgan sadece o lisansın yapabildiklerini yapabilir.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx


logger = logging.getLogger(__name__)


# Supabase REST API endpoint sabitleri
_RPC_PATH = "/rest/v1/rpc"
_TIMEOUT_SECONDS = 10.0


# -----------------------------------------------------------------------------
# Custom exceptions — hata türlerini uygulamada ayırt etmek için
# -----------------------------------------------------------------------------

class SupabaseError(RuntimeError):
    """Tüm Supabase hatalarının base'i."""


class AuthError(SupabaseError):
    """API key geçersiz, iptal edilmiş veya abonelik süresi dolmuş."""


class FingerprintMismatchError(AuthError):
    """Lisans başka bir bilgisayara bağlı (machine fingerprint uyuşmuyor)."""


# -----------------------------------------------------------------------------
# Data classes — RPC dönüşlerini temizce tutmak için
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class HeartbeatResult:
    license_id: str
    valid_until: datetime  # abonelik bitiş tarihi


@dataclass(frozen=True)
class PendingMessage:
    """Bot'tan gelen, PC'ye iletilmesi bekleyen cevap."""
    id: str
    to_character: str
    content: str
    created_at: datetime


# -----------------------------------------------------------------------------
# Ana client sınıfı
# -----------------------------------------------------------------------------

class SupabaseClient:
    """PazarChat Supabase ile konuşan sync HTTP client.

    Tüm metodlar RPC üzerinden gider (003 migration'daki fonksiyonlar).
    AuthError fırlatabilen her metod tray UI'ında kullanıcıya gösterilmeli.
    """

    def __init__(self, url: str, anon_key: str, api_key: str) -> None:
        """
        Args:
            url: https://xxx.supabase.co
            anon_key: anon public JWT (RLS yetkisi authenticated user gibi)
            api_key: PazarChat lisans key (pzc_...) — RPC içinde doğrulanır
        """
        self._url = url.rstrip("/")
        self._api_key = api_key
        self._http = httpx.Client(
            base_url=self._url,
            timeout=_TIMEOUT_SECONDS,
            headers={
                "apikey": anon_key,
                "Authorization": f"Bearer {anon_key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
        )

    def close(self) -> None:
        """Uygulama kapanırken çağrılmalı."""
        self._http.close()

    # ------------------------------------------------------------------
    # Public RPC wrappers
    # ------------------------------------------------------------------

    def heartbeat(
        self,
        machine_fingerprint: str,
        character_name: str,
        server_name: Optional[str] = None,
    ) -> HeartbeatResult:
        """60 saniyede bir çağrılır. Lisansı doğrular + heartbeat günceller."""
        rows = self._rpc(
            "pc_heartbeat",
            {
                "p_api_key": self._api_key,
                "p_machine_fingerprint": machine_fingerprint,
                "p_character_name": character_name,
                "p_server_name": server_name,
            },
        )
        if not rows:
            raise SupabaseError("Heartbeat boş cevap döndü")
        row = rows[0]
        return HeartbeatResult(
            license_id=row["license_id"],
            valid_until=_parse_dt(row["valid_until"]),
        )

    def insert_incoming_message(
        self,
        from_character: str,
        to_character: str,
        content: str,
        content_hash: str,
    ) -> str:
        """Yeni PM kaydet, mesaj ID döndür. Duplicate ise mevcut ID döner."""
        message_id = self._rpc(
            "pc_insert_incoming_message",
            {
                "p_api_key": self._api_key,
                "p_from_character": from_character,
                "p_to_character": to_character,
                "p_content": content,
                "p_content_hash": content_hash,
            },
        )
        # RPC tek bir UUID döner (not table-returning), Supabase'in JSON çıkışı
        # bu durumda direkt değer (list değil).
        if isinstance(message_id, list) and message_id:
            return message_id[0]
        return str(message_id)

    def get_pending_outgoing(self) -> list[PendingMessage]:
        """PC'ye iletilmesi bekleyen cevapları çek (max 10)."""
        rows = self._rpc(
            "pc_get_pending_outgoing",
            {"p_api_key": self._api_key},
        )
        return [
            PendingMessage(
                id=r["id"],
                to_character=r["to_character"],
                content=r["content"],
                created_at=_parse_dt(r["created_at"]),
            )
            for r in (rows or [])
        ]

    def mark_message_sent(self, message_id: str) -> None:
        """Cevap pano'ya kopyalandı; status='sent_to_pc' olarak işaretle."""
        self._rpc(
            "pc_mark_message_sent",
            {"p_api_key": self._api_key, "p_message_id": message_id},
        )

    # ------------------------------------------------------------------
    # Internal: RPC çağrısı + hata mapping
    # ------------------------------------------------------------------

    def _rpc(self, fn_name: str, params: dict) -> object:
        """Supabase RPC çağrısı yap, hata varsa uygun exception fırlat."""
        url = f"{_RPC_PATH}/{fn_name}"
        try:
            response = self._http.post(url, json=params)
        except httpx.RequestError as e:
            raise SupabaseError(f"Ağ hatası ({fn_name}): {e}") from e

        # 2xx success codes
        if response.status_code in (200, 201):
            try:
                return response.json()
            except ValueError as e:
                raise SupabaseError(f"Geçersiz JSON ({fn_name})") from e

        # 204 No Content: void return RPC fonksiyonları (örn. pc_mark_message_sent)
        # body boş, başarı durumu. None döner.
        if response.status_code == 204:
            return None

        # Hata: Supabase Postgres hatasını JSON olarak döner
        try:
            err = response.json()
        except ValueError:
            err = {"message": response.text}

        message = err.get("message", "Bilinmeyen hata")
        sqlstate = err.get("code", "")

        # SQLSTATE 28000 → invalid_authorization (API key/lisans sorunu)
        if sqlstate == "28000" or "Geçersiz" in message or "Gecersiz" in message:
            if "baska bir bilgisayara" in message or "başka bir bilgisayara" in message:
                raise FingerprintMismatchError(message)
            raise AuthError(message)

        logger.error("RPC hatası %s: status=%d body=%s", fn_name, response.status_code, err)
        raise SupabaseError(f"{fn_name} başarısız: {message}")


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _parse_dt(value: str) -> datetime:
    """Postgres'in ISO timestamptz formatını parse et.

    Örnek: '2026-05-17T20:36:42.123456+00:00'
    Python 3.11+ datetime.fromisoformat artık 'Z' ve offset destekliyor.
    """
    # Postgres bazen +00 (sadece) döndürür → +00:00'a normalize et
    if value.endswith("+00"):
        value = value + ":00"
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

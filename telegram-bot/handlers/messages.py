"""
PazarChat Telegram Bot — PM Bildirim ve Cevap Akışı
=====================================================
İki yön:

1. **Polling task** (background): Supabase'den henüz bildirilmemiş incoming
   PM'leri çek, kullanıcıya inline keyboard'lı kart gönder, mark_notified yap.

2. **Reply handler'lar**:
   a) Hazır cevap callback: kullanıcı butona basar → outgoing INSERT
   b) Native reply: kullanıcı bot kartına Telegram'ın "Yanıtla" özelliği ile
      cevap yazar → reply_to_message_id ile orijinal PM bulunur → outgoing INSERT

Reply akışı için yeni state/FSM gerekmez — telegram_message_id eşleştirmesi
yeterli.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import settings
from services.supabase_service import IncomingMessage, SupabaseService


logger = logging.getLogger(__name__)
router = Router(name="messages")


# Callback data formatları (Telegram 64-byte limiti var; UUID + prefix sığar)
# qr = quick reply (hazır cevap)
_CB_QUICK_PREFIX = "qr"


# -----------------------------------------------------------------------------
# Polling task (background)
# -----------------------------------------------------------------------------

class IncomingMessagePoller:
    """Bot startup'ında başlatılan background task.

    Her N saniyede bir get_unnotified_incoming() çağırır, gelen her PM için
    Telegram'a kart gönderir, mark_notified yapar.
    """

    def __init__(self, bot: Bot, svc: SupabaseService) -> None:
        self._bot = bot
        self._svc = svc
        self._interval = settings.incoming_poll_interval
        self._stop_event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._loop(), name="IncomingPoller")
        logger.info("Incoming PM polling başladı (interval=%ds)", self._interval)

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5)
            except asyncio.TimeoutError:
                self._task.cancel()

    async def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                # Service sync; thread'e taşı blocking olmasın
                pending = await asyncio.to_thread(self._svc.get_unnotified_incoming)
                if pending:
                    logger.debug("Polling'de %d yeni PM bulundu", len(pending))
                    # Her kullanıcının ready_replies'ini bir kez çek (cache)
                    user_replies_cache: dict[str, list[dict]] = {}
                    for pm in pending:
                        if pm.user_id not in user_replies_cache:
                            user_replies_cache[pm.user_id] = await asyncio.to_thread(
                                self._svc.get_ready_replies, pm.user_id
                            )
                        await self._notify_pm(pm, user_replies_cache[pm.user_id])
            except Exception:
                logger.exception("Incoming polling iterasyon hatası")

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._interval)
            except asyncio.TimeoutError:
                pass  # normal — bir sonraki iterasyon

    async def _notify_pm(self, pm: IncomingMessage, ready_replies: list[dict]) -> None:
        """Tek bir PM için Telegram'a kart gönder + DB'de mark_notified."""
        try:
            text = _build_pm_card_text(pm)
            keyboard = _build_quick_reply_keyboard(pm.id, ready_replies)
            sent = await self._bot.send_message(
                chat_id=pm.telegram_chat_id,
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN,
            )
            # mark_notified — bot tarafı sync
            await asyncio.to_thread(
                self._svc.mark_message_notified, pm.id, sent.message_id
            )
        except Exception:
            logger.exception("PM bildirilemedi msg_id=%s chat_id=%d",
                             pm.id, pm.telegram_chat_id)


# -----------------------------------------------------------------------------
# UI helpers — kart metni + keyboard
# -----------------------------------------------------------------------------

def _build_pm_card_text(pm: IncomingMessage) -> str:
    """Kullanıcıya gösterilecek mesaj kartı."""
    # Markdown special chars kaçışı
    from_char_safe = _escape_md(pm.from_character)
    content_short = _truncate(pm.content, settings.pm_preview_max_chars)
    content_safe = _escape_md(content_short)
    time_str = pm.created_at.astimezone().strftime("%H:%M")

    return (
        f"📩 *{from_char_safe}* yazdı:\n"
        f"_{content_safe}_\n\n"
        f"🕐 {time_str}\n"
        f"💬 Cevap için butona dokun **ya da** bu mesaja Telegram'ın "
        f"'Yanıtla' özelliği ile yazabilirsin."
    )


def _build_quick_reply_keyboard(
    message_id: str,
    ready_replies: list[dict],
) -> InlineKeyboardMarkup:
    """Hazır cevap butonları — 2'li satırlar halinde."""
    rows: list[list[InlineKeyboardButton]] = []
    current_row: list[InlineKeyboardButton] = []

    for reply in ready_replies[:8]:  # max 8 buton (4 satır)
        # Callback data: qr:{message_id}:{reply_id}
        # UUID 36 + prefix 3 + 2 colon = 77 — Telegram limiti 64.
        # Çözüm: UUID'lerden ilk 8 char kullan (collision riski düşük)
        msg_short = message_id.replace("-", "")[:12]
        reply_short = reply["id"].replace("-", "")[:12]
        callback_data = f"{_CB_QUICK_PREFIX}:{msg_short}:{reply_short}"

        btn = InlineKeyboardButton(text=reply["label"], callback_data=callback_data)
        current_row.append(btn)
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []

    if current_row:
        rows.append(current_row)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def _escape_md(text: str) -> str:
    """Telegram Markdown V1 için kaçış. _, *, [, ], `."""
    return (
        text.replace("\\", "\\\\")
        .replace("_", "\\_")
        .replace("*", "\\*")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("`", "\\`")
    )


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


# -----------------------------------------------------------------------------
# Reply handler'lar
# -----------------------------------------------------------------------------

def setup(svc: SupabaseService) -> Router:

    @router.callback_query(F.data.startswith(f"{_CB_QUICK_PREFIX}:"))
    async def cb_quick_reply(callback: CallbackQuery) -> None:
        """Hazır cevap butonuna tıklandığında."""
        if not callback.data or not callback.from_user or not callback.message:
            await callback.answer("Geçersiz istek", show_alert=True)
            return

        # Parse: qr:msg_short:reply_short
        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer("Geçersiz istek", show_alert=True)
            return

        msg_short = parts[1]
        reply_short = parts[2]

        chat_id = callback.from_user.id
        user = await asyncio.to_thread(svc.get_user_by_chat_id, chat_id)
        if not user:
            await callback.answer("Kullanıcı bulunamadı. /start", show_alert=True)
            return

        # message_id ve reply_id'yi tam UUID'e expand etmek için DB sorgusu lazım
        # — short UUID'leri kullanarak ara
        original_msg = await asyncio.to_thread(
            _find_message_by_short_id, svc, user.id, msg_short
        )
        if not original_msg:
            await callback.answer("Orijinal mesaj bulunamadı (silinmiş olabilir)", show_alert=True)
            return

        ready_reply = await asyncio.to_thread(
            _find_ready_reply_by_short_id, svc, user.id, reply_short
        )
        if not ready_reply:
            await callback.answer("Cevap bulunamadı", show_alert=True)
            return

        # Outgoing INSERT
        try:
            await asyncio.to_thread(
                svc.insert_outgoing_reply,
                user.id,
                original_msg["from_character"],  # PM gönderene cevap
                ready_reply["content"],
            )
        except Exception:
            logger.exception("insert_outgoing_reply başarısız")
            await callback.answer("❌ Cevap kaydedilemedi", show_alert=True)
            return

        # UX: kullanıcıya feedback ver, mesajdaki butonları kaldır
        await callback.answer("✅ Cevap PC'ye gönderildi", show_alert=False)

        try:
            await callback.message.edit_reply_markup(reply_markup=None)
            # Mesaj metnine "cevaplandı" notu ekle
            new_text = (callback.message.text or callback.message.md_text or "")
            new_text += f"\n\n✅ _Cevap: {_escape_md(ready_reply['content'])}_"
            await callback.message.edit_text(new_text, parse_mode=ParseMode.MARKDOWN)
        except TelegramBadRequest:
            pass  # mesaj eski olabilir, edit fail — sorun değil

    @router.message(F.reply_to_message)
    async def handle_native_reply(message: Message) -> None:
        """Kullanıcı bot mesajına 'Yanıtla' ile cevap yazdığında."""
        if not message.from_user:
            logger.debug("Native reply skip: from_user yok")
            return
        if not message.reply_to_message:
            logger.debug("Native reply skip: reply_to_message yok")
            return
        if not message.text:
            logger.debug("Native reply skip: text yok (sticker/photo olabilir)")
            return

        chat_id = message.from_user.id
        replied_msg_id = message.reply_to_message.message_id
        logger.info(
            "Native reply ALINDI: chat_id=%d, reply_to_msg_id=%d, text=%r",
            chat_id, replied_msg_id, message.text[:60],
        )

        # Bu Telegram mesajı bizim attığımız bir PM kartı mı?
        original = await asyncio.to_thread(
            _find_message_by_telegram_id, svc, chat_id, replied_msg_id
        )
        if not original:
            logger.warning(
                "Native reply ATLANDI: orijinal PM bulunamadı "
                "(telegram_message_id=%d, chat_id=%d). Bot bu mesajı atmamış olabilir.",
                replied_msg_id, chat_id,
            )
            await message.answer(
                "ℹ️ Bu mesaja yanıt veriyorsun ama PazarChat sisteminde "
                "kayıtlı bir PM bulamadım. Reply hedefini kontrol et."
            )
            return

        logger.info("Native reply için orijinal PM bulundu: from_character=%s",
                    original["from_character"])

        user = await asyncio.to_thread(svc.get_user_by_chat_id, chat_id)
        if not user:
            await message.answer("Önce /start ile kayıt ol.")
            return

        # Outgoing INSERT
        try:
            outgoing_id = await asyncio.to_thread(
                svc.insert_outgoing_reply,
                user.id,
                original["from_character"],
                message.text,
            )
            logger.info("Outgoing INSERT OK: id=%s", outgoing_id)
        except Exception:
            logger.exception("insert_outgoing_reply başarısız (native reply)")
            await message.answer("❌ Cevap kaydedilemedi, tekrar dene.")
            return

        await message.answer(
            f"✅ Cevap PC'ye gönderildi → *{_escape_md(original['from_character'])}*",
            parse_mode=ParseMode.MARKDOWN,
        )

    return router


# -----------------------------------------------------------------------------
# DB lookup helpers — short UUID'i tam UUID'e map et
# -----------------------------------------------------------------------------
# Why short UUIDs: Telegram callback_data 64 byte limit. Tam UUID 36 char +
# prefix sığmıyor güvenli. Short ilk 12 hex karakter — collision riski user
# bazında ~10^-7 (kabul edilebilir, kullanıcı başına az mesaj).

def _find_message_by_short_id(svc: SupabaseService, user_id: str, short_id: str) -> Optional[dict]:
    """Short ID'den messages tablosunda full mesajı bul."""
    # Postgres'te id::text LIKE 'xxx%' ile prefix arama. Süslü, ama
    # alternative tam UUID'i callback'te taşımak (yer yok).
    # _client direkt erişim yerine raw SQL ile daha pratik olur ama PostgREST
    # like filter destekler.
    full_id = _short_to_full_uuid(short_id)
    resp = (
        svc._client.table("messages")  # type: ignore[attr-defined]
        .select("id, from_character, to_character, direction")
        .eq("user_id", user_id)
        .like("id", f"{full_id[:8]}-{full_id[8:12]}%")
        .eq("direction", "incoming")
        .limit(1)
        .execute()
    )
    rows = resp.data or []
    return rows[0] if rows else None


def _find_ready_reply_by_short_id(svc: SupabaseService, user_id: str, short_id: str) -> Optional[dict]:
    full_id = _short_to_full_uuid(short_id)
    resp = (
        svc._client.table("ready_replies")  # type: ignore[attr-defined]
        .select("id, label, content")
        .eq("user_id", user_id)
        .like("id", f"{full_id[:8]}-{full_id[8:12]}%")
        .limit(1)
        .execute()
    )
    rows = resp.data or []
    return rows[0] if rows else None


def _find_message_by_telegram_id(
    svc: SupabaseService,
    chat_id: int,
    telegram_message_id: int,
) -> Optional[dict]:
    """Native reply için: bot'un attığı Telegram mesajından orijinal PM bul.

    İki ayrı sorgu yapıyoruz (PostgREST inner-join yerine) — schema cache
    sorunlarına karşı dayanıklı, ve hata olursa hangi adımda olduğunu loglar.
    """
    # 1) telegram_message_id ile incoming PM'i bul
    try:
        resp = (
            svc._client.table("messages")  # type: ignore[attr-defined]
            .select("id, user_id, from_character, to_character, direction")
            .eq("telegram_message_id", telegram_message_id)
            .eq("direction", "incoming")
            .limit(1)
            .execute()
        )
    except Exception:
        logger.exception(
            "_find_message_by_telegram_id: messages sorgu hatası "
            "(telegram_message_id=%d)", telegram_message_id,
        )
        return None

    rows = resp.data or []
    if not rows:
        logger.debug(
            "telegram_message_id=%d için incoming PM bulunamadı",
            telegram_message_id,
        )
        return None

    msg = rows[0]

    # 2) user'ın chat_id'sini doğrula (başkasının mesajına müdahale önlemi)
    try:
        user_resp = (
            svc._client.table("users")  # type: ignore[attr-defined]
            .select("telegram_chat_id")
            .eq("id", msg["user_id"])
            .limit(1)
            .execute()
        )
    except Exception:
        logger.exception(
            "_find_message_by_telegram_id: users sorgu hatası (user_id=%s)",
            msg.get("user_id"),
        )
        return None

    user_rows = user_resp.data or []
    if not user_rows:
        logger.warning("user_id=%s için users kaydı yok", msg.get("user_id"))
        return None

    actual_chat_id = user_rows[0].get("telegram_chat_id")
    if actual_chat_id != chat_id:
        logger.warning(
            "Chat_id uyumsuz: expected=%d, actual=%s — reply ignore",
            chat_id, actual_chat_id,
        )
        return None

    return msg


def _short_to_full_uuid(short: str) -> str:
    """12 hex char → "xxxxxxxx-xxxx" formatına döndür (PostgreSQL LIKE için)."""
    # 12 char = ilk 8 + 4. Tam UUID: 8-4-4-4-12.
    # short_to_full mantığı: short ilk 12 char'ı ile prefix arama yap.
    if len(short) >= 8:
        return f"{short[:8]}-{short[8:12]}-0000-0000-000000000000"
    return short

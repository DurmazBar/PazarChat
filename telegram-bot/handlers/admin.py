"""
PazarChat Telegram Bot — Admin Handler'ları
============================================
Sadece ADMIN_TELEGRAM_CHAT_IDS .env değişkenindeki chat_id'ler erişebilir.

Komutlar:
  /davetiye_olustur [açıklama] — Yeni BETA-XXXXXX kodu üret
  /davetiye_listele — Kullanılmamış davetiyeleri listele (faz 2)
"""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from config import settings
from services.supabase_service import SupabaseService


logger = logging.getLogger(__name__)
router = Router(name="admin")


def setup(svc: SupabaseService) -> Router:

    @router.message(Command("davetiye_olustur"))
    async def cmd_create_invite(message: Message, command: CommandObject) -> None:
        if not message.from_user:
            return

        # Yetki kontrolü
        if not settings.is_admin(message.chat.id):
            logger.warning(
                "Yetkisiz davetiye_olustur denemesi chat_id=%d username=%r",
                message.chat.id, message.from_user.username,
            )
            return  # sessiz reddet — admin olmayan command'ı bilmesin

        notes = (command.args or "").strip() or "(admin tarafından üretildi)"

        try:
            code = svc.create_invite_code(notes=notes, beta_days=30)
        except Exception:
            logger.exception("Davetiye oluşturulamadı")
            await message.answer("❌ Davetiye oluşturulamadı (loglara bak).")
            return

        await message.answer(
            f"✅ Yeni davetiye:\n\n"
            f"`{code}`\n\n"
            f"📝 Not: {notes}\n"
            f"📅 30 gün beta",
            parse_mode=ParseMode.MARKDOWN,
        )

    return router

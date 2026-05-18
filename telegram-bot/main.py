"""
PazarChat Telegram Bot — Entrypoint
====================================
Bot başlatma sırası:
  1. Logging kur
  2. Bot + Dispatcher (aiogram)
  3. SupabaseService
  4. Router'ları include et: start, commands, admin, messages
  5. IncomingMessagePoller background task'ı başlat
  6. dp.start_polling() — Telegram'dan update'leri çek, handler'lara dağıt

Deploy: Hetzner/DigitalOcean VPS, systemd ile çalıştırılır. Auto-restart, log
rotation systemd üzerinden.
"""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings, setup_logging
from handlers import admin as admin_handlers
from handlers import commands as command_handlers
from handlers import messages as message_handlers
from handlers import start as start_handlers
from handlers.messages import IncomingMessagePoller
from services.supabase_service import SupabaseService


logger = logging.getLogger("pazarchat.bot")


async def main() -> None:
    setup_logging(settings.log_level, settings.log_file)
    logger.info("PazarChat bot başlatılıyor (bot=@%s)", settings.telegram_bot_username)

    # 1) Service
    svc = SupabaseService()

    # 2) Bot + Dispatcher
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=None),  # default yok; handler'lar açıkça belirtir
    )
    dp = Dispatcher(storage=MemoryStorage())

    # 3) Router'ları include et — sırası önemli, daha spesifik handler'lar önce
    dp.include_router(admin_handlers.setup(svc))       # /davetiye_olustur (admin only)
    dp.include_router(start_handlers.setup(svc))       # /start, /davetiye
    dp.include_router(command_handlers.setup(svc))     # /durum, /yardim
    dp.include_router(message_handlers.setup(svc))     # callback queries + native reply

    # 4) Bot info logla
    me = await bot.get_me()
    logger.info("Bot bağlı: @%s (id=%d)", me.username, me.id)
    if settings.admin_chat_ids:
        logger.info("Admin chat_id'ler: %s", list(settings.admin_chat_ids))
    else:
        logger.warning(
            "ADMIN_TELEGRAM_CHAT_IDS boş — /davetiye_olustur kullanılamaz. "
            ".env'i güncelle."
        )

    # 5) Incoming PM polling task
    poller = IncomingMessagePoller(bot=bot, svc=svc)
    poller.start()

    try:
        # 6) Telegram update'lerini dinle (blocking; ctrl-c ile çıkış)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        logger.info("Bot kapatılıyor...")
        await poller.stop()
        await bot.session.close()
        logger.info("Bot kapatıldı.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot SIGINT ile durduruldu.")

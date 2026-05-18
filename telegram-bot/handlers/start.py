"""
PazarChat Telegram Bot — /start ve /davetiye Handler'ları
==========================================================
İlk temas akışı:
  1. Kullanıcı /start yazar → tanıtım + nasıl davetiye al
  2. Kullanıcı /davetiye BETA-XXXXXX yazar → user + subscription + license oluşur
  3. Bot kullanıcıya API key'i gönderir
  4. Kullanıcı API key'i PC servisinin .env dosyasına yapıştırır
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message

from services.supabase_service import SupabaseService


logger = logging.getLogger(__name__)
router = Router(name="start")


_WELCOME_TEXT = (
    "👋 *PazarChat'e hoş geldin!*\n\n"
    "Knight Online'da pazar kurarken bilgisayar başından ayrıldığında "
    "gelen PM'leri buradan görüp cevap yazabileceğin bir bildirim aracıyım.\n\n"
    "🎟 *Beta dönemindeyiz* — sisteme erişmek için davetiye kodun olması gerek.\n\n"
    "Davetiye kodun varsa şunu yaz:\n"
    "`/davetiye BETA-XXXXXX`\n\n"
    "Davetiye kodun yoksa, beta erişimi için iletişime geç."
)


_ALREADY_REGISTERED_TEXT = (
    "✅ Sen zaten kayıtlısın.\n\n"
    "Aktif lisansını görmek için: /durum\n"
    "Hazır cevaplarını yönetmek için: /cevaplar"
)


_USAGE_DAVETIYE = (
    "❓ Kullanım: `/davetiye BETA-XXXXXX`\n\n"
    "Davetiye kodunu kendine verilen şekilde yapıştır."
)


def setup(svc: SupabaseService) -> Router:
    """Service'i closure'a alıp router'ı döndür. main.py bunu include_router'lar."""

    @router.message(CommandStart())
    async def cmd_start(message: Message) -> None:
        if not message.from_user:
            return
        chat_id = message.chat.id
        existing = svc.get_user_by_chat_id(chat_id)
        if existing:
            await message.answer(_ALREADY_REGISTERED_TEXT)
            return

        # Kullanıcı henüz kayıtlı değil — tanıtım mesajı gönder
        await message.answer(_WELCOME_TEXT, parse_mode=ParseMode.MARKDOWN)

    @router.message(Command("davetiye"))
    async def cmd_davetiye(message: Message, command: CommandObject) -> None:
        if not message.from_user:
            return

        # Argüman kontrolü
        if not command.args:
            await message.answer(_USAGE_DAVETIYE, parse_mode=ParseMode.MARKDOWN)
            return

        code = command.args.strip().upper()
        if not code.startswith("BETA-") or len(code) < 8:
            await message.answer(
                "⚠ Davetiye kodu formatı geçersiz görünüyor.\n"
                "Beklenen format: `BETA-XXXXXX`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        user_id = message.from_user.id
        chat_id = message.chat.id
        username = message.from_user.username
        display_name = (
            message.from_user.full_name
            or message.from_user.username
            or f"user_{user_id}"
        )

        # 1) Kullanıcı zaten redeem etmiş mi? (idempotent davranış)
        existing = svc.get_user_by_chat_id(chat_id)

        try:
            if existing:
                # Mevcut kullanıcı tekrar davetiye girmek istiyor olabilir
                # — yine de redeem'e izin ver (yeni lisans yarat)
                bot_user = existing
            else:
                # 2) Auth + public.users kaydı oluştur
                logger.info("Yeni kullanıcı kaydediliyor chat_id=%d username=%r",
                            chat_id, username)
                bot_user = svc.ensure_user_exists(
                    chat_id=chat_id,
                    username=username,
                    display_name=display_name,
                )
        except Exception as e:
            logger.exception("ensure_user_exists başarısız")
            await message.answer(
                "❌ Kayıt sırasında bir hata oldu. Lütfen tekrar dene veya "
                "destek için bildirim ver."
            )
            return

        # 3) Davetiyeyi kullan (atomic RPC)
        try:
            result = svc.redeem_invite(bot_user.id, code)
        except Exception as e:
            # Postgres exception mesajı user-friendly olmayabilir; pattern match et
            err_msg = str(e)
            if "gecersiz" in err_msg.lower() or "geçersiz" in err_msg.lower() or "kullanilmis" in err_msg.lower():
                await message.answer(
                    "❌ Bu davetiye kodu geçersiz, süresi dolmuş veya zaten kullanılmış.\n\n"
                    "Eğer yanlış kopyaladıysan tekrar dene. Sorun devam ediyorsa "
                    "destek ile iletişime geç."
                )
            else:
                logger.exception("redeem_invite başarısız")
                await message.answer(
                    "❌ Bir hata oldu, lütfen birazdan tekrar dene."
                )
            return

        # 4) Başarılı — API key'i kullanıcıya gönder
        valid_str = result.valid_until.strftime("%d %B %Y")
        success_text = (
            "🎉 *Davetiye başarılı, hoş geldin!*\n\n"
            f"📅 *Beta süresi:* {valid_str} tarihine kadar\n\n"
            "🔑 *Lisans Anahtarın:*\n"
            f"`{result.api_key}`\n"
            "⚠ Bu anahtarı *kimseyle paylaşma* — bilgisayarına bağlanan tek kimlik.\n\n"
            "*Sırada ne var?*\n"
            "1. PC servisini indir\n"
            "2. Kurulumu çalıştır\n"
            "3. Lisans anahtarını gir\n"
            "4. Knight Online'ı windowed mode'da aç\n"
            "5. Pazar kur, hayatına devam et 🛒\n\n"
            "_Lisansını ve durumunu görmek için her zaman /durum yazabilirsin._"
        )
        await message.answer(success_text, parse_mode=ParseMode.MARKDOWN)

    return router

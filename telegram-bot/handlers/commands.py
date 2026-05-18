"""
PazarChat Telegram Bot — Genel Komut Handler'ları
==================================================
/durum, /yardim, /cevaplar (faz 2)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from services.supabase_service import SupabaseService


logger = logging.getLogger(__name__)
router = Router(name="commands")


_HELP_TEXT = (
    "📚 *PazarChat Komutları*\n\n"
    "*/start* — Tanıtım mesajı\n"
    "*/davetiye* `BETA-XXXX` — Beta davetiyesi kullan\n"
    "*/durum* — Lisans, abonelik ve PC bağlantı durumu\n"
    "*/yardim* — Bu mesaj\n\n"
    "_Hazır cevap yönetimi (/cevaplar) yakında._"
)


def setup(svc: SupabaseService) -> Router:

    @router.message(Command("durum"))
    async def cmd_durum(message: Message) -> None:
        if not message.from_user:
            return

        try:
            status = svc.get_user_status(message.chat.id)
        except Exception:
            logger.exception("get_user_status başarısız")
            await message.answer("❌ Durum sorgulanamadı. Lütfen tekrar dene.")
            return

        if not status:
            await message.answer(
                "Henüz kayıtlı değilsin.\n"
                "Önce /start yaz, ardından /davetiye BETA-XXXX ile beta'ya katıl."
            )
            return

        # Durum mesajını derle
        lines: list[str] = ["📊 *Durum Özeti*", ""]

        # Hesap
        username = (
            f"@{status.user.telegram_username}"
            if status.user.telegram_username else "—"
        )
        lines.append(f"👤 Hesap: {username}")
        lines.append(f"🔖 Statü: `{status.user.status}`")
        lines.append("")

        # Abonelik
        if status.has_active_subscription and status.valid_until:
            days_left = (status.valid_until - datetime.now(timezone.utc)).days
            lines.append(
                f"✅ Abonelik: *{status.subscription_plan}* "
                f"({days_left} gün kaldı)"
            )
            lines.append(
                f"   Bitiş: {status.valid_until.strftime('%d %B %Y')}"
            )
        else:
            lines.append("❌ Aktif abonelik yok")
            lines.append("   /davetiye BETA-XXXX ile beta'ya katıl")
        lines.append("")

        # Lisans
        if status.api_key:
            # API key'in son 8 karakteri görünsün, başı maskelensin
            masked = f"`pzc_…{status.api_key[-8:]}`"
            lines.append(f"🔑 Lisans: {masked}")
            if status.character_name:
                lines.append(f"   Karakter: {status.character_name}")

            # PC bağlantı durumu — son 90 saniye içinde heartbeat var mı?
            if status.last_heartbeat:
                age = (datetime.now(timezone.utc) - status.last_heartbeat).total_seconds()
                if age < 90:
                    lines.append(f"   🟢 PC bağlı (son aktivite {int(age)} sn önce)")
                else:
                    minutes = int(age // 60)
                    lines.append(f"   🔴 PC çevrimdışı (son aktivite {minutes} dk önce)")
            else:
                lines.append("   ⏳ PC servisi henüz başlatılmadı")
        else:
            lines.append("⚠ Lisans bulunamadı")
        lines.append("")

        # Tam API key'i ayrı mesajda göster (kopyalanabilir olsun)
        await message.answer("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

        if status.api_key:
            await message.answer(
                "🔑 *Lisans anahtarın (PC servisine yapıştır):*\n"
                f"`{status.api_key}`",
                parse_mode=ParseMode.MARKDOWN,
            )

    @router.message(Command("yardim"))
    async def cmd_yardim(message: Message) -> None:
        await message.answer(_HELP_TEXT, parse_mode=ParseMode.MARKDOWN)

    @router.message(Command("help"))
    async def cmd_help(message: Message) -> None:
        await message.answer(_HELP_TEXT, parse_mode=ParseMode.MARKDOWN)

    return router

"""
PazarChat Telegram Bot — Configuration
=======================================
.env dosyasından ayarları okur, validate eder, immutable Settings döndürür.
PC servisi'ndeki config.py ile aynı pattern.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_PATH)


class ConfigError(RuntimeError):
    """Eksik veya geçersiz env değişkeni."""


def _required(name: str) -> str:
    val = os.getenv(name, "").strip()
    if not val:
        raise ConfigError(
            f"Eksik environment değişkeni: {name}\n"
            f"  .env dosyasını kontrol et: {_ENV_PATH}\n"
            f"  Template: telegram-bot/.env.example"
        )
    return val


def _optional(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _int(name: str, default: int) -> int:
    val = os.getenv(name, "").strip()
    if not val:
        return default
    try:
        return int(val)
    except ValueError as e:
        raise ConfigError(f"{name} bir tam sayı olmalı, '{val}' geçersiz.") from e


def _chat_id_list(name: str) -> list[int]:
    """Virgülle ayrılmış chat_id listesi: '12345,67890' → [12345, 67890]."""
    raw = os.getenv(name, "").strip()
    if not raw:
        return []
    result: list[int] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            result.append(int(token))
        except ValueError as e:
            raise ConfigError(f"{name} içinde geçersiz chat_id: {token!r}") from e
    return result


@dataclass(frozen=True)
class Settings:
    """Bot runtime ayarları."""

    # Telegram
    telegram_bot_token: str
    telegram_bot_username: str

    # Supabase
    supabase_url: str
    supabase_service_role_key: str

    # Admin
    admin_chat_ids: tuple[int, ...] = field(default_factory=tuple)

    # Davranış
    incoming_poll_interval: int = 2
    pm_preview_max_chars: int = 200
    internal_email_domain: str = "tg.pazarchat.internal"

    # Loglama
    log_level: str = "INFO"
    log_file: str = ""

    def is_admin(self, chat_id: int) -> bool:
        return chat_id in self.admin_chat_ids

    def internal_email_for(self, chat_id: int) -> str:
        """Bot'un Supabase Auth'ta yaratacağı kullanıcı için dummy email."""
        return f"tg{chat_id}@{self.internal_email_domain}"


def load_settings() -> Settings:
    return Settings(
        telegram_bot_token=_required("TELEGRAM_BOT_TOKEN"),
        telegram_bot_username=_optional("TELEGRAM_BOT_USERNAME", "KO_PazarChat"),
        supabase_url=_required("SUPABASE_URL"),
        supabase_service_role_key=_required("SUPABASE_SERVICE_ROLE_KEY"),
        admin_chat_ids=tuple(_chat_id_list("ADMIN_TELEGRAM_CHAT_IDS")),
        incoming_poll_interval=_int("INCOMING_POLL_INTERVAL", 2),
        pm_preview_max_chars=_int("PM_PREVIEW_MAX_CHARS", 200),
        internal_email_domain=_optional("INTERNAL_EMAIL_DOMAIN", "tg.pazarchat.internal"),
        log_level=_optional("LOG_LEVEL", "INFO").upper(),
        log_file=_optional("LOG_FILE", ""),
    )


def setup_logging(level_name: str, log_file: str = "") -> None:
    level = getattr(logging, level_name, logging.INFO)
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(path, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )
    # aiogram'ın çok detaylı debug log'ları INFO seviyesinde sussun
    logging.getLogger("aiogram").setLevel(max(level, logging.INFO))
    logging.getLogger("httpx").setLevel(logging.WARNING)


try:
    settings = load_settings()
except ConfigError as e:
    sys.stderr.write(f"\n[CONFIG HATASI]\n{e}\n\n")
    raise

"""
PazarChat PC Service — Configuration
=====================================
.env dosyasından ayarları okur, validate eder, immutable bir Settings nesnesi
döndürür. Uygulama içinde `from config import settings` ile kullanılır.

Why immutable: runtime'da config değişmemeli. Yanlış config tüm pipeline'ı
bozar; erken kontrol et, sonra dokunma.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


# .env dosyasını bu dosyanın bulunduğu klasörden yükle
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_PATH)


class ConfigError(RuntimeError):
    """Eksik veya geçersiz config değeri için kullanılır."""


def _required(name: str) -> str:
    """Zorunlu env değişkenini oku, yoksa erken hata ver."""
    val = os.getenv(name, "").strip()
    if not val:
        raise ConfigError(
            f"Eksik environment değişkeni: {name}\n"
            f"  .env dosyasını kontrol et: {_ENV_PATH}\n"
            f"  Template: pc-service/.env.example"
        )
    return val


def _optional(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name, "").strip().lower()
    if not val:
        return default
    return val in ("1", "true", "yes", "on")


def _int(name: str, default: int) -> int:
    val = os.getenv(name, "").strip()
    if not val:
        return default
    try:
        return int(val)
    except ValueError as e:
        raise ConfigError(f"{name} bir tam sayı olmalı, '{val}' geçersiz.") from e


def _float(name: str, default: float) -> float:
    val = os.getenv(name, "").strip()
    if not val:
        return default
    try:
        return float(val)
    except ValueError as e:
        raise ConfigError(f"{name} bir ondalıklı sayı olmalı, '{val}' geçersiz.") from e


def _crop_region(name: str) -> Optional[tuple[int, int, int, int]]:
    """OCR_CROP_REGION formatı: 'x,y,w,h'. Boşsa None döner (otomatik tespit)."""
    val = os.getenv(name, "").strip()
    if not val:
        return None
    try:
        parts = [int(p.strip()) for p in val.split(",")]
        if len(parts) != 4 or any(p < 0 for p in parts):
            raise ValueError
        return tuple(parts)  # type: ignore[return-value]
    except ValueError as e:
        raise ConfigError(
            f"{name} formatı 'x,y,width,height' olmalı (örn: '10,650,800,180'), "
            f"'{val}' geçersiz."
        ) from e


@dataclass(frozen=True)
class Settings:
    """Tüm runtime ayarları. Frozen — immutable."""

    # Supabase
    supabase_url: str
    supabase_anon_key: str

    # Lisans
    pazarchat_api_key: str

    # Knight Online
    ko_window_title: str
    ko_character_name: str
    ko_server_name: str

    # OCR
    ocr_interval_seconds: float
    ocr_use_gpu: bool
    ocr_crop_region: Optional[tuple[int, int, int, int]]

    # Davranış
    heartbeat_interval_seconds: int
    duplicate_window_size: int

    # Cevap gönderim modu: 'manual' | 'hybrid' | 'auto'
    paste_mode: str
    hotkey_paste_key: str            # hybrid/auto modlarında kullanılan tuş
    auto_paste_delay_ms: int         # auto modunda foreground geçişi sonrası bekleme

    # Loglama
    log_level: str
    log_file: str

    @property
    def hotkey_enabled(self) -> bool:
        """Hotkey hybrid + auto modlarında aktif."""
        return self.paste_mode in ("hybrid", "auto")

    @property
    def autopaste_enabled(self) -> bool:
        """Auto modda outgoing geldiği anda KO'ya otomatik paste."""
        return self.paste_mode == "auto"


def load_settings() -> Settings:
    """Tüm env değerlerini oku ve validate et. Hata varsa erken fail."""
    return Settings(
        # Supabase
        supabase_url=_required("SUPABASE_URL"),
        supabase_anon_key=_required("SUPABASE_ANON_KEY"),

        # Lisans
        pazarchat_api_key=_required("PAZARCHAT_API_KEY"),

        # Knight Online
        ko_window_title=_required("KO_WINDOW_TITLE"),
        ko_character_name=_required("KO_CHARACTER_NAME"),
        ko_server_name=_optional("KO_SERVER_NAME", "Unknown"),

        # OCR
        ocr_interval_seconds=_float("OCR_INTERVAL_SECONDS", 1.5),
        ocr_use_gpu=_bool("OCR_USE_GPU", False),
        ocr_crop_region=_crop_region("OCR_CROP_REGION"),

        # Davranış
        heartbeat_interval_seconds=_int("HEARTBEAT_INTERVAL_SECONDS", 60),
        duplicate_window_size=_int("DUPLICATE_WINDOW_SIZE", 50),

        # Paste modu — validate
        paste_mode=_paste_mode("PASTE_MODE"),
        hotkey_paste_key=_optional("HOTKEY_PASTE_KEY", "f8"),
        auto_paste_delay_ms=_int("AUTO_PASTE_DELAY_MS", 200),

        # Loglama
        log_level=_optional("LOG_LEVEL", "INFO").upper(),
        log_file=_optional("LOG_FILE", ""),
    )


_VALID_PASTE_MODES = ("manual", "hybrid", "auto")


def _paste_mode(name: str) -> str:
    """PASTE_MODE değerini validate et."""
    val = os.getenv(name, "hybrid").strip().lower()
    if val not in _VALID_PASTE_MODES:
        raise ConfigError(
            f"{name} geçersiz değer: {val!r}. Geçerli: {_VALID_PASTE_MODES}"
        )
    return val


def setup_logging(level_name: str, log_file: str = "") -> None:
    """Standart logging konfigürasyonu. main.py başlangıcında bir kez çağrılır."""
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


# Modül yüklenirken otomatik load et — settings'i her yerden kullanabilelim.
# Hata varsa erken patla; runtime'da fark etmek kötü.
try:
    settings = load_settings()
except ConfigError as e:
    # Logger henüz kurulmadığı için stderr'e direkt yaz
    sys.stderr.write(f"\n[CONFIG HATASI]\n{e}\n\n")
    raise

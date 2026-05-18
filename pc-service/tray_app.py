"""
PazarChat PC Service — System Tray UI
======================================
pystray ile tray icon + menu. Kullanıcı sağ tıklayınca:
  • Durum: Bağlı / Hata / Lisans dolacak
  • Karakter: KaraNinja (Cypher)
  • Lisans bitiş: 17 Haziran
  • Son cevap: "100m son fiyat" → KaraNinja (14:23)
  • Çıkış

Menu içeriği dinamik — modül dışından `update_status()` ile güncellenir.
Tray pystray.Icon.run() çağrısı **blocking**'tir; main.py'nin main thread'inde
çalışır, OCR/heartbeat ayrı thread'lerde.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Callable, Optional

import pystray
from PIL import Image, ImageDraw


logger = logging.getLogger(__name__)


# Tray menu için status enum benzeri
@dataclass(frozen=True)
class TrayStatus:
    """Tray'de gösterilecek anlık durum bilgisi."""
    is_online: bool                    # heartbeat OK mi?
    character_name: str                # KO karakter adı
    server_name: str
    license_valid_until: Optional[datetime]  # None → henüz heartbeat gelmedi
    last_reply: Optional[str]          # Son panoya yazılan cevap
    last_reply_to: Optional[str]       # Hangi karaktere
    last_reply_at: Optional[datetime]
    error_message: Optional[str]       # Bir hata varsa kullanıcıya gösterilir


def _default_status() -> TrayStatus:
    return TrayStatus(
        is_online=False,
        character_name="—",
        server_name="—",
        license_valid_until=None,
        last_reply=None,
        last_reply_to=None,
        last_reply_at=None,
        error_message=None,
    )


class TrayApp:
    """Tray icon + dinamik menu sarmalayıcı.

    Thread modeli:
        - Tray run() main thread'de blocking.
        - Diğer thread'ler `update_status()` çağırır (thread-safe).
        - Menu her açıldığında `_build_menu()` re-create eder
          (pystray pattern).
    """

    def __init__(
        self,
        app_name: str = "PazarChat",
        on_quit: Optional[Callable[[], None]] = None,
        icon_path: Optional[Path] = None,
    ) -> None:
        """
        Args:
            app_name: Tray'de gösterilecek isim.
            on_quit: Quit menu item tıklanınca çağrılan callback (shutdown trigger).
            icon_path: .ico veya .png. Yoksa generated bir icon kullanılır.
        """
        self._app_name = app_name
        self._on_quit = on_quit
        self._icon_path = icon_path

        self._status_lock = Lock()
        self._status: TrayStatus = _default_status()

        self._icon: Optional[pystray.Icon] = None

    # ------------------------------------------------------------------
    # Public API — thread-safe
    # ------------------------------------------------------------------

    def update_status(self, status: TrayStatus) -> None:
        """Status güncelle ve menu'yu yenile.

        pystray Icon.update_menu() menu callback'lerini bir sonraki açılışta
        yeniden çağırır; gerçek görünüm değişimi user menu'yu açtığında olur.
        """
        with self._status_lock:
            self._status = status
        if self._icon:
            try:
                self._icon.update_menu()
                # Title (hover tooltip) da güncel olsun
                self._icon.title = self._build_title()
            except Exception as e:
                logger.debug("Tray update_menu hatası (önemsiz): %s", e)

    def run(self) -> None:
        """Tray icon'u başlat. **Blocking** — main thread.

        Quit menu item tıklanınca dönerek main'in cleanup yapmasına izin verir.
        """
        image = self._load_icon_image()
        self._icon = pystray.Icon(
            name=self._app_name,
            icon=image,
            title=self._build_title(),
            menu=self._build_menu(),
        )
        logger.info("Tray başlatılıyor (main thread blocking)...")
        self._icon.run()  # blocking
        logger.info("Tray kapatıldı.")

    def stop(self) -> None:
        """Programatik olarak tray'i kapat (örn. fatal lisans hatasında)."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Internal: menu + icon
    # ------------------------------------------------------------------

    def _current_status(self) -> TrayStatus:
        with self._status_lock:
            return self._status

    def _build_title(self) -> str:
        """Tray icon hover tooltip metni — kısa olmalı, OS sınırları var."""
        s = self._current_status()
        if s.error_message:
            return f"PazarChat — HATA"
        if s.is_online:
            return f"PazarChat — {s.character_name} (bağlı)"
        return "PazarChat — bağlanıyor..."

    def _build_menu(self) -> pystray.Menu:
        """pystray menu'yu lambda'larla kur — her açılışta güncel status okur.

        Note: pystray menu item text callback'leri platforma göre 1 veya 2 arg
        alabilir. *args ile her ikisini de kabul ediyoruz.
        """
        def text_durum(*_args) -> str:
            s = self._current_status()
            if s.error_message:
                return f"⚠ Hata: {s.error_message[:60]}"
            return "● Bağlı" if s.is_online else "○ Bağlanıyor..."

        def text_karakter(*_args) -> str:
            s = self._current_status()
            return f"Karakter: {s.character_name} ({s.server_name})"

        def text_lisans(*_args) -> str:
            s = self._current_status()
            if not s.license_valid_until:
                return "Lisans: —"
            return f"Lisans: {s.license_valid_until.strftime('%d %b %Y')}"

        def text_son_cevap(*_args) -> str:
            s = self._current_status()
            if not s.last_reply:
                return "Henüz cevap gönderilmedi"
            content_short = s.last_reply[:40] + ("..." if len(s.last_reply) > 40 else "")
            return f"Son cevap → {s.last_reply_to}: {content_short}"

        return pystray.Menu(
            pystray.MenuItem(text_durum, action=None, enabled=False),
            pystray.MenuItem(text_karakter, action=None, enabled=False),
            pystray.MenuItem(text_lisans, action=None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(text_son_cevap, action=None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Çıkış", self._handle_quit),
        )

    def _handle_quit(self, _icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        """Çıkış menu item callback'i."""
        logger.info("Tray Çıkış tıklandı.")
        if self._on_quit:
            self._on_quit()
        if self._icon:
            self._icon.stop()

    def _load_icon_image(self) -> Image.Image:
        """Disk'ten .ico/.png yükle, yoksa programatik üret."""
        if self._icon_path and self._icon_path.exists():
            try:
                return Image.open(self._icon_path)
            except Exception as e:
                logger.warning("Icon yüklenemedi (%s), default kullanılıyor: %s",
                               self._icon_path, e)
        return self._generate_default_icon()

    @staticmethod
    def _generate_default_icon(size: int = 64) -> Image.Image:
        """Basit programatik icon: yeşil çember + 'P' harfi.

        Why: Repo'da .ico binary tutmak istemiyoruz. Production'da custom icon
        eklenmeli (assets/icon.ico) ama dev'de bu yeter.
        """
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Yeşil daire (KO yeşilini andırsın)
        draw.ellipse((4, 4, size - 4, size - 4), fill=(40, 180, 90, 255))
        # Beyaz P harfi (font olmadan polygon yaklaşımı yerine basit rect)
        # Pillow font import'unu zorlamamak için minimal görsel
        cx, cy = size // 2, size // 2
        draw.rectangle((cx - 8, cy - 14, cx - 4, cy + 14), fill=(255, 255, 255, 255))
        draw.ellipse((cx - 8, cy - 14, cx + 10, cy + 2), outline=(255, 255, 255, 255), width=4)
        return img


# -----------------------------------------------------------------------------
# Smoke test: doğrudan çalıştırılınca tray'i göster
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    def on_quit() -> None:
        print("Quit handled.")

    tray = TrayApp(on_quit=on_quit)
    # Status'u manuel set et — gerçekçi görünüm
    tray.update_status(TrayStatus(
        is_online=True,
        character_name="TestKarakter",
        server_name="Cypher",
        license_valid_until=datetime.now().astimezone(),
        last_reply="100m son fiyat",
        last_reply_to="KaraNinja",
        last_reply_at=datetime.now().astimezone(),
        error_message=None,
    ))
    tray.run()
    sys.exit(0)

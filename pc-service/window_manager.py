"""
PazarChat PC Service — Knight Online Window Manager
====================================================
KO penceresini başlığına göre bul, chat alanının ekran koordinatlarını hesapla.

Windows API (pywin32) kullanılır. Mac/Linux'ta import sırasında hata vermez,
sadece WindowManager().find_ko_window() çağrılınca NotImplementedError fırlatır.
Bu sayede config/test gibi kısımlar cross-platform editörde import edilebilir.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from typing import Optional


logger = logging.getLogger(__name__)


# pywin32 sadece Windows'ta var. Diğer platformlarda dummy modül.
_IS_WINDOWS = sys.platform == "win32"

if _IS_WINDOWS:
    import win32gui  # type: ignore[import-not-found]
    import win32con  # type: ignore[import-not-found] # noqa: F401


@dataclass(frozen=True)
class WindowRect:
    """KO penceresinin ekrandaki yeri (mutlak koordinat, piksel)."""
    hwnd: int
    title: str
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


@dataclass(frozen=True)
class ChatRegion:
    """Chat metninin yer aldığı kırpılacak alan. mss formatı."""
    left: int
    top: int
    width: int
    height: int

    def as_mss_dict(self) -> dict[str, int]:
        """mss kütüphanesinin beklediği dict formatı."""
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }


class WindowManager:
    """KO penceresini takip eder, chat alanı koordinatını hesaplar.

    Knight Online windowed mode'da chat tipik olarak ekranın sol-alt köşesinde
    yer alır. Genel oran: alt %25, sol %50.

    Override gerekirse config.ocr_crop_region ile sabit koordinat verilebilir.
    """

    # Chat alanı pencerenin yüzde kaçında — kalibrasyon değerleri.
    # KO sürümüne göre küçük farklar olabilir; gerekirse user override eder.
    CHAT_LEFT_RATIO = 0.0
    CHAT_TOP_RATIO = 0.70   # üstten %70 → alt %30 chat alanı
    CHAT_WIDTH_RATIO = 0.55 # sol %55
    CHAT_HEIGHT_RATIO = 0.25

    def __init__(self, window_title_partial: str) -> None:
        """
        Args:
            window_title_partial: Pencere başlığında geçecek (case-insensitive)
                kısmi metin, örn. "Knight OnLine Client".
        """
        if not _IS_WINDOWS:
            logger.warning(
                "Bu işletim sistemi Windows değil (%s). WindowManager sadece "
                "Windows'ta çalışır; dummy mode aktif.", sys.platform
            )
        self._needle = window_title_partial.lower().strip()
        self._cached_rect: Optional[WindowRect] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_ko_window(self) -> Optional[WindowRect]:
        """Açık pencereler arasında KO'yu ara. Bulamazsa None döner.

        Returns:
            WindowRect: bulunduysa pencere boyut/konum bilgisi
            None: KO pencere bulunamadı veya minimize edilmiş

        Non-Windows: Mac/Linux'ta None döner (smoke test için graceful).
        OCR loop bunu "pencere bulunamadı" olarak yorumlar, heartbeat etkilenmez.
        """
        if not _IS_WINDOWS:
            # Smoke test path: KO Mac'te çalışmaz, ama heartbeat + bot bağlantısı
            # test edilebilsin diye sessizce None döndür.
            return None

        match: Optional[WindowRect] = None

        def _enum_callback(hwnd: int, _: object) -> bool:
            nonlocal match
            if not win32gui.IsWindowVisible(hwnd):
                return True  # devam et
            title = win32gui.GetWindowText(hwnd) or ""
            if self._needle in title.lower():
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                # Minimize edilmiş pencereleri at: koordinatlar negatif/sıfır olur
                if right - left < 100 or bottom - top < 100:
                    return True
                match = WindowRect(
                    hwnd=hwnd,
                    title=title,
                    left=left,
                    top=top,
                    right=right,
                    bottom=bottom,
                )
                return False  # eşleşmeyi bulduk, durdur
            return True

        win32gui.EnumWindows(_enum_callback, None)

        if match:
            self._cached_rect = match
            logger.debug(
                "KO penceresi bulundu: hwnd=%d title=%r boyut=%dx%d konum=(%d,%d)",
                match.hwnd, match.title, match.width, match.height,
                match.left, match.top,
            )
        else:
            logger.debug("KO penceresi bulunamadı (aranan: %r)", self._needle)

        return match

    def get_chat_region(
        self,
        override: Optional[tuple[int, int, int, int]] = None,
    ) -> Optional[ChatRegion]:
        """KO penceresine göre chat alanı koordinatını hesapla.

        Args:
            override: (x, y, w, h) verilirse otomatik tespit atlanır,
                doğrudan bu koordinat döner. Config'de OCR_CROP_REGION ayarı bu
                amaçla kullanılır.

        Returns:
            ChatRegion: koordinatlar mutlak ekran piksel cinsinden
            None: KO penceresi bulunamadıysa
        """
        if override:
            x, y, w, h = override
            return ChatRegion(left=x, top=y, width=w, height=h)

        window = self.find_ko_window()
        if not window:
            return None

        chat_left = window.left + int(window.width * self.CHAT_LEFT_RATIO)
        chat_top = window.top + int(window.height * self.CHAT_TOP_RATIO)
        chat_width = int(window.width * self.CHAT_WIDTH_RATIO)
        chat_height = int(window.height * self.CHAT_HEIGHT_RATIO)

        return ChatRegion(
            left=chat_left,
            top=chat_top,
            width=chat_width,
            height=chat_height,
        )

    def is_foreground(self) -> bool:
        """KO penceresi şu an aktif (foreground) mı?

        Kullanım: kullanıcı KO'da değilse OCR'ı atlayıp CPU tasarrufu yapabiliriz.
        """
        if not _IS_WINDOWS:
            return False
        if not self._cached_rect:
            return False
        try:
            return win32gui.GetForegroundWindow() == self._cached_rect.hwnd
        except Exception:
            return False

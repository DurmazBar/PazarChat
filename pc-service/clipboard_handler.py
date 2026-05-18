"""
PazarChat PC Service — Clipboard Handler
=========================================
Telegram'dan gelen cevap metnini Windows panosuna kopyalar. Kullanıcı
KO penceresine geçip Ctrl+V ile yapıştırır (otomatik tuş simulasyonu YOK).

Cross-platform: pyperclip Mac/Linux/Windows'ta çalışır ama production Windows.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

import pyperclip


logger = logging.getLogger(__name__)


class ClipboardError(RuntimeError):
    """Pano işlemi başarısız (Windows pano servisi kilitli olabilir)."""


class ClipboardHandler:
    """Pano yazma + son yazılan metni hatırla.

    Why hatırla: tray UI'da "Son cevap: ..." göstermek için. Ayrıca
    aynı metni iki kez panoya yazmıyoruz (gereksiz wakeup).
    """

    def __init__(self) -> None:
        self._last_written: Optional[str] = None

    def copy_reply(self, content: str, to_character: str) -> None:
        """Cevabı panoya kopyala.

        Args:
            content: KO'ya yapıştırılacak ham metin.
            to_character: Sadece log için — hangi karaktere cevap yazılıyor.

        Raises:
            ClipboardError: Pano API hata verirse (örn. Windows pano servisi kilitli).
        """
        if not content:
            raise ClipboardError("Boş cevap panoya yazılamaz.")

        # KO PM cevabında /<KarakterAdı> prefix yaygın bir kullanım.
        # Ama bu davranış kullanıcıya bağlı; şimdilik sadece içeriği yazıyoruz.
        # İleride config'e taşınabilir (auto-prefix toggle).

        try:
            pyperclip.copy(content)
        except pyperclip.PyperclipException as e:
            # pyperclip Windows'ta nadir hata verir, genelde başka uygulama
            # panoya yazma kilidini tutuyorsa
            raise ClipboardError(f"Pano yazma başarısız: {e}") from e

        self._last_written = content
        logger.info(
            "Pano güncellendi → %s: %s",
            to_character,
            content[:80] + ("..." if len(content) > 80 else ""),
        )

    def last_written(self) -> Optional[str]:
        """Son panoya yazılan metni döndür (tray UI için)."""
        return self._last_written

    @staticmethod
    def is_supported() -> bool:
        """Pano API platformda çalışıyor mu?

        macOS ve Windows'ta her zaman True. Linux'ta xclip/xsel gerek.
        """
        if sys.platform == "win32":
            return True
        if sys.platform == "darwin":
            return True
        # Linux: pyperclip xclip/xsel gerektirir
        try:
            pyperclip.paste()
            return True
        except pyperclip.PyperclipException:
            return False

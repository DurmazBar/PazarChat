"""
PazarChat PC Service — Global Hotkey Handler
=============================================
Kullanıcı F8 (veya yapılandırılmış kısayol) bastığında:
  1. KO penceresinin **foreground** (aktif) olduğunu doğrula
     → değilse: tray notification + işlem iptal (yanlış pencereye yazma önleyici)
  2. Pano içeriğini son cevapla garanti et (başka uygulama panoyu değiştirmiş olabilir)
  3. Ctrl+V tuş kombinasyonu gönder (yapıştır)
  4. Enter gönder (KO'da PM cevabı olarak gider)

Why F8 değil de tıklama-tabanlı: Kullanıcının fiziksel tuş basışı = manuel input.
PazarChat otomatik macro değildir; kullanıcı her cevabı kendisi tetikler.

Windows-only. Mac/Linux'ta initialize edilmez (config.hotkey_paste_enabled=False).
"""

from __future__ import annotations

import logging
import sys
import time
from typing import Callable, Optional

import pyperclip


logger = logging.getLogger(__name__)


_IS_WINDOWS = sys.platform == "win32"


class HotkeyError(RuntimeError):
    """Hotkey kaydı veya tetiklemesinde hata."""


# Callback türü: tetikleme sonucu (success, message)
TriggerCallback = Callable[[bool, str], None]


class HotkeyHandler:
    """Global hotkey'i kaydet, callback'i kontrollü çalıştır.

    `keyboard` kütüphanesi sadece Windows için yüklenir
    (requirements.txt'te sys_platform marker'lı).

    Sınıf instance'ı bir kez yaratılır, start()/stop() lifecycle:
        handler = HotkeyHandler('f8', window_manager, clipboard_handler)
        handler.start(on_trigger=...)
        ...
        handler.stop()
    """

    def __init__(
        self,
        hotkey: str,
        window_manager,           # type: window_manager.WindowManager
        clipboard_handler,        # type: clipboard_handler.ClipboardHandler
    ) -> None:
        if not _IS_WINDOWS:
            raise NotImplementedError(
                "HotkeyHandler sadece Windows'ta çalışır."
            )

        self._hotkey = hotkey.lower().strip()
        self._window = window_manager
        self._clipboard = clipboard_handler
        self._registered = False
        self._on_trigger: Optional[TriggerCallback] = None

        # Windows-only API'ler için lazy import — Mac'te dosya import edilebilsin
        # ama HotkeyHandler() init'te zaten Windows kontrolü var.

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, on_trigger: Optional[TriggerCallback] = None) -> None:
        """Hotkey'i kaydet. Aynı handler iki kez start edilmemeli."""
        if self._registered:
            logger.warning("HotkeyHandler zaten kayıtlı")
            return

        self._on_trigger = on_trigger

        import keyboard  # type: ignore[import-not-found]

        try:
            keyboard.add_hotkey(
                self._hotkey,
                self._handle_press,
                suppress=False,        # KO'ya da geçsin (false = yutmadan ilet)
                trigger_on_release=False,
            )
        except Exception as e:
            raise HotkeyError(f"Hotkey kaydedilemedi ({self._hotkey}): {e}") from e

        self._registered = True
        logger.info("Global hotkey aktif: %s", self._hotkey)

    def stop(self) -> None:
        """Hotkey kaydını kaldır. Idempotent."""
        if not self._registered:
            return
        try:
            import keyboard  # type: ignore[import-not-found]
            keyboard.remove_hotkey(self._hotkey)
        except Exception as e:
            logger.warning("Hotkey kaldırma hatası (önemsiz): %s", e)
        finally:
            self._registered = False
            logger.info("Hotkey kaldırıldı: %s", self._hotkey)

    # ------------------------------------------------------------------
    # Internal — tuş basışı işleme
    # ------------------------------------------------------------------

    def _handle_press(self) -> None:
        """F8 basıldığında çağrılır. KO foreground kontrolü + paste + Enter."""
        try:
            self._do_paste()
        except Exception as e:
            logger.exception("Hotkey paste başarısız")
            if self._on_trigger:
                self._on_trigger(False, f"Yapıştırma hatası: {e}")

    def _do_paste(self) -> None:
        """Hybrid mode: kullanıcı F8 bastığında çağrılır.

        Güvenlik: SADECE KO penceresi aktifken (foreground'da) çalışır.
        Başka pencere aktifse no-op (yanlış pencereye yazma önleyici).
        """
        success, message = paste_clipboard_to_ko(
            self._window,
            self._clipboard,
            force_foreground=False,    # hybrid: kullanıcı zaten KO'ya geçmiş olmalı
        )
        if self._on_trigger:
            self._on_trigger(success, message)


# -----------------------------------------------------------------------------
# Standalone paste fonksiyonu — hem HotkeyHandler hem auto-mode kullanır
# -----------------------------------------------------------------------------

def paste_clipboard_to_ko(
    window_manager,                    # type: window_manager.WindowManager
    clipboard_handler,                 # type: clipboard_handler.ClipboardHandler
    force_foreground: bool = False,
    foreground_delay_ms: int = 200,
) -> tuple[bool, str]:
    """Pano içeriğini KO penceresine yapıştır + Enter gönder.

    Args:
        window_manager: KO penceresini bulan WindowManager instance
        clipboard_handler: Pano'daki son cevabı bilen ClipboardHandler instance
        force_foreground: True ise KO penceresini foreground'a alır (AUTO mode).
                          False ise KO foreground'da değilse no-op (HYBRID mode).
        foreground_delay_ms: force_foreground=True ise pencere geçişi sonrası
                             beklenecek süre (focus stable olsun).

    Returns:
        (success: bool, message: str)
    """
    if not _IS_WINDOWS:
        return False, "Paste sadece Windows'ta çalışır"

    import keyboard  # type: ignore[import-not-found]
    import win32gui  # type: ignore[import-not-found]

    # 1) KO penceresi bulunur mu?
    rect = window_manager.find_ko_window()
    if not rect:
        return False, "KO penceresi bulunamadı. Önce oyunu aç."

    # 2) Foreground kontrolü
    if force_foreground:
        # AUTO mode: KO'yu foreground'a getir
        try:
            win32gui.SetForegroundWindow(rect.hwnd)
        except Exception as e:
            return False, f"KO penceresine geçilemedi: {e}"
        time.sleep(foreground_delay_ms / 1000.0)
    else:
        # HYBRID mode: KO foreground'da değilse iptal
        if not window_manager.is_foreground():
            return False, "Önce KO penceresine geç, sonra hotkey'e bas."

    # 3) Son cevabı tekrar pano'ya kopyala (başka uygulama değiştirmiş olabilir)
    last = clipboard_handler.last_written()
    if not last:
        return False, "Yapıştırılacak cevap yok."

    try:
        pyperclip.copy(last)
    except pyperclip.PyperclipException as e:
        logger.warning("Pano refresh hatası (devam ediliyor): %s", e)

    # 4) Ctrl+V → Enter
    time.sleep(0.05)
    keyboard.send("ctrl+v")
    time.sleep(0.05)
    keyboard.send("enter")

    logger.info("Pano içeriği KO'ya yapıştırıldı: %s", last[:60])
    return True, f"Gönderildi: {last[:40]}"

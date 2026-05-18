"""
PazarChat PC Service — Entrypoint
==================================
Tüm modülleri başlatır, worker thread'leri kurar, tray'i ana thread'de çalıştırır.

Thread modeli:
  - main thread       → tray UI (blocking pystray.Icon.run)
  - heartbeat thread  → license_manager içinden, 60sn periyodik
  - ocr thread        → KO'dan PM yakala → Supabase'e yaz
  - polling thread    → Supabase'den outgoing cevapları çek → clipboard

Shutdown:
  - Tray "Çıkış" → _shutdown_event set → tüm worker'lar loop'tan çıkar
  - Ctrl+C (SIGINT) → aynı event set
  - Fatal lisans hatası → on_license_error → tray hata mesajı + shutdown

İlk Çalıştırma (Setup Wizard):
  - Eğer .env eksikse veya kritik alanlar boşsa setup_gui açılır
  - Kullanıcı formu doldurur → .env oluşturulur → uygulamayı yeniden başlatır
  - Bu kontrol config import edilmeden ÖNCE yapılır (yoksa config eksik .env ile patlar)
"""

from __future__ import annotations

import sys
from pathlib import Path


def _needs_setup_wizard(env_path: Path) -> bool:
    """.env yok veya kritik alanlar boş ise True döner.

    Bu fonksiyon config.py import edilmeden önce çağrılır — eksik .env ile
    config import'u ConfigError fırlatır ve setup wizard hiç görünmez.
    """
    if not env_path.exists():
        return True
    try:
        content = env_path.read_text(encoding="utf-8")
    except Exception:
        return True
    required = ("PAZARCHAT_API_KEY", "KO_CHARACTER_NAME", "SUPABASE_URL")
    for key in required:
        found = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith(f"{key}="):
                value = stripped[len(key) + 1:].strip()
                if value:
                    found = True
                break
        if not found:
            return True
    return False


# Sadece __main__ olarak çalıştırıldığında setup check yapılır
# (import time'da config-eksik testler için problem yaratmasın).
if __name__ == "__main__":
    _env_path = Path(__file__).resolve().parent / ".env"
    if _needs_setup_wizard(_env_path):
        try:
            from setup_gui import run_setup_if_needed
            _success = run_setup_if_needed(_env_path)
            if _success:
                sys.stderr.write(
                    "\n✅ Kurulum tamamlandı. PazarChat'i yeniden başlatın.\n"
                )
                sys.exit(0)
            else:
                sys.stderr.write("\n❌ Kurulum iptal edildi.\n")
                sys.exit(1)
        except ImportError as e:
            sys.stderr.write(
                f"\n[FATAL] Setup wizard yüklenemedi: {e}\n"
                "Manuel kurulum için .env dosyasını .env.example'dan kopyalayıp doldur.\n"
            )
            sys.exit(2)


# Setup OK ya da import time — diğer import'lar güvenli
import logging
import signal
import threading
from datetime import datetime
from typing import Optional

from clipboard_handler import ClipboardError, ClipboardHandler
from config import settings, setup_logging
from license_manager import LicenseManager, LicenseState
from ocr_engine import OcrEngine
from supabase_client import (
    AuthError,
    FingerprintMismatchError,
    PendingMessage,
    SupabaseClient,
    SupabaseError,
)
from tray_app import TrayApp, TrayStatus
from window_manager import WindowManager

# Hotkey sadece Windows'ta yüklenir (keyboard kütüphanesi sys_platform marker'lı)
_IS_WINDOWS = sys.platform == "win32"


logger = logging.getLogger("pazarchat.main")


# Outgoing mesaj polling aralığı (Supabase'den cevap çekme).
# Heartbeat'ten ayrı; bu daha sık çünkü kullanıcı deneyimi gecikme algılar.
POLL_INTERVAL_SECONDS = 3.0


class PazarChatService:
    """Tüm bileşenleri sahiplenen orchestrator."""

    def __init__(self) -> None:
        self._shutdown_event = threading.Event()
        self._fatal_error: Optional[str] = None

        # Bileşenler — start()'ta initialize edilir
        self._client: Optional[SupabaseClient] = None
        self._ocr: Optional[OcrEngine] = None
        self._window: Optional[WindowManager] = None
        self._clipboard: Optional[ClipboardHandler] = None
        self._license: Optional[LicenseManager] = None
        self._tray: Optional[TrayApp] = None
        self._hotkey = None  # HotkeyHandler (Windows-only)

        # Tray status state — birden çok thread bunu okur/günceller
        self._tray_state_lock = threading.Lock()
        self._tray_state: TrayStatus = TrayStatus(
            is_online=False,
            character_name=settings.ko_character_name,
            server_name=settings.ko_server_name,
            license_valid_until=None,
            last_reply=None,
            last_reply_to=None,
            last_reply_at=None,
            error_message=None,
        )

        # Worker thread'ler
        self._threads: list[threading.Thread] = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> int:
        """Servisi başlat. Tray exit edince int exit code döner."""
        logger.info("PazarChat PC servisi başlatılıyor...")
        logger.info("Karakter: %s (%s)", settings.ko_character_name, settings.ko_server_name)
        logger.info("Paste modu: %s", settings.paste_mode.upper())

        # Auto mode uyarısı — kullanıcı bilinçli kullansın
        if settings.paste_mode == "auto":
            logger.warning("=" * 70)
            logger.warning("⚠  OTOMATIK GÖNDERIM MODU AKTIF (PASTE_MODE=auto)")
            logger.warning("   Cevap geldiği anda PC penceresi KO'ya geçirilir ve")
            logger.warning("   pano içeriği otomatik yapıştırılır + Enter gönderilir.")
            logger.warning("   Knight Online TOS açısından yüksek risk içerir.")
            logger.warning("   Kullanım sorumluluğu SİZE aittir.")
            logger.warning("=" * 70)
        elif settings.paste_mode == "manual":
            logger.info("Manuel modda — bot cevapları sadece pano'ya kopyalanır.")

        # 1) Bileşenleri kur
        self._client = SupabaseClient(
            url=settings.supabase_url,
            anon_key=settings.supabase_anon_key,
            api_key=settings.pazarchat_api_key,
        )
        self._window = WindowManager(settings.ko_window_title)
        self._ocr = OcrEngine(
            use_gpu=settings.ocr_use_gpu,
            duplicate_window_size=settings.duplicate_window_size,
        )
        self._clipboard = ClipboardHandler()
        self._license = LicenseManager(
            client=self._client,
            character_name=settings.ko_character_name,
            server_name=settings.ko_server_name,
            interval_seconds=settings.heartbeat_interval_seconds,
        )
        self._tray = TrayApp(on_quit=self._request_shutdown)

        # 2) İlk heartbeat (sync) — lisans hatası varsa hemen patla
        try:
            self._license.start(
                on_state=self._on_license_state,
                on_error=self._on_license_error,
            )
        except FingerprintMismatchError as e:
            return self._fail_with(
                f"Bu lisans başka bir bilgisayara bağlı: {e}", exit_code=2
            )
        except AuthError as e:
            return self._fail_with(
                f"Lisans geçersiz veya abonelik dolmuş: {e}", exit_code=3
            )
        except SupabaseError as e:
            return self._fail_with(
                f"Supabase'e bağlanılamadı: {e}", exit_code=4
            )

        # 3) EasyOCR'ı eager yükle (uzun sürer — kullanıcı tray açılmadan
        #    önce loading'i görsün diye thread'de değil sync)
        logger.info("OCR motoru yükleniyor (ilk başlatma 2-3 sn sürer)...")
        try:
            self._ocr.warmup()
        except Exception as e:
            return self._fail_with(f"OCR motoru yüklenemedi: {e}", exit_code=5)

        # 4) Hotkey handler (Windows + hybrid/auto modlarında)
        if _IS_WINDOWS and settings.hotkey_enabled:
            try:
                from hotkey_handler import HotkeyHandler
                self._hotkey = HotkeyHandler(
                    hotkey=settings.hotkey_paste_key,
                    window_manager=self._window,
                    clipboard_handler=self._clipboard,
                )
                self._hotkey.start(on_trigger=self._on_hotkey_trigger)
            except Exception as e:
                logger.error("Hotkey başlatılamadı (devam ediliyor): %s", e)
                self._hotkey = None
        elif _IS_WINDOWS:
            logger.info("Hotkey atlandı (PASTE_MODE=manual)")
        else:
            logger.info("Hotkey atlandı (Windows değil)")

        # 5) Worker thread'leri başlat
        self._start_workers()

        # 5) SIGINT/SIGTERM handle et
        signal.signal(signal.SIGINT, self._signal_handler)
        try:
            signal.signal(signal.SIGTERM, self._signal_handler)
        except (AttributeError, ValueError):
            # Windows SIGTERM bazı durumlarda yok — sorun değil
            pass

        # 6) Tray (blocking)
        logger.info("Sistem hazır. Tray'den durum izleyebilirsiniz.")
        self._tray.run()  # blocking, çıkışta dönüş

        # 7) Cleanup
        self._shutdown()

        if self._fatal_error:
            logger.error("Servis hata ile sona erdi: %s", self._fatal_error)
            return 10
        logger.info("PazarChat temiz şekilde kapandı.")
        return 0

    def _request_shutdown(self) -> None:
        """Tray Çıkış veya SIGINT tarafından çağrılır."""
        if not self._shutdown_event.is_set():
            logger.info("Shutdown istendi.")
            self._shutdown_event.set()

    def _signal_handler(self, signum: int, _frame: object) -> None:
        logger.info("Sinyal alındı: %d", signum)
        self._request_shutdown()
        if self._tray:
            self._tray.stop()

    def _fail_with(self, message: str, exit_code: int) -> int:
        logger.error(message)
        sys.stderr.write(f"\n[FATAL] {message}\n\n")
        return exit_code

    def _shutdown(self) -> None:
        """Tüm worker thread'leri durdur + kaynakları temizle."""
        self._shutdown_event.set()

        if self._hotkey:
            self._hotkey.stop()
        if self._license:
            self._license.stop(timeout=3)
        for t in self._threads:
            t.join(timeout=3)

        if self._ocr:
            self._ocr.close()
        if self._client:
            self._client.close()

    # ------------------------------------------------------------------
    # Worker thread'leri
    # ------------------------------------------------------------------

    def _start_workers(self) -> None:
        self._threads = [
            threading.Thread(target=self._ocr_loop, name="OcrLoop", daemon=True),
            threading.Thread(target=self._polling_loop, name="PollingLoop", daemon=True),
        ]
        for t in self._threads:
            t.start()

    def _ocr_loop(self) -> None:
        """KO penceresini bul, chat alanından PM yakala, Supabase'e yaz."""
        assert self._window and self._ocr and self._client
        logger.info("OCR loop başladı (interval=%.1fs)", settings.ocr_interval_seconds)

        no_window_logged = False
        while not self._shutdown_event.is_set():
            try:
                region = self._window.get_chat_region(override=settings.ocr_crop_region)
                if not region:
                    if not no_window_logged:
                        logger.info("KO penceresi henüz bulunamadı, bekleniyor...")
                        no_window_logged = True
                    self._shutdown_event.wait(timeout=settings.ocr_interval_seconds)
                    continue

                if no_window_logged:
                    logger.info("KO penceresi bulundu, OCR aktif.")
                    no_window_logged = False

                captured = self._ocr.capture_pms(region.as_mss_dict())
                for pm in captured:
                    self._handle_captured_pm(pm)
            except Exception:
                logger.exception("OCR loop iterasyonu hatası (devam ediliyor)")

            self._shutdown_event.wait(timeout=settings.ocr_interval_seconds)

        logger.info("OCR loop sona erdi.")

    def _handle_captured_pm(self, pm) -> None:
        """Yakalanan PM'i Supabase'e gönder."""
        assert self._client
        try:
            self._client.insert_incoming_message(
                from_character=pm.from_character,
                to_character=settings.ko_character_name,
                content=pm.content,
                content_hash=pm.content_hash,
            )
        except AuthError as e:
            # Loop devam etsin, ama state'e yansıt
            self._update_error(f"Lisans hatası: {e}")
        except SupabaseError as e:
            # Geçici, retry duplicate filter sonraki tarama
            logger.warning("PM Supabase'e yazılamadı (sonraki taramada tekrar): %s", e)

    def _polling_loop(self) -> None:
        """Outgoing cevapları Supabase'den çek, panoya kopyala, mark_sent yap."""
        assert self._client and self._clipboard
        logger.info("Polling loop başladı (interval=%.1fs)", POLL_INTERVAL_SECONDS)

        while not self._shutdown_event.is_set():
            try:
                pending = self._client.get_pending_outgoing()
                for msg in pending:
                    self._handle_outgoing(msg)
            except AuthError as e:
                self._update_error(f"Lisans hatası: {e}")
            except SupabaseError as e:
                logger.warning("Outgoing polling hatası (retry): %s", e)
            except Exception:
                logger.exception("Polling loop iterasyonu hatası")

            self._shutdown_event.wait(timeout=POLL_INTERVAL_SECONDS)

        logger.info("Polling loop sona erdi.")

    def _handle_outgoing(self, msg: PendingMessage) -> None:
        """Tek bir outgoing mesajı işle: pano + (auto modda) auto-paste + mark_sent."""
        assert self._clipboard and self._client
        try:
            self._clipboard.copy_reply(msg.content, msg.to_character)
        except ClipboardError as e:
            logger.error("Pano hatası, mesaj sent_to_pc olarak işaretlenmiyor: %s", e)
            return

        # Tray state'i güncelle: son cevap bilgisi
        self._update_last_reply(msg.content, msg.to_character)

        # Auto mode → KO'ya otomatik paste + Enter
        if _IS_WINDOWS and settings.autopaste_enabled:
            try:
                from hotkey_handler import paste_clipboard_to_ko
                success, message = paste_clipboard_to_ko(
                    self._window,
                    self._clipboard,
                    force_foreground=True,
                    foreground_delay_ms=settings.auto_paste_delay_ms,
                )
                if success:
                    logger.info("Auto-paste OK: %s", message)
                else:
                    logger.warning("Auto-paste atlandı: %s", message)
            except Exception:
                logger.exception("Auto-paste hatası")
                # Hatadan bağımsız mark_sent'i yap — kullanıcı manuel halledebilir

        try:
            self._client.mark_message_sent(msg.id)
        except SupabaseError as e:
            logger.warning(
                "Mark sent başarısız (mesaj %s) — bir sonraki polling'de tekrar denenir: %s",
                msg.id, e,
            )
            return

    # ------------------------------------------------------------------
    # Tray state callbacks
    # ------------------------------------------------------------------

    def _on_license_state(self, state: LicenseState) -> None:
        with self._tray_state_lock:
            self._tray_state = TrayStatus(
                is_online=True,
                character_name=self._tray_state.character_name,
                server_name=self._tray_state.server_name,
                license_valid_until=state.valid_until,
                last_reply=self._tray_state.last_reply,
                last_reply_to=self._tray_state.last_reply_to,
                last_reply_at=self._tray_state.last_reply_at,
                error_message=None,
            )
        if self._tray:
            self._tray.update_status(self._tray_state)

    def _on_license_error(self, error: Exception) -> None:
        message = str(error)
        logger.error("Lisans fatal hatası: %s", message)
        self._fatal_error = message
        self._update_error(message)
        # Tray'i kapat → main thread döner → shutdown sequence başlar
        self._request_shutdown()
        if self._tray:
            self._tray.stop()

    def _update_error(self, message: str) -> None:
        with self._tray_state_lock:
            self._tray_state = TrayStatus(
                is_online=False,
                character_name=self._tray_state.character_name,
                server_name=self._tray_state.server_name,
                license_valid_until=self._tray_state.license_valid_until,
                last_reply=self._tray_state.last_reply,
                last_reply_to=self._tray_state.last_reply_to,
                last_reply_at=self._tray_state.last_reply_at,
                error_message=message,
            )
        if self._tray:
            self._tray.update_status(self._tray_state)

    def _on_hotkey_trigger(self, success: bool, message: str) -> None:
        """F8 basıldığında HotkeyHandler tarafından çağrılır.

        Başarılı/başarısız durumu loglanır. Tray durumunu da yenileyebiliriz
        ama kullanıcı zaten paste'i göz önünde yapıyor; ekstra UI gerek yok.
        """
        if success:
            logger.info("Hotkey paste OK: %s", message)
        else:
            logger.warning("Hotkey paste reddedildi: %s", message)
        # Tray'i refresh — son cevap görselini güncel tut
        if self._tray:
            with self._tray_state_lock:
                state = self._tray_state
            self._tray.update_status(state)

    def _update_last_reply(self, content: str, to_character: str) -> None:
        with self._tray_state_lock:
            self._tray_state = TrayStatus(
                is_online=self._tray_state.is_online,
                character_name=self._tray_state.character_name,
                server_name=self._tray_state.server_name,
                license_valid_until=self._tray_state.license_valid_until,
                last_reply=content,
                last_reply_to=to_character,
                last_reply_at=datetime.now().astimezone(),
                error_message=None,
            )
        if self._tray:
            self._tray.update_status(self._tray_state)


# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------

def main() -> int:
    """Setup wizard zaten module-level'da yapıldı — buraya gelmek = .env tamam."""
    setup_logging(settings.log_level, settings.log_file)
    service = PazarChatService()
    return service.start()


if __name__ == "__main__":
    sys.exit(main())

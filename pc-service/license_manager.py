"""
PazarChat PC Service — License Manager
=======================================
İki sorumluluk:
  1. Machine fingerprint hesapla (CPU + hostname + MAC) — 1 lisans = 1 PC kontrolü için.
  2. Periyodik heartbeat thread çalıştır → Supabase'e last_heartbeat update.

Heartbeat aynı zamanda lisans validasyonu — abonelik süresi dolduysa veya
başka makineden login varsa AuthError fırlatır. Bu durumda main loop kendini
durdurur.
"""

from __future__ import annotations

import hashlib
import logging
import platform
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from supabase_client import (
    AuthError,
    FingerprintMismatchError,
    HeartbeatResult,
    SupabaseClient,
    SupabaseError,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LicenseState:
    """Tray UI ve diğer modüller için lisans durumu."""
    license_id: str
    valid_until: datetime
    last_heartbeat: datetime
    fingerprint: str


# Callback türleri — main.py'ye event haberi vermek için
StateCallback = Callable[[LicenseState], None]
ErrorCallback = Callable[[Exception], None]


def compute_machine_fingerprint() -> str:
    """Stabil bir makine kimliği hash'i.

    Bileşenler:
      - MAC adresi (uuid.getnode → 48-bit, en stable kimlik)
      - hostname (kullanıcı PC adını değiştirmediği sürece stable)
      - CPU mimarisi (x86_64, ARM64, vs.)
      - Platform (Windows-10-..., macOS-..., Linux-...)

    Sonuç: SHA-256 hex (64 char). Kullanıcı PC değiştirirse değişir.

    Note: USB NIC takıp çıkardığında MAC değişebilir. Bu pratikte nadir;
    sorun olursa lisans transferi destek ile yapılır (LEGAL'e ekle).
    """
    components = [
        f"mac={uuid.getnode():012x}",
        f"host={platform.node()}",
        f"cpu={platform.machine()}",
        f"os={platform.platform()}",
    ]
    payload = "|".join(components).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class LicenseManager:
    """Heartbeat thread'i + lisans durumu yönetir.

    Lifecycle:
        manager = LicenseManager(client, character_name, server_name, interval)
        manager.start(on_state=..., on_error=...)
        # ... main loop ...
        manager.stop()
    """

    def __init__(
        self,
        client: SupabaseClient,
        character_name: str,
        server_name: Optional[str],
        interval_seconds: int = 60,
    ) -> None:
        self._client = client
        self._character_name = character_name
        self._server_name = server_name
        self._interval = interval_seconds
        self._fingerprint = compute_machine_fingerprint()

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # En son alınan state — tray UI okuyabilir
        self._state_lock = threading.Lock()
        self._state: Optional[LicenseState] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def fingerprint(self) -> str:
        return self._fingerprint

    def current_state(self) -> Optional[LicenseState]:
        """Thread-safe son state okuma. None ise henüz heartbeat atılmadı."""
        with self._state_lock:
            return self._state

    def start(
        self,
        on_state: Optional[StateCallback] = None,
        on_error: Optional[ErrorCallback] = None,
    ) -> None:
        """Heartbeat thread'i başlat. Önce sync ilk heartbeat at — hata varsa erken fail.

        Args:
            on_state: Her başarılı heartbeat sonrası LicenseState ile çağrılır.
            on_error: AuthError/FingerprintMismatchError olursa çağrılır, thread durur.
        """
        if self._thread and self._thread.is_alive():
            logger.warning("LicenseManager zaten çalışıyor.")
            return

        # 1) İlk heartbeat sync — hata varsa hemen patla (uygulama başlamasın)
        first_state = self._do_heartbeat_once()
        with self._state_lock:
            self._state = first_state
        if on_state:
            on_state(first_state)

        # 2) Background thread başlat
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            args=(on_state, on_error),
            name="HeartbeatThread",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            "Heartbeat thread başladı (%d saniye aralıkla, fingerprint=%s...)",
            self._interval, self._fingerprint[:12],
        )

    def stop(self, timeout: float = 5.0) -> None:
        """Heartbeat thread'i durdur. Idempotent."""
        if not self._thread:
            return
        self._stop_event.set()
        self._thread.join(timeout=timeout)
        if self._thread.is_alive():
            logger.warning("Heartbeat thread join timeout — daemon olduğu için process çıkışta ölecek.")
        self._thread = None

    # ------------------------------------------------------------------
    # Internal: thread loop
    # ------------------------------------------------------------------

    def _do_heartbeat_once(self) -> LicenseState:
        """Tek bir heartbeat çağrısı. Hata yutmaz, üst katmana fırlatır."""
        result: HeartbeatResult = self._client.heartbeat(
            machine_fingerprint=self._fingerprint,
            character_name=self._character_name,
            server_name=self._server_name,
        )
        return LicenseState(
            license_id=result.license_id,
            valid_until=result.valid_until,
            last_heartbeat=datetime.now().astimezone(),
            fingerprint=self._fingerprint,
        )

    def _run_loop(
        self,
        on_state: Optional[StateCallback],
        on_error: Optional[ErrorCallback],
    ) -> None:
        """Background heartbeat döngüsü. AuthError fatal — loop durur."""
        while not self._stop_event.is_set():
            # İlk loop iterasyonunda uyu (start() zaten ilk heartbeat'i attı)
            if self._stop_event.wait(timeout=self._interval):
                return  # stop edildik

            try:
                state = self._do_heartbeat_once()
                with self._state_lock:
                    self._state = state
                if on_state:
                    on_state(state)
                logger.debug(
                    "Heartbeat OK. valid_until=%s", state.valid_until.isoformat()
                )
            except (AuthError, FingerprintMismatchError) as e:
                # Fatal: lisans iptal, fingerprint mismatch, abonelik bitti
                logger.error("Lisans hatası, heartbeat durduruluyor: %s", e)
                if on_error:
                    on_error(e)
                return
            except SupabaseError as e:
                # Ağ hatası — geçici, retry et (yeni iterasyonda)
                logger.warning("Heartbeat ağ hatası (tekrar denenecek): %s", e)
            except Exception as e:
                # Beklenmeyen — loglayıp devam et, ama bildirim ver
                logger.exception("Heartbeat beklenmedik hata")
                if on_error:
                    on_error(e)

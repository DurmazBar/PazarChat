"""
PazarChat PC Service — OCR Engine
==================================
Pipeline:
  1. mss ile chat bölgesinden screenshot
  2. EasyOCR ile metni oku (Türkçe + İngilizce)
  3. PM regex: [PM][KarakterAdı]: mesaj
  4. Duplicate filter (son N hash)
  5. Yeni PM yakalandığında callback çağır

Thread-safe değil; tek bir worker thread'de çalışması bekleniyor (main.py).
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable, Iterable, Optional

import mss
import numpy as np


logger = logging.getLogger(__name__)


# Knight Online PM formatı: [PM][KarakterAdı]: mesaj içeriği
# KarakterAdı non-greedy (.+?) — köşeli parantezler arasında ne varsa yakala.
# Mesaj greedy (.+) — satır sonuna kadar al.
_PM_PATTERN = re.compile(r"\[\s*PM\s*\]\s*\[\s*(.+?)\s*\]\s*:?\s*(.+)", re.IGNORECASE)


@dataclass(frozen=True)
class CapturedPM:
    """Yakalanan ve duplicate filtresinden geçen bir PM."""
    from_character: str
    content: str
    content_hash: str       # (from_character, content) hash'i
    captured_at: float      # time.time()


# Callback tipi: yeni PM yakalandığında çağrılır
PMCallback = Callable[[CapturedPM], None]


class OcrEngine:
    """KO chat alanını periyodik OCR ile tarar.

    EasyOCR Reader instance bir kez yüklenir (ilk yükleme ~2-3 sn). Sonraki
    OCR çağrıları çok daha hızlı (~100-500 ms CPU, ~30-50 ms GPU).
    """

    def __init__(
        self,
        use_gpu: bool = False,
        languages: Optional[Iterable[str]] = None,
        duplicate_window_size: int = 50,
    ) -> None:
        """
        Args:
            use_gpu: NVIDIA + CUDA varsa True. Yoksa CPU.
            languages: EasyOCR dil listesi. Default: ['tr', 'en'].
                Türkçe ve İngilizce karakterler KO PM'lerinde olabilir.
            duplicate_window_size: Son N hash'i deque'de tut, duplicate'leri ele.
        """
        self._use_gpu = use_gpu
        self._languages = list(languages) if languages else ["tr", "en"]
        self._duplicate_window_size = duplicate_window_size

        # Recent hash deque — duplicate kontrolü için
        self._recent_hashes: deque[str] = deque(maxlen=duplicate_window_size)

        # EasyOCR lazy-load: ilk capture() çağrısında initialize edilir
        self._reader = None

        # Screenshot için bir mss instance kullan (re-create yapma, perf)
        self._sct = mss.mss()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def warmup(self) -> None:
        """EasyOCR'ı eagerly initialize et. Main loop başlamadan çağrılabilir."""
        if self._reader is None:
            logger.info(
                "EasyOCR yükleniyor (diller=%s, gpu=%s)... ilk yükleme ~2-3 saniye sürer.",
                self._languages, self._use_gpu,
            )
            t0 = time.time()
            # Geç import: EasyOCR yüklemesi yavaş, modül import'ta yapma
            import easyocr
            self._reader = easyocr.Reader(self._languages, gpu=self._use_gpu, verbose=False)
            logger.info("EasyOCR hazır (%.1fs)", time.time() - t0)

    def close(self) -> None:
        """mss screenshot kaynağını temizle."""
        try:
            self._sct.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Public: chat bölgesinden screenshot al, PM'leri yakala
    # ------------------------------------------------------------------

    def capture_pms(self, region: dict[str, int]) -> list[CapturedPM]:
        """Verilen bölgeden ekran görüntüsü al, OCR'la, yeni PM'leri döndür.

        Args:
            region: mss formatı {'left': x, 'top': y, 'width': w, 'height': h}

        Returns:
            list[CapturedPM]: Bu turda yakalanan, duplicate olmayan PM'ler.
        """
        self.warmup()
        assert self._reader is not None  # for type checker

        # 1) Screenshot
        try:
            shot = self._sct.grab(region)
        except Exception as e:
            logger.warning("Screenshot başarısız: %s", e)
            return []

        # mss ScreenShot → numpy array (RGB)
        img = np.array(shot)  # shape: (H, W, 4) BGRA

        # 2) OCR — paragraph=True line-bazlı birleştirir, PM tek satır olmaya yatkın
        try:
            results = self._reader.readtext(img, detail=0, paragraph=False)
        except Exception as e:
            logger.warning("OCR hatası: %s", e)
            return []

        # 3) Her satırı PM regex ile dene
        captured: list[CapturedPM] = []
        for line in results:
            pm = self._try_extract_pm(line)
            if pm is None:
                continue

            if self._is_duplicate(pm.content_hash):
                logger.debug("Duplicate PM atlandı: %s", pm.from_character)
                continue

            self._recent_hashes.append(pm.content_hash)
            captured.append(pm)
            logger.info(
                "PM yakalandı: [%s]: %s",
                pm.from_character,
                pm.content[:80] + ("..." if len(pm.content) > 80 else ""),
            )

        return captured

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _try_extract_pm(self, raw_line: str) -> Optional[CapturedPM]:
        """Tek bir OCR satırından PM pattern'i çıkarmaya çalış."""
        if not raw_line or "PM" not in raw_line.upper():
            return None

        match = _PM_PATTERN.search(raw_line)
        if not match:
            return None

        from_char = match.group(1).strip()
        content = match.group(2).strip()

        # OCR genelde 1-2 karakter hata yapabilir — boş veya çok kısa kabul etme
        if len(from_char) < 2 or len(content) < 1:
            return None

        return CapturedPM(
            from_character=from_char,
            content=content,
            content_hash=_hash_pm(from_char, content),
            captured_at=time.time(),
        )

    def _is_duplicate(self, content_hash: str) -> bool:
        return content_hash in self._recent_hashes


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _hash_pm(from_character: str, content: str) -> str:
    """Sabit, stable hash. SHA-1 (cryptographic değil, sadece dedup)."""
    payload = f"{from_character}|{content}".encode("utf-8")
    return hashlib.sha1(payload).hexdigest()

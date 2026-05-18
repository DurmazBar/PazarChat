"""
PazarChat PC Service — First-Run Setup Wizard
==============================================
İlk çalıştırmada (.env yoksa) açılan modern Tkinter penceresi. Kullanıcı:
  - Lisans anahtarı (pzc_...)
  - Karakter adı
  - Server adı (dropdown)
  - Paste mode (radio: manual/hybrid/auto)
  - Kullanım koşulları onayı

Form doğrulanır, "Bağlantıyı Test Et" Supabase heartbeat'i RPC ile dener,
"Kaydet & Başlat" `.env` dosyasını oluşturur ve ana servisi başlatır.

customtkinter kullanır (modern dark theme, Tkinter wrapper).
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import customtkinter as ctk
from tkinter import messagebox


logger = logging.getLogger(__name__)


# Default değerler — .env.example'dan
# NOT: SUPABASE_ANON_KEY public — Supabase'de tasarımı gereği client-side'a expose edilir.
# Bu key tek başına RLS bypass etmez; SQL fonksiyonları içinden API key (pzc_...)
# doğrulanır. JavaScript front-end'lerde de aynısı gömülüdür.
_DEFAULTS = {
    "SUPABASE_URL": "https://wgtgbrufzuzjtqhrojjo.supabase.co",
    "SUPABASE_ANON_KEY": (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndndGdicnVmenV6anRxaHJvampvIiwicm9sZSI6"
        "ImFub24iLCJpYXQiOjE3NzkwNDU1NjcsImV4cCI6MjA5NDYyMTU2N30."
        "QAVkmVafslUURQRewQD5HrkgTKGauNrkokW19P6EHS4"
    ),
    "KO_WINDOW_TITLE": "Knight OnLine Client",
    "KO_SERVER_NAME": "Cypher",
    "OCR_INTERVAL_SECONDS": "1.5",
    "OCR_USE_GPU": "False",
    "HEARTBEAT_INTERVAL_SECONDS": "60",
    "DUPLICATE_WINDOW_SIZE": "50",
    "INCOMING_POLL_INTERVAL": "2",
    "PASTE_MODE": "hybrid",
    "HOTKEY_PASTE_KEY": "f8",
    "AUTO_PASTE_DELAY_MS": "200",
    "LOG_LEVEL": "INFO",
    "LOG_FILE": "",
}


# Bilinen KO sunucuları (kullanıcı dropdown'dan seçer veya elle yazar)
_SERVERS = [
    "Cypher",
    "Logos",
    "Sirius",
    "Olympia",
    "Pathos",
    "Manes",
    "Apollo",
    "Gordion",
    "Other (manuel)",
]


class SetupWizard:
    """Modal kurulum penceresi. run() blocking, sonuç True ise kullanıcı kaydetti."""

    def __init__(self, env_path: Path):
        self._env_path = env_path
        self._completed = False

        # customtkinter tema ayarları
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")  # KO yeşil hissi

        self.root = ctk.CTk()
        self.root.title("PazarChat — Kurulum")
        self.root.geometry("620x900")
        self.root.resizable(False, False)

        # Pencere ortaya
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 310
        y = (self.root.winfo_screenheight() // 2) - 450
        self.root.geometry(f"620x900+{x}+{y}")

        # X butonuna basınca çıkış (sırasıyla setup tamamlanmadı sayılır)
        self.root.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # State variables
        self.api_key_var = ctk.StringVar()
        self.character_var = ctk.StringVar()
        self.server_var = ctk.StringVar(value="Cypher")
        self.paste_mode_var = ctk.StringVar(value="hybrid")
        self.terms_var = ctk.BooleanVar(value=False)

        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        main = ctk.CTkFrame(self.root, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=24, pady=20)

        # Başlık
        title = ctk.CTkLabel(
            main, text="PazarChat", font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=(0, 4))

        subtitle = ctk.CTkLabel(
            main,
            text="Knight Online Pazar Asistanı",
            font=ctk.CTkFont(size=13),
            text_color="gray60",
        )
        subtitle.pack(pady=(0, 20))

        # ---- Lisans Anahtarı ----
        self._field_label(main, "🔑  Lisans Anahtarı")
        api_entry = ctk.CTkEntry(
            main,
            textvariable=self.api_key_var,
            placeholder_text="pzc_...",
            height=38,
            font=ctk.CTkFont(family="Courier", size=12),
        )
        api_entry.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(
            main,
            text="Telegram'da @KO_PazarChat_bot'a /durum yazıp alabilirsin.",
            font=ctk.CTkFont(size=11),
            text_color="gray50",
        ).pack(anchor="w", pady=(0, 16))

        # ---- Karakter Adı ----
        self._field_label(main, "🎮  Karakter Adı")
        ctk.CTkEntry(
            main,
            textvariable=self.character_var,
            placeholder_text="Karakter adın",
            height=38,
        ).pack(fill="x", pady=(0, 16))

        # ---- Server ----
        self._field_label(main, "🌐  Sunucu")
        server_menu = ctk.CTkOptionMenu(
            main,
            values=_SERVERS,
            variable=self.server_var,
            height=38,
        )
        server_menu.pack(fill="x", pady=(0, 20))

        # ---- Paste Mode ----
        self._field_label(main, "⚙  Cevap Gönderim Modu")

        # Her mod için ayrı kart (radio + açıklama + risk badge)
        self._mode_card(
            main,
            value="manual",
            title="Manuel",
            badge="🟢 Düşük risk",
            badge_color="#16a34a",
            description=(
                "Telegram'da yazdığın cevap PC'nin panosuna kopyalanır.\n"
                "Sen KO'ya geçip chat input'a Ctrl+V ile yapıştırır, Enter'la gönderirsin.\n"
                "Hiçbir tuş simülasyonu yoktur — KO TOS açısından en savunulabilir mod."
            ),
        )

        self._mode_card(
            main,
            value="hybrid",
            title="Hibrit (F8 hotkey)",
            badge="🟡 Orta risk · Önerilen",
            badge_color="#eab308",
            description=(
                "Cevap pano'ya kopyalanır + F8 tuşu küresel olarak dinlenir.\n"
                "Sen KO penceresinde F8'e basınca otomatik yapıştırma + Enter olur.\n"
                "GÜVENLİK: F8 sadece KO aktif (foreground) pencereyse çalışır.\n"
                "Discord/Chrome aktifken F8 → hiçbir şey olmaz (yanlış yere yazma yok)."
            ),
        )

        self._mode_card(
            main,
            value="auto",
            title="Otomatik",
            badge="🔴 Yüksek risk",
            badge_color="#dc2626",
            description=(
                "Cevap geldiği anda PC servisi KO penceresini otomatik öne alır ve\n"
                "yapıştırma + Enter gönderir. Sen başka pencerede olsan bile çalışır.\n"
                "⚠ Knight Online TOS'unda 'otomasyon aracı' olarak değerlendirilebilir.\n"
                "Banlanma riski mevcuttur, kullanım sorumluluğu sana aittir."
            ),
        )

        ctk.CTkLabel(
            main,
            text="Detaylı yasal açıklama: Kullanım Koşulları §3.1",
            font=ctk.CTkFont(size=10),
            text_color="gray50",
        ).pack(anchor="w", pady=(4, 16))

        # ---- Kullanım Koşulları ----
        terms_check = ctk.CTkCheckBox(
            main,
            text="Kullanım Koşullarını okudum ve onaylıyorum",
            variable=self.terms_var,
            font=ctk.CTkFont(size=12),
        )
        terms_check.pack(anchor="w", pady=(0, 24))

        # ---- Butonlar ----
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 8))

        self.test_btn = ctk.CTkButton(
            btn_frame,
            text="Bağlantıyı Test Et",
            command=self._on_test,
            height=42,
            fg_color="gray30",
            hover_color="gray40",
        )
        self.test_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.save_btn = ctk.CTkButton(
            btn_frame,
            text="Kaydet & Başlat",
            command=self._on_save,
            height=42,
            font=ctk.CTkFont(weight="bold"),
        )
        self.save_btn.pack(side="left", fill="x", expand=True, padx=(6, 0))

        # Status mesajı (test sonucu, hata vs.)
        self.status_label = ctk.CTkLabel(
            main, text="", font=ctk.CTkFont(size=11), text_color="gray60"
        )
        self.status_label.pack(pady=(8, 0))

    def _field_label(self, parent, text: str):
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

    def _mode_card(
        self,
        parent,
        value: str,
        title: str,
        badge: str,
        badge_color: str,
        description: str,
    ):
        """Paste mode için detaylı kart: radio + başlık + risk badge + açıklama."""
        card = ctk.CTkFrame(parent, fg_color="gray20", corner_radius=8)
        card.pack(fill="x", pady=4)

        # Üst satır: radio + başlık + risk badge
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 4))

        radio = ctk.CTkRadioButton(
            header,
            text=title,
            variable=self.paste_mode_var,
            value=value,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        radio.pack(side="left")

        badge_label = ctk.CTkLabel(
            header,
            text=badge,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=badge_color,
        )
        badge_label.pack(side="right")

        # Alt satır: açıklama
        ctk.CTkLabel(
            card,
            text=description,
            font=ctk.CTkFont(size=11),
            text_color="gray70",
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=12, pady=(0, 10))

    # ------------------------------------------------------------------
    # Buton callback'leri
    # ------------------------------------------------------------------

    def _validate(self) -> Optional[str]:
        """Form validation — hata mesajı döner veya None (tamam)."""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            return "Lisans anahtarı boş bırakılamaz."
        if not api_key.startswith("pzc_"):
            return "Lisans anahtarı 'pzc_' ile başlamalı."
        if len(api_key) < 30:
            return "Lisans anahtarı çok kısa görünüyor."

        character = self.character_var.get().strip()
        if not character:
            return "Karakter adı boş bırakılamaz."
        if len(character) < 2:
            return "Karakter adı çok kısa."

        if not self.terms_var.get():
            return "Devam etmek için Kullanım Koşullarını onaylamalısın."

        return None

    def _on_test(self):
        """Supabase'e heartbeat dene — lisans gerçek mi?"""
        err = self._validate()
        if err:
            self._set_status(err, error=True)
            return

        self._set_status("⏳ Bağlantı test ediliyor...", error=False)
        self.test_btn.configure(state="disabled")
        self.root.update()

        try:
            import httpx

            api_key = self.api_key_var.get().strip()
            character = self.character_var.get().strip()
            server = self.server_var.get().strip() or "Unknown"

            # Sentinel machine fingerprint ile pc_heartbeat çağır
            # Eğer geçersiz lisans → 28000 hatası, geçerliyse 200 OK
            response = httpx.post(
                f"{_DEFAULTS['SUPABASE_URL']}/rest/v1/rpc/pc_heartbeat",
                headers={
                    "apikey": _DEFAULTS["SUPABASE_ANON_KEY"],
                    "Authorization": f"Bearer {_DEFAULTS['SUPABASE_ANON_KEY']}",
                    "Content-Type": "application/json",
                },
                json={
                    "p_api_key": api_key,
                    "p_machine_fingerprint": "SETUP_WIZARD_TEST",
                    "p_character_name": character,
                    "p_server_name": server,
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                self._set_status("✅ Bağlantı başarılı, lisans geçerli.", error=False)
            elif response.status_code in (400, 401, 403):
                err_data = response.json() if response.text else {}
                msg = err_data.get("message", "Lisans reddedildi")
                if "baska bir bilgisayara" in msg.lower():
                    self._set_status(
                        "⚠ Bu lisans başka bir bilgisayara bağlı. "
                        "Destek ile transfer yapın.",
                        error=True,
                    )
                else:
                    self._set_status(f"❌ {msg}", error=True)
            else:
                self._set_status(
                    f"❌ Beklenmedik hata: HTTP {response.status_code}",
                    error=True,
                )
        except Exception as e:
            self._set_status(f"❌ Ağ hatası: {e}", error=True)
        finally:
            self.test_btn.configure(state="normal")

    def _on_save(self):
        err = self._validate()
        if err:
            self._set_status(err, error=True)
            return

        try:
            self._write_env()
        except Exception as e:
            messagebox.showerror(
                "Hata", f".env dosyası yazılamadı:\n{e}"
            )
            return

        self._completed = True
        self.root.destroy()

    def _on_cancel(self):
        """X butonuna basıldı."""
        if messagebox.askyesno(
            "Kurulumu iptal et?",
            "Kurulumu tamamlamadan çıkmak istediğine emin misin?\n"
            "Servis başlatılamayacak.",
        ):
            self._completed = False
            self.root.destroy()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_status(self, text: str, error: bool = False):
        self.status_label.configure(
            text=text, text_color="#ef4444" if error else "#22c55e"
        )

    def _write_env(self):
        """Form değerlerinden .env dosyasını oluştur."""
        api_key = self.api_key_var.get().strip()
        character = self.character_var.get().strip()
        server = self.server_var.get().strip()
        if server == "Other (manuel)":
            server = "Unknown"

        paste_mode = self.paste_mode_var.get()

        lines = [
            "# PazarChat .env (setup wizard tarafından oluşturuldu)",
            f"SUPABASE_URL={_DEFAULTS['SUPABASE_URL']}",
            f"SUPABASE_ANON_KEY={_DEFAULTS['SUPABASE_ANON_KEY']}",
            f"PAZARCHAT_API_KEY={api_key}",
            f"KO_WINDOW_TITLE={_DEFAULTS['KO_WINDOW_TITLE']}",
            f"KO_CHARACTER_NAME={character}",
            f"KO_SERVER_NAME={server}",
            f"OCR_INTERVAL_SECONDS={_DEFAULTS['OCR_INTERVAL_SECONDS']}",
            f"OCR_USE_GPU={_DEFAULTS['OCR_USE_GPU']}",
            "OCR_CROP_REGION=",
            f"HEARTBEAT_INTERVAL_SECONDS={_DEFAULTS['HEARTBEAT_INTERVAL_SECONDS']}",
            f"DUPLICATE_WINDOW_SIZE={_DEFAULTS['DUPLICATE_WINDOW_SIZE']}",
            f"PASTE_MODE={paste_mode}",
            f"HOTKEY_PASTE_KEY={_DEFAULTS['HOTKEY_PASTE_KEY']}",
            f"AUTO_PASTE_DELAY_MS={_DEFAULTS['AUTO_PASTE_DELAY_MS']}",
            f"LOG_LEVEL={_DEFAULTS['LOG_LEVEL']}",
            f"LOG_FILE={_DEFAULTS['LOG_FILE']}",
            "",
        ]

        self._env_path.parent.mkdir(parents=True, exist_ok=True)
        self._env_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(".env dosyası oluşturuldu: %s", self._env_path)

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run(self) -> bool:
        """Pencereyi göster, kullanıcı bitirene kadar bekle. True = başarılı."""
        self.root.mainloop()
        return self._completed


def needs_setup(env_path: Path) -> bool:
    """`.env` dosyası eksikse veya kritik alanlar boşsa True döner."""
    if not env_path.exists():
        return True

    # Kritik alanlar dolu mu kontrol
    try:
        content = env_path.read_text(encoding="utf-8")
    except Exception:
        return True

    required = ["PAZARCHAT_API_KEY=", "KO_CHARACTER_NAME=", "SUPABASE_URL="]
    for key in required:
        # Anahtar satırı var ama değer boş mu?
        for line in content.splitlines():
            line = line.strip()
            if line.startswith(key):
                value = line[len(key):].strip()
                if not value:
                    return True
                break
        else:
            return True  # anahtar hiç yok
    return False


def run_setup_if_needed(env_path: Path) -> bool:
    """Main entry point. Setup gerekirse çalıştır. True döner = artık çalışabilir."""
    if not needs_setup(env_path):
        return True

    logger.info("İlk kurulum gerekli, setup wizard açılıyor...")
    wizard = SetupWizard(env_path)
    return wizard.run()


# Standalone test için
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_env = Path(__file__).parent / ".env"
    success = run_setup_if_needed(test_env)
    print(f"Setup tamamlandı: {success}")
    sys.exit(0 if success else 1)

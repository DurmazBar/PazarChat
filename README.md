# PazarChat

> Knight Online tüccar oyuncularının pazar kurarken bilgisayar başından ayrılabilmesi için bir uzaktan PM yönetim sistemi.

PC'de yakalanan PM'ler Telegram'a anlık bildirim olarak gelir, kullanıcı telefondan cevap yazar, cevap PC'nin panosuna kopyalanır — kullanıcı KO'ya geri döndüğünde **F8** veya **Ctrl+V** ile gönderir.

---

## Hızlı Bakış

| Konu | Değer |
|------|-------|
| **Hedef kitle** | Knight Online'da pazar kuran tüccar oyuncular (Türkiye) |
| **Çözdüğü problem** | AFK pazarcılıkta bilgisayar başından ayrılınca müşteri kaçırma |
| **Çekirdek deneyim** | PM gelir → Telegram bildirim → telefondan cevap → PC'de F8 |
| **İş modeli** | Aylık abonelik (fiyatlandırma beta sonrası belirlenecek) |
| **Lisans modeli** | 1 lisans = 1 PC (machine fingerprint ile kontrol) |
| **Telegram bot** | [@KO_PazarChat_bot](https://t.me/KO_PazarChat_bot) |

---

## Sistem Bileşenleri

```
[Knight Online PC]
       ↓ OCR
[PC Servisi (Python)] ─────────┐
                               │
[Web (Next.js)] ────────────── ├──→ [Supabase]
   landing + ödeme + .exe      │
                               │
[Telegram Bot (Python/aiogram)] ┘
       ↑
[Kullanıcının Telegram'ı]
```

---

## 🚀 Hızlı Başlangıç (Beta Kullanıcısı)

### ⭐ Önerilen Yöntem — Hazır `.exe` İndir

> Python kurmadan, tek bir zip ile başla.

1. **[Releases sayfasına git](https://github.com/DurmazBar/PazarChat/releases/latest)**
2. `PazarChat-windows.zip` dosyasını indir
3. Bir klasöre çıkar (örn. `C:\PazarChat`)
4. Klasör içindeki `.env.example`'ı `.env` olarak kopyala
5. Notepad ile `.env` aç:
   - `PAZARCHAT_API_KEY=pzc_...` (Telegram bot'tan `/durum` ile al)
   - `KO_CHARACTER_NAME=...` (KO karakter adın)
6. `PazarChat.exe`'yi çift tıkla
7. KO aç → pazar kur → Telegram'a bildirim gelmeye başlar

⚠ **Microsoft Defender uyarısı normal** — imzasız .exe için "Tanınmayan uygulama" der.
"Diğer bilgi" → "Yine de çalıştır" ile geç.

### Manuel Yöntem — Geliştiriciler İçin

> 📘 **Detaylı rehber:** [WINDOWS_SETUP.md](WINDOWS_SETUP.md)

```powershell
# 1. Repo'yu klonla
cd $HOME\Documents
git clone https://github.com/DurmazBar/PazarChat.git
cd PazarChat\pc-service

# 2. Python sanal ortam + bağımlılıklar
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Config oluştur
copy .env.example .env
notepad .env       # PAZARCHAT_API_KEY ve KO_CHARACTER_NAME doldur

# 4. Çalıştır
python main.py
```

**Önkoşullar (manuel yöntem için):**
- Windows 10/11 (64-bit)
- Python 3.12 ([python.org](https://www.python.org/downloads/release/python-3128/) — "Add to PATH" işaretli olmalı)
- Git for Windows ([git-scm.com](https://git-scm.com/download/win))
- Telegram hesabı + **bot'tan davetiye kodu** (`/davetiye BETA-XXXXXX`)

### Mac/Linux için (sadece bot/web geliştirme)

```bash
# Telegram bot
cd telegram-bot
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env
python main.py

# Web (Next.js)
cd web
npm install
cp .env.example .env.local && nano .env.local
npm run dev    # http://localhost:3000
```

> ⚠ **Mac/Linux'ta PC servisi tam çalışmaz** — `pywin32` ve `keyboard` Windows-only. OCR + heartbeat çalışır ama F8 hotkey ve KO penceresi yönetimi yok.

---

## 🔑 Davetiye Akışı (Beta)

```
1. Telegram'da @KO_PazarChat_bot'a git
2. /start yaz → hoş geldin mesajı
3. /davetiye BETA-XXXXXX (kodu admin'den al)
4. Bot lisans anahtarı verir (pzc_...)
5. PC servisi .env dosyasındaki PAZARCHAT_API_KEY'e yapıştır
6. python main.py → KO aç → pazar kur
```

---

## 🧪 End-to-End Test

```
[KO'da müşteri PM atar]
        ↓
[PC servisi OCR ile yakalar]
        ↓
[Supabase'e yazar]
        ↓
[Bot polling görür → Telegram'a kart gönderir]
        ↓
[Sen hazır cevap butonuna basarsın VEYA "Yanıtla" ile yazarsın]
        ↓
[Bot DB'ye outgoing INSERT yapar]
        ↓
[PC servisi polling ile çeker → Windows panosuna yazar]
        ↓
[Sen KO'ya geç → F8 (hybrid) VEYA Ctrl+V (manuel) → cevap gider]
```

---

## ⚙ Cevap Gönderim Modları (`.env`'de `PASTE_MODE`)

| Mod | Davranış | TOS Riski |
|-----|----------|-----------|
| `manual` | Sadece pano, kullanıcı Ctrl+V yapar | 🟢 Düşük |
| `hybrid` (default) | Pano + F8 hotkey (sadece KO aktifken) | 🟡 Orta |
| `auto` | Cevap geldiği anda otomatik KO foreground + paste + Enter | 🔴 Yüksek |

Detay: [LEGAL.md → §3.1](LEGAL.md)

---

## 📁 Klasör Yapısı

```
PazarChat/
├── README.md             # Bu dosya
├── WINDOWS_SETUP.md      # Windows kurulum rehberi (detaylı)
├── PAZARCHAT.md          # Mimari + roadmap
├── BUSINESS.md           # İş modeli + pricing
├── LEGAL.md              # KVKK + KO TOS riskleri
├── CLAUDE.md             # AI context (Claude Code için)
│
├── pc-service/           # Python — KO PC'de çalışır
│   ├── main.py           # Entrypoint
│   ├── ocr_engine.py     # Screenshot + EasyOCR + PM regex
│   ├── window_manager.py # KO penceresi bulma
│   ├── supabase_client.py # RPC client
│   ├── license_manager.py # Heartbeat + fingerprint
│   ├── clipboard_handler.py
│   ├── hotkey_handler.py # F8 hybrid/auto paste
│   ├── tray_app.py       # System tray UI
│   ├── config.py
│   └── requirements.txt
│
├── telegram-bot/         # Python aiogram 3.x — Cloud/VPS'te
│   ├── main.py
│   ├── handlers/         # /start, /davetiye, /durum, vs.
│   ├── services/         # Supabase erişim
│   └── requirements.txt
│
├── web/                  # Next.js 15 + Tailwind + Vercel
│   ├── app/              # Landing, indir, pricing, yasal sayfalar
│   ├── components/
│   └── package.json
│
└── supabase/
    └── migrations/       # 5 SQL migration
```

---

## 📚 Detaylı Dökümanlar

| Dosya | İçerik |
|-------|--------|
| [PAZARCHAT.md](PAZARCHAT.md) | Mimari, veri akışı, şema, modüller, roadmap |
| [BUSINESS.md](BUSINESS.md) | Pazar, hedef kitle, fiyatlandırma, beta stratejisi |
| [LEGAL.md](LEGAL.md) | KVKK, Knight Online TOS riski, şirket gereklilikleri |
| [WINDOWS_SETUP.md](WINDOWS_SETUP.md) | Windows için adım adım kurulum + sorun giderme |
| [CLAUDE.md](CLAUDE.md) | AI (Claude Code) context ve çalışma kuralları |

---

## 🛠 Geliştirici Notları

### `.exe` Build Almak

İki yol var:

**1. GitHub Actions (önerilen):**
```bash
# Yeni release yayınla — Actions otomatik build alır, Release oluşturur
git tag v0.1.0-beta
git push --tags
```
Veya manuel: GitHub → Actions → **Build PC Service (Windows)** → Run workflow

Build ~10-15 dk sürer. Sonuç: [Releases](https://github.com/DurmazBar/PazarChat/releases) sayfasında `PazarChat-windows.zip`.

**2. Yerel build (Windows'ta):**
```powershell
cd pc-service
.\venv\Scripts\Activate.ps1
pip install pyinstaller==6.10.0
pyinstaller --clean pazarchat.spec
# Çıktı: dist\PazarChat\PazarChat.exe
```

### Supabase migration uygulama (yeni proje için)

```bash
# Supabase CLI veya MCP tool ile
# Sırayla: 001 → 005
psql $DATABASE_URL -f supabase/migrations/001_initial.sql
psql $DATABASE_URL -f supabase/migrations/002_function_search_path_hardening.sql
psql $DATABASE_URL -f supabase/migrations/003_pc_rpc_functions.sql
psql $DATABASE_URL -f supabase/migrations/004_bot_redeem_invite.sql
psql $DATABASE_URL -f supabase/migrations/005_table_grants.sql
```

### Bot deploy (VPS / Hetzner / DigitalOcean)

```bash
# Ubuntu 22.04 VPS'te
sudo apt update && sudo apt install python3.12 python3.12-venv git
git clone https://github.com/DurmazBar/PazarChat.git
cd PazarChat/telegram-bot
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
nano .env       # token, service_role doldur
# systemd service ile 7/24 çalıştır (örnek systemd unit yakında)
```

---

## 📈 Durum

**Faz 1 — MVP geliştirme:**

- [x] Supabase schema + 5 migration uygulandı
- [x] PC servisi (Mac smoke test geçti)
- [x] Telegram bot (`/start`, `/davetiye`, `/durum`, polling, hazır cevap, native reply)
- [x] Web sayfaları (landing + indir + pricing + 4 yasal sayfa)
- [x] End-to-end test (Mac): PM → bot → reply → pano
- [x] 3 paste modu (manual / hybrid / auto)
- [ ] **Windows'ta gerçek OCR + F8 testi** ← şu an buradayız
- [ ] PyInstaller `.exe` paketleme
- [ ] Bot VPS deploy
- [ ] Beta testçi davetiyeleri

Detaylı roadmap: [PAZARCHAT.md → §7](PAZARCHAT.md#7-roadmap)

---

## ⚠ Önemli — Yasal

Bu yazılım **bağımsız üçüncü taraf bir yardımcı uygulamadır**. Knight Online veya NTTGames ile bağlantısı yoktur. Knight Online'ın kullanım koşullarına uyum **tamamen kullanıcı sorumluluğundadır**. Detaylar: [LEGAL.md](LEGAL.md).

---

## 📞 İletişim

Beta erişimi veya destek için: [@KO_PazarChat_bot](https://t.me/KO_PazarChat_bot) → `/destek`

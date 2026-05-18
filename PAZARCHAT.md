# PazarChat — Mimari ve Geliştirme Dökümanı

> Bu dosya teknik **ground truth**'tur. Mimari kararlar, veri akışı, şema ve modül tanımları burada. İş modeli için → [BUSINESS.md](BUSINESS.md), yasal süreç için → [LEGAL.md](LEGAL.md).

---

## 1. Ürün Tanımı

PazarChat, Knight Online tüccar oyuncularının pazar kurarken bilgisayar başından ayrılabilmesi için bir **uzaktan PM yönetim sistemi**dir.

### Kullanım Senaryosu
1. Oyuncu Knight Online'da pazar kurar (örn. Moradon, Ronark Land). Karakter başlığında satış/alış ilanı yazar.
2. Bilgisayar başından ayrılır (yemek, banyo, başka oda).
3. Müşteriler PM atar: `"kaça?"`, `"100m verir misin?"`, `"+9 var mı?"`
4. PC servisi PM'i OCR ile yakalar → Supabase'e yazar → Telegram bot kullanıcıya bildirim gönderir.
5. Kullanıcı telefondan cevap yazar veya hazır cevap butonuna basar.
6. Cevap Supabase üzerinden PC servisine ulaşır → panoya kopyalanır + tray bildirimi: *"Cevap hazır, Ctrl+V'ye basın"*
7. Kullanıcı bilgisayara döndüğünde Ctrl+V ile PM'e cevap verir.

### Ne YAP / Ne YAPMA — Kasıtlı Sınırlar

| Yap | Yapma |
|-----|-------|
| OCR ile PM'i yakala | Memory reading |
| Cevabı panoya kopyala | Keyboard simulation ile otomatik gönderim |
| Kullanıcıya hazır cevap butonu sun | Otomatik anahtar kelime → otomatik cevap |
| Karakter geçmişini tut | Otomatik trade kabul/red |
| Bildirimi sustur (kullanıcı tetiklemesiyle) | Karakter hareketi / oyun penceresine input |

**Neden bu sınırlar:** Knight Online TOS riskini azaltmak ve "macro/bot" kategorisine sokulmayı engellemek için (bkz. [LEGAL.md](LEGAL.md)).

---

## 2. Sistem Mimarisi

```
┌──────────────────────────────────────────────────┐
│  pazarchat.com (Next.js + Vercel)                │
│  • Landing & pricing                              │
│  • Ödeme akışı (iyzico / Shopier — TBD)           │
│  • .exe indirme linki                             │
│  • KVKK / TOS / Mesafeli Satış Sözleşmesi         │
│  • Admin paneli (faz 4+)                          │
└─────────────────┬────────────────────────────────┘
                  │
                  ↕ HTTPS
┌──────────────────────────────────────────────────┐
│  Supabase                                        │
│  • PostgreSQL (users, licenses, messages, …)     │
│  • Auth (web kayıt için)                         │
│  • Realtime (PC ↔ Bot mesaj senkronizasyonu)     │
│  • Edge Functions (Telegram webhook, ödeme cb)    │
│  • Storage (.exe binary — opsiyonel)              │
└──┬───────────────────────────────────┬───────────┘
   ↕                                   ↕
┌──────────────────────┐    ┌──────────────────────────┐
│ PC Servisi (Python)  │    │ Telegram Bot (aiogram 3) │
│ • EasyOCR + mss      │    │ • PM bildirimi           │
│ • PM regex parser    │    │ • Hazır cevap butonları  │
│ • Pano API           │    │ • Komutlar (/start, vs.) │
│ • Lisans + heartbeat │    │ • Davetiye kodu akışı    │
│ • Tray UI            │    │ • Polling veya webhook   │
└─────────┬────────────┘    └──────────────┬───────────┘
          ↑                                ↑
   [Knight Online]              [Kullanıcının Telegram'ı]
```

### Veri Akışı — Detay

**A) PM Geliş Akışı (KO → Telegram)**
```
1. PC servisi her ~1.5sn KO chat alanından screenshot alır
2. EasyOCR ile metni okur
3. Regex: r'\[PM\]\[(.+?)\]:\s*(.+)' ile PM yakalar
4. content_hash ile duplicate filter (son N mesaj cache)
5. Yeni PM → Supabase.messages INSERT (direction=incoming)
6. Supabase Realtime → Bot webhook tetiklenir
7. Bot → Telegram'a inline keyboard'lı mesaj gönderir
8. Kullanıcı telefonda bildirim alır
```

**B) Cevap Akışı (Telegram → KO)**
```
1. Kullanıcı bot'ta cevap yazar (custom text VEYA hazır cevap butonu)
2. Bot → Supabase.messages INSERT (direction=outgoing, target=karakter)
3. Supabase Realtime → PC servisi dinler
4. PC servisi cevap metnini Windows panosuna kopyalar
5. Tray notification: "KaraNinja için cevap hazır, KO'ya geçip Ctrl+V"
6. Kullanıcı PC'ye dönünce KO penceresine geçip Ctrl+V → Enter
```

---

## 3. Klasör Yapısı

```
PazarChat/
├── README.md                    # Genel tanıtım
├── PAZARCHAT.md                 # Bu dosya
├── BUSINESS.md                  # İş modeli
├── LEGAL.md                     # Yasal çerçeve
├── CLAUDE.md                    # AI context
├── .gitignore
├── .mcp.json                    # Supabase MCP (gitignore'da, PAT içerir)
├── .mcp.json.example            # Template (commit edilir)
│
├── pc-service/                  # Python — KO PC'de çalışır
│   ├── main.py                  # Entrypoint
│   ├── config.py                # .env okuma, settings
│   ├── window_manager.py        # KO penceresini bul
│   ├── ocr_engine.py            # Screenshot + EasyOCR + PM regex
│   ├── supabase_client.py       # DB writes + realtime listen
│   ├── clipboard_handler.py     # Cevabı panoya kopyala
│   ├── license_manager.py       # API key + machine fingerprint
│   ├── tray_app.py              # System tray UI
│   ├── requirements.txt
│   ├── .env.example
│   └── assets/icon.ico
│
├── telegram-bot/                # Python aiogram 3.x — Cloud/VPS'te
│   ├── main.py                  # Entrypoint
│   ├── config.py
│   ├── handlers/
│   │   ├── start.py             # /start, /davetiye
│   │   ├── messages.py          # PM bildirim + cevap akışı
│   │   ├── commands.py          # /durum, /pazardayim, /destek
│   │   └── payments.py          # /satinAl (faz 3)
│   ├── services/
│   │   ├── supabase_client.py
│   │   ├── license_service.py
│   │   └── ready_replies.py
│   ├── states/                  # FSM (konuşma state)
│   ├── requirements.txt
│   └── .env.example
│
├── web/                         # Next.js App Router + Tailwind
│   ├── app/
│   │   ├── page.tsx             # Landing
│   │   ├── pricing/page.tsx     # Paketler (TBD)
│   │   ├── kvkk/page.tsx        # Aydınlatma metni
│   │   ├── kullanim-kosullari/page.tsx
│   │   ├── mesafeli-satis/page.tsx
│   │   ├── indir/page.tsx       # .exe indirme
│   │   ├── odeme/page.tsx       # iyzico/Shopier
│   │   └── admin/               # (faz 4+) — Supabase Auth ile korumalı
│   ├── components/
│   ├── lib/
│   │   └── supabase.ts
│   ├── public/
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   └── .env.example
│
└── supabase/
    ├── migrations/              # SQL şema (sıralı)
    │   └── 001_initial.sql
    └── functions/               # Deno Edge Functions
        ├── telegram-webhook/    # Telegram update'lerini handle eder
        └── payment-callback/    # iyzico/Shopier callback
```

---

## 4. Veritabanı Şeması (Taslak)

> Henüz uygulanmadı. MCP düzeldikten sonra `001_initial.sql` olarak yazılıp Supabase'e uygulanacak.

### Tablolar (taslak)

```sql
-- 1. Kullanıcı profili (Supabase Auth + Telegram entegrasyonu)
users
  id uuid PK (auth.users referansı)
  telegram_chat_id bigint UNIQUE NOT NULL   -- Telegram'da benzersiz
  telegram_username text                     -- @username (opsiyonel, değişebilir)
  display_name text
  created_at timestamptz
  status text ('active', 'suspended', 'banned')

-- 2. Davetiye kodları (beta süresince)
invite_codes
  id uuid PK
  code text UNIQUE NOT NULL                  -- örn: "BETA-XYZ123"
  created_by uuid (admin)
  used_by uuid (users.id) NULL               -- null = kullanılmamış
  used_at timestamptz
  expires_at timestamptz
  notes text

-- 3. Abonelikler
subscriptions
  id uuid PK
  user_id uuid → users
  plan text ('beta', 'monthly', 'quarterly', 'yearly')   -- beta = ücretsiz
  status text ('active', 'expired', 'cancelled')
  valid_from timestamptz
  valid_until timestamptz
  source text ('invite', 'payment', 'admin')             -- nereden geldi
  created_at timestamptz

-- 4. Lisanslar (PC servisi auth'u için)
licenses
  id uuid PK
  user_id uuid → users
  api_key text UNIQUE NOT NULL              -- "pzc_xxxx" formatı
  machine_fingerprint text                   -- CPU+disk+MAC hash; ilk login'de kaydedilir
  character_name text                        -- KO karakter adı
  server_name text
  last_heartbeat timestamptz
  is_active boolean
  created_at timestamptz
  revoked_at timestamptz NULL

-- 5. Yakalanan PM'ler ve cevaplar
messages
  id uuid PK
  user_id uuid → users
  license_id uuid → licenses
  from_character text
  to_character text
  content text
  direction text ('incoming', 'outgoing')
  content_hash text                          -- duplicate filter
  status text ('new', 'notified', 'replied', 'sent_to_pc', 'completed')
  telegram_message_id bigint NULL            -- bot'un gönderdiği mesaj ID
  replied_at timestamptz NULL
  created_at timestamptz

-- 6. Hazır cevaplar (kullanıcı bazlı, kullanıcı kendi cevaplarını oluşturur)
ready_replies
  id uuid PK
  user_id uuid → users
  label text                                 -- "100m son fiyat"
  content text
  sort_order int
  created_at timestamptz

-- 7. Ödemeler (faz 3+)
payments
  id uuid PK
  user_id uuid → users
  amount_try numeric
  gateway text ('iyzico', 'shopier', 'manual')
  gateway_ref text
  status text ('pending', 'success', 'failed', 'refunded')
  created_at timestamptz

-- 8. Denetim kaydı (KVKK ve müşteri destek için)
audit_log
  id uuid PK
  user_id uuid → users NULL
  action text                                 -- 'login', 'license_activated', 'message_replied', ...
  metadata jsonb
  ip text NULL
  created_at timestamptz
```

### RLS Politikaları
- Her tablo `enable row level security`.
- `user_id = auth.uid()` filtresi standart.
- `licenses` ve `messages` PC servisi için ayrıca **service_role** anahtarı kullanır (RLS bypass).
- Admin paneli için ayrı `admin_users` rolü (faz 4+).

### Realtime Publication
- `messages` (INSERT, UPDATE) — Bot ve PC servisi dinler.
- `licenses` (UPDATE) — PC servisi lisans revoke olunca duysun.

---

## 5. Modül Sorumlulukları

### PC Servisi
| Modül | Sorumluluk |
|-------|-----------|
| `window_manager.py` | KO penceresini başlığına göre bul, crop bölgesini hesapla |
| `ocr_engine.py` | Screenshot al, EasyOCR ile metni oku, PM regex'i uygula, duplicate filtrele |
| `supabase_client.py` | DB INSERT, Realtime subscribe (outgoing mesajlar) |
| `clipboard_handler.py` | Outgoing mesajı `pyperclip` ile panoya yaz |
| `license_manager.py` | API key validation, machine fingerprint hesaplama, heartbeat |
| `tray_app.py` | `pystray` ile sistem tepsisi UI (online/offline, durum, son log) |
| `main.py` | Tüm servisleri thread'lerde başlat, lifecycle yönet |

### Telegram Bot
| Modül | Sorumluluk |
|-------|-----------|
| `handlers/start.py` | `/start` ile kayıt, `/davetiye CODE` ile beta aktivasyon |
| `handlers/messages.py` | Yeni PM gelince Telegram'a kart gönder, reply / button cevaplarını yakala |
| `handlers/commands.py` | `/durum`, `/pazardayim`, `/destek`, `/cevaplar` (hazır cevapları yönet) |
| `services/license_service.py` | Davetiye kodu doğrula, lisans oluştur, API key üret |
| `services/supabase_client.py` | Realtime subscribe (yeni incoming PM'leri yakala), DB writes |
| `states/` | FSM — "kullanıcı şu an X'e cevap yazıyor" gibi state |

### Web
| Sayfa | İçerik |
|-------|--------|
| `/` | Landing — değer önermesi, demo video, CTA |
| `/pricing` | Paketler (faz 3'te aktif edilir, şimdilik "Beta'ya katıl") |
| `/indir` | .exe indirme + kurulum kılavuzu |
| `/kvkk`, `/kullanim-kosullari`, `/mesafeli-satis` | Yasal sayfalar |
| `/odeme/[plan]` | iyzico/Shopier ile ödeme (faz 3) |
| `/hesabim` | Kullanıcı kendi lisansını/aboneliğini görür |
| `/admin` | Sen kullanıcıları yönetirsin (faz 4) |

---

## 6. Önemli Teknik Kararlar

| Karar | Seçim | Neden |
|-------|-------|-------|
| Mobil app yerine Telegram bot | Telegram | App Store derdi yok, push bedava, geliştirme 5x hızlı |
| Bot framework | aiogram 3.x | Async, modern, type hints, FSM desteği |
| Web framework | Next.js App Router + Tailwind | Vercel'de bedava, ödeme entegrasyonu kolay |
| OCR | EasyOCR | Türkçe destekli, Tesseract'tan daha doğru |
| Cevap mekanizması | Pano (clipboard) | Auto-keyboard = bot kategorisinde sayılır, bu daha güvenli |
| Lisans modeli | 1 lisans = 1 PC | Machine fingerprint ile bağla, şifre paylaşımını engelle |
| Beta lisans dağıtımı | Davetiye kodu (`/davetiye CODE`) | Kontrollü ve sayılabilir |
| Bot adı | `@KO_PazarChat` | Knight Online vurgulu, arama için net |
| Veri katmanı | Supabase | Auth + DB + Realtime + Edge Functions tek pakette |
| MCP entegrasyon | Supabase MCP (`--project-ref` ile scope) | Migration ve SQL'i ben uygulayabileyim |

---

## 7. Roadmap

> Faz tahminleri tahmini, beta geri bildirimine göre değişir.

### Faz 0 — Mimari & Doküman (🟢 Tamamlanıyor)
- [x] Telegram bot kararı
- [x] Tech stack kararları (Next.js, aiogram, Supabase)
- [x] Klasör yapısı
- [x] Doküman seti
- [ ] MCP bağlantısı (yeniden, PAT revoke sonrası)
- [ ] Yeni Supabase şeması

### Faz 1 — Çekirdek MVP (1 hafta)
- [ ] Supabase migration uygula
- [ ] PC servisi: window_manager + ocr_engine + supabase_client
- [ ] Telegram bot iskelet: `/start`, PM bildirim, reply yakalama
- [ ] Tek kullanıcı (kendin) çalışan flow
- [ ] Hazır cevap butonları (sabit 3-5 cevap)
- [ ] Pano cevap akışı

### Faz 2 — Multi-Tenant + Lisans (1 hafta)
- [ ] Davetiye kodu sistemi
- [ ] API key + machine fingerprint
- [ ] PC servisi lisans validation (heartbeat)
- [ ] Bot'ta `/durum` komutu
- [ ] Pinned özet mesaj (bekleyen müşteri sayısı)
- [ ] Kullanıcı-bazlı hazır cevap yönetimi (`/cevaplar`)

### Faz 3 — Web + Ödeme (1.5 hafta)
- [ ] Next.js landing page
- [ ] Yasal sayfalar (KVKK, TOS, MSS)
- [ ] iyzico veya Shopier entegrasyonu
- [ ] `/odeme/[plan]` akışı + Edge Function callback
- [ ] PC .exe için PyInstaller paketleme + indir sayfası

### Faz 4 — Beta Test (1 hafta)
- [ ] 2-3 tanıdığın KO tüccarına davetiye kodu
- [ ] Crash report toplama (Sentry veya basit log)
- [ ] Geri bildirim iterasyonu
- [ ] Yasal süreçler tamamlama paralel (avukat, şirket)

### Faz 5 — Public Launch (1 hafta)
- [ ] Fiyatlandırma kesinleşir
- [ ] Forum/Discord/Telegram grubu duyuruları (dikkatli pozisyon)
- [ ] Admin paneli (kullanıcı yönetimi, refund, vs.)
- [ ] Müşteri destek kanalı

**Toplam:** ~5-6 hafta MVP'den public launch'a.

---

## 8. Açık Sorular / Sonraki Kararlar

- **Ödeme yöntemi:** iyzico (şirket gerek) vs. Shopier (şahıs OK) — şirket durumu netleşince.
- **PC servisi dağıtım:** PyInstaller .exe + Inno Setup installer mı, basit zip mi?
- **Auto-update mekanizması:** Faz 5 öncesinde gerekli. Versiyon Supabase'de tutulur, PC servisi kontrol eder.
- **Hosting (Telegram bot):** Vercel serverless mi (cron + webhook), küçük VPS (Hetzner/DigitalOcean ~$5/ay) mi?
- **Bot polling vs webhook:** Beta'da polling (basit), production'da webhook (Edge Function).
- **Çoklu karakter desteği:** 1 lisans = 1 PC ama kullanıcının PC'sinde aynı anda 2 KO penceresi olabilir mi? (multi-client KO'da yaygın)

---

## 9. Referans Linkler

- Knight Online PM pattern örneği: `[PM][KarakterAdı]: mesaj içeriği`
- Regex: `r'\[PM\]\[(.+?)\]:\s*(.+)'`
- aiogram 3.x dokümantasyon: https://docs.aiogram.dev/
- EasyOCR Türkçe model: `easyocr.Reader(['tr', 'en'])`
- Supabase Realtime: https://supabase.com/docs/guides/realtime

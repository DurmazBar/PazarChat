# Claude Code — PazarChat Context

Bu dosya Claude Code (AI asistan) için projeye özgü çalışma kurallarını tanımlar. Yeni bir conversation başlattığında Claude bunu otomatik okur.

---

## Proje Özeti

**PazarChat:** Knight Online tüccar oyuncularının pazar kurarken telefondan PM cevaplayabilmesi için bir SaaS aracı.

- **Mimari:** PC Servisi (Python OCR) + Telegram Bot (aiogram) + Supabase + Web (Next.js)
- **Hedef kitle:** KO tüccar oyuncuları (Türkiye)
- **İş modeli:** Aylık abonelik (fiyatlandırma beta sonrası belirlenecek)
- **Detaylı mimari:** [PAZARCHAT.md](PAZARCHAT.md)
- **İş modeli:** [BUSINESS.md](BUSINESS.md)
- **Yasal çerçeve:** [LEGAL.md](LEGAL.md)

---

## Mutlak Kurallar

### 🚨 1. Supabase Organizasyon İzolasyonu
Kullanıcının iki ayrı Supabase organizasyonu var:
- **PazarChat** — bu proje, üzerinde çalış
- **checkindate** — ayrı bir ürün, **ASLA DOKUNMA**

`mcp__supabase__*` veya `mcp__claude_ai_Supabase__*` tool'unu çağırmadan önce bağlı olduğun project_ref'i doğrula. PazarChat dışında bir projeye işaret eden MCP'ye yazma operasyonu yapma. checkindate proje ID'leri: `luagklcbsccsbsecmukj` (dev), `ikzxbghzgwrvcpkdqvat` (prod) — bunlar **read bile etmemeli**, write ise tamamen yasak.

### 🚨 2. PAT (Personal Access Token) Güvenliği
- `.mcp.json` dosyası gerçek PAT içerir, `.gitignore`'da olmalı.
- Transcript'e PAT yazma; kullanıcıya da "PAT'ı yazma" diye uyar.
- Dosyada gördüğün PAT'ı transcript'e döktüğünde kullanıcıya hemen revoke etmesi gerektiğini söyle.

### 🚨 3. Türkçe İletişim
Kullanıcı Türkçe konuşuyor. Cevaplar Türkçe olsun. Teknik terimler İngilizce kalabilir (`webhook`, `migration`, `realtime` gibi). Dosya içindekiler (kod yorumları, doküman başlıkları) Türkçe ağırlıklı.

### 🚨 4. Knight Online TOS Hassasiyeti
- Asla "bot", "macro", "AFK farm", "automation" gibi pazarlama dili kullanma.
- "Convenience tool", "bildirim aracı", "pazar asistanı" gibi defansif pozisyon.
- Otomatik cevap özelliği ekleme (kullanıcı her zaman tetikleyici olmalı).
- Detay: [LEGAL.md](LEGAL.md)

---

## Tech Stack

| Katman | Teknoloji |
|--------|-----------|
| PC servisi | Python 3.11, EasyOCR, mss, pywin32, pystray, pyperclip, supabase-py |
| Telegram bot | Python 3.11, **aiogram 3.x** (async), supabase-py |
| Web | **Next.js** App Router + **Tailwind** + Vercel |
| Backend | **Supabase** (PostgreSQL + Auth + Realtime + Edge Functions) |
| Ödeme | iyzico veya Shopier — TBD (faz 3) |

---

## Çalışma Tarzı

### Adım Adım Açıkla
Kullanıcı başlangıç seviyesinde olabilir. Yeni bir dosya yazmadan önce **kısaca ne yaptığını anlat**, kritik noktalara yorum satırı ekle. Ama yorum satırlarını "what" değil **"why"** üzerine yaz.

### Yıkıcı Aksiyon = Önce Sor
- `rm -rf`, `git reset --hard`, DROP TABLE, migration revert → her zaman teyit iste.
- Kullanıcı bir kez onayladıysa o action için tamam, ama farklı bir destructive action için yeniden sor.

### Soruları Toplu Sor
Birden çok karar bekleniyorsa `AskUserQuestion` ile 2-4 soruyu tek seferde topla. Tek tek sorma — kullanıcıyı yorar.

### Plan vs Yapma
"Ne yapalım", "nasıl ilerleyelim" gibi keşif soruları → plan sun, yapma. "Şunu yap", "yaz", "ekle" → direkt yap.

---

## Klasör Yapısı

```
PazarChat/
├── pc-service/       # Python — OCR + clipboard + lisans
├── telegram-bot/     # Python aiogram 3.x
├── web/              # Next.js
├── supabase/
│   ├── migrations/
│   └── functions/
├── README.md
├── PAZARCHAT.md      # Ana teknik doküman
├── BUSINESS.md
├── LEGAL.md
└── CLAUDE.md         # Bu dosya
```

---

## Şu An Nerede

**Faz 0 — Mimari & Doküman.** Henüz hiç kod yazılmadı. Sırada:
1. MCP bağlantısını PazarChat projesine kur (yeni PAT ile)
2. Supabase şemasını uygula (yeni şema, Telegram + lisans + davetiye)
3. PC servisi iskeleti
4. Telegram bot iskeleti

Detay: [PAZARCHAT.md → Roadmap](PAZARCHAT.md#7-roadmap)

---

## Memory Sistemi

Bu projeye özel memory dizini: `/Users/makon/.claude/projects/-Users-makon-Documents-PazarChat/memory/`

Mevcut memory'ler:
- `feedback_supabase_orgs.md` — checkindate izolasyonu kuralı

Yeni öğrendiğin yapısal kararlar veya kullanıcı tercihleri için memory ekle (ephemeral task state için değil).

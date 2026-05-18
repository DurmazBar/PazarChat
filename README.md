# PazarChat

Knight Online tüccar oyuncularının pazar kurarken bilgisayar başından ayrılabilmesi için bir uzaktan PM yönetim sistemi. PC'de yakalanan PM'ler Telegram'a anlık bildirim olarak gelir, kullanıcı telefondan cevap yazar, cevap PC'nin panosuna kopyalanır.

## Hızlı Bakış

- **Hedef kitle:** Knight Online'da pazar kuran tüccar oyuncular (Türkiye)
- **Çözdüğü problem:** AFK pazarcılıkta bilgisayar başından ayrılınca müşteri kaçırma
- **Çekirdek deneyim:** PM gelir → Telegram'da bildirim → telefondan cevap → PC'de Ctrl+V
- **İş modeli:** Aylık abonelik (fiyatlandırma beta sonrası belirlenecek)
- **Lisans:** 1 lisans = 1 PC (machine fingerprint ile kontrol)

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

## Klasör Yapısı

```
PazarChat/
├── pc-service/      # Python — OCR + clipboard + lisans
├── telegram-bot/    # Python aiogram 3.x — PM bildirim + cevap akışı
├── web/             # Next.js — landing + ödeme + yasal sayfalar
└── supabase/
    ├── migrations/  # SQL şema
    └── functions/   # Edge Functions
```

## Dökümanlar

| Dosya | İçerik |
|-------|--------|
| [PAZARCHAT.md](PAZARCHAT.md) | Mimari, veri akışı, şema, modüller, roadmap |
| [BUSINESS.md](BUSINESS.md) | Pazar, hedef kitle, fiyatlandırma, beta stratejisi |
| [LEGAL.md](LEGAL.md) | KVKK, Knight Online TOS riski, şirket gereklilikleri |
| [CLAUDE.md](CLAUDE.md) | AI (Claude Code) context ve çalışma kuralları |

## Durum

🟡 **Faz 0:** Mimari kararlar ve doküman aşaması (şu an)

Sonraki fazlar için bkz: [PAZARCHAT.md → Roadmap](PAZARCHAT.md#roadmap)

# PazarChat — İş Modeli

> Bu dosya pazar konumlaması, hedef kitle, fiyatlandırma stratejisi ve beta yönetimini tanımlar. Teknik mimari için → [PAZARCHAT.md](PAZARCHAT.md), yasal süreç için → [LEGAL.md](LEGAL.md).

---

## 1. Değer Önermesi

> **"AFK pazarcılıkta müşteri kaçırmayı bitir. Pazar kurarken hayatına devam et."**

PazarChat, Knight Online'da pazar kuran tüccar oyuncuların bilgisayar başından ayrılma vaktini değerli zamana çeviren bir bildirim ve cevap köprüsü. Yemek yerken, dışarıdayken, banyoda — gelen PM'i telefondan gör, cevabı yaz, eve gelince Ctrl+V ile gönder.

### Konumlama — Kasıtlı Defansif Dil
- ❌ "Macro", "bot", "AFK farm", "automation tool"
- ✅ "Pazar asistanı", "bildirim aracı", "convenience tool"

**Neden:** Knight Online'ın TOS'unda otomasyon yasak. PazarChat otomasyon değil — sadece "uzaktan bildirim + clipboard yardımcısı". Detay: [LEGAL.md](LEGAL.md).

---

## 2. Hedef Kitle

### Birincil Persona — "AFK Tüccar"
- Knight Online'da pazar kuran, item alıp satan oyuncu
- Genelde Moradon / Ronark Land'de saatlerce pazar açar
- Ailesi, işi, okulu var — sürekli bilgisayar başında olamaz
- Bilgisayarın başında olmadığında müşteri kaçırma riskini biliyor
- Aylık 50-100 TL'ye değer biçer (tek trade ile geri kazanır)

### Sayısal Tahmin (Türkiye)
| Metrik | Tahmin |
|--------|--------|
| KO Türkiye aktif oyuncu | 5.000-15.000 |
| Pazar kuran tüccar (%10-15) | 500-2.000 |
| PazarChat'e abone olma niyeti olan (%10-20) | 50-400 |
| **Gerçekçi hedef (6 ay)** | **30-80 ödeyen kullanıcı** |

> Bu niş bir ürün, yan gelir hedefi. Tam zamanlı iş için yeterli ölçek vermeyecek.

### İkincil Persona — "Multi-Client KO Oynayan"
- 2 PC'de aynı anda farklı karakter oynar (genelde 2. char pazar açar)
- Şu an: 2 PC'yi sürekli kontrol etmek zor
- PazarChat: 2 lisans alır (her PC için 1), her ikisinden Telegram bildirimi → konsolide takip

---

## 3. Fiyatlandırma

> **Karar:** Beta süresince ücretsiz. Public launch'ta fiyatlandırma kesinleştirilecek.

### Öneri (Henüz Karar Verilmedi)

| Paket | Süre | Fiyat | İndirim |
|-------|------|-------|---------|
| Aylık | 1 ay | ~49 TL | — |
| 3 Aylık | 3 ay | ~119 TL | ~%20 |
| Yıllık | 12 ay | ~399 TL | ~%30 |

**Lifetime YOK** — gelir akışını öldürür, sürdürülebilir değil.

### Cayma Hakkı
Türkiye Tüketici Hukuku gereği **7 gün cayma hakkı** zorunlu. Bu sürede iade verilir. (Detay: [LEGAL.md](LEGAL.md))

### Deneme / Free Trial — TBD
Olası modeller:
- 3 gün ücretsiz deneme (kart girmeden, davetiye koduna benzer mekanizma)
- 7 gün cayma hakkını öne çekme (öde, beğenmezsen iade)
- İlk 50 müşteriye %50 indirim (early adopter discount)

---

## 4. Lisans Modeli

**1 Lisans = 1 PC** (kullanıcının kararı)

### Teknik Detaylar
- Her satın alma → benzersiz **API key** üretilir (`pzc_xxxxxxxxxx`)
- PC servisi ilk başlangıçta key'i girer + makineye bağlanır (machine fingerprint: CPU + disk + MAC hash)
- Aynı key başka makineden gelirse → eskisi kick edilir + kullanıcıya uyarı
- 3 farklı makinede deneme → hesap suspend (anti-paylaşım)

### Heartbeat
- PC servisi her dakika Supabase'e `last_heartbeat` günceller
- Bot'ta `/durum` komutu: *"PC bağlı ✅, son aktivite 30 saniye önce"*
- Lisans süresi dolunca servis kendini durdurur

### Multi-Client Use Case
KO multi-client oynayan kullanıcılar 2 PC'de aynı anda pazar açabilir. Çözüm: 2 ayrı lisans satın alır, her PC için 1. (Karakter adı `licenses.character_name`'de ayrı saklanır.)

---

## 5. Beta Stratejisi

### Hedef
2-3 tanıdığın KO tüccarına bedava erişim → gerçek senaryoda test → geri bildirim.

### Davetiye Sistemi
Bot komutu: `/davetiye BETA-XYZ123`

```
1. Sen adminden davetiye kodu üretirsin (DB'ye INSERT)
2. Beta testçiye kodu verirsin (Telegram, Discord, vs.)
3. Testçi @KO_PazarChat bot'una /start yazar
4. Sonra /davetiye BETA-XYZ123 yazar
5. Bot kodu doğrular → "beta" planında subscription oluşturur (örn. 30 gün)
6. Testçiye API key gönderilir → PC servisini indirir, key'i girer
```

### Beta Süresi
- Önerilen: **2 hafta** (yeterli test, çok uzatma)
- Beta sonunda testçilere indirimli üyelik teklif et (örn. 6 ay %50)

### Beta'da Toplanacak Veriler
- Kaç PM yakalandı / cevaplandı
- En sık hata türleri (OCR, bot crash, vs.)
- Hangi hazır cevaplar en çok kullanılıyor
- UX şikayetleri (qualitative)
- Sistem stabilitesi (uptime, memory leak)

---

## 6. Ödeme Yöntemi — TBD

> **Karar faz 3'te.** Şirket durumu netleştikten sonra.

### Karşılaştırma

| Yöntem | Komisyon | Kurulum | Türkiye | Şirket Gerek |
|--------|----------|---------|---------|--------------|
| **Telegram Stars** | %30 (yüksek) | ⭐ Kolay | ❌ TL değil | Hayır |
| **Shopier** | %4-5 | ⭐ Kolay | ✅ | Şahıs OK |
| **iyzico** | ~%2.5 + 0.25₺ | 🟡 Orta | ✅ | Şahıs/LTD |
| **Manuel** (havale/Papara) | %0 | ⭐ Sıfır | ✅ | Yok ama fatura sorunu |
| **Stripe** | %2.9 + $0.30 | ❌ Zor (Atlas) | 🟡 | LTD lazım |

### Önerim
- **Beta (faz 1-2):** Davetiye kodu, ücretsiz
- **İlk 20 müşteri:** Manuel (banka transferi + Papara) → bot'ta IBAN gösterir, sen manuel onaylarsın
- **20+ müşteri:** Shopier veya iyzico (şirket durumuna göre)

---

## 7. Pazarlama / Kullanıcı Edinme

### Kanallar
| Kanal | Maliyet | Etki | Risk |
|-------|---------|------|------|
| KO Türkiye forumları | ₺0 | Orta | TOS dikkat |
| KO Discord/Telegram grupları | ₺0 | Yüksek | NTTGames dikkati |
| Ağızdan ağıza (beta testçi) | ₺0 | En yüksek | Düşük |
| Google Ads (Knight Online keyword) | ₺₺ | Orta | TOS dikkat |
| YouTube içerik (KO oyun videoları) | ₺₺ | Düşük | Düşük |

### Pazarlama Disiplini (LEGAL.md ile bağlantılı)
- "AFK macro" gibi kelimeleri **kullanma** — KO TOS keyword taramasına yakalanma riski
- "Pazar asistanı", "AFK trade yardımcısı" gibi defansif dil
- Forum/Discord'da agresif spam **yapma** — organik ağızdan ağıza daha güvenli
- Beta testçilere "tavsiye etme" özelliği ver (referral discount)

---

## 8. Gelir Projeksiyonu (Tahmin)

> Çok değişkenli. Sadece zihinsel egzersiz.

### Senaryo: 6 ay sonra
- 50 ödeyen kullanıcı
- Ortalama paket: 3 aylık (~39 TL/ay)
- **Aylık gelir:** ~2.000 TL
- **Maliyet:** Supabase free tier + Vercel free tier + VPS (~$5) + alan adı = ~150 TL/ay
- **Net:** ~1.800 TL/ay

### Senaryo: 12 ay sonra
- 100 ödeyen kullanıcı
- **Aylık gelir:** ~4.000-5.000 TL
- **Maliyet:** Supabase Pro ($25), VPS, ödeme komisyonu = ~600 TL
- **Net:** ~3.500-4.500 TL/ay

**Bu yan gelir. Tam zamanlı iş için değil.**

---

## 9. Müşteri Destek

### Kanal
- Telegram'da `/destek` komutu → bot konuşmayı sana forward eder
- (Faz 5'te) `pazarchat.com/destek` form
- (İleride) Telegram grup: "PazarChat Kullanıcıları"

### SLA
- Mesai saatleri içinde (09:00-23:00) **3 saat içinde** cevap
- Mesai dışı: ertesi gün
- (Tek başına yöneteceğin için bu makul başlangıç)

### FAQ — Yazılması Gerekenler
- Kurulum kılavuzu (Windows + KO windowed mode)
- "PM yakalanmıyor" troubleshooting
- "Pano çalışmıyor" troubleshooting
- "Lisans expired" durumunda ne yapmalı
- "Hesabım banlandı, sorumluluk?"  → LEGAL.md referansı

---

## 10. KPI / Metrikler

### MVP (Faz 1-2)
- Yakalanan PM sayısı / gün
- PM → cevap latency (medyan, p95)
- OCR doğruluk oranı (manuel test)
- PC servisi uptime

### Beta (Faz 4)
- Davetiye kullanım oranı
- Beta testçi başına günlük aktif kullanım
- Yığılan bug ve UX feedback'i

### Production (Faz 5+)
- **MRR** (Monthly Recurring Revenue)
- **Churn rate** (aylık iptal oranı)
- **CAC** (Customer Acquisition Cost) — ücretli pazarlama varsa
- **DAU/MAU** (Daily/Monthly Active Users)
- **NPS** (Net Promoter Score) — aylık anket

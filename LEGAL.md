# PazarChat — Yasal Çerçeve

> **Uyarı:** Bu dosya **yasal danışmanlık değildir**. Avukatla görüşmeden production'a çıkma. Türkiye'de oyun teknolojisi / yazılım odaklı avukatlar bu konuda uzman. Beta sonrası faz 3'ten önce avukat görüşmesi şart.

---

## 1. Risk Haritası

| Risk | Olasılık | Etki | Önlem |
|------|----------|------|-------|
| Knight Online TOS ihlali iddiası (NTTGames) | Orta | Yüksek (cease & desist, kullanıcı banları) | Defansif konumlama + savunma metni |
| Türkiye KVKK ihlali (veri saklama) | Düşük (önlem alınırsa) | Çok yüksek (milyonlarca TL ceza) | VERBİS kayıt + aydınlatma metni |
| Tüketici davaları (iade, hizmet kalitesi) | Orta | Düşük-orta | MSS + cayma hakkı + net iade politikası |
| Vergi/fatura ihlali (kayıt dışı satış) | Orta | Yüksek | Şirket kurulumu + muhasebeci |
| Marka ihlali ("Knight Online" markası) | Düşük | Orta | "KO" değil "Knight Online uyumlu" gibi açıklayıcı dil |

---

## 2. Knight Online TOS Riski (En Kritik)

### Durum
Knight Online Türkiye'de **NTTGames** tarafından işletiliyor. Standart MMO TOS'larında genellikle yasak olan:
- ❌ Otomasyon / bot / macro
- ❌ Memory reading / packet manipulation
- ❌ Üçüncü taraf yazılım kullanımı (yaygın bir madde)

### PazarChat'in Pozisyonu

**Savunulabilir Argümanlar (Pro):**
- ✅ Memory reading değil, OCR (sadece ekrandakini okuyoruz, oyun dosyalarına müdahale yok)
- ✅ Otomatik cevap yok — kullanıcı her cevabı kendisi yazıyor
- ✅ Klavye simülasyonu yok — pano (clipboard) yöntemi, kullanıcı Ctrl+V'yi kendisi basıyor
- ✅ Karakter hareketi / trade kabulü yok
- ✅ Discord ekran paylaşımı + telefondan dikte ile teknik olarak eşdeğer (bu hiçbir oyunda ban sebebi değil)

**Risk Argümanları (Con):**
- ⚠️ "Üçüncü taraf yazılım" maddesi geniş yorumlanabilir
- ⚠️ Ücretli, görünür bir hizmet → NTTGames'in radarına girer
- ⚠️ "Convenience tool" demek hukuki zırh değil, sadece pazarlama dili
- ⚠️ NTTGames isterse keyfi yorumla TOS ihlali sayabilir

### Önlemler

#### Pazarlama Dili Disiplini
| ❌ Kullanma | ✅ Kullan |
|-------------|-----------|
| "Macro", "bot", "automation" | "Bildirim aracı", "pazar asistanı" |
| "AFK farm", "auto-reply" | "Uzaktan PM yönetimi" |
| "Hesabını botla" | "Bilgisayar başında olmadan PM görme" |
| "Knight Online aracı" | "Knight Online uyumlu üçüncü taraf yardımcı uygulama" |

#### Kullanım Şartları'na Eklenecek Madde
> "PazarChat, kullanıcının pazar/ticaret mesajlarına manuel olarak cevap yazmasını kolaylaştıran bir bildirim ve pano (clipboard) yardımcı aracıdır. Otomatik PM yanıtlama, otomatik trade kabulü, karakter hareketi veya benzer otomasyon özellikleri içermez. Knight Online'ın kullanım koşullarına ve oyun içi kurallara uyum sorumluluğu tamamen kullanıcıya aittir. PazarChat kullanımı sonucunda doğabilecek hesap askıya alma, banlama veya benzeri tedbirlerden PazarChat sorumluluk kabul etmez."

Bu metin tek başına savunma değil ama bir uyuşmazlıkta **niyet beyanı** sağlar.

#### Pasif Tutum
- NTTGames'in Discord/forum'unda agresif pazarlama yapma
- Knight Online resmi sayfalarına link verme / yorumlama
- "NTTGames onaylı" gibi yanıltıcı ifade asla kullanma

---

## 3. KVKK (Kişisel Verilerin Korunması Kanunu)

### Kapsamımız
Saklanan kişisel veriler:
- E-mail (kayıt için, Supabase Auth)
- Telegram chat_id ve username
- IP adresi (audit log)
- Karakter adı (kullanıcının KO karakteri — pseudonim ama bağlantılı veri)
- Yakalanan PM içeriği (üçüncü kişi karakter adı ve mesaj)

**Üçüncü kişi PM içeriği özellikle hassas** — başka oyuncuların mesajlarını saklıyoruz.

### Gereklilikler

#### 3.1. VERBİS Kayıt
- Şirket / şahıs kuruluşu sonrası **VERBİS** (Veri Sorumluları Sicili) kaydı zorunlu
- https://verbis.kvkk.gov.tr/
- Ücretsiz, online başvuru
- Kayıt olmadan kişisel veri işlenmesi yasak (büyük ceza riski)

#### 3.2. Aydınlatma Metni
Web sitesinde `/kvkk` sayfasında yayınlanır. İçeriği:
- Veri sorumlusu kim (şirket bilgileri)
- Hangi veriler toplanıyor
- Hangi amaçla işleniyor (hizmet sunma, müşteri destek)
- Kimlere aktarılıyor (Supabase = AB içi sunucular, Telegram = Telegram LLC)
- Saklama süresi (hesap silinene kadar + yasal saklama süreleri)
- Veri sahibi hakları (silme, düzeltme, erişim)
- İletişim kanalı

#### 3.3. Açık Rıza
- Kayıt formunda checkbox: *"KVKK Aydınlatma Metnini okudum ve onaylıyorum"*
- Üçüncü kişi (PM gönderen başka oyuncu) verisi için → "Meşru menfaat" gerekçesi kullanılabilir ama tartışmalı, avukatla netleştir

#### 3.4. Veri Saklama Süresi
- Mesaj geçmişi: 30 gün sonra otomatik silme (cron job veya pg_cron)
- Hesap silindiğinde: tüm veriler 24 saat içinde silinir (audit_log hariç — yasal saklama)
- Audit log: 5 yıl (yasal zorunluluk)

#### 3.5. Veri Sahibi Hakları
Kullanıcı talep ederse:
- Verilerini görme (`/hesabim` sayfası + email export)
- Düzeltme (`/hesabim` üzerinden)
- Silme (`/hesabim` → "Hesabımı sil" + onay maili)
- Aktarma (machine-readable JSON export)

Yanıt süresi: **30 gün** (yasal).

#### 3.6. Veri İhlali Bildirimi
KVKK'ya **72 saat** içinde, etkilenen kullanıcılara **mümkün olan en kısa sürede** bildirim.

---

## 4. Tüketici Hukuku (Mesafeli Satış)

### Zorunlu Belgeler
1. **Mesafeli Satış Sözleşmesi** (MSS) — ödeme öncesi gösterilir, kullanıcı onaylar
2. **Cayma hakkı** — 7 gün, bedelsiz iade
3. **Fatura** — her satışta (e-fatura/e-arşiv)
4. **İade ve iptal politikası** — net ve görünür yerde

### Cayma Hakkı İstisnaları
Dijital ürünlerde cayma hakkı şu durumda **kaybolur**:
- Kullanıcı açıkça "hemen ifaya başla, cayma hakkımdan vazgeçiyorum" derse VE
- Hizmet kullanılmaya başlanırsa

PazarChat için: kayıt sonrası "hemen kullanmaya başla" onayı → cayma hakkı kaybolabilir. Ama bu zorlama bir konum, basit yol: **7 gün koşulsuz iade** sunmak. Müşteri memnuniyeti ve davaya gerek bırakmama açısından daha güvenli.

### Yazılması Gereken Metinler
- `/kullanim-kosullari` (Kullanım Şartları)
- `/mesafeli-satis` (Mesafeli Satış Sözleşmesi)
- `/iade-politikasi` (İade ve İptal)
- `/kvkk` (Aydınlatma Metni)

> Bu metinleri **avukatla hazırlat** veya en azından template'i avukatla gözden geçirt. İnternette bulunan jenerik MSS'ler eksik/yanlış olabilir.

---

## 5. Şirket Kurulumu

### Seçenekler

#### A) Şahıs Şirketi (Önerilen — Başlangıç)
- **Maliyet:** ~3.000-4.000 TL kurulum + muhasebeci aylık 1.500-2.500 TL
- **Süre:** ~1 hafta
- **Avantaj:** Hızlı, ucuz, basit
- **Dezavantaj:** Sınırsız sorumluluk (şahsi mal varlığı risk altında)
- **Vergi:** Gelir vergisi (basit usul veya işletme defterli)

#### B) Limited Şirket (LTD) — İleride
- **Maliyet:** ~15.000-25.000 TL kurulum + muhasebeci 2.500-4.000 TL/ay
- **Süre:** ~2-3 hafta
- **Avantaj:** Sınırlı sorumluluk (şahsi mal varlığı korunur)
- **Dezavantaj:** Yüksek maliyet, daha fazla bürokrasi
- **Vergi:** Kurumlar vergisi %25 + KDV

### Önerim
**Şahıs şirketi ile başla** (faz 3'ten önce). Aylık 10.000 TL+ gelire ulaşınca LTD'ye geçiş düşün.

### Vergiler
- **KDV:** %20 (dijital hizmet) — Türkiye'de satılan her abonelikten alınır
- **Stopaj:** Yurt dışı ödemeler için %30 (Supabase, Vercel, OpenAI vs. faturalarında)
- **Gelir/Kurumlar Vergisi:** Yıllık beyanname

### E-Fatura / E-Arşiv
- Tüm satışlarda fatura zorunlu
- GİB e-arşiv portali üzerinden veya muhasebe yazılımı (Logo, Mikro, Paraşüt vs.)
- Bireysel müşterilere e-arşiv, kurumlara e-fatura

---

## 6. Marka & Fikri Mülkiyet

### "PazarChat" Markası
- **Marka tescili** Türk Patent ve Marka Kurumu'nda
- **Maliyet:** ~3.000-5.000 TL (1 sınıf)
- **Süre:** ~1-1.5 yıl
- **Faz:** Public launch sonrası, paralel başlatılabilir

### "Knight Online" Markası
- NTTGames'in tescilli markası
- **Asla** "Knight Online" markasını ürün adında veya logoyla kullanma
- **Açıklayıcı kullanım** OK: "Knight Online ile uyumlu üçüncü taraf yardımcı uygulama"

### Telif (Code)
- Tüm kod sana ait, GitHub private repo
- Üçüncü parti kütüphaneler (EasyOCR, aiogram, Next.js, vs.) → MIT/Apache lisansları, ticari kullanım serbest
- **README'lerde NOTICE** dosyası ile lisansları listele (compliance)

---

## 7. Sunucu/Hosting Veri İkamesi

### Supabase
- Sunucular Frankfurt (EU) — GDPR + KVKK uyumlu
- **AB ülkesi olduğu için** Türkiye'den yurt dışı veri aktarımı kapsamında değerlendirilir
- Aydınlatma metninde belirt: *"Verileriniz Almanya'da bulunan Supabase Inc. sunucularında işlenir."*

### Vercel
- Sunucular ABD/AB (CDN global)
- ABD veri ikamesi → ek tedbir gerekebilir (Standard Contractual Clauses)

### Telegram
- Sunucular dünya geneline dağıtılmış
- Mesaj içerikleri Telegram'a iletilir → kullanıcı aydınlatması şart

### Önerim
- KVKK aydınlatma metninde **net olarak** hangi servislerin nerede veri tuttuğunu yaz
- Hassas veri (kart bilgisi vs.) PazarChat üzerinden ASLA geçmesin — ödeme gateway (iyzico/Shopier) doğrudan kart alır, sen sadece reference saklarsın

---

## 8. Beta Sırasında Yapılacaklar

### Faz 1-2 (Geliştirme)
- Hiçbir yasal ihtiyaç yok (sadece kendin test ediyorsun)
- Veri toplama → sadece kendi verilerin → KVKK kapsamında değil

### Faz 4 (Beta — Tanıdıkların Test'i)
- Beta testçilere sözlü/yazılı **bilgi ver:** "Bu beta, kişisel verileriniz işleniyor, X tarihinde silinecek"
- Resmi KVKK uyum şart değil (gönüllü test) ama bilgi vermek **etik**
- Bu süreçte basit aydınlatma metni hazırla (avukat tavsiyesi)

### Faz 5 Öncesi (Public Launch)
✅ **Yapılması Gerekenler:**
1. Avukatla görüşme (1-2 saat, ~2.000-4.000 TL)
2. Şahıs şirketi kuruluşu
3. Muhasebeci anlaşması
4. VERBİS kaydı
5. Yasal metinler (MSS, KVKK, Kullanım Şartları, İade Politikası)
6. E-arşiv fatura sistemi
7. Banka hesabı + ödeme entegrasyonu (Shopier/iyzico)

**Önce Knight Online TOS riski hakkında avukatla görüş.** Avukatın değerlendirmesi "bu çok riskli" derse stratejiyi yeniden değerlendirelim.

---

## 9. Acil Durum Senaryoları

### A) NTTGames Cease & Desist Mektubu
1. **Panik yapma.** Çoğu durumda "Sitenizi kapatın" diye sade taleptir.
2. Avukatına ilet → cevap stratejisi oluştur.
3. Müşterilere şeffaf bildirim: *"Hizmet geçici olarak askıya alındı, ödemeler iade edilecek"*
4. İade akışı: tüm aktif abonelerin kalan gün × günlük fiyat = iade.

### B) Müşteri KO Hesabı Banlanırsa
1. PazarChat'in **kullanım koşullarını hatırlat** (sorumluluk kullanıcıda)
2. Hesap silme + iade talep ederse → 7 gün cayma hakkı dışında para iade etme zorunluluğun yok
3. **İyi niyetli yaklaşım:** Kalan günleri iade et (itibar için)

### C) KVKK Şikayeti
1. Şikayet eden veri sahibine 30 gün içinde yanıt ver
2. Talep haklıysa veriyi sil/düzelt
3. Talep haksızsa gerekçeli ret yaz
4. KVKK'nın resmi şikayetine 30 gün içinde detaylı cevap ver

---

## 10. Görevler Listesi (Faz 5 Öncesi)

- [ ] Avukat görüşmesi (oyun teknolojisi uzmanı)
- [ ] Şahıs şirketi kurulumu
- [ ] Muhasebeci anlaşması
- [ ] VERBİS kaydı
- [ ] KVKK aydınlatma metni (avukatla hazırla)
- [ ] Kullanım Şartları (avukatla hazırla)
- [ ] Mesafeli Satış Sözleşmesi (avukatla hazırla)
- [ ] İade Politikası
- [ ] Banka hesabı (ticari)
- [ ] E-arşiv fatura sistemi
- [ ] Ödeme gateway sözleşmesi (Shopier veya iyzico)
- [ ] PazarChat marka tescil başvurusu (paralel)
- [ ] Veri silme cron job (30 gün PM silme + audit log politikası)
- [ ] Veri ihlali bildirim prosedürü
- [ ] FAQ sayfası (yasal sorular dahil)

---

## 11. Referanslar

- KVKK Resmi: https://www.kvkk.gov.tr/
- VERBİS: https://verbis.kvkk.gov.tr/
- Tüketici Hakem Heyeti: https://tuketici.ticaret.gov.tr/
- Mesafeli Sözleşmeler Yönetmeliği: https://www.mevzuat.gov.tr/
- Türk Patent ve Marka Kurumu: https://www.turkpatent.gov.tr/
- Gelir İdaresi Başkanlığı (E-arşiv): https://earsivportal.efatura.gov.tr/

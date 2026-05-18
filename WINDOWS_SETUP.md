# Windows Kurulum Rehberi

Bu rehber **Knight Online oynadığın Windows PC** içindir. Mac'teki kod GitHub'da hazır,
Windows'a indirip OCR + F8 gerçek testini buradan yapacağız.

---

## Ön Koşullar (Windows'ta Yüklü Olmalı)

### 1) Git for Windows
- https://git-scm.com/download/win → indir + kur
- Kurulum sırasında default ayarlar yeterli

### 2) Python 3.12 (önemli: 3.13/3.14 değil)
- https://www.python.org/downloads/release/python-3128/ → Windows installer (64-bit)
- ⚠ Kurulum sırasında **"Add Python to PATH"** kutusunu işaretle

### 3) PowerShell veya Windows Terminal
- Windows 11'de zaten var
- Windows 10'da Microsoft Store'dan Windows Terminal kur (opsiyonel)

---

## Adım 1 — Repo'yu Klonla

PowerShell aç (Başlat menüsü → "PowerShell" yaz). Klonlamak istediğin klasöre git:

```powershell
cd $HOME\Documents
git clone https://github.com/DurmazBar/PazarChat.git
cd PazarChat\pc-service
```

**İlk klonlamada GitHub kimlik doğrulama isteyebilir:**
- HTTPS + Personal Access Token (PAT) → https://github.com/settings/tokens/new?scopes=repo
- Veya GitHub Desktop yüklü ise otomatik halleder

---

## Adım 2 — Python Sanal Ortam + Bağımlılıklar

PowerShell'de PC servisi klasöründe:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

⏱ İlk kurulum **~3-5 dakika** sürer (EasyOCR + PyTorch ~500MB indirir).

### Activation Hatası Alırsan
PowerShell execution policy yüzünden:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Onayla, sonra `Activate.ps1` tekrar dene.

---

## Adım 3 — Lisans Transfer (Mac'ten Windows'a)

Mac'te aldığın `pzc_...` lisans anahtarı **şu an Mac'in machine fingerprint'ine bağlı**.
Windows'tan kullanmak için DB'de fingerprint'i sıfırlamamız gerek (bir kerelik işlem).

**Sen yapacaksın:** Bana yaz "windows için fingerprint sıfırla" — ben Supabase'de
şu SQL'i çalıştırırım:
```sql
UPDATE public.licenses SET machine_fingerprint = NULL WHERE api_key = 'pzc_...';
```

Bundan sonra Windows'ta ilk heartbeat'te yeni fingerprint kaydedilir, lisans
Windows PC'ye bağlanır.

Alternatif: yeni davetiye kodu ile baştan kayıt ol (Mac kaydı kalır, ileride
silinir).

---

## Adım 4 — `.env` Dosyasını Doldur

```powershell
copy .env.example .env
notepad .env
```

Şu alanları doldur (eşittirden hemen sonra, yeni satıra atlama):

```env
SUPABASE_URL=https://wgtgbrufzuzjtqhrojjo.supabase.co
SUPABASE_ANON_KEY=<Supabase Dashboard → Settings → API → anon public>
PAZARCHAT_API_KEY=<Mac'teki ile aynı pzc_... veya yeni davetiye'den>
KO_CHARACTER_NAME=<gerçek KO karakterin>
KO_SERVER_NAME=<örn: Cypher>

# Paste mode (Windows için artık F8 hotkey gerçek anlamlı)
PASTE_MODE=hybrid
HOTKEY_PASTE_KEY=f8
```

Notepad kaydet (Ctrl+S) ve kapat.

---

## Adım 5 — Servisi Başlat

```powershell
python main.py
```

**Beklenen ilk çıktı:**
```
[INFO] PazarChat PC servisi başlatılıyor...
[INFO] Karakter: <senin karakter> (<server>)
[INFO] Paste modu: HYBRID
[INFO] HTTP Request: POST .../pc_heartbeat 200 OK
[INFO] Heartbeat thread başladı (60 saniye aralıkla, fingerprint=...)
[INFO] OCR motoru yükleniyor...
[INFO] EasyOCR hazır (Xs)
[INFO] Global hotkey aktif: f8
[INFO] OCR loop başladı (interval=1.5s)
[INFO] KO penceresi henüz bulunamadı, bekleniyor...
[INFO] Sistem hazır.
```

İlk heartbeat'te (eğer fingerprint NULL'sa) Windows fingerprint kaydedilir.
İkinci heartbeat'ten sonra Mac'ten denenirse `FingerprintMismatchError` alır.

⚠ **Terminal'i kapatma**, servis çalışmaya devam etsin.

---

## Adım 6 — Knight Online'ı Aç

1. KO'yu **windowed mode**'da başlat (full screen değil)
2. Karaktere gir
3. Pazar aç (örn: Moradon'da)

PC servisi terminal'inde şunu görmeli:
```
[INFO] KO penceresi bulundu, OCR aktif.
```

---

## Adım 7 — Test PM Yakalama

Bu test için ikinci bir karaktere ihtiyacın var:
- **Alternatif 1:** Arkadaşına "abi bana bir PM at, /w benim_karakterim merhaba" de
- **Alternatif 2:** İkinci hesap multi-client → kendi kendine PM at

PM gelince:
1. ~2 saniye içinde PC servisi terminal'inde:
   ```
   [INFO] PM yakalandı: [arkadaş_karakteri]: merhaba
   ```
2. Telegram'da @KO_PazarChat_bot'tan kart bildirim gelir
3. Bot'ta hazır cevap butonuna bas (örn. "100m son fiyat")
4. PC servisi terminal'inde:
   ```
   [INFO] Pano güncellendi → arkadaş_karakteri: 100m son fiyat
   ```

---

## Adım 8 — F8 Hotkey Test

1. KO penceresine geç (Alt+Tab veya pencereye tıkla)
2. Chat input'a bir kez tıkla (focus orada olsun)
3. **F8 tuşuna bas**
4. KO'da PM cevap olarak gönderilir: `/w arkadaş_karakteri 100m son fiyat` (Enter'la birlikte)

### F8 Çalışmazsa
- KO penceresinin **aktif** (foreground) olduğundan emin ol — F8 sadece KO aktifken çalışır
- Chat input'a (F2 ile pencere aç) tıklamış olman gerek; aksi takdirde Ctrl+V başka yere gider
- Terminal'de `[WARNING] Hotkey paste reddedildi: ...` mesajını oku

---

## Adım 9 — `auto` Mode'u Test Et (Opsiyonel)

```powershell
notepad .env
```

`PASTE_MODE=hybrid` → `PASTE_MODE=auto` yap, kaydet.

PC servisini Ctrl+C ile durdur, tekrar başlat:
```powershell
python main.py
```

Şu uyarıyı görmen lazım:
```
⚠  OTOMATIK GÖNDERIM MODU AKTIF (PASTE_MODE=auto)
   Knight Online TOS açısından yüksek risk içerir.
   Kullanım sorumluluğu SİZE aittir.
```

Sonra bot'ta hazır cevap basınca **otomatik** olarak KO foreground'a geçer ve
yapıştırır. Test sonrası `hybrid`'e geri dön (önerilen).

---

## Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| `pip install` torch için "Visual C++ 14.0 required" diyor | Microsoft C++ Build Tools indir |
| `python: command not found` | "Add Python to PATH" işaretlenmemiş, Python'u yeniden kur |
| `KO penceresi bulunamadı` | KO **windowed mode** olmalı; başlığında "Knight OnLine Client" yazıyor mu kontrol et |
| `Hotkey paste reddedildi: KO aktif değil` | KO penceresine alt-tab yap, sonra F8 |
| OCR PM yakalamıyor | Chat alanı görünür mü? `OCR_CROP_REGION` ile manuel bölge ayarla |
| `FingerprintMismatchError` | Bu lisans başka makineye bağlı — fingerprint'i sıfırla (Adım 3) |

---

## .exe Paketleme (Yarın, Bu Adımlardan Sonra)

Manuel kurulum çalıştığını doğruladıktan sonra PyInstaller ile `.exe` üretiriz:

```powershell
pip install pyinstaller==6.10.0
pyinstaller --clean --onefile --noconsole --icon=assets\icon.ico --name=PazarChat main.py
```

Çıktı: `dist\PazarChat.exe` (~250-400 MB tek dosya). Sonra Inno Setup ile installer.

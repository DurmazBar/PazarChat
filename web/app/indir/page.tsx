import type { Metadata } from "next";
import Link from "next/link";

const BOT_URL = process.env.NEXT_PUBLIC_BOT_URL || "https://t.me/KO_PazarChat_bot";

export const metadata: Metadata = {
  title: "İndir & Kurulum",
  description:
    "PazarChat PC servisini indirin ve Knight Online ile birlikte kullanmaya başlayın. Adım adım kurulum.",
};

export default function IndirPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="mb-10">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
          İndir & Kurulum
        </h1>
        <p className="mt-3 text-surface-50/60">
          Beta dönemindeyiz — kurulum dosyası henüz hazırlanıyor.
          Bu sırada manuel kurulum adımları aşağıda.
        </p>
      </div>

      {/* İndirme kutusu (placeholder) */}
      <div className="mb-12 rounded-2xl border border-surface-800 bg-surface-900/60 p-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold">PazarChat for Windows</h2>
            <p className="mt-1 text-sm text-surface-50/60">
              Windows 10 / 11 · 64-bit · ~250 MB
            </p>
          </div>
          <button
            disabled
            className="cursor-not-allowed rounded-lg bg-surface-800 px-6 py-3 text-sm font-semibold text-surface-50/40"
          >
            Yakında (.exe)
          </button>
        </div>
        <p className="mt-4 text-xs text-surface-50/40">
          Hazır kurulum dosyası faz 3'te yayınlanacak. Şu an manuel Python
          kurulumu ile çalışıyor.
        </p>
      </div>

      {/* Ön koşullar */}
      <section className="mb-12">
        <h2 className="mb-4 text-xl font-semibold">Ön koşullar</h2>
        <ul className="space-y-2 text-sm text-surface-50/70">
          <li>✓ Windows 10 veya 11 (64-bit)</li>
          <li>✓ Knight Online <strong>windowed mode</strong>'da çalışmalı</li>
          <li>✓ Telegram hesabı + davetiye kodu</li>
          <li>✓ Python 3.12+ (manuel kurulum için)</li>
          <li>✓ İnternet bağlantısı</li>
        </ul>
      </section>

      {/* Adım adım */}
      <section className="space-y-8">
        <h2 className="text-xl font-semibold">Adım adım kurulum (beta)</h2>

        <Step n={1} title="Telegram bot'a katıl">
          <p>
            Önce <a href={BOT_URL} target="_blank" rel="noopener noreferrer"
              className="text-primary-300 underline hover:text-primary-200">
              @KO_PazarChat_bot
            </a>{" "}
            bot'una git, <code>/start</code> yaz.
          </p>
          <p>
            Sonra davetiye kodunla giriş yap:
          </p>
          <pre className="mt-2 rounded-lg bg-surface-950 p-3 text-xs">
            <code>/davetiye BETA-XXXXXX</code>
          </pre>
          <p>
            Bot sana <code>pzc_...</code> formatında bir <strong>lisans anahtarı</strong> verecek. Kopyala, sakla.
          </p>
        </Step>

        <Step n={2} title="Python 3.12 kur (yoksa)">
          <p>
            Python 3.12 yüklü değilse:{" "}
            <a
              href="https://www.python.org/downloads/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-300 underline hover:text-primary-200"
            >
              python.org/downloads
            </a>{" "}
            adresinden Windows installer'ı indir.
          </p>
          <p className="text-xs text-surface-50/50">
            Kurulum sırasında <strong>"Add Python to PATH"</strong> kutusunu işaretle.
          </p>
        </Step>

        <Step n={3} title="PC servisini indir">
          <p>
            GitHub release sayfasından <code>pc-service.zip</code> dosyasını indir
            (link beta testçilerine özel verilecek). Çıkar, klasöre git.
          </p>
        </Step>

        <Step n={4} title="Bağımlılıkları kur">
          <p>Klasör içinde PowerShell aç ve şunu çalıştır:</p>
          <pre className="mt-2 overflow-x-auto rounded-lg bg-surface-950 p-3 text-xs">
            <code>
{`python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt`}
            </code>
          </pre>
          <p className="text-xs text-surface-50/50">
            İlk kurulumda EasyOCR modelleri indirilir (~150 MB), 1-2 dakika sürer.
          </p>
        </Step>

        <Step n={5} title=".env dosyasını oluştur">
          <p>
            Aynı klasörde <code>.env.example</code>'ı kopyala, <code>.env</code> olarak adlandır.
            İçindeki <code>PAZARCHAT_API_KEY=</code> satırına bot'tan aldığın anahtarı yapıştır.
          </p>
          <p>
            <code>KO_CHARACTER_NAME=</code> satırına KO karakter adını yaz.
          </p>
        </Step>

        <Step n={6} title="Servisi başlat">
          <p>PowerShell'de:</p>
          <pre className="mt-2 rounded-lg bg-surface-950 p-3 text-xs">
            <code>python main.py</code>
          </pre>
          <p>
            Tray icon belirir. Knight Online'ı windowed mode'da aç ve pazar kur.
            PM geldiğinde Telegram'a bildirim düşecek.
          </p>
        </Step>

        <Step n={7} title="Cevap modunu seç">
          <p>
            <code>.env</code> dosyasında <code>PASTE_MODE</code> ayarı ile 3
            farklı mod arasından seç. Her birinin yasal ve teknik trade-off'u
            aşağıda.
          </p>
        </Step>
      </section>

      {/* 3 Mod karşılaştırması */}
      <section className="mt-12">
        <h2 className="mb-6 text-xl font-semibold">Cevap Gönderim Modları</h2>
        <div className="grid gap-4 md:grid-cols-3">
          <ModeCard
            title="Manuel"
            envValue="manual"
            risk="ok"
            description="Sadece pano. Sen KO'da Ctrl+V + Enter."
            pros={["En düşük TOS riski", "Tam kullanıcı kontrolü"]}
            cons={["Her cevap için manuel adımlar"]}
            warning={null}
          />
          <ModeCard
            title="Hibrit (F8)"
            envValue="hybrid"
            risk="mid"
            description="Pano + F8 hotkey. KO aktifken F8 basınca otomatik yapıştırma."
            pros={[
              "Tek tuşla cevap",
              "Kullanıcı tetikli (manuel fiziksel basış)",
              "F8 sadece KO aktifken çalışır",
            ]}
            cons={["KO bilgisayar başında olmak şart"]}
            warning={null}
            recommended
          />
          <ModeCard
            title="Otomatik"
            envValue="auto"
            risk="high"
            description="Cevap geldiği anda KO foreground'a alınır + yapıştırılır + Enter."
            pros={[
              "En hızlı UX",
              "Dışarıdayken bile çalışır",
            ]}
            cons={[
              "Knight Online TOS açısından yüksek risk",
              "Banlanma riski mevcuttur",
              "Avukat onayı olmadan kullanılması önerilmez",
            ]}
            warning="Kullanım sorumluluğu tamamen kullanıcıya aittir."
          />
        </div>
        <p className="mt-4 text-xs text-surface-50/40">
          Varsayılan mod: <code>hybrid</code>. Değiştirmek için{" "}
          <code>.env</code> dosyasındaki <code>PASTE_MODE</code> satırını
          güncelle, servisi yeniden başlat.
        </p>
      </section>

      {/* Sorun giderme */}
      <section className="mt-16 rounded-2xl border border-surface-800 bg-surface-900/60 p-6">
        <h2 className="mb-3 text-lg font-semibold">Sorun mu var?</h2>
        <ul className="space-y-2 text-sm text-surface-50/70">
          <li>
            <strong>PM yakalanmıyor:</strong> KO penceresinin windowed mode'da olduğundan emin ol, chat alanının görünür olduğunu kontrol et.
          </li>
          <li>
            <strong>"Lisans hatası" mesajı:</strong> Bot'tan <code>/durum</code> ile abonelik bitiş tarihini kontrol et.
          </li>
          <li>
            <strong>Pano güncellenmiyor:</strong> Başka bir uygulama pano'yu kilitlemiş olabilir.
          </li>
        </ul>
        <p className="mt-4 text-sm text-surface-50/60">
          Daha fazla soru için bot'ta <code>/destek</code> yazabilirsin.
        </p>
      </section>

      <div className="mt-12 flex items-center justify-between text-sm">
        <Link href="/" className="text-surface-50/60 hover:text-surface-50">
          ← Ana sayfa
        </Link>
        <Link href="/kvkk" className="text-surface-50/60 hover:text-surface-50">
          KVKK Aydınlatma →
        </Link>
      </div>
    </div>
  );
}

function Step({
  n,
  title,
  children,
}: {
  n: number;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex gap-4">
      <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-primary-500/15 text-sm font-semibold text-primary-300">
        {n}
      </span>
      <div className="flex-1 space-y-2 text-sm leading-relaxed text-surface-50/80">
        <h3 className="text-base font-semibold text-surface-50">{title}</h3>
        {children}
      </div>
    </div>
  );
}

function ModeCard({
  title,
  envValue,
  risk,
  description,
  pros,
  cons,
  warning,
  recommended,
}: {
  title: string;
  envValue: string;
  risk: "ok" | "mid" | "high";
  description: string;
  pros: string[];
  cons: string[];
  warning: string | null;
  recommended?: boolean;
}) {
  const riskColor =
    risk === "ok"
      ? "border-primary-500/40 bg-primary-500/5"
      : risk === "mid"
      ? "border-accent-400/40 bg-accent-500/5"
      : "border-red-500/40 bg-red-500/5";

  const riskLabel =
    risk === "ok"
      ? { text: "Düşük risk", className: "bg-primary-500/20 text-primary-200" }
      : risk === "mid"
      ? { text: "Orta risk", className: "bg-accent-500/20 text-accent-200" }
      : { text: "Yüksek risk", className: "bg-red-500/20 text-red-200" };

  return (
    <div className={`relative rounded-2xl border p-5 ${riskColor}`}>
      {recommended && (
        <span className="absolute -top-3 left-4 rounded-full bg-primary-500 px-3 py-0.5 text-xs font-semibold text-surface-950">
          Önerilen
        </span>
      )}
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-lg font-semibold">{title}</h3>
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${riskLabel.className}`}>
          {riskLabel.text}
        </span>
      </div>
      <code className="text-xs text-surface-50/40">PASTE_MODE={envValue}</code>
      <p className="mt-3 text-sm text-surface-50/70">{description}</p>

      <div className="mt-4">
        <p className="text-xs font-semibold text-surface-50/60">Artılar</p>
        <ul className="mt-1 space-y-1 text-xs text-surface-50/70">
          {pros.map((p) => (
            <li key={p} className="flex gap-1.5">
              <span className="text-primary-400">+</span>
              <span>{p}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-3">
        <p className="text-xs font-semibold text-surface-50/60">Eksiler</p>
        <ul className="mt-1 space-y-1 text-xs text-surface-50/70">
          {cons.map((c) => (
            <li key={c} className="flex gap-1.5">
              <span className="text-surface-50/40">−</span>
              <span>{c}</span>
            </li>
          ))}
        </ul>
      </div>

      {warning && (
        <div className="mt-4 rounded-md border border-red-500/40 bg-red-500/10 p-2 text-[11px] text-red-200">
          ⚠ {warning}
        </div>
      )}
    </div>
  );
}

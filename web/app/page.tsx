import Link from "next/link";

const BOT_URL = process.env.NEXT_PUBLIC_BOT_URL || "https://t.me/KO_PazarChat_bot";

export default function HomePage() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-grid pointer-events-none" />
        <div className="relative mx-auto max-w-6xl px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary-500/30 bg-primary-500/10 px-3 py-1 text-xs font-medium text-primary-300">
              <span className="h-1.5 w-1.5 rounded-full bg-primary-400" />
              Beta dönemi · Davetiye ile katılım
            </div>

            <h1 className="text-balance text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
              Pazar kurarken{" "}
              <span className="bg-gradient-to-r from-primary-400 to-accent-500 bg-clip-text text-transparent">
                hayatına devam et
              </span>
            </h1>

            <p className="mx-auto mt-6 max-w-2xl text-pretty text-lg text-surface-50/70">
              Knight Online'da AFK pazarcılık yaparken müşterilerinin PM'lerini
              telefonundan gör, hazır cevapla yanıtla. Bilgisayarına döndüğünde
              tek tıkla yapıştır.
            </p>

            <div className="mt-10 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
              <a
                href={BOT_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-lg bg-primary-500 px-6 py-3 text-sm font-semibold text-surface-950 transition hover:bg-primary-400"
              >
                Telegram Bot'unu Aç
              </a>
              <Link
                href="/indir"
                className="rounded-lg border border-surface-800 bg-surface-900 px-6 py-3 text-sm font-semibold text-surface-50 transition hover:bg-surface-800"
              >
                PC Servisini İndir
              </Link>
            </div>

            <p className="mt-4 text-xs text-surface-50/40">
              Beta süresince ücretsiz. Davetiye kodu için iletişime geç.
            </p>
          </div>
        </div>
      </section>

      {/* Nasıl çalışır */}
      <section className="border-y border-surface-800/80 bg-surface-900/40 py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Nasıl çalışır?
            </h2>
            <p className="mt-4 text-surface-50/60">
              Üç bileşen, tek deneyim. PC'nde çalışan küçük bir servis pazar
              ekranını okur, Telegram'a aktarır, cevabını panoya kopyalar.
            </p>
          </div>

          <ol className="mt-14 grid gap-8 md:grid-cols-3">
            <Step
              n={1}
              title="PC servisi ekranı okur"
              body="Pazar açtığında müşteri PM atınca PC servisi yazıyı OCR ile yakalar. Oyun dosyalarına müdahale yok, sadece ekran okuma."
              icon="🖥"
            />
            <Step
              n={2}
              title="Telegram'a bildirim gelir"
              body="PM kart olarak telefonuna düşer. Hazır cevap butonlarıyla 1 tık veya kendi yazıyla cevapla."
              icon="📱"
            />
            <Step
              n={3}
              title="Cevap KO'ya gider"
              body="3 mod seçeneği: tamamen manuel (Ctrl+V), F8 ile tek tuş, veya kendi sorumluluğunda tam otomatik. İndir sayfasında detaylar."
              icon="📋"
            />
          </ol>
        </div>
      </section>

      {/* Ne YAP / Ne YAPMA */}
      <section className="py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Bilinçli sınırlar
            </h2>
            <p className="mt-4 text-surface-50/60">
              PazarChat kasıtlı olarak bir <em>bot</em> değildir. Tek amacı PM
              bildirimlerini ulaştırmak ve cevaplarını panoya hazırlamaktır.
            </p>
          </div>

          <div className="mt-12 grid gap-6 md:grid-cols-2">
            <Panel title="✓ Yapar" tone="ok">
              <ul className="space-y-3 text-sm">
                <li>OCR ile ekrandan PM yakalar</li>
                <li>Cevabı Windows panosuna kopyalar</li>
                <li>Hazır cevap butonu sunar (kullanıcı tetiklemeli)</li>
                <li>Karakter ve müşteri geçmişini tutar</li>
                <li>Bildirim sustur (manuel)</li>
              </ul>
            </Panel>
            <Panel title="✗ Yapmaz" tone="warn">
              <ul className="space-y-3 text-sm">
                <li>Otomatik PM yanıtlama (anahtar kelime tetiği)</li>
                <li>Otomatik trade kabul/red</li>
                <li>Karakter hareketi veya tuş simülasyonu</li>
                <li>Memory reading veya packet manipülasyonu</li>
                <li>Pazar başlığını değiştirme</li>
              </ul>
            </Panel>
          </div>

          <p className="mx-auto mt-10 max-w-2xl text-center text-xs text-surface-50/40">
            Bu sınırlar oyun deneyimini korumak ve üçüncü taraf yazılım risklerini
            azaltmak için kasıtlı seçilmiştir. Detay için{" "}
            <Link href="/kullanim-kosullari" className="underline hover:text-surface-50/70">
              kullanım koşulları
            </Link>
            .
          </p>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-surface-800/80 bg-gradient-to-br from-surface-900 to-surface-950 py-20">
        <div className="mx-auto max-w-3xl px-4 text-center sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Beta'ya katıl
          </h2>
          <p className="mt-4 text-surface-50/70">
            Şu an küçük bir grup test ediyor. Davetiye kodunla bot'a katılınca
            30 günlük ücretsiz erişim alırsın.
          </p>
          <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <a
              href={BOT_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg bg-primary-500 px-6 py-3 text-sm font-semibold text-surface-950 transition hover:bg-primary-400"
            >
              Bot'a Git
            </a>
            <Link
              href="/indir"
              className="rounded-lg border border-surface-800 bg-surface-900 px-6 py-3 text-sm font-semibold text-surface-50 transition hover:bg-surface-800"
            >
              Kurulum Kılavuzu
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}

/* ----------------------------------------------------------------------------
 * Yardımcı komponentler — sayfa-içi, dış dosyaya gerek yok
 * -------------------------------------------------------------------------- */

function Step({
  n,
  title,
  body,
  icon,
}: {
  n: number;
  title: string;
  body: string;
  icon: string;
}) {
  return (
    <li className="relative rounded-2xl border border-surface-800 bg-surface-900/60 p-6">
      <div className="mb-4 flex items-center gap-3">
        <span className="grid h-9 w-9 place-items-center rounded-lg bg-primary-500/15 text-lg">
          {icon}
        </span>
        <span className="text-xs font-medium uppercase tracking-widest text-surface-50/40">
          Adım {n}
        </span>
      </div>
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-surface-50/60">{body}</p>
    </li>
  );
}

function Panel({
  title,
  tone,
  children,
}: {
  title: string;
  tone: "ok" | "warn";
  children: React.ReactNode;
}) {
  const accent =
    tone === "ok"
      ? "border-primary-500/30 bg-primary-500/5"
      : "border-accent-500/30 bg-accent-500/5";
  return (
    <div className={`rounded-2xl border ${accent} p-6`}>
      <h3 className="mb-4 text-lg font-semibold">{title}</h3>
      <div className="text-surface-50/70">{children}</div>
    </div>
  );
}

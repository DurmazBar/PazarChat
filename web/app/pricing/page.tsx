import type { Metadata } from "next";
import Link from "next/link";

const BOT_URL = process.env.NEXT_PUBLIC_BOT_URL || "https://t.me/KO_PazarChat_bot";

export const metadata: Metadata = {
  title: "Fiyatlandırma",
  description:
    "PazarChat fiyatlandırması. Beta döneminde ücretsiz, public launch sonrası abonelik tabanlı.",
};

export default function PricingPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-2xl text-center">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
          Fiyatlandırma
        </h1>
        <p className="mt-4 text-surface-50/60">
          Şu an beta dönemindeyiz. Aşağıdaki paketler tahminidir, beta sonrası
          kesinleşecek. Beta testçilerine özel indirim sunulacak.
        </p>
      </div>

      {/* Beta CTA */}
      <div className="mt-10 rounded-2xl border border-primary-500/40 bg-gradient-to-br from-primary-500/10 to-accent-500/5 p-8 text-center">
        <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary-500/30 bg-primary-500/15 px-3 py-1 text-xs font-medium text-primary-300">
          <span className="h-1.5 w-1.5 rounded-full bg-primary-400" />
          Beta dönemi · 30 gün ücretsiz
        </div>
        <h2 className="text-2xl font-bold">Davetiye ile ücretsiz erişim</h2>
        <p className="mx-auto mt-3 max-w-xl text-sm text-surface-50/60">
          Beta süresince davetiye kodu olan kullanıcılar 30 gün boyunca tüm
          özelliklere ücretsiz erişebilir. Geri bildirim ver, ürünü beraber
          şekillendirelim.
        </p>
        <a
          href={BOT_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-6 inline-block rounded-lg bg-primary-500 px-6 py-3 text-sm font-semibold text-surface-950 transition hover:bg-primary-400"
        >
          Bot'a Git
        </a>
      </div>

      {/* Tahmini paketler (tbd) */}
      <h2 className="mt-16 mb-6 text-center text-xl font-semibold text-surface-50/70">
        Public launch için tahmini paketler
      </h2>
      <p className="mx-auto mb-10 max-w-2xl text-center text-xs text-surface-50/40">
        Aşağıdaki fiyatlar kesinleşmemiştir, beta geri bildirimine göre değişebilir.
        Türkiye tüketici hukuku gereği <strong>7 gün cayma hakkı</strong> her zaman geçerlidir.
      </p>

      <div className="grid gap-6 md:grid-cols-3">
        <PriceCard
          name="Aylık"
          price="49"
          period="ay"
          features={[
            "1 PC lisans",
            "Sınırsız PM bildirim",
            "Hazır cevap setleri",
            "Mesaj geçmişi (30 gün)",
            "Telegram destek",
          ]}
        />
        <PriceCard
          name="3 Aylık"
          price="119"
          period="3 ay"
          highlight="~%20 indirim"
          features={[
            "Aylık'taki her şey",
            "Öncelikli destek",
            "Tek seferlik ödeme",
          ]}
          recommended
        />
        <PriceCard
          name="Yıllık"
          price="399"
          period="yıl"
          highlight="~%30 indirim"
          features={[
            "3 Aylık'taki her şey",
            "Erken erişim özellikler",
            "Marka stickerları (opsiyonel)",
          ]}
        />
      </div>

      <div className="mt-12 text-center text-sm text-surface-50/40">
        Soru için{" "}
        <a href={BOT_URL} target="_blank" rel="noopener noreferrer"
          className="text-primary-300 underline hover:text-primary-200">
          Telegram bot
        </a>{" "}
        veya{" "}
        <Link href="/iletisim" className="text-primary-300 underline hover:text-primary-200">
          iletişim sayfası
        </Link>
        .
      </div>
    </div>
  );
}

function PriceCard({
  name,
  price,
  period,
  features,
  highlight,
  recommended,
}: {
  name: string;
  price: string;
  period: string;
  features: string[];
  highlight?: string;
  recommended?: boolean;
}) {
  return (
    <div
      className={`relative rounded-2xl border p-6 ${
        recommended
          ? "border-primary-500/60 bg-primary-500/5"
          : "border-surface-800 bg-surface-900/60"
      }`}
    >
      {recommended && (
        <span className="absolute -top-3 left-6 rounded-full bg-primary-500 px-3 py-1 text-xs font-semibold text-surface-950">
          Önerilen
        </span>
      )}
      <h3 className="text-lg font-semibold">{name}</h3>
      <div className="mt-4 flex items-baseline gap-1">
        <span className="text-4xl font-bold tracking-tight">{price}₺</span>
        <span className="text-sm text-surface-50/50">/ {period}</span>
      </div>
      {highlight && (
        <p className="mt-1 text-xs font-medium text-accent-400">{highlight}</p>
      )}
      <ul className="mt-6 space-y-2 text-sm text-surface-50/70">
        {features.map((f) => (
          <li key={f} className="flex items-start gap-2">
            <span className="mt-0.5 text-primary-400">✓</span>
            <span>{f}</span>
          </li>
        ))}
      </ul>
      <button
        disabled
        className="mt-6 w-full cursor-not-allowed rounded-lg border border-surface-800 bg-surface-900 px-4 py-2 text-sm font-medium text-surface-50/40"
      >
        Beta sonrası açılacak
      </button>
    </div>
  );
}

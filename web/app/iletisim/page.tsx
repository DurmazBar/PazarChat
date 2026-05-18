import type { Metadata } from "next";
import Link from "next/link";

const BOT_URL = process.env.NEXT_PUBLIC_BOT_URL || "https://t.me/KO_PazarChat_bot";

export const metadata: Metadata = {
  title: "İletişim",
  description: "PazarChat ile iletişime geç — Telegram bot, e-posta ve destek kanalları.",
};

export default function IletisimPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6 lg:px-8">
      <Link href="/" className="text-sm text-surface-50/50 hover:text-surface-50">
        ← Ana sayfa
      </Link>

      <h1 className="mt-6 text-3xl font-bold tracking-tight sm:text-4xl">İletişim</h1>
      <p className="mt-3 text-surface-50/60">
        Beta süresince en hızlı destek kanalımız Telegram bot. İletişim
        e-posta adresimiz Faz 3 ile birlikte aktif olacaktır.
      </p>

      <div className="mt-10 space-y-6">
        <ContactCard
          icon="💬"
          title="Telegram Bot (Önerilen)"
          desc="En hızlı yöntem. Bot içinde /destek komutu ile yaz."
          actionText="Bot'u Aç"
          actionUrl={BOT_URL}
        />
        <ContactCard
          icon="✉️"
          title="E-posta"
          desc="Resmi yazışmalar için (faz 3'te aktif): destek@pazarchat.com"
          disabled
        />
        <ContactCard
          icon="📍"
          title="Resmi Adres & Ticari Bilgiler"
          desc="Şirket kuruluşundan sonra burada güncellenecek."
          disabled
        />
      </div>

      <div className="mt-12 rounded-lg border border-accent-500/30 bg-accent-500/5 p-4 text-xs text-accent-200">
        <strong>Yanıt süresi:</strong> Beta süresince 09:00–23:00 (TR saati) arasında
        en geç 3 saat içinde yanıt veriyoruz. Hafta sonları yanıt 24 saate uzayabilir.
      </div>
    </div>
  );
}

function ContactCard({
  icon,
  title,
  desc,
  actionText,
  actionUrl,
  disabled,
}: {
  icon: string;
  title: string;
  desc: string;
  actionText?: string;
  actionUrl?: string;
  disabled?: boolean;
}) {
  return (
    <div
      className={`flex items-start gap-4 rounded-2xl border p-5 ${
        disabled
          ? "border-surface-800 bg-surface-900/40 opacity-60"
          : "border-surface-800 bg-surface-900/60"
      }`}
    >
      <span className="text-2xl">{icon}</span>
      <div className="flex-1">
        <h3 className="font-semibold">{title}</h3>
        <p className="mt-1 text-sm text-surface-50/60">{desc}</p>
      </div>
      {actionText && actionUrl && (
        <a
          href={actionUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 rounded-lg bg-primary-500 px-4 py-2 text-sm font-medium text-surface-950 hover:bg-primary-400"
        >
          {actionText}
        </a>
      )}
    </div>
  );
}

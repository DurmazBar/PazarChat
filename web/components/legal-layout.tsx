import Link from "next/link";

/**
 * Yasal sayfalar için ortak layout — başlık, taslak uyarısı, içerik wrapper.
 */
export default function LegalLayout({
  title,
  lastUpdated,
  children,
}: {
  title: string;
  lastUpdated: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
      <Link href="/" className="text-sm text-surface-50/50 hover:text-surface-50">
        ← Ana sayfa
      </Link>

      <h1 className="mt-6 text-3xl font-bold tracking-tight sm:text-4xl">{title}</h1>
      <p className="mt-2 text-sm text-surface-50/40">Son güncelleme: {lastUpdated}</p>

      <div className="mt-6 rounded-lg border border-accent-500/30 bg-accent-500/5 p-4 text-xs text-accent-200">
        <strong>Taslak:</strong> Bu metin beta sürecinde bilgilendirme amaçlıdır.
        Public launch öncesi avukat tarafından son haline getirilecektir. Hukuki
        bağlayıcı sözleşme metni için final versiyonu bekleyiniz.
      </div>

      <article className="prose prose-invert mt-10 max-w-none space-y-6 text-sm leading-relaxed text-surface-50/80
        [&_h2]:mt-10 [&_h2]:text-xl [&_h2]:font-semibold [&_h2]:text-surface-50
        [&_h3]:mt-6 [&_h3]:text-base [&_h3]:font-semibold [&_h3]:text-surface-50
        [&_p]:text-surface-50/70
        [&_ul]:list-disc [&_ul]:pl-6 [&_ul]:space-y-1 [&_ul]:text-surface-50/70
        [&_a]:text-primary-300 [&_a]:underline hover:[&_a]:text-primary-200
        [&_strong]:text-surface-50 [&_code]:text-accent-300">
        {children}
      </article>
    </div>
  );
}

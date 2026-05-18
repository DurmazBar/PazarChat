import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-surface-800/80 bg-surface-950/50">
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          <div>
            <h3 className="mb-3 text-sm font-semibold text-surface-50">Ürün</h3>
            <ul className="space-y-2 text-sm text-surface-50/60">
              <li><Link href="/" className="hover:text-surface-50">Ana Sayfa</Link></li>
              <li><Link href="/indir" className="hover:text-surface-50">İndir</Link></li>
              <li><Link href="/pricing" className="hover:text-surface-50">Fiyatlandırma</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="mb-3 text-sm font-semibold text-surface-50">Yasal</h3>
            <ul className="space-y-2 text-sm text-surface-50/60">
              <li><Link href="/kvkk" className="hover:text-surface-50">KVKK Aydınlatma Metni</Link></li>
              <li><Link href="/kullanim-kosullari" className="hover:text-surface-50">Kullanım Koşulları</Link></li>
              <li><Link href="/mesafeli-satis" className="hover:text-surface-50">Mesafeli Satış</Link></li>
              <li><Link href="/iade-politikasi" className="hover:text-surface-50">İade Politikası</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="mb-3 text-sm font-semibold text-surface-50">Destek</h3>
            <ul className="space-y-2 text-sm text-surface-50/60">
              <li>
                <a
                  href={process.env.NEXT_PUBLIC_BOT_URL || "https://t.me/KO_PazarChat_bot"}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-surface-50"
                >
                  Telegram Bot
                </a>
              </li>
              <li><Link href="/iletisim" className="hover:text-surface-50">İletişim</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="mb-3 text-sm font-semibold text-surface-50">Önemli</h3>
            <p className="text-xs leading-relaxed text-surface-50/50">
              PazarChat bağımsız bir üçüncü taraf yardımcı uygulamadır.
              Knight Online veya NTTGames ile bağlantısı yoktur.
              Knight Online'ın kullanım koşullarına uyum kullanıcı sorumluluğundadır.
            </p>
          </div>
        </div>

        <div className="mt-10 flex flex-col items-start justify-between gap-4 border-t border-surface-800/80 pt-6 sm:flex-row sm:items-center">
          <p className="text-xs text-surface-50/40">
            © {new Date().getFullYear()} PazarChat. Tüm hakları saklıdır.
          </p>
          <p className="text-xs text-surface-50/40">
            Türkiye · Beta dönemi
          </p>
        </div>
      </div>
    </footer>
  );
}

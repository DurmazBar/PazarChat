import Link from "next/link";

const BOT_URL = process.env.NEXT_PUBLIC_BOT_URL || "https://t.me/KO_PazarChat_bot";

export default function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-surface-800/80 bg-surface-950/70 backdrop-blur-md">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-2 font-semibold tracking-tight"
          >
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary-600 text-surface-50 text-sm">
              P
            </span>
            <span className="text-lg">PazarChat</span>
          </Link>

          <nav className="hidden gap-6 text-sm text-surface-50/70 sm:flex">
            <Link href="/indir" className="hover:text-surface-50">İndir</Link>
            <Link href="/pricing" className="hover:text-surface-50">Fiyatlandırma</Link>
            <Link href="/kvkk" className="hover:text-surface-50">KVKK</Link>
            <Link href="/kullanim-kosullari" className="hover:text-surface-50">Şartlar</Link>
          </nav>

          <a
            href={BOT_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg bg-primary-500 px-3 py-1.5 text-sm font-medium text-surface-950 transition hover:bg-primary-400"
          >
            Bot'u Aç →
          </a>
        </div>
      </div>
    </header>
  );
}

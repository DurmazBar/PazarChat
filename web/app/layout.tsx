import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

import Header from "@/components/header";
import Footer from "@/components/footer";

const inter = Inter({
  subsets: ["latin", "latin-ext"],
  display: "swap",
  variable: "--font-inter",
});

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://pazarchat.com";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "PazarChat — Knight Online Pazar Asistanı",
    template: "%s · PazarChat",
  },
  description:
    "Knight Online'da pazar kurarken bilgisayar başından ayrılırken bile " +
    "müşterilerinin PM'lerine telefonundan cevap yaz. Otomatik cevap yok, " +
    "manuel cevaplama için bildirim aracı.",
  openGraph: {
    title: "PazarChat — Knight Online Pazar Asistanı",
    description:
      "AFK pazarcılıkta müşteri kaçırmayı bitir. Pazar kurarken hayatına devam et.",
    url: SITE_URL,
    siteName: "PazarChat",
    locale: "tr_TR",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "PazarChat — Knight Online Pazar Asistanı",
    description:
      "AFK pazarcılıkta müşteri kaçırmayı bitir. Pazar kurarken hayatına devam et.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr" className={inter.variable}>
      <body className="min-h-screen flex flex-col bg-surface-950 text-surface-50">
        <Header />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}

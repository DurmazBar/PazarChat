import type { Metadata } from "next";
import LegalLayout from "@/components/legal-layout";

export const metadata: Metadata = {
  title: "Kullanım Koşulları",
  description: "PazarChat kullanım koşulları — hizmetin kapsamı, kullanıcı sorumlulukları ve sınırlamalar.",
};

export default function KullanimKosullariPage() {
  return (
    <LegalLayout title="Kullanım Koşulları" lastUpdated="18 Mayıs 2026">
      <p>
        Bu sözleşme, PazarChat hizmetini kullanan kullanıcılar (<strong>"Kullanıcı"</strong>)
        ile hizmeti sağlayan PazarChat işletmesi (<strong>"PazarChat"</strong>)
        arasında akdedilir. Hizmeti kullanarak bu koşulları kabul etmiş sayılırsınız.
      </p>

      <h2>1. Hizmetin Tanımı</h2>
      <p>
        PazarChat, Knight Online oyununda pazar kuran kullanıcıların oyun içi
        özel mesajlarına (PM) manuel olarak cevap yazmasını kolaylaştıran bir{" "}
        <strong>bildirim ve pano (clipboard) yardımcı aracıdır</strong>.
        Aşağıdakileri <strong>içermez</strong>:
      </p>
      <ul>
        <li>Otomatik PM yanıtlama (anahtar kelime tetikli veya benzeri)</li>
        <li>Otomatik trade kabulü veya reddi</li>
        <li>Karakter hareketi, klavye veya fare simülasyonu</li>
        <li>Oyun belleğine müdahale (memory reading/writing)</li>
        <li>Oyun paketlerinin değiştirilmesi (packet manipulation)</li>
      </ul>

      <h2>2. Kullanıcı Sorumlulukları</h2>
      <ul>
        <li>
          <strong>Knight Online TOS Uyumu:</strong> Kullanıcı, Knight Online'ın
          işleten şirket (NTTGames veya halefi) tarafından belirlenen kullanım
          koşullarına uyum sağlamakla yükümlüdür. PazarChat üçüncü taraf bir
          uygulamadır ve Knight Online ile resmi bir bağlantısı yoktur.
        </li>
        <li>
          <strong>Lisans Paylaşımı Yasağı:</strong> Aldığınız lisans anahtarı
          kişisel kullanımınız içindir, başka bir kullanıcıya devredemez veya
          paylaşamazsınız.
        </li>
        <li>
          <strong>Yasal Kullanım:</strong> Hizmet, dolandırıcılık, taciz veya
          yasa dışı amaçlar için kullanılamaz.
        </li>
        <li>
          <strong>Asgari Yaş:</strong> Hizmet 18 yaş ve üzeri kullanıcılar
          içindir. 18 yaş altıysanız velinizin rızası ile kullanabilirsiniz.
        </li>
      </ul>

      <h2>3. Sorumluluk Reddi</h2>
      <p>
        PazarChat, kullanıcının Knight Online hesabında doğabilecek herhangi
        bir askıya alma, banlama veya benzeri tedbirden{" "}
        <strong>sorumluluk kabul etmez</strong>. Bu tedbirler oyun şirketinin
        takdirindedir ve PazarChat üçüncü taraf bir araç olduğundan, oyun
        şirketinin kullanım koşullarına göre yorumlanabilir.
      </p>
      <p>
        Hizmet "olduğu gibi" sunulur; kesintisiz çalışacağı, hatasız olacağı
        veya belirli sonuçlar üreteceği garanti edilmez.
      </p>

      <h3>3.1. Cevap Gönderim Modları ve Risk Seviyeleri</h3>
      <p>
        PazarChat üç farklı cevap gönderim modu sunar. Her birinin Knight
        Online kullanım koşulları açısından farklı risk profili vardır.
        Modu seçim sorumluluğu ve sonuçları tamamen kullanıcıya aittir:
      </p>
      <ul>
        <li>
          <strong>Manuel mod:</strong> Pano (clipboard) ile çalışır, hiçbir
          tuş simülasyonu yoktur. Kullanıcı her cevabı kendisi yapıştırır
          (Ctrl+V). TOS açısından <em>en güvenli</em> mod.
        </li>
        <li>
          <strong>Hibrit mod (F8 hotkey):</strong> Kullanıcı fiziksel olarak F8
          tuşuna bastığında pano içeriği KO penceresine yapıştırılır. Kullanıcı
          tetikli olması nedeniyle "otomasyon" sayılması zayıf olasılıktır,
          ancak nihai yorum oyun şirketine aittir.
        </li>
        <li>
          <strong>Otomatik mod (auto):</strong>{" "}
          <strong className="text-red-300">⚠ Yüksek risk.</strong> Cevap geldiği
          anda PC servisi KO penceresini otomatik olarak öne alır ve yapıştırma
          yapar. <strong>Bu mod keyboard simulation kategorisinde</strong> sayılabilir
          ve Knight Online kullanım koşullarınca <em>"otomasyon aracı"</em> olarak
          değerlendirilebilir. Bu modu kullanan kullanıcılar, oluşabilecek hesap
          askıya alma veya banlama risklerini <strong>açıkça kabul ederek</strong>{" "}
          kullanır. PazarChat bu moddan doğabilecek hesap kayıplarından{" "}
          <strong>hiçbir sorumluluk kabul etmez</strong>.
        </li>
      </ul>
      <p>
        Mod seçimi <code>.env</code> dosyasında <code>PASTE_MODE</code>{" "}
        değişkeniyle yapılır. Varsayılan değer{" "}
        <code>hybrid</code>'dir. <code>auto</code> moduna geçmek, bu paragraftaki
        ek riskleri kabul ettiğiniz anlamına gelir.
      </p>

      <h2>4. Lisans ve Erişim</h2>
      <p>
        PazarChat size hizmeti kullanma hakkı tanıyan kişisel, devredilemez,
        münhasır olmayan bir lisans verir. Bu lisans:
      </p>
      <ul>
        <li>1 lisans = 1 PC ilkesine bağlıdır.</li>
        <li>Makine kimliği değiştiğinde lisans otomatik askıya alınabilir.</li>
        <li>Abonelik süresi sona erdiğinde hizmet durur.</li>
      </ul>

      <h2>5. Veri ve Gizlilik</h2>
      <p>
        Kişisel verilerinizin işlenmesi hakkında detaylı bilgi için{" "}
        <a href="/kvkk">KVKK Aydınlatma Metni</a> sayfasına bakınız.
      </p>

      <h2>6. Hizmet Değişiklikleri</h2>
      <p>
        PazarChat hizmeti, özelliklerini ve bu kullanım koşullarını önceden
        bildirimle güncelleyebilir. Önemli değişiklikler en az 14 gün önceden
        duyurulur.
      </p>

      <h2>7. Fesih</h2>
      <p>
        Kullanıcı, hesabını her zaman silme hakkına sahiptir. PazarChat, kullanım
        koşullarına aykırı davranan kullanıcıların hesabını uyarı ile veya
        ağır ihlallerde doğrudan askıya alma hakkını saklı tutar.
      </p>

      <h2>8. Geçerli Hukuk ve Uyuşmazlık Çözümü</h2>
      <p>
        Bu sözleşme Türkiye Cumhuriyeti yasalarına tabidir. Uyuşmazlıklarda
        Türkiye Cumhuriyeti tüketici hakları mevzuatı uygulanır. Tüketici
        Hakem Heyeti yetkilidir.
      </p>

      <h2>9. İletişim</h2>
      <p>
        Sorularınız için <a href="/iletisim">iletişim sayfası</a> üzerinden veya
        bot içinden <code>/destek</code> komutuyla ulaşabilirsiniz.
      </p>
    </LegalLayout>
  );
}

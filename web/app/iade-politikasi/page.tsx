import type { Metadata } from "next";
import LegalLayout from "@/components/legal-layout";

export const metadata: Metadata = {
  title: "İade Politikası",
  description: "PazarChat iade politikası — cayma hakkı ve geri ödeme süreçleri.",
};

export default function IadePage() {
  return (
    <LegalLayout title="İade Politikası" lastUpdated="18 Mayıs 2026">
      <p>
        PazarChat olarak müşteri memnuniyetini önemsiyoruz. Hizmetimiz
        dijital olduğundan iade süreçlerimiz Türkiye tüketici hukukuna
        uygun olarak aşağıdaki gibi düzenlenmiştir.
      </p>

      <h2>1. 7 Günlük Cayma Hakkı</h2>
      <p>
        Türkiye Cumhuriyeti Tüketici Kanunu gereği, hizmeti satın aldığınız
        tarihten itibaren <strong>7 gün içinde</strong> herhangi bir gerekçe
        belirtmeksizin cayma hakkınızı kullanabilirsiniz.
      </p>

      <h2>2. Cayma Talebi Nasıl İletilir?</h2>
      <ul>
        <li>Telegram bot üzerinden <code>/destek iade</code> komutuyla yazabilirsiniz.</li>
        <li>İletişim sayfasındaki e-posta adresine yazabilirsiniz.</li>
      </ul>
      <p>
        Talebinizde sipariş numaranızı (e-arşiv fatura numarası) belirtmeniz
        süreci hızlandırır.
      </p>

      <h2>3. İade Süresi</h2>
      <p>
        Cayma talebiniz kabul edildikten sonra ödediğiniz tutar:
      </p>
      <ul>
        <li>Aynı ödeme yöntemine (kart, banka hesabı vb.)</li>
        <li>En geç <strong>14 gün</strong> içinde</li>
        <li>Herhangi bir kesinti yapılmadan</li>
      </ul>
      <p>iade edilir.</p>

      <h2>4. İyi Niyet Politikası</h2>
      <p>
        7 günlük cayma süresi dolduktan sonra da, hesap banlanması veya benzer
        durumlarda <strong>iyi niyet kuralı</strong> gereği kalan abonelik
        günlerinizin orantılı bedelini iade etme hakkımızı saklı tutarız.
        Bu durumlar takdire bağlıdır.
      </p>

      <h2>5. İade Yapılamayan Durumlar</h2>
      <ul>
        <li>
          Cayma hakkı süresi dolmuş ve kullanıcı sözleşmenin "hemen ifaya
          başlama" maddesini açıkça onaylamışsa.
        </li>
        <li>
          Kötüye kullanım, lisans paylaşımı veya kullanım koşulları ihlali
          tespit edilmiş hesaplarda.
        </li>
        <li>
          Dolandırıcılık şüphesi nedeniyle askıya alınan hesaplarda
          (soruşturma sonrası karar verilir).
        </li>
      </ul>

      <h2>6. Hizmet Kesintilerinde İade</h2>
      <p>
        Beklenmedik teknik nedenlerle PazarChat'in tamamen kapanması durumunda,
        kalan abonelik günleriniz tam orantılı olarak iade edilir.
      </p>

      <h2>7. Şikayet</h2>
      <p>
        İade talebiniz reddedilirse veya işlem 14 günde tamamlanmazsa, Tüketici
        Hakem Heyeti'ne başvurabilirsiniz.
      </p>
    </LegalLayout>
  );
}

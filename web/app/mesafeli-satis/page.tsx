import type { Metadata } from "next";
import LegalLayout from "@/components/legal-layout";

export const metadata: Metadata = {
  title: "Mesafeli Satış Sözleşmesi",
  description: "PazarChat mesafeli satış sözleşmesi — abonelik satın alma şartları.",
};

export default function MesafeliSatisPage() {
  return (
    <LegalLayout title="Mesafeli Satış Sözleşmesi" lastUpdated="18 Mayıs 2026">
      <p>
        6502 sayılı Tüketicinin Korunması Hakkında Kanun ve Mesafeli Sözleşmeler
        Yönetmeliği uyarınca düzenlenmiştir.
      </p>

      <h2>1. Taraflar</h2>
      <ul>
        <li>
          <strong>Satıcı:</strong> PazarChat (Beta döneminde bireysel; şirket
          kuruluşu sonrası bu bölüm güncellenecektir.)
        </li>
        <li>
          <strong>Alıcı:</strong> Hizmeti satın alan kişi (sözleşmeyi onaylayan
          kullanıcı).
        </li>
      </ul>

      <h2>2. Sözleşmenin Konusu</h2>
      <p>
        Alıcı'nın PazarChat hizmetine belirli bir süre için abonelik
        satın almasıdır. Hizmet dijitaldir, fiziksel teslimat yoktur.
      </p>

      <h2>3. Hizmet Bedeli</h2>
      <p>
        Hizmet bedeli, satın alma anında web sayfasında belirtilen tutardır.
        Tüm fiyatlar KDV dahil Türk Lirası cinsindendir. Beta dönemi süresince
        ücretsizdir.
      </p>

      <h2>4. Ödeme</h2>
      <p>
        Ödeme, anlaşmalı ödeme kuruluşu (örn. iyzico veya Shopier) üzerinden
        kredi kartı, banka kartı veya havale ile alınır. Ödeme bilgileri
        PazarChat tarafından saklanmaz.
      </p>

      <h2>5. İfa</h2>
      <p>
        Ödemenin tamamlanmasından sonra hizmet anında aktive edilir. Lisans
        anahtarı Telegram bot üzerinden teslim edilir.
      </p>

      <h2>6. Cayma Hakkı</h2>
      <p>
        Alıcı, sözleşmenin imzalanmasından itibaren{" "}
        <strong>7 (yedi) gün</strong> içinde herhangi bir gerekçe göstermeksizin
        cayma hakkına sahiptir. Cayma için bot üzerinden <code>/destek</code>{" "}
        komutuyla talep iletilmesi yeterlidir.
      </p>
      <p>
        Cayma süresi içinde yapılan iadelerde:
      </p>
      <ul>
        <li>Ödeme aynı yöntemle 14 gün içinde iade edilir.</li>
        <li>Hizmet kullanımına bakılmaksızın bedel iade edilir.</li>
      </ul>
      <p>
        Cayma hakkının kullanılamayacağı haller (yönetmelik m.15):
      </p>
      <ul>
        <li>
          Tüketicinin açık onayı ile, cayma hakkı süresi dolmadan ifa edilmesi
          ve ifa edilmiş kısma ilişkin tüketici onayı verilmesi durumunda
          (ifa edilmiş kısım için).
        </li>
      </ul>

      <h2>7. Cayma Sonrası İade Süresi</h2>
      <p>
        İade tutarı, cayma talebinin kabulünden itibaren <strong>14 gün
        içinde</strong> Alıcı'nın ödeme yaptığı yönteme yatırılır.
      </p>

      <h2>8. Hizmet İptali ve Yenileme</h2>
      <p>
        Abonelik süresi sonunda otomatik yenileme uygulanmaz; süre dolduğunda
        kullanıcının manuel yenileme yapması gerekir. (Sonraki sürümlerde
        otomatik yenileme opsiyonel olarak sunulabilir.)
      </p>

      <h2>9. Şikâyet ve Uyuşmazlık</h2>
      <p>
        Şikâyetler için Tüketici Hakem Heyeti'ne veya Tüketici Mahkemesine
        başvurulabilir.
      </p>

      <h2>10. Yürürlük</h2>
      <p>
        Sözleşme, Alıcı'nın ödemeyi onaylaması ile yürürlüğe girer.
      </p>
    </LegalLayout>
  );
}

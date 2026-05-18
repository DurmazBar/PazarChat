import type { Metadata } from "next";
import LegalLayout from "@/components/legal-layout";

export const metadata: Metadata = {
  title: "KVKK Aydınlatma Metni",
  description: "PazarChat KVKK aydınlatma metni — kişisel verilerinizin nasıl işlendiği.",
};

export default function KvkkPage() {
  return (
    <LegalLayout title="KVKK Aydınlatma Metni" lastUpdated="18 Mayıs 2026">
      <p>
        6698 sayılı <strong>Kişisel Verilerin Korunması Kanunu</strong> (KVKK)
        kapsamında, PazarChat hizmetini kullanmanız sırasında işlenen kişisel
        verileriniz hakkında sizi bilgilendirmek isteriz.
      </p>

      <h2>1. Veri Sorumlusu</h2>
      <p>
        PazarChat hizmetini sunan veri sorumlusu beta sürecinde bireysel olarak
        hizmet sahibi tarafından yönetilmektedir. Şirket kuruluşu sonrası bu
        bölüm güncellenecek ve ticaret sicil bilgileri eklenecektir.
      </p>

      <h2>2. İşlenen Kişisel Veriler</h2>
      <p>Hizmet sunulurken aşağıdaki veriler işlenir:</p>
      <ul>
        <li><strong>Hesap bilgileri:</strong> Telegram kullanıcı adı, Telegram chat ID, görünen isim.</li>
        <li><strong>Lisans verileri:</strong> Makine kimlik özeti (CPU, MAC adresi vb. hash'i), abonelik bilgisi.</li>
        <li><strong>Hizmet kullanım verileri:</strong> Yakalanan PM içeriği, oyun içi karakter adı, sunucu adı.</li>
        <li><strong>Teknik veriler:</strong> IP adresi, kullanıcı ajanı, oturum zaman damgaları (denetim kaydı).</li>
      </ul>

      <h2>3. İşleme Amacı</h2>
      <ul>
        <li>PazarChat hizmetinin sunulması (PM yakalama, Telegram'a aktarma, panoya kopyalama)</li>
        <li>Lisans doğrulaması ve kötüye kullanım önleme</li>
        <li>Müşteri destek hizmeti</li>
        <li>Hizmet kalitesini iyileştirme ve hata teşhisi</li>
        <li>Yasal yükümlülüklerin yerine getirilmesi (vergi, tüketici hakları)</li>
      </ul>

      <h2>4. Veri Aktarımı (Üçüncü Taraf İşleyiciler)</h2>
      <p>
        Verileriniz aşağıdaki yurt dışı veri işleyicilere yasal sınırlar
        içinde aktarılır:
      </p>
      <ul>
        <li><strong>Supabase Inc.</strong> (Frankfurt, AB) — veritabanı ve kimlik doğrulama altyapısı.</li>
        <li><strong>Telegram FZ-LLC</strong> (Dubai) — mesajlaşma altyapısı.</li>
        <li><strong>Vercel Inc.</strong> (ABD/AB) — web sitesi barındırma.</li>
      </ul>
      <p>
        Bu aktarımlar KVKK m.9 ve standart sözleşme hükümleri çerçevesinde
        gerçekleştirilir.
      </p>

      <h2>5. Saklama Süreleri</h2>
      <ul>
        <li><strong>PM mesajları:</strong> 30 gün sonra otomatik silinir.</li>
        <li><strong>Hesap bilgileri:</strong> Hesap silinene kadar.</li>
        <li><strong>Denetim kayıtları:</strong> Yasal saklama süresi (5 yıl).</li>
        <li><strong>Ödeme bilgileri:</strong> Faz 3 sonrası vergi yasalarına uygun süre.</li>
      </ul>

      <h2>6. Üçüncü Kişi Mesaj İçeriği Hakkında</h2>
      <p>
        Pazardayken sizin karakterinize PM atan diğer oyuncuların mesajları
        sistem tarafından işlenir. Bu kapsamda <strong>üçüncü kişi mesaj
        içeriği</strong> meşru menfaat dayanağıyla, sadece hizmetin sunulması
        amacıyla, 30 gün saklanır ve sonrasında silinir. Bu mesajlar
        pazarlama, profiling veya analitik amaçlı kullanılmaz.
      </p>

      <h2>7. Veri Sahibi Hakları (KVKK m.11)</h2>
      <p>Kanun gereği aşağıdaki haklara sahipsiniz:</p>
      <ul>
        <li>Kişisel verilerinizin işlenip işlenmediğini öğrenme</li>
        <li>İşlenmişse buna ilişkin bilgi talep etme</li>
        <li>Verilerinizin düzeltilmesini veya silinmesini isteme</li>
        <li>Yurt içi/yurt dışı aktarımdan haberdar olma</li>
        <li>Otomatik karar verme sonuçlarına itiraz etme</li>
        <li>Zarar oluşmuşsa giderim talep etme</li>
      </ul>
      <p>
        Bu haklarınızı kullanmak için bot üzerinden <code>/destek</code>{" "}
        komutuyla iletişime geçebilir veya destek e-posta adresine yazabilirsiniz.
        Talepleriniz 30 gün içinde yanıtlanır.
      </p>

      <h2>8. Açık Rıza ve Onay</h2>
      <p>
        Hizmeti kullanmaya başlamanız bu aydınlatma metnini okuduğunuz ve
        kişisel verilerinizin yukarıda belirtilen kapsamda işlenmesini kabul
        ettiğiniz anlamına gelir.
      </p>
    </LegalLayout>
  );
}

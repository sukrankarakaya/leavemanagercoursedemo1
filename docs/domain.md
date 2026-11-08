# Domain

> Alan dili: iş, insanlar ve ajanlar arasındaki ortak sözlük. Burada olmayan bir terim için ajan
> kendi anlamını uydurur — terimi önce buraya ekleyin. Kodda İngilizce karşılık kullanılır.

## Ubiquitous language

| Term | Meaning | Notes / not to be confused with |
|---|---|---|
| Çalışan (`Employee`) | Sistemde izin talep eden kişi. Her çalışanın tam olarak bir yöneticisi vardır. | Bir yönetici de kendi izni için çalışandır. |
| Yönetici (`Manager`) | Kendi ekibindeki çalışanların taleplerini onaylayan/reddeden kişi. | Yönetici ≠ İK; İK onay vermez (BR-4). |
| İK (`HR`) | İzin türlerini, yıllık hakları ve bakiye düzeltmelerini yöneten rol. | İK rolü talep onaylamaz. |
| Rol (`Role`) | `EMPLOYEE`, `MANAGER`, `HR`. Bir kullanıcının tek rolü vardır; yönetici aynı zamanda çalışandır. | |
| İzin türü (`LeaveType`) | Yıllık (`ANNUAL`), Mazeret (`EXCUSE`), Hastalık (`SICK`), Ücretsiz (`UNPAID`). Her türün "bakiyeden düşer" bayrağı vardır. | MVP'de Yıllık bakiyeden düşer; diğerleri İK tanımına göre. |
| İzin talebi (`LeaveRequest`) | Bir çalışanın bir izin türü ve tarih aralığı (başlangıç–bitiş, dahil) için açtığı kayıt. | "İzin" tek başına belirsizdir: talep mi, bakiye mi — açık yazın. |
| Talep durumu (`RequestStatus`) | `PENDING` (Beklemede) → `APPROVED` (Onaylandı) / `REJECTED` (Reddedildi); veya `CANCELLED` (İptal edildi). | |
| Yıllık hak (`Entitlement`) | Bir çalışanın bir yıl ve izin türü için tanımlı toplam gün sayısı (İK belirler). | Bakiye ile karıştırmayın. |
| İzin bakiyesi (`Balance`) | Kalan gün = hak − onaylanmış günler − beklemedeki günler (o yıl, o tür). | Beklemedeki talepler bakiyeyi rezerve eder. |
| İş günü (`Workday`) | Cumartesi, Pazar ve tanımlı resmî tatiller dışındaki gün. | Takvim günü değil. |
| Resmî tatil (`Holiday`) | İK'nın tanımladığı, iş günü sayılmayan tarih. | |
| Denetim kaydı (`AuditEntry`) | Bir talebin her durum değişikliğinde kim, ne zaman, hangi geçişi yaptı kaydı. | Silinmez, değiştirilmez. |

## Business rules

- **BR-1:** İzin süresi, başlangıç ve bitiş günleri **dahil**, yalnızca *iş günü* olarak hesaplanır.
  Aralıkta hiç iş günü yoksa talep oluşturulamaz.
- **BR-2:** Bakiyeden düşen bir izin türünde, talep edilen iş günü sayısı mevcut bakiyeyi aşıyorsa
  talep oluşturulamaz.
- **BR-3:** Aynı çalışanın `PENDING` veya `APPROVED` durumundaki talepleri tarih olarak çakışamaz
  (tek bir ortak gün bile çakışmadır).
- **BR-4:** Bir talebi yalnızca talep sahibinin yöneticisi onaylayabilir veya reddedebilir.
  Kimse kendi talebini onaylayamaz/reddedemez.
- **BR-5:** Reddetmede gerekçe zorunludur (boş veya yalnızca boşluk kabul edilmez).
- **BR-6:** Çalışan, başlangıç tarihi henüz gelmemiş (başlangıç > bugün) kendi `PENDING` veya
  `APPROVED` talebini iptal edebilir. İptal edilen talebin günleri bakiyeye geri döner.
- **BR-7:** `APPROVED`, `REJECTED` ve `CANCELLED` son durumlardır: içerikleri (tarih, tür, gerekçe)
  düzenlenemez. Tek izinli geçiş BR-6'daki `APPROVED → CANCELLED`'dır.
- **BR-8:** Başlangıç tarihi bugünden önce olan talep açılamaz. İstisna: `SICK` türünde başlangıç
  en fazla 7 takvim günü geriye dönük olabilir.

## Key domain invariants

- Bir izin bakiyesi **hiçbir zaman negatif olamaz** (hiçbir işlem sırası, İK düzeltmesi dahil).
- Her talep durum değişikliği bir denetim kaydı üretir: kim (`actor_id`), ne zaman (UTC), hangi
  geçiş. Denetim kayıtları silinmez ve değiştirilmez.
- Geçerli durum geçişleri yalnızca şunlardır: `PENDING→APPROVED`, `PENDING→REJECTED`,
  `PENDING→CANCELLED`, `APPROVED→CANCELLED` (BR-6). Başka her geçiş reddedilir.
- "Bugün" her zaman `Clock` üzerinden okunur (`docs/conventions.md`, Data rules).

## Sensitive areas

- **Yetkilendirme** — kim kimin talebini görebilir, onaylayabilir, iptal edebilir (BR-4, BR-6);
  rol kontrolü ve kayıt sahipliği. Hata: yetkisiz onay veya başkasının verisini görme.
- **İzin bakiyesi** — iş günü hesabı, bakiye hesabı, rezervasyon ve iade (BR-1, BR-2, BR-6, negatif
  bakiye değişmezi). Hata: çalışan hakkı ve bordro etkilenir.
- **Kişisel veri** — kullanıcı bilgileri ve özellikle `SICK` taleplerinin gerekçe/ek alanları
  (dolaylı sağlık verisi, KVKK). Yalnızca talep sahibi, yöneticisi ve İK görür; log'a yazılmaz
  (`docs/security.md`).

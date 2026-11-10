# Spec 0002 — hesaplar, giriş ve oturum

- Status: In progress
- Mode: lite
- Plan: `specs/plans/0002-plan.md`
- Self-critique: done

## Intent
İK, şirket çalışanlarının hesaplarını kendisi açmak istiyor; çalışanlar ve yöneticiler kendi e-posta
ve parolalarıyla giriş yapıp çıkabilmeli, böylece sonraki izin özellikleri "kim, neyi yapabilir"
sorusuna dayanabilir. Başarı: yalnızca İK'nın açtığı hesaplar giriş yapar; ilk girişte geçici parola
değiştirilmek zorundadır; hareketsiz veya çok uzun açık kalan oturum kendiliğinden kapanır; parola
tahmini yavaşlatılır. Bilerek yapılmayan: herkese açık kayıt, parola sıfırlama (B-2), iki adımlı
doğrulama (B-3), "beni hatırla", kullanıcı düzenleme/pasifleştirme, IP tabanlı sınırlama.

## Requirements
- R-1 **İlk İK hesabı:** Sistemde hiç kullanıcı yokken, sunucuda çalıştırılan tek seferlik bir yönetim
  komutu ilk İK hesabını oluşturur ve geçici parolasını bir kez gösterir. Sistemde en az bir kullanıcı
  varken komut hesap oluşturmaz. Repoda varsayılan parola veya demo hesabı yoktur.
- R-2 **Hesap oluşturma (yalnızca İK):** İK; ad soyad, e-posta, rol (Çalışan / Yönetici / İK) ve
  yönetici bilgisiyle hesap oluşturur. Ad soyad baş/son boşlukları kırpılarak 1–100 karakterdir.
  E-posta geçerli biçimde, en fazla 254 karakter, küçük harfe çevrilerek saklanır ve büyük/küçük harf
  farkı gözetmeksizin benzersizdir. Çalışan rolü için yönetici zorunludur; Yönetici ve İK rolleri için
  isteğe bağlıdır; seçilen yönetici, Yönetici rolündeki mevcut bir hesap olmalıdır.
- R-3 **Geçici parola:** Hesap oluşturulduğunda sistem kriptografik rastgelelikle 12 karakterlik (harf + rakam,
  karıştırılabilir 0/O/1/l/I hariç) bir geçici parola üretir ve
  yalnızca o anda İK'ya bir kez gösterir; düz metin olarak hiçbir yerde saklanmaz veya loglanmaz.
- R-4 **Hesap listesi (yalnızca İK):** İK tüm hesapları ad, e-posta, rol ve yöneticisiyle görür.
  Parola veya parola özeti hiçbir yanıtta yer almaz.
- R-5 **Giriş:** Kullanıcı e-posta ve parolasıyla giriş yapar. Hatalı e-posta, hatalı parola ve
  sınırlanmış hesap için aynı genel mesaj döner; hesabın var olup olmadığı anlaşılmaz.
- R-6 **İlk girişte parola değişikliği:** Geçici parolayla giriş yapan kullanıcı, parolasını
  değiştirene kadar parola değiştirme ve çıkış dışında hiçbir işlem yapamaz.
- R-7 **Parola kuralları:** Yeni parola 12–128 karakterdir; karmaşıklık zorunluluğu yoktur; e-postayla
  (büyük/küçük harf duyarsız) ve mevcut parolayla aynı olamaz. Parola değiştirmek mevcut parolayı ister.
- R-8 **Oturum:** Başarılı girişte yeni bir oturum başlar (önceki oturum kimliği yeniden kullanılmaz).
  Oturum 30 dakika hareketsizlikte, hareket olsa bile girişten 8 saat sonra kapanır. Giriş
  yapmış kullanıcının her isteği hareket sayılır; arayüz arka planda periyodik istek göndermez. Çıkışta oturum
  sunucuda da sonlanır. Parola değiştirildiğinde o kullanıcının diğer tüm oturumları kapanır.
- R-9 **Kimlik bilgisi:** Giriş yapmış kullanıcı kendi adını, e-postasını ve rolünü görür.
- R-10 **Giriş denemesi sınırı:** Aynı e-posta için 15 dakika içinde 5 başarısız denemeden sonra o
  e-postayla giriş 15 dakika boyunca reddedilir (doğru parolayla bile); başarılı giriş sayacı sıfırlar.
  Var olmayan e-postalar da aynı şekilde sayılır.
- R-11 **Erişim:** Giriş yapmamış biri hiçbir korumalı işlemi yapamaz ve arayüzde giriş sayfasına
  yönlendirilir. İK olmayan biri İK işlemlerini yapamaz (`docs/security.md`, yetki matrisi).

## User experience
- Flow:
  1. Giriş yapmamış kullanıcı herhangi bir sayfayı açar → giriş sayfasına yönlendirilir.
  2. E-posta + parola → geçici parolaysa "Parolanı değiştir" sayfası → değiştirince ana sayfa.
  3. Ana sayfada üst çubuk: ad, rol, "Çıkış". İK için ek olarak "Kullanıcılar" bağlantısı.
  4. İK → Kullanıcılar: liste + "Kullanıcı oluştur" formu → oluşturunca geçici parola bir kez gösterilir.
- States:
  - Giriş sayfası: boş form · gönderiliyor · hata (genel mesaj, sınırlama dahil) · başarı (yönlendirme).
  - Parolanı değiştir: boş form · gönderiliyor · doğrulama hatası (kurala göre mesaj) · başarı.
  - Kullanıcılar (İK): yükleniyor · liste · boş liste mümkün değil (en az İK kendisi) · hata ·
    yetki yok (İK olmayan biri adrese giderse "Bu sayfayı görüntüleme yetkiniz yok").
  - Kullanıcı oluştur: boş form · doğrulama hatası (alan bazında) · e-posta zaten kayıtlı · başarı
    (geçici parola tek seferlik gösterim, "bir daha gösterilmeyecek" uyarısıyla).
  - Oturum süresi dolduğunda: bir sonraki işlemde giriş sayfasına yönlendirme ve "Oturumunuzun süresi
    doldu, lütfen tekrar giriş yapın." mesajı.
- Design reference: none — the flow above is the design.
- Accessibility: her form alanının görünür etiketi var; hata mesajları ilgili alana bağlı ve ekran
  okuyucuya duyurulur; tüm akış klavyeyle yapılabilir; parola alanları `autocomplete` ipuçlarıyla
  (`current-password`, `new-password`); kontrast WCAG AA.

## Constraints & out of scope
- Sensitive area: Yetkilendirme
- Sensitive area: Kişisel veri
- Split: proposed 0002 (giriş/çıkış/oturum) · 0003 (İK hesap oluşturma) · 0004 (giriş denemesi sınırı),
  alternatif iki spec; kept as one — sukrankarakaya, 2026-11-10, özellikler birbirine bağlı ve tek
  teslimde istendi.
- Kimlik doğrulama ve yetki kuralları `docs/security.md`'deki gibidir (sunucu tarafı oturum,
  `HttpOnly` + `SameSite=Strict` cookie, Argon2id, varsayılan reddet, başkasının kaydına 404).
- Süre hesapları tek saat kaynağından (`Clock`) okunur; 30 dk / 8 sa / 15 dk sınırları sabit saatle test edilir.
- Log'a parola, geçici parola, oturum kimliği yazılmaz.
- Var olmayan e-postada da sahte bir Argon2 doğrulaması çalışır (yanıt süresi hesabın varlığını
  sızdırmasın) — review'da kontrol edilir, ölçüm kriteri değildir.
- Başarısız deneme sayacı atomik güncellenir (eşzamanlı denemeler sayımdan kaçmaz).
- Bu spec B-1'i (giriş denemesi sınırlama) kapatır.
- Kapsam dışı: parola değiştirmede yanlış mevcut parola denemelerinin sınırlanması (B-5), herkese açık kayıt, parola sıfırlama (B-2), 2FA (B-3), "beni hatırla", hesap
  düzenleme/pasifleştirme/silme, IP tabanlı sınırlama, e-posta gönderimi, izin alanı özellikleri.

## Acceptance criteria
**İlk hesap ve hesap oluşturma**
- [ ] AC-1 — Hiç kullanıcı yokken yönetim komutu bir İK hesabı oluşturur ve geçici parolayı bir kez
  yazdırır; en az bir kullanıcı varken komut hesap oluşturmadan hata verir (R-1).
- [ ] AC-2 — İK geçerli bilgilerle hesap oluşturur; yanıt geçici parolayı bir kez içerir (12 karakter, her hesapta farklı); aynı hesabın
  sonraki hiçbir yanıtında (liste, kimlik bilgisi) parola veya parola özeti bulunmaz (R-2, R-3, R-4).
- [ ] AC-3 — Büyük/küçük harf farkıyla aynı olan bir e-postayla ikinci hesap reddedilir; geçersiz
  e-posta biçimi ve 254 karakteri aşan e-posta reddedilir; boşluk kırpıldıktan sonra boş veya 100
  karakteri aşan ad soyad reddedilir, 1 ve 100 karakter kabul edilir (R-2).
- [ ] AC-4 — Çalışan rolü yöneticisiz reddedilir; Yönetici rolünde olmayan biri yönetici seçilirse
  reddedilir; Yönetici ve İK rolleri yöneticisiz kabul edilir (R-2).
- [ ] AC-5 — İK olmayan bir kullanıcı hesap oluşturamaz ve hesap listesini göremez (R-11).
- [ ] AC-6 — Geçici parola ve parolalar veritabanında yalnızca Argon2id özeti olarak durur; log
  çıktısında geçici parola, parola veya oturum kimliği geçmez (R-3).

**Giriş, parola ve oturum**
- [ ] AC-7 — Doğru e-posta ve parolayla giriş başarılı olur; e-posta büyük/küçük harf duyarsızdır (R-5).
- [ ] AC-8 — Hatalı parola, var olmayan e-posta ve sınırlanmış hesap aynı yanıtı (durum + mesaj) döner (R-5).
- [ ] AC-9 — Geçici parolayla giriş yapan kullanıcı parolayı değiştirmeden yalnızca parola değiştirme ve
  çıkış yapabilir; diğer her korumalı işlem reddedilir (R-6).
- [ ] AC-10 — 11 karakterlik, 129 karakterlik, e-postayla aynı ve mevcut parolayla aynı yeni parola
  reddedilir; 12 ve 128 karakterlik parola kabul edilir; mevcut parola yanlışsa değişiklik reddedilir (R-7).
- [ ] AC-11 — Başarılı girişte oturum kimliği yenilenir; giriş öncesi verilen kimlik girişten sonra
  geçersizdir; cookie `HttpOnly` ve `SameSite=Strict` taşır; JSON olmayan (form-encoded) yazma isteği reddedilir (R-8).
- [ ] AC-12 — Son işlemden 30 dakika sonra oturum geçersizdir; 29 dakika 59 saniyede geçerlidir (R-8).
- [ ] AC-13 — Sürekli işlem yapılsa bile girişten tam 8 saat sonra oturum geçersizdir (R-8).
- [ ] AC-14 — Çıkıştan sonra aynı oturum kimliğiyle hiçbir korumalı işlem yapılamaz (R-8).
- [ ] AC-15 — Parola değiştirildiğinde aynı kullanıcının diğer oturumları geçersiz olur; değiştiren
  oturum geçerli kalır (R-8).
- [ ] AC-16 — Giriş yapmış kullanıcı kendi ad, e-posta ve rolünü görür; giriş yapmamışken bu bilgi
  istenemez (R-9, R-11).

**Giriş denemesi sınırı**
- [ ] AC-17 — 15 dakika içinde 5 başarısız denemeden sonra 6. deneme doğru parolayla bile reddedilir;
  4 başarısızdan sonra doğru parola kabul edilir ve sayaç sıfırlanır; eşzamanlı 10 başarısız denemeden
  sonra doğru parola reddedilir (R-10).
- [ ] AC-18 — Sınırlama 15 dakika sonra kalkar; 15 dakikadan eski başarısız denemeler sayılmaz;
  var olmayan e-posta da aynı şekilde sınırlanır (R-10).

**Arayüz**
- [ ] AC-19 — Giriş yapmamış kullanıcı herhangi bir sayfayı açınca giriş sayfasına yönlendirilir;
  süresi dolmuş oturumda "Oturumunuzun süresi doldu…" mesajı gösterilir; sunucu süresi dolmuş oturum
  için `SESSION_EXPIRED`, oturum yok/tanınmıyorsa `UNAUTHENTICATED` hata kodunu (401) döner (R-11, UX).
- [ ] AC-20 — Giriş ve parola değiştirme sayfaları boş, gönderiliyor, hata ve başarı durumlarını
  gösterir; hata mesajları ilgili alana bağlıdır (UX).
- [ ] AC-21 — İK için Kullanıcılar sayfası listeyi, oluşturma formunu, alan bazında hataları,
  "e-posta zaten kayıtlı" hatasını ve tek seferlik geçici parola gösterimini sunar; İK olmayan
  kullanıcıya "yetki yok" durumu gösterilir (UX).
- [ ] AC-22 — Üst çubuk ad, rol ve çıkışı gösterir; "Kullanıcılar" bağlantısı yalnızca İK'ya görünür (UX).

## Definition of Done
- [ ] Every acceptance criterion mapped to proof (test or reproducible observation)
- [ ] `scripts/check` green
- [ ] Independent review done; real findings fixed, noise rejected with written rationale, deferred ones in `specs/backlog.md`
- [ ] Docs / ADRs updated if behavior or architecture changed
- [ ] Spec moved to `specs/done/` (it becomes immutable there)

## Scorecard (fill at ship — honest numbers make the process improvable)
| Metric | Value |
|---|---|
| Spec revisions | |
| Fix rounds | |
| Review findings: real / noise / deferred | |
| Regressions introduced | |
| Bugs escaped to production | |

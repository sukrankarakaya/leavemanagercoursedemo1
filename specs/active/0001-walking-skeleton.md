# Spec 0001 — walking skeleton

- Status: In progress
- Mode: lite
- Plan: `specs/plans/0001-plan.md`
- Self-critique: done

## Intent
Geliştirici (ve kursu izleyenler), izin özelliklerine başlamadan önce uçtan uca çalışan en küçük
dilimi istiyor: tarayıcıda açılan bir sayfa, sunucunun ve veritabanının ayakta olduğunu kendisine
sorarak gösterir. Başarı: aynı tek doğrulama komutu (`./scripts/check`) hem geliştirici makinesinde
(Windows) hem CI'da (Linux) bootstrap'ta planlanan tüm adımları gerçekten çalıştırır ve yeşil verir;
böylece sonraki her özellik hazır bir araç zinciri, katman yapısı ve test düzeni üzerine kurulur.
Bilerek yapılmayan: hiçbir izin özelliği (talep, onay, bakiye), giriş/oturum, kullanıcı ve rol
yönetimi, arayüz tasarımı.

## Requirements
- R-1: Sistem, kendisine sorulduğunda çalışır durumda olup olmadığını ve veritabanına erişip
  erişemediğini bildirir; yanıt sunucunun o anki zamanını (UTC) içerir.
- R-2: Veritabanına erişilemiyorsa sistem bunu "bozuk" durumu olarak bildirir; iç ayrıntıları
  (dosya yolu, hata metni, yığın izi) dışarı vermez, standart hata biçimini kullanır
  (`docs/conventions.md`, Error handling).
- R-3: Sistem ilk çalıştırıldığında boş bir veritabanını kayıtlı şema geçmişinden en güncel sürüme
  kurar; tekrar çalıştırıldığında yapılacak değişiklik bulmaz. Her veritabanı bağlantısında ilişki
  bütünlüğü zorlaması açıktır.
- R-4: Kullanıcı ana sayfayı açtığında sistemin durumunu Türkçe görür.
- R-5: "Bugün/şimdi" bilgisi tek bir saat kaynağından gelir ve testlerde sabitlenebilir
  (`docs/conventions.md`, Data rules).
- R-6: Doğrulama komutu bootstrap'ta planlanan adımları (lint, format, tip, mimari, unit, arayüz
  mantığı, integration, kapsam, bağımlılık taraması) çalıştırır; her test katmanından en az bir test
  gerçekten koşar. Yasak bağımlılık kurallarından (`docs/architecture.md`) birinin ihlali doğrulamayı
  kırmızıya düşürür.
- R-7: Aynı doğrulama komutu Windows geliştirici makinesinde ve CI'da (Linux) değişiklik yapmadan çalışır.

## User experience
- Flow: Kullanıcı uygulamanın ana sayfasını tarayıcıda açar → sayfa sistemin durumunu sorar →
  sonucu gösterir. Başka etkileşim yok.
- States:
  - **Yükleniyor:** "Sistem durumu kontrol ediliyor…"
  - **Başarılı:** "Sistem çalışıyor" + veritabanı durumu "erişilebilir" + sunucu zamanı (sunucunun
    döndürdüğü UTC ISO 8601 değeri olduğu gibi, "UTC" etiketiyle; yerel saate çevrilmez).
  - **Hata (sistem bozuk veya yanıt alınamadı):** "Sistem şu anda kullanılamıyor" — teknik ayrıntı
    gösterilmez.
  - Boş durum / yetki yok: uygulanmaz (veri ve giriş yok).
- Design reference: none — the flow above is the design.
- Accessibility: sayfa `lang="tr"`; durum metni ekran okuyucuya duyurulur (canlı bölge); yalnızca
  renkle anlam verilmez (metin her durumda var); metin kontrastı WCAG AA.

## Constraints & out of scope
- Sensitive area: none — bu spec yetki, bakiye veya kişisel veriye dokunmaz.
- Araçlar ve sürümler ADR 0001 ve `docs/conventions.md`'deki gibidir; yeni bağımlılık eklenmez
  (listede olanlar dışında).
- Gizli bilgi repoya girmez; yalnızca sahte değerli örnek ortam dosyası bulunur.
- Kaynak hijyeni: doğrulama arkasında süreç ve veri bırakmaz (residue testi BUILD'in Done'ının
  parçasıdır, kabul kriteri değildir — `docs/testing.md`).
- Önkoşul: VERIFY'dan önce GitHub push erişimi çalışır olmalı (AC-9 CI çalıştırması gerektirir);
  çalışmazsa AC-9 SHIP'te R-08 ile taşınır, asla feragat edilmez.
- Full profil ağ erişimi gerektirir (bağımlılık taraması); fast profil gerektirmez.
- Arayüz durumları (AC-4…AC-6), durumu ekran metnine çeviren saf mantıkla test edilir; görsel kanıt
  VERIFY'da ekran görüntüsüdür ("Yükleniyor" için gecikmeli yanıt stub'ı) — `docs/testing.md`.
- Kapsam dışı: izin alanı modelleri, giriş/oturum, kullanıcılar ve roller, CSS tasarımı ötesinde
  görsel çalışma, dağıtım (deploy), Docker.

## Acceptance criteria
- [ ] AC-1 — Sistem ve veritabanı ayaktayken durum sorgusu "çalışıyor", veritabanı "erişilebilir" ve
  sabit saat kaynağının verdiği zamanı UTC ISO 8601 olarak döner (R-1, R-5).
- [ ] AC-2 — Veritabanına erişilemezken durum sorgusu "bozuk" durumunu standart hata biçiminde, başarısız
  bir durum kodu ve sabit bir hata koduyla döner; yanıtta dosya yolu, hata metni veya yığın izi yoktur (R-2).
- [ ] AC-3 — İlk çalıştırma boş veritabanında şemayı en güncel sürüme kurar; ikinci çalıştırma yapılacak
  değişiklik bulmaz ve şema sürüm bilgisini değiştirmez; açılan her veritabanı bağlantısında ilişki
  bütünlüğü zorlaması açıktır (R-3).
- [ ] AC-4 — Ana sayfa, yanıt gelmeden önce "Yükleniyor" durumunu gösterir (R-4).
- [ ] AC-5 — Başarılı yanıtta ana sayfa "Sistem çalışıyor", veritabanı durumu ve sunucu zamanını
  (UTC ISO 8601, olduğu gibi, "UTC" etiketiyle) gösterir (R-4).
- [ ] AC-6 — Hata yanıtında veya yanıt alınamadığında ana sayfa "Sistem şu anda kullanılamıyor"
  gösterir, teknik ayrıntı göstermez (R-4).
- [ ] AC-7 — `./scripts/check` (full ve `--fast`) planlanan adımların tümünü çalıştırır ve yeşildir;
  unit, integration ve arayüz mantığı katmanlarının her birinde çalışan test sayısı > 0'dır (R-6).
- [ ] AC-8 — `docs/architecture.md`'deki yasak bağımlılıklardan birinin bilerek ihlali
  `./scripts/check`'i kırmızıya düşürür (R-6).
- [ ] AC-9 — `./scripts/check` full profili CI'da (Linux) da yeşildir, aynı `check.conf` ile (R-7).

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

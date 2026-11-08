# Security

> Her plan ve review'da uyulması gereken temel kurallar (bootstrap 2026-11-08).

## Secrets
- Secrets never enter the repo, specs, prompts, or chat. `.env` is gitignored; provide `.env.example`.
- Agents never print secret values, even when debugging.
- Oturum imzalama anahtarı (`SECRET_KEY`) ve DB yolu `.env`'den okunur; repoda yalnızca
  `.env.example` (sahte değerlerle) bulunur.

## Input & output
- Tüm girdiler sınırda (`api`) Pydantic v2 şemalarıyla doğrulanır; bilinmeyen alanlar reddedilir
  (`extra="forbid"`). Doğrulama hatası 422 + standart hata gövdesi (`docs/conventions.md`).
- API yalnızca `application/json` kabul eder ve döner.
- SQL yalnızca SQLAlchemy ifadeleri/parametreleriyle; string birleştirme veya f-string ile SQL yasak.
- Frontend kullanıcı verisini `textContent`/`createElement` ile basar; `innerHTML`, `eval`,
  `new Function` kullanıcı verisiyle yasak.
- Hata yanıtlarına stack trace, SQL, dosya yolu, iç kimlik bilgisi sızmaz.
- Log'lara parola, oturum kimliği/cookie, izin gerekçesi metni ve `SICK` ek bilgisi yazılmaz; kişi
  yerine kullanıcı ID'si loglanır.
- Repoya gerçek kişisel veri girmez; test ve demo verisi uydurmadır.

## AuthN / AuthZ
- **Kimlik doğrulama:** e-posta + parola; parolalar `argon2-cffi` (Argon2id) ile hash'lenir.
  Başarısız girişte genel mesaj ("e-posta veya parola hatalı").
- **Oturum:** sunucu tarafında tutulur; tarayıcıda yalnızca rastgele oturum kimliği, cookie
  `HttpOnly` + `SameSite=Strict` (+ canlıda `Secure`). Çıkışta oturum sunucuda silinir. JWT yok.
- **CSRF:** `SameSite=Strict` + yalnızca JSON isteği (form-encoded reddedilir) MVP için yeterli.
- **Yetkilendirme sunucuda, `services` katmanında** yapılır; arayüzde buton gizlemek güvenlik değildir.
- **Varsayılan reddet:** açıkça izin verilmeyen her işlem reddedilir. Yetki matrisi:
  - Çalışan: kendi taleplerini oluşturur, görür, iptal eder (BR-6); kendi bakiyesini görür.
  - Yönetici: ek olarak ekibinin taleplerini görür, onaylar/reddeder (BR-4); kendi talebini onaylayamaz.
  - İK: izin türleri, yıllık haklar, resmî tatiller, bakiye düzeltmeleri; tüm talepleri görür;
    talep onaylamaz.
- Erişim hakkı olmayan bir kayda istek **404** döner (403 değil) — kaydın varlığı sızmaz.
  Rolün hiç izinli olmadığı bir işlem (ör. çalışanın İK ucu) 403 döner.
- `SICK` taleplerinin gerekçe/ek alanları yalnızca talep sahibi, yöneticisi ve İK'ya döner (KVKK).

## Dependencies
- Yeni bir üçüncü parti kütüphane yalnızca spec veya planda gerekçesiyle yazılıp insan onayından
  sonra eklenir. Kontrol edilenler: lisans (MIT/BSD/Apache-2.0 uyumlu), aktif bakım (son 12 ayda
  sürüm), bilinen açık (`pip-audit`).
- Bakımı durmuş paket kullanılmaz (ör. `passlib` → yerine `argon2-cffi`).
- Kesin sürümler `requirements.lock`'ta sabitlenir; `pip-audit` full profilde check adımıdır.
- Frontend'de üçüncü parti JS/CSS (CDN dahil) yok.

## Review lens
Security is a mandatory dimension of every independent review (see `prompts/review.md`), not a
separate afterthought phase.

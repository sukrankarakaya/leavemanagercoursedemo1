# Architecture

> Kararlaştırılmış mimari (bootstrap 2026-11-08). Ajanlar planlamadan önce bu dosyayı okur.

## System overview
İzin Yöneticisi, tek bir **FastAPI** uygulamasından oluşan **katmanlı bir monolittir**. Uygulama hem
JSON REST API'yi (`/api/...`) hem de build adımı olmayan saf HTML/CSS/JS arayüzünü (statik dosya)
sunar. Veri tek bir **SQLite** dosyasında, **SQLAlchemy 2.0** ORM ile tutulur; şema değişiklikleri
**Alembic** migration'larıyla yapılır. İş kuralları HTTP ve veritabanından bağımsız `services` ve
`domain` katmanlarında toplanır, böylece hassas alanlar hızlı unit testlerle kanıtlanır.
Gerekçe: tek geliştiricili kurs/demo MVP'si için en az hareketli parça — ADR
[0001](decisions/0001-stack-and-layered-monolith.md).

## Modules / components and ownership

| Module | Single responsibility | Owns |
|---|---|---|
| `app/api/` | HTTP katmanı: router'lar, istek/yanıt şemaları (Pydantic), oturum/kimlik bağımlılıkları, hata → HTTP çevirisi | HTTP sözleşmesi (uç adresleri, yanıt biçimi) |
| `app/services/` | Kullanım senaryoları ve iş kuralları (BR-1…BR-8), yetki kontrolleri, transaction sınırı | İş akışları: talep oluşturma, onay/ret, iptal, bakiye |
| `app/domain/` | Saf modeller ve hesaplar: iş günü hesabı, durum geçişleri, bakiye formülü, `Clock` arayüzü, tipli hatalar | Alan kavramları ve değişmezler |
| `app/repositories/` | Veri erişimi: SQLAlchemy sorguları, domain nesnesi ↔ ORM satırı dönüşümü | Sorgular |
| `app/db/` | SQLAlchemy modelleri, engine/oturum kurulumu (PRAGMA'lar), Alembic migration'ları | Şema ve kalıcı veri |
| `app/main.py` | Uygulama kurulumu: router'ları bağlama, statik dosyaları sunma, ayarlar | Uygulama yaşam döngüsü |
| `app/cli.py` | Yönetim komutları (ikinci composition root): ilk İK hesabı (spec 0002) | — |
| `web/` | Tarayıcı arayüzü: HTML sayfaları, CSS, ES module JS; DOM'a dokunmayan mantık ayrı modüllerde | Sunum ve arayüz durumu |
| `tests/` | `unit/` (domain, services) · `integration/` (api + gerçek SQLite) · `web/` (`node --test`) | Test verisi (uydurma) |

## Communication rules
- Bağımlılık yönü tek yönlüdür: `api → services → domain`; `services → repositories → db`.
  `repositories` domain tiplerini kullanabilir (döndürür/alır).
- Katmanlar arası iletişim doğrudan fonksiyon çağrısıdır; olay/mesaj kuyruğu yoktur (MVP).
- Transaction sınırı `services` katmanındadır: bir kullanım senaryosu = bir DB transaction'ı.
  Servisler `UnitOfWork` arayüzüyle (`app/services/ports.py`) çalışır; somut `SqlUnitOfWork`
  (`app/repositories/unit_of_work.py`) yazma kilidini transaction başında alır (SQLite `BEGIN IMMEDIATE`).
- `web/` backend ile **yalnızca** `/api/...` JSON uçları üzerinden `fetch` ile konuşur.
- `app/main.py` ve `app/cli.py` composition root'tur: somut repository/UoW/hasher'ı yalnızca onlar bağlar.
- `api` katmanı `services`'i FastAPI dependency'leri ile alır; testlerde bunlar override edilir
  (ör. sabit `Clock`, geçici DB).

## Forbidden dependencies (make them testable)
1. `app/domain` hiçbir `app.*` katmanını ve hiçbir framework'ü import etmez (FastAPI, Starlette,
   SQLAlchemy, Pydantic yok) — yalnızca standart kütüphane.
2. `app/api` doğrudan `app/repositories` veya `app/db` import etmez; her erişim `app/services` üzerinden.
3. `app/services` FastAPI/Starlette import etmez (`Request`, `HTTPException`, `Depends` yalnızca `api`'de).
4. `app/repositories` ve `app/db`, `app/services` veya `app/api` import etmez.
5. `web/` yalnızca `/api/...` uçlarını çağırır; backend HTML üretmez (sunucu tarafı şablon yok).
6. `app/` içinde döngüsel import yoktur.

Bu kurallar `import-linter` sözleşmesiyle `scripts/check` adımı olarak zorlanacaktır (walking
skeleton'da etkinleşir; `scripts/check.conf`).

## Deliberately out of scope
- E-posta / anlık bildirim, takvim entegrasyonu, çoklu şirket (multi-tenant).
- Yarım gün izin, yıldan yıla devreden bakiye.
- Parola sıfırlama, 2FA, giriş denemesi sınırlama (`specs/backlog.md`).
- Frontend build zinciri (npm, bundler, framework), sunucu tarafı şablon, SPA router kütüphanesi.
- Ayrı servisler, mesaj kuyruğu, önbellek sunucusu, Docker.

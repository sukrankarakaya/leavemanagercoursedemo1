# ADR 0001 — Python/FastAPI + SQLite + saf HTML/CSS/JS, katmanlı monolit

- Status: Accepted
- Date: 2026-11-08

## Context
İzin Yöneticisi, tek geliştiricili bir kurs/demo MVP'sidir: tek şirket, üç rol (Çalışan, Yönetici,
İK), gerçek iş kuralları (iş günü, bakiye, çakışma, onay akışı) ve üç hassas alan (yetki, bakiye,
kişisel veri). Geliştirme makinesi Windows; Docker yok, Python 3.12 kurulu. Hedef: az hareketli
parça, hızlı ve deterministik testler, ANEW sürecinin (spec → plan → build → review → verify)
öğretilebilir olması.

## Decision
Backend Python 3.12 + FastAPI, veri SQLite + SQLAlchemy 2.0 (+ Alembic), arayüz build adımı olmayan
saf HTML/CSS/JS; tümü tek bir FastAPI uygulamasında `api → services → domain` (+ `repositories → db`)
katmanlarıyla, yasak bağımlılıklar `import-linter` ile zorlanarak.

## Consequences
- Kazanç: Kurulum yok denecek kadar az (Python + venv); DB sunucusu/Docker gerekmez; her test kendi
  geçici SQLite'ını kullanır (kaynak hijyeni kolay). İş kuralları framework'süz `domain`/`services`
  katmanında hızlı unit testlerle kanıtlanır. Frontend için npm/bundler bakımı yok.
- Maliyet: İki dil (Python + JS); JS tarafında tip kontrolü ve bileşen test framework'ü yok — arayüz
  mantığını saf modüllere ayırma disiplini gerekir. SQLite eşzamanlı yazmada sınırlı (MVP için yeterli).
  Saf JS ile büyüyen bir arayüz zamanla elle yönetilen durum karmaşasına dönüşebilir.

## Alternatives considered
- **TypeScript full-stack (Node 24 + Fastify + React/Vite):** tek dil avantajı; ama Node 24 kurulumu,
  npm bağımlılık zinciri ve frontend build gerektirir. İnsanın tercihi Python/FastAPI oldu.
- **.NET 10 + ASP.NET Core:** sağlam tip sistemi; ama kurulu .NET 8'in desteği bitiyor, .NET 10
  kurulumu ve arayüz için ikinci bir araç zinciri gerekir.
- **Hexagonal/modüler monolit veya mikroservis:** bu boyut için fazla tören; katmanlı yapı aynı test
  edilebilirliği daha az kavramla sağlar.

## Revisit triggers
- Eşzamanlı kullanıcı sayısı SQLite yazma kilidini sorun haline getirirse (→ PostgreSQL).
- Arayüz durum yönetimi saf JS ile zorlaşırsa veya bileşen testleri gerekirse (→ hafif framework + build).
- Çoklu şirket, bildirim veya entegrasyonlar kapsama girerse (→ modül sınırlarını yeniden düşün).

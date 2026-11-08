# Conventions

> Yalnızca gerçek kurallar: her kural ya araçla zorlanır (tercih edilen) ya da review'da kontrol edilir.

## Language
<!-- Set at bootstrap (step 0) and mirrored in AGENTS.md. Changing it later is allowed — edit both
     places; existing documents are not translated retroactively. -->
- Chat language (interviews, sessions): Türkçe (`tr`)
- Document language (docs/, specs, plans, ADRs, review and verify reports): Türkçe (`tr`)
- Always English (protocol, not prose): ANEW core files, template headings and field labels,
  `Status:` values (Draft / Approved / In progress / Shipped), `Approved by / on:`, `Source:`.
- Code identifiers, branch names, commit messages: kod tanımlayıcıları, tablo/alan adları, API alan
  adları ve dal adları **İngilizce**; commit'te tür ve kapsam İngilizce (`feat(leave): …`),
  açıklama **Türkçe**. Kullanıcıya görünen arayüz metinleri **Türkçe**.
- Agent messages (handoff summaries, refusals, `Next:` lines): chat language; command names, file
  paths and protocol fields verbatim.

## Language & framework versions
- Python **3.12** (`requires-python = ">=3.12,<3.13"`), sanal ortam: `.venv` (`python -m venv .venv`).
- FastAPI (güncel 0.1xx) + Uvicorn · Pydantic **v2** · SQLAlchemy **2.0** · Alembic · SQLite (stdlib `sqlite3`).
- Test: pytest + FastAPI `TestClient` (httpx) + pytest-cov · Lint/format: Ruff · Tip: mypy.
- Parola: `argon2-cffi`. Bağımlılık taraması: `pip-audit`. Mimari sözleşme: `import-linter`.
- Frontend: saf HTML/CSS/JavaScript (ES modules, ES2022), build yok; JS testleri `node --test`
  (Node ≥ 20, npm paketi yok).
- Bağımlılıklar `pyproject.toml`'da tanımlanır, kesin sürümler `requirements.lock`'ta sabitlenir.
- Kurulum: `tools/setup` (lock'tan) · lock yenileme: `tools/setup --lock`. Python araçları her
  platformda `tools/venv <komut>` ile çalışır (ör. `tools/venv python -m pytest`); uygulama:
  `tools/venv uvicorn app.main:create_app --factory`. Kök `package.json` yalnızca ESM bildirir (A-1).

## Naming
- Python: PEP 8 — `snake_case` modül/fonksiyon/değişken, `PascalCase` sınıf, `UPPER_SNAKE` sabit.
- JS: `camelCase` fonksiyon/değişken, `PascalCase` sınıf; dosyalar `kebab-case.js`.
- Domain terimleri `docs/domain.md` sözlüğündeki İngilizce karşılıklarıyla adlandırılır
  (`LeaveRequest`, `Balance`, `Workday`); sözlükte olmayan yeni terim önce sözlüğe eklenir.
- Enum değerleri `UPPER_SNAKE` (`PENDING`, `ANNUAL`); DB'de string olarak saklanır.
- DB tabloları çoğul `snake_case` (`leave_requests`).
- REST: çoğul, `kebab-case` kaynak adları; eylemler alt kaynak: `POST /api/leave-requests/{id}/approve`.
  JSON alan adları `snake_case`.
- Testler: `tests/<katman>/test_<modül>.py`, fonksiyonlar `test_<davranış>` — ilgili kural varsa
  adında geçer (`test_br3_overlapping_pending_request_is_rejected`). JS: `tests/web/<modül>.test.js`.
- Tüm public Python fonksiyonlarında tip ipuçları zorunlu.

## Error handling
- İş kuralı ihlalleri `app/domain/errors.py`'deki tipli istisnalardır (ör. `InsufficientBalanceError`,
  `OverlappingRequestError`, `InvalidTransitionError`, `NotAuthorizedError`, `NotFoundError`) ve
  `services`'ten fırlatılır. Her birinin sabit bir `code`'u vardır (`INSUFFICIENT_BALANCE`).
- `api` katmanında **tek** exception handler bunları HTTP'ye çevirir: doğrulama 422, iş kuralı 409
  (çakışma/geçersiz geçiş) veya 400, yetkisiz 403, bulunamadı/erişimi olmayan kayıt 404
  (`docs/security.md`), oturum yok 401.
- Hata gövdesi her zaman: `{"error": {"code": "<CODE>", "message": "<Türkçe, kullanıcıya uygun>"}}`.
- Beklenmeyen hata → 500 ve genel mesaj; stack trace, SQL, dosya yolu istemciye **asla** gitmez,
  yalnızca log'a yazılır.
- Hatalar sessizce yutulmaz: çıplak `except:` ve `except Exception: pass` yasak (Ruff `E722`, `S110`).
- Frontend her `fetch` hatasını `error.code`'a göre kullanıcıya Türkçe mesajla gösterir.

## Data rules
- İzin tarihleri `datetime.date` (saatsiz); API'de ISO 8601 (`2026-11-08`).
- Zaman damgaları (denetim, oluşturulma) timezone-aware **UTC** `datetime`; API'de ISO 8601 `Z`'li.
- "Bugün" ve "şimdi" yalnızca `Clock` arayüzünden okunur (`app/domain/clock.py`); `date.today()`,
  `datetime.now()` doğrudan çağrılmaz. Testlerde sabit `Clock` verilir.
- Gün sayıları ve bakiyeler `int` (MVP'de yarım gün yok); float kullanılmaz.
- Kimlikler `UUID` v4; dışarıya sıralı/tahmin edilebilir ID açılmaz.
- Durum ve türler Python `Enum`; DB'de string.
- Parolalar yalnızca Argon2 hash olarak saklanır.

## Known traps
- SQLite foreign key'leri varsayılan kapalı — her bağlantıda `PRAGMA foreign_keys=ON` (SQLAlchemy `connect` event) — from bootstrap 2026-11-08.
- SQLite eşzamanlılık — `check_same_thread=False`; bellek içi DB testlerinde `StaticPool` (aksi halde her bağlantı ayrı boş DB görür) — from bootstrap 2026-11-08.
- Naive/aware `datetime` karışması — `datetime.utcnow()` yok; `datetime.now(timezone.utc)` yalnızca `Clock` içinde — from bootstrap 2026-11-08.
- `async def` endpoint içinde senkron DB çağrısı event loop'u kilitler — DB kullanan endpoint'ler düz `def` — from bootstrap 2026-11-08.
- Pydantic v1 sözdizimi (`.dict()`, `class Config`, `orm_mode`) — v2: `.model_dump()`, `model_config`, `from_attributes` — from bootstrap 2026-11-08.
- Windows yol/satır sonu farkları — yollar için `pathlib`; script'ler `.gitattributes` ile LF — from bootstrap 2026-11-08.
- Kullanıcı verisini `innerHTML` ile basmak XSS'tir — `textContent` / `createElement` kullan — from bootstrap 2026-11-08.
- Tarih aralığında off-by-one — BR-1 başlangıç ve bitiş dahil; sınır günleri için test zorunlu — from bootstrap 2026-11-08.

## Enforced by tooling
<!-- Walking skeleton bu araçları scripts/check.conf'ta etkinleştirdiğinde geçerli olur. -->
- Ruff lint: PEP 8, import sırası, `E722`/`S110` (yutulan hatalar), `DTZ` (naive datetime),
  `S608` (string ile SQL), Bandit kuralları (`S`).
- Ruff format: biçim tartışılmaz.
- mypy (`strict`): tip ipuçları zorunlu, `Any` sızıntısı.
- import-linter: `docs/architecture.md` "Forbidden dependencies" 1–6.
- pip-audit: bilinen açığı olan bağımlılık.

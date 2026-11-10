# Backlog — deferred findings

Findings a human triaged as **defer**: real, but fixed later by decision (`workflows/feature-development.md`,
step 7). Nothing lands here without that decision; noise is rejected in the triage record, not parked here.

- A criterion moved out at the ship gate (R-08, `→ moved to B-<n>`) lands here too, by the
  human's ship decision; the entry names the spec and criterion.
- One entry per finding, newest last. Delete the entry in the commit of the work that closes it.
- An entry that grows into new behavior becomes a spec (`specs/active/`), not a fix.

<!-- Format (labels stay English):
- **B-<n>** — <finding, one line> — Source: spec <NNNN>, review round <n> (<file:line>) — Severity: <…>
  — Recommendation: <the reviewer's action> — Deferred by: <name>, <YYYY-MM-DD>, <why>
  A decision deferred at bootstrap (its REPORT) uses Source: bootstrap <YYYY-MM-DD>.
-->

- **B-1** — Giriş denemesi sınırlama (rate limit / brute-force koruması) yok — Source: bootstrap 2026-11-08 — Severity: Medium
  — Recommendation: MVP sonrası ayrı spec (hassas alan: Yetkilendirme) — Deferred by: sukrankarakaya, 2026-11-08, MVP demo kapsamı dışında
- **B-2** — Parola sıfırlama akışı yok — Source: bootstrap 2026-11-08 — Severity: Low
  — Recommendation: MVP sonrası ayrı spec; e-posta altyapısı gerektirir — Deferred by: sukrankarakaya, 2026-11-08, MVP demo kapsamı dışında
- **B-3** — İki adımlı doğrulama (2FA) yok — Source: bootstrap 2026-11-08 — Severity: Low
  — Recommendation: gerçek kullanıma geçilirse ayrı spec — Deferred by: sukrankarakaya, 2026-11-08, MVP demo kapsamı dışında
- **B-4** — Starlette ≥1.x `TestClient` httpx yerine httpx2 bekliyor (StarletteDeprecationWarning); lock yenilemesi integration testlerini kırabilir — Source: spec 0001, review round 1 (`requirements.lock:21`) — Severity: Low
  — Recommendation: httpx2'ye geçiş + `docs/conventions.md` güncellemesi (gerekirse ADR notu); uyarı susturulmaz — Deferred by: sukrankarakaya, 2026-11-09, spec 0001 "yeni bağımlılık yok"

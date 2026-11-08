// AC-4, AC-5, AC-6: arayüz durumları → ekran metni.
import assert from "node:assert/strict";
import test from "node:test";

import { TEXT, healthView, stateFromResponse } from "../../web/health-view.js";

const OK_BODY = { status: "ok", database: "ok", server_time: "2026-11-08T09:30:00Z" };

test("loading state shows the checking message", () => {
  assert.deepEqual(healthView({ kind: "loading" }), {
    tone: "loading",
    title: "Sistem durumu kontrol ediliyor…",
    details: [],
  });
});

test("ok state shows running, database and server time as returned with UTC label", () => {
  const view = healthView(stateFromResponse({ status: 200, body: OK_BODY }));
  assert.deepEqual(view, {
    tone: "ok",
    title: "Sistem çalışıyor",
    details: ["Veritabanı: erişilebilir", "Sunucu zamanı (UTC): 2026-11-08T09:30:00Z"],
  });
});

test("error state for an error response shows no technical detail", () => {
  const body = { error: { code: "DB_UNAVAILABLE", message: "Sistem şu anda kullanılamıyor." } };
  const view = healthView(stateFromResponse({ status: 503, body }));
  assert.deepEqual(view, { tone: "error", title: TEXT.error, details: [] });
  assert.equal(view.title, "Sistem şu anda kullanılamıyor");
  assert.ok(!JSON.stringify(view).includes("DB_UNAVAILABLE"));
});

test("network failure (no response) shows the error state", () => {
  assert.deepEqual(stateFromResponse(null), { kind: "error" });
  assert.equal(healthView(stateFromResponse(null)).tone, "error");
});

test("unexpected 200 body is treated as error, not as ok", () => {
  for (const body of [null, "ok", {}, { ...OK_BODY, database: "down" }, { ...OK_BODY, server_time: 1 }]) {
    assert.deepEqual(stateFromResponse({ status: 200, body }), { kind: "error" });
  }
});

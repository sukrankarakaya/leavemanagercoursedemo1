// Saf arayüz mantığı: DOM'a dokunmaz, `node --test` ile test edilir (docs/testing.md).
// Durum: { kind: "loading" } | { kind: "ok", serverTime } | { kind: "error" }

export const TEXT = Object.freeze({
  loading: "Sistem durumu kontrol ediliyor…",
  ok: "Sistem çalışıyor",
  databaseOk: "Veritabanı: erişilebilir",
  serverTimeLabel: "Sunucu zamanı (UTC)",
  error: "Sistem şu anda kullanılamıyor",
});

/**
 * HTTP yanıtını arayüz durumuna çevirir.
 * @param {{ status: number, body: unknown } | null} response — null: ağ hatası, yanıt yok
 */
export function stateFromResponse(response) {
  if (response === null || response.status !== 200) return { kind: "error" };
  const body = response.body;
  if (
    body !== null &&
    typeof body === "object" &&
    body.status === "ok" &&
    body.database === "ok" &&
    typeof body.server_time === "string"
  ) {
    return { kind: "ok", serverTime: body.server_time };
  }
  return { kind: "error" };
}

/**
 * Arayüz durumunu ekranda gösterilecek metinlere çevirir. Sunucu zamanı olduğu gibi gösterilir.
 * @returns {{ tone: "loading" | "ok" | "error", title: string, details: string[] }}
 */
export function healthView(state) {
  switch (state.kind) {
    case "loading":
      return { tone: "loading", title: TEXT.loading, details: [] };
    case "ok":
      return {
        tone: "ok",
        title: TEXT.ok,
        details: [TEXT.databaseOk, `${TEXT.serverTimeLabel}: ${state.serverTime}`],
      };
    default:
      return { tone: "error", title: TEXT.error, details: [] };
  }
}

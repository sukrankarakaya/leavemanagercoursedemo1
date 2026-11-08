// DOM bağlama. Kullanıcıya/sunucuya ait metin yalnızca textContent ile basılır (Known traps 7).
import { healthView, stateFromResponse } from "./health-view.js";

const region = document.getElementById("health");
// Takılan istek "Yükleniyor"da bırakmasın: süre dolunca hata durumu gösterilir (AC-6).
const REQUEST_TIMEOUT_MS = 10_000;

function render(view) {
  region.dataset.tone = view.tone;
  const title = document.createElement("p");
  title.className = "health-title";
  title.textContent = view.title;
  const items = view.details.map((detail) => {
    const item = document.createElement("li");
    item.textContent = detail;
    return item;
  });
  const list = document.createElement("ul");
  list.className = "health-details";
  list.replaceChildren(...items);
  region.replaceChildren(title, list);
}

async function fetchHealth() {
  try {
    const response = await fetch("/api/health", {
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    let body = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }
    return { status: response.status, body };
  } catch {
    return null;
  }
}

render(healthView({ kind: "loading" }));
render(healthView(stateFromResponse(await fetchHealth())));

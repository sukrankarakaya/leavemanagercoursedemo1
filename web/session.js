// fetch sarmalayıcı + oturum yönlendirmesi + üst çubuk (DOM bağlama). Metinler yalnızca
// textContent ile basılır (Known traps 7). Arka planda periyodik istek YOK (spec 0002, R-8).
import { LOGIN_PAGE, redirectFor } from "./auth-view.js";
import { topbarView } from "./topbar-view.js";

const TIMEOUT_MS = 10_000;

/** JSON istek; 401/403-parola durumunda yönlendirir. Ağ hatasında null döner. */
export async function api(path, { method = "GET", body, redirect = true } = {}) {
  let response;
  try {
    response = await fetch(path, {
      method,
      credentials: "same-origin",
      headers: { Accept: "application/json", ...(method === "GET" ? {} : { "Content-Type": "application/json" }) },
      body: method === "GET" ? undefined : JSON.stringify(body ?? {}),
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
  } catch {
    return null;
  }
  let data = null;
  if (response.status !== 204) {
    try {
      data = await response.json();
    } catch {
      data = null;
    }
  }
  const code = data && data.error ? data.error.code : undefined;
  const target = redirect ? redirectFor(response.status, code) : null;
  if (target) {
    window.location.assign(target);
    return new Promise(() => {}); // sayfa değişiyor
  }
  return { status: response.status, body: data };
}

/** Korumalı sayfa girişi: oturum yoksa yönlendirir; varsa kullanıcıyı döner ve üst çubuğu çizer. */
export async function requireUser() {
  const result = await api("/api/auth/me");
  if (result === null || result.status !== 200) {
    window.location.assign(LOGIN_PAGE);
    return new Promise(() => {});
  }
  renderTopbar(result.body);
  return result.body;
}

export function renderTopbar(me) {
  const bar = document.getElementById("topbar");
  if (!bar) return;
  const view = topbarView(me);
  const nav = document.createElement("nav");
  nav.setAttribute("aria-label", "Ana menü");
  for (const link of view.links) {
    const a = document.createElement("a");
    a.href = link.href;
    a.textContent = link.label;
    nav.append(a);
  }
  const who = document.createElement("span");
  who.className = "topbar-user";
  who.textContent = `${view.name} · ${view.role}`;
  const logout = document.createElement("button");
  logout.type = "button";
  logout.textContent = view.logoutLabel;
  logout.addEventListener("click", async () => {
    await api("/api/auth/logout", { method: "POST", redirect: false });
    window.location.assign(LOGIN_PAGE);
  });
  bar.replaceChildren(nav, who, logout);
  bar.hidden = false;
}

/** Form alanı hata metnini bağlar (aria-describedby + aria-invalid). */
export function showFieldErrors(form, fieldErrors) {
  for (const input of form.querySelectorAll("input, select")) {
    const slot = document.getElementById(`${input.name}-error`);
    const message = fieldErrors[input.name] || "";
    if (slot) slot.textContent = message;
    if (message) input.setAttribute("aria-invalid", "true");
    else input.removeAttribute("aria-invalid");
  }
}

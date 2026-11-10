// Saf arayüz mantığı: üst çubuk (ad, rol, bağlantılar) — DOM'a dokunmaz (AC-22).

import { roleLabel } from "./users-view.js";

export function topbarView(me) {
  const links = [{ href: "/", label: "Ana sayfa" }];
  if (me.role === "HR") links.push({ href: "/users.html", label: "Kullanıcılar" });
  return { name: me.full_name, role: roleLabel(me.role), links, logoutLabel: "Çıkış" };
}

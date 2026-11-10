// AC-22: üst çubuk ad, rol ve çıkışı gösterir; "Kullanıcılar" yalnızca İK'ya.
import assert from "node:assert/strict";
import test from "node:test";

import { topbarView } from "../../web/topbar-view.js";

test("HR sees the Users link", () => {
  assert.deepEqual(topbarView({ full_name: "İK Uzmanı", role: "HR" }), {
    name: "İK Uzmanı",
    role: "İK",
    links: [
      { href: "/", label: "Ana sayfa" },
      { href: "/users.html", label: "Kullanıcılar" },
    ],
    logoutLabel: "Çıkış",
  });
});

test("manager and employee do not see the Users link", () => {
  for (const role of ["MANAGER", "EMPLOYEE"]) {
    const view = topbarView({ full_name: "Kişi", role });
    assert.deepEqual(view.links, [{ href: "/", label: "Ana sayfa" }]);
    assert.equal(view.logoutLabel, "Çıkış");
  }
  assert.equal(topbarView({ full_name: "Y", role: "MANAGER" }).role, "Yönetici");
  assert.equal(topbarView({ full_name: "C", role: "EMPLOYEE" }).role, "Çalışan");
});

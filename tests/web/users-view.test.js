// AC-21: İK Kullanıcılar sayfası — liste, hata, yetki yok, oluşturma hataları, tek seferlik parola.
import assert from "node:assert/strict";
import test from "node:test";

import {
  createdNotice,
  createErrors,
  listState,
  managerOptions,
  TEXT,
  userRows,
} from "../../web/users-view.js";

const USERS = [
  { id: "h", email: "ik@firma.com", full_name: "İK Uzmanı", role: "HR", manager_id: null },
  { id: "m", email: "yonetici@firma.com", full_name: "Yönetici", role: "MANAGER", manager_id: null },
  { id: "e", email: "calisan@firma.com", full_name: "Çalışan", role: "EMPLOYEE", manager_id: "m" },
];

test("list, forbidden and error states", () => {
  assert.deepEqual(listState(200, USERS), { kind: "list", users: USERS });
  assert.deepEqual(listState(403, { error: { code: "FORBIDDEN" } }), { kind: "forbidden" });
  assert.deepEqual(listState(500, null), { kind: "error" });
  assert.deepEqual(listState(200, { not: "a list" }), { kind: "error" });
  assert.equal(TEXT.forbidden, "Bu sayfayı görüntüleme yetkiniz yok.");
});

test("rows show role labels and manager names", () => {
  assert.deepEqual(userRows(USERS), [
    { id: "h", name: "İK Uzmanı", email: "ik@firma.com", role: "İK", manager: "—" },
    { id: "m", name: "Yönetici", email: "yonetici@firma.com", role: "Yönetici", manager: "—" },
    { id: "e", name: "Çalışan", email: "calisan@firma.com", role: "Çalışan", manager: "Yönetici" },
  ]);
});

test("manager options are only managers", () => {
  assert.deepEqual(managerOptions(USERS), [{ value: "m", label: "Yönetici (yonetici@firma.com)" }]);
});

test("temp password is shown once with a warning", () => {
  const notice = createdNotice({ user: { email: "yeni@firma.com" }, temp_password: "AbcDef234567" });
  assert.deepEqual(notice, {
    title: "Kullanıcı oluşturuldu.",
    email: "yeni@firma.com",
    tempPassword: "AbcDef234567",
    warning: "Bu geçici parola bir daha gösterilmeyecek. Kullanıcıya güvenli bir yolla iletin.",
  });
});

test("create errors: per field, email taken, generic", () => {
  assert.deepEqual(
    createErrors(422, { error: { message: "Girilen bilgiler geçersiz.", fields: { full_name: "Ad soyad 1–100 karakter olmalıdır." } } }),
    { formError: "Girilen bilgiler geçersiz.", fields: { full_name: "Ad soyad 1–100 karakter olmalıdır." } },
  );
  assert.deepEqual(
    createErrors(409, { error: { code: "EMAIL_TAKEN", message: "Bu e-posta adresi zaten kayıtlı." } }),
    { formError: "", fields: { email: "Bu e-posta adresi zaten kayıtlı." } },
  );
  assert.deepEqual(createErrors(0, null), { formError: TEXT.error, fields: {} });
});

// AC-19 (yönlendirme, süresi doldu mesajı), AC-20 (giriş / parola değiştirme durumları).
import assert from "node:assert/strict";
import test from "node:test";

import {
  afterLogin,
  CHANGE_PASSWORD_PAGE,
  errorState,
  formView,
  loginNotice,
  redirectFor,
  TEXT,
} from "../../web/auth-view.js";

test("redirect on 401 codes", () => {
  assert.equal(redirectFor(401, "SESSION_EXPIRED"), "/login.html?expired=1");
  assert.equal(redirectFor(401, "UNAUTHENTICATED"), "/login.html");
  assert.equal(redirectFor(401, undefined), "/login.html");
  assert.equal(redirectFor(403, "PASSWORD_CHANGE_REQUIRED"), CHANGE_PASSWORD_PAGE);
  assert.equal(redirectFor(403, "FORBIDDEN"), null);
  assert.equal(redirectFor(422, "VALIDATION_ERROR"), null);
  assert.equal(redirectFor(200, undefined), null);
});

test("expired notice only for ?expired=1", () => {
  assert.equal(loginNotice("?expired=1"), "Oturumunuzun süresi doldu, lütfen tekrar giriş yapın.");
  assert.equal(loginNotice(""), "");
  assert.equal(loginNotice("?expired=0"), "");
});

test("after login: temp password goes to change-password, otherwise home", () => {
  assert.equal(afterLogin({ must_change_password: true }), "/change-password.html");
  assert.equal(afterLogin({ must_change_password: false }), "/");
});

test("login and change-password states", () => {
  assert.deepEqual(formView("login", { kind: "idle" }), {
    disabled: false, button: "Giriş yap", formError: "", fieldErrors: {}, status: "",
  });
  assert.deepEqual(formView("login", { kind: "submitting" }), {
    disabled: true, button: "Giriş yapılıyor…", formError: "", fieldErrors: {}, status: "",
  });
  const failed = errorState({
    error: { code: "INVALID_CREDENTIALS", message: "E-posta veya parola hatalı ya da çok fazla deneme yapıldı." },
  });
  assert.deepEqual(formView("login", failed), {
    disabled: false,
    button: "Giriş yap",
    formError: "E-posta veya parola hatalı ya da çok fazla deneme yapıldı.",
    fieldErrors: {},
    status: "",
  });
  assert.equal(formView("login", { kind: "success" }).status, TEXT.loginSuccess);

  const invalid = errorState({
    error: { code: "VALIDATION_ERROR", message: "Girilen bilgiler geçersiz.", fields: { new_password: "Parola 12–128 karakter olmalıdır." } },
  });
  assert.deepEqual(formView("change", invalid).fieldErrors, { new_password: "Parola 12–128 karakter olmalıdır." });
  assert.equal(formView("change", { kind: "idle" }).button, "Parolayı değiştir");
  assert.equal(formView("change", { kind: "submitting" }).disabled, true);
  assert.equal(formView("change", { kind: "success" }).status, TEXT.changeSuccess);
});

test("network failure or unexpected body falls back to a generic error", () => {
  assert.deepEqual(errorState(null), { kind: "error", message: TEXT.genericError, fields: {} });
  assert.deepEqual(errorState("oops"), { kind: "error", message: TEXT.genericError, fields: {} });
});

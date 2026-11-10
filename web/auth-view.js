// Saf arayüz mantığı (giriş, parola değiştirme, oturum yönlendirmesi) — DOM'a dokunmaz.

export const LOGIN_PAGE = "/login.html";
export const CHANGE_PASSWORD_PAGE = "/change-password.html";
export const HOME_PAGE = "/";

export const TEXT = Object.freeze({
  expired: "Oturumunuzun süresi doldu, lütfen tekrar giriş yapın.",
  genericError: "İşlem tamamlanamadı. Lütfen tekrar deneyin.",
  loginButton: "Giriş yap",
  loginSubmitting: "Giriş yapılıyor…",
  changeButton: "Parolayı değiştir",
  changeSubmitting: "Değiştiriliyor…",
  changeSuccess: "Parolanız değiştirildi. Yönlendiriliyorsunuz…",
  loginSuccess: "Giriş başarılı. Yönlendiriliyorsunuz…",
});

/** API hatasına göre gidilecek sayfa; yönlendirme gerekmiyorsa null (AC-19). */
export function redirectFor(status, code) {
  if (status === 401) return code === "SESSION_EXPIRED" ? `${LOGIN_PAGE}?expired=1` : LOGIN_PAGE;
  if (status === 403 && code === "PASSWORD_CHANGE_REQUIRED") return CHANGE_PASSWORD_PAGE;
  return null;
}

/** Giriş sayfasının üst bilgi mesajı (adres sorgusuna göre). */
export function loginNotice(search) {
  return new URLSearchParams(search).get("expired") === "1" ? TEXT.expired : "";
}

/** Başarılı girişten sonra gidilecek sayfa. */
export function afterLogin(body) {
  return body && body.must_change_password ? CHANGE_PASSWORD_PAGE : HOME_PAGE;
}

/** Hata yanıtını form durumuna çevirir: genel mesaj + alan bazında mesajlar. */
export function errorState(body) {
  const error = body && typeof body === "object" ? body.error : null;
  return {
    kind: "error",
    message: (error && typeof error.message === "string" && error.message) || TEXT.genericError,
    fields: (error && error.fields && typeof error.fields === "object" && error.fields) || {},
  };
}

/**
 * Form durumu → görünüm. state.kind: idle | submitting | error | success
 * @param {"login"|"change"} form
 */
export function formView(form, state) {
  const labels =
    form === "login"
      ? { idle: TEXT.loginButton, busy: TEXT.loginSubmitting, done: TEXT.loginSuccess }
      : { idle: TEXT.changeButton, busy: TEXT.changeSubmitting, done: TEXT.changeSuccess };
  switch (state.kind) {
    case "submitting":
      return { disabled: true, button: labels.busy, formError: "", fieldErrors: {}, status: "" };
    case "error":
      return {
        disabled: false,
        button: labels.idle,
        formError: state.message,
        fieldErrors: { ...state.fields },
        status: "",
      };
    case "success":
      return { disabled: true, button: labels.idle, formError: "", fieldErrors: {}, status: labels.done };
    default:
      return { disabled: false, button: labels.idle, formError: "", fieldErrors: {}, status: "" };
  }
}

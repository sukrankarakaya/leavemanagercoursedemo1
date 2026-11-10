// Saf arayüz mantığı: İK "Kullanıcılar" sayfası — DOM'a dokunmaz.

export const ROLE_LABELS = Object.freeze({ EMPLOYEE: "Çalışan", MANAGER: "Yönetici", HR: "İK" });

export const TEXT = Object.freeze({
  loading: "Kullanıcılar yükleniyor…",
  forbidden: "Bu sayfayı görüntüleme yetkiniz yok.",
  error: "Kullanıcılar yüklenemedi. Lütfen tekrar deneyin.",
  noManager: "—",
  tempWarning: "Bu geçici parola bir daha gösterilmeyecek. Kullanıcıya güvenli bir yolla iletin.",
  created: "Kullanıcı oluşturuldu.",
});

export function roleLabel(role) {
  return ROLE_LABELS[role] || role;
}

/** Liste yanıtını sayfa durumuna çevirir. */
export function listState(status, body) {
  if (status === 200 && Array.isArray(body)) return { kind: "list", users: body };
  if (status === 403) return { kind: "forbidden" };
  return { kind: "error" };
}

/** Tablo satırları: ad, e-posta, rol etiketi, yönetici adı. */
export function userRows(users) {
  const names = new Map(users.map((u) => [u.id, u.full_name]));
  return users.map((u) => ({
    id: u.id,
    name: u.full_name,
    email: u.email,
    role: roleLabel(u.role),
    manager: (u.manager_id && names.get(u.manager_id)) || TEXT.noManager,
  }));
}

/** Yönetici seçimi: yalnızca Yönetici rolündekiler. */
export function managerOptions(users) {
  return users
    .filter((u) => u.role === "MANAGER")
    .map((u) => ({ value: u.id, label: `${u.full_name} (${u.email})` }));
}

/** Oluşturma başarılı: geçici parola tek seferlik gösterim. */
export function createdNotice(body) {
  return {
    title: TEXT.created,
    email: body.user.email,
    tempPassword: body.temp_password,
    warning: TEXT.tempWarning,
  };
}

/** Oluşturma hatası: alan bazında mesajlar ve "e-posta zaten kayıtlı" (409). */
export function createErrors(status, body) {
  const error = (body && body.error) || {};
  if (status === 409 && error.code === "EMAIL_TAKEN") {
    return { formError: "", fields: { email: error.message } };
  }
  if (status === 422 && error.fields) return { formError: error.message || "", fields: { ...error.fields } };
  return { formError: error.message || TEXT.error, fields: {} };
}

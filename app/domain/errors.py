"""Tipli alan hataları; api katmanı bunları tek bir handler ile HTTP'ye çevirir."""


class DomainError(Exception):
    """Tüm alan hatalarının tabanı. `code` sabit, `message` kullanıcıya uygun Türkçe metindir."""

    code = "DOMAIN_ERROR"
    message = "İşlem tamamlanamadı."

    def __init__(self) -> None:
        super().__init__(self.code)


class DatabaseUnavailableError(DomainError):
    """Veritabanına erişilemiyor."""

    code = "DB_UNAVAILABLE"
    message = "Sistem şu anda kullanılamıyor."


class InvalidCredentialsError(DomainError):
    """Hatalı e-posta/parola veya sınırlanmış hesap — tek, genel yanıt (spec 0002, R-5)."""

    code = "INVALID_CREDENTIALS"
    message = "E-posta veya parola hatalı ya da çok fazla deneme yapıldı."


class UnauthenticatedError(DomainError):
    code = "UNAUTHENTICATED"
    message = "Lütfen giriş yapın."


class SessionExpiredError(DomainError):
    code = "SESSION_EXPIRED"
    message = "Oturumunuzun süresi doldu, lütfen tekrar giriş yapın."


class PasswordChangeRequiredError(DomainError):
    code = "PASSWORD_CHANGE_REQUIRED"
    message = "Devam etmeden önce parolanızı değiştirmelisiniz."


class ForbiddenError(DomainError):
    code = "FORBIDDEN"
    message = "Bu işlem için yetkiniz yok."


class EmailTakenError(DomainError):
    code = "EMAIL_TAKEN"
    message = "Bu e-posta adresi zaten kayıtlı."


class FirstUserExistsError(DomainError):
    code = "USERS_ALREADY_EXIST"
    message = "Sistemde zaten kullanıcı var; ilk İK hesabı yalnızca boş sistemde oluşturulur."


class ValidationError(DomainError):
    """Alan bazında doğrulama hataları: {alan: Türkçe mesaj}."""

    code = "VALIDATION_ERROR"
    message = "Girilen bilgiler geçersiz."

    def __init__(self, fields: dict[str, str]) -> None:
        super().__init__()
        self.fields = dict(fields)

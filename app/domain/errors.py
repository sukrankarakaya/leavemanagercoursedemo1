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

"""AC-2 (geçici parola), AC-3 (e-posta/ad sınırları), AC-10 (yeni parola kuralları)."""

import pytest

from app.domain.errors import ValidationError
from app.domain.users import (
    TEMP_PASSWORD_ALPHABET,
    generate_temp_password,
    normalize_email,
    normalize_full_name,
    validate_new_password,
)


def test_temp_password_length_and_uniqueness() -> None:
    passwords = {generate_temp_password() for _ in range(200)}
    assert len(passwords) == 200
    for password in passwords:
        assert len(password) == 12
        assert set(password) <= set(TEMP_PASSWORD_ALPHABET)
    assert not set("0O1lI") & set(TEMP_PASSWORD_ALPHABET)


def test_email_and_name_rules() -> None:
    assert normalize_email("  Ayse.Yilmaz@Firma.COM ") == "ayse.yilmaz@firma.com"
    local = "a" * (254 - len("@firma.com"))
    assert normalize_email(f"{local}@firma.com") == f"{local}@firma.com"  # tam 254
    for bad in ["", "   ", "ayse", "ayse@firma", "ay se@firma.com", f"{local}x@firma.com"]:
        with pytest.raises(ValidationError) as info:
            normalize_email(bad)
        assert set(info.value.fields) == {"email"}

    assert normalize_full_name("  Ayşe Yılmaz  ") == "Ayşe Yılmaz"
    assert normalize_full_name("A") == "A"
    assert normalize_full_name("x" * 100) == "x" * 100
    for bad in ["", "    ", "x" * 101]:
        with pytest.raises(ValidationError) as info:
            normalize_full_name(bad)
        assert set(info.value.fields) == {"full_name"}


@pytest.mark.parametrize(
    ("new_password", "accepted"),
    [
        ("a" * 11, False),
        ("a" * 12, True),
        ("a" * 128, True),
        ("a" * 129, False),
        ("Ayse@Firma.com", False),  # e-postayla aynı (büyük/küçük harf duyarsız)
        ("Gecici-Parola-1", False),  # mevcut parolayla aynı
        ("yepyeni uzun parola", True),
    ],
)
def test_new_password_rules_boundaries(new_password: str, accepted: bool) -> None:
    def check() -> None:
        validate_new_password(
            new_password, email="ayse@firma.com", current_password="Gecici-Parola-1"
        )

    if accepted:
        check()
    else:
        with pytest.raises(ValidationError) as info:
            check()
        assert set(info.value.fields) == {"new_password"}

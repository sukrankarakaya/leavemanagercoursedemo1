"""Yönetim komutları (ikinci composition root). Spec 0002, R-1.

Kullanım:
  tools/venv python -m app.cli create-first-hr --email ik@firma.com --name "Ad Soyad"
"""

import argparse
import sys
from collections.abc import Sequence
from typing import TextIO

from app.config import Settings
from app.db.engine import make_engine
from app.db.migrate import upgrade_to_head
from app.domain.clock import Clock, SystemClock
from app.domain.errors import FirstUserExistsError, ValidationError
from app.repositories.unit_of_work import SqlUnitOfWorkFactory
from app.services.passwords import Argon2PasswordHasher, PasswordHasher
from app.services.user_service import UserService


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    first = commands.add_parser("create-first-hr", help="Boş sistemde ilk İK hesabını oluşturur.")
    first.add_argument("--email", required=True)
    first.add_argument("--name", required=True)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    settings: Settings | None = None,
    hasher: PasswordHasher | None = None,
    clock: Clock | None = None,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    args = _parser().parse_args(argv)
    settings = settings or Settings.from_env()
    upgrade_to_head(settings.database_url)
    engine = make_engine(settings.database_url)
    try:
        service = UserService(
            SqlUnitOfWorkFactory(engine), hasher or Argon2PasswordHasher(), clock or SystemClock()
        )
        created = service.create_first_hr(email=args.email, full_name=args.name)
    except FirstUserExistsError as exc:
        print(exc.message, file=err)
        return 1
    except ValidationError as exc:
        for message in exc.fields.values():
            print(message, file=err)
        return 2
    finally:
        engine.dispose()
    print(f"İK hesabı oluşturuldu: {created.user.email}", file=out)
    print(f"Geçici parola (yalnızca bir kez gösterilir): {created.temp_password}", file=out)
    print("İlk girişte parola değiştirilmelidir.", file=out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

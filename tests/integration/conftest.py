"""Bu klasördeki her test otomatik olarak `integration` işaretlenir (full profil).

Seçiciyle bölme: fast `-m "not integration"`, full `-m integration` (testing.md, Two speeds 4).
"""

from pathlib import Path

import pytest

INTEGRATION_DIR = Path(__file__).resolve().parent


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if INTEGRATION_DIR in Path(item.path).resolve().parents:
            item.add_marker(pytest.mark.integration)

"""Import the bundled surname text samples into the Django database.

Run from the repository root:
    python scripts/import_surnames.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

import django  # noqa: E402

django.setup()

from Surname.models import SecondName  # noqa: E402

FIELDS = {
    "基本信息.txt": "base_information",
    "历代名人.txt": "fam",
    "迁徙传播.txt": "mig",
    "人口分布.txt": "dis",
    "姓氏起源.txt": "ori",
    "姓氏文化.txt": "cul",
}


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")[:1000]


def import_all(data_dir: Path | None = None) -> int:
    data_dir = Path(data_dir or ROOT / "data" / "surnames")
    count = 0
    for folder in sorted(data_dir.iterdir()):
        if not folder.is_dir():
            continue
        values = {field: _read(folder / filename) for filename, field in FIELDS.items()}
        SecondName.objects.update_or_create(second_name=folder.name, defaults=values)
        count += 1
    return count


if __name__ == "__main__":
    total = import_all()
    print(f"imported {total} surnames")

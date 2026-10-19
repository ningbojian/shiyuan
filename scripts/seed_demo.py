"""Seed a small, reproducible demo dataset for the shiyuan website.

The full course dataset has 300+ surnames and is not committed. This script
imports the four samples under ``data/surnames`` and adds provinces, dynasties,
distribution rows, a few famous people, a demo account and comments.

Run:
    python manage.py migrate
    python scripts/seed_demo.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

import django  # noqa: E402

django.setup()

from import_surnames import import_all  # noqa: E402
from Surname.models import (  # noqa: E402
    Distribution,
    Dynasty,
    Famous,
    Province,
    SecondName,
)
from user.models import Comment, User  # noqa: E402

PROVINCES = [
    "河北省", "山西省", "吉林省", "辽宁省", "黑龙江省", "陕西省", "甘肃省",
    "青海省", "山东省", "福建省", "浙江省", "台湾省", "河南省", "湖北省",
    "湖南省", "江西省", "江苏省", "安徽省", "广东省", "海南省", "四川省",
    "贵州省", "云南省", "内蒙古", "北京", "天津", "重庆", "广西", "新疆",
    "西藏", "澳门", "香港", "宁夏", "上海",
]

DYNASTIES = {
    "夏朝": (-2070, -1600),
    "商（殷）朝": (-1600, -1046),
    "周朝": (-1046, -256),
    "春秋战国": (-770, -221),
    "秦朝": (-221, -206),
    "汉朝": (-202, 263),
    "三国时期": (220, 280),
    "晋朝": (265, 420),
    "南北朝": (386, 589),
    "隋朝": (581, 618),
    "唐朝": (618, 907),
    "五代十国": (907, 960),
    "宋朝": (960, 1279),
    "元朝": (1271, 1368),
    "明朝": (1368, 1644),
    "清朝": (1636, 1912),
    "中华民国": (1912, 1949),
    "中华人民共和国": (1949, None),
}

FAMOUS = [
    ("李", "春秋战国", "李冰", "主持修建都江堰的水利工程专家"),
    ("李", "汉朝", "李广", "西汉名将，以勇敢善战著称"),
    ("李", "唐朝", "李世民", "唐太宗，唐朝第二位皇帝"),
    ("王", "晋朝", "王羲之", "东晋书法家，被称为书圣"),
    ("王", "宋朝", "王安石", "北宋政治家、文学家、改革家"),
    ("张", "汉朝", "张衡", "东汉天文学家，发明地动仪"),
    ("张", "汉朝", "张良", "汉初谋士，辅助刘邦建立汉朝"),
    ("丁", "宋朝", "丁谓", "北宋宰相、文学家"),
    ("丁", "清朝", "丁汝昌", "清末北洋水师提督"),
]

DEMO_NAMES = ["丁", "李", "王", "张"]
DEMO_COUNTS = {"李": 128, "王": 96, "张": 77, "丁": 54}


def seed() -> None:
    imported = import_all()
    print(f"imported {imported} surnames")

    provinces = []
    for name in PROVINCES:
        province, _ = Province.objects.update_or_create(name=name)
        provinces.append(province)

    dynasties = {}
    for name, (begin, end) in DYNASTIES.items():
        dynasty, _ = Dynasty.objects.update_or_create(
            name=name,
            defaults={"begin": begin, "end": end},
        )
        dynasties[name] = dynasty

    surnames = {item.second_name: item for item in SecondName.objects.filter(second_name__in=DEMO_NAMES)}

    # Rebuild only the demo rows so the script can be run repeatedly.
    Distribution.objects.filter(surname__second_name__in=DEMO_NAMES).delete()
    Famous.objects.filter(surname__second_name__in=DEMO_NAMES).delete()

    for surname_name, surname in surnames.items():
        for index, province in enumerate(provinces):
            ratio = ((index * 7 + len(surname_name) * 5) % 13 + 1) / 1000
            distribution = Distribution.objects.create(ratio=ratio)
            distribution.surname.add(surname)
            distribution.province.add(province)
        surname.count = DEMO_COUNTS.get(surname_name, 0)
        surname.save(update_fields=["count"])

    for surname_name, dynasty_name, person, info in FAMOUS:
        surname = surnames.get(surname_name)
        dynasty = dynasties.get(dynasty_name)
        if surname is None or dynasty is None:
            continue
        famous = Famous.objects.create(name=person, info=info[:50])
        famous.surname.add(surname)
        famous.dynasty.add(dynasty)

    user, _ = User.objects.update_or_create(
        account="demo",
        defaults={"name": "演示用户", "surname": "李", "code": ""},
    )
    user.set_password("demo123456")
    user.save()

    Comment.objects.get_or_create(
        account=user,
        content="氏源示例评论：这里可以查姓氏起源、人口分布和迁徙地图。",
    )
    Comment.objects.get_or_create(
        account=user,
        content="这是一条用于演示评论区的课程项目数据。",
    )

    print(f"provinces={len(provinces)}, dynasties={len(dynasties)}, surnames={len(surnames)}")
    print("demo account: demo / demo123456")


if __name__ == "__main__":
    seed()

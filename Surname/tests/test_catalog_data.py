from __future__ import annotations

import json
import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from Surname.services.catalog import validate_catalog

CATALOG_PATH = Path(settings.BASE_DIR) / "data" / "catalog.json"
SOURCE_DIR = Path(settings.BASE_DIR) / "data" / "surnames"

SOURCE_FIELDS = {
    "基本信息.txt": "base_information",
    "历代名人.txt": "fam",
    "迁徙传播.txt": "mig",
    "人口分布.txt": "dis",
    "姓氏起源.txt": "ori",
    "姓氏文化.txt": "cul",
}

CURATED_NAMES = {
    "李", "王", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴", "徐",
    "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗", "梁", "宋",
    "郑", "谢", "韩", "唐", "冯", "于", "董", "萧", "沈", "叶", "丁",
}

MARKUP_MARKERS = ("<script", "onerror=", "onload=", "javascript:", "<iframe", "<img")
INITIAL_RE = re.compile(r"^[A-Z]$")


class CatalogDataTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        cls.surnames = cls.data["surnames"]
        cls.by_name = {item["second_name"]: item for item in cls.surnames}
        cls.imported = [
            item for item in cls.surnames if item["second_name"] not in CURATED_NAMES
        ]

    def test_catalog_validates(self):
        self.assertEqual(validate_catalog(CATALOG_PATH, min_surnames=32), [])

    def test_surname_count_and_uniqueness(self):
        self.assertEqual(len(self.surnames), 348)
        names = [item["second_name"] for item in self.surnames]
        slugs = [item["slug"] for item in self.surnames]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_curated_entries_remain_rich(self):
        curated = [item for item in self.surnames if item["second_name"] in CURATED_NAMES]
        self.assertEqual(len(curated), 33)
        for item in curated:
            for field in (
                "second_name",
                "slug",
                "pinyin",
                "initial",
                "summary",
                "base_information",
                "ori",
                "mig",
                "dis",
                "cul",
                "source_note",
            ):
                self.assertTrue(item.get(field), f"{item['second_name']} 缺少 {field}")
            self.assertFalse(item["is_imported"], item["second_name"])
            self.assertTrue(item["is_demo"], item["second_name"])
            self.assertTrue(60 <= len(item["summary"]) <= 120, item["second_name"])
            self.assertTrue(8 <= len(item["keywords"]) <= 12, item["second_name"])
            self.assertTrue(
                6 <= len(item["distributions"]) <= 10, item["second_name"]
            )
            self.assertTrue(len(item["figures"]) >= 3, item["second_name"])
            self.assertTrue(
                2 <= len(item["migration_events"]) <= 3, item["second_name"]
            )
            self.assertTrue(len(item["relations"]) >= 1, item["second_name"])

    def test_imported_entries_are_usable(self):
        self.assertEqual(len(self.imported), 315)
        for item in self.imported:
            name = item["second_name"]
            self.assertTrue(item["is_imported"], name)
            self.assertTrue(item["is_demo"], name)
            self.assertTrue(item["source_note"], name)
            self.assertTrue(item["summary"], name)
            self.assertTrue(
                any(
                    item[field]
                    for field in ("base_information", "ori", "mig", "dis", "cul")
                ),
                f"{name} 没有任何原始文字",
            )
            self.assertEqual(item["fam"], "", name)
            self.assertEqual(item["keywords"], [], name)
            self.assertEqual(item["distributions"], [], name)
            self.assertEqual(item["migration_events"], [], name)
            self.assertEqual(item["relations"], [], name)
            self.assertTrue(item["pinyin"], name)
            self.assertRegex(item["initial"], INITIAL_RE, name)
            blob = json.dumps(item, ensure_ascii=False).lower()
            for marker in MARKUP_MARKERS:
                self.assertNotIn(marker, blob, f"{name} 含标记 {marker}")

    def test_figure_total_and_slugs(self):
        all_figures = [
            figure for item in self.surnames for figure in item["figures"]
        ]
        self.assertEqual(len(all_figures), 6251)
        slugs = [figure["slug"] for figure in all_figures]
        self.assertEqual(len(slugs), len(set(slugs)))
        for figure in all_figures:
            self.assertTrue(figure["name"], figure["slug"])
            self.assertTrue(figure["info"], figure["name"])
            self.assertTrue(figure["source_note"], figure["name"])

        li = self.by_name["李"]
        libai = next(figure for figure in li["figures"] if figure["name"] == "李白")
        self.assertEqual(libai["slug"], "li-bai")
        self.assertEqual(
            libai["info"], "唐代诗人，代表作有《静夜思》《将进酒》。"
        )
        self.assertEqual(len(self.by_name["邓"]["figures"]), 0)
        self.assertGreaterEqual(len(li["figures"]), 50)

    def test_imported_special_cases(self):
        self.assertIn("又", self.by_name)
        you_figures = {figure["name"] for figure in self.by_name["又"]["figures"]}
        self.assertIn("又尚珍", you_figures)
        self.assertNotIn("上官", self.by_name)
        for name in ("弓", "璩", "荀"):
            self.assertIn(name, self.by_name)
        for name in ("刘", "叶"):
            self.assertIn(name, self.by_name)
            self.assertFalse(self.by_name[name]["is_imported"])

    def test_distribution_intensity_range(self):
        for item in self.surnames:
            for distribution in item["distributions"]:
                self.assertTrue(distribution["is_illustrative"])
                self.assertTrue(distribution["source_note"])
                self.assertTrue(0 <= distribution["intensity"] <= 100)

    def test_every_demo_record_has_source_note(self):
        for item in self.surnames:
            self.assertTrue(item["source_note"])
            for figure in item["figures"]:
                self.assertTrue(figure["source_note"], figure["name"])
            for event in item["migration_events"]:
                self.assertTrue(event["source_note"], event["description"])
            for relation in item["relations"]:
                self.assertTrue(relation["source_note"], relation["description"])

    def test_required_relation_edges(self):
        expected = {
            ("马", "赵", "branch"),
            ("何", "韩", "changed"),
            ("叶", "沈", "branch"),
        }
        found = set()
        for item in self.surnames:
            for relation in item["relations"]:
                if relation.get("target_surname"):
                    found.add(
                        (
                            item["second_name"],
                            relation["target_surname"],
                            relation["relation_type"],
                        )
                    )
        self.assertTrue(expected.issubset(found), expected - found)

    def test_required_clan_nodes(self):
        clans = {clan["name"] for clan in self.data["clans"]}
        required = {"姬姓", "嬴姓", "子姓", "妫姓", "姜姓", "祁姓", "曹姓", "妘姓", "己姓"}
        self.assertTrue(required.issubset(clans), required - clans)

    def test_original_samples_are_complete(self):
        for surname in ("李", "王", "张", "丁"):
            item = self.by_name[surname]
            folder = SOURCE_DIR / surname
            for filename, field in SOURCE_FIELDS.items():
                path = folder / filename
                if not path.exists():
                    continue
                source = path.read_text(encoding="utf-8-sig").strip()
                if source:
                    self.assertEqual(item[field], source, f"{surname}/{filename}")

    def test_no_script_markup(self):
        raw = CATALOG_PATH.read_text(encoding="utf-8")
        self.assertNotIn("<script", raw.lower())
        self.assertNotIn("onerror=", raw.lower())

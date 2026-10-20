from __future__ import annotations

import json
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


class CatalogDataTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        cls.surnames = cls.data["surnames"]
        cls.by_name = {item["second_name"]: item for item in cls.surnames}

    def test_catalog_validates(self):
        self.assertEqual(validate_catalog(CATALOG_PATH, min_surnames=32), [])

    def test_surname_count_and_uniqueness(self):
        self.assertEqual(len(self.surnames), 33)
        names = [item["second_name"] for item in self.surnames]
        slugs = [item["slug"] for item in self.surnames]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_required_fields_and_volume(self):
        figures = 0
        events = 0
        relations = 0
        for item in self.surnames:
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
            self.assertTrue(60 <= len(item["summary"]) <= 120, item["second_name"])
            self.assertTrue(8 <= len(item["keywords"]) <= 12, item["second_name"])
            self.assertTrue(
                6 <= len(item["distributions"]) <= 10, item["second_name"]
            )
            self.assertTrue(3 <= len(item["figures"]) <= 5, item["second_name"])
            self.assertTrue(
                2 <= len(item["migration_events"]) <= 3, item["second_name"]
            )
            self.assertTrue(len(item["relations"]) >= 1, item["second_name"])
            figures += len(item["figures"])
            events += len(item["migration_events"])
            relations += len(item["relations"])

        self.assertGreaterEqual(figures, 100)
        self.assertGreaterEqual(events, 64)
        self.assertGreaterEqual(relations, 30)

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

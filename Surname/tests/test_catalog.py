from __future__ import annotations

import copy
import json
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from Surname.models import (
    Distribution,
    Famous,
    MigrationEvent,
    Province,
    SecondName,
    SurnameRelation,
)
from Surname.services.catalog import CatalogValidationError, load_catalog, validate_catalog


class CatalogTestCase(TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def write_catalog(self, payload):
        path = Path(self.tmpdir.name) / "catalog.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def payload(self):
        common = {
            "source_note": "课程演示整理，非权威统计",
            "is_demo": True,
            "aliases": [],
            "summary": "示例摘要",
            "base_information": "示例基本信息",
            "ori": "示例起源",
            "mig": "示例迁徙",
            "dis": "示例分布",
            "cul": "示例文化",
            "keywords": [{"name": "示例", "value": 10}],
            "is_featured": False,
            "popularity": 10,
        }
        return {
            "meta": {
                "version": 1,
                "generated_at": "2026-10-20",
                "disclaimer": "课程展示用整理，非权威统计",
            },
            "clans": [
                {"name": "嬴姓", "slug": "ying-xing", "kind": "xing", "description": "示例"}
            ],
            "surnames": [
                {
                    **common,
                    "second_name": "李",
                    "slug": "li",
                    "pinyin": "li",
                    "initial": "L",
                    "figures": [
                        {
                            "name": "李白",
                            "slug": "li-bai",
                            "dynasty": "唐朝",
                            "info": "唐代诗人",
                            "birth_year": 701,
                            "death_year": 762,
                            "source_note": "课程演示整理",
                        }
                    ],
                    "distributions": [
                        {
                            "province": "河北省",
                            "intensity": 72,
                            "is_illustrative": True,
                            "source_note": "示意强度，非人口占比",
                        }
                    ],
                    "migration_events": [
                        {
                            "dynasty": "唐朝",
                            "from_province": "河南省",
                            "to_province": "福建省",
                            "description": "示例南迁",
                            "order": 1,
                            "source_note": "课程演示整理",
                        }
                    ],
                    "relations": [],
                },
                {
                    **common,
                    "second_name": "王",
                    "slug": "wang",
                    "pinyin": "wang",
                    "initial": "W",
                    "figures": [
                        {
                            "name": "王维",
                            "slug": "wang-wei",
                            "dynasty": "唐朝",
                            "info": "唐代诗人",
                            "birth_year": 701,
                            "death_year": 761,
                            "source_note": "课程演示整理",
                        }
                    ],
                    "distributions": [
                        {
                            "province": "河南省",
                            "intensity": 65,
                            "is_illustrative": True,
                            "source_note": "示意强度，非人口占比",
                        }
                    ],
                    "migration_events": [],
                    "relations": [
                        {
                            "target_surname": "李",
                            "relation_type": "branch",
                            "description": "示例分支关系",
                            "source_note": "课程演示整理",
                        }
                    ],
                },
            ],
        }


class LoadCatalogTests(CatalogTestCase):
    def test_load_is_idempotent(self):
        path = self.write_catalog(self.payload())

        first = load_catalog(path)
        second = load_catalog(path)

        self.assertEqual(first, second)
        self.assertEqual(first.surnames, 2)
        self.assertEqual(first.figures, 2)
        self.assertEqual(first.events, 1)
        self.assertEqual(first.relations, 1)
        self.assertEqual(SecondName.objects.count(), 2)
        self.assertEqual(Famous.objects.count(), 2)
        self.assertEqual(Distribution.objects.count(), 2)
        self.assertEqual(MigrationEvent.objects.count(), 1)
        self.assertEqual(SurnameRelation.objects.count(), 1)
        self.assertTrue(Province.objects.filter(name="河北省").exists())

    def test_load_rejects_bad_intensity(self):
        payload = self.payload()
        payload["surnames"][0]["distributions"][0]["intensity"] = 150
        path = self.write_catalog(payload)

        with self.assertRaises(CatalogValidationError):
            load_catalog(path)
        self.assertEqual(SecondName.objects.count(), 0)

    def test_load_rejects_unknown_province(self):
        payload = self.payload()
        payload["surnames"][0]["distributions"][0]["province"] = "火星省"
        path = self.write_catalog(payload)

        with self.assertRaises(CatalogValidationError):
            load_catalog(path)
        self.assertEqual(SecondName.objects.count(), 0)

    def test_load_is_atomic_on_error(self):
        payload = self.payload()
        payload["surnames"][1]["distributions"][0]["intensity"] = -1
        path = self.write_catalog(payload)

        with self.assertRaises(CatalogValidationError):
            load_catalog(path)
        self.assertEqual(SecondName.objects.count(), 0)
        self.assertEqual(Distribution.objects.count(), 0)

    def test_load_sets_is_imported(self):
        payload = self.payload()
        payload["surnames"][1]["is_imported"] = True
        path = self.write_catalog(payload)

        load_catalog(path)

        self.assertFalse(SecondName.objects.get(second_name="李").is_imported)
        self.assertTrue(SecondName.objects.get(second_name="王").is_imported)


class ValidateCatalogTests(CatalogTestCase):
    def test_validate_reports_missing_source_note(self):
        payload = self.payload()
        payload["surnames"][0].pop("source_note")
        path = self.write_catalog(payload)

        errors = validate_catalog(path)

        self.assertTrue(any("source_note" in error for error in errors), errors)
        self.assertTrue(any("李" in error for error in errors), errors)

    def test_validate_reports_markup(self):
        payload = copy.deepcopy(self.payload())
        payload["surnames"][0]["summary"] = "<script>alert(1)</script>"
        path = self.write_catalog(payload)

        errors = validate_catalog(path)

        self.assertTrue(any("标记" in error or "markup" in error for error in errors), errors)

    def test_validate_rejects_non_bool_is_imported(self):
        payload = self.payload()
        payload["surnames"][0]["is_imported"] = "yes"
        path = self.write_catalog(payload)

        errors = validate_catalog(path)

        self.assertTrue(any("is_imported" in error for error in errors), errors)

    def test_validate_imported_requires_source_note(self):
        payload = self.payload()
        payload["surnames"][0]["is_imported"] = True
        payload["surnames"][0]["is_demo"] = False
        payload["surnames"][0].pop("source_note")
        path = self.write_catalog(payload)

        errors = validate_catalog(path)

        self.assertTrue(any("is_imported" in error for error in errors), errors)
        self.assertTrue(any("source_note" in error for error in errors), errors)


class CatalogCommandTests(CatalogTestCase):
    def test_load_catalog_dry_run_reports_and_skips_database(self):
        path = self.write_catalog(self.payload())
        out = StringIO()

        call_command("load_catalog", str(path), dry_run=True, stdout=out)

        output = out.getvalue()
        self.assertIn("将加载 2 个姓氏", output)
        self.assertIn("dry-run", output)
        self.assertEqual(SecondName.objects.count(), 0)

    def test_load_catalog_writes_records(self):
        path = self.write_catalog(self.payload())
        out = StringIO()

        call_command("load_catalog", str(path), stdout=out)

        self.assertIn("已加载 2 个姓氏", out.getvalue())
        self.assertTrue(SecondName.objects.filter(slug="li").exists())
        self.assertEqual(Famous.objects.count(), 2)

    def test_load_catalog_rejects_invalid_catalog(self):
        payload = self.payload()
        payload["surnames"][0]["distributions"][0]["intensity"] = 150
        path = self.write_catalog(payload)
        err = StringIO()

        with self.assertRaises(CommandError):
            call_command("load_catalog", str(path), stderr=err)

        self.assertIn("intensity", err.getvalue())
        self.assertEqual(SecondName.objects.count(), 0)

    def test_validate_catalog_command_passes_on_default_catalog(self):
        out = StringIO()

        call_command("validate_catalog", stdout=out)

        self.assertIn("目录校验通过", out.getvalue())

    def test_validate_catalog_command_reports_errors(self):
        path = self.write_catalog(self.payload())
        err = StringIO()

        with self.assertRaises(CommandError):
            call_command("validate_catalog", str(path), stderr=err)

        self.assertIn("姓氏数量不足", err.getvalue())

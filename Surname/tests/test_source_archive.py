from __future__ import annotations

import tempfile
from pathlib import Path

from django.test import SimpleTestCase

from Surname.services.source_archive import (
    DYNASTY_ALIASES,
    SURNAME_PINYIN_OVERRIDES,
    ParseStats,
    SurnameSource,
    build_imported_entry,
    build_summary,
    merge_catalog,
    parse_figures,
    pinyin_for_surname,
    read_surname_folder,
    sanitize_text,
    scan_source_dir,
    slug_for_surname,
)

OBSERVED_DYNASTY_HEADERS = [
    "明",
    "清",
    "中华人民共和国",
    "中华民国",
    "唐",
    "东汉",
    "元",
    "北宋",
    "西汉",
    "宋",
    "南宋",
    "春秋",
    "战国",
    "北魏",
    "隋",
    "晋",
    "魏",
    "西晋",
    "东晋",
    "吴",
    "秦",
    "梁",
    "蜀",
    "金",
    "齐",
    "后唐",
    "北齐",
    "后梁",
    "北周",
    "周",
    "夏",
    "西周",
    "陈",
    "后周",
    "商",
    "南唐",
    "东周",
    "后晋",
    "后汉",
    "后蜀",
    "西魏",
    "前蜀",
    "玄汉",
    "东魏",
    "南汉（荆南）",
    "新朝",
    "西夏",
    "辽",
    "吴越",
    "南平",
]

CANONICAL_DYNASTIES = {
    "夏朝",
    "商朝",
    "周朝",
    "春秋",
    "战国",
    "秦朝",
    "汉朝",
    "三国",
    "晋朝",
    "南北朝",
    "隋朝",
    "唐朝",
    "五代十国",
    "宋朝",
    "辽朝",
    "金朝",
    "西夏",
    "元朝",
    "明朝",
    "清朝",
    "中华民国",
    "中华人民共和国",
}

FIELD_FILES = {
    "基本信息": "base_information",
    "姓氏起源": "ori",
    "迁徙传播": "mig",
    "人口分布": "dis",
    "历代名人": "fam",
    "姓氏文化": "cul",
}


def write_folder(root: Path, name: str, files: dict[str, str]) -> Path:
    folder = root / name
    folder.mkdir()
    for filename, text in files.items():
        (folder / filename).write_text(text, encoding="utf-8")
    return folder


def make_source(
    name: str = "李",
    *,
    fields: dict[str, str] | None = None,
    figures: list | None = None,
) -> SurnameSource:
    return SurnameSource(
        name=name,
        folder=Path("/tmp") / name,
        fields=fields or {field: "" for field in FIELD_FILES.values()},
        figures=figures or [],
        stats=ParseStats(
            headers=0,
            person_lines=0,
            valid=0,
            skipped_empty=0,
            duplicates_merged=0,
        ),
    )


class ReadSurnameFolderTests(SimpleTestCase):
    def test_read_surname_folder_maps_six_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = write_folder(
                Path(tmp),
                "李",
                {f"{stem}.txt": f"  {stem}内容  \n" for stem in FIELD_FILES},
            )
            fields = read_surname_folder(folder)

        for stem, field in FIELD_FILES.items():
            self.assertEqual(fields[field], f"{stem}内容")

    def test_missing_files_become_empty_strings(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = write_folder(
                Path(tmp), "李", {"基本信息.txt": "李姓基本信息"}
            )
            fields = read_surname_folder(folder)

        self.assertEqual(fields["base_information"], "李姓基本信息")
        for field in set(FIELD_FILES.values()) - {"base_information"}:
            self.assertEqual(fields[field], "")

    def test_read_surname_folder_falls_back_to_gbk(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "李"
            folder.mkdir()
            (folder / "姓氏起源.txt").write_bytes(
                "嬴姓后裔，世代居于陇西".encode("gb18030")
            )
            fields = read_surname_folder(folder)

        self.assertEqual(fields["ori"], "嬴姓后裔，世代居于陇西")


class ScanSourceDirTests(SimpleTestCase):
    def test_scan_ignores_non_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_folder(root, "李", {"基本信息.txt": "李姓"})
            (root / "rename.xls").write_text("dir/b", encoding="gbk")
            (root / "获取文件名.bat").write_text("dir/b>rename.xls", encoding="gbk")
            sources = scan_source_dir(root)

        self.assertEqual([source.name for source in sources], ["李"])

    def test_scan_maps_shangguan_to_you(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_folder(
                Path(tmp),
                "上官",
                {
                    "基本信息.txt": "又姓，课程原始资料。",
                    "历代名人.txt": "明\n又尚珍：明代人物。",
                },
            )
            sources = scan_source_dir(Path(tmp))

        self.assertEqual([source.name for source in sources], ["又"])
        self.assertEqual([figure.name for figure in sources[0].figures], ["又尚珍"])

    def test_scan_skips_empty_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_folder(Path(tmp), "空", {f"{stem}.txt": "" for stem in FIELD_FILES})
            sources = scan_source_dir(Path(tmp))

        self.assertEqual(sources, [])


class ParseFiguresTests(SimpleTestCase):
    def test_parse_figures_groups_by_dynasty(self):
        figures, stats = parse_figures("战国\n李冰：都江堰\n秦\n李斯：丞相")

        self.assertEqual(
            [(figure.name, figure.dynasty, figure.info) for figure in figures],
            [("李冰", "战国", "都江堰"), ("李斯", "秦朝", "丞相")],
        )
        self.assertEqual([figure.order for figure in figures], [1, 2])
        self.assertEqual(stats.headers, 2)
        self.assertEqual(stats.person_lines, 2)
        self.assertEqual(stats.valid, 2)

    def test_parse_figures_skips_empty_name_and_info(self):
        figures, stats = parse_figures("明\n晏几道：\n：无姓名\n张三：有信息")

        self.assertEqual([figure.name for figure in figures], ["张三"])
        self.assertEqual(stats.skipped_empty, 2)
        self.assertEqual(stats.valid, 1)

    def test_parse_figures_merges_duplicate_names_keeping_longest_info(self):
        figures, stats = parse_figures("唐\n李白：短介绍\n李白：更长的介绍")

        self.assertEqual(len(figures), 1)
        self.assertEqual(figures[0].info, "更长的介绍")
        self.assertEqual(stats.valid, 2)
        self.assertEqual(stats.duplicates_merged, 1)

    def test_parse_figures_rejects_unknown_dynasty_header(self):
        with self.assertRaises(ValueError) as raised:
            parse_figures("火星\n李四：来自未来")

        message = str(raised.exception)
        self.assertIn("火星", message)
        self.assertIn("1", message)

    def test_all_observed_dynasty_headers_map(self):
        for header in OBSERVED_DYNASTY_HEADERS:
            self.assertIn(header, DYNASTY_ALIASES)
            self.assertIn(DYNASTY_ALIASES[header], CANONICAL_DYNASTIES)


class SanitizeAndSummaryTests(SimpleTestCase):
    def test_sanitize_rejects_script_markup(self):
        with self.assertRaises(ValueError):
            sanitize_text("<script>alert(1)</script>")

        self.assertEqual(sanitize_text("李姓起源"), "李姓起源")

    def test_build_summary_falls_back_to_origin(self):
        source = make_source(
            fields={
                "base_information": "",
                "ori": "李姓出自嬴姓，后世分支众多。",
                "mig": "",
                "dis": "",
                "fam": "",
                "cul": "",
            }
        )
        summary = build_summary(source)

        self.assertTrue(summary)
        self.assertLessEqual(len(summary), 120)
        self.assertIn("嬴姓", summary)

    def test_build_summary_is_bounded(self):
        source = make_source(
            fields={
                "base_information": "李" * 500,
                "ori": "",
                "mig": "",
                "dis": "",
                "fam": "",
                "cul": "",
            }
        )
        summary = build_summary(source)

        self.assertGreaterEqual(len(summary), 60)
        self.assertLessEqual(len(summary), 120)


class PinyinAndSlugTests(SimpleTestCase):
    def test_pinyin_overrides_for_polyphonic_surnames(self):
        for name, expected in SURNAME_PINYIN_OVERRIDES.items():
            self.assertEqual(pinyin_for_surname(name), expected)

    def test_slug_collision_gets_suffix(self):
        used = {"li"}
        self.assertEqual(slug_for_surname("李", used), "li-2")


class BuildImportedEntryTests(SimpleTestCase):
    def test_build_imported_entry_marks_raw_entry(self):
        source = make_source(
            name="又",
            fields={
                "base_information": "又姓的课程原始资料。",
                "ori": "又姓起源。",
                "mig": "又姓迁徙。",
                "dis": "又姓分布。",
                "fam": "明\n又尚珍：明代人物。",
                "cul": "又姓文化。",
            },
            figures=[
                parse_figures("明\n又尚珍：明代人物。")[0][0],
            ],
        )
        entry = build_imported_entry(
            source, slug="you", pinyin="you", initial="Y"
        )

        self.assertEqual(entry["second_name"], "又")
        self.assertTrue(entry["is_imported"])
        self.assertTrue(entry["is_demo"])
        self.assertTrue(entry["source_note"])
        self.assertEqual(entry["fam"], "")
        self.assertEqual(entry["keywords"], [])
        self.assertEqual(entry["distributions"], [])
        self.assertEqual(entry["migration_events"], [])
        self.assertEqual(entry["relations"], [])
        self.assertEqual(len(entry["figures"]), 1)
        self.assertNotIn("slug", entry["figures"][0])


class MergeCatalogTests(SimpleTestCase):
    def curated_entry(self) -> dict:
        return {
            "second_name": "李",
            "slug": "li",
            "pinyin": "li",
            "initial": "L",
            "summary": "策划摘要",
            "base_information": "策划正文",
            "ori": "",
            "mig": "",
            "dis": "",
            "cul": "",
            "fam": "",
            "keywords": [],
            "distributions": [],
            "migration_events": [],
            "relations": [],
            "figures": [
                {
                    "name": "李白",
                    "slug": "li-bai",
                    "dynasty": "唐朝",
                    "info": "策划李白",
                    "source_note": "策划来源",
                    "is_demo": True,
                    "order": 0,
                }
            ],
        }

    def imported_entry(self, name: str = "李", figures: list | None = None) -> dict:
        source = make_source(
            name=name,
            fields={
                "base_information": f"{name}姓原始资料。",
                "ori": "",
                "mig": "",
                "dis": "",
                "fam": "",
                "cul": "",
            },
            figures=figures or [],
        )
        return build_imported_entry(
            source,
            slug="li" if name == "李" else "wang",
            pinyin="li" if name == "李" else "wang",
            initial="L" if name == "李" else "W",
        )

    def test_merge_preserves_curated_fields_and_figures(self):
        figures, _ = parse_figures("唐\n李白：原始李白\n战国\n李冰：都江堰")
        merged, stats = merge_catalog(
            [self.curated_entry()], [self.imported_entry(figures=figures)]
        )

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["summary"], "策划摘要")
        self.assertEqual(merged[0]["base_information"], "策划正文")
        names = [figure["name"] for figure in merged[0]["figures"]]
        self.assertEqual(names, ["李白", "李冰"])
        self.assertEqual(merged[0]["figures"][0]["info"], "策划李白")
        self.assertEqual(stats["merged"], 1)
        self.assertEqual(stats["figures_deduped"], 1)
        self.assertEqual(stats["figures_added"], 1)

    def test_merge_appends_raw_only_figures_and_dedupes(self):
        figures, _ = parse_figures("明\n王阳明：原始王阳明")
        merged, stats = merge_catalog([], [self.imported_entry("王", figures)])

        self.assertEqual(len(merged), 1)
        self.assertEqual(stats["added"], 1)
        figure = merged[0]["figures"][0]
        self.assertEqual(figure["name"], "王阳明")
        self.assertEqual(figure["slug"], "wang-wangyangming")

"""Parse the original course archive into catalog-shaped data.

The archive is a directory of surname folders, each holding up to six text
files. This module is deliberately Django-free: it only reads files and
returns plain dictionaries, so it can be tested with temporary directories
and reused by ``scripts/generate_catalog.py``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pypinyin import lazy_pinyin

SOURCE_FIELD_FILES = {
    "基本信息": "base_information",
    "姓氏起源": "ori",
    "迁徙传播": "mig",
    "人口分布": "dis",
    "历代名人": "fam",
    "姓氏文化": "cul",
}

FOLDER_NAME_OVERRIDES = {"上官": "又"}

DYNASTY_ALIASES: dict[str, str] = {
    "夏": "夏朝",
    "夏朝": "夏朝",
    "商": "商朝",
    "商朝": "商朝",
    "周": "周朝",
    "西周": "周朝",
    "东周": "周朝",
    "周朝": "周朝",
    "春秋": "春秋",
    "战国": "战国",
    "秦": "秦朝",
    "秦朝": "秦朝",
    "汉": "汉朝",
    "西汉": "汉朝",
    "东汉": "汉朝",
    "玄汉": "汉朝",
    "新朝": "汉朝",
    "汉朝": "汉朝",
    "魏": "三国",
    "蜀": "三国",
    "吴": "三国",
    "三国": "三国",
    "晋": "晋朝",
    "西晋": "晋朝",
    "东晋": "晋朝",
    "晋朝": "晋朝",
    "北魏": "南北朝",
    "西魏": "南北朝",
    "东魏": "南北朝",
    "北齐": "南北朝",
    "北周": "南北朝",
    "梁": "南北朝",
    "陈": "南北朝",
    "齐": "南北朝",
    "南北朝": "南北朝",
    "隋": "隋朝",
    "隋朝": "隋朝",
    "唐": "唐朝",
    "唐朝": "唐朝",
    "后唐": "五代十国",
    "后梁": "五代十国",
    "后周": "五代十国",
    "后晋": "五代十国",
    "后汉": "五代十国",
    "后蜀": "五代十国",
    "南唐": "五代十国",
    "前蜀": "五代十国",
    "吴越": "五代十国",
    "南平": "五代十国",
    "南汉（荆南）": "五代十国",
    "五代十国": "五代十国",
    "宋": "宋朝",
    "北宋": "宋朝",
    "南宋": "宋朝",
    "宋朝": "宋朝",
    "辽": "辽朝",
    "辽朝": "辽朝",
    "金": "金朝",
    "金朝": "金朝",
    "西夏": "西夏",
    "元": "元朝",
    "元朝": "元朝",
    "明": "明朝",
    "明朝": "明朝",
    "清": "清朝",
    "清朝": "清朝",
    "中华民国": "中华民国",
    "中华人民共和国": "中华人民共和国",
}

SURNAME_PINYIN_OVERRIDES: dict[str, tuple[str, str]] = {
    "乐": ("yue", "Y"),
    "仇": ("qiu", "Q"),
    "单": ("shan", "S"),
    "卜": ("bu", "B"),
    "解": ("xie", "X"),
    "翟": ("zhai", "Z"),
    "都": ("du", "D"),
    "能": ("nai", "N"),
    "薄": ("bo", "B"),
}

MARKUP_MARKERS = (
    "<script",
    "onerror=",
    "onload=",
    "javascript:",
    "<iframe",
    "<img",
)

IMPORTED_SOURCE_NOTE = (
    "上海财经大学《数据库原理》2021 Fall 课程原始资料（未校订）；"
    "分布、人物等信息以原文为准。"
)
IMPORTED_FIGURE_NOTE = "课程原始资料《历代名人.txt》（未校订）。"

_COLON_RE = re.compile(r"[:：]")
_SENTENCE_RE = re.compile(r"(?<=[。！？；])")


@dataclass(frozen=True)
class FigureSource:
    name: str
    dynasty: str | None
    info: str
    order: int


@dataclass(frozen=True)
class ParseStats:
    headers: int
    person_lines: int
    valid: int
    skipped_empty: int
    duplicates_merged: int


@dataclass
class SurnameSource:
    name: str
    folder: Path
    fields: dict[str, str]
    figures: list[FigureSource]
    stats: ParseStats


def sanitize_text(text: str) -> str:
    """Normalize a source text file and reject markup-looking content."""
    normalized = (
        text.replace("﻿", "")
        .replace("\x00", "")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )
    normalized = "\n".join(line.rstrip() for line in normalized.split("\n"))
    normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()

    lowered = normalized.lower()
    for marker in MARKUP_MARKERS:
        if marker in lowered:
            raise ValueError(f"含有禁止的 HTML/脚本标记：{marker}")
    return normalized


def _read_text(path: Path) -> str:
    data = path.read_bytes()
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("gb18030")


def read_surname_folder(folder: Path) -> dict[str, str]:
    """Read the six optional text files, returning every field key."""
    fields: dict[str, str] = {}
    for stem, field in SOURCE_FIELD_FILES.items():
        path = Path(folder) / f"{stem}.txt"
        if not path.exists():
            fields[field] = ""
            continue
        try:
            fields[field] = sanitize_text(_read_text(path))
        except ValueError as exc:
            raise ValueError(f"{Path(folder).name}/{path.name}: {exc}") from exc
    return fields


def parse_figures(text: str) -> tuple[list[FigureSource], ParseStats]:
    """Parse ``朝代`` header lines and ``姓名：简介`` person lines."""
    figures: dict[str, FigureSource] = {}
    headers = 0
    person_lines = 0
    valid = 0
    skipped_empty = 0
    duplicates_merged = 0
    current_dynasty: str | None = None
    order = 0

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        match = _COLON_RE.search(line)
        if match is None:
            header = line
            if header not in DYNASTY_ALIASES:
                raise ValueError(f"第 {line_number} 行未知朝代标题：{header}")
            current_dynasty = DYNASTY_ALIASES[header]
            headers += 1
            continue

        person_lines += 1
        order += 1
        name = line[: match.start()].strip()
        info = line[match.end() :].strip()
        if not name or not info:
            skipped_empty += 1
            continue

        valid += 1
        if current_dynasty is None:
            raise ValueError(f"第 {line_number} 行人物缺少朝代标题：{line[:30]}")

        candidate = FigureSource(
            name=name, dynasty=current_dynasty, info=info, order=order
        )
        existing = figures.get(name)
        if existing is not None:
            duplicates_merged += 1
            if len(info) > len(existing.info):
                figures[name] = FigureSource(
                    name=name,
                    dynasty=existing.dynasty,
                    info=info,
                    order=existing.order,
                )
        else:
            figures[name] = candidate

    return list(figures.values()), ParseStats(
        headers=headers,
        person_lines=person_lines,
        valid=valid,
        skipped_empty=skipped_empty,
        duplicates_merged=duplicates_merged,
    )


def scan_source_dir(root: Path) -> list[SurnameSource]:
    """Scan surname directories, ignoring files and empty folders."""
    sources: list[SurnameSource] = []
    for folder in sorted(Path(root).iterdir()):
        if not folder.is_dir():
            continue
        name = FOLDER_NAME_OVERRIDES.get(folder.name, folder.name)
        fields = read_surname_folder(folder)
        figures, stats = parse_figures(fields["fam"])
        if not figures and not any(fields.values()):
            continue
        sources.append(
            SurnameSource(
                name=name,
                folder=folder,
                fields=fields,
                figures=figures,
                stats=stats,
            )
        )
    sources.sort(key=lambda source: source.name)
    return sources


def build_summary(source: SurnameSource) -> str:
    """Build a 60-120 character summary without inventing facts."""
    base = re.sub(r"\s+", " ", source.fields.get("base_information", "")).strip()
    origin = re.sub(r"\s+", " ", source.fields.get("ori", "")).strip()
    text = base or origin

    if text:
        summary = ""
        for sentence in _SENTENCE_RE.split(text):
            if not sentence:
                continue
            if summary and len(summary) + len(sentence) > 100:
                break
            summary += sentence
            if len(summary) >= 60:
                break
        summary = summary.strip() or text[:100]
    else:
        summary = ""

    if len(summary) < 20:
        culture = re.sub(r"\s+", " ", source.fields.get("cul", "")).strip()
        if culture:
            summary = f"{summary} {culture}".strip() if summary else culture

    if not summary:
        summary = f"{source.name}姓的课程原始资料。"
    return summary[:120].strip()


def pinyin_for_surname(name: str) -> tuple[str, str]:
    override = SURNAME_PINYIN_OVERRIDES.get(name)
    if override is not None:
        return override
    pinyin = "".join(lazy_pinyin(name)).lower()
    return pinyin, pinyin[:1].upper() if pinyin else ""


def slug_for_surname(name: str, used: set[str]) -> str:
    pinyin, _ = pinyin_for_surname(name)
    base = re.sub(r"[^a-z0-9]+", "-", pinyin).strip("-") or "surname"
    candidate = base
    index = 2
    while candidate in used:
        candidate = f"{base}-{index}"
        index += 1
    used.add(candidate)
    return candidate


def build_imported_entry(
    source: SurnameSource, *, slug: str, pinyin: str, initial: str
) -> dict:
    """Build a catalog entry for a course-archive surname."""
    fields = source.fields
    return {
        "second_name": source.name,
        "slug": slug,
        "pinyin": pinyin,
        "initial": initial.upper(),
        "aliases": [],
        "summary": build_summary(source),
        "base_information": fields.get("base_information", ""),
        "ori": fields.get("ori", ""),
        "mig": fields.get("mig", ""),
        "dis": fields.get("dis", ""),
        "cul": fields.get("cul", ""),
        "fam": "",
        "keywords": [],
        "source_note": IMPORTED_SOURCE_NOTE,
        "is_demo": True,
        "is_imported": True,
        "is_featured": False,
        "popularity": 0,
        "figures": [
            {
                "name": figure.name,
                "dynasty": figure.dynasty,
                "info": figure.info,
                "source_note": IMPORTED_FIGURE_NOTE,
                "is_demo": True,
                "order": figure.order,
            }
            for figure in source.figures
        ],
        "distributions": [],
        "migration_events": [],
        "relations": [],
    }


def _unique_slug(base: str, used: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-") or "figure"
    candidate = base
    index = 2
    while candidate in used:
        candidate = f"{base}-{index}"
        index += 1
    used.add(candidate)
    return candidate


def _figure_slug(surname_slug: str, name: str) -> str:
    name_pinyin = "".join(lazy_pinyin(name)).lower()
    return f"{surname_slug}-{name_pinyin}"


def merge_catalog(
    curated: list[dict], imported: list[dict]
) -> tuple[list[dict], dict]:
    """Merge raw entries into curated ones, keeping curated content authoritative."""
    merged = [
        {
            **item,
            "figures": [dict(figure) for figure in item.get("figures", [])],
        }
        for item in curated
    ]
    by_name = {item["second_name"]: item for item in merged}
    used_figure_slugs = {
        figure["slug"]
        for item in merged
        for figure in item.get("figures", [])
        if figure.get("slug")
    }
    stats = {
        "added": 0,
        "merged": 0,
        "figures_added": 0,
        "figures_deduped": 0,
    }

    for item in imported:
        name = item["second_name"]
        existing = by_name.get(name)
        if existing is not None:
            curated_names = {
                figure["name"] for figure in existing.get("figures", [])
            }
            for figure in item.get("figures", []):
                if figure["name"] in curated_names:
                    stats["figures_deduped"] += 1
                    continue
                new_figure = dict(figure)
                new_figure["slug"] = _unique_slug(
                    _figure_slug(existing["slug"], figure["name"]),
                    used_figure_slugs,
                )
                existing.setdefault("figures", []).append(new_figure)
                curated_names.add(figure["name"])
                stats["figures_added"] += 1
            stats["merged"] += 1
            continue

        entry = dict(item)
        figures = []
        for figure in entry.get("figures", []):
            new_figure = dict(figure)
            new_figure["slug"] = _unique_slug(
                _figure_slug(entry["slug"], figure["name"]),
                used_figure_slugs,
            )
            figures.append(new_figure)
            stats["figures_added"] += 1
        entry["figures"] = figures
        merged.append(entry)
        by_name[name] = entry
        stats["added"] += 1

    return merged, stats

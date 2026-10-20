from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.db import transaction
from pypinyin import lazy_pinyin

from Surname.models import (
    Clan,
    Distribution,
    Dynasty,
    Famous,
    MigrationEvent,
    Province,
    SecondName,
    SurnameRelation,
)

PROVINCE_NAMES = (
    "北京市",
    "天津市",
    "河北省",
    "山西省",
    "内蒙古自治区",
    "辽宁省",
    "吉林省",
    "黑龙江省",
    "上海市",
    "江苏省",
    "浙江省",
    "安徽省",
    "福建省",
    "江西省",
    "山东省",
    "河南省",
    "湖北省",
    "湖南省",
    "广东省",
    "广西壮族自治区",
    "海南省",
    "重庆市",
    "四川省",
    "贵州省",
    "云南省",
    "西藏自治区",
    "陕西省",
    "甘肃省",
    "青海省",
    "宁夏回族自治区",
    "新疆维吾尔自治区",
    "香港特别行政区",
    "澳门特别行政区",
    "台湾省",
)

DYNASTY_NAMES = (
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
    "元朝",
    "明朝",
    "清朝",
    "中华民国",
)

RELATION_TYPES = {"origin", "branch", "changed", "same_clan"}
CLAN_KINDS = {"xing", "shi", "state", "other"}
MARKUP_MARKERS = (
    "<script",
    "onerror=",
    "onload=",
    "javascript:",
    "<iframe",
    "<img",
)


class CatalogValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("\n".join(self.errors))


@dataclass(frozen=True)
class CatalogStats:
    surnames: int
    figures: int
    events: int
    relations: int


def _read_catalog(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _scan_markup(value: Any, location: str, errors: list[str]) -> None:
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in MARKUP_MARKERS):
            errors.append(f"{location}: 含有禁止的 HTML/脚本标记")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_markup(item, f"{location}[{index}]", errors)
    elif isinstance(value, dict):
        for key, item in value.items():
            _scan_markup(item, f"{location}.{key}", errors)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_catalog(path: Path, *, min_surnames: int = 0) -> list[str]:
    """Return a list of human-readable errors; an empty list means valid."""
    try:
        data = _read_catalog(path)
    except OSError as exc:
        return [f"无法读取目录文件：{exc}"]
    except json.JSONDecodeError as exc:
        return [f"目录文件不是合法 JSON：{exc}"]

    if not isinstance(data, dict):
        return ["目录根节点必须是 JSON 对象。"]

    errors: list[str] = []
    _scan_markup(data, "catalog", errors)

    clans = data.get("clans", [])
    surnames = data.get("surnames")
    if not isinstance(clans, list):
        errors.append("catalog.clans 必须是列表。")
        clans = []
    if not isinstance(surnames, list):
        errors.append("catalog.surnames 必须是列表。")
        return errors

    clan_names: set[str] = set()
    clan_slugs: set[str] = set()
    for index, clan in enumerate(clans):
        prefix = f"clans[{index}]"
        if not isinstance(clan, dict):
            errors.append(f"{prefix}: 必须是对象。")
            continue
        name = clan.get("name")
        slug = clan.get("slug")
        kind = clan.get("kind")
        if not _non_empty_string(name):
            errors.append(f"{prefix}: name 不能为空。")
        elif name in clan_names:
            errors.append(f"{prefix}: 宗族名称重复：{name}")
        else:
            clan_names.add(name)
        if not _non_empty_string(slug):
            errors.append(f"{prefix}: slug 不能为空。")
        elif slug in clan_slugs:
            errors.append(f"{prefix}: 宗族 slug 重复：{slug}")
        else:
            clan_slugs.add(slug)
        if kind not in CLAN_KINDS:
            errors.append(f"{prefix}: kind 必须是 {sorted(CLAN_KINDS)} 之一。")

    surname_names = {
        item["second_name"]
        for item in surnames
        if isinstance(item, dict) and _non_empty_string(item.get("second_name"))
    }
    seen_surname_names: set[str] = set()
    surname_slugs: set[str] = set()
    figure_slugs: set[str] = set()
    for index, item in enumerate(surnames):
        prefix = f"surnames[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: 必须是对象。")
            continue

        name = item.get("second_name")
        slug = item.get("slug")
        pinyin = item.get("pinyin")
        initial = item.get("initial")
        if not _non_empty_string(name):
            errors.append(f"{prefix}: second_name 不能为空。")
        elif name in seen_surname_names:
            errors.append(f"{prefix}: 姓氏重复：{name}")
        else:
            seen_surname_names.add(name)

        if not _non_empty_string(slug):
            errors.append(f"{prefix}: slug 不能为空。")
        elif slug in surname_slugs:
            errors.append(f"{prefix}: 姓氏 slug 重复：{slug}")
        else:
            surname_slugs.add(slug)

        if not _non_empty_string(pinyin):
            errors.append(f"{prefix}: pinyin 不能为空。")
        if not isinstance(initial, str) or not initial.isascii() or not initial.isalpha():
            errors.append(f"{prefix}: initial 必须是 A-Z 单字母。")

        aliases = item.get("aliases", [])
        if not isinstance(aliases, list) or any(not isinstance(a, str) for a in aliases):
            errors.append(f"{prefix}: aliases 必须是字符串列表。")

        keywords = item.get("keywords", [])
        if not isinstance(keywords, list):
            errors.append(f"{prefix}: keywords 必须是列表。")
        else:
            if len(keywords) > 20:
                errors.append(f"{prefix}: keywords 最多 20 个。")
            for keyword_index, keyword in enumerate(keywords):
                if (
                    not isinstance(keyword, dict)
                    or not _non_empty_string(keyword.get("name"))
                    or not _is_int(keyword.get("value"))
                    or not 1 <= keyword["value"] <= 100
                ):
                    errors.append(
                        f"{prefix}.keywords[{keyword_index}]: "
                        "必须是 name/value（1-100）对象。"
                    )

        if item.get("is_demo", True) and not _non_empty_string(item.get("source_note")):
            label = name or prefix
            errors.append(f"{prefix}: 姓氏 {label} 的 is_demo 为真时必须提供 source_note。")

        is_imported = item.get("is_imported", False)
        if not isinstance(is_imported, bool):
            errors.append(f"{prefix}: is_imported 必须是布尔值。")
        elif is_imported:
            if not item.get("is_demo", True):
                errors.append(f"{prefix}: is_imported 为真时必须保留 is_demo。")
            if not _non_empty_string(item.get("source_note")):
                errors.append(f"{prefix}: is_imported 为真时必须提供 source_note。")

        distributions = item.get("distributions", [])
        seen_provinces: set[str] = set()
        if not isinstance(distributions, list):
            errors.append(f"{prefix}: distributions 必须是列表。")
            distributions = []
        for dist_index, dist in enumerate(distributions):
            dist_prefix = f"{prefix}.distributions[{dist_index}]"
            if not isinstance(dist, dict):
                errors.append(f"{dist_prefix}: 必须是对象。")
                continue
            province = dist.get("province")
            intensity = dist.get("intensity")
            if province not in PROVINCE_NAMES:
                errors.append(f"{dist_prefix}: 未知省份：{province}")
            elif province in seen_provinces:
                errors.append(f"{dist_prefix}: 同一姓氏的省份重复：{province}")
            else:
                seen_provinces.add(province)
            if not _is_int(intensity) or not 0 <= intensity <= 100:
                errors.append(f"{dist_prefix}: intensity 必须是 0-100 的整数。")

        figures = item.get("figures", [])
        if not isinstance(figures, list):
            errors.append(f"{prefix}: figures 必须是列表。")
            figures = []
        for figure_index, figure in enumerate(figures):
            figure_prefix = f"{prefix}.figures[{figure_index}]"
            if not isinstance(figure, dict):
                errors.append(f"{figure_prefix}: 必须是对象。")
                continue
            for field in ("name", "slug", "info", "source_note"):
                if not _non_empty_string(figure.get(field)):
                    errors.append(f"{figure_prefix}: {field} 不能为空。")
            figure_slug = figure.get("slug")
            if _non_empty_string(figure_slug):
                if figure_slug in figure_slugs:
                    errors.append(f"{figure_prefix}: 人物 slug 重复：{figure_slug}")
                else:
                    figure_slugs.add(figure_slug)
            dynasty = figure.get("dynasty")
            if dynasty and dynasty not in DYNASTY_NAMES:
                errors.append(f"{figure_prefix}: 未知朝代：{dynasty}")

        events = item.get("migration_events", [])
        seen_orders: set[int] = set()
        if not isinstance(events, list):
            errors.append(f"{prefix}: migration_events 必须是列表。")
            events = []
        for event_index, event in enumerate(events):
            event_prefix = f"{prefix}.migration_events[{event_index}]"
            if not isinstance(event, dict):
                errors.append(f"{event_prefix}: 必须是对象。")
                continue
            if not _non_empty_string(event.get("description")):
                errors.append(f"{event_prefix}: description 不能为空。")
            if not _non_empty_string(event.get("source_note")):
                errors.append(f"{event_prefix}: source_note 不能为空。")
            dynasty = event.get("dynasty")
            if dynasty and dynasty not in DYNASTY_NAMES:
                errors.append(f"{event_prefix}: 未知朝代：{dynasty}")
            for field in ("from_province", "to_province"):
                province = event.get(field)
                if province and province not in PROVINCE_NAMES:
                    errors.append(f"{event_prefix}: 未知省份：{province}")
            order = event.get("order", 0)
            if not _is_int(order) or order < 0:
                errors.append(f"{event_prefix}: order 必须是非负整数。")
            elif order in seen_orders:
                errors.append(f"{event_prefix}: 同一姓氏的 order 重复：{order}")
            else:
                seen_orders.add(order)

        relations = item.get("relations", [])
        if not isinstance(relations, list):
            errors.append(f"{prefix}: relations 必须是列表。")
            relations = []
        for relation_index, relation in enumerate(relations):
            relation_prefix = f"{prefix}.relations[{relation_index}]"
            if not isinstance(relation, dict):
                errors.append(f"{relation_prefix}: 必须是对象。")
                continue
            target_surname = relation.get("target_surname")
            target_clan = relation.get("target_clan")
            if bool(target_surname) == bool(target_clan):
                errors.append(
                    f"{relation_prefix}: target_surname 与 target_clan 必须恰好一个。"
                )
            if target_surname and target_surname not in surname_names:
                errors.append(f"{relation_prefix}: 未知目标姓氏：{target_surname}")
            if target_clan and target_clan not in clan_names:
                errors.append(f"{relation_prefix}: 未知目标宗族：{target_clan}")
            if relation.get("relation_type") not in RELATION_TYPES:
                errors.append(
                    f"{relation_prefix}: relation_type 必须是 "
                    f"{sorted(RELATION_TYPES)} 之一。"
                )
            if not _non_empty_string(relation.get("source_note")):
                errors.append(f"{relation_prefix}: source_note 不能为空。")

    if len(surnames) < min_surnames:
        errors.append(f"姓氏数量不足：{len(surnames)} < {min_surnames}")

    return errors


def _slug_from_name(name: str) -> str:
    return "".join(lazy_pinyin(name)).lower() or "reference"


def _unique_reference_slug(model, name: str) -> str:
    base = _slug_from_name(name)
    candidate = base
    index = 2
    while model.objects.filter(slug=candidate).exists():
        candidate = f"{base}-{index}"
        index += 1
    return candidate


def _ensure_reference_rows(data: dict[str, Any]) -> None:
    province_names: set[str] = set()
    dynasty_names: set[str] = set()
    for item in data["surnames"]:
        for dist in item.get("distributions", []):
            province_names.add(dist["province"])
        for event in item.get("migration_events", []):
            for field in ("from_province", "to_province"):
                if event.get(field):
                    province_names.add(event[field])
            if event.get("dynasty"):
                dynasty_names.add(event["dynasty"])
        for figure in item.get("figures", []):
            if figure.get("dynasty"):
                dynasty_names.add(figure["dynasty"])

    for name in sorted(province_names):
        Province.objects.get_or_create(
            name=name,
            defaults={"slug": _unique_reference_slug(Province, name)},
        )
    for name in sorted(dynasty_names):
        Dynasty.objects.get_or_create(
            name=name,
            defaults={
                "slug": _unique_reference_slug(Dynasty, name),
                "order": DYNASTY_NAMES.index(name) + 1,
            },
        )


def _sync_surname(item: dict[str, Any]) -> SecondName:
    defaults = {
        "slug": item["slug"],
        "pinyin": item["pinyin"],
        "initial": item["initial"].upper(),
        "aliases": ",".join(item.get("aliases") or []),
        "summary": item.get("summary", ""),
        "base_information": item.get("base_information", ""),
        "fam": item.get("fam", ""),
        "mig": item.get("mig", ""),
        "dis": item.get("dis", ""),
        "ori": item.get("ori", ""),
        "cul": item.get("cul", ""),
        "keywords": item.get("keywords") or [],
        "source_note": item.get("source_note", ""),
        "is_demo": item.get("is_demo", True),
        "is_imported": item.get("is_imported", False),
        "is_featured": item.get("is_featured", False),
        "popularity": item.get("popularity", 0),
    }
    surname, _ = SecondName.objects.update_or_create(
        second_name=item["second_name"], defaults=defaults
    )
    return surname


def _sync_children(surname: SecondName, item: dict[str, Any], prune: bool) -> None:
    kept_distributions = []
    for dist in item.get("distributions", []):
        province = Province.objects.get(name=dist["province"])
        distribution, _ = Distribution.objects.update_or_create(
            surname=surname,
            province=province,
            defaults={
                "intensity": dist["intensity"],
                "is_illustrative": dist.get("is_illustrative", True),
                "source_note": dist.get("source_note", ""),
            },
        )
        kept_distributions.append(distribution.pk)
    if prune:
        surname.distributions.exclude(pk__in=kept_distributions).delete()

    kept_figures = []
    for figure in item.get("figures", []):
        dynasty = (
            Dynasty.objects.get(name=figure["dynasty"])
            if figure.get("dynasty")
            else None
        )
        famous, _ = Famous.objects.update_or_create(
            slug=figure["slug"],
            defaults={
                "surname": surname,
                "name": figure["name"],
                "dynasty": dynasty,
                "info": figure["info"],
                "birth_year": figure.get("birth_year"),
                "death_year": figure.get("death_year"),
                "source_note": figure.get("source_note", ""),
                "is_demo": figure.get("is_demo", True),
                "order": figure.get("order", 0),
            },
        )
        kept_figures.append(famous.pk)
    if prune:
        surname.figures.exclude(pk__in=kept_figures).delete()

    kept_events = []
    for event in item.get("migration_events", []):
        dynasty = (
            Dynasty.objects.get(name=event["dynasty"])
            if event.get("dynasty")
            else None
        )
        from_province = (
            Province.objects.get(name=event["from_province"])
            if event.get("from_province")
            else None
        )
        to_province = (
            Province.objects.get(name=event["to_province"])
            if event.get("to_province")
            else None
        )
        migration_event, _ = MigrationEvent.objects.update_or_create(
            surname=surname,
            order=event.get("order", 0),
            defaults={
                "dynasty": dynasty,
                "from_province": from_province,
                "to_province": to_province,
                "description": event["description"],
                "source_note": event.get("source_note", ""),
            },
        )
        kept_events.append(migration_event.pk)
    if prune:
        surname.migration_events.exclude(pk__in=kept_events).delete()

    kept_relations = []
    for relation in item.get("relations", []):
        target_surname = (
            SecondName.objects.get(second_name=relation["target_surname"])
            if relation.get("target_surname")
            else None
        )
        target_clan = (
            Clan.objects.get(name=relation["target_clan"])
            if relation.get("target_clan")
            else None
        )
        relation_obj, _ = SurnameRelation.objects.update_or_create(
            source=surname,
            target_surname=target_surname,
            target_clan=target_clan,
            relation_type=relation["relation_type"],
            defaults={
                "description": relation.get("description", ""),
                "source_note": relation.get("source_note", ""),
            },
        )
        kept_relations.append(relation_obj.pk)
    if prune:
        surname.outgoing_relations.exclude(pk__in=kept_relations).delete()


def load_catalog(
    path: Path, *, prune: bool = False, dry_run: bool = False
) -> CatalogStats:
    """Load a catalog JSON file. Validation precedes any database write."""
    errors = validate_catalog(path)
    if errors:
        raise CatalogValidationError(errors)

    data = _read_catalog(path)
    stats = CatalogStats(
        surnames=len(data["surnames"]),
        figures=sum(len(item.get("figures", [])) for item in data["surnames"]),
        events=sum(len(item.get("migration_events", [])) for item in data["surnames"]),
        relations=sum(len(item.get("relations", [])) for item in data["surnames"]),
    )
    if dry_run:
        return stats

    with transaction.atomic():
        _ensure_reference_rows(data)

        clan_names = []
        for clan_data in data.get("clans", []):
            Clan.objects.update_or_create(
                name=clan_data["name"],
                defaults={
                    "slug": clan_data["slug"],
                    "kind": clan_data["kind"],
                    "description": clan_data.get("description", ""),
                },
            )
            clan_names.append(clan_data["name"])

        surnames = {
            item["second_name"]: _sync_surname(item) for item in data["surnames"]
        }
        for item in data["surnames"]:
            _sync_children(surnames[item["second_name"]], item, prune)

        if prune:
            SecondName.objects.exclude(
                second_name__in=[item["second_name"] for item in data["surnames"]]
            ).delete()
            Clan.objects.exclude(name__in=clan_names).delete()

    return stats

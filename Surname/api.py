from __future__ import annotations

from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from Surname.models import (
    Distribution,
    Dynasty,
    Famous,
    MigrationEvent,
    Province,
    SecondName,
    SurnameRelation,
)

PAGE_SIZE_DEFAULT = 20
PAGE_SIZE_MAX = 100


def ok(data, **extra):
    payload = {"code": 0, "message": "ok", "data": data}
    payload.update(extra)
    return JsonResponse(payload)


def fail(message: str, status: int = 400, code: int = 1):
    return JsonResponse(
        {"code": code, "message": message, "data": None}, status=status
    )


def _page_context(request, queryset, default_size: int = PAGE_SIZE_DEFAULT):
    try:
        page_size = int(request.GET.get("page_size", default_size))
    except (TypeError, ValueError):
        page_size = default_size
    page_size = max(1, min(page_size, PAGE_SIZE_MAX))
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(request.GET.get("page"))
    return page_obj, {
        "page": page_obj.number,
        "page_size": page_size,
        "pages": paginator.num_pages,
        "total": paginator.count,
    }


def serialize_surname(surname: SecondName, detail: bool = False) -> dict:
    data = {
        "second_name": surname.second_name,
        "slug": surname.slug,
        "pinyin": surname.pinyin,
        "initial": surname.initial,
        "summary": surname.summary,
    }
    if not detail:
        return data

    data.update(
        {
            "aliases": [item for item in surname.aliases.split(",") if item],
            "base_information": surname.base_information,
            "origin": surname.ori,
            "migration_text": surname.mig,
            "distribution_text": surname.dis,
            "culture": surname.cul,
            "keywords": surname.keywords,
            "source_note": surname.source_note,
            "is_demo": surname.is_demo,
            "distributions": [
                {
                    "province": row.province.name,
                    "map_name": row.province.map_name or row.province.name,
                    "intensity": row.intensity,
                }
                for row in surname.distributions.all()
            ],
            "figures": [
                {
                    "name": figure.name,
                    "slug": figure.slug,
                    "dynasty": figure.dynasty.name if figure.dynasty else None,
                    "birth_year": figure.birth_year,
                    "death_year": figure.death_year,
                }
                for figure in surname.figures.all()
            ],
            "migration_events": [
                {
                    "dynasty": event.dynasty.name if event.dynasty else None,
                    "from_province": (
                        event.from_province.name if event.from_province else None
                    ),
                    "to_province": (
                        event.to_province.name if event.to_province else None
                    ),
                    "description": event.description,
                    "order": event.order,
                }
                for event in surname.migration_events.all()
            ],
            "relations": [
                {
                    "relation_type": relation.relation_type,
                    "relation_label": relation.get_relation_type_display(),
                    "target_surname": (
                        relation.target_surname.second_name
                        if relation.target_surname
                        else None
                    ),
                    "target_clan": (
                        relation.target_clan.name if relation.target_clan else None
                    ),
                    "description": relation.description,
                }
                for relation in surname.outgoing_relations.all()
            ],
        }
    )
    return data


def _filter_surnames(request, queryset):
    query = (request.GET.get("q") or "").strip()
    if query:
        queryset = queryset.filter(
            Q(second_name__icontains=query)
            | Q(pinyin__icontains=query)
            | Q(initial__icontains=query)
            | Q(aliases__icontains=query)
            | Q(summary__icontains=query)
        )
    initial = (request.GET.get("initial") or "").strip().upper()
    if initial:
        queryset = queryset.filter(initial=initial)
    province = (request.GET.get("province") or "").strip()
    if province:
        queryset = queryset.filter(distributions__province__slug=province)
    return queryset.distinct()


@require_GET
def surname_list(request):
    queryset = _filter_surnames(request, SecondName.objects.all()).order_by(
        "-popularity", "second_name"
    )
    page_obj, meta = _page_context(request, queryset)
    return ok(
        {
            "results": [serialize_surname(item) for item in page_obj.object_list],
            **meta,
        }
    )


@require_GET
def surname_detail(request, slug: str):
    queryset = SecondName.objects.prefetch_related(
        Prefetch(
            "distributions",
            queryset=Distribution.objects.select_related("province").order_by(
                "-intensity"
            ),
        ),
        Prefetch(
            "figures",
            queryset=Famous.objects.select_related("dynasty").order_by(
                "dynasty__order", "order", "name"
            ),
        ),
        Prefetch(
            "migration_events",
            queryset=MigrationEvent.objects.select_related(
                "dynasty", "from_province", "to_province"
            ).order_by("dynasty__order", "order"),
        ),
        Prefetch(
            "outgoing_relations",
            queryset=SurnameRelation.objects.select_related(
                "target_surname", "target_clan"
            ),
        ),
    )
    try:
        surname = queryset.get(slug=slug)
    except SecondName.DoesNotExist:
        return fail("未找到该姓氏。", status=404, code=404)
    return ok(serialize_surname(surname, detail=True))


@require_GET
def search(request):
    query = (request.GET.get("q") or "").strip()
    if not query:
        return ok({"results": [], "page": 1, "page_size": 0, "pages": 0, "total": 0})
    queryset = _filter_surnames(request, SecondName.objects.all()).order_by(
        "second_name"
    )
    page_obj, meta = _page_context(request, queryset)
    return ok(
        {
            "results": [serialize_surname(item) for item in page_obj.object_list],
            **meta,
        }
    )


@require_GET
def figure_list(request):
    queryset = Famous.objects.select_related("surname", "dynasty")
    dynasty = (request.GET.get("dynasty") or "").strip()
    if dynasty:
        queryset = queryset.filter(dynasty__slug=dynasty)
    surname = (request.GET.get("surname") or "").strip()
    if surname:
        queryset = queryset.filter(surname__slug=surname)
    queryset = queryset.order_by("surname__second_name", "dynasty__order", "name")
    page_obj, meta = _page_context(request, queryset)
    results = [
        {
            "name": figure.name,
            "slug": figure.slug,
            "dynasty": figure.dynasty.name if figure.dynasty else None,
            "surname": figure.surname.second_name,
            "surname_slug": figure.surname.slug,
            "birth_year": figure.birth_year,
            "death_year": figure.death_year,
            "info": figure.info,
        }
        for figure in page_obj.object_list
    ]
    return ok({"results": results, **meta})


@require_GET
def meta(request):
    return ok(
        {
            "provinces": [
                {"name": province.name, "slug": province.slug}
                for province in Province.objects.all()
            ],
            "dynasties": [
                {
                    "name": dynasty.name,
                    "slug": dynasty.slug,
                    "order": dynasty.order,
                }
                for dynasty in Dynasty.objects.all()
            ],
            "initials": sorted(
                SecondName.objects.values_list("initial", flat=True).distinct()
            ),
        }
    )

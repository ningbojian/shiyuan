from string import ascii_uppercase

from django.core.paginator import Paginator
from django.db.models import Count, F, Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.html import strip_tags

from Surname.forms import SurnameFilterForm
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
from user.forms import CommentForm
from user.models import Comment, Favorite
from user.services import record_history


def _relation_graph(relations, source_label=None, source_slug=None):
    """Turn relation rows into the node/edge shape used by the graph charts."""
    nodes = {}
    edges = []

    def surname_node(second_name, slug):
        label = f"{second_name}姓"
        nodes.setdefault(label, {"name": label, "slug": slug, "category": 0})
        return label

    for relation in relations:
        if source_label:
            source = source_label
            nodes.setdefault(
                source, {"name": source, "slug": source_slug, "category": 0}
            )
        else:
            source = surname_node(
                relation.source.second_name, relation.source.slug
            )
        if relation.target_surname:
            target = surname_node(
                relation.target_surname.second_name,
                relation.target_surname.slug,
            )
        else:
            target = relation.target_clan.name
            nodes.setdefault(
                target, {"name": target, "slug": None, "category": 1}
            )
        edges.append(
            {
                "source": source,
                "target": target,
                "label": relation.get_relation_type_display(),
                "description": relation.description,
            }
        )

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "categories": [{"name": "姓氏"}, {"name": "宗族"}],
    }


def _chart_payloads(surname):
    """Build JSON-safe chart data from already-prefetched related rows."""
    distributions = [
        {
            "name": row.province.map_name or row.province.short_name or row.province.name,
            "value": row.intensity,
            "province": row.province.name,
        }
        for row in surname.distributions.all()
    ]

    migration = []
    for event in surname.migration_events.all():
        migration.append(
            {
                "dynasty": event.dynasty.name if event.dynasty else "时期不详",
                "description": event.description,
                "from_name": event.from_province.name if event.from_province else "",
                "from_coord": (
                    [event.from_province.center_lng, event.from_province.center_lat]
                    if event.from_province
                    else None
                ),
                "to_name": event.to_province.name if event.to_province else "",
                "to_coord": (
                    [event.to_province.center_lng, event.to_province.center_lat]
                    if event.to_province
                    else None
                ),
            }
        )

    source_label = f"{surname.second_name}姓"
    relations = _relation_graph(
        surname.outgoing_relations.all(),
        source_label=source_label,
        source_slug=surname.slug,
    )
    if not relations["edges"]:
        relations = {"nodes": [], "edges": [], "categories": []}

    keywords = [
        {"name": item["name"], "value": item["value"]}
        for item in surname.keywords
        if isinstance(item, dict)
        and isinstance(item.get("name"), str)
        and item["name"].strip()
        and isinstance(item.get("value"), int)
        and not isinstance(item.get("value"), bool)
        and 1 <= item["value"] <= 100
    ]

    return {
        "distribution": distributions,
        "migration": migration,
        "relations": relations,
        "keywords": keywords,
    }


def _seo_description(text: str, limit: int = 300) -> str:
    return strip_tags(text or "").strip()[:limit]


def _webpage_jsonld(request, *, name: str, description: str) -> dict:
    url = request.build_absolute_uri(request.path)
    return {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": name,
        "description": description,
        "url": url,
        "inLanguage": "zh-Hans",
        "isPartOf": {
            "@type": "WebSite",
            "name": "氏源",
            "url": request.build_absolute_uri("/"),
        },
    }


def _person_jsonld(request, figure) -> dict:
    url = request.build_absolute_uri(request.path)
    return {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": figure.name,
        "description": _seo_description(figure.info),
        "url": url,
        "mainEntityOfPage": {"@type": "WebPage", "url": url},
    }


def home(request):
    """Landing page: search, letter index, featured surnames, daily pick."""
    featured = list(
        SecondName.objects.filter(is_featured=True).order_by(
            "-popularity", "second_name"
        )[:6]
    )
    total = SecondName.objects.count()
    daily = None
    if total:
        offset = timezone.localdate().toordinal() % total
        daily = SecondName.objects.order_by("second_name")[offset]

    counts = {
        row["initial"]: row["count"]
        for row in SecondName.objects.values("initial").annotate(count=Count("pk"))
    }
    initials = [
        {"letter": letter, "count": counts.get(letter, 0)}
        for letter in ascii_uppercase
    ]
    stats = {
        "surnames": total,
        "figures": Famous.objects.count(),
        "provinces": Province.objects.count(),
    }
    return render(
        request,
        "surname/home.html",
        {
            "featured": featured,
            "daily": daily,
            "initials": initials,
            "stats": stats,
        },
    )


def index(request):
    """Redirect the legacy query-string detail URL to the slug detail URL."""
    second_name = request.GET.get("surname")
    if not second_name:
        raise Http404("没有姓氏")
    surname = get_object_or_404(SecondName, second_name=second_name)
    return redirect("Surname:detail", slug=surname.slug)


def surname_detail(request, slug):
    """Render one surname's detail page.

    All surname text is rendered as escaped plain text. The view counter is
    updated in a single query so charts or helper functions cannot increment
    it again.
    """
    surname = get_object_or_404(
        SecondName.objects.prefetch_related(
            Prefetch(
                "distributions",
                queryset=Distribution.objects.select_related("province").order_by(
                    "-intensity", "province__name"
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
            Prefetch(
                "comments",
                queryset=Comment.objects.filter(status="visible")
                .select_related("user", "user__profile")
                .order_by("-created_at"),
            ),
        ),
        slug=slug,
    )
    SecondName.objects.filter(pk=surname.pk).update(view_count=F("view_count") + 1)
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(
            user=request.user, surname=surname
        ).exists()
        record_history(request.user, surname)
    return render(
        request,
        "surname/index.html",
        {
            "surname": surname,
            "comments": surname.comments.all(),
            "comment_form": CommentForm(),
            "is_favorite": is_favorite,
            "chart_payloads": _chart_payloads(surname),
            "jsonld": _webpage_jsonld(
                request,
                name=f"{surname.second_name}姓",
                description=_seo_description(
                    surname.summary or surname.base_information
                ),
            ),
        },
    )


def announce(request):
    return render(request, "surname/announce.html")


def developer(request):
    return render(request, "surname/developer.html")


def information(request):
    return render(request, "surname/information.html")


def introduction(request):
    return render(request, "surname/introduction.html")


def science(request):
    return render(request, "surname/science.html")


def figure_list(request):
    """Browse historical figures, filterable by dynasty and surname."""
    queryset = Famous.objects.select_related("surname", "dynasty")
    dynasty_slug = (request.GET.get("dynasty") or "").strip()
    surname_slug = (request.GET.get("surname") or "").strip()
    if dynasty_slug:
        queryset = queryset.filter(dynasty__slug=dynasty_slug)
    if surname_slug:
        queryset = queryset.filter(surname__slug=surname_slug)
    queryset = queryset.order_by(
        "surname__second_name", "dynasty__order", "order", "name"
    )

    paginator = Paginator(queryset, 24)
    page_obj = paginator.get_page(request.GET.get("page"))
    dynasties = Dynasty.objects.filter(figures__isnull=False).distinct()
    surnames = (
        SecondName.objects.filter(figures__isnull=False)
        .distinct()
        .order_by("second_name")
    )
    return render(
        request,
        "surname/figures.html",
        {
            "page_obj": page_obj,
            "figures": page_obj.object_list,
            "total_count": paginator.count,
            "dynasties": dynasties,
            "surnames": surnames,
            "dynasty_filter": dynasty_slug,
            "surname_filter": surname_slug,
            "has_filters": bool(dynasty_slug or surname_slug),
        },
    )


def figure_detail(request, slug):
    figure = get_object_or_404(
        Famous.objects.select_related("surname", "dynasty"), slug=slug
    )
    same_dynasty = Famous.objects.none()
    if figure.dynasty_id:
        same_dynasty = (
            Famous.objects.filter(dynasty_id=figure.dynasty_id)
            .exclude(pk=figure.pk)
            .select_related("surname")
            .order_by("surname__second_name", "order", "name")[:8]
        )
    return render(
        request,
        "surname/figure_detail.html",
        {
            "figure": figure,
            "same_dynasty": same_dynasty,
            "jsonld": _person_jsonld(request, figure),
        },
    )


def origins(request):
    """Overview of clan roots and surname-to-surname relations."""
    clans = Clan.objects.order_by("kind", "name")
    relations = SurnameRelation.objects.select_related(
        "source", "target_surname", "target_clan"
    ).order_by("source__second_name", "relation_type")
    return render(
        request,
        "surname/origins.html",
        {
            "clans": clans,
            "relations": relations,
            "relation_graph": _relation_graph(relations),
        },
    )


def _directory_context(request):
    form = SurnameFilterForm(request.GET or None)
    queryset = SecondName.objects.all()

    if form.is_bound and form.is_valid():
        data = form.cleaned_data
        query = data.get("q")
        if query:
            queryset = queryset.filter(
                Q(second_name__icontains=query)
                | Q(pinyin__icontains=query)
                | Q(initial__icontains=query)
                | Q(aliases__icontains=query)
                | Q(summary__icontains=query)
            )
        if data.get("initial"):
            queryset = queryset.filter(initial=data["initial"])
        if data.get("province"):
            queryset = queryset.filter(distributions__province=data["province"])
        sort = data.get("sort") or "popular"
    else:
        sort = request.GET.get("sort") or "popular"

    queryset = queryset.annotate(
        figure_count=Count("figures", distinct=True),
        province_count=Count("distributions", distinct=True),
    )
    if sort == "name":
        queryset = queryset.order_by("second_name")
    else:
        queryset = queryset.order_by("-popularity", "second_name")

    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return {
        "form": form,
        "page_obj": page_obj,
        "surnames": page_obj.object_list,
        "total_count": paginator.count,
        "has_filters": bool(request.GET.get("q") or request.GET.get("initial")
                            or request.GET.get("province")),
    }


def surname_list(request):
    context = _directory_context(request)
    return render(request, "surname/list.html", context)


def search(request):
    context = _directory_context(request)
    return render(request, "surname/search.html", context)

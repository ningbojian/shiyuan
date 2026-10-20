from __future__ import annotations

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from Surname.models import Famous, SecondName

STATIC_VIEW_NAMES = [
    "home",
    "Surname:list",
    "Surname:figures",
    "Surname:origins",
    "Surname:science",
    "Surname:information",
    "Surname:introduction",
    "Surname:announce",
    "Surname:developer",
]


class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return STATIC_VIEW_NAMES

    def location(self, item):
        return reverse(item)


class SurnameSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return SecondName.objects.order_by("second_name")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse("Surname:detail", args=[obj.slug])


class FigureSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return Famous.objects.order_by("slug")

    def location(self, obj):
        return reverse("Surname:figure_detail", args=[obj.slug])

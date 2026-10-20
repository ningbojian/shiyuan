from __future__ import annotations

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from Surname.models import Dynasty, Famous, SecondName


class FigureListTests(TestCase):
    def setUp(self):
        self.li = SecondName.objects.create(second_name="李", pinyin="li", initial="L")
        self.wang = SecondName.objects.create(
            second_name="王", pinyin="wang", initial="W"
        )
        self.tang = Dynasty.objects.create(name="唐朝", slug="tang", order=12)
        self.song = Dynasty.objects.create(name="宋朝", slug="song", order=13)
        Famous.objects.create(
            surname=self.li,
            dynasty=self.tang,
            name="李白",
            slug="li-bai",
            info="唐代诗人",
        )
        Famous.objects.create(
            surname=self.li,
            dynasty=self.song,
            name="李清照",
            slug="li-qingzhao",
            info="宋代词人",
        )
        Famous.objects.create(
            surname=self.wang,
            dynasty=self.tang,
            name="王维",
            slug="wang-wei",
            info="唐代诗人",
        )
        self.url = reverse("Surname:figures")

    def test_figures_list_200_and_contains_all(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        for name in ("李白", "李清照", "王维"):
            self.assertContains(response, name)

    def test_filter_by_dynasty(self):
        response = self.client.get(self.url, {"dynasty": "tang"})
        self.assertContains(response, "李白")
        self.assertContains(response, "王维")
        self.assertNotContains(response, "李清照")

    def test_filter_by_surname(self):
        response = self.client.get(self.url, {"surname": "li"})
        self.assertContains(response, "李白")
        self.assertContains(response, "李清照")
        self.assertNotContains(response, "王维")

    def test_figures_link_to_detail_and_surname(self):
        response = self.client.get(self.url)
        self.assertContains(response, reverse("Surname:figure_detail", args=["li-bai"]))
        self.assertContains(response, reverse("Surname:detail", args=["li"]))

    def test_list_query_budget(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(queries), 5)

    def test_pagination_24(self):
        for index in range(25):
            Famous.objects.create(
                surname=self.li,
                name=f"人物{index:02d}",
                slug=f"figure-{index:02d}",
                info="演示人物",
            )
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["page_obj"].object_list), 24)
        self.assertTrue(response.context["page_obj"].has_next())


class FigureDetailTests(TestCase):
    def setUp(self):
        self.li = SecondName.objects.create(second_name="李", pinyin="li", initial="L")
        self.tang = Dynasty.objects.create(name="唐朝", slug="tang", order=12)
        self.poet = Famous.objects.create(
            surname=self.li,
            dynasty=self.tang,
            name="李白",
            slug="li-bai",
            info="唐代诗人，号青莲居士。",
            birth_year=701,
            death_year=762,
            source_note="演示资料",
        )
        Famous.objects.create(
            surname=self.li,
            dynasty=self.tang,
            name="杜甫",
            slug="du-fu",
            info="唐代诗人",
        )
        self.url = reverse("Surname:figure_detail", args=["li-bai"])

    def test_figure_detail_content(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "李白")
        self.assertContains(response, "701")
        self.assertContains(response, "762")
        self.assertContains(response, "唐代诗人，号青莲居士。")
        self.assertContains(response, "唐朝")
        self.assertContains(response, reverse("Surname:detail", args=["li"]))

    def test_same_dynasty_figures_listed(self):
        response = self.client.get(self.url)
        self.assertContains(response, "杜甫")

    def test_figure_404(self):
        response = self.client.get(
            reverse("Surname:figure_detail", args=["missing-figure"])
        )
        self.assertEqual(response.status_code, 404)

    def test_figure_detail_query_budget(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(queries), 4)


class FigureNavTests(TestCase):
    def test_header_has_figures_link(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("Surname:figures"))

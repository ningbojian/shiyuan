from __future__ import annotations

import re

from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from Surname import views
from Surname.models import Clan, SecondName, SurnameRelation

INTERNAL_HREF_RE = re.compile(r'href="(/(?![/#])[^"]*)"')


class StaticPageTests(TestCase):
    def test_static_pages_200(self):
        for name in (
            "Surname:science",
            "Surname:information",
            "Surname:introduction",
            "Surname:announce",
            "Surname:developer",
            "Surname:origins",
        ):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

    def test_static_pages_share_global_shell(self):
        for name in ("Surname:science", "Surname:introduction", "Surname:announce"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertContains(response, "skip-link")
                self.assertContains(response, "site-footer")
                self.assertContains(response, 'id="site-nav"')

    def test_announce_content_is_current(self):
        response = self.client.get(reverse("Surname:announce"))
        self.assertContains(response, "seed_demo")
        self.assertContains(response, "33")
        self.assertNotContains(response, "scripts/seed_demo.py")
        self.assertNotContains(response, "GET 查询参数")

    def test_search_links_use_real_namespace(self):
        for name in ("Surname:science", "Surname:introduction"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertContains(response, reverse("Surname:search"))

    def test_no_dead_origin_view(self):
        self.assertFalse(hasattr(views, "origin"))
        with self.assertRaises(NoReverseMatch):
            reverse("Surname:origin")


class OriginsPageTests(TestCase):
    def setUp(self):
        self.li = SecondName.objects.create(second_name="李", pinyin="li")
        self.wang = SecondName.objects.create(second_name="王", pinyin="wang")
        clan = Clan.objects.create(name="姬姓", slug="ji-xing", kind="xing")
        SurnameRelation.objects.create(
            source=self.li,
            target_surname=self.wang,
            relation_type="branch",
            description="李姓一支分于王姓",
        )
        SurnameRelation.objects.create(
            source=self.li,
            target_clan=clan,
            relation_type="origin",
            description="源出姬姓",
        )
        self.url = reverse("Surname:origins")

    def test_origins_table_lists_edges(self):
        response = self.client.get(self.url)
        self.assertContains(response, "源流总览")
        self.assertContains(response, "李姓")
        self.assertContains(response, "王姓")
        self.assertContains(response, "姬姓")
        self.assertContains(response, "分支")
        self.assertContains(response, "源出")
        self.assertContains(response, "李姓一支分于王姓")

    def test_origins_explains_relation_types(self):
        response = self.client.get(self.url)
        for label in ("源出", "分支", "改姓", "同源"):
            self.assertContains(response, label)

    def test_origins_links_target_surname(self):
        response = self.client.get(self.url)
        self.assertContains(
            response, reverse("Surname:detail", args=[self.wang.slug])
        )


class NavigationTests(TestCase):
    def setUp(self):
        SecondName.objects.create(
            second_name="李", slug="li", pinyin="li", initial="L", is_featured=True
        )

    def test_nav_links_resolve(self):
        response = self.client.get(reverse("home"))
        html = response.content.decode()
        nav = re.search(r'<nav id="site-nav".*?</nav>', html, re.DOTALL)
        self.assertIsNotNone(nav)
        hrefs = INTERNAL_HREF_RE.findall(nav.group(0))
        self.assertTrue(hrefs)
        for href in hrefs:
            with self.subTest(href=href):
                target = self.client.get(href)
                self.assertEqual(target.status_code, 200)

    def test_header_has_origins_link(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("Surname:origins"))

    def test_footer_links_resolve(self):
        response = self.client.get(reverse("home"))
        html = response.content.decode()
        footer = re.search(
            r'<footer class="site-footer".*?</footer>', html, re.DOTALL
        )
        self.assertIsNotNone(footer)
        hrefs = INTERNAL_HREF_RE.findall(footer.group(0))
        self.assertTrue(hrefs)
        for href in hrefs:
            with self.subTest(href=href):
                target = self.client.get(href)
                self.assertEqual(target.status_code, 200)

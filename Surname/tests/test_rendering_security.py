from __future__ import annotations

from django.test import TestCase
from django.urls import reverse

from Surname.models import SecondName


class RenderingSecurityTests(TestCase):
    def setUp(self):
        self.surname = SecondName.objects.create(
            second_name="李",
            base_information="基本信息",
            fam="历代名人",
            mig="迁徙传播",
            dis="人口分布",
            ori="<script>alert(1)</script>",
            cul="姓氏文化",
        )
        self.url = reverse("Surname:detail", args=[self.surname.slug])

    def test_surname_text_is_escaped(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertNotContains(response, "<script>alert(1)</script>")

    def test_no_pyecharts_or_cdn(self):
        response = self.client.get(self.url)
        self.assertNotContains(response, "pyecharts")
        self.assertNotContains(response, "assets.pyecharts.org")

    def test_view_count_increments_once(self):
        before = self.surname.view_count
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.surname.refresh_from_db()
        self.assertEqual(self.surname.view_count, before + 1)


class DemoDisclosureTests(TestCase):
    def setUp(self):
        self.surname = SecondName.objects.create(
            second_name="王",
            summary="演示摘要",
            source_note="据课程资料整理，演示用",
        )

    def test_detail_shows_demo_badge_and_source_note(self):
        response = self.client.get(
            reverse("Surname:detail", args=[self.surname.slug])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "演示数据")
        self.assertContains(response, "据课程资料整理，演示用")
        self.assertContains(response, "非权威统计")

    def test_information_page_disclaims_demo_data(self):
        response = self.client.get(reverse("Surname:information"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "非权威统计")
        self.assertContains(response, "docs/DATA.md")

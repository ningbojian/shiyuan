from __future__ import annotations

from django.test import TestCase
from django.urls import reverse

from Surname.models import SecondName


class LayoutTests(TestCase):
    def setUp(self):
        self.surname = SecondName.objects.create(
            second_name="李",
            summary="测试摘要",
            source_note="演示来源说明",
        )

    def detail_url(self):
        return reverse("Surname:detail", args=[self.surname.slug])

    def assert_shell(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="skip-link"')
        self.assertContains(response, 'id="main"')
        self.assertContains(response, 'aria-label="主导航"')
        self.assertContains(response, "<footer")
        self.assertContains(response, "css/tokens.css")
        self.assertContains(response, "css/main.css")
        self.assertContains(response, "js/site.js")

    def test_login_uses_site_shell(self):
        self.assert_shell(self.client.get(reverse("user:login")))

    def test_detail_uses_site_shell(self):
        self.assert_shell(self.client.get(self.detail_url()))

    def test_static_page_uses_site_shell(self):
        self.assert_shell(self.client.get(reverse("Surname:information")))

    def test_theme_toggle_is_present_and_labelled(self):
        response = self.client.get(reverse("user:login"))
        self.assertContains(response, "data-theme-toggle")
        self.assertContains(response, 'aria-pressed="false"')

    def test_no_external_static_hosts(self):
        response = self.client.get(reverse("user:login"))
        for host in ("cdn.", "unpkg.com", "jsdelivr", "assets.pyecharts.org"):
            self.assertNotContains(response, host)

    def test_curated_detail_shows_demo_badge(self):
        response = self.client.get(self.detail_url())
        self.assertContains(response, "演示数据 · 非权威统计")
        self.assertContains(response, "演示数据")


class ImportedProvenanceLayoutTests(TestCase):
    def setUp(self):
        self.surname = SecondName.objects.create(
            second_name="又",
            summary="又姓原始摘要",
            base_information="又姓原始基本信息",
            ori="又姓原始起源",
            mig="原始迁徙文字",
            dis="原始分布文字",
            cul="又姓原始文化",
            source_note="上海财经大学《数据库原理》2021 Fall 课程原始资料（未校订）。",
            is_imported=True,
        )
        self.detail_url = reverse("Surname:detail", args=[self.surname.slug])

    def test_imported_detail_shows_raw_badge(self):
        response = self.client.get(self.detail_url)

        self.assertContains(response, "课程原始资料 · 未校订")
        self.assertContains(response, "原始分布文字")
        self.assertContains(response, "原始迁徙文字")
        self.assertNotContains(response, "暂无分布数据")
        self.assertNotContains(response, "暂无迁徙记录")
        self.assertNotContains(response, "演示数据")

    def test_empty_sections_use_raw_text_when_present(self):
        response = self.client.get(self.detail_url)

        self.assertContains(response, "暂无结构化分布数据；以上为原始文字资料。")
        self.assertContains(response, "暂无结构化迁徙事件；以上为原始文字资料。")

    def test_list_card_marks_imported(self):
        response = self.client.get(reverse("Surname:list"))

        self.assertContains(response, "原始资料")
        self.assertContains(response, "又")

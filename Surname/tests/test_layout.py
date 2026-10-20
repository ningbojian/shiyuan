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

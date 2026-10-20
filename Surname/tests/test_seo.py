from __future__ import annotations

import json
import re

from django.test import TestCase
from django.urls import reverse

from Surname.models import Famous, SecondName
from Surname.templatetags.seo_tags import jsonld


def jsonld_payloads(response) -> list[dict]:
    html = response.content.decode()
    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.S
    )
    return [json.loads(block) for block in blocks]


class SitemapTests(TestCase):
    def setUp(self):
        self.surname = SecondName.objects.create(
            second_name="李", slug="li", pinyin="li", initial="L"
        )
        Famous.objects.create(
            surname=self.surname,
            name="李白",
            slug="li-bai",
            info="唐代诗人",
        )

    def test_sitemap_contains_surnames_figures_and_static_pages(self):
        response = self.client.get("/sitemap.xml")

        self.assertEqual(response.status_code, 200)
        self.assertIn("application/xml", response["Content-Type"])
        content = response.content.decode()
        self.assertIn("http://testserver/surname/li/", content)
        self.assertIn("http://testserver/surname/figures/li-bai/", content)
        self.assertIn("http://testserver/surname/figures/", content)
        self.assertIn("http://testserver/", content)

    def test_robots_points_to_sitemap(self):
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/plain", response["Content-Type"])
        content = response.content.decode()
        self.assertIn("Sitemap: http://testserver/sitemap.xml", content)
        self.assertIn("Disallow: /admin/", content)
        self.assertIn("Disallow: /user/", content)


class MetadataTests(TestCase):
    def setUp(self):
        self.surname = SecondName.objects.create(
            second_name="李",
            slug="li",
            pinyin="li",
            initial="L",
            summary="李氏源流概述",
        )
        self.figure = Famous.objects.create(
            surname=self.surname,
            name="李白",
            slug="li-bai",
            info="唐代诗人，字太白。",
        )

    def test_detail_has_canonical_and_open_graph(self):
        response = self.client.get(reverse("Surname:detail", args=["li"]))

        self.assertContains(
            response,
            '<link rel="canonical" href="http://testserver/surname/li/">',
        )
        self.assertContains(response, 'property="og:title"')
        self.assertContains(response, "李姓 · 氏源")
        self.assertContains(
            response, 'property="og:url" content="http://testserver/surname/li/"'
        )
        self.assertContains(response, 'name="twitter:card"')

    def test_surname_jsonld_is_webpage(self):
        response = self.client.get(reverse("Surname:detail", args=["li"]))

        payloads = jsonld_payloads(response)
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]["@context"], "https://schema.org")
        self.assertEqual(payloads[0]["@type"], "WebPage")
        self.assertEqual(payloads[0]["name"], "李姓")
        self.assertEqual(payloads[0]["url"], "http://testserver/surname/li/")

    def test_figure_jsonld_is_person(self):
        response = self.client.get(
            reverse("Surname:figure_detail", args=["li-bai"])
        )

        payloads = jsonld_payloads(response)
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]["@type"], "Person")
        self.assertEqual(payloads[0]["name"], "李白")
        self.assertEqual(
            payloads[0]["url"], "http://testserver/surname/figures/li-bai/"
        )

    def test_jsonld_escapes_script_breakout(self):
        self.surname.summary = '</script><script>alert(1)</script>'
        self.surname.save(update_fields=["summary"])

        response = self.client.get(reverse("Surname:detail", args=["li"]))

        html = response.content.decode()
        self.assertNotIn("</script><script>alert(1)", html)
        payloads = jsonld_payloads(response)
        self.assertEqual(payloads[0]["description"], "alert(1)")
        self.assertNotIn("<script", payloads[0]["description"])

    def test_jsonld_filter_escapes_markup_characters(self):
        payload = jsonld({"text": "甲 & 乙 < 丙 > 丁" + chr(0x2028)})

        self.assertIn("\\u0026", payload)
        self.assertIn("\\u003C", payload)
        self.assertIn("\\u003E", payload)
        self.assertIn("\\u2028", payload)
        self.assertEqual(
            json.loads(payload), {"text": "甲 & 乙 < 丙 > 丁" + chr(0x2028)}
        )


class ErrorPageTests(TestCase):
    def test_unknown_surname_uses_friendly_404(self):
        response = self.client.get("/surname/no-such-surname/")

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "没有找到", status_code=404)
        self.assertContains(response, "返回姓氏目录", status_code=404)

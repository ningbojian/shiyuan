from __future__ import annotations

from django.test import TestCase
from django.urls import reverse

from Surname.models import (
    Clan,
    Distribution,
    Dynasty,
    Famous,
    Province,
    SecondName,
    SurnameRelation,
)


class ApiTestCase(TestCase):
    def setUp(self):
        self.li = SecondName.objects.create(
            second_name="李",
            slug="li",
            pinyin="li",
            initial="L",
            aliases="李氏",
            summary="陇西望族",
        )
        self.wang = SecondName.objects.create(
            second_name="王", slug="wang", pinyin="wang", initial="W"
        )
        self.province = Province.objects.create(
            name="河北省", slug="hebei", map_name="河北"
        )
        Distribution.objects.create(
            surname=self.li, province=self.province, intensity=72
        )
        self.tang = Dynasty.objects.create(name="唐朝", slug="tang", order=12)
        Famous.objects.create(
            surname=self.li,
            dynasty=self.tang,
            name="李白",
            slug="li-bai",
            info="唐代诗人",
        )
        clan = Clan.objects.create(name="姬姓", slug="ji-xing", kind="xing")
        SurnameRelation.objects.create(
            source=self.li,
            target_clan=clan,
            relation_type="origin",
            description="源出姬姓",
        )


class SurnameApiTests(ApiTestCase):
    def test_envelope_success(self):
        response = self.client.get(reverse("api:surnames"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        self.assertEqual(payload["message"], "ok")
        self.assertEqual(payload["data"]["total"], 2)
        self.assertEqual(len(payload["data"]["results"]), 2)

    def test_pagination(self):
        for index in range(23):
            SecondName.objects.create(
                second_name=f"姓{index:02d}",
                slug=f"xing-{index:02d}",
                pinyin=f"x{index}",
                initial="X",
            )
        response = self.client.get(reverse("api:surnames"), {"page_size": 10, "page": 2})
        data = response.json()["data"]
        self.assertEqual(data["page"], 2)
        self.assertEqual(data["page_size"], 10)
        self.assertEqual(data["total"], 25)
        self.assertEqual(len(data["results"]), 10)

    def test_page_size_cap(self):
        response = self.client.get(reverse("api:surnames"), {"page_size": 1000})
        self.assertEqual(response.json()["data"]["page_size"], 100)

    def test_search_api_by_pinyin_and_alias(self):
        response = self.client.get(reverse("api:search"), {"q": "li"})
        self.assertEqual(response.status_code, 200)
        results = response.json()["data"]["results"]
        self.assertEqual([item["slug"] for item in results], ["li"])

        response = self.client.get(reverse("api:search"), {"q": "李氏"})
        self.assertEqual([item["slug"] for item in response.json()["data"]["results"]], ["li"])

    def test_detail_includes_relations(self):
        response = self.client.get(reverse("api:surname_detail", args=["li"]))
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["slug"], "li")
        self.assertEqual(data["aliases"], ["李氏"])
        self.assertEqual(data["distributions"][0]["province"], "河北省")
        self.assertEqual(data["figures"][0]["name"], "李白")
        self.assertEqual(data["relations"][0]["target_clan"], "姬姓")
        self.assertEqual(data["relations"][0]["relation_type"], "origin")

    def test_envelope_404(self):
        response = self.client.get(
            reverse("api:surname_detail", args=["missing"])
        )
        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertNotEqual(payload["code"], 0)
        self.assertIn("未找到", payload["message"])

    def test_figures_api_filters(self):
        response = self.client.get(reverse("api:figures"), {"dynasty": "tang"})
        results = response.json()["data"]["results"]
        self.assertEqual([item["name"] for item in results], ["李白"])
        response = self.client.get(reverse("api:figures"), {"surname": "wang"})
        self.assertEqual(response.json()["data"]["results"], [])

    def test_meta_api(self):
        response = self.client.get(reverse("api:meta"))
        data = response.json()["data"]
        self.assertEqual(data["provinces"][0]["slug"], "hebei")
        self.assertEqual(data["dynasties"][0]["slug"], "tang")
        self.assertIn("L", data["initials"])


class ApiMethodTests(ApiTestCase):
    def test_api_no_write_methods(self):
        urls = [
            reverse("api:surnames"),
            reverse("api:surname_detail", args=["li"]),
            reverse("api:search"),
            reverse("api:figures"),
            reverse("api:meta"),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url).status_code, 405)
                self.assertEqual(self.client.put(url).status_code, 405)
                self.assertEqual(self.client.delete(url).status_code, 405)

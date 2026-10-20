from __future__ import annotations

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from Surname.models import Distribution, Province, SecondName


class SurnameSearchTests(TestCase):
    def setUp(self):
        self.li = SecondName.objects.create(
            second_name="李",
            pinyin="li",
            aliases="李氏,陇西",
            summary="陇西望族，源流悠长。",
        )
        self.wang = SecondName.objects.create(
            second_name="王",
            pinyin="wang",
            summary="太原望族。",
        )
        self.zhang = SecondName.objects.create(
            second_name="张",
            pinyin="zhang",
            summary="清河郡望。",
        )
        hebei = Province.objects.create(name="河北省", slug="hebei")
        henan = Province.objects.create(name="河南省", slug="henan")
        Distribution.objects.create(surname=self.li, province=hebei, intensity=80)
        Distribution.objects.create(surname=self.wang, province=henan, intensity=70)

    def test_directory_200(self):
        response = self.client.get(reverse("Surname:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "姓氏目录")
        self.assertContains(response, "李")

    def test_search_by_chinese(self):
        response = self.client.get(reverse("Surname:search"), {"q": "李"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "李")
        self.assertNotContains(response, ">王<")

    def test_search_by_pinyin(self):
        response = self.client.get(reverse("Surname:search"), {"q": "li"})
        self.assertContains(response, "李")
        self.assertNotContains(response, ">王<")

    def test_search_by_initial(self):
        response = self.client.get(reverse("Surname:search"), {"q": "L"})
        self.assertContains(response, "李")
        self.assertNotContains(response, ">王<")

    def test_search_by_alias(self):
        response = self.client.get(reverse("Surname:search"), {"q": "陇西"})
        self.assertContains(response, "李")
        self.assertNotContains(response, ">王<")

    def test_filter_by_initial(self):
        response = self.client.get(reverse("Surname:list"), {"initial": "L"})
        self.assertContains(response, "李")
        self.assertNotContains(response, ">王<")

    def test_filter_by_province(self):
        response = self.client.get(reverse("Surname:list"), {"province": "河北省"})
        self.assertContains(response, "李")
        self.assertNotContains(response, ">王<")

    def test_search_no_results(self):
        response = self.client.get(reverse("Surname:search"), {"q": "不存在的姓"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "没有找到")

    def test_search_query_is_escaped(self):
        response = self.client.get(
            reverse("Surname:search"), {"q": "<script>alert(1)</script>"}
        )
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")

    def test_pagination_preserves_query(self):
        for index in range(25):
            SecondName.objects.create(
                second_name=f"姓{index}",
                slug=f"xing-{index}",
                pinyin=f"xing{index}",
                summary="测试分页",
            )
        response = self.client.get(
            reverse("Surname:search"), {"q": "测试分页", "page": 2}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "q=%E6%B5%8B%E8%AF%95%E5%88%86%E9%A1%B5")
        self.assertContains(response, "page=1")

    def test_list_query_budget(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("Surname:list"))
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(queries), 5)

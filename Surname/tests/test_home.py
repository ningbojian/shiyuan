from __future__ import annotations

from datetime import date
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from Surname.models import Famous, Province, SecondName


class HomeTests(TestCase):
    def setUp(self):
        for index in range(8):
            SecondName.objects.create(
                second_name=chr(ord("李") + index),
                slug=f"name-{index}",
                summary=f"摘要 {index}",
                popularity=100 - index,
                is_featured=index < 8,
            )
        self.li = SecondName.objects.get(slug="name-0")
        Famous.objects.create(
            surname=self.li,
            name="李白",
            info="唐代诗人",
            slug="li-bai",
        )
        Province.objects.create(name="北京市", slug="beijing")

    def test_home_200(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "查找姓氏")
        self.assertContains(response, "今日一姓")

    def test_featured_limit(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.context["featured"]), 6)
        self.assertEqual(len(response.context["featured"]), 6)

    @mock.patch("Surname.views.timezone.localdate", return_value=date(2026, 10, 20))
    def test_daily_is_deterministic(self, _localdate):
        first = self.client.get(reverse("home")).context["daily"]
        second = self.client.get(reverse("home")).context["daily"]
        self.assertEqual(first.pk, second.pk)

    def test_home_query_budget(self):
        with self.assertNumQueries(6):
            self.client.get(reverse("home"))

    def test_search_form_targets_search_view(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, 'action="/surname/search/"')
        self.assertContains(response, 'name="q"')

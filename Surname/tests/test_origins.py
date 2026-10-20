from __future__ import annotations

import json
import re

from django.test import TestCase
from django.urls import reverse

from Surname.models import Clan, SecondName, SurnameRelation

JSON_SCRIPT_RE = re.compile(
    r'<script id="(?P<id>[\w-]+)" type="application/json">(?P<data>.*?)</script>',
    re.DOTALL,
)


class OriginsGraphTests(TestCase):
    def setUp(self):
        self.li = SecondName.objects.create(second_name="李", pinyin="li")
        self.wang = SecondName.objects.create(second_name="王", pinyin="wang")
        self.clan = Clan.objects.create(name="姬姓", slug="ji-xing", kind="xing")
        SurnameRelation.objects.create(
            source=self.li,
            target_surname=self.wang,
            relation_type="branch",
            description="李姓一支分于王姓",
        )
        SurnameRelation.objects.create(
            source=self.wang,
            target_clan=self.clan,
            relation_type="origin",
            description="源出姬姓",
        )
        self.url = reverse("Surname:origins")

    def payload(self):
        html = self.client.get(self.url).content.decode()
        match = JSON_SCRIPT_RE.search(html)
        self.assertIsNotNone(match)
        self.assertEqual(match.group("id"), "origins-data")
        return json.loads(match.group("data"))

    def test_origins_relation_payload_shape(self):
        data = self.payload()
        self.assertEqual(data["categories"], [{"name": "姓氏"}, {"name": "宗族"}])
        nodes = {node["name"]: node for node in data["nodes"]}
        self.assertEqual(nodes["李姓"]["slug"], "li")
        self.assertEqual(nodes["李姓"]["category"], 0)
        self.assertEqual(nodes["王姓"]["slug"], "wang")
        self.assertIsNone(nodes["姬姓"]["slug"])
        self.assertEqual(nodes["姬姓"]["category"], 1)
        edges = {(edge["source"], edge["target"], edge["label"]) for edge in data["edges"]}
        self.assertIn(("李姓", "王姓", "分支"), edges)
        self.assertIn(("王姓", "姬姓", "源出"), edges)

    def test_origins_graph_markup(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'data-chart="origins"')
        self.assertContains(response, "/static/js/charts.js")
        self.assertContains(response, "查看源流数据表")

    def test_origins_table_contains_all_edges(self):
        response = self.client.get(self.url)
        for edge in ("李姓一支分于王姓", "源出姬姓"):
            self.assertContains(response, edge)

    def test_empty_origins_has_no_chart(self):
        SurnameRelation.objects.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'data-chart="origins"')
        self.assertContains(response, "暂无源流关系")

    def test_detail_relations_payload_still_works(self):
        response = self.client.get(reverse("Surname:detail", args=["li"]))
        html = response.content.decode()
        self.assertIn('id="relations-data"', html)
        self.assertIn('data-chart="relations"', html)

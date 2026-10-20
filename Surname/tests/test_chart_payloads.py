from __future__ import annotations

import json
import re

from django.test import TestCase
from django.urls import reverse

from Surname.models import (
    Clan,
    Distribution,
    Dynasty,
    Famous,
    MigrationEvent,
    Province,
    SecondName,
    SurnameRelation,
)

JSON_SCRIPT_RE = re.compile(
    r'<script id="(?P<id>[\w-]+)" type="application/json">(?P<data>.*?)</script>',
    re.DOTALL,
)


def payloads(response) -> dict:
    html = response.content.decode()
    return {
        match.group("id"): json.loads(match.group("data"))
        for match in JSON_SCRIPT_RE.finditer(html)
    }


class ChartPayloadTests(TestCase):
    def setUp(self):
        self.surname = SecondName.objects.create(
            second_name="李",
            slug="li",
            pinyin="li",
            initial="L",
            keywords=[{"name": "陇西", "value": 40}, {"name": "赵郡", "value": 30}],
        )
        hebei = Province.objects.create(
            name="河北省",
            slug="hebei",
            short_name="河北",
            map_name="河北",
            center_lng=114.5,
            center_lat=38.0,
        )
        henan = Province.objects.create(
            name="河南省",
            slug="henan",
            short_name="河南",
            map_name="河南",
            center_lng=113.6,
            center_lat=34.7,
        )
        Distribution.objects.create(
            surname=self.surname, province=hebei, intensity=80
        )
        tang = Dynasty.objects.create(name="唐朝", slug="tang", order=12)
        Famous.objects.create(
            surname=self.surname, dynasty=tang, name="李白", slug="li-bai", info="诗人"
        )
        MigrationEvent.objects.create(
            surname=self.surname,
            dynasty=tang,
            from_province=hebei,
            to_province=henan,
            description="由河北迁往河南",
            order=1,
        )
        MigrationEvent.objects.create(
            surname=self.surname,
            dynasty=tang,
            from_province=None,
            to_province=henan,
            description="只知去向的迁徙",
            order=2,
        )
        wang = SecondName.objects.create(
            second_name="王", pinyin="wang", initial="W"
        )
        clan = Clan.objects.create(name="姬姓", slug="ji-xing", kind="xing")
        SurnameRelation.objects.create(
            source=self.surname,
            target_surname=wang,
            relation_type="branch",
            description="李姓一支分于王姓",
        )
        SurnameRelation.objects.create(
            source=self.surname,
            target_clan=clan,
            relation_type="origin",
            description="源出姬姓",
        )
        self.url = reverse("Surname:detail", args=[self.surname.slug])

    def test_detail_embeds_four_json_payloads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = payloads(response)
        self.assertEqual(
            set(data),
            {"distribution-data", "migration-data", "relations-data", "keywords-data"},
        )

    def test_distribution_payload_uses_map_name(self):
        data = payloads(self.client.get(self.url))["distribution-data"]
        self.assertEqual(
            data, [{"name": "河北", "value": 80, "province": "河北省"}]
        )

    def test_migration_payload_carries_coordinates(self):
        events = payloads(self.client.get(self.url))["migration-data"]
        self.assertEqual(len(events), 2)
        first = events[0]
        self.assertEqual(first["from_name"], "河北省")
        self.assertEqual(first["to_name"], "河南省")
        self.assertEqual(first["from_coord"], [114.5, 38.0])
        self.assertEqual(first["to_coord"], [113.6, 34.7])
        self.assertEqual(first["dynasty"], "唐朝")

    def test_migration_payload_without_from_has_destination_only(self):
        events = payloads(self.client.get(self.url))["migration-data"]
        second = events[1]
        self.assertIsNone(second["from_coord"])
        self.assertEqual(second["to_coord"], [113.6, 34.7])

    def test_relation_payload_nodes_and_edges(self):
        data = payloads(self.client.get(self.url))["relations-data"]
        node_names = {node["name"] for node in data["nodes"]}
        self.assertIn("李姓", node_names)
        self.assertIn("王姓", node_names)
        self.assertIn("姬姓", node_names)
        by_name = {node["name"]: node for node in data["nodes"]}
        self.assertEqual(by_name["李姓"]["slug"], "li")
        self.assertIsNone(by_name["姬姓"]["slug"])
        edges = {(edge["source"], edge["target"], edge["label"]) for edge in data["edges"]}
        self.assertIn(("李姓", "王姓", "分支"), edges)
        self.assertIn(("李姓", "姬姓", "源出"), edges)

    def test_keywords_payload(self):
        data = payloads(self.client.get(self.url))["keywords-data"]
        self.assertEqual(
            data,
            [{"name": "陇西", "value": 40}, {"name": "赵郡", "value": 30}],
        )

    def test_charts_are_local_and_only_on_detail(self):
        response = self.client.get(self.url)
        html = response.content.decode()
        self.assertIn("/static/js/charts.js", html)
        self.assertIn("/static/vendor/echarts/echarts.min.js", html)
        self.assertIn("/static/vendor/echarts/china.js", html)
        self.assertIn("/static/vendor/echarts/echarts-wordcloud.min.js", html)
        for host in ("assets.pyecharts.org", "cdn.", "unpkg.com", "jsdelivr"):
            self.assertNotIn(host, html)
        self.assertNotIn('<script src="http', html)
        self.assertNotIn('<img src="http', html)
        self.assertNotRegex(
            html, r'<link[^>]+rel="stylesheet"[^>]+href="https?://'
        )

    def test_chart_containers_and_text_alternatives(self):
        html = self.client.get(self.url).content.decode()
        for chart in ("distribution", "migration", "relations", "keywords"):
            self.assertIn(f'data-chart="{chart}"', html)
            self.assertIn(f'id="{chart}-data"', html)
        self.assertGreaterEqual(html.count("<details"), 3)
        self.assertIn("查看分布数据表", html)
        self.assertIn("查看迁徙数据表", html)
        self.assertIn("查看关系数据表", html)
        self.assertIn("查看关键词数据", html)

    def test_empty_detail_has_no_chart_containers(self):
        empty = SecondName.objects.create(second_name="丁", slug="ding")
        response = self.client.get(reverse("Surname:detail", args=[empty.slug]))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertNotIn("data-chart=", html)
        self.assertNotIn("/static/vendor/echarts/", html)
        self.assertIn("暂无人物资料", html)
        data = payloads(response)
        self.assertEqual(data["distribution-data"], [])
        self.assertEqual(data["migration-data"], [])
        self.assertEqual(data["relations-data"]["nodes"], [])
        self.assertEqual(data["keywords-data"], [])

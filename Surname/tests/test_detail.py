from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from Surname.models import (
    Distribution,
    Dynasty,
    Famous,
    MigrationEvent,
    Province,
    SecondName,
)
from user.models import Comment, Favorite

User = get_user_model()


class SurnameDetailTests(TestCase):
    def setUp(self):
        self.surname = SecondName.objects.create(
            second_name="李",
            pinyin="li",
            summary="陇西望族",
            base_information="基本信息",
            ori="姓氏起源",
            mig="迁徙传播",
            dis="人口分布",
            cul="姓氏文化",
            fam="历代名人",
        )
        self.detail_url = reverse("Surname:detail", args=[self.surname.slug])
        province = Province.objects.create(name="河北省", slug="hebei")
        dynasty = Dynasty.objects.create(name="唐朝", slug="tang", order=12)
        Distribution.objects.create(
            surname=self.surname, province=province, intensity=80
        )
        Famous.objects.create(
            surname=self.surname,
            dynasty=dynasty,
            name="李白",
            info="唐代诗人",
            slug="li-bai",
        )
        MigrationEvent.objects.create(
            surname=self.surname,
            dynasty=dynasty,
            from_province=province,
            description="示例迁徙事件",
            source_note="演示",
            order=1,
        )

    def test_detail_by_slug(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "李姓")
        self.assertContains(response, "李白")
        self.assertContains(response, "示例迁徙事件")

    def test_unknown_slug_404(self):
        response = self.client.get(reverse("Surname:detail", args=["missing"]))
        self.assertEqual(response.status_code, 404)

    def test_legacy_url_redirects(self):
        response = self.client.get(
            reverse("Surname:index"), {"surname": self.surname.second_name}
        )
        self.assertRedirects(response, self.detail_url)

    def test_view_count_increments_once(self):
        before = self.surname.view_count
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.surname.refresh_from_db()
        self.assertEqual(self.surname.view_count, before + 1)

    def test_detail_query_budget(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(queries), 16)

    def test_empty_sections_render(self):
        empty = SecondName.objects.create(second_name="丁", slug="ding")
        response = self.client.get(reverse("Surname:detail", args=[empty.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "暂无人物资料")
        self.assertContains(response, "暂无迁徙记录")
        self.assertContains(response, "暂无分布数据")
        self.assertContains(response, "暂无源流关系记录")
        self.assertContains(response, "暂无关键词数据")

    def test_favorite_state(self):
        user = User.objects.create_user(username="reader", password="pass-123456")
        Favorite.objects.create(user=user, surname=self.surname)
        self.client.force_login(user)
        response = self.client.get(self.detail_url)
        self.assertContains(response, "已收藏")

    def test_comment_form_visible(self):
        user = User.objects.create_user(username="commenter", password="pass-123456")
        self.client.force_login(user)
        response = self.client.get(self.detail_url)
        self.assertContains(response, 'name="content"')
        self.assertContains(response, "发表评论")

    def test_comment_form_replaced_by_login_prompt(self):
        response = self.client.get(self.detail_url)
        self.assertNotContains(response, 'name="content"')
        self.assertContains(response, "登录")
        self.assertContains(response, "后可以评论")

    def test_toc_anchors(self):
        response = self.client.get(self.detail_url)
        for anchor in ("overview", "origin", "migration", "distribution", "figures"):
            self.assertContains(response, f'id="{anchor}"')
        self.assertContains(response, 'href="#migration"')


class FavoriteToggleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reader", password="pass-123456")
        self.surname = SecondName.objects.create(second_name="李", slug="li")
        self.url = reverse("user:favorite_toggle", args=[self.surname.slug])

    def test_requires_login(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("user:login"), response.url)

    def test_toggle_is_idempotent_and_private(self):
        self.client.force_login(self.user)
        self.client.post(self.url)
        self.assertTrue(
            Favorite.objects.filter(user=self.user, surname=self.surname).exists()
        )
        self.client.post(self.url)
        self.assertFalse(Favorite.objects.filter(user=self.user).exists())
        self.assertEqual(Favorite.objects.count(), 0)

    def test_other_users_favorites_untouched(self):
        other = User.objects.create_user(username="other", password="pass-123456")
        Favorite.objects.create(user=other, surname=self.surname)
        self.client.force_login(self.user)
        self.client.post(self.url)
        self.assertTrue(Favorite.objects.filter(user=other).exists())
        self.assertEqual(Favorite.objects.count(), 2)


class DetailCommentVisibilityTests(TestCase):
    def test_hidden_comments_excluded(self):
        surname = SecondName.objects.create(second_name="李", slug="li")
        user = User.objects.create_user(username="reader", password="pass-123456")
        Comment.objects.create(user=user, surname=surname, content="可见评论")
        Comment.objects.create(
            user=user, surname=surname, content="隐藏评论", status="hidden"
        )
        response = self.client.get(reverse("Surname:detail", args=["li"]))
        self.assertContains(response, "可见评论")
        self.assertNotContains(response, "隐藏评论")

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from Surname.models import SecondName
from user.models import Comment
from user.views import _login_failure_key

User = get_user_model()


class ThrottleTestBase(TestCase):
    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()


class LoginThrottleTests(ThrottleTestBase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="reader", password="pass-123456"
        )
        self.login_url = reverse("user:login")

    def test_login_throttled_after_limit(self):
        with self.assertLogs("shiyuan.audit", level="WARNING") as captured:
            for _ in range(5):
                self.client.post(
                    self.login_url,
                    {"username": "reader", "password": "wrong-password"},
                )
            response = self.client.post(
                self.login_url,
                {"username": "reader", "password": "pass-123456"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "尝试次数过多")
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertTrue(any("throttled" in line for line in captured.output))

    def test_cache_key_includes_username(self):
        self.assertNotEqual(
            _login_failure_key("1.2.3.4", "reader"),
            _login_failure_key("1.2.3.4", "other"),
        )
        with self.assertLogs("shiyuan.audit", level="INFO"):
            for _ in range(5):
                self.client.post(
                    self.login_url,
                    {"username": "reader", "password": "wrong-password"},
                )
            User.objects.create_user(username="other", password="pass-123456")
            response = self.client.post(
                self.login_url,
                {"username": "other", "password": "pass-123456"},
            )
        self.assertRedirects(response, reverse("user:personal"))

    def test_successful_login_clears_counter(self):
        with self.assertLogs("shiyuan.audit", level="INFO") as captured:
            for _ in range(3):
                self.client.post(
                    self.login_url,
                    {"username": "reader", "password": "wrong-password"},
                )
            key = _login_failure_key("127.0.0.1", "reader")
            self.assertEqual(cache.get(key), 3)
            self.client.post(
                self.login_url,
                {"username": "reader", "password": "pass-123456"},
            )
        self.assertIsNone(cache.get(key))
        self.assertTrue(any("login success" in line for line in captured.output))


class CommentThrottleTests(ThrottleTestBase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="reader", password="pass-123456"
        )
        self.surname = SecondName.objects.create(
            second_name="李", pinyin="li", slug="li"
        )
        self.url = reverse("user:comment_add", args=["李"])
        self.client.force_login(self.user)

    def test_comment_throttled_after_limit(self):
        for index in range(10):
            self.client.post(self.url, {"content": f"评论 {index}"})
        self.assertEqual(Comment.objects.filter(user=self.user).count(), 10)
        with self.assertLogs("shiyuan.audit", level="WARNING") as captured:
            self.client.post(self.url, {"content": "第十一条"})
        self.assertEqual(Comment.objects.filter(user=self.user).count(), 10)
        self.assertTrue(any("comment throttled" in line for line in captured.output))

    def test_other_user_not_affected(self):
        other = User.objects.create_user(
            username="other", password="pass-123456"
        )
        for index in range(10):
            self.client.post(self.url, {"content": f"评论 {index}"})
        self.client.force_login(other)
        self.client.post(self.url, {"content": "另一个人的评论"})
        self.assertTrue(
            Comment.objects.filter(user=other, content="另一个人的评论").exists()
        )

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from Surname.models import SecondName
from user.models import Comment

User = get_user_model()


class CommentTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            username="alice", password="old-pass-123"
        )
        self.bob = User.objects.create_user(
            username="bob", password="old-pass-123"
        )
        self.staff = User.objects.create_user(
            username="staff", password="old-pass-123", is_staff=True
        )
        self.surname = SecondName.objects.create(
            second_name="李",
            base_information="",
            fam="",
            mig="",
            dis="",
            ori="",
            cul="",
        )
        self.client.force_login(self.alice)

    def _add_url(self) -> str:
        return reverse("user:comment_add", args=[self.surname.second_name])

    def _detail_url(self) -> str:
        return reverse("Surname:detail", args=[self.surname.slug])

    def test_comment_requires_login(self):
        self.client.logout()
        response = self.client.post(self._add_url(), {"content": "你好"})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("user:login"), response.url)
        self.assertEqual(Comment.objects.count(), 0)

    def test_comment_post_creates_for_current_user(self):
        response = self.client.post(self._add_url(), {"content": "你好"})
        self.assertEqual(response.status_code, 302)
        comment = Comment.objects.get()
        self.assertEqual(comment.user, self.alice)
        self.assertEqual(comment.surname, self.surname)
        self.assertEqual(comment.status, "visible")

    def test_comment_rejects_other_users_delete(self):
        comment = Comment.objects.create(
            user=self.bob, surname=self.surname, content="bob 的评论"
        )
        response = self.client.post(
            reverse("user:comment_delete", args=[comment.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())

    def test_comment_delete_own(self):
        comment = Comment.objects.create(
            user=self.alice, surname=self.surname, content="我的评论"
        )
        response = self.client.post(
            reverse("user:comment_delete", args=[comment.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_comment_escapes_html(self):
        self.client.post(
            self._add_url(), {"content": "<script>alert(1)</script>"}
        )
        response = self.client.get(self._detail_url())
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertNotContains(response, "<script>alert(1)</script>")

    def test_comment_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.alice)
        response = client.post(self._add_url(), {"content": "没有 CSRF"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Comment.objects.count(), 0)

    def test_hidden_comment_not_in_public_list(self):
        Comment.objects.create(
            user=self.alice, surname=self.surname, content="显示中的评论"
        )
        Comment.objects.create(
            user=self.bob,
            surname=self.surname,
            content="被隐藏的评论",
            status="hidden",
        )
        response = self.client.get(self._detail_url())
        self.assertContains(response, "显示中的评论")
        self.assertNotContains(response, "被隐藏的评论")

    def test_staff_can_hide_comment(self):
        comment = Comment.objects.create(
            user=self.alice, surname=self.surname, content="待隐藏评论"
        )
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("user:comment_hide", args=[comment.pk])
        )
        self.assertEqual(response.status_code, 302)
        comment.refresh_from_db()
        self.assertEqual(comment.status, "hidden")

    def test_non_staff_cannot_hide_comment(self):
        comment = Comment.objects.create(
            user=self.bob, surname=self.surname, content="别人的评论"
        )
        response = self.client.post(
            reverse("user:comment_hide", args=[comment.pk])
        )
        self.assertEqual(response.status_code, 403)
        comment.refresh_from_db()
        self.assertEqual(comment.status, "visible")

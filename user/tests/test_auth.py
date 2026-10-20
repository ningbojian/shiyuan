from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class AuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", password="old-pass-123"
        )

    def test_login_success_redirects(self):
        response = self.client.post(
            reverse("user:login"),
            {"username": "alice", "password": "old-pass-123"},
        )
        self.assertRedirects(response, reverse("user:personal"))

    def test_login_failure_is_generic(self):
        response = self.client.post(
            reverse("user:login"),
            {"username": "nobody", "password": "wrong-pass-123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "账号或密码错误")
        self.assertNotContains(response, "账号不存在")

    def test_login_cycles_session_key(self):
        self.client.get(reverse("user:login"))
        session = self.client.session
        session["marker"] = "1"
        session.save()
        before = session.session_key

        response = self.client.post(
            reverse("user:login"),
            {"username": "alice", "password": "old-pass-123"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(self.client.session.session_key, before)

    def test_register_creates_user_and_profile(self):
        response = self.client.post(
            reverse("user:register"),
            {
                "username": "bob",
                "display_name": "小博",
                "password1": "new-pass-456",
                "password2": "new-pass-456",
            },
        )
        self.assertRedirects(response, reverse("user:personal"))
        user = User.objects.get(username="bob")
        self.assertEqual(user.profile.display_name, "小博")
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))

    def test_register_rejects_duplicate_username(self):
        response = self.client.post(
            reverse("user:register"),
            {
                "username": "alice",
                "display_name": "",
                "password1": "new-pass-456",
                "password2": "new-pass-456",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username="alice").count(), 1)

    def test_register_rejects_weak_password(self):
        response = self.client.post(
            reverse("user:register"),
            {
                "username": "bob",
                "display_name": "",
                "password1": "123",
                "password2": "123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="bob").exists())

    def test_logout_get_is_405(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("user:logout"))
        self.assertEqual(response.status_code, 405)

    def test_logout_post_flushes_session(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("user:logout"))
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_personal_requires_login(self):
        response = self.client.get(reverse("user:personal"))
        self.assertRedirects(
            response,
            f"{reverse('user:login')}?next={reverse('user:personal')}",
        )

    def test_password_change_requires_old_password(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("user:password_change"),
            {
                "old_password": "wrong-pass-123",
                "new_password1": "new-pass-456",
                "new_password2": "new-pass-456",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("old-pass-123"))

    def test_password_change_updates_hash(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("user:password_change"),
            {
                "old_password": "old-pass-123",
                "new_password1": "new-pass-456",
                "new_password2": "new-pass-456",
            },
        )
        self.assertRedirects(response, reverse("user:personal"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new-pass-456"))

    def test_csrf_enforced_on_login_and_register(self):
        client = Client(enforce_csrf_checks=True)
        login_response = client.post(
            reverse("user:login"),
            {"username": "alice", "password": "old-pass-123"},
        )
        register_response = client.post(
            reverse("user:register"),
            {
                "username": "bob",
                "password1": "new-pass-456",
                "password2": "new-pass-456",
            },
        )
        self.assertEqual(login_response.status_code, 403)
        self.assertEqual(register_response.status_code, 403)

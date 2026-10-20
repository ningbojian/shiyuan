from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from Surname.models import SecondName
from user.models import Favorite, ReadingHistory

User = get_user_model()


class FavoriteListTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reader", password="pass-123456")
        self.other = User.objects.create_user(username="other", password="pass-123456")
        self.li = SecondName.objects.create(second_name="李", pinyin="li")
        self.wang = SecondName.objects.create(second_name="王", pinyin="wang")
        Favorite.objects.create(user=self.user, surname=self.li)
        Favorite.objects.create(user=self.other, surname=self.wang)
        self.url = reverse("user:favorites")

    def test_favorites_require_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("user:login"), response.url)

    def test_favorites_are_private(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, "李")
        self.assertNotContains(response, "王")

    def test_favorite_list_links_to_detail(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, reverse("Surname:detail", args=["li"]))


class HistoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reader", password="pass-123456")
        self.other = User.objects.create_user(username="other", password="pass-123456")
        self.li = SecondName.objects.create(second_name="李", pinyin="li", slug="li")
        self.url = reverse("user:history")

    def test_history_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("user:login"), response.url)

    def test_detail_records_unique_history_row(self):
        self.client.force_login(self.user)
        detail_url = reverse("Surname:detail", args=["li"])
        self.client.get(detail_url)
        self.client.get(detail_url)
        entry = ReadingHistory.objects.get(user=self.user, surname=self.li)
        self.assertEqual(entry.view_count, 2)
        self.assertEqual(ReadingHistory.objects.filter(user=self.user).count(), 1)

    def test_anonymous_detail_does_not_record_history(self):
        self.client.get(reverse("Surname:detail", args=["li"]))
        self.assertEqual(ReadingHistory.objects.count(), 0)

    def test_history_is_private(self):
        ReadingHistory.objects.create(
            user=self.other, surname=self.li, view_count=1
        )
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "李姓")

    def test_history_trimmed_to_50(self):
        surnames = SecondName.objects.bulk_create(
            [
                SecondName(second_name=f"姓{i:02d}", slug=f"xing-{i:02d}", pinyin=f"x{i}")
                for i in range(50)
            ]
        )
        ReadingHistory.objects.bulk_create(
            [
                ReadingHistory(user=self.user, surname=surname, view_count=1)
                for surname in surnames
            ]
        )
        self.assertEqual(ReadingHistory.objects.filter(user=self.user).count(), 50)
        self.client.force_login(self.user)
        self.client.get(reverse("Surname:detail", args=["li"]))
        entries = ReadingHistory.objects.filter(user=self.user)
        self.assertEqual(entries.count(), 50)
        self.assertTrue(entries.filter(surname=self.li).exists())

    def test_delete_own_history_entry(self):
        entry = ReadingHistory.objects.create(
            user=self.user, surname=self.li, view_count=1
        )
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("user:history_delete", args=[entry.pk])
        )
        self.assertRedirects(response, reverse("user:history"))
        self.assertFalse(ReadingHistory.objects.filter(pk=entry.pk).exists())

    def test_cannot_delete_other_users_history(self):
        entry = ReadingHistory.objects.create(
            user=self.other, surname=self.li, view_count=1
        )
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("user:history_delete", args=[entry.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(ReadingHistory.objects.filter(pk=entry.pk).exists())

    def test_delete_history_requires_post(self):
        entry = ReadingHistory.objects.create(
            user=self.user, surname=self.li, view_count=1
        )
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("user:history_delete", args=[entry.pk])
        )
        self.assertEqual(response.status_code, 405)
        self.assertTrue(ReadingHistory.objects.filter(pk=entry.pk).exists())

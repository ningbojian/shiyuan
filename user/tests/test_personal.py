from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from Surname.models import SecondName
from user.models import Comment, Favorite, Profile, ReadingHistory

User = get_user_model()


class PersonalCenterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reader", password="pass-123456")
        self.other = User.objects.create_user(username="other", password="pass-123456")
        self.li = SecondName.objects.create(second_name="李", pinyin="li", slug="li")
        self.wang = SecondName.objects.create(
            second_name="王", pinyin="wang", slug="wang"
        )
        self.user.profile.display_name = "读者甲"
        self.user.profile.save(update_fields=["display_name"])
        self.other.profile.display_name = "读者乙"
        self.other.profile.save(update_fields=["display_name"])
        Favorite.objects.create(user=self.user, surname=self.li)
        Favorite.objects.create(user=self.other, surname=self.wang)
        ReadingHistory.objects.create(
            user=self.user, surname=self.wang, view_count=2
        )
        Comment.objects.create(
            user=self.user, surname=self.li, content="我自己的评论"
        )
        Comment.objects.create(
            user=self.other, surname=self.li, content="别人的评论"
        )
        self.url = reverse("user:personal")

    def test_personal_shows_only_own_data(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "读者甲")
        self.assertNotContains(response, "读者乙")
        self.assertContains(response, "我自己的评论")
        self.assertNotContains(response, "别人的评论")
        self.assertEqual(response.context["favorite_count"], 1)
        self.assertEqual(response.context["history_count"], 1)
        self.assertEqual(response.context["comment_count"], 1)

    def test_personal_links_to_lists(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, reverse("user:favorites"))
        self.assertContains(response, reverse("user:history"))
        self.assertContains(response, reverse("user:profile_edit"))
        self.assertContains(response, reverse("user:password_change"))


class ProfileEditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reader", password="pass-123456")
        self.li = SecondName.objects.create(second_name="李", pinyin="li", slug="li")
        self.url = reverse("user:profile_edit")
        self.client.force_login(self.user)

    def test_profile_edit_updates_allowed_fields(self):
        response = self.client.post(
            self.url,
            {
                "display_name": "新名字",
                "home_surname": self.li.pk,
                "bio": "喜欢读姓氏源流。",
            },
        )
        self.assertRedirects(response, reverse("user:personal"))
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.display_name, "新名字")
        self.assertEqual(profile.home_surname, self.li)
        self.assertEqual(profile.bio, "喜欢读姓氏源流。")

    def test_profile_edit_cannot_change_username(self):
        response = self.client.post(
            self.url,
            {
                "username": "hacked",
                "display_name": "新名字",
                "home_surname": "",
                "bio": "",
            },
        )
        self.assertRedirects(response, reverse("user:personal"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "reader")

    def test_profile_edit_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("user:login"), response.url)

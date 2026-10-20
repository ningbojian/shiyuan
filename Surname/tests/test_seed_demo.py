from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from Surname.models import Dynasty, Province, SecondName
from user.models import Comment, Favorite, ReadingHistory


@override_settings(DEBUG=True)
class SeedDemoTests(TestCase):
    def seed(self):
        call_command("seed_demo", verbosity=0)

    def counts(self):
        return {
            "provinces": Province.objects.count(),
            "dynasties": Dynasty.objects.count(),
            "surnames": SecondName.objects.count(),
            "users": get_user_model().objects.count(),
            "comments": Comment.objects.count(),
            "favorites": Favorite.objects.count(),
            "history": ReadingHistory.objects.count(),
        }

    def test_seed_demo_idempotent(self):
        self.seed()
        first = self.counts()
        self.seed()
        self.assertEqual(first, self.counts())

        self.assertEqual(first["provinces"], 34)
        self.assertEqual(first["dynasties"], 18)
        self.assertEqual(first["surnames"], 33)
        self.assertEqual(first["users"], 3)
        self.assertGreaterEqual(first["comments"], 2)
        self.assertGreaterEqual(first["favorites"], 1)
        self.assertGreaterEqual(first["history"], 1)

    def test_demo_user_can_login(self):
        self.seed()
        self.assertTrue(
            self.client.login(username="demo", password="demo123456")
        )

    def test_seed_creates_profile_and_comments(self):
        self.seed()
        user = get_user_model().objects.get(username="demo")
        self.assertEqual(user.profile.display_name, "演示用户")
        self.assertGreaterEqual(Comment.objects.filter(user=user).count(), 1)

    def test_seed_creates_favorites_and_history(self):
        self.seed()
        self.assertTrue(Favorite.objects.filter(user__username="demo").exists())
        self.assertTrue(
            ReadingHistory.objects.filter(user__username="demo").exists()
        )


class SeedDemoProductionGuardTests(TestCase):
    @override_settings(DEBUG=False)
    def test_seed_demo_requires_force_outside_debug(self):
        with self.assertRaises(CommandError):
            call_command("seed_demo", verbosity=0)

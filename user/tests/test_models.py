from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from user.models import Profile


class ProfileTests(TestCase):
    def test_profile_created_for_new_user(self):
        user = get_user_model().objects.create_user(
            username="alice", password="correct horse battery staple"
        )
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_str_falls_back_to_username(self):
        user = get_user_model().objects.create_user(
            username="alice", password="correct horse battery staple"
        )
        self.assertEqual(str(user.profile), "alice")

    def test_profile_home_surname_optional(self):
        user = get_user_model().objects.create_user(
            username="alice", password="correct horse battery staple"
        )
        self.assertIsNone(user.profile.home_surname)

    def test_builtin_user_has_password_hash(self):
        user = get_user_model().objects.create_user(
            username="alice", password="correct horse battery staple"
        )
        self.assertNotEqual(user.password, "correct horse battery staple")
        self.assertTrue(user.check_password("correct horse battery staple"))

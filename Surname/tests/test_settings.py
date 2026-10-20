from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

BASE_DIR = Path(settings.BASE_DIR)


def run_settings_import(*, env_overrides: dict[str, str], remove: tuple[str, ...] = ()):
    env = os.environ.copy()
    for key in remove:
        env.pop(key, None)
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-c", "import project.settings"],
        cwd=BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


class SettingsTests(SimpleTestCase):
    def test_debug_defaults_false(self):
        result = run_settings_import(
            env_overrides={"DJANGO_SECRET_KEY": "test-secret"},
            remove=("DJANGO_DEBUG",),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(settings.DEBUG)

    def test_production_requires_secret_key(self):
        result = run_settings_import(
            env_overrides={"DJANGO_DEBUG": "0"},
            remove=("DJANGO_SECRET_KEY",),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ImproperlyConfigured", result.stderr)

    def test_csrf_trusted_origins_parse_env(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import project.settings as s; print(','.join(s.CSRF_TRUSTED_ORIGINS))",
            ],
            cwd=BASE_DIR,
            env={
                **os.environ,
                "DJANGO_SECRET_KEY": "test-secret",
                "DJANGO_DEBUG": "0",
                "DJANGO_CSRF_TRUSTED_ORIGINS": "https://a.example, https://b.example",
            },
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip().split(","),
            ["https://a.example", "https://b.example"],
        )

    def test_static_assets_cached_long_in_production(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import project.settings as s; print(s.WHITENOISE_MAX_AGE)",
            ],
            cwd=BASE_DIR,
            env={
                **os.environ,
                "DJANGO_SECRET_KEY": "test-secret",
                "DJANGO_DEBUG": "0",
                "DJANGO_SECURE_SSL": "1",
            },
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "31536000")

    def test_forwarded_proto_trust_is_explicit_opt_in(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import project.settings as s; print(getattr(s, 'SECURE_PROXY_SSL_HEADER', None))",
            ],
            cwd=BASE_DIR,
            env={
                **os.environ,
                "DJANGO_SECRET_KEY": "test-secret",
                "DJANGO_DEBUG": "0",
                "DJANGO_TRUST_X_FORWARDED_PROTO": "1",
            },
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(), "('HTTP_X_FORWARDED_PROTO', 'https')"
        )

    def test_forwarded_proto_trust_defaults_off(self):
        env = os.environ.copy()
        env.pop("DJANGO_TRUST_X_FORWARDED_PROTO", None)
        env.update({"DJANGO_SECRET_KEY": "test-secret", "DJANGO_DEBUG": "0"})
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import project.settings as s; print(getattr(s, 'SECURE_PROXY_SSL_HEADER', None))",
            ],
            cwd=BASE_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "None")

    def test_audit_logger_emits_info_in_production_style_setup(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import django; django.setup(); import logging; "
                    "logging.getLogger('shiyuan.audit').info('AUDIT-PROBE')"
                ),
            ],
            cwd=BASE_DIR,
            env={
                **os.environ,
                "DJANGO_SETTINGS_MODULE": "project.settings",
                "DJANGO_SECRET_KEY": "test-secret",
                "DJANGO_DEBUG": "0",
            },
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("AUDIT-PROBE", result.stderr)

    def test_production_requirements_include_gunicorn(self):
        path = BASE_DIR / "requirements-prod.txt"
        self.assertTrue(path.exists(), "requirements-prod.txt is missing")
        content = path.read_text(encoding="utf-8")
        self.assertIn("-r requirements.txt", content)
        self.assertIn("gunicorn", content)

    def test_security_headers_configured(self):
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, "Lax")
        self.assertEqual(settings.CSRF_COOKIE_SAMESITE, "Lax")
        self.assertEqual(settings.SECURE_CONTENT_TYPE_NOSNIFF, True)
        self.assertEqual(settings.X_FRAME_OPTIONS, "DENY")
        self.assertEqual(settings.SECURE_REFERRER_POLICY, "same-origin")
        self.assertIn("default", settings.CACHES)

        security_index = settings.MIDDLEWARE.index(
            "django.middleware.security.SecurityMiddleware"
        )
        self.assertEqual(
            settings.MIDDLEWARE[security_index + 1],
            "whitenoise.middleware.WhiteNoiseMiddleware",
        )


class ForwardedProtoRequestTests(TestCase):
    @override_settings(
        SECURE_SSL_REDIRECT=True,
        SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"),
    )
    def test_forwarded_https_is_not_redirected_and_canonical_is_https(self):
        response = self.client.get(reverse("home"), HTTP_X_FORWARDED_PROTO="https")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<link rel="canonical" href="https://')

    @override_settings(SECURE_SSL_REDIRECT=True, SECURE_PROXY_SSL_HEADER=None)
    def test_plain_http_is_redirected_when_ssl_required(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response["Location"].startswith("https://"))

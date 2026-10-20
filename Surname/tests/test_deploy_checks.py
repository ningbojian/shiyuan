from __future__ import annotations

import os
import secrets
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

BASE_DIR = Path(settings.BASE_DIR)


def run_deploy_check(*, secure_ssl: bool) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "DJANGO_DEBUG": "0",
            "DJANGO_SECRET_KEY": secrets.token_urlsafe(50),
            "DJANGO_ALLOWED_HOSTS": "example.com",
            "DJANGO_SECURE_SSL": "1" if secure_ssl else "0",
        }
    )
    env.pop("DJANGO_CSRF_TRUSTED_ORIGINS", None)
    return subprocess.run(
        [sys.executable, "manage.py", "check", "--deploy"],
        cwd=BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


class DeployCheckTests(SimpleTestCase):
    def test_production_config_passes_deploy_checks(self):
        result = run_deploy_check(secure_ssl=True)
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("System check identified no issues", output)
        self.assertNotIn("security.W", output)

    def test_unhardened_config_reports_expected_warnings(self):
        result = run_deploy_check(secure_ssl=False)
        output = result.stdout + result.stderr
        for code in ("security.W004", "security.W008", "security.W012", "security.W016"):
            self.assertIn(code, output)

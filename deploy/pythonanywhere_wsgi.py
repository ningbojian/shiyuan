"""WSGI template for PythonAnywhere.

Copy this file's contents into the WSGI configuration file that
PythonAnywhere creates for your web app (``/var/www/<user>_pythonanywhere_com_wsgi.py``),
then replace ``YOUR_USERNAME`` with your PythonAnywhere username.

Do not use this file directly as ``project/wsgi.py``. The virtualenv is
selected in the PythonAnywhere Web tab; do not activate it here. Secrets
live in ``~/.shiyuan.env`` (chmod 600) and never in this repository.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PA_USERNAME = "YOUR_USERNAME"
PROJECT_HOME = Path(f"/home/{PA_USERNAME}/shiyuan")
ENV_FILE = Path.home() / ".shiyuan.env"


def _load_env_file(path: Path) -> None:
    """Load KEY=value lines without overriding variables set by the platform."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


if str(PROJECT_HOME) not in sys.path:
    sys.path.insert(0, str(PROJECT_HOME))

_load_env_file(ENV_FILE)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()

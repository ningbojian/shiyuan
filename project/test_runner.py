from __future__ import annotations

from pathlib import Path

from django.apps import apps
from django.test.runner import DiscoverRunner


class ProjectDiscoverRunner(DiscoverRunner):
    """Default to dotted app test labels.

    The interpreter's site-packages may contain a top-level ``tests``
    namespace package, which shadows app-level ``tests`` packages during
    unittest's directory discovery. Dotted labels avoid that ambiguity.
    """

    def build_suite(self, test_labels=None, **kwargs):
        if not test_labels:
            test_labels = [
                f"{config.name}.tests"
                for config in apps.get_app_configs()
                if (Path(config.path) / "tests" / "__init__.py").exists()
            ]
        return super().build_suite(test_labels, **kwargs)

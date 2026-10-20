from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from Surname.services.catalog import validate_catalog


class Command(BaseCommand):
    help = "Validate the surname catalog JSON file."

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            nargs="?",
            default=str(Path(settings.BASE_DIR) / "data" / "catalog.json"),
        )

    def handle(self, *args, **options):
        path = Path(options["path"])
        errors = validate_catalog(path, min_surnames=32)
        if errors:
            for error in errors:
                self.stderr.write(error)
            raise CommandError(f"目录校验失败：{len(errors)} 个问题")
        self.stdout.write(self.style.SUCCESS("目录校验通过。"))

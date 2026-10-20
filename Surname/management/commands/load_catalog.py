from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from Surname.services.catalog import CatalogValidationError, load_catalog


class Command(BaseCommand):
    help = "Load (or preview) the surname catalog JSON file."

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            nargs="?",
            default=str(Path(settings.BASE_DIR) / "data" / "catalog.json"),
        )
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--prune", action="store_true")

    def handle(self, *args, **options):
        path = Path(options["path"])
        try:
            stats = load_catalog(
                path,
                prune=options["prune"],
                dry_run=options["dry_run"],
            )
        except CatalogValidationError as exc:
            for error in exc.errors:
                self.stderr.write(error)
            raise CommandError(f"目录校验失败：{len(exc.errors)} 个问题") from exc

        prefix = "将加载" if options["dry_run"] else "已加载"
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix} {stats.surnames} 个姓氏、{stats.figures} 位人物、"
                f"{stats.events} 条迁徙事件、{stats.relations} 条关系。"
            )
        )
        if options["dry_run"]:
            self.stdout.write("dry-run：未写入数据库。")

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Surname", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("user", "0002_comment"),
    ]

    operations = [
        migrations.CreateModel(
            name="Favorite",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="收藏时间"),
                ),
                (
                    "surname",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="favorited_by",
                        to="Surname.secondname",
                        verbose_name="姓氏",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="favorites",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "收藏",
                "verbose_name_plural": "收藏",
                "db_table": "user_favorite",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ReadingHistory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "last_viewed_at",
                    models.DateTimeField(auto_now=True, verbose_name="最近浏览"),
                ),
                (
                    "view_count",
                    models.PositiveIntegerField(default=0, verbose_name="浏览次数"),
                ),
                (
                    "surname",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="read_by",
                        to="Surname.secondname",
                        verbose_name="姓氏",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="reading_history",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "浏览历史",
                "verbose_name_plural": "浏览历史",
                "db_table": "user_reading_history",
                "ordering": ["-last_viewed_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="favorite",
            constraint=models.UniqueConstraint(
                fields=("user", "surname"), name="favorite_unique_pair"
            ),
        ),
        migrations.AddConstraint(
            model_name="readinghistory",
            constraint=models.UniqueConstraint(
                fields=("user", "surname"), name="history_unique_pair"
            ),
        ),
    ]

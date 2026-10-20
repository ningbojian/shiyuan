from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Surname", "0004_famous_fk"),
    ]

    operations = [
        migrations.CreateModel(
            name="Clan",
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
                ("name", models.CharField(max_length=32, unique=True)),
                ("slug", models.SlugField(db_index=True, max_length=64, unique=True)),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("xing", "姓"),
                            ("shi", "氏"),
                            ("state", "国"),
                            ("other", "其他"),
                        ],
                        max_length=10,
                    ),
                ),
                ("description", models.TextField(blank=True)),
            ],
            options={
                "verbose_name": "宗族",
                "db_table": "clan",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="SurnameRelation",
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
                    "relation_type",
                    models.CharField(
                        choices=[
                            ("origin", "源出"),
                            ("branch", "分支"),
                            ("changed", "改姓"),
                            ("same_clan", "同源"),
                        ],
                        max_length=10,
                    ),
                ),
                ("description", models.TextField(blank=True)),
                ("source_note", models.TextField(blank=True)),
                (
                    "source",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="outgoing_relations",
                        to="Surname.secondname",
                    ),
                ),
                (
                    "target_clan",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.CASCADE,
                        related_name="surname_relations",
                        to="Surname.clan",
                    ),
                ),
                (
                    "target_surname",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.CASCADE,
                        related_name="incoming_relations",
                        to="Surname.secondname",
                    ),
                ),
            ],
            options={
                "verbose_name": "姓氏关系",
                "db_table": "surname_relation",
            },
        ),
        migrations.CreateModel(
            name="MigrationEvent",
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
                ("description", models.TextField()),
                ("source_note", models.TextField(blank=True)),
                ("order", models.PositiveSmallIntegerField(default=0)),
                (
                    "dynasty",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="migration_events",
                        to="Surname.dynasty",
                    ),
                ),
                (
                    "from_province",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="migration_from",
                        to="Surname.province",
                    ),
                ),
                (
                    "surname",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="migration_events",
                        to="Surname.secondname",
                    ),
                ),
                (
                    "to_province",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="migration_to",
                        to="Surname.province",
                    ),
                ),
            ],
            options={
                "verbose_name": "迁徙事件",
                "db_table": "migration_event",
                "ordering": ["dynasty__order", "order"],
            },
        ),
        migrations.AddConstraint(
            model_name="surnamerelation",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(target_surname__isnull=False, target_clan__isnull=True)
                    | models.Q(target_surname__isnull=True, target_clan__isnull=False)
                ),
                name="relation_one_target",
            ),
        ),
    ]

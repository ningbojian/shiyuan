from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Surname", "0002_catalog_schema"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="distribution",
            name="surname",
        ),
        migrations.RemoveField(
            model_name="distribution",
            name="province",
        ),
        migrations.RemoveField(
            model_name="distribution",
            name="ratio",
        ),
        migrations.AddField(
            model_name="distribution",
            name="surname",
            field=models.ForeignKey(
                default=1,
                on_delete=models.deletion.CASCADE,
                related_name="distributions",
                to="Surname.secondname",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="distribution",
            name="province",
            field=models.ForeignKey(
                default=1,
                on_delete=models.deletion.CASCADE,
                related_name="distributions",
                to="Surname.province",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="distribution",
            name="intensity",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="distribution",
            name="is_illustrative",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="distribution",
            name="source_note",
            field=models.CharField(blank=True, default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AlterModelOptions(
            name="distribution",
            options={"ordering": ["-intensity"], "verbose_name": "人口分布"},
        ),
        migrations.AddConstraint(
            model_name="distribution",
            constraint=models.UniqueConstraint(
                fields=("surname", "province"), name="dist_surname_province_uniq"
            ),
        ),
        migrations.AddConstraint(
            model_name="distribution",
            constraint=models.CheckConstraint(
                condition=models.Q(intensity__gte=0) & models.Q(intensity__lte=100),
                name="dist_intensity_range",
            ),
        ),
    ]

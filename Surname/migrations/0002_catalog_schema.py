import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Surname", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="secondname",
            old_name="count",
            new_name="view_count",
        ),
        migrations.AddField(
            model_name="secondname",
            name="slug",
            field=models.SlugField(default="", max_length=32, unique=True, db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="secondname",
            name="pinyin",
            field=models.CharField(default="", max_length=64, db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="secondname",
            name="initial",
            field=models.CharField(default="", max_length=1, db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="secondname",
            name="aliases",
            field=models.CharField(blank=True, default="", max_length=128),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="secondname",
            name="summary",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="secondname",
            name="keywords",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="secondname",
            name="source_note",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="secondname",
            name="is_demo",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="secondname",
            name="is_featured",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="secondname",
            name="popularity",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="secondname",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="secondname",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="secondname",
            name="base_information",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="secondname",
            name="fam",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="secondname",
            name="mig",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="secondname",
            name="dis",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="secondname",
            name="ori",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="secondname",
            name="cul",
            field=models.TextField(blank=True),
        ),
        migrations.RemoveField(
            model_name="secondname",
            name="father_surname",
        ),
        migrations.AddField(
            model_name="province",
            name="slug",
            field=models.SlugField(default="", max_length=64, unique=True, db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="province",
            name="short_name",
            field=models.CharField(blank=True, default="", max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="province",
            name="map_name",
            field=models.CharField(blank=True, default="", max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="province",
            name="region",
            field=models.CharField(blank=True, default="", max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="province",
            name="center_lng",
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name="province",
            name="center_lat",
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterModelOptions(
            name="province",
            options={"ordering": ["name"], "verbose_name": "省份"},
        ),
        migrations.AddField(
            model_name="dynasty",
            name="slug",
            field=models.SlugField(default="", max_length=64, unique=True, db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="dynasty",
            name="order",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="dynasty",
            name="period_label",
            field=models.CharField(blank=True, default="", max_length=32),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="dynasty",
            name="description",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AlterModelOptions(
            name="dynasty",
            options={"ordering": ["order"], "verbose_name": "朝代"},
        ),
    ]

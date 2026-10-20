from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Surname", "0003_distribution_fk"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="famous",
            name="surname",
        ),
        migrations.RemoveField(
            model_name="famous",
            name="dynasty",
        ),
        migrations.AddField(
            model_name="famous",
            name="surname",
            field=models.ForeignKey(
                default=1,
                on_delete=models.deletion.CASCADE,
                related_name="figures",
                to="Surname.secondname",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="famous",
            name="dynasty",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="figures",
                to="Surname.dynasty",
            ),
        ),
        migrations.AddField(
            model_name="famous",
            name="slug",
            field=models.SlugField(default="", max_length=64, unique=True, db_index=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="famous",
            name="name",
            field=models.CharField(max_length=32, verbose_name="姓名"),
        ),
        migrations.AlterField(
            model_name="famous",
            name="info",
            field=models.TextField(verbose_name="简介"),
        ),
        migrations.AddField(
            model_name="famous",
            name="birth_year",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="famous",
            name="death_year",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="famous",
            name="source_note",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="famous",
            name="is_demo",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="famous",
            name="order",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name="famous",
            options={"ordering": ["order", "name"], "verbose_name": "历史人物"},
        ),
        migrations.AddConstraint(
            model_name="famous",
            constraint=models.UniqueConstraint(
                fields=("surname", "name", "dynasty"),
                name="famous_unique_per_dynasty",
            ),
        ),
    ]

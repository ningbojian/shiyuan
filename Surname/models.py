import re

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.text import slugify
from pypinyin import lazy_pinyin


def _unique_slug(instance, base: str, max_length: int) -> str:
    """Return a slug that is unique within the instance's model."""
    base = slugify(base) or "surname"
    base = base[:max_length]
    candidate = base
    index = 2
    queryset = type(instance)._default_manager.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    while queryset.filter(slug=candidate).exists():
        suffix = f"-{index}"
        candidate = f"{base[: max_length - len(suffix)]}{suffix}"
        index += 1
    return candidate


class SecondName(models.Model):
    second_name = models.CharField(verbose_name="姓氏", max_length=32, primary_key=True)
    slug = models.SlugField(max_length=32, unique=True, db_index=True)
    pinyin = models.CharField(max_length=64, db_index=True)
    initial = models.CharField(max_length=1, db_index=True)
    aliases = models.CharField(max_length=128, blank=True)
    summary = models.TextField(blank=True)
    base_information = models.TextField(blank=True)
    fam = models.TextField(blank=True)
    mig = models.TextField(blank=True)
    dis = models.TextField(blank=True)
    ori = models.TextField(blank=True)
    cul = models.TextField(blank=True)
    keywords = models.JSONField(default=list, blank=True)
    source_note = models.TextField(blank=True)
    is_demo = models.BooleanField(default=True)
    is_imported = models.BooleanField(default=False, db_index=True)
    is_featured = models.BooleanField(default=False)
    popularity = models.PositiveIntegerField(default=0)
    view_count = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "姓氏"
        db_table = "surname"

    def __str__(self):
        return self.second_name

    def save(self, *args, **kwargs):
        if not self.pinyin:
            self.pinyin = "".join(lazy_pinyin(self.second_name)).lower()
        if not self.initial:
            self.initial = (self.pinyin[:1] or self.second_name[:1]).upper()
        if not self.slug:
            self.slug = _unique_slug(self, self.pinyin, 32)
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if not re.fullmatch(r"[A-Z]", self.initial or ""):
            raise ValidationError({"initial": "首字母必须为 A-Z。"})
        if not isinstance(self.keywords, list):
            raise ValidationError({"keywords": "关键词必须是列表。"})
        for item in self.keywords:
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("name"), str)
                or not item["name"].strip()
                or isinstance(item.get("value"), bool)
                or not isinstance(item.get("value"), int)
                or not 1 <= item["value"] <= 100
            ):
                raise ValidationError(
                    {"keywords": "关键词必须是 name/value（1-100）对象。"}
                )


class Province(models.Model):
    name = models.CharField(verbose_name="省份名称", max_length=10, primary_key=True)
    slug = models.SlugField(max_length=64, unique=True, db_index=True)
    short_name = models.CharField(max_length=10, blank=True)
    map_name = models.CharField(max_length=10, blank=True)
    region = models.CharField(max_length=10, blank=True)
    center_lng = models.FloatField(default=0.0)
    center_lat = models.FloatField(default=0.0)

    class Meta:
        verbose_name = "省份"
        db_table = "province"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Dynasty(models.Model):
    name = models.CharField(verbose_name="朝代名称", max_length=10, primary_key=True)
    slug = models.SlugField(max_length=64, unique=True, db_index=True)
    order = models.PositiveSmallIntegerField(default=0)
    begin = models.IntegerField(verbose_name="起始时间", blank=True, null=True)
    end = models.IntegerField(verbose_name="终止时间", blank=True, null=True)
    period_label = models.CharField(max_length=32, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "朝代"
        db_table = "dynasty"
        ordering = ["order"]

    def __str__(self):
        return self.name


class Distribution(models.Model):
    surname = models.ForeignKey(
        SecondName, on_delete=models.CASCADE, related_name="distributions"
    )
    province = models.ForeignKey(
        Province, on_delete=models.CASCADE, related_name="distributions"
    )
    intensity = models.PositiveSmallIntegerField(default=0)
    is_illustrative = models.BooleanField(default=True)
    source_note = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "人口分布"
        db_table = "distribution"
        ordering = ["-intensity"]
        constraints = [
            models.UniqueConstraint(
                fields=["surname", "province"], name="dist_surname_province_uniq"
            ),
            models.CheckConstraint(
                condition=Q(intensity__gte=0) & Q(intensity__lte=100),
                name="dist_intensity_range",
            ),
        ]

    def __str__(self):
        return f"{self.surname} · {self.province}"


class Famous(models.Model):
    surname = models.ForeignKey(
        SecondName, on_delete=models.CASCADE, related_name="figures"
    )
    dynasty = models.ForeignKey(
        Dynasty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="figures",
    )
    name = models.CharField(verbose_name="姓名", max_length=32)
    slug = models.SlugField(max_length=64, unique=True, db_index=True)
    info = models.TextField(verbose_name="简介")
    birth_year = models.IntegerField(null=True, blank=True)
    death_year = models.IntegerField(null=True, blank=True)
    source_note = models.TextField(blank=True)
    is_demo = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "历史人物"
        db_table = "famous"
        ordering = ["order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["surname", "name", "dynasty"],
                name="famous_unique_per_dynasty",
            )
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = "".join(lazy_pinyin(self.name)) or self.name
            self.slug = _unique_slug(self, base, 64)
        super().save(*args, **kwargs)


class Clan(models.Model):
    KIND_CHOICES = [
        ("xing", "姓"),
        ("shi", "氏"),
        ("state", "国"),
        ("other", "其他"),
    ]

    name = models.CharField(max_length=32, unique=True)
    slug = models.SlugField(max_length=64, unique=True, db_index=True)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "宗族"
        db_table = "clan"
        ordering = ["name"]

    def __str__(self):
        return self.name


class SurnameRelation(models.Model):
    RELATION_CHOICES = [
        ("origin", "源出"),
        ("branch", "分支"),
        ("changed", "改姓"),
        ("same_clan", "同源"),
    ]

    source = models.ForeignKey(
        SecondName, on_delete=models.CASCADE, related_name="outgoing_relations"
    )
    target_surname = models.ForeignKey(
        SecondName,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="incoming_relations",
    )
    target_clan = models.ForeignKey(
        Clan,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="surname_relations",
    )
    relation_type = models.CharField(max_length=10, choices=RELATION_CHOICES)
    description = models.TextField(blank=True)
    source_note = models.TextField(blank=True)

    class Meta:
        verbose_name = "姓氏关系"
        db_table = "surname_relation"
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(target_surname__isnull=False, target_clan__isnull=True)
                    | Q(target_surname__isnull=True, target_clan__isnull=False)
                ),
                name="relation_one_target",
            )
        ]

    def __str__(self):
        target = self.target_surname or self.target_clan
        return f"{self.source} → {target}（{self.get_relation_type_display()}）"

    def clean(self):
        super().clean()
        if (self.target_surname is None) == (self.target_clan is None):
            raise ValidationError("目标必须是姓氏或宗族之一。")
        if self.source_id and self.target_surname_id:
            duplicates = SurnameRelation.objects.filter(
                source_id=self.source_id,
                target_surname_id=self.target_surname_id,
                relation_type=self.relation_type,
            )
            if self.pk:
                duplicates = duplicates.exclude(pk=self.pk)
            if duplicates.exists():
                raise ValidationError("已存在相同的关系。")


class MigrationEvent(models.Model):
    surname = models.ForeignKey(
        SecondName, on_delete=models.CASCADE, related_name="migration_events"
    )
    dynasty = models.ForeignKey(
        Dynasty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="migration_events",
    )
    from_province = models.ForeignKey(
        Province,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="migration_from",
    )
    to_province = models.ForeignKey(
        Province,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="migration_to",
    )
    description = models.TextField()
    source_note = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "迁徙事件"
        db_table = "migration_event"
        ordering = ["dynasty__order", "order"]

    def __str__(self):
        return f"{self.surname} · {self.dynasty or '时期不详'}"

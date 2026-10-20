from __future__ import annotations

from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="账号",
    )
    display_name = models.CharField(max_length=40, blank=True, verbose_name="显示名称")
    home_surname = models.ForeignKey(
        "Surname.SecondName",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="interested_users",
        verbose_name="关注姓氏",
    )
    bio = models.TextField(blank=True, verbose_name="简介")
    is_supporter = models.BooleanField(default=False, verbose_name="支持者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "user_profile"
        verbose_name = "用户资料"
        verbose_name_plural = "用户资料"

    def __str__(self) -> str:
        return self.display_name or self.user.username


class Comment(models.Model):
    STATUS_VISIBLE = "visible"
    STATUS_HIDDEN = "hidden"
    STATUS_CHOICES = [
        (STATUS_VISIBLE, "显示"),
        (STATUS_HIDDEN, "隐藏"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="用户",
    )
    surname = models.ForeignKey(
        "Surname.SecondName",
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="姓氏",
    )
    content = models.TextField(max_length=1000, verbose_name="评论内容")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_VISIBLE,
        verbose_name="状态",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "user_comment"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["surname", "status", "-created_at"],
                name="comment_surname_status_idx",
            )
        ]
        verbose_name = "评论"
        verbose_name_plural = "评论"

    def __str__(self) -> str:
        return f"{self.user}: {self.content[:30]}"


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="用户",
    )
    surname = models.ForeignKey(
        "Surname.SecondName",
        on_delete=models.CASCADE,
        related_name="favorited_by",
        verbose_name="姓氏",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="收藏时间")

    class Meta:
        db_table = "user_favorite"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "surname"], name="favorite_unique_pair"
            )
        ]
        verbose_name = "收藏"
        verbose_name_plural = "收藏"

    def __str__(self) -> str:
        return f"{self.user} ★ {self.surname}"


class ReadingHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reading_history",
        verbose_name="用户",
    )
    surname = models.ForeignKey(
        "Surname.SecondName",
        on_delete=models.CASCADE,
        related_name="read_by",
        verbose_name="姓氏",
    )
    last_viewed_at = models.DateTimeField(auto_now=True, verbose_name="最近浏览")
    view_count = models.PositiveIntegerField(default=0, verbose_name="浏览次数")

    class Meta:
        db_table = "user_reading_history"
        ordering = ["-last_viewed_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "surname"], name="history_unique_pair"
            )
        ]
        verbose_name = "浏览历史"
        verbose_name_plural = "浏览历史"

    def __str__(self) -> str:
        return f"{self.user} · {self.surname}"

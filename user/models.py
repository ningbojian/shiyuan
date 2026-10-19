from django.contrib.auth.models import AbstractBaseUser
from django.db import models


class User(AbstractBaseUser):
    name = models.CharField(max_length=20, verbose_name="用户名称")
    account = models.CharField(max_length=20, verbose_name="用户账号", primary_key=True)
    # Legacy field from the 2022 course project. New accounts store the hash
    # in AbstractBaseUser.password and leave this blank.
    code = models.CharField(max_length=40, verbose_name="旧密码字段", blank=True, default="")
    surname = models.CharField(max_length=5, verbose_name="用户姓氏", blank=True, null=True)
    count = models.IntegerField(default=1)
    creat_time = models.DateField(verbose_name="创建时间", auto_now_add=True)
    lately = models.DateField(verbose_name="最近登录时间", auto_now=True)
    vip = models.BooleanField(default=False)
    vip_begin = models.DateTimeField(blank=True, null=True)
    vip_end = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = "account"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        verbose_name = "用户信息"
        db_table = "user"

    def __str__(self) -> str:
        return self.account


class Comment(models.Model):
    account = models.ForeignKey(
        to="User",
        on_delete=models.CASCADE,
        related_name="C_account",
    )
    content = models.CharField(max_length=200, verbose_name="评论内容")
    creatTime = models.DateField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        db_table = "comment"

    def __str__(self) -> str:
        return f"{self.account}: {self.content[:30]}"

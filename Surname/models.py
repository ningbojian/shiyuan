from django.db import models


# Create your models here.
class SecondName(models.Model):
    second_name = models.CharField(verbose_name = u"姓氏" ,max_length=32 , primary_key=True)
    base_information = models.CharField(verbose_name= u'基本信息' , max_length=1024)
    fam = models.CharField(verbose_name=u'历代名人' , max_length=1024)
    mig = models.CharField(verbose_name=u'迁徙传播' , max_length=1024)
    dis = models.CharField(verbose_name=u'人口分布' , max_length=1024)
    ori = models.CharField(verbose_name=u'姓氏起源' , max_length=1024)
    cul = models.CharField(verbose_name=u'姓氏文化' , max_length=1024)
    father_surname = models.ManyToManyField(to='self',symmetrical=False,related_name='children')
    count = models.PositiveBigIntegerField(default=0)
    class Meta:
        verbose_name = "姓氏"
        db_table = "surname"

class Province(models.Model):
    name = models.CharField(verbose_name = u"省份名称" ,max_length=10 , primary_key=True)
    class Meta:
         verbose_name = "省份"
         db_table = 'province'

class Dynasty(models.Model):
    name = models.CharField(verbose_name = u"朝代名称" ,max_length=10,primary_key=True)
    begin = models.IntegerField(verbose_name=u'起始时间',blank=True , null=True)
    end = models.IntegerField(verbose_name=u'终止时间',blank=True,null=True)
    class Meta:
         verbose_name = "朝代"
         db_table = 'dynasty'

class Distribution(models.Model):
    surname = models.ManyToManyField(
        to="SecondName", related_name="D_surname", verbose_name="姓氏"
    )
    province = models.ManyToManyField(
        to="Province", related_name="D_province", verbose_name="省份"
    )
    ratio = models.FloatField(verbose_name="比例")

    class Meta:
        verbose_name = "人口分布"
        db_table = "distribution"


class Famous(models.Model):
    surname = models.ManyToManyField(
        to="SecondName", related_name="F_surname", verbose_name="姓氏"
    )
    dynasty = models.ManyToManyField(
        to="Dynasty", related_name="F_dynasty", verbose_name="朝代"
    )
    name = models.CharField(verbose_name="姓名", max_length=15)
    info = models.CharField(verbose_name="简介", max_length=50)

    class Meta:
        verbose_name = "姓氏名人"
        db_table = "famous"

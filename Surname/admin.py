from django.contrib import admin

from Surname.models import (
    Clan,
    Distribution,
    Dynasty,
    Famous,
    MigrationEvent,
    Province,
    SecondName,
    SurnameRelation,
)


@admin.register(SecondName)
class SecondNameAdmin(admin.ModelAdmin):
    list_display = ("second_name", "pinyin", "initial", "is_featured", "view_count")
    list_filter = ("initial", "is_featured", "is_demo")
    search_fields = ("second_name", "pinyin", "aliases", "summary")
    prepopulated_fields = {"slug": ("pinyin",)}


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "region")
    search_fields = ("name", "short_name")


@admin.register(Dynasty)
class DynastyAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "begin", "end")
    ordering = ("order",)


@admin.register(Distribution)
class DistributionAdmin(admin.ModelAdmin):
    list_display = ("surname", "province", "intensity", "is_illustrative")
    list_filter = ("is_illustrative", "province")
    search_fields = ("surname__second_name",)
    list_select_related = ("surname", "province")


@admin.register(Famous)
class FamousAdmin(admin.ModelAdmin):
    list_display = ("name", "surname", "dynasty", "order")
    list_filter = ("dynasty", "is_demo")
    search_fields = ("name", "surname__second_name", "info")
    list_select_related = ("surname", "dynasty")


@admin.register(Clan)
class ClanAdmin(admin.ModelAdmin):
    list_display = ("name", "kind")
    list_filter = ("kind",)
    search_fields = ("name", "description")


@admin.register(SurnameRelation)
class SurnameRelationAdmin(admin.ModelAdmin):
    list_display = ("source", "target_surname", "target_clan", "relation_type")
    list_filter = ("relation_type",)
    search_fields = ("source__second_name", "target_surname__second_name")
    list_select_related = ("source", "target_surname", "target_clan")


@admin.register(MigrationEvent)
class MigrationEventAdmin(admin.ModelAdmin):
    list_display = ("surname", "dynasty", "from_province", "to_province", "order")
    list_filter = ("dynasty",)
    search_fields = ("surname__second_name", "description")
    list_select_related = ("surname", "dynasty", "from_province", "to_province")

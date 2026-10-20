from django.contrib import admin

from user.models import Comment, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "home_surname", "is_supporter", "updated_at")
    list_filter = ("is_supporter",)
    search_fields = ("user__username", "display_name")
    list_select_related = ("user", "home_surname")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("user", "surname", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("content", "user__username", "surname__second_name")
    list_select_related = ("user", "surname")
    readonly_fields = ("created_at", "updated_at")

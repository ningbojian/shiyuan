from django.urls import path
from django.views.generic import RedirectView

from user import views

app_name = "user"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("personal/", views.personal, name="personal"),
    path("profile/", views.profile_edit, name="profile_edit"),
    path("password/", views.password_change, name="password_change"),
    path(
        "favorite/<slug:slug>/",
        views.toggle_favorite,
        name="favorite_toggle",
    ),
    path("favorites/", views.favorites, name="favorites"),
    path("history/", views.history, name="history"),
    path(
        "history/<int:pk>/delete/",
        views.delete_history,
        name="history_delete",
    ),
    path(
        "comment/<str:second_name>/add/",
        views.add_comment,
        name="comment_add",
    ),
    path(
        "comment/<int:comment_id>/delete/",
        views.delete_comment,
        name="comment_delete",
    ),
    path(
        "comment/<int:comment_id>/hide/",
        views.hide_comment,
        name="comment_hide",
    ),
    # Legacy course-project URLs kept as redirects.
    path(
        "log/",
        RedirectView.as_view(pattern_name="user:login", permanent=False),
    ),
    path(
        "create/",
        RedirectView.as_view(pattern_name="user:register", permanent=False),
    ),
    path("", RedirectView.as_view(url="/", permanent=False)),
]

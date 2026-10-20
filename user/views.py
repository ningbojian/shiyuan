from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from Surname.models import SecondName
from user.forms import CommentForm, LoginForm, ProfileForm, RegisterForm
from user.models import Comment, Favorite, Profile, ReadingHistory
from user.throttle import cache_key, clear, is_limited, rate_limit, record_failure

logger = logging.getLogger("shiyuan.audit")

LOGIN_FAILURE_LIMIT = 5
LOGIN_FAILURE_WINDOW_SECONDS = 300
COMMENT_LIMIT = 10
COMMENT_WINDOW_SECONDS = 600


def _login_failure_key(ip: str, username: str) -> str:
    return cache_key("login-fail", f"{ip}:{username.strip().lower()}")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("user:personal")

    next_url = request.POST.get("next") or request.GET.get("next") or ""

    if request.method == "POST":
        username = request.POST.get("username", "")
        ip = request.META.get("REMOTE_ADDR", "")
        key = _login_failure_key(ip, username)
        form = LoginForm(request, data=request.POST)

        if is_limited(key, LOGIN_FAILURE_LIMIT):
            form.add_error(None, "尝试次数过多，请稍后再试")
            logger.warning("login throttled username=%r ip=%s", username, ip)
        elif form.is_valid():
            user = form.get_user()
            login(request, user)
            clear(key)
            logger.info("login success user=%s ip=%s", user.pk, ip)
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect("user:personal")
        else:
            record_failure(key, LOGIN_FAILURE_WINDOW_SECONDS)
            logger.warning("login failure username=%r ip=%s", username, ip)
    else:
        form = LoginForm(request)

    return render(request, "user/login.html", {"form": form, "next": next_url})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("user:personal")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.display_name = form.cleaned_data["display_name"]
            profile.save(update_fields=["display_name"])
            login(request, user)
            return redirect("user:personal")
    else:
        form = RegisterForm()

    return render(request, "user/register.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("/")


@login_required
def personal(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(
        request,
        "user/personal.html",
        {
            "profile": profile,
            "favorite_count": Favorite.objects.filter(user=request.user).count(),
            "history_count": ReadingHistory.objects.filter(user=request.user).count(),
            "comment_count": Comment.objects.filter(user=request.user).count(),
            "recent_comments": Comment.objects.filter(user=request.user)
            .select_related("surname")
            .order_by("-created_at")[:5],
        },
    )


@login_required
def profile_edit(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "资料已更新。")
            return redirect("user:personal")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "user/profile_edit.html", {"form": form})


@login_required
def password_change(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "密码已更新。")
            return redirect("user:personal")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "user/password_change.html", {"form": form})


def _surname_detail_url(surname: SecondName) -> str:
    return reverse("Surname:detail", args=[surname.slug])


@login_required
def favorites(request):
    queryset = Favorite.objects.filter(user=request.user).select_related("surname")
    page_obj = Paginator(queryset, 20).get_page(request.GET.get("page"))
    return render(
        request,
        "user/favorites.html",
        {"page_obj": page_obj, "favorites": page_obj.object_list},
    )


@login_required
def history(request):
    queryset = ReadingHistory.objects.filter(user=request.user).select_related(
        "surname"
    )
    page_obj = Paginator(queryset, 20).get_page(request.GET.get("page"))
    return render(
        request,
        "user/history.html",
        {"page_obj": page_obj, "entries": page_obj.object_list},
    )


@login_required
@require_POST
def delete_history(request, pk: int):
    entry = get_object_or_404(ReadingHistory, pk=pk, user=request.user)
    entry.delete()
    messages.success(request, "已从浏览历史中移除。")
    return redirect("user:history")


@login_required
@require_POST
def toggle_favorite(request, slug: str):
    surname = get_object_or_404(SecondName, slug=slug)
    favorite = Favorite.objects.filter(user=request.user, surname=surname)
    if favorite.exists():
        favorite.delete()
        messages.success(request, "已取消收藏。")
    else:
        Favorite.objects.create(user=request.user, surname=surname)
        messages.success(request, "已加入收藏。")
    return redirect("Surname:detail", slug=surname.slug)


@login_required
@require_POST
def add_comment(request, second_name: str):
    surname = get_object_or_404(SecondName, second_name=second_name)
    form = CommentForm(request.POST)
    if form.is_valid():
        key = cache_key("comment", str(request.user.pk))
        if not rate_limit(key, COMMENT_LIMIT, COMMENT_WINDOW_SECONDS):
            messages.error(request, "评论过于频繁，请稍后再试。")
            logger.warning("comment throttled user=%s", request.user.pk)
        else:
            Comment.objects.create(
                user=request.user,
                surname=surname,
                content=form.cleaned_data["content"],
            )
            messages.success(request, "评论已发表。")
    else:
        messages.error(request, "评论内容不能为空，且不得超过 1000 字。")
    return redirect(_surname_detail_url(surname))


@login_required
@require_POST
def delete_comment(request, comment_id: int):
    comment = get_object_or_404(Comment, pk=comment_id, user=request.user)
    surname = comment.surname
    comment.delete()
    logger.info("comment delete user=%s comment=%s", request.user.pk, comment_id)
    messages.success(request, "评论已删除。")
    return redirect(_surname_detail_url(surname))


@login_required
@require_POST
def hide_comment(request, comment_id: int):
    if not request.user.is_staff:
        raise PermissionDenied
    comment = get_object_or_404(Comment, pk=comment_id)
    comment.status = Comment.STATUS_HIDDEN
    comment.save(update_fields=["status", "updated_at"])
    logger.info("comment hide staff=%s comment=%s", request.user.pk, comment_id)
    messages.success(request, "评论已隐藏。")
    return redirect(_surname_detail_url(comment.surname))

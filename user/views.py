import json
from datetime import datetime

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from user.forms import UserCreatForm
from user.models import Comment, User


def getToken(request):
    """Return a CSRF token for the small Vue front-end."""
    return JsonResponse({"token": get_token(request)})


class UsersAction(View):
    def get(self, request):
        return render(request, "user/index.html")

    def log(request):
        if "user_info" in request.session:
            return HttpResponseRedirect(reverse("user:personal"))
        return render(request, "user/login.html")

    def login(request):
        account = request.POST.get("account")
        code = request.POST.get("code")
        if not account or not code:
            return render(request, "user/login.html", {"err": "账号或密码错误"})

        user = User.objects.filter(account=account).first()
        if user is None:
            return render(request, "user/login.html", {"err": "账号不存在"})

        # New accounts use Django's password hash; ``code`` is a legacy
        # plaintext field from the original course project.
        if user.check_password(code) or (user.code and user.code == code):
            if user.code and not user.check_password(code):
                user.set_password(code)
                user.code = ""
                user.save(update_fields=["password", "code"])
            request.session["user_info"] = user.account
            request.session["user_name"] = user.name
            return HttpResponseRedirect(reverse("user:personal"))
        return render(request, "user/login.html", {"err": "账号或密码错误"})

    def create(request):
        form = UserCreatForm(data=request.POST)
        if not form.is_valid():
            return JsonResponse({"error": form.errors.get_json_data()}, status=400)

        if User.objects.filter(account=form.cleaned_data["account"]).exists():
            return JsonResponse({"error": {"account": "账号已存在"}}, status=400)

        user = User(
            name=form.cleaned_data["name"],
            account=form.cleaned_data["account"],
            surname=request.POST.get("surname") or None,
            code="",
        )
        user.set_password(form.cleaned_data["code"])
        user.save()
        request.session["is_login"] = "true"
        return HttpResponseRedirect(reverse("user:personal"))

    def changeVip(self, request):
        account = request.POST.get("account")
        if not account:
            return JsonResponse({"err": "请输入账号"}, status=400)
        user = User.objects.filter(account=account).first()
        if user is None:
            return JsonResponse({"err": "请输入正确的账号"}, status=400)

        try:
            months = int(request.POST.get("month", "1"))
        except (TypeError, ValueError):
            months = 1
        now = datetime.now()
        total_month = now.month - 1 + max(months, 1)
        year = now.year + total_month // 12
        month = total_month % 12 + 1
        user.vip = True
        user.vip_begin = now
        user.vip_end = now.replace(year=year, month=month)
        user.save(update_fields=["vip", "vip_begin", "vip_end"])
        return JsonResponse({"success": "恭喜成为VIP"})

    def alter(self, request):
        account = request.POST.get("account")
        if not account:
            return JsonResponse({"err": "请输入账号"}, status=400)
        user = User.objects.filter(account=account).first()
        if user is None:
            return JsonResponse({"err": "请输入正确的账号"}, status=400)

        code = request.POST.get("code")
        name = request.POST.get("name")
        surname = request.POST.get("surname")
        if code:
            if user.check_password(code):
                return JsonResponse({"err": "请输入与上次不同的密码"})
            user.set_password(code)
            user.code = ""
        if name:
            user.name = name
        if surname:
            user.surname = surname
        user.save()
        return JsonResponse({"success": "更改成功"})

    def comment(request):
        # The original course front-end uses query parameters. This is kept
        # for compatibility; a production version should use POST + CSRF.
        params = request.POST if request.method == "POST" else request.GET
        action = params.get("action")
        if not action:
            return JsonResponse({"err": {"action": "请输入操作"}}, status=400)
        account = params.get("account")
        content = params.get("content")
        errors = {}
        if not account:
            errors["account"] = "请输入账号"
        if not content and action != "find":
            errors["content"] = "请输入内容"
        if errors:
            return JsonResponse(errors, status=400)

        user = User.objects.filter(account=account).first()
        if user is None:
            return JsonResponse({"account": "请输入正确账号"}, status=400)

        if action == "find":
            return JsonResponse({"msg": list(user.C_account.values_list("content", flat=True))})

        comment = Comment.objects.filter(account=user, content=content).first()
        if action in {"delete", "alter"} and comment is None:
            return JsonResponse({"content": "请输入正确内容"}, status=400)

        if action == "delete":
            comment.delete()
        elif action == "alter":
            new_content = params.get("newComment")
            if not new_content:
                return JsonResponse({"err": {"newComment": "请输入新的评论"}}, status=400)
            comment.content = new_content
            comment.save(update_fields=["content"])
        elif action == "add":
            Comment.objects.create(account=user, content=content)
        else:
            return JsonResponse({"success": "操作成功"})
        return JsonResponse({"success": "操作成功"})

    def register(request):
        return render(request, "user/register.html")

    def personal(request):
        account = request.session.get("user_info")
        if not account:
            return HttpResponseRedirect(reverse("user:log"))
        user = User.objects.filter(account=account).first()
        if user is None:
            request.session.flush()
            return HttpResponseRedirect(reverse("user:log"))
        return render(request, "user/personal.html", {"user": user})

    def logout(request):
        request.session.pop("user_info", None)
        request.session.pop("user_name", None)
        return HttpResponseRedirect(reverse("user:log"))

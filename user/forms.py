from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from user.models import Comment, Profile


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="账号",
        max_length=150,
        widget=forms.TextInput(
            attrs={"autocomplete": "username", "autofocus": True}
        ),
    )
    password = forms.CharField(
        label="密码",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    error_messages = {
        "invalid_login": "账号或密码错误",
        "inactive": "该账号已被停用",
    }


class RegisterForm(UserCreationForm):
    display_name = forms.CharField(
        label="显示名称",
        max_length=40,
        required=False,
    )

    class Meta(UserCreationForm.Meta):
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "账号"
        self.fields["username"].widget.attrs.update(
            {"autocomplete": "username", "autofocus": True}
        )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("display_name", "home_surname", "bio")
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("content",)
        widgets = {
            "content": forms.Textarea(
                attrs={"rows": 3, "maxlength": 1000, "placeholder": "写下你的看法"}
            )
        }

    def clean_content(self) -> str:
        content = self.cleaned_data["content"].strip()
        if not content:
            raise forms.ValidationError("评论不能为空。")
        return content

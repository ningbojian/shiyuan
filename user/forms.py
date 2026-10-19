from django import forms


class UserCreatForm(forms.Form):
    name = forms.CharField(
        max_length=20,
        error_messages={"required": "用户名不能为空", "max_length": "用户名不得超过20个字符"},
    )
    account = forms.CharField(
        max_length=20,
        error_messages={"required": "账号不能为空", "max_length": "账号不得超过20个字符"},
    )
    code = forms.CharField(
        max_length=40,
        min_length=6,
        error_messages={
            "required": "密码不能为空",
            "max_length": "密码不得超过40个字符",
            "min_length": "密码最少要有6个字符或数字",
        },
    )

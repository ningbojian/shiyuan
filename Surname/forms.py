from string import ascii_uppercase

from django import forms

from Surname.models import Province

INITIAL_CHOICES = [("", "全部首字母")] + [(letter, letter) for letter in ascii_uppercase]

SORT_CHOICES = [
    ("popular", "热门优先"),
    ("name", "姓氏排序"),
]


class SurnameFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        max_length=64,
        label="关键词",
        widget=forms.SearchInput(
            attrs={
                "placeholder": "姓氏、拼音、首字母或别名",
                "autocomplete": "off",
            }
        ),
    )
    initial = forms.ChoiceField(
        required=False,
        choices=INITIAL_CHOICES,
        label="首字母",
    )
    province = forms.ModelChoiceField(
        required=False,
        queryset=Province.objects.order_by("name"),
        label="省份",
        empty_label="全部省份",
    )
    sort = forms.ChoiceField(
        required=False,
        choices=SORT_CHOICES,
        initial="popular",
        label="排序",
    )

    def clean_q(self):
        return (self.cleaned_data.get("q") or "").strip()

    def clean_initial(self):
        return (self.cleaned_data.get("initial") or "").upper()

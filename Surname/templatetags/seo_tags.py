from __future__ import annotations

import json

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def jsonld(value):
    """Serialize JSON-LD and neutralise characters that can break out of <script>."""
    if not value:
        return ""
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    for char, escape in (
        ("<", "\\u003C"),
        (">", "\\u003E"),
        ("&", "\\u0026"),
        (chr(0x2028), "\\u2028"),
        (chr(0x2029), "\\u2029"),
    ):
        text = text.replace(char, escape)
    return mark_safe(text)

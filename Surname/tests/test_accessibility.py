from __future__ import annotations

import re

from django.conf import settings
from django.test import SimpleTestCase

TOKENS_PATH = settings.BASE_DIR / "static" / "css" / "tokens.css"
MAIN_CSS_PATH = settings.BASE_DIR / "static" / "css" / "main.css"


def relative_luminance(hex_color: str) -> float:
    channels = [int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(first: str, second: str) -> float:
    low, high = sorted((relative_luminance(first), relative_luminance(second)))
    return (high + 0.05) / (low + 0.05)


def color_values(css: str, name: str) -> list[str]:
    return re.findall(rf"--{name}:\s*(#[0-9a-fA-F]{{6}})", css)


class TokenContrastTests(SimpleTestCase):
    def setUp(self):
        self.css = TOKENS_PATH.read_text(encoding="utf-8")

    def test_muted_text_meets_aa_in_light_and_night_themes(self):
        muted = color_values(self.css, "muted")
        paper = color_values(self.css, "paper")
        paper_deep = color_values(self.css, "paper-deep")
        self.assertEqual(len(muted), 2)
        self.assertEqual(len(paper), 2)
        self.assertEqual(len(paper_deep), 2)

        self.assertGreaterEqual(contrast_ratio(muted[0], paper[0]), 4.5)
        self.assertGreaterEqual(contrast_ratio(muted[0], paper_deep[0]), 4.5)
        self.assertGreaterEqual(contrast_ratio(muted[1], paper[1]), 4.5)

    def test_primary_text_meets_aaa(self):
        ink = color_values(self.css, "ink")
        paper = color_values(self.css, "paper")
        self.assertGreaterEqual(contrast_ratio(ink[0], paper[0]), 7)


class InteractionStyleTests(SimpleTestCase):
    def test_focus_visible_and_reduced_motion_rules_exist(self):
        css = MAIN_CSS_PATH.read_text(encoding="utf-8")
        self.assertIn(":focus-visible", css)
        self.assertIn("prefers-reduced-motion: reduce", css)

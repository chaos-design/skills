"""Text measurement, wrapping and escaping helpers.

Diagram geometry is computed in Python, so the renderer needs a cheap and
deterministic way to know how wide a piece of text will be once it reaches the
browser. No font metrics are available here, so widths are estimated from
character classes. The estimate only has to be good enough to keep labels from
colliding or being clipped.
"""
from __future__ import annotations

import re
import unicodedata
from html import escape

# Narrow glyphs that keep punctuation from inflating a box.
_NARROW = set("ijltfrI.,:;'!|()[]{}-`·…")
_WIDE_BREAK = ("W", "F")

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def char_em(ch: str) -> float:
    """Approximate advance width of one character, in em."""
    if ch == "\t":
        return 2.0
    if ch == " ":
        return 0.3
    if unicodedata.east_asian_width(ch) in _WIDE_BREAK:
        return 1.0
    if ch in _NARROW:
        return 0.32
    if ch.isdigit():
        return 0.56
    if ch.isupper():
        return 0.67
    if ch.islower():
        return 0.53
    return 0.55


def text_em(text: str) -> float:
    """Approximate advance width of a string, in em."""
    return sum(char_em(ch) for ch in text)


# The browser renders these fonts slightly wider than a character-class
# estimate predicts. Padding every measurement by this factor keeps a label
# inside its box instead of trusting an exact-looking number.
FIT = 1.1


def text_px(text: str, size: float) -> float:
    """Approximate advance width of a string, in pixels."""
    return text_em(text) * size * FIT


def is_wide(ch: str) -> bool:
    return unicodedata.east_asian_width(ch) in _WIDE_BREAK


def wrap_text(text: str, size: float, max_px: float) -> list[str]:
    """Greedy wrap that understands CJK text and keeps latin words intact."""
    text = text.strip()
    if not text:
        return [""]
    lines: list[str] = []
    current = ""
    current_px = 0.0
    pending = ""

    def flush_word() -> None:
        nonlocal current, current_px, pending
        if not pending:
            return
        word_px = text_px(pending, size)
        if current and current_px + word_px > max_px:
            lines.append(current.rstrip())
            current = ""
            current_px = 0.0
        if word_px > max_px and not current:
            # A single word longer than the box: break it by characters.
            for ch in pending:
                ch_px = text_px(ch, size)
                if current_px + ch_px > max_px and current:
                    lines.append(current)
                    current = ""
                    current_px = 0.0
                current += ch
                current_px += ch_px
            pending = ""
            return
        current += pending
        current_px += word_px
        pending = ""

    for ch in text:
        if is_wide(ch):
            flush_word()
            ch_px = text_px(ch, size)
            if current_px + ch_px > max_px and current:
                lines.append(current.rstrip())
                current = ""
                current_px = 0.0
            current += ch
            current_px += ch_px
            pending = ""
        elif ch == " ":
            flush_word()
            if current:
                current += " "
                current_px += text_px(" ", size)
        else:
            pending += ch
    flush_word()
    if current.strip():
        lines.append(current.rstrip())
    return lines or [""]


def esc(text: str) -> str:
    """Escape text for HTML body content."""
    return escape(str(text), quote=False)


def esc_attr(text: str) -> str:
    """Escape text for a double-quoted HTML attribute."""
    return escape(str(text), quote=True)


def slugify(text: str) -> str:
    """Lowercase, hyphen-separated slug. Keeps CJK out of file names."""
    base = unicodedata.normalize("NFKD", str(text))
    ascii_only = base.encode("ascii", "ignore").decode("ascii")
    slug = _SLUG_RE.sub("-", ascii_only.lower()).strip("-")
    return slug or "brief"


_FENCE_BLOCK_RE = re.compile(r"^\s*(`{3,}|~{3,}).*?^\s*\1\s*$", re.S | re.M)
_INLINE_CODE_RE = re.compile(r"`[^`]*`")
_LATIN_RE = re.compile(r"[A-Za-z]")
CJK_RATIO = 0.12


def detect_lang(text: str) -> str:
    """Guess the document language from the prose, not from stray characters.

    Fenced and inline code are ignored, and the script needs a real share of
    the letters. An English page that mentions one Chinese term, or a Chinese
    page full of English product names, keeps the language a reader expects.
    """
    body = _INLINE_CODE_RE.sub(" ", _FENCE_BLOCK_RE.sub(" ", text))
    kana = sum(1 for ch in body if "\u3040" <= ch <= "\u30ff")
    cjk = sum(1 for ch in body if "\u4e00" <= ch <= "\u9fff")
    latin = len(_LATIN_RE.findall(body))
    if not (cjk + latin):
        return "en"
    if kana and kana * 4 >= cjk and kana / (kana + cjk + latin) >= CJK_RATIO / 3:
        return "ja"
    if cjk / (cjk + latin) >= CJK_RATIO:
        return "zh"
    return "en"


HTML_LANG = {"zh": "zh-CN", "ja": "ja", "en": "en"}

UI_TEXT = {
    "en": {
        "theme": "Theme",
        "mode": "Mode",
        "copy": "Copy source",
        "copied": "Copied",
        "copy_failed": "Copy failed",
        "light": "Light",
        "dark": "Dark",
        "auto": "Auto",
        "diagram": "Diagram",
    },
    "zh": {
        "theme": "主题",
        "mode": "明暗",
        "copy": "复制源文",
        "copied": "已复制",
        "copy_failed": "复制失败",
        "light": "亮色",
        "dark": "深色",
        "auto": "自动",
        "diagram": "图示",
    },
    "ja": {
        "theme": "テーマ",
        "mode": "表示",
        "copy": "原稿をコピー",
        "copied": "コピーしました",
        "copy_failed": "コピーに失敗しました",
        "light": "ライト",
        "dark": "ダーク",
        "auto": "自動",
        "diagram": "図",
    },
}

LOCALE = {"lang": "en"}

DIAGRAM_WORDS = {
    "en": {
        "flow": "flow diagram",
        "sequence": "sequence diagram",
        "tree": "tree diagram",
        "timeline": "timeline diagram",
    },
    "zh": {"flow": "流程图", "sequence": "时序图", "tree": "目录树", "timeline": "时间线"},
    "ja": {"flow": "フローチャート", "sequence": "シーケンス図", "tree": "ツリー", "timeline": "タイムライン"},
}


def set_locale(lang: str) -> None:
    """Remember the page language for every localized label."""
    LOCALE["lang"] = lang if lang in UI_TEXT else "en"


def diagram_word(kind: str) -> str:
    return DIAGRAM_WORDS[LOCALE["lang"]][kind]

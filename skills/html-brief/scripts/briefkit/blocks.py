"""HTML-rendered blocks: prose, tables, callouts and data components."""
from __future__ import annotations

import re

from . import diagrams
from .parser import (
    CalloutBlock,
    CodeBlock,
    ComponentBlock,
    DraftError,
    Heading,
    ListBlock,
    Paragraph,
    QuoteBlock,
    TableBlock,
    strip_emphasis,
)
from .textutil import esc, esc_attr
from .textutil import set_locale as set_page_locale

_CODE_SPAN_RE = re.compile(r"`([^`]+)`")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*|__(.+?)__", re.S)
_ITALIC_RE = re.compile(r"(?<![\w*])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![\w*])")
_STRIKE_RE = re.compile(r"~~(.+?)~~", re.S)
_BARE_URL_RE = re.compile(r"(?<![\"'>=(])((?:https?://)[^\s<>()]+[^\s<>().,;])")

_SAFE_URL = re.compile(r"^(https?:|mailto:|/|\./|\#)")

OK_WORDS = {"ok", "yes", "y", "true", "✓", "✔", "支持", "有", "可以", "适合"}
NO_WORDS = {"no", "n", "false", "✗", "✘", "×", "不支持", "无", "不适合"}
WARN_WORDS = {"warn", "!", "~", "部分", "有限", "谨慎"}

CALLOUT_LABELS = {
    "en": {"note": "Note", "tip": "Tip", "warn": "Warning", "danger": "Risk", "key": "Key point"},
    "zh": {"note": "注记", "tip": "建议", "warn": "警告", "danger": "风险", "key": "关键结论"},
    "ja": {"note": "メモ", "tip": "提案", "warn": "警告", "danger": "リスク", "key": "要点"},
}

ANNOT_LABELS = {
    "en": {"bad": "Problem", "warn": "Risk", "good": "Good", "fix": "Fix"},
    "zh": {"bad": "问题", "warn": "风险", "good": "优点", "fix": "改法"},
    "ja": {"bad": "問題", "warn": "リスク", "good": "良い点", "fix": "修正"},
}

LOCALE = {"lang": "en"}


def set_locale(lang: str) -> None:
    """Pick the labels used by callouts and annotations."""
    LOCALE["lang"] = lang if lang in CALLOUT_LABELS else "en"
    set_page_locale(lang)

DIAGRAM_BUILDERS = {
    "flow": diagrams.render_flow,
    "sequence": diagrams.render_sequence,
    "tree": diagrams.render_tree,
    "timeline": diagrams.render_timeline,
}


# --------------------------------------------------------------------------- #
# inline markdown
# --------------------------------------------------------------------------- #
def inline(text: str) -> str:
    """Render inline Markdown into HTML.

    The text is escaped once, up front, and every substitution below works on
    that escaped string without escaping a second time. Escaping inside a
    substitution double-encodes anything that already holds an entity, which is
    how a query string like `?a=1&b=2` used to come out as `&amp;amp;`.
    """
    fragments: list[str] = []
    while True:
        match = _CODE_SPAN_RE.search(text)
        if not match:
            break
        fragments.append(f"<code>{esc(match.group(1))}</code>")
        text = f"{text[: match.start()]}{len(fragments) - 1}{text[match.end() :]}"

    out = esc(text)

    def link_sub(match: re.Match[str]) -> str:
        label, href = match.group(1), match.group(2)
        if _SAFE_URL.match(href):
            return f'<a href="{href}">{label}</a>'
        return label

    out = _LINK_RE.sub(link_sub, out)
    out = _BOLD_RE.sub(lambda m: f"<strong>{m.group(1) or m.group(2)}</strong>", out)
    out = _ITALIC_RE.sub(lambda m: f"<em>{m.group(1)}</em>", out)
    out = _STRIKE_RE.sub(lambda m: f"<del>{m.group(1)}</del>", out)
    out = _BARE_URL_RE.sub(lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>', out)
    for index, fragment in enumerate(fragments):
        out = out.replace(f"{index}", fragment)
    return out


def plain(text: str) -> str:
    """Plain text without inline markup, for titles and labels."""
    return strip_emphasis(text)


# --------------------------------------------------------------------------- #
# prose blocks
# --------------------------------------------------------------------------- #
def render_heading(block: Heading) -> str:
    level = min(max(block.level, 3), 6)
    return f'<h{level} class="sub">{inline(block.text)}</h{level}>'


def render_paragraph(block: Paragraph) -> str:
    return f"<p>{inline(block.text)}</p>"


def render_list(block: ListBlock) -> str:
    tag = "ol" if block.ordered else "ul"
    items = "".join(f"<li>{inline(item)}</li>" for item in block.items)
    return f'<{tag} class="list">{items}</{tag}>'


def render_quote(block: QuoteBlock) -> str:
    paragraphs = "".join(f"<p>{inline(line)}</p>" for line in block.text.split("\n\n") if line.strip())
    return f'<blockquote class="quote">{paragraphs}</blockquote>'


def render_code(block: CodeBlock) -> str:
    label = f'<span class="code-lang">{esc(block.lang)}</span>' if block.lang and block.lang != "text" else ""
    return f'<pre class="code">{label}<code>{esc(block.text)}</code></pre>'


def render_callout(block: CalloutBlock) -> str:
    label = CALLOUT_LABELS[LOCALE["lang"]].get(block.kind, block.kind)
    heading = f'<strong class="callout-title">{inline(block.title)}</strong>' if block.title else ""
    body = f"<p>{inline(block.text)}</p>" if block.text else ""
    return (
        f'<aside class="callout callout-{esc_attr(block.kind)}">'
        f'<span class="callout-tag">{esc(label)}</span>'
        f'<div class="callout-body">{heading}{body}</div></aside>'
    )


def status_glyph(value: str) -> str:
    """Return the ✓ / ✗ / ! span for a status word, or an empty string."""
    token = value.strip().lower()
    if token in OK_WORDS:
        return '<span class="mark mark-ok">✓</span>'
    if token in NO_WORDS:
        return '<span class="mark mark-no">✗</span>'
    if token in WARN_WORDS:
        return '<span class="mark mark-warn">!</span>'
    return ""


def status_columns(block: TableBlock) -> set[int]:
    """Columns whose every cell is a status word.

    Deciding per column rather than per cell keeps a row label like `no` or
    `部分` from being swallowed by the glyph rule, which is how a first-column
    label used to disappear from the page.
    """
    columns: set[int] = set()
    for index in range(len(block.headers)):
        values = [row[index] for row in block.rows if index < len(row) and row[index].strip()]
        if values and all(status_glyph(value) for value in values):
            columns.add(index)
    return columns


def render_table(block: TableBlock) -> str:
    aligns = block.align or ["left"] * len(block.headers)
    glyphs = status_columns(block)
    head = "".join(
        f'<th style="text-align:{aligns[index] if index < len(aligns) else "left"}">'
        f"{inline(cell)}</th>"
        for index, cell in enumerate(block.headers)
    )
    rows: list[str] = []
    for row in block.rows:
        cells = "".join(
            f'<td style="text-align:{aligns[index] if index < len(aligns) else "left"}">'
            f"{status_glyph(cell) or inline(cell) if index in glyphs else inline(cell)}</td>"
            for index, cell in enumerate(row)
        )
        rows.append(f"<tr>{cells}</tr>")
    return (
        '<div class="table-wrap"><table class="table">'
        f"<thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
    )


# --------------------------------------------------------------------------- #
# data components
# --------------------------------------------------------------------------- #
def _rows(block: ComponentBlock, expected: int, shape: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for offset, raw in enumerate(block.text.split("\n"), start=1):
        if not raw.strip():
            continue
        cells = [cell.strip() for cell in raw.split("|")]
        if len(cells) < expected:
            raise DraftError(
                f"this component needs {expected} `|` separated fields",
                block.line + offset,
                block.name,
                shape,
            )
        rows.append(cells)
    if not rows:
        raise DraftError(f"{block.name} block is empty", block.line, block.name, shape)
    return rows


def render_limits(block: ComponentBlock) -> str:
    shape = "```limits\nContext window | 200k tokens | 85% | p99 of measured runs\n```"
    out: list[str] = []
    for offset, row in enumerate(_rows(block, 3, shape)):
        line_no = block.line + offset + 1
        name, value, percent = row[0], row[1], row[2].replace("%", "").strip()
        note = row[3] if len(row) > 3 else ""
        try:
            ratio = float(percent)
        except ValueError:
            raise DraftError(
                f"`{percent}` is not a number", line_no, "limits", shape
            ) from None
        if not 0 <= ratio <= 100:
            raise DraftError(
                f"percentage {ratio:g} is outside 0-100", line_no, "limits", shape
            )
        level = "ok" if ratio < 75 else "warn" if ratio < 90 else "bad"
        note_html = f'<span class="limit-note">{inline(note)}</span>' if note else ""
        out.append(
            f'<div class="limit"><div class="limit-head"><span class="limit-name">{inline(name)}</span>'
            f'<span class="limit-value">{inline(value)}</span></div>'
            f'<div class="limit-track"><span class="limit-fill limit-{level}" style="width:{ratio:g}%"></span></div>'
            f'<div class="limit-foot"><span class="limit-pct limit-{level}">{ratio:g}%</span>{note_html}</div></div>'
        )
    return f'<div class="limits">{"".join(out)}</div>'


def render_stat(block: ComponentBlock) -> str:
    shape = "```stat\nOutput tokens | 923 | -87% | good\n```"
    out: list[str] = []
    for row in _rows(block, 2, shape):
        name, value = row[0], row[1]
        delta = row[2] if len(row) > 2 else ""
        status = (row[3] if len(row) > 3 else "").lower()
        level = {"good": "ok", "ok": "ok", "bad": "no", "risk": "no", "warn": "warn"}.get(status, "")
        delta_class = f" stat-delta stat-{level}" if delta else ""
        delta_html = f'<span class="{delta_class.strip()}">{inline(delta)}</span>' if delta else ""
        out.append(
            f'<div class="stat"><span class="stat-name">{inline(name)}</span>'
            f'<span class="stat-value">{inline(value)}</span>{delta_html}</div>'
        )
    return f'<div class="stats">{"".join(out)}</div>'


def render_kv(block: ComponentBlock) -> str:
    shape = "```kv\nOwner | Platform team\nStatus | GA\n```"
    out: list[str] = []
    for row in _rows(block, 2, shape):
        key = row[0]
        value = " · ".join(row[1:])
        out.append(
            f'<div class="kv-row"><dt>{inline(key)}</dt><dd>{inline(value)}</dd></div>'
        )
    return f'<dl class="kv">{"".join(out)}</dl>'


_ANNOT_RE = re.compile(r"\{(?P<kind>bad|warn|good|fix)\|(?P<text>[^}]*?)(?:::(?P<note>[^}]*))?\}")
_ANNOT_CLASS = {
    "bad": "annot-bad",
    "warn": "annot-warn",
    "good": "annot-good",
    "fix": "annot-fix",
}


def render_annot(block: ComponentBlock) -> str:
    shape = "```annot\nThe {bad|service} retries {fix|with jittered backoff} on 5xx.\n```"
    source = block.text.strip()
    if not source:
        raise DraftError("annot block is empty", block.line, "annot", shape)
    notes: list[tuple[str, str]] = []
    counter = [0]

    def replace(match: re.Match[str]) -> str:
        counter[0] += 1
        kind = match.group("kind")
        # `source` is escaped before substitution, so the capture already
        # holds safe text. Escaping again here would show `&amp;lt;` to the
        # reader instead of `<`.
        text = match.group("text").strip()
        note = (match.group("note") or "").strip()
        css = _ANNOT_CLASS[kind]
        if note:
            notes.append((str(counter[0]), inline(note)))
        return (
            f'<span class="annot {css}" data-note="{counter[0]}">{text}'
            f'<sup class="annot-mark">{counter[0]}</sup></span>'
        )

    # Escape first, then let the marker substitution add its own markup. The
    # other order leaves the unmarked part of the sentence as raw draft text,
    # which is a script injection into the finished page.
    sentence = _ANNOT_RE.sub(replace, esc(source))
    legend = ""
    if notes:
        items = "".join(f'<li><span>{index}</span>{inline(note)}</li>' for index, note in notes)
        legend = f'<ol class="annot-legend">{items}</ol>'
    return f'<div class="annot-block"><p class="annot-sentence">{sentence}</p>{legend}</div>'


DATA_COMPONENTS = {
    "limits": render_limits,
    "stat": render_stat,
    "kv": render_kv,
    "annot": render_annot,
}


def render_component(block: ComponentBlock, title: str) -> str:
    if block.name in DIAGRAM_BUILDERS:
        return DIAGRAM_BUILDERS[block.name](block.text, block.args, block.line, title)
    builder = DATA_COMPONENTS[block.name]
    return builder(block)


BLOCK_RENDERERS = {
    Heading: render_heading,
    Paragraph: render_paragraph,
    ListBlock: render_list,
    TableBlock: render_table,
    CodeBlock: render_code,
    QuoteBlock: render_quote,
    CalloutBlock: render_callout,
}


def render_blocks(blocks: list[object], title: str) -> str:
    out: list[str] = []
    for block in blocks:
        if isinstance(block, ComponentBlock):
            out.append(render_component(block, title))
            continue
        renderer = BLOCK_RENDERERS.get(type(block))
        if renderer:
            out.append(renderer(block))
    return "".join(out)

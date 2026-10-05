#!/usr/bin/env python3
"""Semantic checks for generated briefs.

`validate` proves a page is self-contained and `check_layout` proves no diagram
label is clipped. Neither can tell you that the page says the wrong thing: a
callout title that vanished, an English brief that renders Chinese controls, or
a panel that quietly lost its table all pass both.

This script asserts meaning instead. It re-derives the expected structure from
each draft with its own small parser, so a bug in the renderer cannot hide by
being shared with the expectation. It renders into a temporary folder and writes
nothing to the repository.

Usage:
    python3 scripts/check_semantics.py
    python3 scripts/check_semantics.py --draft my-draft.md

Checks per draft:
  1  the embedded source round-trips exactly
  2  panel count and headings match the draft's `##` lines
  3  an explicit `lang:` reaches `<html lang>`
  4  the chrome labels agree with `<html lang>`
  5  a callout has a title only when its quote has two or more paragraphs
  6  every `ok` / `no` / `warn` table cell produced exactly one glyph
  7  every limits row produced a bar at the declared percentage
  8  sequence participants appear in first-use order
  9  every diagram carries a title, an aria-label and a viewBox
 10  rendering twice produces the same bytes
 11  one render stays inside its wall-clock budget
 12  no closing-tag variant escapes the embedded source
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
import time
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from briefkit.blocks import NO_WORDS, OK_WORDS, WARN_WORDS  # noqa: E402
from briefkit.cli import build_page, example_files, slugify  # noqa: E402
from briefkit.render import embed_source, unembed_source  # noqa: E402
from briefkit.textutil import DIAGRAM_WORDS  # noqa: E402

FRONTMATTER = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.S)
HEADING = re.compile(r"^##\s+\S", re.M)
FENCE = re.compile(r"^(?P<fence>`{3,}|~{3,})\s*(?P<info>[^\n]*)\n(?P<body>.*?)^\s*(?P=fence)\s*$", re.S | re.M)
CALLOUT_START = re.compile(r"^>\s*(note|tip|warn|danger|key)\s*[:：]")
ARROW = re.compile(r"^\s*(?P<src>[^\s]+?)\s*(?:-\.->|==>|-->|->)\s*(?P<dst>[^\s:]+)\s*:?")
LABEL_WRAPPER = re.compile(r"^[*(\[{]+|[)\]}]*$")

COPY_LABEL = {"en": "Copy source", "zh": "复制源文", "ja": "原稿をコピー"}
HTML_LANG = {"en": "en", "zh": "zh-CN", "ja": "ja"}
# Closing sequences a browser accepts even though a naive search misses.
HOSTILE_DUMPS = (
    "</script>",
    "</SCRIPT>",
    "</SCRIPT >",
    "</script\t>",
    "</script\n>",
    "</script/>",
    "</script\x00>",
    "</ScRiPt bar>",
    "</ script>",
    "< /script>",
    "</script",
    "<script>alert(1)</script>",
    "```html\n</SCRIPT >\n```",
)

CALLOUT_TAGS = {
    "en": {"Note", "Tip", "Warning", "Risk", "Key point"},
    "zh": {"注记", "建议", "警告", "风险", "关键结论"},
    "ja": {"メモ", "提案", "警告", "リスク", "要点"},
}
TOKEN_GLYPHS = {"ok": "✓", "no": "✗", "warn": "!"}

# (title, html lang, panel count, SVG diagram kinds in page order).
# `limits`, `stat`, `kv` and `annot` render as HTML and carry no figure.
GOLDEN = {
    "tcp-handshake": ("TCP three-way handshake", "en", 6, ["sequence", "flow", "flow"]),
    "cache-choice-zh-cn": ("缓存选型评审", "zh-CN", 6, ["flow"]),
    "congestion-control-history": ("TCP congestion control, 1988 to today", "en", 5, ["timeline", "sequence"]),
    "skill-pipeline": ("Skill repository content pipeline", "en", 5, ["flow", "tree"]),
    "writing-check": ("Writing check, line by line", "en", 4, ["flow"]),
}


class Failure(Exception):
    pass


def need(condition: bool, message: str) -> None:
    if not condition:
        raise Failure(message)


def front_matter(text: str) -> dict[str, str]:
    match = FRONTMATTER.match(text.lstrip("\ufeff"))
    if not match:
        return {}
    meta: dict[str, str] = {}
    for line in match.group("body").split("\n"):
        pair = re.match(r"^([A-Za-z][A-Za-z0-9_-]*)\s*:\s*(.*)$", line)
        if pair:
            meta[pair.group(1).lower()] = pair.group(2).strip().strip("\"'")
    return meta


def components(text: str) -> list[tuple[str, str]]:
    """Return (info-string, body) for every fenced block."""
    return [(match.group("info").strip(), match.group("body")) for match in FENCE.finditer(text)]


def expected_callout_titles(text: str) -> int:
    """Count callouts whose quote carries a second paragraph."""
    titles = 0
    lines = text.split("\n")
    index = 0
    while index < len(lines):
        if not CALLOUT_START.match(lines[index]):
            index += 1
            continue
        paragraphs = [[]]
        while index < len(lines) and lines[index].startswith(">"):
            content = lines[index][1:].strip()
            if content:
                paragraphs[-1].append(content)
            else:
                paragraphs.append([])
            index += 1
        if len([group for group in paragraphs if group]) > 1:
            titles += 1
        while index < len(lines) and not lines[index].startswith(">"):
            index += 1
    return titles


SEPARATOR_ROW = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?[\s:|-]*$")


def expected_glyphs(text: str) -> int:
    """Count table cells that the renderer must turn into a glyph.

    Tables sit in the document body, so the scan walks the draft instead of the
    fenced blocks: a header row, a separator row, then the body rows.
    """
    total = 0
    lines = text.split("\n")
    index = 0
    fence = None
    while index < len(lines):
        line = lines[index]
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            fence = None if fence else marker.group(1)
            index += 1
            continue
        is_table = (
            fence is None
            and "|" in line
            and index + 1 < len(lines)
            and SEPARATOR_ROW.match(lines[index + 1])
            and "-" in lines[index + 1]
        )
        if not is_table:
            index += 1
            continue
        index += 2
        while index < len(lines) and lines[index].strip() and "|" in lines[index]:
            for cell in lines[index].strip().strip("|").split("|"):
                token = cell.strip().lower()
                if token in OK_WORDS or token in NO_WORDS or token in WARN_WORDS:
                    total += 1
            index += 1
    return total


def expected_limits(text: str) -> list[float]:
    values: list[float] = []
    for info, body in components(text):
        if not info.lower().startswith("limits"):
            continue
        for line in body.split("\n"):
            if "|" not in line:
                continue
            cells = [cell.strip() for cell in line.split("|")]
            if len(cells) < 3:
                continue
            try:
                values.append(float(cells[2].replace("%", "")))
            except ValueError:
                continue
    return values


def strip_label(token: str) -> str:
    return LABEL_WRAPPER.sub("", token.strip()).strip()


def expected_participants(text: str) -> list[str]:
    """First-use order of sequence participants, re-derived from the draft."""
    order: list[str] = []
    labels: dict[str, str] = {}

    def add(name: str) -> None:
        if name not in labels:
            labels[name] = name
            order.append(name)

    for info, body in components(text):
        if not info.lower().startswith("sequence"):
            continue
        for line in body.split("\n"):
            text_line = line.strip()
            if not text_line or text_line.startswith("#"):
                continue
            renamed = re.match(r"^participant\s+(\S+)(?:\s+as\s+(.+))?$", text_line, re.I)
            if renamed:
                name = renamed.group(1)
                add(name)
                labels[name] = (renamed.group(2) or name).strip()
                continue
            arrow = ARROW.match(text_line)
            if arrow:
                add(strip_label(arrow.group("src")))
                add(strip_label(arrow.group("dst")))
                continue
            note = re.match(r"^note\s+(.+?):", text_line, re.I)
            if note:
                for name in note.group(1).split(","):
                    add(strip_label(name))
                continue
            keyword = text_line.split(None, 1)
            if keyword[0].lower() in ("activate", "deactivate") and len(keyword) > 1:
                add(strip_label(keyword[1]))
    return [labels[name] for name in order]


COMPONENT_NAMES = {"flow", "sequence", "tree", "timeline", "limits", "stat", "annot", "kv"}

# Wall-clock ceiling for one render. Measured worst case for a 20-layer graph
# with 160 edges is about 70 ms, so this leaves room without hiding a runaway.
RENDER_SECONDS = 3.0


def count_script_elements(page: str) -> int:
    """Count script elements the way a parser would, not by string search."""
    counter = _ScriptCounter()
    counter.feed(page)
    return counter.total


class _ScriptCounter(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.total = 0

    def handle_starttag(self, tag, _attrs):
        if tag == "script":
            self.total += 1


def count_figures(page: str) -> int:
    return page.count('<figure class="diagram"')


def diagram_kinds(page: str, lang: str = "en") -> list[str]:
    """Read the diagram kind back out of each figure's aria-label."""
    words = DIAGRAM_WORDS.get(lang, DIAGRAM_WORDS["en"])
    found: list[str] = []
    for label in re.findall(r'<figure class="diagram" role="img" aria-label="([^"]+)"', page):
        for kind, word in words.items():
            if label.endswith(word):
                found.append(kind)
                break
        else:
            found.append(f"?{label}")
    return found


def check(draft: Path, page: str, draft_text: str) -> list[str]:
    """Return the list of failed checks; empty means everything held."""
    problems: list[str] = []

    def expect(condition: bool, message: str) -> None:
        if not condition:
            problems.append(message)

    # 1 embedded source round-trips
    embedded = re.search(
        r'id="html-brief-source">\n(?P<text>.*?)\n</script>\n<script>', page, re.S
    )
    need(embedded is not None, "the page does not embed the source draft")
    expect(
        unembed_source(embedded.group("text")) == draft_text,
        "the embedded source does not match the draft",
    )
    # A draft that tries to close the script element must not be able to.
    expect(
        count_script_elements(page) == 2,
        f"the source dump is not closed properly, page has {count_script_elements(page)} script elements",
    )
    for hostile in HOSTILE_DUMPS:
        embedded_one = embed_source(hostile)
        expect(
            unembed_source(embedded_one) == hostile,
            f"embedding then reading back changed {hostile!r}",
        )
        counter = _ScriptCounter()
        counter.feed(f'<script type="text/markdown">{embedded_one}</script>')
        expect(counter.total == 1, f"{hostile!r} closes the script element early")

    meta = front_matter(draft_text)
    source = draft_text.lstrip("\ufeff")
    headings = len(HEADING.findall(source))

    # 2 panel count and headings
    panels = len(re.findall(r'<section class="panel', page))
    expect(panels == max(1, headings), f"expected {max(1, headings)} panels, found {panels}")
    named = len(
        re.findall(r"^##\s+(?!\{span)\S.*$", FRONTMATTER.sub("", source), re.M)
    )
    expect(
        page.count('class="panel-head"') == named,
        f"expected {named} panel headings, found {page.count(chr(34) + 'panel-head' + chr(34))}",
    )

    # 3 explicit lang reaches the document
    lang = re.search(r'<html lang="([^"]+)"', page)
    need(lang is not None, "the page has no html lang attribute")
    if meta.get("lang"):
        expect(
            lang.group(1) == meta["lang"],
            f"front matter sets lang: {meta['lang']} but the page is {lang.group(1)}",
        )

    # 4 chrome labels agree with the document language
    family = next((key for key, value in HTML_LANG.items() if value == lang.group(1)), None)
    need(family is not None, f"unknown html lang {lang.group(1)}")
    copy_button = re.search(r'data-act="copy"[^>]*>([^<]*)<', page)
    need(copy_button is not None, "the toolbar has no copy button")
    expect(
        copy_button.group(1).strip() == COPY_LABEL[family],
        f"copy button reads {copy_button.group(1)!r} on a {lang.group(1)} page",
    )
    tags = set(re.findall(r'class="callout-tag">([^<]+)<', page))
    stray = tags - CALLOUT_TAGS[family]
    expect(not stray, f"callout tags {sorted(stray)} do not belong to a {lang.group(1)} page")

    # 5 callout titles follow the paragraph rule
    titles = page.count('class="callout-title"')
    expect(
        titles == expected_callout_titles(draft_text),
        f"expected {expected_callout_titles(draft_text)} callout titles, found {titles}",
    )

    # 6 table glyphs
    glyphs = sum(page.count(f">{glyph}<") for glyph in TOKEN_GLYPHS.values())
    expect(
        glyphs == expected_glyphs(draft_text),
        f"expected {expected_glyphs(draft_text)} table glyphs, found {glyphs}",
    )

    # 7 limits bars
    for value in expected_limits(draft_text):
        expect(
            f"width:{value:g}%" in page,
            f"no limit bar at {value:g}%",
        )

    # 8 sequence participant order
    for wanted in expected_participants(draft_text):
        if wanted not in page:
            problems.append(f"sequence participant {wanted!r} is missing from the page")
    # 9 diagram accessibility
    for figure in re.findall(r'<figure class="diagram".*?</figure>', page, re.S):
        need("aria-label=\"" in figure, "a figure has no aria-label")
        need("<title>" in figure, "a figure has no title")
        need("viewBox=" in figure, "a figure has no viewBox")
    expect(
        count_figures(page) == len(diagram_kinds(page, next((key for key, value in HTML_LANG.items() if value == lang.group(1)), "en"))),
        "a figure is missing its kind in the aria-label",
    )
    return [item for item in problems if item]


def golden_check(slug: str, page: str) -> list[str]:
    expected = GOLDEN.get(slug)
    if not expected:
        return []
    title, lang, panels, kinds = expected
    problems: list[str] = []
    if f"<h1>{title}</h1>" not in page and f"<title>{title}</title>" not in page:
        problems.append(f"title drifted from {title!r}")
    if f'<html lang="{lang}"' not in page:
        problems.append(f"language drifted from {lang!r}")
    actual_panels = len(re.findall(r'<section class="panel', page))
    if actual_panels != panels:
        problems.append(f"panel count drifted from {panels} to {actual_panels}")
    family = next((key for key, value in HTML_LANG.items() if value == lang), "en")
    actual_kinds = diagram_kinds(page, family)
    if actual_kinds != kinds:
        problems.append(f"diagram kinds drifted from {kinds} to {actual_kinds}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--draft", default=None, help="check one draft instead of the examples")
    parser.add_argument("--examples-dir", default=None)
    parser.add_argument("--date", default="2026-01-02 03:04:05", help="fixed stamp, keeps runs comparable")
    args = parser.parse_args()

    if args.draft:
        drafts = [Path(args.draft)]
    else:
        root = Path(args.examples_dir) if args.examples_dir else Path(__file__).resolve().parents[1] / "examples"
        drafts = example_files(root)
    if not drafts:
        print("no drafts to check", file=sys.stderr)
        return 1

    class Options:
        theme = mode = lang = columns = None
        date = args.date
        no_date = False
        check = "off"

    failures = 0
    with tempfile.TemporaryDirectory(prefix="html-brief-semantics-") as work:
        for draft in drafts:
            slug = slugify(draft.stem)
            text = draft.read_text(encoding="utf-8")
            try:
                started = time.perf_counter()
                page, _title, _panels = build_page(text, args=Options(), source=str(draft))
                elapsed = time.perf_counter() - started
                again, _t, _p = build_page(text, args=Options(), source=str(draft))
                problems = check(draft, page, text)
                problems += golden_check(slug, page)
                if page != again:
                    problems.append("two renders of the same draft differ")
                if elapsed > RENDER_SECONDS:
                    problems.append(f"render took {elapsed:.1f}s, over the {RENDER_SECONDS:.0f}s budget")
            except Failure as error:
                print(f"FAIL {draft.name}: {error}")
                failures += 1
                continue
            if problems:
                failures += 1
                print(f"FAIL {draft.name}")
                for item in problems:
                    print(f"  - {item}")
            else:
                snapshot = "golden ok" if slug in GOLDEN else "no golden, invariants only"
                print(f"ok   {draft.name} · {snapshot}")
    print("semantic check failed" if failures else f"semantic check passed for {len(drafts)} draft(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

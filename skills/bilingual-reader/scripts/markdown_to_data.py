#!/usr/bin/env python3
"""Convert normalized article Markdown into bilingual-reader template data.

The module intentionally keeps extraction deterministic. Translation,
summarization, and glossary enrichment are injected as callables so callers can
use the Agent/LLM layer after the full source article has been parsed.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import html
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Optional


DEV_MARKER_RE = re.compile(r"\b(?:DOC|TPL|DOM)\d+\b")
PLACEHOLDER_RE = re.compile(r"__(?:[A-Z][A-Z0-9_]*|DATA_JSON|THEME_JSON)__")
SOURCE_RE = re.compile(r"^>\s*Source:\s*(\S+)\s*$", re.IGNORECASE)
FETCHED_RE = re.compile(r"^>\s*Fetched:\s*(.+?)\s*$", re.IGNORECASE)
FETCHED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
PUBLISHED_RE = re.compile(r"^(?:Published|Date|发布时间)[:：]?\s+(.+?)\s*$", re.IGNORECASE)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
IMAGE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)\s*$")
FENCE_RE = re.compile(r"^```([A-Za-z0-9_+.-]*)\s*$")
LIST_ITEM_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.+?)\s*$")
BLOCKQUOTE_RE = re.compile(r"^\s*>\s?(.*)$")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
LINK_RE = re.compile(r"^\[([^\]]+)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)$")
IMAGE_TOKEN_RE = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)$")
INLINE_TOKEN_RE = re.compile(
    r"(`[^`\n]+`|!\[[^\]]*\]\([^)]+\)|\[[^\]]+\]\([^)]+\)|"
    r"\*\*[^*\n]+(?:\*[^*\n]+)*\*\*|__[^_\n]+(?:_[^_\n]+)*__|"
    r"\*[^*\n]+\*|_[^_\n]+_)"
)
GLOSSARY_KEY_RE = re.compile(r"[^a-z0-9]+")
CHINESE_TEXT_RE = re.compile(r"[\u3400-\u9fff]")
CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
SOURCE_URL_RE = re.compile(r"^https?://[^\s\"'<>]+$", re.IGNORECASE)
MAX_MARKDOWN_CHARS = 2_000_000
MAX_TABLE_ROWS = 200
MAX_TABLE_COLUMNS = 20
MAX_TABLE_CELL_CHARS = 2_000
MAX_CODE_BLOCK_CHARS = 200_000
ORIGINAL_ROW_TARGET_CHARS = 420
ORIGINAL_ROW_MIN_CHARS = 140
IRREGULAR_INFLECTIONS = {
    "be": ("am", "are", "is", "was", "were", "been", "being"),
    "do": ("does", "did", "done", "doing"),
    "go": ("goes", "went", "gone", "going"),
    "have": ("has", "had", "having"),
}
POS_ALIASES = {
    "noun": "n",
    "nouns": "n",
    "verb": "v",
    "verbs": "v",
    "adjective": "adj",
    "adjectives": "adj",
    "adverb": "adv",
    "adverbs": "adv",
    "preposition": "prep",
    "prepositions": "prep",
    "conjunction": "conj",
    "conjunctions": "conj",
    "pronoun": "pron",
    "pronouns": "pron",
    "determiner": "det",
    "determiners": "det",
    "interjection": "interj",
    "interjections": "interj",
}
POS_ABBREVIATIONS = (
    "adj",
    "adv",
    "conj",
    "det",
    "interj",
    "n",
    "num",
    "phr",
    "prep",
    "pron",
    "v",
)

BOILERPLATE_PHRASES = (
    "introduction what is an agent? when should you build an agent? agent design foundations guardrails conclusion",
    "try chatgpt",
    "contact sales",
    "opens in a new window",
    "subscribe",
    "cookie",
)


@dataclass
class Metadata:
    """Article metadata extracted from normalized Markdown."""

    title: str
    source_url: str
    fetched_at: str = ""
    published_at: str = ""


@dataclass
class Block:
    """A normalized source block in original reading order."""

    type: str
    text: str = ""
    html: str = ""
    markdown: str = ""
    level: int = 0
    language: str = ""
    code: str = ""
    src: str = ""
    alt: str = ""
    caption: str = ""
    rows: list[list[str]] = field(default_factory=list)
    html_rows: list[list[str]] = field(default_factory=list)
    markdown_rows: list[list[str]] = field(default_factory=list)


@dataclass
class Article:
    """Parsed article with metadata and ordered content blocks."""

    metadata: Metadata
    blocks: list[Block]


GlossaryBuilder = Callable[[Article], list[dict[str, str]]]
SummaryBuilder = Callable[[Article], dict[str, object]]
Translator = Callable[[str], str]


class ConversionError(ValueError):
    """Raised when source Markdown cannot produce reliable reader data."""


def clean_text(value: str) -> str:
    """Normalize inline whitespace without changing source wording."""

    return re.sub(r"\s+", " ", value).strip()


def display_pos(word: str, pos: str) -> str:
    """Return only a concise grammatical part-of-speech abbreviation."""

    if re.search(r"[\s-]", clean_text(word)):
        return ""
    normalized = clean_text(pos).casefold().replace(".", "")
    if not normalized:
        return ""
    tokens = [token for token in re.split(r"[^a-z]+", normalized) if token]
    for token in tokens:
        if token in POS_ALIASES:
            return POS_ALIASES[token]
        if token in POS_ABBREVIATIONS:
            return token
    return ""


def strip_inline_markdown(value: str) -> str:
    """Convert lightweight inline Markdown to readable plain text."""

    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", value)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*`]+", "", text)
    return clean_text(text)


def parse_markdown(markdown: str) -> Article:
    """Parse web-markdown output into article blocks."""

    validate_raw_markdown(markdown)
    lines = markdown.splitlines()
    metadata = extract_metadata(lines)
    blocks = parse_blocks(lines)
    blocks = remove_metadata_blocks(metadata, blocks)
    article = Article(metadata=metadata, blocks=blocks)
    validate_article(article)
    return article


def validate_raw_markdown(markdown: str) -> None:
    """Reject inputs that cannot be safely parsed into reader data."""

    if not isinstance(markdown, str):
        raise ConversionError("Markdown input must be text.")
    if not markdown.strip():
        raise ConversionError("Markdown input is empty.")
    if len(markdown) > MAX_MARKDOWN_CHARS:
        raise ConversionError(f"Markdown input is too large: {len(markdown)} characters.")
    if CONTROL_CHAR_RE.search(markdown):
        raise ConversionError("Markdown input contains unsupported control characters.")


def extract_metadata(lines: list[str]) -> Metadata:
    """Extract title, source URL, and fetch timestamp."""

    title = ""
    source_url = ""
    fetched_at = ""
    published_at = ""
    h1_count = 0
    for line in lines:
        match = HEADING_RE.match(line)
        if match and len(match.group(1)) == 1:
            h1_count += 1
            if not title:
                title = strip_inline_markdown(match.group(2))
        source_match = SOURCE_RE.match(line)
        fetched_match = FETCHED_RE.match(line)
        if source_match:
            source_url = source_match.group(1)
        if fetched_match:
            fetched_at = fetched_match.group(1)
        if not published_at:
            published_match = PUBLISHED_RE.match(line.strip())
            if published_match:
                published_at = clean_text(published_match.group(1))
    if not title:
        raise ConversionError("Markdown title is missing.")
    if not source_url:
        raise ConversionError("Source URL metadata is missing.")
    validate_metadata(source_url, fetched_at)
    return Metadata(title=title, source_url=source_url, fetched_at=fetched_at, published_at=published_at)


def validate_metadata(source_url: str, fetched_at: str) -> None:
    """Validate source metadata before article parsing continues."""

    if not SOURCE_URL_RE.fullmatch(source_url):
        raise ConversionError("Source URL metadata must be an http(s) URL.")
    if not fetched_at:
        raise ConversionError("Fetched timestamp metadata is missing.")
    if not FETCHED_AT_RE.fullmatch(fetched_at):
        raise ConversionError("Fetched timestamp must use YYYY-MM-DD HH:mm:ss.")
    try:
        datetime.strptime(fetched_at, "%Y-%m-%d %H:%M:%S")
    except ValueError as exc:
        raise ConversionError("Fetched timestamp is not a valid calendar time.") from exc


def parse_blocks(lines: list[str]) -> list[Block]:
    """Parse block-level Markdown while preserving reading order."""

    blocks: list[Block] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if SOURCE_RE.match(line) or FETCHED_RE.match(line) or is_published_line(line):
            index += 1
            continue
        next_index = parse_next_block(lines, index, blocks)
        index = next_index if next_index > index else index + 1
    return blocks


def parse_next_block(lines: list[str], index: int, blocks: list[Block]) -> int:
    """Parse one Markdown block starting at index."""

    line = lines[index]
    fence = FENCE_RE.match(line)
    if fence:
        return parse_code_block(lines, index, fence.group(1), blocks)
    heading = HEADING_RE.match(line)
    if heading:
        blocks.append(
            Block(
                type="heading",
                level=len(heading.group(1)),
                text=strip_inline_markdown(heading.group(2)),
                html=render_inline_markdown(heading.group(2)),
            )
        )
        return index + 1
    image = IMAGE_RE.match(line)
    if image:
        validate_image_src(image.group(2))
        blocks.append(Block(type="image", alt=clean_text(image.group(1)), src=image.group(2), caption=clean_text(image.group(3) or "")))
        return index + 1
    if looks_like_table(lines, index):
        return parse_table_block(lines, index, blocks)
    if LIST_ITEM_RE.match(line):
        return parse_list_block(lines, index, blocks)
    if BLOCKQUOTE_RE.match(line):
        return parse_blockquote(lines, index, blocks)
    return parse_paragraph(lines, index, blocks)


def parse_code_block(lines: list[str], index: int, language: str, blocks: list[Block]) -> int:
    """Parse a fenced code block without modifying its body."""

    code_lines: list[str] = []
    cursor = index + 1
    while cursor < len(lines) and not lines[cursor].startswith("```"):
        code_lines.append(lines[cursor])
        cursor += 1
    if cursor >= len(lines):
        raise ConversionError("Unclosed fenced code block.")
    code = "\n".join(code_lines)
    if len(code) > MAX_CODE_BLOCK_CHARS:
        raise ConversionError("Code block is too large for stable rendering.")
    blocks.append(Block(type="code", language=language, code=code))
    return cursor + 1


def looks_like_table(lines: list[str], index: int) -> bool:
    """Return true when the current line starts a Markdown table."""

    return index + 1 < len(lines) and "|" in lines[index] and bool(TABLE_SEPARATOR_RE.match(lines[index + 1]))


def parse_table_block(lines: list[str], index: int, blocks: list[Block]) -> int:
    """Parse a consecutive Markdown table into row cells."""

    table_lines: list[str] = []
    cursor = index
    while cursor < len(lines) and "|" in lines[cursor] and lines[cursor].strip():
        if not TABLE_SEPARATOR_RE.match(lines[cursor]):
            table_lines.append(lines[cursor])
        cursor += 1
    rows = [parse_table_row(line) for line in table_lines]
    html_rows = [parse_table_html_row(line) for line in table_lines]
    markdown_rows = [parse_table_markdown_row(line) for line in table_lines]
    rows = [row for row in rows if row]
    html_rows = [row for row in html_rows if row]
    markdown_rows = [row for row in markdown_rows if row]
    validate_table_rows(rows)
    blocks.append(Block(type="table", rows=rows, html_rows=html_rows, markdown_rows=markdown_rows))
    return cursor


def parse_table_row(line: str) -> list[str]:
    """Parse one Markdown table row."""

    value = line.strip().strip("|")
    return [strip_inline_markdown(cell) for cell in value.split("|")]


def parse_table_html_row(line: str) -> list[str]:
    """Parse one Markdown table row into safe inline HTML cells."""

    value = line.strip().strip("|")
    return [render_inline_markdown(cell.strip()) for cell in value.split("|")]


def parse_table_markdown_row(line: str) -> list[str]:
    """Parse one Markdown table row while preserving inline Markdown markers."""

    value = line.strip().strip("|")
    return [cell.strip() for cell in value.split("|")]


def validate_table_rows(rows: list[list[str]]) -> None:
    """Validate Markdown table shape before rendering."""

    if not rows:
        raise ConversionError("Markdown table is empty.")
    if len(rows) > MAX_TABLE_ROWS:
        raise ConversionError("Markdown table has too many rows.")
    width = len(rows[0])
    if width == 0 or width > MAX_TABLE_COLUMNS:
        raise ConversionError("Markdown table has an unsupported column count.")
    for row in rows:
        if len(row) != width:
            raise ConversionError("Markdown table rows must have a consistent column count.")
        if any(len(cell) > MAX_TABLE_CELL_CHARS for cell in row):
            raise ConversionError("Markdown table cell is too long for stable rendering.")


def validate_image_src(src: str) -> None:
    """Validate image references accepted by the original-source view."""

    if not src.strip():
        raise ConversionError("Markdown image source is empty.")
    if src.startswith("data:image/"):
        if ";base64," not in src or len(src) > 3_000_000:
            raise ConversionError("Markdown image data URI is invalid or too large.")
        return
    if not src.startswith(("http://", "https://")):
        raise ConversionError("Markdown image source must be http(s) or data:image.")


def parse_paragraph(lines: list[str], index: int, blocks: list[Block]) -> int:
    """Parse a paragraph into prose and safe HTML."""

    parts: list[str] = []
    raw_parts: list[str] = []
    cursor = index
    while cursor < len(lines) and can_continue_paragraph(lines[cursor]):
        parts.append(clean_markdown_line(lines[cursor]))
        raw_parts.append(lines[cursor].strip())
        cursor += 1
    text = strip_inline_markdown(" ".join(part for part in parts if part))
    if text and not is_boilerplate(text):
        raw = " ".join(part for part in raw_parts if part)
        blocks.append(Block(type="paragraph", text=text, html=f"<p>{render_inline_markdown(raw)}</p>", markdown=raw))
    return cursor


def parse_list_block(lines: list[str], index: int, blocks: list[Block]) -> int:
    """Parse a consecutive Markdown list into one source block."""

    items: list[str] = []
    ordered = False
    cursor = index
    while cursor < len(lines):
        match = LIST_ITEM_RE.match(lines[cursor])
        if not match:
            break
        marker = match.group(2)
        if not items:
            ordered = bool(re.match(r"\d+[.)]", marker))
        elif ordered != bool(re.match(r"\d+[.)]", marker)):
            break
        items.append(match.group(3))
        cursor += 1
    text = clean_text(" ".join(strip_inline_markdown(item) for item in items))
    if text and not is_boilerplate(text):
        tag = "ol" if ordered else "ul"
        item_html = "".join(f"<li>{render_inline_markdown(item)}</li>" for item in items)
        blocks.append(Block(type="paragraph", text=text, html=f"<{tag}>{item_html}</{tag}>", markdown="\n".join(items)))
    return cursor


def parse_blockquote(lines: list[str], index: int, blocks: list[Block]) -> int:
    """Parse a consecutive Markdown blockquote into one source block."""

    quote_lines: list[str] = []
    cursor = index
    while cursor < len(lines):
        match = BLOCKQUOTE_RE.match(lines[cursor])
        if not match:
            break
        quote_lines.append(match.group(1))
        cursor += 1
    raw = " ".join(line.strip() for line in quote_lines if line.strip())
    text = strip_inline_markdown(raw)
    if text and not SOURCE_RE.match(f"> {raw}") and not FETCHED_RE.match(f"> {raw}") and not is_boilerplate(text):
        blocks.append(Block(type="paragraph", text=text, html=f"<blockquote>{render_inline_markdown(raw)}</blockquote>", markdown=raw))
    return cursor


def can_continue_paragraph(line: str) -> bool:
    """Check whether a line belongs to the current prose block."""

    if not line.strip():
        return False
    if is_published_line(line):
        return False
    return not (
        HEADING_RE.match(line)
        or FENCE_RE.match(line)
        or IMAGE_RE.match(line)
        or LIST_ITEM_RE.match(line)
        or BLOCKQUOTE_RE.match(line)
    )


def render_inline_markdown(value: str) -> str:
    """Render supported inline Markdown into safe HTML."""

    text = str(value or "")
    output: list[str] = []
    cursor = 0
    for match in INLINE_TOKEN_RE.finditer(text):
        output.append(html.escape(text[cursor:match.start()]))
        output.append(render_inline_token(match.group(0)))
        cursor = match.end()
    output.append(html.escape(text[cursor:]))
    return "".join(output)


def render_inline_token(token: str) -> str:
    """Render one inline Markdown token."""

    if token.startswith("`") and token.endswith("`"):
        return f"<code>{html.escape(token[1:-1])}</code>"
    if token.startswith("!["):
        return render_inline_image(token)
    if token.startswith("["):
        return render_inline_link(token)
    if token.startswith(("**", "__")) and token.endswith(("**", "__")):
        return f"<strong>{render_inline_markdown(token[2:-2])}</strong>"
    if token.startswith(("*", "_")) and token.endswith(("*", "_")):
        return f"<em>{render_inline_markdown(token[1:-1])}</em>"
    return html.escape(token)


def render_inline_link(token: str) -> str:
    """Render one Markdown link with safe attributes."""

    match = LINK_RE.match(token)
    if not match:
        return html.escape(token)
    label, href, title = match.groups()
    if not is_safe_link_href(href):
        return render_inline_markdown(label)
    title_attr = f' title="{html.escape(title, quote=True)}"' if title else ""
    return (
        f'<a href="{html.escape(href, quote=True)}" target="_blank" '
        f'rel="noopener"{title_attr}>{render_inline_markdown(label)}</a>'
    )


def render_inline_image(token: str) -> str:
    """Render one inline Markdown image with safe attributes."""

    match = IMAGE_TOKEN_RE.match(token)
    if not match:
        return html.escape(token)
    alt, src, title = match.groups()
    try:
        validate_image_src(src)
    except ConversionError:
        return html.escape(alt)
    title_attr = f' title="{html.escape(title, quote=True)}"' if title else ""
    return (
        f'<img src="{html.escape(src, quote=True)}" alt="{html.escape(alt, quote=True)}"'
        f'{title_attr} loading="lazy" decoding="async">'
    )


def is_safe_link_href(href: str) -> bool:
    """Allow normal document links while rejecting script-like protocols."""

    value = href.strip()
    if not value:
        return False
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", value):
        return value.startswith(("http://", "https://", "mailto:"))
    return True


def clean_markdown_line(line: str) -> str:
    """Remove list and quote markers from prose lines."""

    value = re.sub(r"^\s*>\s?", "", line)
    value = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", value)
    return value.strip()


def is_published_line(line: str) -> bool:
    """Return true for source publication-date lines kept as metadata."""

    return bool(PUBLISHED_RE.match(line.strip()))


def is_boilerplate(text: str) -> bool:
    """Filter common navigation and marketing fragments."""

    lowered = text.lower()
    if any(phrase in lowered for phrase in BOILERPLATE_PHRASES):
        return True
    return lowered in BOILERPLATE_PHRASES


def remove_metadata_blocks(metadata: Metadata, blocks: list[Block]) -> list[Block]:
    """Remove duplicate title headings emitted by web-markdown."""

    cleaned: list[Block] = []
    for block in blocks:
        if block.type == "heading" and block.level == 1 and clean_text(block.text).casefold() == metadata.title.casefold():
            continue
        cleaned.append(block)
    return cleaned


def validate_article(article: Article, min_paragraphs: int = 3, min_text_length: int = 400) -> None:
    """Validate that the parsed result is a complete source article."""

    visible = "\n".join(iter_visible_text(article))
    all_text = "\n".join(iter_all_text(article))
    paragraph_count = sum(1 for block in article.blocks if block.type == "paragraph")
    if article.metadata.title.casefold() == "bilingual-reader":
        raise ConversionError("Article title resolved to the skill name instead of the source title.")
    if DEV_MARKER_RE.search(all_text):
        raise ConversionError("Article contains user-visible development markers.")
    if PLACEHOLDER_RE.search(visible):
        raise ConversionError("Article contains unresolved template placeholders.")
    if paragraph_count < min_paragraphs or len(visible) < min_text_length:
        raise ConversionError("Parsed article content is too short; fetch or extraction is likely incomplete.")


def iter_visible_text(article: Article) -> Iterable[str]:
    """Yield user-visible source text, excluding raw code."""

    yield article.metadata.title
    for block in article.blocks:
        if block.type in {"heading", "paragraph"}:
            yield block.text
        elif block.type == "table":
            yield " ".join(cell for row in block.rows for cell in row)
        elif block.type == "image":
            yield " ".join(part for part in (block.alt, block.caption) if part)


def iter_all_text(article: Article) -> Iterable[str]:
    """Yield all source text that would be visible in the final reader."""

    yield from iter_visible_text(article)
    for block in article.blocks:
        if block.type == "code":
            yield block.code


def build_learning_data(
    article: Article,
    translate: Translator,
    summarize: Optional[SummaryBuilder] = None,
    build_glossary: Optional[GlossaryBuilder] = None,
) -> dict[str, object]:
    """Build the template data contract from parsed article data."""

    summary = build_summary(article, translate, summarize)
    glossary_entries = build_glossary(article) if build_glossary else []
    sections = build_sections(article, translate)
    data = {
        "metadata": {
            "title": article.metadata.title,
            "sourceUrl": article.metadata.source_url,
            "fetchedAt": article.metadata.fetched_at,
            "publishedAt": article.metadata.published_at,
        },
        "article": build_article_context(article),
        "hero": build_hero(article, translate),
        "summary": summary,
        "framework": build_logic_framework(article),
        "sections": sections,
        "quiz": build_comprehension_quiz(sections),
        "original": build_original(article, translate),
        "glossary": build_glossary_contract(glossary_entries),
        "footer": {
            "sourceUrl": article.metadata.source_url,
            "sourceText": article.metadata.title,
        },
    }
    validate_learning_data(data)
    return data


def build_article_context(article: Article) -> dict[str, object]:
    """Build source-grounded tags and anchors for the original view."""

    sections = split_top_level_sections(article, include_media=True)
    anchors = [
        {"id": f"og-{index}", "label": str(section["title"])}
        for index, section in enumerate(sections, 1)
    ]
    return {
        "title": article.metadata.title,
        "sourceUrl": article.metadata.source_url,
        "fetchedAt": article.metadata.fetched_at,
        "publishedAt": article.metadata.published_at,
        "tags": infer_article_tags(article),
        "anchors": anchors,
    }


def infer_article_tags(article: Article, limit: int = 6) -> list[str]:
    """Infer compact tags only from visible article wording."""

    visible = " ".join(iter_visible_text(article)).lower()
    candidates = [
        ("AI", ("ai", "artificial intelligence", "llm", "agent")),
        ("Agent", ("agent", "agents")),
        ("工程实践", ("build", "design", "workflow", "tool")),
        ("安全护栏", ("guardrail", "safety", "risk")),
        ("评估", ("evaluation", "evaluate", "test")),
        ("产品策略", ("product", "business", "user")),
        ("系统设计", ("architecture", "orchestration", "system")),
        ("学习材料", ("guide", "course", "learn")),
    ]
    tags = [label for label, words in candidates if any(word in visible for word in words)]
    if not tags:
        tags = [block.text for block in article.blocks if block.type == "heading"][:3]
    return tags[:limit]


def build_summary(article: Article, translate: Translator, summarize: Optional[SummaryBuilder]) -> dict[str, object]:
    """Build a complete summary, using injected LLM output when valid."""

    fallback = default_summary(article, translate)
    if not summarize:
        return fallback
    try:
        candidate = summarize(article)
    except Exception:
        return fallback
    return normalize_summary(candidate, fallback)


def normalize_summary(candidate: dict[str, object], fallback: dict[str, object]) -> dict[str, object]:
    """Merge a custom summary with the deterministic schema fallback."""

    if not isinstance(candidate, dict):
        return fallback
    cards = normalize_summary_cards(candidate.get("cards"))
    if not cards:
        cards = list(fallback.get("cards", []))
    key_points = normalize_key_points(candidate.get("keyPoints"))
    if not key_points:
        key_points = list(fallback.get("keyPoints", []))
    reading_path = normalize_text_list(candidate.get("readingPath"))
    if not reading_path:
        reading_path = list(fallback.get("readingPath", []))
    lead = clean_text(str(candidate.get("lead", ""))) or str(fallback.get("lead", ""))
    thesis = clean_text(str(candidate.get("thesis", ""))) or str(fallback.get("thesis", lead))
    return {
        "overviewTitle": clean_text(str(candidate.get("overviewTitle", "")))
        or str(fallback.get("overviewTitle", "全文速览")),
        "thesis": thesis,
        "lead": lead,
        "keyPoints": key_points,
        "cards": cards,
        "readingPath": reading_path,
    }


def normalize_summary_cards(value: object) -> list[dict[str, str]]:
    """Normalize summary cards from custom summary output."""

    if not isinstance(value, list):
        return []
    cards = []
    for item in value:
        if not isinstance(item, dict):
            continue
        title = clean_text(str(item.get("title", "")))
        body = clean_text(str(item.get("body", "")))
        if not title or not body:
            continue
        cards.append({"icon": str(item.get("icon", "")), "title": title, "body": body})
    return cards


def normalize_key_points(value: object) -> list[dict[str, str]]:
    """Normalize headline-level takeaways."""

    if not isinstance(value, list):
        return []
    points = []
    for index, item in enumerate(value, 1):
        if isinstance(item, dict):
            text = clean_text(str(item.get("text", "")))
            label = clean_text(str(item.get("label", ""))) or f"要点 {index}"
        else:
            text = clean_text(str(item))
            label = f"要点 {index}"
        if text:
            points.append({"label": label, "text": text})
    return points


def normalize_text_list(value: object) -> list[str]:
    """Normalize a list of short text entries."""

    if not isinstance(value, list):
        return []
    return [text for item in value if (text := clean_text(str(item)))]


def build_glossary_contract(entries: list[dict[str, str]]) -> dict[str, object]:
    """Build the complete glossary shape consumed by templates and runtime."""

    dictionary: dict[str, dict[str, str]] = {}
    autowrap = []
    used_keys: set[str] = set()
    for entry in entries:
        word = clean_text(str(entry.get("word", "")))
        if not word:
            continue
        key = glossary_key(word, used_keys)
        dictionary[key] = {
            "w": word,
            "ipa": str(entry.get("ipa", "")),
            "pos": display_pos(word, str(entry.get("pos", ""))),
            "level": str(entry.get("level") or "术语"),
            "def": str(entry.get("definitionZh", "")),
            "eg": str(entry.get("collocationExample", "")),
            "egzh": str(entry.get("exampleZh", "")),
        }
        autowrap.append([autowrap_pattern(word, str(entry.get("pos", ""))), "i", key])
    return {"entries": entries, "dict": dictionary, "autowrap": autowrap}


def glossary_key(word: str, used_keys: set[str]) -> str:
    """Create a stable data-k key for one glossary entry."""

    base = GLOSSARY_KEY_RE.sub("_", word.casefold()).strip("_") or "term"
    key = base
    suffix = 2
    while key in used_keys:
        key = f"{base}_{suffix}"
        suffix += 1
    used_keys.add(key)
    return key


def autowrap_pattern(word: str, pos: str = "") -> str:
    """Create a whole-word regex source for runtime autowrap."""

    if re.fullmatch(r"[A-Za-z]+", word):
        variants = inflected_word_forms(word, pos)
        escaped_variants = sorted((re.escape(item) for item in variants), key=len, reverse=True)
        return rf"\b(?:{'|'.join(escaped_variants)})\b"
    escaped = re.escape(word)
    if re.match(r"^[A-Za-z0-9]", word) and re.search(r"[A-Za-z0-9]$", word):
        return rf"\b{escaped}\b"
    return escaped


def inflected_word_forms(word: str, pos: str = "") -> set[str]:
    """Return common inflected forms for one English glossary word."""

    lowered = word.casefold()
    normalized_pos = pos.casefold()
    forms = {word}
    irregular = IRREGULAR_INFLECTIONS.get(lowered)
    if irregular:
        forms.update(irregular)
        return forms
    if len(lowered) <= 2:
        return forms
    is_adjective_or_adverb = "adj" in normalized_pos or "adv" in normalized_pos
    is_verb = not normalized_pos.strip() or bool(re.search(r"(^|[/,;\s])v(?:\.|/|$)", normalized_pos))
    if not is_verb and is_adjective_or_adverb:
        return forms
    if lowered.endswith("y") and len(lowered) > 1 and lowered[-2] not in "aeiou":
        forms.add(f"{word[:-1]}ies")
        if is_verb:
            forms.update({f"{word[:-1]}ied", f"{word[:-1]}ying"})
    elif lowered.endswith(("s", "x", "z", "ch", "sh")):
        forms.add(f"{word}es")
        if is_verb:
            forms.update({f"{word}ed", f"{word}ing"})
    elif lowered.endswith("e") and not lowered.endswith(("ee", "ye", "oe")):
        forms.add(f"{word}s")
        if is_verb:
            forms.update({f"{word}d", f"{word[:-1]}ing"})
    else:
        forms.add(f"{word}s")
        if is_verb:
            forms.update({f"{word}ed", f"{word}ing"})
    return forms


def build_hero(article: Article, translate: Translator) -> dict[str, str]:
    """Build hero metadata from the article title and first paragraph."""

    first = first_paragraph(article)
    return {
        "title": article.metadata.title,
        "meta": article.metadata.source_url,
        "en": first,
        "zh": translate(first),
    }


def default_summary(article: Article, translate: Translator) -> dict[str, object]:
    """Create a source-grounded full-article summary seed."""

    sections = split_sections(article)
    lead_en = first_paragraph(article)
    thesis = (
        f"本文围绕《{article.metadata.title}》展开，核心结论是："
        f"{translate(lead_en)}"
    )
    cards = build_summary_cards(sections, translate)
    key_points = build_key_points(cards)
    reading_path = build_reading_path(sections)
    return {
        "overviewTitle": "全文速览",
        "thesis": thesis,
        "lead": thesis,
        "keyPoints": key_points,
        "cards": cards,
        "readingPath": reading_path,
    }


def build_summary_cards(sections: list[dict[str, object]], translate: Translator) -> list[dict[str, str]]:
    """Build four to six section-grounded summary cards when possible."""

    icons = ["🧭", "⚖️", "🧩", "🔧", "🤖", "🎯"]
    cards = []
    for index, section in enumerate(sections[:6]):
        opening = first_text_block(section["blocks"])
        if not opening:
            continue
        cards.append(
            {
                "icon": icons[len(cards) % len(icons)],
                "title": str(section["title"]),
                "body": summarize_opening(opening, translate),
            }
        )
    return cards


def summarize_opening(text: str, translate: Translator) -> str:
    """Turn a section opening into a concise Chinese summary card."""

    translated = translate(text)
    first_sentence = re.split(r"(?<=[。！？.!?])\s*", translated, maxsplit=1)[0]
    return clean_text(first_sentence or translated)


def build_key_points(cards: list[dict[str, str]]) -> list[dict[str, str]]:
    """Promote the first summary cards into headline-level takeaways."""

    labels = ("核心判断", "关键边界", "实践路径")
    points = []
    for label, card in zip(labels, cards):
        points.append({"label": label, "text": card["body"]})
    return points


def build_reading_path(sections: list[dict[str, object]]) -> list[str]:
    """Create a compact reading path from the article section order."""

    titles = [str(section["title"]) for section in sections[:6] if str(section["title"]).strip()]
    if not titles:
        return ["先理解全文主张", "再进入逐段对照", "最后回到词汇与测验巩固"]
    if len(titles) == 1:
        return [f"先抓住“{titles[0]}”的主张", "再进入逐段对照", "最后回到词汇与测验巩固"]
    return [f"{index}. {title}" for index, title in enumerate(titles, 1)]


def build_sections(article: Article, translate: Translator) -> list[dict[str, object]]:
    """Build prose-only bilingual sections for the summary view."""

    output: list[dict[str, object]] = []
    for index, section in enumerate(split_sections(article), start=1):
        rows = []
        for block in section["blocks"]:
            text = prose_text(block)
            if text:
                rows.append({"en": text, "zh": translate(text)})
        if rows:
            output.append({"num": str(index), "toc": section["title"], "title": section["title"], "rows": rows})
    return output


def build_logic_framework(article: Article, limit: int = 6) -> dict[str, object]:
    """Build a stable source-order framework for visual close reading."""

    sections = split_sections(article)
    nodes = []
    for index, section in enumerate(sections[:limit], 1):
        opening = first_text_block(section["blocks"])
        if not opening:
            continue
        nodes.append(
            {
                "id": f"fw-{index}",
                "label": str(section["title"]),
                "summary": summarize_framework_node(opening),
            }
        )
    edges = [
        {"from": nodes[index - 1]["id"], "to": nodes[index]["id"]}
        for index in range(1, len(nodes))
    ]
    return {"title": "文章逻辑框架", "nodes": nodes, "edges": edges}


def summarize_framework_node(text: str, max_length: int = 92) -> str:
    """Create a short framework label without inventing new claims."""

    value = clean_text(text)
    if len(value) <= max_length:
        return value
    return value[: max_length - 1].rstrip() + "…"


def build_comprehension_quiz(
    sections: list[dict[str, object]],
    max_questions: int = 4,
) -> list[dict[str, object]]:
    """Build source-grounded comprehension questions from section rows."""

    usable = [section for section in sections if section.get("rows")]
    questions = []
    for index, section in enumerate(usable[:max_questions]):
        rows = list(section.get("rows", []))
        correct = clean_text(str(rows[0]["zh"]))
        if not correct:
            continue
        distractors = quiz_distractors(usable, index)
        options = [correct, *distractors[:3]]
        answer = index % len(options)
        options[0], options[answer] = options[answer], options[0]
        questions.append(
            {
                "question": f"关于“{section['title']}”，哪一项最符合原文？",
                "options": options,
                "answer": answer,
                "explain": f"依据原文段落：{clean_text(str(rows[0]['en']))}",
                "wrongReason": "该选项没有对应本节原文，或混淆了其他章节的观点。",
                "sourceAnchor": str(section.get("toc") or section["title"]),
            }
        )
    return questions


def quiz_distractors(sections: list[dict[str, object]], current_index: int) -> list[str]:
    """Select wrong options from other real sections, not fabricated claims."""

    distractors = []
    for index, section in enumerate(sections):
        if index == current_index or not section.get("rows"):
            continue
        candidate = clean_text(str(section["rows"][0]["zh"]))
        if candidate and candidate not in distractors:
            distractors.append(candidate)
    fallback = [
        "无法从该节原文判断此说法成立。",
        "该说法与本节核心段落没有直接对应关系。",
    ]
    for candidate in fallback:
        if len(distractors) >= 2:
            break
        distractors.append(candidate)
    return distractors


def build_original(article: Article, translate: Translator) -> dict[str, object]:
    """Build original-view groups preserving media and tables in order."""

    groups = []
    for index, section in enumerate(split_top_level_sections(article, include_media=True), 1):
        rows = original_rows(section["blocks"], translate)
        groups.append({"id": f"og-{index}", "group": section["title"], "rows": rows})
    return {"title": f"{original_display_title(article)} · 原文全文对照", "meta": article.metadata.source_url, "groups": groups}


def original_display_title(article: Article) -> str:
    """Return original-view title text, optionally annotated with publication date."""

    published = clean_text(article.metadata.published_at)
    if not published:
        return article.metadata.title
    return f"{article.metadata.title} · {published}"


def original_rows(blocks: list[Block], translate: Translator) -> list[dict[str, object]]:
    """Merge consecutive source paragraphs before translating original-view rows."""

    rows: list[dict[str, object]] = []
    pending_blocks: list[Block] = []

    def flush_paragraphs() -> None:
        if not pending_blocks:
            return
        rows.extend(chunk_original_blocks(pending_blocks, translate))
        pending_blocks.clear()

    for block in blocks:
        if block.type == "paragraph":
            pending_blocks.append(block)
            continue
        flush_paragraphs()
        row = original_row(block, translate)
        if row:
            rows.append(row)
    flush_paragraphs()
    return rows


def chunk_original_blocks(blocks: list[Block], translate: Translator) -> list[dict[str, object]]:
    """Split long original prose into readable comparison rows."""

    rows: list[dict[str, object]] = []
    current: list[Block] = []
    current_size = 0
    for block in blocks:
        pieces = split_original_block(block)
        for piece in pieces:
            size = len(clean_text(piece.text))
            if current and current_size + size > ORIGINAL_ROW_TARGET_CHARS:
                rows.append(original_bilingual_row(current, translate))
                current = []
                current_size = 0
            current.append(piece)
            current_size += size
            if size >= ORIGINAL_ROW_TARGET_CHARS:
                rows.append(original_bilingual_row(current, translate))
                current = []
                current_size = 0
    if current:
        rows.append(original_bilingual_row(current, translate))
    return rows


def split_original_block(block: Block) -> list[Block]:
    """Split one long paragraph block without changing media/table/code blocks."""

    if not is_plain_paragraph_block(block) or len(clean_text(block.text)) <= ORIGINAL_ROW_TARGET_CHARS:
        return [block]
    markdown_parts = split_markdown_prose(block.markdown or block.text)
    if len(markdown_parts) <= 1:
        return [block]
    pieces = []
    for part in markdown_parts:
        text = strip_inline_markdown(part)
        if not text:
            continue
        pieces.append(
            Block(
                type="paragraph",
                text=text,
                html=f"<p>{render_inline_markdown(part)}</p>",
                markdown=part,
            )
        )
    return pieces or [block]


def is_plain_paragraph_block(block: Block) -> bool:
    """Return true when a paragraph can be safely split as prose."""

    html_value = block.html.lstrip()
    return block.type == "paragraph" and html_value.startswith("<p>")


def original_bilingual_row(blocks: list[Block], translate: Translator) -> dict[str, object]:
    """Build one original-view bilingual row from one or more prose blocks."""

    paragraphs = [block.text for block in blocks]
    source_text = "\n\n".join(paragraphs)
    source_html = "\n".join(block.html or f"<p>{render_inline_markdown(block.text)}</p>" for block in blocks)
    return {
        "type": "bilingual",
        "en": source_text,
        "html": source_html,
        "zh": translate_original_group(source_text, paragraphs, translate),
        "zhHtml": translate_original_blocks(blocks, translate),
    }


def translate_original_blocks(blocks: list[Block], translate: Translator) -> str:
    """Translate source prose blocks while preserving their block styles."""

    return "\n".join(render_translated_block(block, translate) for block in blocks)


def render_translated_block(block: Block, translate: Translator) -> str:
    """Render one translated block with safe structural HTML."""

    try:
        markdown = block.markdown or block.text
        html_value = block.html.lstrip()
        if html_value.startswith("<blockquote"):
            return f"<blockquote>{render_translated_inline_markdown(markdown, translate)}</blockquote>"
        if html_value.startswith("<ul") or html_value.startswith("<ol"):
            tag = "ol" if html_value.startswith("<ol") else "ul"
            items = [item for item in markdown.splitlines() if clean_text(item)]
            translated_items = "".join(
                f"<li>{render_translated_inline_markdown(item, translate)}</li>"
                for item in items
            )
            return f"<{tag}>{translated_items}</{tag}>"
        return f"<p>{render_translated_inline_markdown(markdown, translate)}</p>"
    except ConversionError:
        return f"<p>{html.escape(translate(block.text))}</p>"


def render_translated_inline_markdown(value: str, translate: Translator) -> str:
    """Translate inline Markdown text while preserving supported inline styles."""

    text = str(value or "")
    if not INLINE_TOKEN_RE.search(text):
        return html.escape(translate(strip_inline_markdown(text)))
    output: list[str] = []
    cursor = 0
    for match in INLINE_TOKEN_RE.finditer(text):
        output.append(render_translated_text_segment(text[cursor:match.start()], translate))
        output.append(render_translated_inline_token(match.group(0), translate))
        cursor = match.end()
    output.append(render_translated_text_segment(text[cursor:], translate))
    return "".join(output)


def render_translated_text_segment(value: str, translate: Translator) -> str:
    """Translate a plain inline text segment."""

    text = clean_text(value)
    if text and not re.search(r"[A-Za-z0-9]", text):
        return html.escape(value)
    return html.escape(translate(text)) if text else html.escape(value)


def render_translated_inline_token(token: str, translate: Translator) -> str:
    """Translate one inline Markdown token without changing its style tag."""

    if token.startswith("`") and token.endswith("`"):
        return f"<code>{html.escape(token[1:-1])}</code>"
    if token.startswith("!["):
        return render_inline_image(token)
    if token.startswith("["):
        return render_translated_inline_link(token, translate)
    if token.startswith(("**", "__")) and token.endswith(("**", "__")):
        return f"<strong>{render_translated_inline_markdown(token[2:-2], translate)}</strong>"
    if token.startswith(("*", "_")) and token.endswith(("*", "_")):
        return f"<em>{render_translated_inline_markdown(token[1:-1], translate)}</em>"
    return html.escape(token)


def render_translated_inline_link(token: str, translate: Translator) -> str:
    """Translate a Markdown link label while preserving the href."""

    match = LINK_RE.match(token)
    if not match:
        return html.escape(token)
    label, href, title = match.groups()
    if not is_safe_link_href(href):
        return render_translated_inline_markdown(label, translate)
    title_attr = f' title="{html.escape(title, quote=True)}"' if title else ""
    return (
        f'<a href="{html.escape(href, quote=True)}" target="_blank" '
        f'rel="noopener"{title_attr}>{render_translated_inline_markdown(label, translate)}</a>'
    )


def translated_html_to_text(value: str) -> str:
    """Return readable Chinese text from generated translated HTML."""

    text = re.sub(r"<[^>]+>", " ", value)
    return clean_text(html.unescape(text))


def split_markdown_prose(markdown_text: str) -> list[str]:
    """Split Markdown prose at sentence and clause boundaries."""

    text = clean_text(markdown_text)
    if len(text) <= ORIGINAL_ROW_TARGET_CHARS:
        return [text]
    segments = prose_segments(text)
    chunks: list[str] = []
    current = ""
    for segment in segments:
        candidate = clean_text(f"{current} {segment}" if current else segment)
        if current and len(candidate) > ORIGINAL_ROW_TARGET_CHARS:
            chunks.append(current)
            current = segment
        else:
            current = candidate
    if current:
        chunks.append(current)
    return [chunk for item in chunks for chunk in split_oversized_segment(item)]


def prose_segments(text: str) -> list[str]:
    """Return sentence-like Markdown segments without splitting inline links/code."""

    boundaries = prose_boundaries(text)
    segments: list[str] = []
    start = 0
    for boundary in boundaries:
        segment = clean_text(text[start:boundary])
        if segment:
            segments.append(segment)
        start = boundary
    tail = clean_text(text[start:])
    if tail:
        segments.append(tail)
    return segments or [text]


def prose_boundaries(text: str) -> list[int]:
    """Find natural split positions outside inline Markdown tokens."""

    boundaries: list[int] = []
    bracket_depth = 0
    paren_depth = 0
    in_code = False
    for index, char in enumerate(text):
        if char == "`":
            in_code = not in_code
            continue
        if in_code:
            continue
        if char == "[":
            bracket_depth += 1
        elif char == "]" and bracket_depth:
            bracket_depth -= 1
        elif char == "(":
            paren_depth += 1
        elif char == ")" and paren_depth:
            paren_depth -= 1
        if bracket_depth or paren_depth:
            continue
        next_char = text[index + 1] if index + 1 < len(text) else ""
        previous = boundaries[-1] if boundaries else 0
        distance = index - previous
        primary = char in ".!?" and (not next_char or next_char.isspace())
        secondary = char in ";:，,、—–" and distance >= ORIGINAL_ROW_MIN_CHARS
        if primary or secondary:
            boundaries.append(index + 1)
    return boundaries


def split_oversized_segment(text: str) -> list[str]:
    """Split very long single sentences at safe whitespace when possible."""

    if len(text) <= ORIGINAL_ROW_TARGET_CHARS:
        return [text]
    chunks: list[str] = []
    rest = text
    while len(rest) > ORIGINAL_ROW_TARGET_CHARS:
        split_at = rest.rfind(" ", ORIGINAL_ROW_MIN_CHARS, ORIGINAL_ROW_TARGET_CHARS)
        if split_at <= 0:
            break
        chunks.append(rest[:split_at].strip())
        rest = rest[split_at:].strip()
    if rest:
        chunks.append(rest)
    return chunks or [text]


def translate_original_group(source_text: str, paragraphs: list[str], translate: Translator) -> str:
    """Translate one merged original paragraph, with deterministic fallback for previews."""

    try:
        translated = translate(source_text)
    except ConversionError:
        if len(paragraphs) <= 1:
            raise
        return "\n\n".join(translate(paragraph) for paragraph in paragraphs)
    if CHINESE_TEXT_RE.search(translated) or len(paragraphs) <= 1:
        return translated
    return "\n\n".join(translate(paragraph) for paragraph in paragraphs)


def original_row(block: Block, translate: Translator) -> dict[str, object]:
    """Convert a source block to an original-view row."""

    if block.type == "paragraph":
        zh_html = render_translated_block(block, translate)
        return {
            "type": "bilingual",
            "en": block.text,
            "html": block.html or f"<p>{render_inline_markdown(block.text)}</p>",
            "zh": translate(block.text),
            "zhHtml": zh_html,
        }
    if block.type == "heading":
        level = min(max(block.level, 3), 6)
        return {
            "type": "heading",
            "text": block.text,
            "level": level,
            "html": f"<h{level}>{block.html or render_inline_markdown(block.text)}</h{level}>",
        }
    if block.type == "table":
        return {
            "type": "table",
            "rows": block.rows,
            "htmlRows": block.html_rows,
            "zhRows": translate_table_rows(block.rows, translate),
            "zhHtmlRows": translate_table_html_rows(block.markdown_rows or block.rows, translate),
        }
    if block.type == "image":
        return {"type": "image", "src": block.src, "alt": block.alt, "caption": block.caption}
    if block.type == "code":
        return {"type": "code", "language": block.language, "code": block.code}
    return {}


def translate_table_rows(rows: list[object], translate: Translator) -> list[list[str]]:
    """Translate each table cell while preserving the source table shape."""

    translated = []
    for row in rows:
        if not isinstance(row, list):
            continue
        translated.append([translate(str(cell)) for cell in row])
    return translated


def translate_table_html_rows(rows: list[object], translate: Translator) -> list[list[str]]:
    """Translate each table cell while preserving inline Markdown styling."""

    translated = []
    for row in rows:
        if not isinstance(row, list):
            continue
        translated.append([render_translated_inline_markdown(str(cell), translate) for cell in row])
    return translated


def split_top_level_sections(article: Article, include_media: bool = False) -> list[dict[str, object]]:
    """Group original-view content under Markdown level-two headings."""

    sections: list[dict[str, object]] = []
    current = {"title": original_display_title(article), "blocks": []}
    for block in article.blocks:
        if block.type == "heading":
            if block.level == 2:
                if current["blocks"]:
                    sections.append(current)
                current = {"title": block.text, "blocks": []}
            elif include_media and block.level > 2:
                current["blocks"].append(block)
            continue
        if include_media or block.type == "paragraph":
            current["blocks"].append(block)
    if current["blocks"]:
        sections.append(current)
    return sections


def split_sections(article: Article, include_media: bool = False) -> list[dict[str, object]]:
    """Group article blocks under headings while preserving source order."""

    sections: list[dict[str, object]] = []
    current = {"title": "Introduction", "blocks": []}
    for block in article.blocks:
        if block.type == "heading":
            if current["blocks"]:
                sections.append(current)
            current = {"title": block.text, "blocks": []}
            continue
        if include_media or block.type == "paragraph":
            current["blocks"].append(block)
    if current["blocks"]:
        sections.append(current)
    return sections


def prose_text(block: Block) -> str:
    """Return readable prose for paragraph blocks."""

    if block.type == "paragraph":
        return block.text
    return ""


def first_paragraph(article: Article) -> str:
    """Return the first prose paragraph."""

    for block in article.blocks:
        if block.type == "paragraph":
            return block.text
    raise ConversionError("Article has no prose paragraph.")


def first_text_block(blocks: list[Block]) -> str:
    """Return the first paragraph text from a section."""

    for block in blocks:
        text = prose_text(block)
        if text:
            return text
    return ""


def validate_learning_data(data: dict[str, object]) -> None:
    """Validate template data before rendering."""

    if not isinstance(data, dict):
        raise ConversionError("Template data must be an object.")
    required = ("metadata", "article", "hero", "summary", "framework", "sections", "quiz", "original", "glossary", "footer")
    missing = [key for key in required if key not in data]
    if missing:
        raise ConversionError(f"Template data is missing fields: {', '.join(missing)}.")
    validate_metadata_object(data.get("metadata", {}), "metadata")
    validate_metadata_object(data.get("article", {}), "article")
    validate_footer_data(data.get("footer", {}))
    validate_hero_data(data.get("hero", {}))
    if not data.get("sections"):
        raise ConversionError("Template data has no bilingual sections.")
    validate_article_context(data.get("article", {}))
    validate_summary_data(data.get("summary", {}))
    validate_framework_data(data.get("framework", {}))
    validate_quiz_data(data.get("quiz", []))
    validate_sections_data(data["sections"])
    for row in iter_original_rows(data):
        if row.get("type") == "bilingual":
            validate_bilingual_row(row)
        if row.get("type") in {"code", "image", "table"} and ("zh" in row or "en" in row):
            raise ConversionError("Media and table rows must not participate in bilingual comparison.")
        if row.get("type") == "image":
            validate_image_src(str(row.get("src", "")))
        if row.get("type") == "table":
            validate_table_rows([[str(cell) for cell in table_row] for table_row in row.get("rows", [])])
    for entry in data.get("glossary", {}).get("entries", []):
        validate_glossary_entry(entry)
    glossary = data.get("glossary", {})
    if glossary.get("entries") and (not glossary.get("dict") or not glossary.get("autowrap")):
        raise ConversionError("Glossary runtime dict/autowrap data is missing.")
    validate_glossary_runtime(glossary)


def validate_metadata_object(metadata: object, path: str) -> None:
    """Validate source metadata objects in data.json."""

    if not isinstance(metadata, dict):
        raise ConversionError(f"{path} must be an object.")
    title = str(metadata.get("title", "")).strip()
    source_url = str(metadata.get("sourceUrl", "")).strip()
    if not title:
        raise ConversionError(f"{path}.title is missing.")
    if source_url and not SOURCE_URL_RE.fullmatch(source_url):
        raise ConversionError(f"{path}.sourceUrl must be an http(s) URL.")
    fetched_at = str(metadata.get("fetchedAt", "")).strip()
    if fetched_at:
        validate_metadata(source_url or "https://example.invalid", fetched_at)


def validate_footer_data(footer: object) -> None:
    """Validate footer source attribution."""

    if not isinstance(footer, dict):
        raise ConversionError("Footer data must be an object.")
    source_url = str(footer.get("sourceUrl", "")).strip()
    source_text = str(footer.get("sourceText", "")).strip()
    if not source_url or not SOURCE_URL_RE.fullmatch(source_url):
        raise ConversionError("Footer sourceUrl must be an http(s) URL.")
    if not source_text:
        raise ConversionError("Footer sourceText is missing.")


def validate_hero_data(hero: object) -> None:
    """Validate hero fields required by every template."""

    if not isinstance(hero, dict):
        raise ConversionError("Hero data must be an object.")
    for key in ("title", "en", "zh"):
        if not str(hero.get(key, "")).strip():
            raise ConversionError(f"Hero field is missing: {key}.")
    validate_chinese_text(hero.get("zh", ""), "hero.zh")


def validate_article_context(context: object) -> None:
    """Validate source metadata shown at the top of the original tab."""

    if not isinstance(context, dict):
        raise ConversionError("Article context must be an object.")
    if not context.get("tags") or not context.get("anchors"):
        raise ConversionError("Article context must include tags and anchors.")


def validate_summary_data(summary: object) -> None:
    """Validate that the close-reading guide has real summary content."""

    if not isinstance(summary, dict):
        raise ConversionError("Summary data must be an object.")
    if not str(summary.get("lead", "")).strip():
        raise ConversionError("Summary lead is missing.")
    cards = summary.get("cards", [])
    if not isinstance(cards, list) or not cards:
        raise ConversionError("Summary cards are missing.")
    for card in cards:
        if not isinstance(card, dict) or not str(card.get("title", "")).strip() or not str(card.get("body", "")).strip():
            raise ConversionError("Summary cards must include title and body.")


def validate_framework_data(framework: object) -> None:
    """Validate the close-reading logic framework."""

    if not isinstance(framework, dict):
        raise ConversionError("Framework data must be an object.")
    nodes = framework.get("nodes", [])
    if not isinstance(nodes, list) or not nodes:
        raise ConversionError("Framework nodes are missing.")
    for node in nodes:
        if not isinstance(node, dict) or not node.get("label") or not node.get("summary"):
            raise ConversionError("Framework nodes must include label and summary.")


def validate_quiz_data(quiz: object) -> None:
    """Validate article comprehension quiz data."""

    if not isinstance(quiz, list) or not quiz:
        raise ConversionError("Comprehension quiz is missing.")
    for item in quiz:
        if not isinstance(item, dict):
            raise ConversionError("Quiz item must be an object.")
        options = item.get("options", [])
        answer = item.get("answer")
        if not item.get("question") or not isinstance(options, list) or len(options) < 3:
            raise ConversionError("Quiz item must include a question and at least three options.")
        cleaned_options = [clean_text(str(option)) for option in options]
        if len(set(cleaned_options)) != len(cleaned_options):
            raise ConversionError("Quiz options must not contain duplicates.")
        if not isinstance(answer, int) or answer < 0 or answer >= len(options):
            raise ConversionError("Quiz answer index is invalid.")
        if not item.get("explain") or not item.get("wrongReason"):
            raise ConversionError("Quiz item must include explanation and wrong reason.")


def validate_sections_data(sections: object) -> None:
    """Validate summary-view sections and their Chinese fields."""

    if not isinstance(sections, list):
        raise ConversionError("Template sections must be a list.")
    for section in sections:
        if not isinstance(section, dict):
            raise ConversionError("Each template section must be an object.")
        rows = section.get("rows", [])
        if not isinstance(rows, list) or not rows:
            raise ConversionError("Each template section must include rows.")
        for row in rows:
            validate_bilingual_row(row)
        validate_section_chinese_fields(section)


def validate_section_chinese_fields(value: object, path: str = "sections[]") -> None:
    """Ensure section fields named zh/zh* contain Chinese text."""

    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if (key == "zh" or key.startswith("zh")) and isinstance(child, str):
                validate_chinese_text(child, child_path)
            validate_section_chinese_fields(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_section_chinese_fields(child, f"{path}[{index}]")


def validate_bilingual_row(row: dict[str, object]) -> None:
    """Validate that bilingual prose keeps both source and Chinese text."""

    if not isinstance(row, dict):
        raise ConversionError("Bilingual row must be an object.")
    if not str(row.get("en", "")).strip() or not str(row.get("zh", "")).strip():
        raise ConversionError("Bilingual rows must include both English and Chinese text.")
    validate_chinese_text(row.get("zh", ""), "sections[].rows[].zh")


def validate_chinese_text(value: object, path: str) -> None:
    """Validate that a Chinese field is actually translated into Chinese."""

    text = str(value or "").strip()
    if text and not CHINESE_TEXT_RE.search(text):
        raise ConversionError(f"{path} must contain Chinese translation text.")


def validate_glossary_entry(entry: dict[str, str]) -> None:
    """Validate one enriched glossary item."""

    if not isinstance(entry, dict):
        raise ConversionError("Glossary entry must be an object.")
    required = ("word", "ipa", "definitionZh", "collocationExample")
    missing = [key for key in required if not str(entry.get(key, "")).strip()]
    if missing:
        raise ConversionError(f"Glossary entry is missing required fields: {', '.join(missing)}.")
    validate_chinese_text(entry.get("definitionZh", ""), "glossary.entries[].definitionZh")


def validate_glossary_runtime(glossary: object) -> None:
    """Validate runtime glossary dictionary and autowrap references."""

    if not isinstance(glossary, dict):
        raise ConversionError("Glossary data must be an object.")
    dictionary = glossary.get("dict", {})
    autowrap = glossary.get("autowrap", [])
    if dictionary and not isinstance(dictionary, dict):
        raise ConversionError("Glossary dict must be an object.")
    if autowrap and not isinstance(autowrap, list):
        raise ConversionError("Glossary autowrap must be a list.")
    for index, item in enumerate(autowrap if isinstance(autowrap, list) else []):
        if not isinstance(item, list) or len(item) != 3:
            raise ConversionError("Glossary autowrap item must be [pattern, flags, key].")
        pattern, _, key = item
        if str(key) not in dictionary:
            raise ConversionError(f"Glossary autowrap key is missing from dict: {key}.")
        try:
            re.compile(str(pattern))
        except re.error as exc:
            raise ConversionError(f"Glossary autowrap regex is invalid at index {index}.") from exc


def iter_original_rows(data: dict[str, object]) -> Iterable[dict[str, object]]:
    """Yield rows from the original-view data structure."""

    original = data.get("original", {})
    if not isinstance(original, dict):
        raise ConversionError("Original data must be an object.")
    groups = original.get("groups", [])
    if not isinstance(groups, list):
        raise ConversionError("Original groups must be a list.")
    for group in groups:
        if not isinstance(group, dict):
            raise ConversionError("Original group must be an object.")
        rows = group.get("rows", [])
        if not isinstance(rows, list):
            raise ConversionError("Original group rows must be a list.")
        yield from rows


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""

    parser = argparse.ArgumentParser(description="Convert normalized Markdown to bilingual-reader data.")
    parser.add_argument("markdown_file", type=Path, help="Markdown file generated by web-markdown.")
    parser.add_argument("--output", type=Path, help="Optional JSON output path.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point."""

    args = build_parser().parse_args(argv)
    try:
        article = parse_markdown(args.markdown_file.read_text(encoding="utf-8"))
        payload = json.dumps(asdict(article), ensure_ascii=False, indent=2)
        if args.output:
            args.output.write_text(payload + "\n", encoding="utf-8")
        else:
            print(payload)
    except Exception as exc:
        print(f"markdown_to_data failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

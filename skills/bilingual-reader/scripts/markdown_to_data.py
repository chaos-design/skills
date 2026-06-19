#!/usr/bin/env python3
"""Convert normalized article Markdown into bilingual-reader template data.

The module intentionally keeps extraction deterministic. Translation,
summarization, and glossary enrichment are injected as callables so callers can
use the Agent/LLM layer after the full source article has been parsed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Optional, Union


DEV_MARKER_RE = re.compile(r"\b(?:DOC|TPL|DOM)\d+\b")
PLACEHOLDER_RE = re.compile(r"__(?:[A-Z][A-Z0-9_]*|DATA_JSON|THEME_JSON)__")
SOURCE_RE = re.compile(r"^>\s*Source:\s*(\S+)\s*$", re.IGNORECASE)
FETCHED_RE = re.compile(r"^>\s*Fetched:\s*(.+?)\s*$", re.IGNORECASE)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
IMAGE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)\s*$")
FENCE_RE = re.compile(r"^```([A-Za-z0-9_+.-]*)\s*$")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
GLOSSARY_KEY_RE = re.compile(r"[^a-z0-9]+")

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


@dataclass
class Block:
    """A normalized source block in original reading order."""

    type: str
    text: str = ""
    level: int = 0
    language: str = ""
    code: str = ""
    src: str = ""
    alt: str = ""
    caption: str = ""
    rows: list[list[str]] = field(default_factory=list)


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


def strip_inline_markdown(value: str) -> str:
    """Convert lightweight inline Markdown to readable plain text."""

    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", value)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*`]+", "", text)
    return clean_text(text)


def parse_markdown(markdown: str) -> Article:
    """Parse web-markdown output into article blocks."""

    lines = markdown.splitlines()
    metadata = extract_metadata(lines)
    blocks = parse_blocks(lines)
    blocks = remove_metadata_blocks(metadata, blocks)
    article = Article(metadata=metadata, blocks=blocks)
    validate_article(article)
    return article


def extract_metadata(lines: list[str]) -> Metadata:
    """Extract title, source URL, and fetch timestamp."""

    title = ""
    source_url = ""
    fetched_at = ""
    for line in lines:
        if not title:
            match = HEADING_RE.match(line)
            if match and len(match.group(1)) == 1:
                title = strip_inline_markdown(match.group(2))
        source_match = SOURCE_RE.match(line)
        fetched_match = FETCHED_RE.match(line)
        if source_match:
            source_url = source_match.group(1)
        if fetched_match:
            fetched_at = fetched_match.group(1)
    if not title:
        raise ConversionError("Markdown title is missing.")
    if not source_url:
        raise ConversionError("Source URL metadata is missing.")
    return Metadata(title=title, source_url=source_url, fetched_at=fetched_at)


def parse_blocks(lines: list[str]) -> list[Block]:
    """Parse block-level Markdown while preserving reading order."""

    blocks: list[Block] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if SOURCE_RE.match(line) or FETCHED_RE.match(line):
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
        blocks.append(Block(type="heading", level=len(heading.group(1)), text=strip_inline_markdown(heading.group(2))))
        return index + 1
    image = IMAGE_RE.match(line)
    if image:
        blocks.append(Block(type="image", alt=clean_text(image.group(1)), src=image.group(2), caption=clean_text(image.group(3) or "")))
        return index + 1
    if looks_like_table(lines, index):
        return parse_table_block(lines, index, blocks)
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
    blocks.append(Block(type="code", language=language, code="\n".join(code_lines)))
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
    blocks.append(Block(type="table", rows=[row for row in rows if row]))
    return cursor


def parse_table_row(line: str) -> list[str]:
    """Parse one Markdown table row."""

    value = line.strip().strip("|")
    return [strip_inline_markdown(cell) for cell in value.split("|")]


def parse_paragraph(lines: list[str], index: int, blocks: list[Block]) -> int:
    """Parse a paragraph, list item group, or blockquote into prose."""

    parts: list[str] = []
    cursor = index
    while cursor < len(lines) and can_continue_paragraph(lines[cursor]):
        parts.append(clean_markdown_line(lines[cursor]))
        cursor += 1
    text = strip_inline_markdown(" ".join(part for part in parts if part))
    if text and not is_boilerplate(text):
        blocks.append(Block(type="paragraph", text=text))
    return cursor


def can_continue_paragraph(line: str) -> bool:
    """Check whether a line belongs to the current prose block."""

    if not line.strip():
        return False
    return not (HEADING_RE.match(line) or FENCE_RE.match(line) or IMAGE_RE.match(line))


def clean_markdown_line(line: str) -> str:
    """Remove list and quote markers from prose lines."""

    value = re.sub(r"^\s*>\s?", "", line)
    value = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", value)
    return value.strip()


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
            "pos": str(entry.get("pos") or ("术语" if entry.get("level") == "术语" else "")),
            "level": str(entry.get("level") or "术语"),
            "def": str(entry.get("definitionZh", "")),
            "eg": str(entry.get("collocationExample", "")),
            "egzh": str(entry.get("exampleZh", "")),
        }
        autowrap.append([autowrap_pattern(word), "i", key])
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


def autowrap_pattern(word: str) -> str:
    """Create a whole-word regex source for runtime autowrap."""

    escaped = re.escape(word)
    if re.fullmatch(r"[A-Za-z]+", word):
        if len(word) > 2 and not word.casefold().endswith("s"):
            escaped += "s?"
        return rf"\b{escaped}\b"
    if re.match(r"^[A-Za-z0-9]", word) and re.search(r"[A-Za-z0-9]$", word):
        return rf"\b{escaped}\b"
    return escaped


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
        rows = [original_row(block, translate) for block in section["blocks"]]
        groups.append({"id": f"og-{index}", "group": section["title"], "rows": [row for row in rows if row]})
    return {"title": f"{article.metadata.title} · 原文全文对照", "meta": article.metadata.source_url, "groups": groups}


def original_row(block: Block, translate: Translator) -> dict[str, object]:
    """Convert a source block to an original-view row."""

    if block.type == "paragraph":
        return {"type": "bilingual", "en": block.text, "zh": translate(block.text)}
    if block.type == "table":
        return {
            "type": "table",
            "rows": block.rows,
            "zhRows": translate_table_rows(block.rows, translate),
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


def split_top_level_sections(article: Article, include_media: bool = False) -> list[dict[str, object]]:
    """Group original-view content under Markdown level-two headings."""

    sections: list[dict[str, object]] = []
    current = {"title": article.metadata.title, "blocks": []}
    for block in article.blocks:
        if block.type == "heading":
            if block.level == 2:
                if current["blocks"]:
                    sections.append(current)
                current = {"title": block.text, "blocks": []}
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

    if not data["sections"]:
        raise ConversionError("Template data has no bilingual sections.")
    validate_article_context(data.get("article", {}))
    validate_summary_data(data.get("summary", {}))
    validate_framework_data(data.get("framework", {}))
    validate_quiz_data(data.get("quiz", []))
    for section in data["sections"]:
        for row in section.get("rows", []):
            validate_bilingual_row(row)
    for row in iter_original_rows(data):
        if row.get("type") == "bilingual":
            validate_bilingual_row(row)
        if row.get("type") in {"code", "image", "table"} and ("zh" in row or "en" in row):
            raise ConversionError("Media and table rows must not participate in bilingual comparison.")
    for entry in data.get("glossary", {}).get("entries", []):
        validate_glossary_entry(entry)
    glossary = data.get("glossary", {})
    if glossary.get("entries") and (not glossary.get("dict") or not glossary.get("autowrap")):
        raise ConversionError("Glossary runtime dict/autowrap data is missing.")


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
        if not isinstance(answer, int) or answer < 0 or answer >= len(options):
            raise ConversionError("Quiz answer index is invalid.")
        if not item.get("explain") or not item.get("wrongReason"):
            raise ConversionError("Quiz item must include explanation and wrong reason.")


def validate_bilingual_row(row: dict[str, object]) -> None:
    """Validate that bilingual prose keeps both source and Chinese text."""

    if not str(row.get("en", "")).strip() or not str(row.get("zh", "")).strip():
        raise ConversionError("Bilingual rows must include both English and Chinese text.")


def validate_glossary_entry(entry: dict[str, str]) -> None:
    """Validate one enriched glossary item."""

    required = ("word", "ipa", "definitionZh", "collocationExample")
    missing = [key for key in required if not str(entry.get(key, "")).strip()]
    if missing:
        raise ConversionError(f"Glossary entry is missing required fields: {', '.join(missing)}.")


def iter_original_rows(data: dict[str, object]) -> Iterable[dict[str, object]]:
    """Yield rows from the original-view data structure."""

    original = data.get("original", {})
    for group in original.get("groups", []):
        yield from group.get("rows", [])


def identity_translator(text: str) -> str:
    """Testing/demo translator; production callers should inject real Chinese."""

    return f"中文：{text}"


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""

    parser = argparse.ArgumentParser(description="Convert normalized Markdown to bilingual-reader data.")
    parser.add_argument("markdown_file", type=Path, help="Markdown file generated by web-markdown.")
    parser.add_argument("--output", type=Path, help="Optional JSON output path.")
    parser.add_argument("--demo-translator", action="store_true", help="Use a demo translator for local structural tests.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point."""

    args = build_parser().parse_args(argv)
    try:
        article = parse_markdown(args.markdown_file.read_text(encoding="utf-8"))
        data: Union[dict[str, object], Article]
        if args.demo_translator:
            data = build_learning_data(article, identity_translator)
        else:
            data = article
        payload = json.dumps(asdict(data) if isinstance(data, Article) else data, ensure_ascii=False, indent=2)
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

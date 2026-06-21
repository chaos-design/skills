#!/usr/bin/env python3
"""Review bilingual-reader Markdown, data.json, and generated HTML artifacts."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import re
import sys
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable

try:
    from markdown_to_data import (
        GLOSSARY_LEVELS,
        ConversionError,
        parse_markdown,
        source_contains_word_or_inflection,
        validate_learning_data,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from markdown_to_data import (
        GLOSSARY_LEVELS,
        ConversionError,
        parse_markdown,
        source_contains_word_or_inflection,
        validate_learning_data,
    )


CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
DEV_MARKER_RE = re.compile(r"\b(?:DOC|TPL|DOM)\d+\b")
PLACEHOLDER_RE = re.compile(r"__(?:[A-Z][A-Z0-9_]*|DATA_JSON|THEME_JSON)__")
SOURCE_RE = re.compile(r"^>\s*Source:\s*(\S+)\s*$", re.MULTILINE | re.IGNORECASE)
FETCHED_RE = re.compile(r"^>\s*Fetched:\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*$", re.MULTILINE | re.IGNORECASE)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
FENCE_RE = re.compile(r"^```", re.MULTILINE)
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
URL_RE = re.compile(r"https?://[^\s\"'<>]+")
SOURCE_URL_RE = re.compile(r"^https?://[^\s\"'<>]+$", re.IGNORECASE)
CHINESE_RE = re.compile(r"[\u3400-\u9fff]")
ASCII_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]{2,}")
FORBIDDEN_HTML_RE = re.compile(
    r"__DATA_JSON__|__THEME_JSON__|\b(?:DOC|TPL|DOM)\d+\b|fetch\s*\(|type=[\"']module[\"']",
    re.IGNORECASE,
)
APPROVED_CODE_HIGHLIGHT_ASSETS = {
    "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js",
}


@dataclass
class Issue:
    """One review finding."""

    severity: str
    code: str
    artifact: str
    path: str
    message: str
    suggestion: str


class TagCollector(HTMLParser):
    """Collect HTML tags and attributes for static checks."""

    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag.casefold(), {key.casefold(): value or "" for key, value in attrs}))


def add_issue(
    issues: list[Issue],
    severity: str,
    code: str,
    artifact: str,
    path: str,
    message: str,
    suggestion: str,
) -> None:
    """Append one normalized issue."""

    issues.append(Issue(severity, code, artifact, path, message, suggestion))


def read_utf8(path: Path, artifact: str, issues: list[Issue]) -> str:
    """Read a text file as strict UTF-8 and report encoding problems."""

    try:
        payload = path.read_bytes()
    except OSError as exc:
        add_issue(issues, "error", "file.read_failed", artifact, str(path), str(exc), "确认文件存在且可读。")
        return ""
    if payload.startswith(b"\xef\xbb\xbf"):
        add_issue(issues, "warning", "encoding.utf8_bom", artifact, str(path), "文件包含 UTF-8 BOM。", "保存为无 BOM UTF-8。")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        add_issue(issues, "error", "encoding.invalid_utf8", artifact, str(path), str(exc), "用 UTF-8 重新导出文件。")
        return ""
    if "\ufffd" in text:
        add_issue(issues, "error", "encoding.replacement_char", artifact, str(path), "发现替换字符 �，疑似乱码。", "回到源内容重新抓取或修正编码。")
    if CONTROL_CHAR_RE.search(text):
        add_issue(issues, "error", "encoding.control_char", artifact, str(path), "发现不可见控制字符。", "删除控制字符后重新生成。")
    return text


def compact_text(value: object) -> str:
    """Normalize text for comparison."""

    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = re.sub(r"[^A-Za-z0-9\u3400-\u9fff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def glossary_source_text(value: object) -> str:
    """Normalize source text for glossary matching, preserving word-internal punctuation.

    Unlike `compact_text`, this keeps hyphens and apostrophes so multiword and
    hyphenated glossary terms such as `all-or-nothing` or `human-in-the-loop` are
    matched against their verbatim source form rather than a punctuation-stripped one.
    """

    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = re.sub(r"[^A-Za-z0-9\u3400-\u9fff'\-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def source_contains(source_text: str, candidate: object, min_words: int = 4) -> bool:
    """Return whether candidate prose appears to be source-backed."""

    candidate_text = compact_text(candidate)
    if not candidate_text:
        return True
    if candidate_text in source_text:
        return True
    words = [word for word in ASCII_WORD_RE.findall(candidate_text) if len(word) > 2]
    if len(words) < min_words:
        return True
    hits = sum(1 for word in set(words) if re.search(rf"\b{re.escape(word)}\b", source_text))
    return hits / max(len(set(words)), 1) >= 0.72


def review_markdown(path: Path, issues: list[Issue]) -> str:
    """Review normalized Markdown format, metadata, and encoding."""

    text = read_utf8(path, "markdown", issues)
    if not text:
        return ""
    if len(text.strip()) < 400:
        add_issue(issues, "error", "markdown.too_short", "markdown", str(path), "正文过短，可能不是完整来源。", "重新抓取或补全 Markdown。")
    if not HEADING_RE.search(text):
        add_issue(issues, "error", "markdown.missing_heading", "markdown", str(path), "缺少 Markdown 标题。", "补充来源文章标题。")
    if len([match for match in HEADING_RE.finditer(text) if len(match.group(1)) == 1]) != 1:
        add_issue(issues, "warning", "markdown.h1_count", "markdown", str(path), "H1 标题数量不是 1。", "保留一个来源主标题。")
    if not SOURCE_RE.search(text):
        add_issue(issues, "error", "markdown.missing_source", "markdown", str(path), "缺少 `> Source:` 元数据。", "补充原文 URL。")
    source_match = SOURCE_RE.search(text)
    if source_match and not SOURCE_URL_RE.fullmatch(source_match.group(1)):
        add_issue(issues, "error", "markdown.invalid_source", "markdown", str(path), "`Source` 不是 http(s) URL。", "使用真实来源 URL。")
    fetched_match = FETCHED_RE.search(text)
    if not fetched_match:
        add_issue(issues, "error", "markdown.invalid_fetched", "markdown", str(path), "缺少合法 `YYYY-MM-DD HH:mm:ss` Fetched 时间。", "使用 UTC+8 格式重新生成。")
    else:
        review_fetched_time(fetched_match.group(1), path, issues)
    review_markdown_syntax(text, path, issues)
    try:
        parse_markdown(text)
    except ConversionError as exc:
        add_issue(issues, "error", "markdown.parser_contract", "markdown", str(path), str(exc), "修复 Markdown 结构后重新解析。")
    return text


def review_markdown_syntax(text: str, path: Path, issues: list[Issue]) -> None:
    """Check Markdown syntax risks not fully covered by the parser."""

    if len(FENCE_RE.findall(text)) % 2:
        add_issue(issues, "error", "markdown.unclosed_fence", "markdown", str(path), "代码围栏数量为奇数。", "补齐闭合 ```。")
    for index, line in enumerate(text.splitlines(), 1):
        if re.match(r"^#{1,6}\s*$", line):
            add_issue(issues, "error", "markdown.empty_heading", "markdown", f"{path}#L{index}", "发现空标题。", "补充标题文本或删除该行。")
        if "|" in line and re.match(r"^\s*\|?\s*:?-{0,2}:?\s*(?:\|\s*:?-{0,2}:?\s*)+\|?\s*$", line):
            add_issue(issues, "error", "markdown.bad_table_separator", "markdown", f"{path}#L{index}", "表格分隔行至少需要 3 个连字符。", "使用 `---` 表格分隔符。")
    for match in IMAGE_RE.finditer(text):
        src = match.group(1)
        if src.startswith("http://"):
            add_issue(issues, "warning", "markdown.insecure_image", "markdown", str(path), f"图片使用 http：{src}", "优先使用 https 或内联 data URI。")
        if not (src.startswith(("http://", "https://", "data:image/"))):
            add_issue(issues, "error", "markdown.invalid_image_src", "markdown", str(path), f"图片来源不受支持：{src}", "使用 http(s) URL 或 data:image。")


def review_fetched_time(value: str, path: Path, issues: list[Issue]) -> None:
    """Check fetched timestamp is a real calendar time."""

    try:
        datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        add_issue(issues, "error", "markdown.invalid_fetched_time", "markdown", str(path), "Fetched 时间不是有效日期。", "使用真实 UTC+8 时间。")


def load_data(path: Path, issues: list[Issue]) -> dict[str, Any]:
    """Load and review JSON syntax."""

    text = read_utf8(path, "data", issues)
    if not text:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        add_issue(issues, "error", "data.invalid_json", "data", str(path), str(exc), "修复 JSON 语法。")
        return {}
    if not isinstance(data, dict):
        add_issue(issues, "error", "data.root_type", "data", str(path), "data.json 根节点必须是对象。", "重新生成 data.json。")
        return {}
    return data


def review_data(path: Path, markdown_text: str, issues: list[Issue]) -> dict[str, Any]:
    """Review data contract, ranges, and source fidelity."""

    data = load_data(path, issues)
    if not data:
        return {}
    try:
        validate_learning_data(data)
    except Exception as exc:
        add_issue(issues, "error", "data.contract", "data", str(path), str(exc), "按 data-schema.md 修复结构。")
    for key in ("metadata", "article", "hero", "summary", "framework", "sections", "quiz", "original", "glossary", "footer"):
        if key not in data:
            add_issue(issues, "error", "data.missing_top_field", "data", key, f"缺少顶层字段 `{key}`。", "重新生成或补齐该字段。")
    review_data_ranges(data, path, issues)
    review_data_text_fields(data, path, issues)
    if markdown_text:
        review_source_fidelity(data, compact_text(markdown_text), path, issues)
        review_glossary_quality(data, glossary_source_text(markdown_text), path, issues)
    else:
        add_issue(issues, "warning", "content.no_markdown_reference", "data", str(path), "未提供 Markdown，无法做来源忠实性自动比对。", "同时传入 `--markdown`。")
    return data


def review_data_ranges(data: dict[str, Any], path: Path, issues: list[Issue]) -> None:
    """Check numeric and collection ranges."""

    sections = data.get("sections", [])
    quiz = data.get("quiz", [])
    glossary = data.get("glossary", {}).get("entries", []) if isinstance(data.get("glossary"), dict) else []
    if not isinstance(sections, list) or not 1 <= len(sections) <= 80:
        add_issue(issues, "error", "data.sections_range", "data", "sections", "sections 数量超出 1-80 合理范围。", "检查是否缺失或重复生成。")
    if isinstance(quiz, list) and len(quiz) > 20:
        add_issue(issues, "warning", "data.quiz_range", "data", "quiz", "quiz 数量超过 20。", "保留高价值题目，避免噪声。")
    if isinstance(glossary, list) and len(glossary) > 160:
        add_issue(issues, "warning", "data.glossary_range", "data", "glossary.entries", "词汇表超过 160 项。", "减少低价值或重复词条。")
    if isinstance(sections, list) and len(sections) >= 4 and isinstance(glossary, list) and 0 < len(glossary) < 60:
        add_issue(issues, "warning", "data.glossary_sparse", "data", "glossary.entries", "中等及以上文章的词汇表少于 60 项。", "优先补充来源中的高价值词、短语和领域术语，避免无关填充。")
    source_url = str(data.get("metadata", {}).get("sourceUrl") or data.get("article", {}).get("sourceUrl") or "")
    if source_url and not source_url.startswith(("http://", "https://")):
        add_issue(issues, "error", "data.invalid_source_url", "data", str(path), "sourceUrl 不是 http(s) URL。", "使用真实来源 URL。")
    review_glossary_runtime(data, path, issues)


def review_data_text_fields(data: dict[str, Any], path: Path, issues: list[Issue]) -> None:
    """Check placeholders, Chinese fields, and quiz answer bounds."""

    for item_path, value in walk_values(data):
        if isinstance(value, str):
            if PLACEHOLDER_RE.search(value) or DEV_MARKER_RE.search(value):
                add_issue(issues, "error", "data.placeholder", "data", item_path, "发现占位符或开发标记。", "删除模板占位内容。")
            if item_path.split(".")[-1].startswith("zh") and value.strip() and not CHINESE_RE.search(value):
                add_issue(issues, "error", "data.zh_not_chinese", "data", item_path, "中文字段不含中文字符。", "补充准确中文翻译。")
    for index, item in enumerate(data.get("quiz", []) if isinstance(data.get("quiz"), list) else []):
        options = item.get("options", [])
        answer = item.get("answer")
        if isinstance(options, list) and (not isinstance(answer, int) or answer < 0 or answer >= len(options)):
            add_issue(issues, "error", "data.quiz_answer_bounds", "data", f"quiz[{index}].answer", "答案索引越界。", "修正 answer 到 options 范围内。")
        normalized = [compact_text(option) for option in options] if isinstance(options, list) else []
        if normalized and len(set(normalized)) != len(normalized):
            add_issue(issues, "error", "data.quiz_duplicate_options", "data", f"quiz[{index}].options", "题目选项重复。", "保留唯一选项。")


def review_glossary_runtime(data: dict[str, Any], path: Path, issues: list[Issue]) -> None:
    """Check glossary runtime references and regex syntax."""

    glossary = data.get("glossary", {})
    if not isinstance(glossary, dict):
        return
    dictionary = glossary.get("dict", {})
    autowrap = glossary.get("autowrap", [])
    if not isinstance(dictionary, dict) or not isinstance(autowrap, list):
        return
    for index, item in enumerate(autowrap):
        if not isinstance(item, list) or len(item) != 3:
            add_issue(issues, "error", "data.glossary_autowrap_shape", "data", f"glossary.autowrap[{index}]", "autowrap 必须是 [pattern, flags, key]。", "重新生成词汇运行时索引。")
            continue
        pattern, _, key = item
        if str(key) not in dictionary:
            add_issue(issues, "error", "data.glossary_missing_key", "data", f"glossary.autowrap[{index}]", f"词汇 key 不存在：{key}", "同步 dict 与 autowrap。")
        try:
            re.compile(str(pattern))
        except re.error as exc:
            add_issue(issues, "error", "data.glossary_bad_regex", "data", f"glossary.autowrap[{index}]", str(exc), "修正 autowrap 正则。")


def review_glossary_quality(data: dict[str, Any], source_text: str, path: Path, issues: list[Issue]) -> None:
    """Check glossary CEFR levels and that every word comes from the source."""

    glossary = data.get("glossary", {})
    if not isinstance(glossary, dict):
        return
    entries = glossary.get("entries", [])
    if not isinstance(entries, list):
        return
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        word = str(entry.get("word", "")).strip()
        level = str(entry.get("level", "")).strip()
        pos = str(entry.get("pos", ""))
        if level not in GLOSSARY_LEVELS:
            add_issue(
                issues,
                "error",
                "data.glossary_invalid_level",
                "data",
                f"glossary.entries[{index}].level",
                f"词汇等级不合法：{word or '(空)'} -> {level or '(缺失)'}。",
                f"仅使用 {', '.join(GLOSSARY_LEVELS)}，并按真实英语难度标注。",
            )
        if not word:
            continue
        key = word.casefold()
        if key in seen:
            continue
        seen.add(key)
        if not source_contains_word_or_inflection(word, pos, source_text):
            add_issue(
                issues,
                "error",
                "data.glossary_not_source_backed",
                "data",
                f"glossary.entries[{index}].word",
                f"词汇未在 Markdown 原文中出现：{word}。",
                "只收录原文中真实出现的词、短语或术语，删除凭空生成的词条。",
            )


def walk_values(value: Any, prefix: str = "$") -> Iterable[tuple[str, Any]]:
    """Yield dotted paths and values recursively."""

    yield prefix, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk_values(child, f"{prefix}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_values(child, f"{prefix}[{index}]")


def review_source_fidelity(data: dict[str, Any], source_text: str, path: Path, issues: list[Issue]) -> None:
    """Check that source-backed English and claims are traceable."""

    for item_path, value in source_backed_english(data):
        if not source_contains(source_text, value):
            add_issue(issues, "error", "content.not_source_backed", "data", item_path, "英文内容无法在 Markdown 来源中找到足够依据。", "删除杜撰内容或改为原文支持的表达。")
    for item_path, value in summary_claims(data):
        if contains_unbacked_url(value, source_text):
            add_issue(issues, "error", "content.unbacked_url", "data", item_path, "总结或解释中出现原文未包含的 URL。", "移除非来源 URL。")
        if contains_suspicious_number(value, source_text):
            add_issue(issues, "warning", "content.number_needs_review", "data", item_path, "总结或解释中包含原文未明显支持的数字。", "人工核对数字是否来自原文。")
    add_issue(issues, "info", "content.manual_review_required", "data", str(path), "事实准确性和是否胡编乱造仍需人工审查最终确认。", "逐句对照 Markdown 审阅翻译、总结、quiz 和 glossary。")


def source_backed_english(data: dict[str, Any]) -> Iterable[tuple[str, str]]:
    """Yield English fields expected to be source-backed."""

    for index, section in enumerate(data.get("sections", []) if isinstance(data.get("sections"), list) else []):
        for row_index, row in enumerate(section.get("rows", []) if isinstance(section, dict) else []):
            yield f"sections[{index}].rows[{row_index}].en", str(row.get("en", ""))
    for group_index, group in enumerate(data.get("original", {}).get("groups", []) if isinstance(data.get("original"), dict) else []):
        for row_index, row in enumerate(group.get("rows", []) if isinstance(group, dict) else []):
            if isinstance(row, dict) and row.get("en"):
                yield f"original.groups[{group_index}].rows[{row_index}].en", str(row.get("en", ""))


def summary_claims(data: dict[str, Any]) -> Iterable[tuple[str, str]]:
    """Yield generated interpretive fields that need source review."""

    interesting = ("lead", "thesis", "body", "summary", "explain", "wrongReason", "definitionZh", "exampleZh")
    for path, value in walk_values(data):
        if isinstance(value, str) and any(path.endswith(f".{name}") for name in interesting):
            yield path, value


def contains_unbacked_url(value: str, source_text: str) -> bool:
    """Return true when generated text contains a URL not present in source."""

    return any(compact_text(url) not in source_text for url in URL_RE.findall(value))


def contains_suspicious_number(value: str, source_text: str) -> bool:
    """Return true when a non-trivial generated number is not source-backed."""

    for number in re.findall(r"\b\d+(?:\.\d+)?%?\b", value):
        if number not in source_text and number not in {"0", "1", "2", "3", "4"}:
            return True
    return False


VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
    "param", "source", "track", "wbr", "path", "circle", "rect", "line",
    "polygon", "polyline", "ellipse", "stop", "use",
}


class CloseReadingAuditor(HTMLParser):
    """Audit that every close-reading evidence block has a paired analysis block.

    The close-reading layer must never present source evidence without an
    accompanying analytical conclusion. This parser tracks each conclusion-output
    and close-core-section block and records whether it contains analysis text and
    evidence text, so an evidence-only block can be reported as an error.
    """

    def __init__(self) -> None:
        super().__init__()
        self.stack: list[dict[str, Any]] = []
        self.active: list[dict[str, Any]] = []
        self.findings: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.casefold()
        if tag in VOID_TAGS:
            return
        attr_map = {key.casefold(): (value or "") for key, value in attrs}
        classes = set(attr_map.get("class", "").split())
        self.stack.append({"tag": tag, "classes": classes})
        if tag == "section":
            kind = (
                "conclusion"
                if "conclusion-output" in classes
                else "core"
                if "close-core-section" in classes
                else ""
            )
            if kind:
                self.active.append(
                    {
                        "kind": kind,
                        "depth": len(self.stack),
                        "id": attr_map.get("id", ""),
                        "analysis": False,
                        "evidence": False,
                    }
                )

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        return

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        if tag in VOID_TAGS:
            return
        if self.active and tag == "section" and self.active[-1]["depth"] == len(self.stack):
            self.findings.append(self.active.pop())
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]["tag"] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if not self.active or not data.strip() or not self.stack:
            return
        context = self.active[-1]
        parent = self.stack[-1]["tag"]
        ancestor_classes: set[str] = set()
        for node in self.stack:
            ancestor_classes |= node["classes"]
        if context["kind"] == "conclusion":
            if parent == "blockquote" or any(node["tag"] == "blockquote" for node in self.stack):
                context["evidence"] = True
            if "conclusion-list" in ancestor_classes and parent in {"li", "b", "span"}:
                context["analysis"] = True
        else:
            if "core-source" in ancestor_classes and parent == "p":
                context["evidence"] = True
            if ("core-thesis" in ancestor_classes and parent == "p") or (
                "core-principles" in ancestor_classes and parent == "li"
            ):
                context["analysis"] = True


def review_close_reading(text: str, path: Path, issues: list[Issue]) -> None:
    """Flag any close-reading block that shows evidence without analysis."""

    auditor = CloseReadingAuditor()
    try:
        auditor.feed(text)
    except Exception:
        return
    labels = {"conclusion": "结论输出", "core": "精读章节"}
    for finding in auditor.findings:
        anchor = finding.get("id") or finding["kind"]
        if finding["evidence"] and not finding["analysis"]:
            add_issue(
                issues,
                "error",
                "content.evidence_without_analysis",
                "html",
                f"{path}#{anchor}",
                f"{labels[finding['kind']]}只有证据区块，缺少配套分析要点。",
                "为每个证据区块补充基于原文推导的分析结论，或移除孤立证据。",
            )


def review_html(path: Path, issues: list[Issue]) -> str:
    """Review generated HTML content, functionality, and layout risks."""

    text = read_utf8(path, "html", issues)
    if not text:
        return ""
    collector = TagCollector()
    try:
        collector.feed(text)
    except Exception as exc:
        add_issue(issues, "error", "html.parse_failed", "html", str(path), str(exc), "修复 HTML 语法。")
    if not text.lstrip().startswith("<!DOCTYPE html>"):
        add_issue(issues, "warning", "html.missing_doctype", "html", str(path), "HTML 缺少 DOCTYPE。", "补充 `<!DOCTYPE html>`。")
    if FORBIDDEN_HTML_RE.search(text):
        add_issue(issues, "error", "html.forbidden_runtime", "html", str(path), "发现占位符、开发标记或禁用运行时模式。", "重新渲染静态 HTML。")
    review_html_contract(text, collector, path, issues)
    review_layout_boundaries(text, collector, path, issues)
    review_close_reading(text, path, issues)
    return text


def review_html_contract(text: str, collector: TagCollector, path: Path, issues: list[Issue]) -> None:
    """Check required page content and interaction hooks."""

    required_ids = ("hero", "toc", "originalSection", "glossary")
    ids = [attrs.get("id", "") for _, attrs in collector.tags if attrs.get("id")]
    id_set = set(ids)
    for required_id in required_ids:
        if required_id not in id_set:
            add_issue(issues, "error", "html.missing_required_id", "html", f"#{required_id}", "缺少必要页面区块。", "检查模板渲染是否完整。")
    for html_id in sorted({item for item in ids if ids.count(item) > 1}):
        add_issue(issues, "error", "html.duplicate_id", "html", f"#{html_id}", "发现重复 ID。", "确保模板和渲染数据生成唯一 ID。")
    if "原文：" not in text:
        add_issue(issues, "error", "html.missing_source_footer", "html", str(path), "缺少页脚原文链接文本。", "按 page-contract.md 渲染 footer。")
    buttons = [attrs for tag, attrs in collector.tags if tag == "button"]
    for mode in ("summary", "original", "glossary"):
        if not any(attrs.get("data-mode") == mode for attrs in buttons):
            add_issue(issues, "error", "html.missing_mode_button", "html", mode, f"缺少 `{mode}` 模式按钮。", "修复分段控件。")
    has_code_blocks = "<pre><code" in text
    if has_code_blocks and "language-" not in text:
        add_issue(issues, "warning", "html.code_language_missing", "html", str(path), "代码块缺少 language class。", "保留代码语言信息。")
    if has_code_blocks:
        stylesheet_urls = [attrs.get("href", "") for tag, attrs in collector.tags if tag == "link" and attrs.get("rel") == "stylesheet"]
        script_urls = [attrs.get("src", "") for tag, attrs in collector.tags if tag == "script"]
        has_highlight_css = any(is_approved_code_highlight_asset(url) and url.endswith(".css") for url in stylesheet_urls)
        has_highlight_script = any(is_approved_code_highlight_asset(url) and url.endswith(".min.js") for url in script_urls)
        if not has_highlight_css or not has_highlight_script:
            add_issue(
                issues,
                "error",
                "html.code_highlight_missing",
                "html",
                str(path),
                "页面包含代码块但缺少批准的代码高亮 SDK。",
                "保留 Highlight.js CSS 与脚本，同时确保代码内容仍以 <pre><code> 可见。",
            )


def review_layout_boundaries(text: str, collector: TagCollector, path: Path, issues: list[Issue]) -> None:
    """Check common overflow, image, and tooltip boundary protections."""

    if "overflow-wrap:anywhere" not in text and "overflow-wrap: anywhere" not in text:
        add_issue(issues, "warning", "layout.no_overflow_wrap", "html", str(path), "缺少长词换行保护。", "为正文/tooltip 添加 overflow-wrap。")
    if "minmax(0,1fr)" not in text:
        add_issue(issues, "warning", "layout.grid_min_width", "html", str(path), "网格布局缺少 `minmax(0,1fr)`。", "避免长内容撑破列宽。")
    if "source-table-wrap" in text and "overflow:auto" not in text and "overflow: auto" not in text:
        add_issue(issues, "error", "layout.table_overflow", "html", str(path), "表格容器缺少横向滚动保护。", "为表格容器添加 `overflow:auto`。")
    if ".tip" in text and "white-space:normal" not in text and "white-space: normal" not in text:
        add_issue(issues, "warning", "layout.tooltip_wrap", "html", str(path), "tooltip 缺少换行策略。", "添加 `white-space: normal`。")
    for index, attrs in enumerate(attrs for tag, attrs in collector.tags if tag == "img"):
        check_image_bounds(attrs, index, path, issues)
    for tag, attrs in collector.tags:
        if tag == "link" and attrs.get("rel") == "stylesheet" and attrs.get("href", "").startswith(("http://", "https://")):
            if not is_approved_code_highlight_asset(attrs.get("href", "")):
                add_issue(issues, "warning", "html.external_stylesheet", "html", str(path), f"外部样式：{attrs.get('href')}", "最终交付应内联 CSS，代码高亮 SDK 除外。")
        if tag == "script" and attrs.get("src", "").startswith(("http://", "https://")):
            if not is_approved_code_highlight_asset(attrs.get("src", "")):
                add_issue(issues, "warning", "html.external_script", "html", str(path), f"外部脚本：{attrs.get('src')}", "最终交付应内联 JS，代码高亮 SDK 除外。")


def is_approved_code_highlight_asset(url: str) -> bool:
    """Return true for approved external assets used only for code highlighting."""

    return url in APPROVED_CODE_HIGHLIGHT_ASSETS


def check_image_bounds(attrs: dict[str, str], index: int, path: Path, issues: list[Issue]) -> None:
    """Check generated image boundary attributes."""

    src = attrs.get("src", "")
    width = attrs.get("width", "")
    height = attrs.get("height", "")
    if src and ("data:image" in src or "http" in src) and (width, height) != ("720", "405"):
        add_issue(issues, "error", "layout.image_bounds", "html", f"{path} img[{index}]", "原文图片未使用 720x405 约束。", "设置 width=\"720\" height=\"405\" 并使用 object-fit: contain。")


def build_report(issues: list[Issue]) -> dict[str, Any]:
    """Build the JSON review report."""

    counts = {"error": 0, "warning": 0, "info": 0}
    for issue in issues:
        counts[issue.severity] = counts.get(issue.severity, 0) + 1
    return {
        "status": "fail" if counts.get("error", 0) else "pass",
        "counts": counts,
        "issues": [asdict(issue) for issue in issues],
    }


def build_parser() -> argparse.ArgumentParser:
    """Build command-line parser."""

    parser = argparse.ArgumentParser(description="Review bilingual-reader generated artifacts.")
    parser.add_argument("--markdown", type=Path, help="Approved Markdown source.")
    parser.add_argument("--data", type=Path, help="Generated and reviewed data.json.")
    parser.add_argument("--html", type=Path, action="append", default=[], help="Generated HTML file; repeatable.")
    parser.add_argument("--output", type=Path, help="Optional JSON report path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    args = build_parser().parse_args(argv)
    issues: list[Issue] = []
    markdown_text = review_markdown(args.markdown, issues) if args.markdown else ""
    if args.data:
        review_data(args.data, markdown_text, issues)
    for html_path in args.html:
        review_html(html_path, issues)
    if not args.markdown and not args.data and not args.html:
        add_issue(issues, "error", "cli.no_artifacts", "cli", ".", "未提供任何审查文件。", "至少传入 --markdown、--data 或 --html。")
    report = build_report(issues)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())

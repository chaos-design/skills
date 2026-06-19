#!/usr/bin/env python3
"""Convert web and document inputs to Markdown with MarkItDown."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable
from html.parser import HTMLParser


SKIP_TAGS = {"script", "style", "template", "noscript", "svg", "canvas"}
DROP_TAGS = {"nav", "header", "footer", "aside", "form"}
CONTENT_HINTS = ("content", "article", "post", "entry", "doc", "markdown", "prose")
NOISE_HINTS = ("cookie", "banner", "advert", "ads", "modal", "popup", "share", "subscribe")
PLATFORM_HOST_HINTS = {
    "x-twitter": ("x.com", "twitter.com"),
    "weibo": ("weibo.com", "weibo.cn"),
    "zhihu": ("zhihu.com",),
    "xiaohongshu": ("xiaohongshu.com", "xhslink.com"),
    "bilibili": ("bilibili.com", "b23.tv"),
    "wechat": ("mp.weixin.qq.com",),
}

LANG_CLASS_RE = re.compile(r"(?:language|lang|brush|highlight-source)[-:]\s*([a-z0-9#+.]+)", re.IGNORECASE)
LANG_ALIASES = {
    "py": "python",
    "js": "javascript",
    "jsx": "javascript",
    "ts": "typescript",
    "tsx": "typescript",
    "rb": "ruby",
    "sh": "bash",
    "shell": "bash",
    "zsh": "bash",
    "yml": "yaml",
    "md": "markdown",
    "plaintext": "text",
    "plain": "text",
    "c++": "cpp",
    "c#": "csharp",
    "cs": "csharp",
}
KNOWN_LANGS = {
    "python", "javascript", "typescript", "java", "kotlin", "swift", "go",
    "rust", "ruby", "php", "bash", "shell", "sh", "sql", "json", "yaml",
    "toml", "html", "css", "scss", "xml", "c", "cpp", "csharp", "objectivec",
    "scala", "perl", "lua", "r", "dart", "elixir", "erlang", "haskell",
    "clojure", "groovy", "markdown", "dockerfile", "makefile", "graphql",
    "diff", "ini", "powershell", "vim", "text",
}


@dataclass
class Node:
    """Small DOM node used by the Markdown converter."""

    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list["Node"] = field(default_factory=list)
    text: str = ""


@dataclass
class MarkdownDocument:
    """Markdown content produced from any MarkItDown-supported source."""

    title: str
    source: str
    body: str
    method: str = "markitdown-direct"
    confidence: str = "high"
    issues: list[str] = field(default_factory=list)
    source_language: str = "unspecified"
    target_language: str = "none"


class TreeBuilder(HTMLParser):
    """Parse enough HTML structure for content extraction and Markdown output."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        node = Node(tag, {key.lower(): value or "" for key, value in attrs})
        self.stack[-1].children.append(node)
        if tag not in {"br", "img", "meta", "link", "hr", "input"}:
            self.stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.stack[-1].children.append(Node("#text", text=data))


def validate_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Only absolute http:// and https:// URLs are supported.")
    if parsed.username or parsed.password:
        raise ValueError("URLs with embedded credentials are not supported.")
    return url


def delegated_platform(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower().split("@")[-1].split(":")[0]
    host = host[4:] if host.startswith("www.") else host
    for platform, hints in PLATFORM_HOST_HINTS.items():
        if any(host == hint or host.endswith(f".{hint}") for hint in hints):
            return platform
    return ""


def validate_web_markdown_url(url: str) -> str:
    url = validate_url(url)
    platform = delegated_platform(url)
    if platform:
        raise ValueError(
            f"{platform} URLs must be handled by url-content-fetcher; "
            "web-markdown only processes non-specialized URLs with MarkItDown."
        )
    return url


def is_http_url(value: str) -> bool:
    parsed = urllib.parse.urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def has_url_scheme(value: str) -> bool:
    return bool(urllib.parse.urlparse(value).scheme)


def load_markitdown():
    """Load MarkItDown lazily so tests and error messages stay deterministic."""
    try:
        from markitdown import MarkItDown  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "MarkItDown is required for web-markdown conversion. "
            "Install it with: pip install 'markitdown[all]'"
        ) from exc
    return MarkItDown()


def markdown_result_text(result: object) -> str:
    """Extract Markdown text from MarkItDown result variants."""
    for attr in ("text_content", "markdown", "text"):
        value = getattr(result, attr, None)
        if isinstance(value, str) and value.strip():
            return value
    if isinstance(result, str):
        return result
    raise ValueError("MarkItDown returned no Markdown text.")


def markdown_result_title(result: object) -> str:
    title = getattr(result, "title", "")
    return clean_inline(title) if isinstance(title, str) else ""


def first_markdown_heading(markdown: str) -> str:
    for line in markdown.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return clean_inline(match.group(1))
    return ""


def source_title_fallback(source: str) -> str:
    if is_http_url(source):
        parsed = urllib.parse.urlparse(source)
        return parsed.netloc or "Untitled Page"
    if source == "pasted-notes":
        return "Pasted Notes"
    path = Path(source)
    return path.stem or "Untitled Document"


def fetched_timestamp() -> str:
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")


def wrap_markdown_document(document: MarkdownDocument) -> str:
    body = document.body.strip()
    if not body:
        raise ValueError("Markdown body is empty after conversion.")
    fetched = fetched_timestamp()
    markdown = f"# {document.title}\n\n> Source: {document.source}\n> Fetched: {fetched}\n\n{body}\n"
    validate_markdown(markdown)
    return markdown


def convert_markitdown_input(
    value: str | Path,
    source: str,
    is_url: bool = False,
    method: str = "",
    confidence: str = "high",
    issues: list[str] | None = None,
) -> MarkdownDocument:
    converter = load_markitdown()
    if is_url and hasattr(converter, "convert_url"):
        result = converter.convert_url(str(value))
    else:
        result = converter.convert(str(value))
    body = markdown_result_text(result)
    title = markdown_result_title(result) or first_markdown_heading(body) or source_title_fallback(source)
    resolved_method = method or ("markitdown-direct" if is_url else "markitdown-file")
    return MarkdownDocument(
        title=title,
        source=source,
        body=body,
        method=resolved_method,
        confidence=confidence,
        issues=issues or [],
    )


def convert_rendered_html_with_markitdown(
    source_url: str,
    html_source: str,
    method: str = "html-file",
    confidence: str = "medium",
    issues: list[str] | None = None,
) -> MarkdownDocument:
    with NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=True) as html_file:
        html_file.write(html_source)
        html_file.flush()
        return convert_markitdown_input(
            Path(html_file.name),
            source_url,
            method=method,
            confidence=confidence,
            issues=issues,
        )


def convert_text_with_markitdown(
    text: str,
    source: str = "pasted-notes",
    method: str = "text",
) -> MarkdownDocument:
    if not text.strip():
        raise ValueError("Pasted text is empty.")
    with NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=True) as text_file:
        text_file.write(text)
        text_file.flush()
        return convert_markitdown_input(Path(text_file.name), source, method=method)


def convert_url_with_markitdown(source_url: str, port: int = 9377, wait: float = 4.0) -> MarkdownDocument:
    source_url = validate_web_markdown_url(source_url)
    try:
        return convert_markitdown_input(source_url, source_url, is_url=True)
    except Exception as markitdown_error:
        if "MarkItDown is required" in str(markitdown_error):
            raise
        try:
            rendered_html = fetch_with_camofox(source_url, port, wait)
            return convert_rendered_html_with_markitdown(
                source_url,
                rendered_html,
                method="camofox-fallback",
                confidence="medium",
                issues=[f"Direct MarkItDown URL conversion failed: {markitdown_error}"],
            )
        except Exception as camofox_error:
            raise RuntimeError(
                "MarkItDown URL conversion failed and Camofox fallback also failed: "
                f"MarkItDown={markitdown_error}; Camofox={camofox_error}"
            ) from camofox_error


def convert_file_with_markitdown(path: Path) -> MarkdownDocument:
    if not path.exists():
        raise FileNotFoundError(f"Input file does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"Input path is not a file: {path}")
    return convert_markitdown_input(path, str(path))


def convert_source_to_document(args: argparse.Namespace) -> MarkdownDocument:
    if args.html_file:
        source_url = validate_web_markdown_url(args.source or getattr(args, "url", "") or "")
        source = args.html_file.read_text(encoding="utf-8")
        document = convert_rendered_html_with_markitdown(source_url, source)
    elif args.text is not None:
        document = convert_text_with_markitdown(args.text, method="text")
    elif args.stdin:
        document = convert_text_with_markitdown(sys.stdin.read(), method="stdin")
    else:
        source = args.source or getattr(args, "url", "")
        if not source:
            raise ValueError("Provide a URL, file path, --text, or --stdin input.")
        if is_http_url(source):
            document = convert_url_with_markitdown(source, args.port, args.wait)
        elif has_url_scheme(source):
            raise ValueError("Only absolute http:// and https:// URLs are supported.")
        else:
            document = convert_file_with_markitdown(Path(source))
    document.source_language = getattr(args, "source_language", None) or "unspecified"
    document.target_language = getattr(args, "target_language", None) or "none"
    return document


def convert_source_to_markdown(args: argparse.Namespace) -> str:
    return wrap_markdown_document(convert_source_to_document(args))


def slugify(value: str, fallback: str = "page") -> str:
    slug = re.sub(r"\s+", "-", value.strip().lower())
    slug = re.sub(r"[^a-z0-9-]+", "", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return (slug[:80].strip("-") or fallback) + ".md"


def parse_html(source: str) -> Node:
    parser = TreeBuilder()
    parser.feed(source)
    return parser.root


def node_text(node: Node) -> str:
    if node.tag == "#text":
        return node.text
    return "".join(node_text(child) for child in node.children)


def element_key(node: Node) -> str:
    return " ".join([node.attrs.get("id", ""), node.attrs.get("class", ""), node.attrs.get("role", "")]).lower()


def should_drop(node: Node) -> bool:
    if node.tag in DROP_TAGS:
        return True
    key = element_key(node)
    return any(hint in key for hint in NOISE_HINTS)


def iter_nodes(node: Node) -> Iterable[Node]:
    yield node
    for child in node.children:
        yield from iter_nodes(child)


def content_score(node: Node) -> int:
    if should_drop(node):
        return -1000
    key = element_key(node)
    score = len(re.findall(r"\w+", node_text(node)))
    if node.tag == "article":
        score += 800
    if node.tag == "main" or node.attrs.get("role", "").lower() == "main":
        score += 700
    if any(hint in key for hint in CONTENT_HINTS):
        score += 300
    score += sum(20 for child in node.children if child.tag in {"p", "pre", "blockquote", "ul", "ol"})
    return score


def extract_main(root: Node) -> Node:
    candidates = [node for node in iter_nodes(root) if node.tag not in {"#text", "document"}]
    if not candidates:
        raise ValueError("No HTML elements found in rendered page.")
    best = max(candidates, key=content_score)
    if len(node_text(best).strip()) < 20:
        raise ValueError("No readable content area found in rendered page.")
    return best


def absolute_url(base_url: str, value: str) -> str:
    if not value:
        return ""
    return urllib.parse.urljoin(base_url, html.unescape(value.strip()))


def inline_markdown(node: Node, base_url: str) -> str:
    if node.tag == "#text":
        return re.sub(r"\s+", " ", node.text)
    if should_drop(node):
        return ""
    if node.tag == "br":
        return "\n"
    if node.tag == "code":
        return "`" + node_text(node).strip().replace("`", "\\`") + "`"
    if node.tag in {"strong", "b"}:
        text = clean_inline("".join(inline_markdown(child, base_url) for child in node.children))
        return f"**{text}**" if text else ""
    if node.tag in {"em", "i"}:
        text = clean_inline("".join(inline_markdown(child, base_url) for child in node.children))
        return f"*{text}*" if text else ""
    if node.tag == "img":
        alt = node.attrs.get("alt", "")
        src = absolute_url(base_url, node.attrs.get("src", ""))
        return f"![{alt}]({src})" if src else ""
    if node.tag == "a":
        label = clean_inline("".join(inline_markdown(child, base_url) for child in node.children))
        href = absolute_url(base_url, node.attrs.get("href", ""))
        return f"[{label or href}]({href})" if href else label
    return "".join(inline_markdown(child, base_url) for child in node.children)


def clean_inline(value: str) -> str:
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    return html.unescape(value).strip()


def block_markdown(
    node: Node,
    base_url: str,
    list_depth: int = 0,
    code_language_hint: str = "",
) -> list[str]:
    if should_drop(node):
        return []
    if node.tag == "#text":
        text = clean_inline(node.text)
        return [text] if text else []
    if node.tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        level = int(node.tag[1])
        return [f"{'#' * level} {clean_inline(inline_markdown(node, base_url))}"]
    if node.tag in {"p", "figcaption"}:
        text = clean_inline(inline_markdown(node, base_url))
        return [text] if text else []
    if node.tag == "pre":
        code = normalize_code_block(node_text(node))
        if not code:
            return []
        language = detect_code_language(node) or code_language_hint
        return [f"```{language}\n{code}\n```"]
    if node.tag in {"ul", "ol"}:
        return list_markdown(node, base_url, ordered=node.tag == "ol", depth=list_depth)
    if node.tag == "blockquote":
        lines = children_markdown(node, base_url, list_depth)
        return ["> " + line if line else ">" for line in lines]
    if node.tag == "table":
        table = table_markdown(node, base_url)
        if table:
            return ["\n".join(table)]
        return children_markdown(node, base_url, list_depth, code_language_hint)
    if node.tag == "img":
        image = inline_markdown(node, base_url)
        return [image] if image else []
    if node.tag == "a":
        label = clean_inline(" ".join(clean_inline(inline_markdown(child, base_url)) for child in node.children))
        label = re.sub(r"\s+", " ", label).strip()
        href = absolute_url(base_url, node.attrs.get("href", ""))
        link = f"[{label or href}]({href})" if href else label
        return [link] if link else []
    return children_markdown(node, base_url, list_depth, code_language_hint)


def normalize_code_block(value: str) -> str:
    """Strip rendered line-number gutters and keep the original code intact."""
    code = html.unescape(value).strip("\n")
    if "\n" in code:
        return strip_line_number_gutter(code)
    code = re.sub(r"(?<!\d)(\d+)(?=[A-Za-z_@#\"'({])", r"\n\1\n", code)
    code = re.sub(r"(?<=[^\d\s])(\d{1,3})(?=\s{2,}|[A-Za-z_@#\"'({])", r"\n\1\n", code)
    code = re.sub(r"(?<=[^\d\s])(\d{1,3})(?=[)\]}])", r"\n\1\n", code)
    code = re.sub(r"^\n+", "", code)
    return strip_line_number_gutter(code.strip("\n"))


def strip_line_number_gutter(code: str) -> str:
    """Remove standalone line-number lines that come from rendered code gutters."""
    lines = code.split("\n")
    numbered = [line for line in lines if re.fullmatch(r"\s*\d+\s*", line)]
    content = [line for line in lines if not re.fullmatch(r"\s*\d+\s*", line)]
    # Only drop the gutter when numbers form a meaningful share of the lines and
    # there is real code left behind. This protects genuine numeric-only code.
    if numbered and content and len(numbered) >= max(2, len(content) // 2):
        return "\n".join(content).strip("\n")
    return code.strip("\n")


def detect_code_language(node: Node) -> str:
    """Infer a highlight.js language hint from the code element's attributes."""
    targets = [node]
    targets.extend(child for child in node.children if child.tag == "code")
    for element in targets:
        for attr in ("class", "data-language", "data-lang", "lang"):
            value = element.attrs.get(attr, "")
            if not value:
                continue
            match = LANG_CLASS_RE.search(value)
            candidate = match.group(1) if match else value.strip()
            language = normalize_language(candidate)
            if language:
                return language
            for token in re.split(r"[\s_]+", value):
                language = normalize_language(token)
                if language:
                    return language
    return ""


def normalize_language(token: str) -> str:
    token = token.strip().lower()
    token = re.sub(r"\s+", "-", token)
    token = re.sub(r"^(language|lang|brush|highlight-source)[-:]", "", token)
    token = {"plain-text": "text"}.get(token, token)
    token = LANG_ALIASES.get(token, token)
    return token if token in KNOWN_LANGS else ""


def heading_language_hint(node: Node) -> str:
    if node.tag not in {"h3", "h4", "h5", "h6"}:
        return ""
    return normalize_language(clean_inline(node_text(node)))


def children_markdown(
    node: Node,
    base_url: str,
    list_depth: int = 0,
    code_language_hint: str = "",
) -> list[str]:
    parts: list[str] = []
    pending_language = code_language_hint
    for child in node.children:
        if child.tag in {"h3", "h4", "h5", "h6"}:
            parts.extend(block_markdown(child, base_url, list_depth, pending_language))
            pending_language = heading_language_hint(child) or pending_language
            continue
        previous_count = len(parts)
        parts.extend(block_markdown(child, base_url, list_depth, pending_language))
        if pending_language and len(parts) > previous_count and child.tag != "#text":
            pending_language = ""
    return [part for part in parts if part.strip()]


def list_markdown(node: Node, base_url: str, ordered: bool, depth: int) -> list[str]:
    lines: list[str] = []
    index = 1
    for child in node.children:
        if child.tag != "li":
            continue
        nested = [grand for grand in child.children if grand.tag in {"ul", "ol"}]
        direct = Node("li", child.attrs, [grand for grand in child.children if grand not in nested])
        text = clean_inline(inline_markdown(direct, base_url))
        marker = f"{index}." if ordered else "-"
        lines.append(f"{'  ' * depth}{marker} {text}".rstrip())
        for nested_list in nested:
            lines.extend(list_markdown(nested_list, base_url, nested_list.tag == "ol", depth + 1))
        index += 1
    return lines


def table_markdown(node: Node, base_url: str) -> list[str]:
    rows = []
    for row in [child for child in iter_nodes(node) if child.tag == "tr"]:
        cells = [clean_inline(inline_markdown(cell, base_url)) for cell in row.children if cell.tag in {"th", "td"}]
        if cells:
            rows.append(cells)
    if not rows:
        return []
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    header = "| " + " | ".join(rows[0]) + " |"
    separator = "| " + " | ".join(["---"] * width) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows[1:]]
    return [header, separator, *body]


def detect_title(root: Node, main: Node, source_url: str) -> str:
    for tag in ("h1", "title"):
        for node in iter_nodes(main if tag == "h1" else root):
            if node.tag == tag:
                title = clean_inline(node_text(node))
                if title:
                    return title
    return urllib.parse.urlparse(source_url).netloc or "Untitled Page"


def html_to_markdown(source: str, source_url: str) -> str:
    if not re.search(r"<[a-zA-Z][^>]*>", source):
        return snapshot_to_markdown(source, source_url)
    root = parse_html(source)
    main = extract_main(root)
    title = detect_title(root, main, source_url)
    body = "\n\n".join(children_markdown(main, source_url))
    if not body:
        raise ValueError("Markdown body is empty after conversion.")
    fetched = fetched_timestamp()
    markdown = f"# {title}\n\n> Source: {source_url}\n> Fetched: {fetched}\n\n{body}\n"
    validate_markdown(markdown)
    return markdown


def snapshot_to_markdown(source: str, source_url: str) -> str:
    lines = [line.strip() for line in source.splitlines()]
    blocks: list[str] = []
    title = ""
    index = 0
    while index < len(lines):
        line = lines[index]
        heading = re.search(r'heading "(.+?)".*level=(\d)', line)
        link = re.search(r'link "(.+?)"', line)
        image = re.search(r'(?:img|image) "([^"]*)"', line)
        if heading:
            level = max(1, min(6, int(heading.group(2))))
            text = clean_inline(heading.group(1))
            title = title or text
            blocks.append(f"{'#' * level} {text}")
        elif link:
            label = clean_inline(link.group(1))
            href = snapshot_nearby_url(lines, index)
            blocks.append(f"[{label}]({href})" if href else label)
        elif image:
            alt = clean_inline(image.group(1))
            src = snapshot_nearby_url(lines, index)
            blocks.append(f"![{alt}]({src})" if src else f"![{alt}]()")
        elif line.startswith(("- text:", "text:")):
            blocks.append(clean_inline(line.split(":", 1)[1]))
        index += 1
    body = "\n\n".join(block for block in blocks if block)
    if not body:
        raise ValueError("Snapshot body is empty after conversion.")
    title = title or urllib.parse.urlparse(source_url).netloc or "Untitled Page"
    fetched = fetched_timestamp()
    markdown = f"# {title}\n\n> Source: {source_url}\n> Fetched: {fetched}\n\n{body}\n"
    validate_markdown(markdown)
    return markdown


def snapshot_nearby_url(lines: list[str], start: int) -> str:
    window = lines[start:min(len(lines), start + 4)]
    for line in window:
        if "/url:" in line:
            return line.split("/url:", 1)[1].strip()
        match = re.search(r"https?://\S+", line)
        if match:
            return match.group(0).rstrip(".,);]")
    return ""


def validate_markdown(markdown: str) -> None:
    if not markdown.startswith("# "):
        raise ValueError("Markdown title is missing.")
    if "> Source:" not in markdown:
        raise ValueError("Source metadata is missing.")
    if len(re.findall(r"```", markdown)) % 2:
        raise ValueError("Unbalanced fenced code block.")
    if re.search(r"\b(TODO|FIXME|<Title>)\b", markdown):
        raise ValueError("Markdown contains placeholder text.")


def metadata_source(markdown: str) -> str:
    match = re.search(r"^> Source:\s*(.+)$", markdown, re.MULTILINE)
    return match.group(1).strip() if match else "unknown-source"


def unique_output_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    index = 2
    while True:
        candidate = path.with_name(f"{stem}-{index}{suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def default_output_path(markdown: str) -> Path:
    title = markdown.splitlines()[0].lstrip("#").strip()
    return Path("web") / slugify(title)


def write_markdown(markdown: str, output: Path | None) -> Path:
    target = unique_output_path(output or default_output_path(markdown))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    return target


def workspace_original_output(args: argparse.Namespace) -> Path | None:
    workspace = getattr(args, "workspace", None)
    if getattr(args, "output", None) or workspace is None:
        return getattr(args, "output", None)
    return workspace / "source" / "original.md"


def translated_source_path(output: Path, target_language: str) -> str:
    if not target_language or target_language == "none":
        return "none"
    return str(output.with_name(f"original.{target_language}.md"))


def build_extraction_notes(document: MarkdownDocument, output: Path, validation: str = "pass") -> str:
    issues = document.issues or ["none"]
    issue_lines = "\n".join(f"  - {issue}" for issue in issues)
    return (
        "# Extraction Notes\n\n"
        f"- Source: {document.source}\n"
        f"- Output: {output}\n"
        f"- Source Language: {document.source_language}\n"
        f"- Target Language: {document.target_language}\n"
        f"- Translated Source: {translated_source_path(output, document.target_language)}\n"
        f"- Method: {document.method}\n"
        f"- Confidence: {document.confidence}\n"
        "- Issues:\n"
        f"{issue_lines}\n"
        f"- Validation: {validation}\n"
    )


def write_extraction_notes(document: MarkdownDocument, output: Path, notes_output: Path | None) -> Path | None:
    if notes_output is None:
        return None
    target = unique_output_path(notes_output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_extraction_notes(document, output), encoding="utf-8")
    return target


def camofox_request(url: str, method: str = "GET", payload: dict[str, str] | None = None, timeout: int = 15) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
    return json.loads(body) if body else {}


def fetch_with_camofox(source_url: str, port: int = 9377, wait: float = 4.0) -> str:
    payload = {"userId": "web-markdown", "sessionKey": "web-markdown", "url": source_url}
    try:
        data = camofox_request(f"http://localhost:{port}/tabs", "POST", payload, timeout=15)
        tab_id = data.get("tabId") or data.get("id")
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Camofox is not reachable or could not open the URL: {exc}") from exc
    if not tab_id:
        raise RuntimeError("Camofox did not return a tab id.")
    try:
        time.sleep(wait)
        return read_camofox_content(str(tab_id), port)
    finally:
        close_camofox_tab(str(tab_id), port)


def read_camofox_content(tab_id: str, port: int) -> str:
    endpoints = ("content", "html", "snapshot")
    for endpoint in endpoints:
        url = f"http://localhost:{port}/tabs/{tab_id}/{endpoint}?userId=web-markdown"
        try:
            data = camofox_request(url, timeout=20)
        except (OSError, urllib.error.URLError, json.JSONDecodeError):
            continue
        content = data.get("html") or data.get("content") or data.get("snapshot") or ""
        if content.strip():
            return content
    raise RuntimeError("Camofox rendered the tab, but no page content could be read.")


def close_camofox_tab(tab_id: str, port: int) -> None:
    url = f"http://localhost:{port}/tabs/{tab_id}?userId=web-markdown"
    try:
        camofox_request(url, "DELETE", timeout=5)
    except Exception:
        pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert URLs, documents, images, and pasted notes to Markdown.")
    parser.add_argument(
        "source",
        nargs="?",
        help="HTTP(S) URL or local file supported by MarkItDown, such as PDF, DOCX, Markdown, text, or screenshot.",
    )
    parser.add_argument("--output", type=Path, help="Optional output Markdown path.")
    parser.add_argument("--workspace", type=Path, help="Workspace root; defaults output to source/original.md.")
    parser.add_argument("--notes-output", type=Path, help="Optional extraction notes Markdown path.")
    parser.add_argument("--source-language", help="Original source language label for extraction notes.")
    parser.add_argument("--target-language", help="Requested translation language label, such as zh-CN or en.")
    parser.add_argument("--html-file", type=Path, help="Use a local rendered HTML file as URL fallback input.")
    parser.add_argument("--text", help="Convert pasted notes or plain text provided directly on the command line.")
    parser.add_argument("--stdin", action="store_true", help="Read pasted notes or plain text from standard input.")
    parser.add_argument("--port", type=int, default=9377, help="Camofox fallback port for rendered URLs. Defaults to 9377.")
    parser.add_argument("--wait", type=float, default=4.0, help="Seconds to wait after opening the Camofox fallback tab.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        document = convert_source_to_document(args)
        markdown = wrap_markdown_document(document)
        output = write_markdown(markdown, workspace_original_output(args))
        notes = write_extraction_notes(document, output, args.notes_output)
    except Exception as exc:
        print(f"web-markdown failed: {exc}", file=sys.stderr)
        return 1
    word_count = len(re.findall(r"\w+", markdown))
    source_label = metadata_source(markdown)
    message = f"Saved {output} - {word_count} words - {source_label} - confidence {document.confidence}"
    if notes:
        message += f" - notes {notes}"
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

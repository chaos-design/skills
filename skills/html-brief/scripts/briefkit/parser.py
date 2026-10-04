"""Draft parser: front matter, Markdown blocks and diagram components.

A draft is ordinary Markdown plus fenced blocks whose info string names one of
the diagram components. Every failure carries a line number and a correct
example so an agent can fix a draft in one pass.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Fenced info strings that mean "this is source code", not a component.
CODE_LANGUAGES = {
    "bash", "c", "conf", "cpp", "css", "csv", "diff", "dockerfile", "go", "golang",
    "graphql", "hcl", "html", "ini", "java", "javascript", "js", "json", "json5",
    "jsx", "kotlin", "kt", "lua", "make", "makefile", "markdown", "md", "none",
    "php", "plain", "plaintext", "proto", "python", "py", "r", "rb", "ruby",
    "rust", "scala", "sh", "shell", "sql", "swift", "text", "toml", "ts",
    "typescript", "tsx", "txt", "vue", "xml", "yaml", "yml", "zsh",
}

# Components that draw themselves and therefore ignore plain code rendering.
COMPONENTS = {
    "flow": "flow [LR|TB]",
    "sequence": "sequence [num]",
    "tree": "tree",
    "timeline": "timeline",
    "limits": "limits",
    "stat": "stat",
    "annot": "annot",
    "kv": "kv",
}

_FENCE_RE = re.compile(r"^(?P<fence>`{3,}|~{3,})\s*(?P<info>.*)$")
_HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.*)$")
_LIST_RE = re.compile(r"^(?P<indent>\s*)(?P<bullet>[-*+]|\d+[.)])\s+(?P<text>.*)$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_SPAN_RE = re.compile(r"\{span=(?P<span>\d+)\}\s*$")
_CALLOUT_RE = re.compile(r"^(?P<kind>note|tip|warn|danger|key)\s*[:：]\s*(?P<rest>.*)$")
_FRONTMATTER_KEY_RE = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9_-]*)\s*:\s*(?P<value>.*)$")

CALLOUT_KINDS = ("note", "tip", "warn", "danger", "key")


class DraftError(Exception):
    """A draft problem that an agent can fix, with a line number."""

    def __init__(self, message: str, line: int = 0, component: str = "", example: str = ""):
        super().__init__(message)
        self.message = message
        self.line = line
        self.component = component
        self.example = example

    def render(self, source: str = "") -> str:
        where = f"line {self.line}" if self.line else "draft"
        head = f"{source + ': ' if source else ''}{where}"
        if self.component:
            head += f" · {self.component}"
        out = f"{head}: {self.message}"
        if self.example:
            out += f"\n  correct form: {self.example}"
        return out


@dataclass
class Heading:
    level: int
    text: str
    line: int


@dataclass
class Paragraph:
    text: str
    line: int


@dataclass
class ListBlock:
    ordered: bool
    items: list[str]
    line: int


@dataclass
class TableBlock:
    headers: list[str]
    rows: list[list[str]]
    align: list[str]
    line: int


@dataclass
class CodeBlock:
    lang: str
    text: str
    line: int


@dataclass
class QuoteBlock:
    text: str
    line: int


@dataclass
class CalloutBlock:
    kind: str
    title: str
    text: str
    line: int


@dataclass
class ComponentBlock:
    name: str
    args: list[str]
    text: str
    line: int
    label: str = ""


@dataclass
class Panel:
    title: str
    span: int
    blocks: list[object]
    line: int
    lead: str = ""


@dataclass
class Document:
    meta: dict[str, str] = field(default_factory=dict)
    title: str = ""
    panels: list[Panel] = field(default_factory=list)


def parse_front_matter(lines: list[str]) -> tuple[dict[str, str], int]:
    """Read a leading `---` block of `key: value` pairs."""
    if not lines or lines[0].strip() != "---":
        return {}, 0
    meta: dict[str, str] = {}
    for index in range(1, len(lines)):
        line = lines[index]
        if line.strip() == "---":
            return meta, index + 1
        if not line.strip():
            continue
        match = _FRONTMATTER_KEY_RE.match(line)
        if not match:
            raise DraftError(
                "front matter must use `key: value` pairs",
                index + 1,
                "front matter",
                "title: TCP three-way handshake",
            )
        value = match.group("value").strip().strip('"').strip("'")
        meta[match.group("key").lower()] = value
    raise DraftError("front matter is never closed with `---`", 1, "front matter")


def _split_table_row(row: str) -> list[str]:
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    cells: list[str] = []
    buffer: list[str] = []
    escaped = False
    for ch in row:
        if escaped:
            buffer.append(ch)
            escaped = False
        elif ch == "\\":
            buffer.append(ch)
            escaped = True
        elif ch == "|":
            cells.append("".join(buffer).strip())
            buffer = []
        else:
            buffer.append(ch)
    cells.append("".join(buffer).strip())
    return cells


def _table_align(row: str) -> list[str]:
    align: list[str] = []
    for cell in _split_table_row(row):
        left = cell.startswith(":")
        right = cell.endswith(":")
        if left and right:
            align.append("center")
        elif right:
            align.append("right")
        else:
            align.append("left")
    return align


def _is_table_row(line: str) -> bool:
    return "|" in line and line.strip() != ""


def _parse_table(body: list[str], start: int, offset: int) -> tuple[TableBlock, int]:
    line_no = start + 1 + offset
    if start + 1 >= len(body) or not _TABLE_SEP_RE.match(body[start + 1]):
        raise DraftError(
            "a table needs a separator row under the header row",
            line_no,
            "table",
            "| A | B |\n| --- | --- |\n| 1 | 2 |",
        )
    headers = _split_table_row(body[start])
    align = _table_align(body[start + 1])
    rows: list[list[str]] = []
    index = start + 2
    while index < len(body) and _is_table_row(body[index]):
        cells = _split_table_row(body[index])
        if len(cells) != len(headers):
            raise DraftError(
                f"table row has {len(cells)} cells but the header has {len(headers)}",
                index + 1 + offset,
                "table",
                "| A | B |\n| --- | --- |\n| 1 | 2 |",
            )
        rows.append(cells)
        index += 1
    return TableBlock(headers, rows, align, line_no), index


def _is_block_start(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if _FENCE_RE.match(line):
        return True
    if _HEADING_RE.match(line):
        return True
    if _LIST_RE.match(line):
        return True
    if stripped.startswith(">"):
        return True
    if set(stripped) <= set("-|: ") and "|" in stripped:
        return True
    return False


def _parse_blocks(body: list[str], start: int, end: int, offset: int = 0) -> list[object]:
    blocks: list[object] = []
    index = start
    while index < end:
        raw = body[index]
        line = raw.rstrip("\n")
        if not line.strip():
            index += 1
            continue

        fence = _FENCE_RE.match(line)
        if fence:
            block, index = _parse_fence(body, index, end, offset)
            if block is not None:
                blocks.append(block)
            continue

        heading = _HEADING_RE.match(line)
        if heading:
            blocks.append(
                Heading(len(heading.group("hashes")), heading.group("text").strip(), index + 1 + offset)
            )
            index += 1
            continue

        if _LIST_RE.match(line):
            block, index = _parse_list(body, index, end, offset)
            blocks.append(block)
            continue

        if stripped_quote(line):
            block, index = _parse_quote(body, index, end, offset)
            blocks.append(block)
            continue

        if (
            _is_table_row(line)
            and index + 1 < end
            and _TABLE_SEP_RE.match(body[index + 1].rstrip("\n"))
        ):
            block, index = _parse_table(body, index, offset)
            blocks.append(block)
            continue

        paragraph, index = _parse_paragraph(body, index, end, offset)
        if paragraph is not None:
            blocks.append(paragraph)
    return blocks


def stripped_quote(line: str) -> bool:
    return line.strip().startswith(">")


def _parse_paragraph(
    body: list[str], start: int, end: int, offset: int = 0
) -> tuple[Paragraph | None, int]:
    buffer: list[str] = []
    index = start
    while index < end:
        line = body[index].rstrip("\n")
        if not line.strip():
            break
        if buffer and _is_block_start(line):
            break
        if stripped_quote(line):
            break
        if buffer and _LIST_RE.match(line):
            break
        buffer.append(line.strip())
        index += 1
    if not buffer:
        return None, start + 1
    return Paragraph(" ".join(buffer), start + 1 + offset), index


def _parse_list(body: list[str], start: int, end: int, offset: int = 0) -> tuple[ListBlock, int]:
    first = _LIST_RE.match(body[start].rstrip("\n"))
    ordered = bool(first and first.group("bullet")[0].isdigit())
    items: list[str] = []
    index = start
    base_indent = len(first.group("indent")) if first else 0
    while index < end:
        line = body[index].rstrip("\n")
        match = _LIST_RE.match(line)
        if match:
            if len(match.group("indent")) < base_indent and items:
                break
            ordered = ordered or match.group("bullet")[0].isdigit()
            text = match.group("text").strip()
            items.append(text)
            index += 1
            continue
        if not line.strip():
            lookahead = index + 1
            while lookahead < end and not body[lookahead].strip():
                lookahead += 1
            if lookahead < end and _LIST_RE.match(body[lookahead].rstrip("\n")):
                index = lookahead
                continue
            break
        if items and not _is_block_start(line):
            items[-1] = f"{items[-1]} {line.strip()}"
            index += 1
            continue
        break
    return ListBlock(ordered, items, start + 1 + offset), index


def _parse_quote(body: list[str], start: int, end: int, offset: int = 0) -> tuple[object, int]:
    # A bare `>` line starts a new paragraph inside the quote. Source wrapping
    # inside one paragraph is not a title, and an empty line always ends the
    # quote so two adjacent callouts stay two callouts.
    paragraphs: list[list[str]] = [[]]
    index = start
    while index < end:
        line = body[index].rstrip("\n")
        if not stripped_quote(line):
            break
        content = line.strip().lstrip(">").strip()
        if content:
            paragraphs[-1].append(content)
        else:
            paragraphs.append([])
        index += 1
    groups = ["\n".join(group) for group in paragraphs if group]
    text = "\n\n".join(groups)
    match = _CALLOUT_RE.match(groups[0].split("\n")[0]) if groups else None
    if match:
        first_paragraph = groups[0].split("\n")
        first_paragraph[0] = match.group("rest")
        body_text = "\n\n".join(["\n".join(first_paragraph).strip()] + groups[1:]).strip()
        title, body_text = _split_callout_title(body_text)
        return CalloutBlock(match.group("kind"), title, body_text, start + 1 + offset), index
    return QuoteBlock(text, start + 1 + offset), index


def _split_callout_title(text: str) -> tuple[str, str]:
    """One paragraph is all body. Two paragraphs means the first is a title."""
    head, separator, rest = text.partition("\n\n")
    if not separator:
        return "", text.strip()
    return head.strip(), rest.strip()


def _parse_fence(body: list[str], start: int, end: int, offset: int = 0) -> tuple[object | None, int]:
    open_line = body[start].rstrip("\n")
    fence = _FENCE_RE.match(open_line)
    marker = fence.group("fence")
    info = fence.group("info").strip()
    line_no = start + 1 + offset
    index = start + 1
    buffer: list[str] = []
    while index < end:
        line = body[index].rstrip("\n")
        closing = _FENCE_RE.match(line)
        if closing and closing.group("fence")[0] == marker[0] and len(closing.group("fence")) >= len(marker) and not closing.group("info").strip():
            index += 1
            break
        buffer.append(line)
        index += 1
    else:
        raise DraftError(
            f"fenced block opened with `{marker}` is never closed",
            line_no,
            info.split()[0] if info else "fence",
            f"```{info}\n...\n```",
        )

    text = "\n".join(buffer).strip("\n")
    if not info:
        return CodeBlock("text", text, line_no), index

    parts = info.split()
    name = parts[0].lower()
    args = [part.lower() for part in parts[1:]]
    if name in COMPONENTS:
        return ComponentBlock(name, args, text, line_no), index
    if name in CODE_LANGUAGES:
        return CodeBlock(name, text, line_no), index
    known = ", ".join(sorted(COMPONENTS))
    raise DraftError(
        f"unknown component or language `{name}`",
        line_no,
        name,
        f"```flow LR\nA -> B: label\n```\ncomponents: {known}",
    )


def _parse_panels(blocks: list[object]) -> tuple[list[Panel], list[object]]:
    panels: list[Panel] = []
    lead: list[object] = []
    current: Panel | None = None
    title_level = 2
    seen_levels: list[int] = []

    for block in blocks:
        if isinstance(block, Heading) and block.level == 2:
            span_match = _SPAN_RE.search(block.text)
            span = 1
            title = block.text
            if span_match:
                span = int(span_match.group("span"))
                title = block.text[: span_match.start()].strip()
                if span not in (1, 2):
                    raise DraftError(
                        f"`span={span}` is not supported, use span=1 or span=2",
                        block.line,
                        "panel",
                        "## Why this matters {span=2}",
                    )
            current = Panel(title, span, [], block.line)
            panels.append(current)
            continue
        if isinstance(block, Heading):
            seen_levels.append(block.level)
            if not panels and block.level < 2:
                title_level = block.level
        if current is None:
            lead.append(block)
        else:
            current.blocks.append(block)

    if not panels:
        if lead:
            panels.append(Panel("", 2, lead, 1))
    else:
        if lead:
            panels.insert(0, Panel("", 2, lead, 1))
        for panel in panels:
            for block in panel.blocks:
                if isinstance(block, Heading) and block.level >= title_level:
                    raise DraftError(
                        "panels must start at `##`; deeper headings belong inside a panel",
                        block.line,
                        "heading",
                        "## Panel title {span=2}\n\n### Subsection",
                    )
    return panels, lead


def parse_draft(text: str, source: str = "") -> Document:
    """Parse a full draft into a document of panels and blocks."""
    # A byte-order mark is metadata, not content: it would otherwise turn the
    # front matter fence into a line of text and duplicate the first panel.
    body = text.lstrip("\ufeff").replace("\r\n", "\n").split("\n")
    meta, offset = parse_front_matter(body)
    rest = body[offset:]
    blocks = _parse_blocks(rest, 0, len(rest), offset)
    panels, lead = _parse_panels(blocks)

    doc_title = meta.get("title", "")
    if not doc_title:
        for block in lead:
            if isinstance(block, Heading) and block.level == 1:
                doc_title = block.text
                break
    if not doc_title:
        for panel in panels:
            if panel.title:
                doc_title = panel.title
                break
    if not panels:
        raise DraftError(
            "the draft has no content to render",
            1,
            "draft",
            "---\ntitle: Brief title\n---\n\n## Panel title\n\nText.",
        )
    return Document(meta=meta, title=doc_title, panels=panels)


def strip_emphasis(text: str) -> str:
    """Plain-text version of inline Markdown, used for labels and titles."""
    out = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    out = re.sub(r"[*_`~]{1,3}", "", out)
    return out.strip()
